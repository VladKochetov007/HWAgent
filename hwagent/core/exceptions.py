"""
Custom exceptions for HWAgent.
Following SRP - each exception has specific responsibility.
"""


class HWAgentException(Exception):
    """Base exception for all HWAgent-related errors."""
    
    def __init__(self, message: str, details: str | None = None):
        self.message = message
        self.details = details
        super().__init__(self.message)
    
    def __str__(self) -> str:
        if self.details:
            return f"{self.message}: {self.details}"
        return self.message


class ValidationError(HWAgentException):
    """Raised when input validation fails."""
    pass


class ConfigurationError(HWAgentException):
    """Raised when configuration loading or parsing fails."""
    pass


class ToolExecutionError(HWAgentException):
    """Raised when tool execution fails."""
    
    def __init__(self, tool_name: str, message: str, details: str | None = None):
        self.tool_name = tool_name
        super().__init__(message, details)
    
    def __str__(self) -> str:
        base_msg = f"Tool '{self.tool_name}': {self.message}"
        if self.details:
            return f"{base_msg}: {self.details}"
        return base_msg


class ParsingError(HWAgentException):
    """Raised when response parsing fails."""
    pass


class StreamingError(HWAgentException):
    """Raised when streaming operations fail."""
    pass 