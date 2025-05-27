"""
Abstract interfaces for HWAgent components.
Following DIP - depend on abstractions, not concretions.
Following ISP - segregated interfaces for specific responsibilities.
"""

from abc import ABC, abstractmethod
from typing import Any, Iterator
from hwagent.core.models import ToolExecutionResult, ParsedLLMResponse


class ConfigLoader(ABC):
    """Abstract interface for configuration loading."""
    
    @abstractmethod
    def load_config(self, config_path: str) -> dict[str, Any]:
        """Load configuration from specified path."""
        pass


class MessageParser(ABC):
    """Abstract interface for parsing LLM responses."""
    
    @abstractmethod
    def parse_response(self, response_text: str) -> ParsedLLMResponse:
        """Parse LLM response text into structured format."""
        pass


class StreamingHandler(ABC):
    """Abstract interface for handling streaming responses."""
    
    @abstractmethod
    def handle_stream(self, completion_stream: Iterator[Any]) -> tuple[str, list[Any]]:
        """Handle streaming response and return content and tool calls."""
        pass


class ConversationManager(ABC):
    """Abstract interface for managing conversation history."""
    
    @abstractmethod
    def add_message(self, role: str, content: str, **kwargs) -> None:
        """Add message to conversation history."""
        pass
    
    @abstractmethod
    def get_messages(self) -> list[dict[str, Any]]:
        """Get all messages in conversation."""
        pass
    
    @abstractmethod
    def clear_history(self) -> None:
        """Clear conversation history."""
        pass
    
    @abstractmethod
    def get_summary(self) -> str:
        """Get conversation summary."""
        pass


class ToolValidator(ABC):
    """Abstract interface for tool input validation."""
    
    @abstractmethod
    def validate_parameters(self, parameters: dict[str, Any]) -> ToolExecutionResult:
        """Validate tool parameters."""
        pass


class ToolExecutor(ABC):
    """Abstract interface for tool execution."""
    
    @abstractmethod
    def execute(self, **kwargs) -> ToolExecutionResult:
        """Execute tool with given parameters."""
        pass 