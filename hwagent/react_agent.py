"""
Refactored ReAct Agent following SOLID principles.
Breaking down the monolithic agent into focused, single-responsibility components.
"""

from typing import Any
from openai import OpenAI

from hwagent.tool_manager import ToolManager
from hwagent.core import (
    MessageManager, StreamingHandlerImpl, ResponseParser, 
    ConversationManagerImpl, ToolExecutor, LLMClient, Constants, 
    AgentConfig, get_agent_config
)


class SystemPromptBuilder:
    """Builds system prompts for the agent. Following SRP."""
    
    def __init__(self, tool_manager: ToolManager, message_manager: MessageManager, conversation_manager=None):
        """
        Initialize SystemPromptBuilder.
        
        Args:
            tool_manager: Tool manager for getting tool definitions
            message_manager: Message manager for prompt templates
            conversation_manager: Optional conversation manager for memory context
        """
        self.tool_manager = tool_manager
        self.message_manager = message_manager
        self.conversation_manager = conversation_manager
    
    def build_system_prompt(self, base_system_prompt: str, agent_prompts: dict[str, str]) -> str:
        """Build comprehensive system prompt with tools, iteration awareness, and memory context."""
        agent_config = get_agent_config()
        max_iterations = agent_config.get_max_iterations()
        
        # Get memory context if available
        memory_context = self._get_memory_context()
        
        # Add iteration awareness to the system prompt
        iteration_guidance = f"""
ITERATION MANAGEMENT:
- You have a maximum of {max_iterations} iterations to complete tasks
- Use iterations efficiently - aim to complete tasks in minimum steps
- If you need multiple steps, plan them carefully to stay within limits
- Always check your work before providing final answers
- If approaching iteration limit, prioritize the most important aspects of the task

EFFICIENCY GUIDELINES:
- Combine related operations when possible
- Verify results immediately after tool execution
- Provide clear, complete answers to avoid follow-up questions
- If a task seems too complex, break it into essential components only
"""

        # Add memory context section
        memory_section = ""
        if memory_context:
            memory_section = f"""
CONVERSATION MEMORY & CONTEXT:
{memory_context}

MEMORY USAGE GUIDELINES:
- Reference previous successful solutions when facing similar tasks
- Build upon previous work rather than starting from scratch
- Remember user preferences and adapt your approach accordingly
- Learn from past errors and avoid repeating them
- Use context from previous sessions to provide continuity
"""
        
        # Build the complete system prompt
        tools_section = f"AVAILABLE TOOLS:\n{self._format_tools_for_prompt()}\n"
        
        system_prompt_parts = [
            base_system_prompt,
            iteration_guidance,
            memory_section,
            tools_section
        ]
        
        # Add any additional prompts
        for key, prompt_text in agent_prompts.items():
            if key != "base" and prompt_text:
                system_prompt_parts.append(f"{key.upper()}:\n{prompt_text}\n")
        
        return "\n".join(filter(None, system_prompt_parts))

    def _get_memory_context(self) -> str:
        """Get memory context from conversation manager."""
        if not self.conversation_manager:
            return ""
        
        try:
            # Get enhanced context with memory
            context_data = self.conversation_manager.get_enhanced_context_summary()
            
            if not context_data:
                return ""
            
            context_lines = []
            
            # Current session context - more detailed information
            session_context = context_data.get('session_context', {})
            if session_context:
                total_exchanges = session_context.get('total_exchanges', 0)
                if total_exchanges > 0:
                    context_lines.append(f"📋 Current Session: {total_exchanges} exchanges completed")
                    
                    # Task types in current session
                    task_types = session_context.get('task_types', [])
                    if task_types:
                        task_str = ", ".join(task_types)
                        context_lines.append(f"🎯 Session Task Types: {task_str}")
                    
                    # Success rate
                    success_rate = session_context.get('success_rate', 0)
                    context_lines.append(f"✅ Session Success Rate: {success_rate:.1%}")
                    
                    # Recent tools used
                    tools_used = session_context.get('tools_used', [])
                    if tools_used:
                        tools_str = ", ".join(tools_used[:8])  # Limit to 8 tools
                        context_lines.append(f"🔧 Session Tools Used: {tools_str}")
            
            # Historical context - patterns and insights
            historical_context = context_data.get('historical_context', {})
            if historical_context:
                total_sessions = historical_context.get('total_sessions', 0)
                if total_sessions > 0:
                    context_lines.append(f"📈 Historical: {total_sessions} recent sessions")
                    
                    # Frequent task patterns
                    frequent_tasks = historical_context.get('frequent_tasks', [])
                    if frequent_tasks:
                        # frequent_tasks is list of (task_type, count) tuples
                        task_summary = []
                        for task_info in frequent_tasks[:3]:  # Top 3 task types
                            if isinstance(task_info, (list, tuple)) and len(task_info) >= 2:
                                task_type, count = task_info[0], task_info[1]
                                task_summary.append(f"{task_type}({count})")
                            elif isinstance(task_info, str):
                                task_summary.append(task_info)
                        
                        if task_summary:
                            context_lines.append(f"🔄 Frequent Tasks: {', '.join(task_summary)}")
            
            # Context insights if available
            insights = context_data.get('context_insights', [])
            if insights:
                insights_str = "; ".join(insights[:2])  # Limit to 2 key insights
                context_lines.append(f"💡 Key Insights: {insights_str}")
            
            # Recent patterns from session
            session_patterns = session_context.get('recent_patterns', [])
            if session_patterns:
                patterns_str = "; ".join(session_patterns[:2])  # Limit to 2 patterns
                context_lines.append(f"🎨 Recent Patterns: {patterns_str}")
            
            # Memory availability status
            memory_available = context_data.get('persistent_memory_available', False)
            if memory_available:
                context_lines.append("🧠 Persistent Memory: Active & Learning")
            
            # Add conversation continuity instruction
            if context_lines:
                context_lines.insert(0, "🔗 CONVERSATION CONTINUITY:")
                context_lines.append("")
                context_lines.append("MEMORY USAGE INSTRUCTIONS:")
                context_lines.append("- Reference previous work when relevant to current task")
                context_lines.append("- Build upon established concepts and solutions") 
                context_lines.append("- Avoid re-explaining concepts already covered in this session")
                context_lines.append("- Maintain consistent style and approach established in session")
                context_lines.append("- Use memory tool if you need to search for specific past interactions")
            
            return "\n".join(context_lines) if context_lines else ""
            
        except Exception as e:
            # Don't fail if memory context retrieval fails
            print(f"Warning: Could not retrieve memory context: {e}")
            return ""

    def _format_tools_for_prompt(self) -> str:
        """Format tools for display in the system prompt."""
        tool_definitions = self.tool_manager.get_tool_definitions_for_prompt()
        formatted_tools = "\n".join(f"- {tool}" for tool in tool_definitions)
        return formatted_tools


class ResponseDisplayManager:
    """Manages response display and logging. Following SRP."""
    
    def __init__(self, message_manager: MessageManager):
        """
        Initialize ResponseDisplayManager.
        
        Args:
            message_manager: Message manager for display messages
        """
        self.message_manager = message_manager
    
    def print_iteration_header(self, iteration: int) -> None:
        """Print iteration header."""
        header = self.message_manager.format_message(
            "react_agent", "iteration_header", iteration=iteration
        )
        print(header)
    
    def print_debug_info(self, assistant_content: str, tool_calls: list[Any], streaming_enabled: bool) -> None:
        """Print debug information about LLM response."""
        if not streaming_enabled:
            header = self.message_manager.get_message("react_agent", "llm_raw_output_header")
            print(f"{header}\n{assistant_content}")
        
        if tool_calls:
            header = self.message_manager.format_message(
                "react_agent", "llm_tool_calls_header", tool_calls=tool_calls
            )
            print(header)
    
    def print_parsed_components(self, thought: str | None, plan: list[str] | None, final_answer: str | None) -> None:
        """Print parsed response components."""
        if thought:
            print(self.message_manager.format_message("react_agent", "thought_header", thought=thought))
        
        if plan:
            print(self.message_manager.format_message("react_agent", "plan_header", plan=plan))
        
        if final_answer:
            print(self.message_manager.format_message("react_agent", "final_answer_header", final_answer=final_answer))


class IterationProcessor:
    """Processes single iterations of the ReAct loop. Following SRP."""
    
    def __init__(self, llm_client: LLMClient, response_parser: ResponseParser, 
                 tool_executor: ToolExecutor, display_manager: ResponseDisplayManager):
        """
        Initialize IterationProcessor.
        
        Args:
            llm_client: LLM client for API communication
            response_parser: Parser for LLM responses
            tool_executor: Tool executor for running tools
            display_manager: Display manager for output
        """
        self.llm_client = llm_client
        self.response_parser = response_parser
        self.tool_executor = tool_executor
        self.display_manager = display_manager
    
    def process_iteration(self, iteration: int, conversation_manager: ConversationManagerImpl, 
                         tools_for_api: list[dict[str, Any]]) -> str | None:
        """
        Process a single iteration of the ReAct loop.
        
        Args:
            iteration: Current iteration number
            conversation_manager: Conversation manager
            tools_for_api: Tool definitions for API
            
        Returns:
            Final answer if found, None to continue iterations
        """
        self.display_manager.print_iteration_header(iteration)
        
        try:
            # Get LLM response
            assistant_content, assistant_message = self.llm_client.get_llm_response(
                conversation_manager.get_conversation_history(),
                tools_for_api
            )
            
            # Add to conversation
            conversation_manager.add_assistant_message(assistant_message)
            
            # Display debug info
            self.display_manager.print_debug_info(
                assistant_content, 
                assistant_message.tool_calls,
                self.llm_client.enable_streaming
            )
            
            # Parse response
            parsed_response = self.response_parser.parse_llm_response(assistant_content)
            
            # Display parsed components
            self.display_manager.print_parsed_components(
                parsed_response.thought,
                parsed_response.plan,
                parsed_response.final_answer
            )
            
            # Handle response based on type
            return self._handle_parsed_response(
                assistant_message, parsed_response, conversation_manager
            )
            
        except Exception as e:
            return self._handle_iteration_error(e, conversation_manager)
    
    def _handle_parsed_response(self, assistant_message: Any, parsed_response: Any, 
                               conversation_manager: ConversationManagerImpl) -> str | None:
        """Handle parsed response based on its type."""
        agent_config = get_agent_config()
        debug_enabled = agent_config.is_debug_enabled()
        tool_call_logging = agent_config.is_tool_call_logging_enabled()
        
        if debug_enabled:
            print(f"[DEBUG] IterationProcessor: Handling parsed response")
            print(f"[DEBUG] IterationProcessor: Assistant has tool calls: {bool(assistant_message.tool_calls)}")
            print(f"[DEBUG] IterationProcessor: Parsed has tool call: {parsed_response.has_tool_call()}")
            print(f"[DEBUG] IterationProcessor: Parsed has final answer: {parsed_response.has_final_answer()}")
            print(f"[DEBUG] IterationProcessor: Assistant content length: {len(assistant_message.content) if assistant_message.content else 0}")
        
        # API tool calls have priority
        if assistant_message.tool_calls:
            if debug_enabled and tool_call_logging:
                print(f"[DEBUG] IterationProcessor: Executing API tool calls")
            self.tool_executor.execute_api_tool_calls(assistant_message.tool_calls, conversation_manager)
            return None
        
        # Text-based tool call (warning case) - provide corrective feedback
        elif parsed_response.has_tool_call():
            if debug_enabled and tool_call_logging:
                print(f"[DEBUG] IterationProcessor: Handling malformed tool call: {parsed_response.tool_call_name}")
            self._handle_malformed_tool_call(parsed_response, conversation_manager)
            return None
        
        # Final answer
        elif parsed_response.has_final_answer():
            if debug_enabled:
                print(f"[DEBUG] IterationProcessor: Returning final answer")
            return parsed_response.final_answer
        
        # No clear action - handle accordingly
        else:
            if debug_enabled:
                print(f"[DEBUG] IterationProcessor: No clear action, handling no action response")
            return self._handle_no_action_response(assistant_message.content, conversation_manager)
    
    def _handle_malformed_tool_call(self, parsed_response: Any, conversation_manager: ConversationManagerImpl) -> None:
        """Handle malformed tool calls with corrective feedback."""
        tool_name = parsed_response.tool_call_name
        
        # Add detailed corrective feedback to help the agent fix the tool call
        corrective_feedback = self.message_manager.format_message(
            "react_agent", "malformed_tool_call_feedback",
            tool_name=tool_name
        )
        print(corrective_feedback)
        conversation_manager.add_system_note(corrective_feedback)
    
    def _handle_no_action_response(self, content: str, conversation_manager: ConversationManagerImpl) -> str | None:
        """Handle response with no clear action."""
        agent_config = get_agent_config()
        debug_enabled = agent_config.is_debug_enabled()
        empty_response_logging = agent_config.is_empty_response_logging_enabled()
        
        if debug_enabled and empty_response_logging:
            print(f"[DEBUG] IterationProcessor: _handle_no_action_response called")
            print(f"[DEBUG] IterationProcessor: Content: {repr(content)}")
            print(f"[DEBUG] IterationProcessor: Content stripped: {repr(content.strip()) if content else 'None'}")
        
        if content.strip():
            if debug_enabled and empty_response_logging:
                print(f"[DEBUG] IterationProcessor: Content is not empty, checking for repetitive question")
            
            # Check if this looks like a repetitive question or request for same information
            if self._is_repetitive_question(content, conversation_manager):
                if debug_enabled and empty_response_logging:
                    print(f"[DEBUG] IterationProcessor: Detected repetitive question, handling")
                # Try to make intelligent assumptions based on context
                return self._handle_repetitive_request(content, conversation_manager)
            
            # Check if this looks like a direct answer to the user's question
            # If the content seems to be answering the question directly, treat it as final answer
            if self._is_likely_final_answer(content):
                if debug_enabled and empty_response_logging:
                    print(f"[DEBUG] IterationProcessor: Content looks like final answer")
                return content.strip()
            else:
                # LLM provided text but no action
                if debug_enabled and empty_response_logging:
                    print(f"[DEBUG] IterationProcessor: LLM provided text but no action")
                print(self.display_manager.message_manager.get_message("react_agent", "bot_text_but_no_action_note"))
                return None
        else:
            # Empty response - add system note but don't terminate
            if debug_enabled and empty_response_logging:
                print(f"[DEBUG] IterationProcessor: Empty response detected")
            empty_msg = self.display_manager.message_manager.get_message("react_agent", "model_empty_response_note")
            system_note = self.display_manager.message_manager.get_message("react_agent", "model_empty_response_system_note")
            print(empty_msg)
            conversation_manager.add_system_note(system_note)
            return None  # Return None to continue iterations instead of terminating
    
    def _is_repetitive_question(self, content: str, conversation_manager: ConversationManagerImpl) -> bool:
        """Check if the agent is asking the same question repeatedly."""
        content_lower = content.lower()
        
        # Get recent assistant messages
        history = conversation_manager.get_conversation_history()
        recent_assistant_messages = [
            msg['content'] for msg in history[-6:] 
            if msg.get('role') == 'assistant' and msg.get('content')
        ]
        
        # Check for repetitive patterns
        repetitive_patterns = [
            "what should the name", "filename", "content you want", 
            "provide both", "tell me two things", "need you to"
        ]
        
        current_has_pattern = any(pattern in content_lower for pattern in repetitive_patterns)
        
        if current_has_pattern and len(recent_assistant_messages) >= 3:
            # Count how many recent messages have similar patterns
            similar_count = sum(
                1 for msg in recent_assistant_messages 
                if any(pattern in msg.lower() for pattern in repetitive_patterns)
            )
            return similar_count >= 3
        
        return False
    
    def _handle_repetitive_request(self, content: str, conversation_manager: ConversationManagerImpl) -> str | None:
        """Handle repetitive requests by making intelligent assumptions."""
        history = conversation_manager.get_conversation_history()
        
        # Look for the original user request
        user_request = None
        for msg in reversed(history):
            if msg.get('role') == 'user':
                user_request = msg.get('content', '')
                break
        
        if not user_request:
            return "I couldn't find your original request. Please provide more specific instructions."
        
        # Check if it's a file creation request
        if 'file' in user_request.lower() or 'write' in user_request.lower():
            return self._handle_file_creation_with_context(user_request, history)
        
        # For other repetitive requests, provide a helpful response
        return f"I notice I've been asking the same question repeatedly. Based on your request '{user_request}', let me try to proceed with reasonable assumptions or provide a more specific response."
    
    def _handle_file_creation_with_context(self, user_request: str, history: list) -> str | None:
        """Handle file creation using context from conversation."""
        # Look for content in the conversation that could be written to a file
        potential_content = ""
        
        # Check for large text blocks in recent messages
        for msg in reversed(history[-10:]):  # Look at last 10 messages
            if msg.get('role') == 'user' and msg.get('content'):
                content = msg['content']
                # If user message is long, it might be content to write
                if len(content) > 100:
                    potential_content = content
                    break
        
        # If no substantial content found, look for assistant responses that might be research
        if not potential_content:
            for msg in reversed(history[-10:]):
                if msg.get('role') == 'assistant' and msg.get('content'):
                    content = msg['content']
                    # Look for research-like content
                    if any(keyword in content.lower() for keyword in ['research', 'hypothesis', 'markdown', 'efficiency', 'data']):
                        if len(content) > 200:
                            potential_content = content
                            break
        
        if potential_content:
            # Create a reasonable filename based on content
            filename = self._generate_filename_from_content(potential_content)
            
            # Use the create_file tool with the found content
            try:
                result = self.tool_manager.execute_tool('create_file', {
                    'filepath': filename,
                    'content': potential_content
                })
                return f"I found substantial content in our conversation and wrote it to {filename}. {result}"
            except Exception as e:
                return f"I attempted to create a file with the content from our conversation, but encountered an error: {e}"
        
        # If no content found, create a simple example file
        default_filename = "user_request.txt"
        default_content = f"User request: {user_request}\nTimestamp: {self._get_current_time()}"
        
        try:
            result = self.tool_manager.execute_tool('create_file', {
                'filepath': default_filename,
                'content': default_content
            })
            return f"I created {default_filename} with your request. {result}"
        except Exception as e:
            return f"I tried to create a default file but encountered an error: {e}"
    
    def _generate_filename_from_content(self, content: str) -> str:
        """Generate a reasonable filename based on content."""
        content_lower = content.lower()
        
        # Check for specific content types
        if 'market efficiency' in content_lower or 'emh' in content_lower:
            return "market_efficiency_research.md"
        elif 'research' in content_lower and 'hypothesis' in content_lower:
            return "research_outline.md"
        elif any(keyword in content_lower for keyword in ['python', 'def ', 'import ', 'class ']):
            return "script.py"
        elif 'markdown' in content_lower or '##' in content:
            return "document.md"
        elif 'data' in content_lower or 'analysis' in content_lower:
            return "data_analysis.txt"
        else:
            return "content.txt"
    
    def _get_current_time(self) -> str:
        """Get current timestamp as string."""
        import datetime
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def _is_likely_final_answer(self, content: str) -> bool:
        """
        Determine if content looks like a final answer.
        
        Args:
            content: Response content to analyze
            
        Returns:
            True if content looks like a final answer
        """
        content_lower = content.lower().strip()
        
        # Skip if it contains typical reasoning patterns
        reasoning_indicators = [
            "i need to", "i should", "let me", "i'll", "i will",
            "first i", "then i", "next i", "step", "plan:",
            "thought:", "tool_call:"
        ]
        
        if any(indicator in content_lower for indicator in reasoning_indicators):
            return False
        
        # Check if it's a direct informational response
        answer_indicators = [
            "there are", "these are", "the files are", "here are",
            "the answer is", "the result is", "it contains",
            "your workspace", "in the workspace", "files in"
        ]
        
        if any(indicator in content_lower for indicator in answer_indicators):
            return True
        
        # If content is relatively short and declarative, likely an answer
        sentences = content.split('.')
        if len(sentences) <= 3 and len(content) < 200:
            return True
        
        return False
    
    def _handle_iteration_error(self, error: Exception, conversation_manager: ConversationManagerImpl) -> str:
        """Handle errors during iteration processing."""
        error_msg = str(error)
        
        # Provide specific feedback for common error types
        if "function response parts" in error_msg.lower():
            specific_msg = self.display_manager.message_manager.get_message(
                "react_agent", "function_parts_error_recovery"
            )
            print(specific_msg)
            conversation_manager.add_system_note(specific_msg)
            return None  # Don't terminate, let agent retry
        
        elif "tool_call" in error_msg.lower() or "json" in error_msg.lower():
            specific_msg = self.display_manager.message_manager.get_message(
                "react_agent", "tool_call_error_recovery"
            )
            print(specific_msg)
            conversation_manager.add_system_note(specific_msg)
            return None  # Don't terminate, let agent retry
        
        else:
            # Generic error handling
            formatted_error_msg = self.display_manager.message_manager.format_message(
                "react_agent", "agent_processing_error", error=error_msg
            )
            print(formatted_error_msg)
            conversation_manager.add_system_note(f"[System Error: {formatted_error_msg}]")
            return None  # Don't terminate on first error, let agent retry


class ReActAgent:
    """
    Refactored ReAct Agent following SOLID principles.
    Each component has a single responsibility and focused methods.
    """
    
    def __init__(self, client: OpenAI, model_name: str, tool_manager: ToolManager, 
                 base_system_prompt: str, agent_prompts: dict[str, Any], enable_streaming: bool = True):
        """
        Initialize ReAct Agent with dependency injection.
        
        Args:
            client: OpenAI client
            model_name: Model name to use
            tool_manager: Tool manager instance
            base_system_prompt: Base system prompt
            agent_prompts: Agent prompt templates
            enable_streaming: Whether to enable streaming
        """
        self.tool_manager = tool_manager
        
        # Initialize core components
        self.message_manager = MessageManager()
        self.conversation_manager = ConversationManagerImpl(self.message_manager)
        self.llm_client = LLMClient(client, model_name, self.message_manager, enable_streaming)
        
        # Initialize specialized components
        self.response_parser = ResponseParser(self.message_manager)
        self.tool_executor = ToolExecutor(tool_manager, self.message_manager)
        self.display_manager = ResponseDisplayManager(self.message_manager)
        
        # Build system prompt with memory context
        self.system_prompt_builder = SystemPromptBuilder(tool_manager, self.message_manager, self.conversation_manager)
        
        # Store base prompt and agent prompts for dynamic system prompt building
        self.base_system_prompt = base_system_prompt
        self.agent_prompts = agent_prompts
        
        # Build initial system prompt (will be updated with memory context for each request)
        initial_system_prompt = self.system_prompt_builder.build_system_prompt(base_system_prompt, agent_prompts)
        
        # Initialize conversation
        self.conversation_manager.initialize_with_system_prompt(initial_system_prompt)
        
        # Initialize iteration processor
        self.iteration_processor = IterationProcessor(
            self.llm_client, self.response_parser, self.tool_executor, self.display_manager
        )
    
    def _is_high_confidence_result(self, result: str) -> bool:
        """Check if result indicates high confidence completion."""
        if not result or len(result.strip()) < 10:
            return False
        
        # High confidence indicators
        confidence_indicators = [
            "successfully", "completed", "created", "generated", "compiled",
            "executed", "finished", "done", "ready", "available"
        ]
        
        # Check for completion phrases
        completion_phrases = [
            "task completed", "file created", "script executed", "compilation successful",
            "pdf generated", "graph plotted", "document ready"
        ]
        
        result_lower = result.lower()
        
        # Check for confidence indicators
        confidence_score = sum(1 for indicator in confidence_indicators if indicator in result_lower)
        
        # Check for completion phrases (higher weight)
        completion_score = sum(2 for phrase in completion_phrases if phrase in result_lower)
        
        # High confidence if we have multiple indicators or completion phrases
        total_score = confidence_score + completion_score
        return total_score >= 3
    
    def _enhance_final_answer_with_files(self, final_answer: str) -> str:
        """
        Enhance final answer with information about created files.
        
        Args:
            final_answer: Original final answer from agent
            
        Returns:
            Enhanced final answer with file information
        """
        try:
            # Get list of files from tool manager - this returns a string, not a ToolExecutionResult
            list_result_str = self.tool_manager.execute_tool('list_files', {})
            
            # Parse the result string to check if it contains file information
            if not list_result_str.startswith("Error:") and "items" in list_result_str:
                # Try to extract file information from the string result
                # This is a simplified approach - we could use regex or JSON parsing
                # For now, just add a simple file count enhancement
                files_section = f"\n\n**📁 Файлы в рабочей директории:**\nВыполните команду list_files для просмотра созданных файлов."
                return final_answer + files_section
                
        except Exception as e:
            # Don't fail if file listing fails - just return original answer
            print(f"Warning: Could not enhance answer with file info: {e}")
        
        return final_answer

    def process_user_request(self, user_input: str) -> str:
        """
        Process user request through ReAct loop.
        
        Args:
            user_input: User's input message
            
        Returns:
            Final response from agent
        """
        # Update system prompt with current memory context
        updated_system_prompt = self.build_system_prompt(user_input)
        
        # Update the conversation with the new system prompt
        conversation_history = self.conversation_manager.get_conversation_history()
        if conversation_history and conversation_history[0]["role"] == "system":
            # Replace the existing system prompt
            conversation_history[0]["content"] = updated_system_prompt
        else:
            # Insert system prompt at the beginning
            conversation_history.insert(0, {"role": "system", "content": updated_system_prompt})
        
        # Add user message to conversation
        self.conversation_manager.add_user_message(user_input)
        
        # Get tools for API
        tools_for_api = self.tool_manager.get_tools_for_api()
        
        # Get configuration settings
        agent_config = get_agent_config()
        
        # Process iterations with early termination logic
        consecutive_empty_responses = 0
        consecutive_errors = 0
        total_empty_responses = 0
        max_empty_responses = agent_config.get_max_empty_responses()
        max_consecutive_errors = agent_config.get_max_consecutive_errors()
        max_total_empty_responses = agent_config.get_max_total_empty_responses()
        max_iterations = agent_config.get_max_iterations()
        
        final_response = None
        success = True
        error_message = None
        
        for iteration in range(1, max_iterations + 1):
            agent_config = get_agent_config()
            debug_enabled = agent_config.is_debug_enabled()
            verbose_iteration = agent_config.is_verbose_iteration_enabled()
            
            # Smart completion checks
            warning_threshold = int(max_iterations * agent_config.get_iteration_warning_threshold())
            is_final_attempt = (iteration == max_iterations)
            should_warn = (iteration >= warning_threshold)
            
            if debug_enabled and verbose_iteration:
                print(f"[DEBUG] ReActAgent: Starting iteration {iteration}/{max_iterations}")
                print(f"[DEBUG] ReActAgent: consecutive_empty={consecutive_empty_responses}, total_empty={total_empty_responses}, consecutive_errors={consecutive_errors}")
            
            # Add iteration awareness to conversation if enabled
            if agent_config.should_show_remaining_iterations():
                if is_final_attempt:
                    warning_msg = agent_config.get_final_attempt_warning(iteration, max_iterations)
                    self.conversation_manager.add_system_note(warning_msg)
                elif should_warn:
                    warning_msg = agent_config.get_iteration_warning_message(iteration, max_iterations)
                    self.conversation_manager.add_system_note(warning_msg)
            
            try:
                result = self.iteration_processor.process_iteration(
                    iteration, self.conversation_manager, tools_for_api
                )
                
                if debug_enabled and verbose_iteration:
                    print(f"[DEBUG] ReActAgent: Iteration {iteration} result: {repr(result[:100] if result else 'None')}")
                
                # Reset error counter on successful iteration
                consecutive_errors = 0
                
                if result is not None:
                    # Check if result is an actual answer or error message
                    if result.strip():
                        if debug_enabled and verbose_iteration:
                            print(f"[DEBUG] ReActAgent: Got non-empty result, checking confidence")
                        
                        # Always return non-empty results with enhancement
                        enhanced_result = self._enhance_final_answer_with_files(result)
                        
                        # Check for high confidence early completion
                        if agent_config.is_smart_completion_enabled() and self._is_high_confidence_result(result):
                            if debug_enabled and verbose_iteration:
                                print(f"[DEBUG] ReActAgent: High confidence result detected, completing early")
                        elif iteration < max_iterations:
                            if debug_enabled and verbose_iteration:
                                print(f"[DEBUG] ReActAgent: Moderate confidence, but returning result anyway")
                        else:
                            if debug_enabled and verbose_iteration:
                                print(f"[DEBUG] ReActAgent: Final iteration, returning result")
                        
                        final_response = enhanced_result
                        success = True
                        break
                    else:
                        if debug_enabled and verbose_iteration:
                            print(f"[DEBUG] ReActAgent: Got empty result, incrementing counters")
                        consecutive_empty_responses += 1
                        total_empty_responses += 1
                else:
                    if debug_enabled and verbose_iteration:
                        print(f"[DEBUG] ReActAgent: Got None result, incrementing counters")
                    # Reset consecutive counter but continue tracking total
                    consecutive_empty_responses += 1
                    total_empty_responses += 1
                
                # Check termination conditions
                if consecutive_empty_responses >= agent_config.get_max_empty_responses():
                    empty_term_msg = agent_config.get_message("too_many_empty_responses")
                    print(empty_term_msg)
                    self.conversation_manager.add_system_note(empty_term_msg)
                    final_response = empty_term_msg
                    success = False
                    error_message = "Too many empty responses"
                    break
                
                if total_empty_responses >= agent_config.get_max_total_empty_responses():
                    total_empty_msg = agent_config.get_message("too_many_total_empty_responses")
                    print(total_empty_msg)
                    self.conversation_manager.add_system_note(total_empty_msg)
                    final_response = total_empty_msg
                    success = False
                    error_message = "Too many total empty responses"
                    break
                
                if consecutive_errors >= agent_config.get_max_consecutive_errors():
                    error_term_msg = agent_config.get_message("too_many_consecutive_errors")
                    print(error_term_msg)
                    self.conversation_manager.add_system_note(error_term_msg)
                    final_response = error_term_msg
                    success = False
                    error_message = "Too many consecutive errors"
                    break
                    
            except Exception as e:
                consecutive_errors += 1
                consecutive_empty_responses = 0  # Don't count errors as empty responses
                
                error_msg = f"Error in iteration {iteration}: {str(e)}"
                print(error_msg)
                
                # Only add recovery messages for the first few errors to avoid spam
                if consecutive_errors <= 2:
                    if "function response parts" in str(e).lower():
                        recovery_msg = self.message_manager.get_message("react_agent", "function_parts_error_recovery")
                        self.conversation_manager.add_system_note(recovery_msg)
                        print(recovery_msg)
                    elif "tool_call" in str(e).lower():
                        tool_error_msg = self.message_manager.get_message("react_agent", "tool_call_error_recovery")
                        self.conversation_manager.add_system_note(tool_error_msg)
                        print(tool_error_msg)
                
                # Early termination if too many consecutive errors
                if consecutive_errors >= max_consecutive_errors:
                    error_term_msg = agent_config.get_message("too_many_consecutive_errors")
                    print(error_term_msg)
                    final_response = error_term_msg
                    success = False
                    error_message = f"Consecutive errors: {str(e)}"
                    break
        
        # If we've exhausted all iterations without a satisfactory result and haven't set final_response
        if final_response is None:
            if agent_config.is_smart_completion_enabled():
                final_response = agent_config.get_polite_completion_request()
            else:
                final_response = agent_config.get_message("max_iterations_reached")
            success = False
            error_message = "Max iterations reached"
        
        # ✅ SAVE TO PERSISTENT MEMORY - Critical for complete conversation memory
        try:
            # Determine task type from user input
            task_type = self._determine_task_type(user_input)
            
            # Complete conversation turn and save to persistent memory
            if hasattr(self.conversation_manager, 'complete_conversation_turn'):
                self.conversation_manager.complete_conversation_turn(
                    agent_response=final_response,
                    task_type=task_type,
                    success=success,
                    error_message=error_message
                )
        except Exception as e:
            # Don't fail the response if memory saving fails, just log
            print(f"Warning: Could not save conversation to memory: {e}")
        
        return final_response
    
    def _determine_task_type(self, user_input: str) -> str:
        """Determine task type from user input for memory categorization."""
        user_input_lower = user_input.lower()
        
        # Check for mathematical/technical keywords
        if any(keyword in user_input_lower for keyword in 
               ['calculus', 'derivative', 'integral', 'matrix', 'equation', 'solve', 'calculate', 
                'математика', 'интеграл', 'производная', 'уравнение', 'вычисли', 'реши']):
            return "mathematics"
        
        # Check for programming/coding keywords
        if any(keyword in user_input_lower for keyword in 
               ['code', 'program', 'python', 'javascript', 'algorithm', 'function',
                'код', 'программа', 'алгоритм', 'функция']):
            return "programming"
        
        # Check for physics keywords
        if any(keyword in user_input_lower for keyword in 
               ['physics', 'force', 'energy', 'momentum', 'velocity', 'acceleration',
                'физика', 'сила', 'энергия', 'скорость', 'ускорение']):
            return "physics"
        
        # Check for document creation keywords
        if any(keyword in user_input_lower for keyword in 
               ['create document', 'write report', 'latex', 'pdf', 'document',
                'создай документ', 'напиши отчет', 'документ']):
            return "document_creation"
        
        # Check for data analysis keywords
        if any(keyword in user_input_lower for keyword in 
               ['analyze', 'data', 'chart', 'graph', 'plot', 'statistics',
                'анализ', 'данные', 'график', 'диаграмма', 'статистика']):
            return "data_analysis"
        
        # Default to general
        return "general"
    
    def clear_context(self) -> None:
        """Clear conversation context but keep system prompt."""
        self.conversation_manager.clear_conversation()
        agent_config = get_agent_config()
        print(agent_config.get_message("context_cleared"))
    
    def get_context_summary(self) -> str:
        """Get summary of current conversation context."""
        return self.conversation_manager.get_context_summary()
    
    def set_streaming_enabled(self, enabled: bool) -> None:
        """Enable or disable streaming responses."""
        self.llm_client.toggle_streaming(enabled)
        
        agent_config = get_agent_config()
        if enabled:
            print(agent_config.get_message("streaming_enabled"))
        else:
            print(agent_config.get_message("streaming_disabled"))
    
    @property
    def enable_streaming(self) -> bool:
        """Get current streaming status."""
        return self.llm_client.enable_streaming
    
    @enable_streaming.setter
    def enable_streaming(self, value: bool) -> None:
        """Set streaming status."""
        self.set_streaming_enabled(value)

    def build_system_prompt(self, user_query: str) -> str:
        """Build system prompt with memory context"""
        # Get base system prompt
        base_prompt = self.system_prompt_builder.build_system_prompt(self.base_system_prompt, self.agent_prompts)
        
        # Get memory context from conversation manager
        memory_context = ""
        if hasattr(self.conversation_manager, 'get_conversation_context_for_prompt'):
            memory_context = self.conversation_manager.get_conversation_context_for_prompt()
        
        # Inject memory context into system prompt if available
        if memory_context:
            # Find a good place to inject memory context (after the memory section)
            memory_injection_point = base_prompt.find("**MEMORY-POWERED RESPONSE STRUCTURE:**")
            if memory_injection_point != -1:
                # Find the end of the memory section
                next_section = base_prompt.find("**🚨🔥 CRITICAL:", memory_injection_point)
                if next_section != -1:
                    # Inject memory context before the next major section
                    injection_text = f"\n\n{memory_context}\n"
                    base_prompt = base_prompt[:next_section] + injection_text + base_prompt[next_section:]
                else:
                    # Fallback: append to the end of memory section
                    base_prompt = base_prompt + f"\n\n{memory_context}\n"
            else:
                # Fallback: append at the beginning after the title
                title_end = base_prompt.find("**🧠 COMPLETE CONVERSATION MEMORY SYSTEM 🧠**")
                if title_end != -1:
                    title_end = base_prompt.find("\n", title_end) + 1
                    injection_text = f"\n{memory_context}\n"
                    base_prompt = base_prompt[:title_end] + injection_text + base_prompt[title_end:]
        
        return base_prompt 