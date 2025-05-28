"""
Refactored ReAct Agent following SOLID principles.
Breaking down the monolithic agent into focused, single-responsibility components.
"""

from typing import Any
from openai import OpenAI

from hwagent.tool_manager import ToolManager
from hwagent.core import (
    MessageManager, StreamingHandlerImpl, ResponseParser, 
    ConversationManagerImpl, ToolExecutor, LLMClient
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
        
        # Text-based tool call (warning case)
        elif parsed_response.has_tool_call():
            self.tool_executor.handle_text_based_tool_call(
                parsed_response.tool_call_name, conversation_manager
            )
            return None
        
        # Final answer
        elif parsed_response.has_final_answer():
            return parsed_response.final_answer
        
        # No clear action - handle accordingly
        else:
            return self._handle_no_action_response(assistant_message.content, conversation_manager)
    
    def _handle_no_action_response(self, content: str, conversation_manager: ConversationManagerImpl) -> None:
        """Handle response with no clear action."""
        if content.strip():
            # LLM provided text but no action
            print(self.display_manager.message_manager.get_message("react_agent", "bot_text_but_no_action_note"))
        else:
            # Empty response
            empty_msg = self.display_manager.message_manager.get_message("react_agent", "model_empty_response_note")
            system_note = self.display_manager.message_manager.get_message("react_agent", "model_empty_response_system_note")
            print(empty_msg)
            conversation_manager.add_system_note(system_note)
        
        return None
    
    def _handle_iteration_error(self, error: Exception, conversation_manager: ConversationManagerImpl) -> str:
        """Handle errors during iteration processing."""
        error_msg = self.display_manager.message_manager.format_message(
            "react_agent", "agent_processing_error", error=str(error)
        )
        print(error_msg)
        conversation_manager.add_system_note(f"[System Error: {error_msg}]")
        return error_msg


class ReActAgent:
    """
    Refactored ReAct Agent following SOLID principles.
    Each component has a single responsibility and focused methods.
    """
    
    MAX_ITERATIONS = 7
    
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
        
        # Process iterations
        for iteration in range(1, self.MAX_ITERATIONS + 1):
            result = self.iteration_processor.process_iteration(
                iteration, self.conversation_manager, tools_for_api
            )
            
            if result is not None:
                return result
        
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