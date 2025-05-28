"""
Refactored ReAct Agent following SOLID principles.
Breaking down the monolithic agent into focused, single-responsibility components.
"""

from typing import Any
from openai import OpenAI

from hwagent.tool_manager import ToolManager
from hwagent.core import (
    MessageManager, StreamingHandlerImpl, ResponseParser, 
    ConversationManagerImpl, ToolExecutor, LLMClient, Constants
)


class SystemPromptBuilder:
    """Builds system prompts for the agent. Following SRP."""
    
    def __init__(self, tool_manager: ToolManager, message_manager: MessageManager):
        """
        Initialize SystemPromptBuilder.
        
        Args:
            tool_manager: Tool manager for getting tool definitions
            message_manager: Message manager for prompt templates
        """
        self.tool_manager = tool_manager
        self.message_manager = message_manager
    
    def build_system_prompt(self, base_prompt: str, agent_prompts: dict[str, Any]) -> str:
        """
        Build complete system prompt.
        
        Args:
            base_prompt: Base system prompt from configuration
            agent_prompts: Agent prompt templates
            
        Returns:
            Complete system prompt string
        """
        tool_definitions = self.tool_manager.get_tool_definitions_for_prompt()
        
        # Get base addition template from agent prompts
        base_addition_template = agent_prompts.get("base_system_prompt_addition", "")
        
        return f"""{base_prompt}
{base_addition_template.format(tool_defs=tool_definitions)}

IMPORTANT: You maintain memory of our entire conversation. You can reference previous messages, files created earlier, and build upon previous work.
"""


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
        # API tool calls have priority
        if assistant_message.tool_calls:
            self.tool_executor.execute_api_tool_calls(assistant_message.tool_calls, conversation_manager)
            return None
        
        # Text-based tool call (warning case) - provide corrective feedback
        elif parsed_response.has_tool_call():
            self._handle_malformed_tool_call(parsed_response, conversation_manager)
            return None
        
        # Final answer
        elif parsed_response.has_final_answer():
            return parsed_response.final_answer
        
        # No clear action - handle accordingly
        else:
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
        if content.strip():
            # Check if this looks like a repetitive question or request for same information
            if self._is_repetitive_question(content, conversation_manager):
                # Try to make intelligent assumptions based on context
                return self._handle_repetitive_request(content, conversation_manager)
            
            # Check if this looks like a direct answer to the user's question
            # If the content seems to be answering the question directly, treat it as final answer
            if self._is_likely_final_answer(content):
                return content.strip()
            else:
                # LLM provided text but no action
                print(self.display_manager.message_manager.get_message("react_agent", "bot_text_but_no_action_note"))
                return None
        else:
            # Empty response
            empty_msg = self.display_manager.message_manager.get_message("react_agent", "model_empty_response_note")
            system_note = self.display_manager.message_manager.get_message("react_agent", "model_empty_response_system_note")
            print(empty_msg)
            conversation_manager.add_system_note(system_note)
            return ""  # Return empty string to indicate empty response
    
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
        
        # Build system prompt
        self.system_prompt_builder = SystemPromptBuilder(tool_manager, self.message_manager)
        system_prompt = self.system_prompt_builder.build_system_prompt(base_system_prompt, agent_prompts)
        
        # Initialize conversation
        self.conversation_manager.initialize_with_system_prompt(system_prompt)
        
        # Initialize iteration processor
        self.iteration_processor = IterationProcessor(
            self.llm_client, self.response_parser, self.tool_executor, self.display_manager
        )
    
    def process_user_request(self, user_input: str) -> str:
        """
        Process user request through ReAct loop.
        
        Args:
            user_input: User's input message
            
        Returns:
            Final response from agent
        """
        # Add user message to conversation
        self.conversation_manager.add_user_message(user_input)
        
        # Get tools for API
        tools_for_api = self.tool_manager.get_tools_for_api()
        
        # Process iterations with early termination logic
        consecutive_empty_responses = 0
        consecutive_errors = 0
        max_empty_responses = 3  # Allow up to 3 consecutive empty responses before terminating
        max_consecutive_errors = 5  # Allow up to 5 consecutive errors before terminating
        
        for iteration in range(1, Constants.MAX_REACT_ITERATIONS + 1):
            try:
                result = self.iteration_processor.process_iteration(
                    iteration, self.conversation_manager, tools_for_api
                )
                
                # Reset error counter on successful iteration
                consecutive_errors = 0
                
                if result is not None:
                    # Check if result is an actual answer or error message
                    if result.strip():
                        return result
                    else:
                        consecutive_empty_responses += 1
                else:
                    consecutive_empty_responses = 0  # Reset counter on successful tool execution
                
                # Early termination if too many consecutive empty responses
                if consecutive_empty_responses >= max_empty_responses:
                    early_term_msg = self.message_manager.get_message("react_agent", "early_termination_message")
                    print(early_term_msg)
                    self.conversation_manager.add_system_note(early_term_msg)
                    return early_term_msg
                    
            except Exception as e:
                consecutive_errors += 1
                consecutive_empty_responses = 0  # Don't count errors as empty responses
                
                error_msg = f"Error in iteration {iteration}: {str(e)}"
                print(error_msg)
                
                # Add helpful feedback for common errors
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
                    error_term_msg = self.message_manager.get_message("react_agent", "error_termination_message")
                    print(error_term_msg)
                    self.conversation_manager.add_system_note(error_term_msg)
                    return error_term_msg
        
        # Max iterations reached
        max_iter_msg = self.message_manager.get_message("react_agent", "max_iterations_reached_message")
        print(max_iter_msg)
        self.conversation_manager.add_system_note(max_iter_msg)
        return max_iter_msg
    
    def clear_context(self) -> None:
        """Clear conversation context but keep system prompt."""
        self.conversation_manager.clear_conversation()
        print(self.message_manager.get_message("react_agent", "context_cleared"))
    
    def get_context_summary(self) -> str:
        """Get summary of current conversation context."""
        return self.conversation_manager.get_context_summary()
    
    def set_streaming_enabled(self, enabled: bool) -> None:
        """Enable or disable streaming responses."""
        self.llm_client.toggle_streaming(enabled)
        
        if enabled:
            print(self.message_manager.get_message("react_agent", "streaming_enabled"))
        else:
            print(self.message_manager.get_message("react_agent", "streaming_disabled"))
    
    @property
    def enable_streaming(self) -> bool:
        """Get current streaming status."""
        return self.llm_client.enable_streaming
    
    @enable_streaming.setter
    def enable_streaming(self, value: bool) -> None:
        """Set streaming status."""
        self.set_streaming_enabled(value) 