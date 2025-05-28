"""
Streaming Response Handler for OpenAI API.
Following Single Responsibility Principle - handles only streaming response processing.
"""

from typing import Any
from hwagent.core.message_manager import MessageManager


class ToolCallBuffer:
    """Manages tool call data during streaming."""
    
    def __init__(self):
        self.buffer: dict[int, dict[str, Any]] = {}
    
    def update_tool_call(self, index: int, tool_call_delta: Any) -> None:
        """Update tool call data with delta information."""
        if index not in self.buffer:
            self.buffer[index] = {
                "id": "",
                "type": "function", 
                "function": {"name": "", "arguments": ""}
            }
        
        if tool_call_delta.id:
            self.buffer[index]["id"] = tool_call_delta.id
        
        if tool_call_delta.function:
            if tool_call_delta.function.name:
                self.buffer[index]["function"]["name"] += tool_call_delta.function.name
            if tool_call_delta.function.arguments:
                self.buffer[index]["function"]["arguments"] += tool_call_delta.function.arguments
    
    def get_final_tool_calls(self) -> list[Any]:
        """Convert buffer to final tool call objects."""
        final_tool_calls = []
        
        for index in sorted(self.buffer.keys()):
            tool_call = self.buffer[index]
            final_tool_calls.append(ToolCallObject(
                tool_call["id"],
                tool_call["type"],
                tool_call["function"]
            ))
        
        return final_tool_calls


class ToolCallObject:
    """Represents a tool call object for API compatibility."""
    
    def __init__(self, id_: str, type_: str, function_data: dict[str, str]):
        self.id = id_
        self.type = type_
        self.function = FunctionObject(function_data["name"], function_data["arguments"])


class FunctionObject:
    """Represents a function object within tool call."""
    
    def __init__(self, name: str, arguments: str):
        self.name = name
        self.arguments = arguments


class StreamingHandler:
    """Handles streaming responses from OpenAI API."""
    
    def __init__(self, message_manager: MessageManager):
        """
        Initialize StreamingHandler.
        
        Args:
            message_manager: Message manager for getting display messages
        """
        self.message_manager = message_manager
    
    def process_streaming_response(self, completion_stream: Any) -> tuple[str, list[Any]]:
        """
        Process streaming response and return content and tool calls.
        
        Args:
            completion_stream: OpenAI streaming completion object
            
        Returns:
            Tuple of (accumulated_content, final_tool_calls)
        """
        accumulated_content = ""
        tool_call_buffer = ToolCallBuffer()
        
        self._print_bot_prefix()
        
        for chunk in completion_stream:
            if not chunk.choices:
                continue
            
            choice = chunk.choices[0]
            delta = choice.delta
            
            # Handle content streaming
            if delta.content:
                accumulated_content += delta.content
                print(delta.content, end="", flush=True)
            
            # Handle tool calls streaming
            if delta.tool_calls:
                self._process_tool_call_deltas(delta.tool_calls, tool_call_buffer)
            
            # Check if streaming is finished
            if choice.finish_reason:
                break
        
        print()  # New line after streaming
        
        return accumulated_content, tool_call_buffer.get_final_tool_calls()
    
    def _print_bot_prefix(self) -> None:
        """Print bot prefix for streaming."""
        bot_prefix = self.message_manager.get_message("react_agent", "bot_prefix")
        print(bot_prefix, end="", flush=True)
    
    def _process_tool_call_deltas(self, tool_call_deltas: list[Any], buffer: ToolCallBuffer) -> None:
        """Process tool call deltas and update buffer."""
        for tool_call_delta in tool_call_deltas:
            index = tool_call_delta.index
            buffer.update_tool_call(index, tool_call_delta) 