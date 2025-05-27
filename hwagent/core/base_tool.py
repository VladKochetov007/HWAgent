"""
Base tool class implementing common functionality.
Following SRP and Template Method pattern.
"""

import os
from abc import ABC, abstractmethod
from typing import Any

from hwagent.core.constants import Constants
from hwagent.core.models import ToolExecutionResult, ToolDefinition
from hwagent.core.validators import FilePathValidator, ParameterValidator


class BaseTool(ABC):
    """
    Base class for all tools.
    Implements common validation and execution patterns.
    Following Template Method pattern for consistent tool behavior.
    """
    
    def __init__(self, tmp_directory: str = Constants.DEFAULT_TMP_DIRECTORY):
        self.tmp_directory = tmp_directory
        self._ensure_tmp_directory()
    
    def _ensure_tmp_directory(self) -> None:
        """Ensure temporary directory exists."""
        if not os.path.exists(self.tmp_directory):
            os.makedirs(self.tmp_directory, exist_ok=True)
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name for registration."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description for LLM."""
        pass
    
    @property
    @abstractmethod
    def parameters_schema(self) -> dict[str, Any]:
        """JSON schema for tool parameters."""
        pass
    
    def get_tool_definition(self) -> ToolDefinition:
        """Get tool definition for API registration."""
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters=self.parameters_schema
        )
    
    def validate_parameters(self, parameters: dict[str, Any]) -> ToolExecutionResult:
        """
        Validate tool parameters.
        Template method - can be overridden by subclasses.
        """
        return self._validate_common_parameters(parameters)
    
    def _validate_common_parameters(self, parameters: dict[str, Any]) -> ToolExecutionResult:
        """Common parameter validation logic."""
        if not isinstance(parameters, dict):
            return ToolExecutionResult.error("Parameters must be a dictionary")
        
        return ToolExecutionResult.success("Basic parameter validation passed")
    
    def execute(self, **kwargs) -> ToolExecutionResult:
        """
        Execute tool with validation.
        Template method implementing the execution flow.
        """
        # Step 1: Validate parameters
        validation_result = self.validate_parameters(kwargs)
        if validation_result.is_error():
            return validation_result
        
        # Step 2: Execute tool-specific logic
        try:
            return self._execute_impl(**kwargs)
        except Exception as e:
            return ToolExecutionResult.error(
                f"Tool execution failed: {self.name}",
                str(e)
            )
    
    @abstractmethod
    def _execute_impl(self, **kwargs) -> ToolExecutionResult:
        """
        Tool-specific execution logic.
        Must be implemented by subclasses.
        """
        pass
    
    def _get_full_path(self, filepath: str) -> str:
        """Get full path within temporary directory."""
        return os.path.join(self.tmp_directory, filepath)
    
    def _validate_filepath_parameter(self, filepath: str) -> ToolExecutionResult:
        """Common filepath validation for file operations."""
        # Validate parameter type and content
        param_result = ParameterValidator.validate_required_string(filepath, "filepath")
        if param_result.is_error():
            return param_result
        
        # Validate path safety
        path_result = FilePathValidator.validate_relative_path(filepath)
        if path_result.is_error():
            return path_result
        
        return ToolExecutionResult.success("Filepath parameter is valid")


class FileOperationTool(BaseTool):
    """
    Base class for file operation tools.
    Provides common file operation functionality.
    """
    
    def _validate_common_parameters(self, parameters: dict[str, Any]) -> ToolExecutionResult:
        """Validate common file operation parameters."""
        base_result = super()._validate_common_parameters(parameters)
        if base_result.is_error():
            return base_result
        
        # All file operations require filepath
        filepath = parameters.get("filepath")
        return self._validate_filepath_parameter(filepath)
    
    def _ensure_file_exists(self, filepath: str) -> ToolExecutionResult:
        """Ensure file exists for read operations."""
        full_path = self._get_full_path(filepath)
        return FilePathValidator.validate_file_exists(full_path)
    
    def _get_file_info(self, filepath: str) -> dict[str, Any]:
        """Get file information for metadata."""
        full_path = self._get_full_path(filepath)
        try:
            stat = os.stat(full_path)
            return {
                "size_bytes": stat.st_size,
                "modified_time": stat.st_mtime,
                "full_path": full_path
            }
        except OSError:
            return {"full_path": full_path} 