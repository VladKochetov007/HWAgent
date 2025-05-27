"""
Data models for HWAgent.
Following SRP - each model has single responsibility.
"""

from dataclasses import dataclass
from typing import Any, Optional
from enum import Enum


class ExecutionStatus(Enum):
    """Enumeration for execution statuses."""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"


@dataclass
class ToolExecutionResult:
    """Standardized result for tool execution."""
    status: ExecutionStatus
    message: str
    details: Optional[str] = None
    data: Optional[dict[str, Any]] = None
    
    @classmethod
    def success(cls, message: str, details: str | None = None, data: dict[str, Any] | None = None) -> 'ToolExecutionResult':
        """Create successful result."""
        return cls(ExecutionStatus.SUCCESS, message, details, data)
    
    @classmethod
    def error(cls, message: str, details: str | None = None) -> 'ToolExecutionResult':
        """Create error result."""
        return cls(ExecutionStatus.ERROR, message, details)
    
    @classmethod
    def warning(cls, message: str, details: str | None = None) -> 'ToolExecutionResult':
        """Create warning result."""
        return cls(ExecutionStatus.WARNING, message, details)
    
    def is_success(self) -> bool:
        """Check if execution was successful."""
        return self.status == ExecutionStatus.SUCCESS
    
    def is_error(self) -> bool:
        """Check if execution resulted in error."""
        return self.status == ExecutionStatus.ERROR
    
    def to_string(self) -> str:
        """Convert result to string format."""
        if self.is_error():
            prefix = "Error:"
        else:
            prefix = "Successfully" if self.is_success() else "Warning:"
        
        result = f"{prefix} {self.message}"
        if self.details:
            result += f": {self.details}"
        return result


@dataclass
class ParsedLLMResponse:
    """Parsed structure for LLM responses."""
    thought: str | None = None
    plan: list[str] | None = None
    tool_call_name: str | None = None
    tool_call_params: dict[str, Any] | None = None
    final_answer: str | None = None
    raw_text: str = ""
    
    def has_tool_call(self) -> bool:
        """Check if response contains tool call."""
        return self.tool_call_name is not None and self.tool_call_params is not None
    
    def has_final_answer(self) -> bool:
        """Check if response contains final answer."""
        return self.final_answer is not None and self.final_answer.strip()


@dataclass
class ConversationMessage:
    """Represents a single conversation message."""
    role: str
    content: str
    tool_call_id: str | None = None
    name: str | None = None
    metadata: dict[str, Any] | None = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary format."""
        result = {"role": self.role, "content": self.content}
        
        if self.tool_call_id:
            result["tool_call_id"] = self.tool_call_id
        if self.name:
            result["name"] = self.name
        if self.metadata:
            result.update(self.metadata)
            
        return result


@dataclass
class ToolDefinition:
    """Represents a tool definition for API."""
    name: str
    description: str
    parameters: dict[str, Any]
    
    def to_api_format(self) -> dict[str, Any]:
        """Convert to OpenAI API format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters  # parameters is already a complete JSON Schema
            }
        } 