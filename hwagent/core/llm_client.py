"""
LLM Client for handling communication with OpenAI API.
Following Single Responsibility Principle - handles only LLM communication.
"""

from typing import Any
from openai import OpenAI
from hwagent.core.message_manager import MessageManager
from hwagent.core.streaming_handler import StreamingHandler
from hwagent.core.conversation_manager import ConversationManager


class AssistantMessageWrapper:
    """Wrapper for assistant message to maintain API compatibility."""
    
    def __init__(self, content: str, tool_calls: list[Any] | None = None):
        """
        Initialize assistant message wrapper.
        
        Args:
            content: Message content
            tool_calls: Tool calls if any
        """
        self.content = content
        self.tool_calls = tool_calls
    
    def model_dump(self, exclude_none: bool = True) -> dict[str, Any]:
        """
        Convert to dictionary format.
        
        Args:
            exclude_none: Whether to exclude None values
            
        Returns:
            Dictionary representation of message
        """
        result = {"role": "assistant", "content": self.content}
        
        if self.tool_calls and not exclude_none:
            result["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                } for tc in self.tool_calls
            ]
        
        return result


class LLMClient:
    """Handles communication with LLM API."""
    
    def __init__(self, client: OpenAI, model_name: str, message_manager: MessageManager, enable_streaming: bool = True):
        """
        Initialize LLM client.
        
        Args:
            client: OpenAI client instance
            model_name: Name of the model to use
            message_manager: Message manager for error messages
            enable_streaming: Whether to enable streaming responses
        """
        self.client = client
        self.model_name = model_name
        self.message_manager = message_manager
        self.enable_streaming = enable_streaming
        self.streaming_handler = StreamingHandler(message_manager)
    
    def get_llm_response(self, conversation_history: list[dict[str, Any]], tools_for_api: list[dict[str, Any]]) -> tuple[str, Any]:
        """
        Get response from LLM.
        
        Args:
            conversation_history: Conversation history
            tools_for_api: Tool definitions for API
            
        Returns:
            Tuple of (response_content, assistant_message_object)
        """
        completion_params = self._build_completion_params(conversation_history, tools_for_api)
        
        if self.enable_streaming:
            return self._handle_streaming_response(completion_params)
        else:
            return self._handle_non_streaming_response(completion_params)
    
    def _build_completion_params(self, conversation_history: list[dict[str, Any]], tools_for_api: list[dict[str, Any]]) -> dict[str, Any]:
        """Build completion parameters for API call."""
        params = {
            "model": self.model_name,
            "messages": conversation_history,
            "stream": self.enable_streaming
        }
        
        if tools_for_api:
            params["tools"] = tools_for_api
            params["tool_choice"] = "auto"
        
        return params
    
    def _handle_streaming_response(self, completion_params: dict[str, Any]) -> tuple[str, Any]:
        """Handle streaming response from API."""
        completion_stream = self.client.chat.completions.create(**completion_params)
        content, tool_calls = self.streaming_handler.process_streaming_response(completion_stream)
        
        assistant_message = AssistantMessageWrapper(content, tool_calls)
        return content, assistant_message
    
    def _handle_non_streaming_response(self, completion_params: dict[str, Any]) -> tuple[str, Any]:
        """Handle non-streaming response from API."""
        completion = self.client.chat.completions.create(**completion_params)
        
        if not (completion.choices and completion.choices[0].message):
            error_msg = self.message_manager.get_message("react_agent", "failed_to_get_model_response_error")
            raise RuntimeError(error_msg)
        
        assistant_message = completion.choices[0].message
        content = assistant_message.content or ""
        
        # Print response for non-streaming
        bot_prefix = self.message_manager.get_message("react_agent", "bot_prefix")
        print(f"{bot_prefix}{content}")
        
        return content, assistant_message
    
    def toggle_streaming(self, enabled: bool) -> None:
        """
        Toggle streaming mode.
        
        Args:
            enabled: Whether to enable streaming
        """
        self.enable_streaming = enabled 