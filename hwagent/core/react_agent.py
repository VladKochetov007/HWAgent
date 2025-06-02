"""ReAct Agent for homework solving with MCP tools."""

import asyncio
import json
import uuid
import tempfile
import shutil
import re
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass

import mcp.types as types
from mcp.server import Server

from ..utils.config import config
from ..utils.api_client import openrouter_client
from ..utils.tool_parser import get_all_tool_descriptions
from ..tools import create_mcp_server


@dataclass
class ReActStep:
    """Represents a single ReAct step."""
    iteration: int
    thought: str
    action: Optional[str] = None
    action_input: Optional[dict] = None
    observation: Optional[str] = None


class ReActAgent:
    """ReAct agent for homework solving with MCP tools."""
    
    def __init__(self, agent_id: Optional[str] = None):
        self.agent_id = agent_id or str(uuid.uuid4())
        self.mcp_server = create_mcp_server()
        self.working_dir: Optional[Path] = None
        self.steps: list[ReActStep] = []
        self.max_iterations = config.agent_settings["react_agent"]["max_iterations"]
        self.system_prompt = config.prompts["thinking"]["system_prompt"]
        self.user_prompt_template = config.prompts["thinking"]["user_prompt_template"]
        self.files_created: list[str] = []  # Track created files
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self.setup_working_directory()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()
    
    async def setup_working_directory(self) -> None:
        """Create session-specific working directory in ./tmp/<agent_id>/"""
        # Create session directory in ./tmp/<agent_id>/
        base_tmp_dir = Path("./tmp")
        base_tmp_dir.mkdir(exist_ok=True)
        
        self.working_dir = base_tmp_dir / self.agent_id
        self.working_dir.mkdir(parents=True, exist_ok=True)
        
        # Change to the session directory
        import os
        self.original_cwd = Path.cwd()
        os.chdir(self.working_dir)
        
    async def cleanup(self) -> None:
        """Clean up and restore original working directory."""
        # Restore original working directory
        if hasattr(self, 'original_cwd'):
            import os
            os.chdir(self.original_cwd)
        
        # Optionally clean up session directory
        if self.working_dir and self.working_dir.exists():
            cleanup_enabled = config.agent_settings["react_agent"]["cleanup_tmp_dirs"]
            if cleanup_enabled:
                shutil.rmtree(self.working_dir, ignore_errors=True)
    
    def build_user_prompt(self, problem: str) -> str:
        """
        Build the user prompt by parsing tool descriptions from source code.
        
        Args:
            problem: The homework problem to solve
            
        Returns:
            Formatted user prompt with tools description
        """
        tools_description = get_all_tool_descriptions()
        return self.user_prompt_template.format(
            problem=problem,
            tools_description=tools_description
        )
    
    async def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> str:
        """Execute MCP tool and return result."""
        try:
            # Track file creation for final answer
            if tool_name == "create_file" and "file_path" in arguments:
                file_path = arguments["file_path"]
                # Convert to absolute path for tracking
                abs_path = (self.working_dir / file_path).resolve()
                self.files_created.append(str(abs_path))
            
            # Get tool handler from server
            tool_handlers = {}
            for handler_name in dir(self.mcp_server):
                if handler_name.startswith('_call_tool_'):
                    tool_handlers[handler_name.replace('_call_tool_', '')] = getattr(self.mcp_server, handler_name)
            
            # Find matching tool
            handler = None
            for name, func in tool_handlers.items():
                if name == tool_name or tool_name in name:
                    handler = func
                    break
            
            if not handler:
                # Fallback: try to call tools directly
                if tool_name == "create_file":
                    from ..tools.create_file import create_file_tool
                    result = await create_file_tool(tool_name, arguments)
                elif tool_name == "edit_file":
                    from ..tools.edit_file import edit_file_tool
                    result = await edit_file_tool(tool_name, arguments)
                elif tool_name == "execute_command":
                    from ..tools.execute_command import execute_command_tool
                    result = await execute_command_tool(tool_name, arguments)
                elif tool_name == "search_web":
                    from ..tools.search_web import search_web_tool
                    result = await search_web_tool(tool_name, arguments)
                elif tool_name == "final_answer":
                    from ..tools.final_answer import final_answer_tool
                    result = await final_answer_tool(tool_name, arguments)
                else:
                    return f"Error: Unknown tool '{tool_name}'"
            else:
                result = await handler(tool_name, arguments)
            
            # Extract text from result
            if isinstance(result, list) and result:
                if hasattr(result[0], 'text'):
                    return result[0].text
                elif isinstance(result[0], dict) and 'text' in result[0]:
                    return result[0]['text']
                else:
                    return str(result[0])
            
            return str(result)
            
        except Exception as e:
            return f"Error executing tool '{tool_name}': {str(e)}"
    
    def parse_action(self, response: str) -> tuple[Optional[str], Optional[dict]]:
        """Parse action and action_input from LLM response."""
        try:
            # First try line-by-line parsing for properly formatted responses
            lines = response.split('\n')
            action = None
            action_input = None
            
            for i, line in enumerate(lines):
                line = line.strip()
                if line.startswith('Action:'):
                    action = line.replace('Action:', '').strip()
                elif line.startswith('Action Input:'):
                    # Try to parse JSON from the rest of the line
                    input_text = line.replace('Action Input:', '').strip()
                    try:
                        action_input = json.loads(input_text)
                    except json.JSONDecodeError:
                        # If not valid JSON, treat as string
                        action_input = {"input": input_text}
            
            # If line-by-line parsing didn't work, try inline parsing
            if not action or not action_input:
                # Look for patterns like "Action: tool_nameAction Input: {...}"
                # Use regex to find Action: followed by Action Input:
                action_pattern = r'Action:\s*([^\s]+)(?:.*?)Action Input:\s*(\{.*?\})'
                match = re.search(action_pattern, response, re.DOTALL)
                
                if match:
                    action = match.group(1).strip()
                    input_text = match.group(2).strip()
                    try:
                        action_input = json.loads(input_text)
                    except json.JSONDecodeError:
                        # Try to extract JSON more carefully
                        # Look for the first { and find its matching }
                        start_idx = input_text.find('{')
                        if start_idx != -1:
                            brace_count = 0
                            end_idx = start_idx
                            for i, char in enumerate(input_text[start_idx:], start_idx):
                                if char == '{':
                                    brace_count += 1
                                elif char == '}':
                                    brace_count -= 1
                                    if brace_count == 0:
                                        end_idx = i
                                        break
                            
                            json_str = input_text[start_idx:end_idx+1]
                            try:
                                action_input = json.loads(json_str)
                            except json.JSONDecodeError:
                                action_input = {"input": input_text}
                        else:
                            action_input = {"input": input_text}
                
                # If still no match, try a more flexible pattern
                if not action or not action_input:
                    # Pattern for inline actions without proper formatting
                    simple_pattern = r'Action:\s*([a-zA-Z_]+).*?Input:\s*(\{[^}]*\})'
                    simple_match = re.search(simple_pattern, response, re.DOTALL)
                    
                    if simple_match:
                        action = simple_match.group(1).strip()
                        input_text = simple_match.group(2).strip()
                        try:
                            action_input = json.loads(input_text)
                        except json.JSONDecodeError:
                            action_input = {"input": input_text}
            
            return action, action_input
            
        except Exception as e:
            return None, None
    
    def should_continue(self, response: str) -> bool:
        """Check if agent should continue or has finished."""
        # Look for final_answer tool usage instead of text patterns
        action, _ = self.parse_action(response)
        if action == "final_answer":
            return False
        
        # Also check for old-style final answer patterns as fallback
        final_patterns = [
            "Final Answer:",
            "FINAL ANSWER:",
        ]
        
        response_upper = response.upper()
        for pattern in final_patterns:
            if pattern.upper() in response_upper:
                return False
        
        return True
    
    async def solve(self, problem: str, verbose: bool = False) -> dict[str, Any]:
        """
        Solve a homework problem using ReAct approach.
        
        Args:
            problem: The homework problem to solve
            verbose: If True, print real-time progress
            
        Returns:
            Dictionary containing solution and execution steps
        """
        # Build dynamic user prompt with parsed tool descriptions
        user_prompt = self.build_user_prompt(problem)
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        if verbose:
            # ANSI color codes for terminal output
            GRAY = '\033[90m'
            GREEN = '\033[92m'
            BLUE = '\033[94m'
            YELLOW = '\033[93m'
            RESET = '\033[0m'
        
        for iteration in range(self.max_iterations):
            try:
                if verbose:
                    print(f"{GRAY}🔄 Iteration {iteration + 1}/{self.max_iterations}...{RESET}")
                
                # Get LLM response
                response = await openrouter_client.thinking_completion(messages)
                
                if verbose:
                    print(f"{GRAY}🤖 Agent response:{RESET}")
                    print(f"{GRAY}{response}{RESET}")
                    print(f"{GRAY}{'─'*40}{RESET}")
                
                # Parse thought
                thought_start = response.find("Thought:")
                if thought_start != -1:
                    thought_end = response.find('\n', thought_start)
                    if thought_end == -1:
                        thought_end = len(response)
                    thought = response[thought_start + 8:thought_end].strip()
                else:
                    thought = response[:100] + "..." if len(response) > 100 else response
                
                # Create step
                step = ReActStep(iteration=iteration + 1, thought=thought)
                
                # Parse action first
                action, action_input = self.parse_action(response)
                
                if action and action_input:
                    step.action = action
                    step.action_input = action_input
                    
                    if verbose:
                        print(f"{BLUE}⚡ Executing: {action}{RESET}")
                        print(f"{YELLOW}📥 Input: {action_input}{RESET}")
                    
                    # Execute action
                    observation = await self.execute_tool(action, action_input)
                    step.observation = observation
                    
                    if verbose:
                        obs_preview = observation[:200] + "..." if len(observation) > 200 else observation
                        print(f"{GREEN}👁️ Result: {obs_preview}{RESET}")
                        print()
                    
                    # Check if this was a final_answer tool call
                    if action == "final_answer":
                        self.steps.append(step)
                        if verbose:
                            print(f"{GREEN}✅ Task completed with final_answer tool!{RESET}")
                        break
                    
                    # Add assistant response and observation to conversation
                    messages.append({"role": "assistant", "content": response})
                    messages.append({"role": "user", "content": f"Observation: {observation}"})
                
                else:
                    # Check if this is a final answer (fallback)
                    if not self.should_continue(response):
                        step.observation = "Task completed with text-based final answer."
                        self.steps.append(step)
                        if verbose:
                            print(f"{GREEN}✅ Task completed!{RESET}")
                        break
                    else:
                        step.observation = "No valid action found in response. Please provide Action: and Action Input:"
                        if verbose:
                            print(f"{YELLOW}⚠️ No action found, asking for clarification...{RESET}")
                        # Add response and ask for action
                        messages.append({"role": "assistant", "content": response})
                        messages.append({"role": "user", "content": "Please provide a specific Action and Action Input to continue solving the problem. Remember to use the final_answer tool when you have completed all tasks."})
                
                self.steps.append(step)
                
            except Exception as e:
                error_step = ReActStep(
                    iteration=iteration + 1,
                    thought=f"Error occurred: {str(e)}",
                    observation="Iteration failed due to error."
                )
                self.steps.append(error_step)
                if verbose:
                    print(f"❌ Error in iteration {iteration + 1}: {str(e)}")
                break
        
        # Compile result
        result = {
            "agent_id": self.agent_id,
            "working_directory": str(self.working_dir) if self.working_dir else None,
            "files_created": self.files_created,
            "total_iterations": len(self.steps),
            "steps": [
                {
                    "iteration": step.iteration,
                    "thought": step.thought,
                    "action": step.action,
                    "action_input": step.action_input,
                    "observation": step.observation
                }
                for step in self.steps
            ],
            "completed": len(self.steps) < self.max_iterations and any(
                step.action == "final_answer" or not self.should_continue(step.observation or "") 
                for step in self.steps
            )
        }
        
        return result 