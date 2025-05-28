"""
Tool Executor for handling tool execution in ReAct Agent.
Following Single Responsibility Principle - handles only tool execution logic.
"""

import json
from typing import Any, TYPE_CHECKING
from hwagent.core.message_manager import MessageManager
from hwagent.core.conversation_manager import ConversationManager

if TYPE_CHECKING:
    from hwagent.tool_manager import ToolManager


class ToolExecutor:
    """Executes tools and handles results."""
    
    def __init__(self, tool_manager: 'ToolManager', message_manager: MessageManager):
        """
        Initialize ToolExecutor.
        
        Args:
            tool_manager: Tool manager instance
            message_manager: Message manager for error messages
        """
        self.tool_manager = tool_manager
        self.message_manager = message_manager
    
    def execute_api_tool_calls(self, tool_calls: list[Any], conversation_manager: ConversationManager) -> None:
        """
        Execute API tool calls and add results to conversation.
        
        Args:
            tool_calls: List of tool call objects from OpenAI API
            conversation_manager: Conversation manager to add results
        """
        for tool_call in tool_calls:
            self._execute_single_api_tool_call(tool_call, conversation_manager)
    
    def _execute_single_api_tool_call(self, tool_call: Any, conversation_manager: ConversationManager) -> None:
        """
        Execute a single API tool call.
        
        Args:
            tool_call: Tool call object from OpenAI API
            conversation_manager: Conversation manager to add results
        """
        tool_call_id = tool_call.id
        tool_name = tool_call.function.name
        tool_args_json = tool_call.function.arguments
        
        print(self.message_manager.format_message(
            "react_agent", "executing_tool_call",
            tool_call_id=tool_call_id,
            tool_name=tool_name,
            args=tool_args_json
        ))
        
        # Parse tool arguments
        try:
            tool_params = json.loads(tool_args_json)
        except json.JSONDecodeError as e:
            error_msg = self.message_manager.format_message(
                "react_agent", "tool_args_decode_error", error=e
            )
            print(error_msg)
            
            error_content = self.message_manager.format_message(
                "react_agent", "failed_to_parse_tool_args_error",
                tool_name=tool_name, error=e, args=tool_args_json
            )
            conversation_manager.add_tool_result(tool_call_id, tool_name, error_content)
            return
        
        # Execute tool
        raw_output = self.tool_manager.execute_tool(tool_name, tool_params)
        print(self.message_manager.format_message(
            "react_agent", "raw_tool_output", output=raw_output
        ))
        
        # Format output for conversation
        formatted_output = self._format_tool_output(raw_output)
        print(self.message_manager.format_message(
            "react_agent", "formatted_tool_output", output=formatted_output
        ))
        
        # Add to conversation
        conversation_manager.add_tool_result(tool_call_id, tool_name, formatted_output)
    
    def handle_text_based_tool_call(self, tool_name: str, conversation_manager: ConversationManager) -> None:
        """
        Handle text-based tool call (warning case).
        
        Args:
            tool_name: Name of the tool from text parsing
            conversation_manager: Conversation manager to add warning
        """
        warning_msg = self.message_manager.format_message(
            "react_agent", "text_tool_call_warning", tool_name=tool_name
        )
        print(warning_msg)
        
        system_note = self.message_manager.format_message(
            "react_agent", "text_tool_call_system_note", tool_name=tool_name
        )
        conversation_manager.add_system_note(system_note)
    
    def _format_tool_output(self, raw_output: str) -> str:
        """
        Format tool output for conversation history.
        
        Args:
            raw_output: Raw output from tool manager
            
        Returns:
            Formatted output string
        """
        if raw_output.lower().startswith("error:"):
            error_detail = raw_output[len('error:'):].strip()
            return f"*error while calling tool: {error_detail}*"
        else:
            return raw_output