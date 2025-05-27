"""
Validators for HWAgent components.
Following SRP - each validator has single responsibility.
"""

import os
from pathlib import Path
from typing import Any

from .constants import Constants
from .exceptions import ValidationError
from .models import ToolExecutionResult, ExecutionStatus


class FilePathValidator:
    """Validator for file paths and file operations."""
    
    @staticmethod
    def validate_relative_path(filepath: str) -> ToolExecutionResult:
        """Validate that filepath is relative and safe."""
        if not filepath:
            return ToolExecutionResult.error("Filepath cannot be empty")
        
        if not isinstance(filepath, str):
            return ToolExecutionResult.error("Filepath must be a string")
        
        # Check for forbidden path segments
        for forbidden in Constants.FORBIDDEN_PATH_SEGMENTS:
            if forbidden in filepath:
                return ToolExecutionResult.error(
                    f"Invalid filepath '{filepath}'",
                    f"Contains forbidden segment '{forbidden}'"
                )
        
        # Check if path is absolute
        if os.path.isabs(filepath):
            return ToolExecutionResult.error(
                f"Invalid filepath '{filepath}'",
                "Must be a relative path"
            )
        
        return ToolExecutionResult.success("Filepath validation passed")
    
    @staticmethod
    def validate_file_exists(filepath: str, base_dir: str = "") -> ToolExecutionResult:
        """Validate that file exists."""
        full_path = os.path.join(base_dir, filepath) if base_dir else filepath
        
        if not os.path.exists(full_path):
            return ToolExecutionResult.error(
                f"File not found: {filepath}",
                f"Full path: {full_path}"
            )
        
        if not os.path.isfile(full_path):
            return ToolExecutionResult.error(
                f"Path is not a file: {filepath}",
                f"Full path: {full_path}"
            )
        
        return ToolExecutionResult.success("File exists and is valid")
    
    @staticmethod
    def validate_directory_exists(dirpath: str) -> ToolExecutionResult:
        """Validate that directory exists."""
        if not os.path.exists(dirpath):
            return ToolExecutionResult.error(f"Directory not found: {dirpath}")
        
        if not os.path.isdir(dirpath):
            return ToolExecutionResult.error(f"Path is not a directory: {dirpath}")
        
        return ToolExecutionResult.success("Directory exists and is valid")
    
    @staticmethod
    def validate_file_size(filepath: str, max_size: int = Constants.MAX_FILE_SIZE_BYTES) -> ToolExecutionResult:
        """Validate file size is within limits."""
        try:
            file_size = os.path.getsize(filepath)
            if file_size > max_size:
                return ToolExecutionResult.error(
                    f"File too large: {filepath}",
                    f"Size: {file_size} bytes, Max: {max_size} bytes"
                )
            return ToolExecutionResult.success("File size is within limits")
        except OSError as e:
            return ToolExecutionResult.error(f"Cannot check file size: {filepath}", str(e))


class ParameterValidator:
    """Validator for tool parameters."""
    
    @staticmethod
    def validate_required_string(value: Any, param_name: str) -> ToolExecutionResult:
        """Validate that parameter is a non-empty string."""
        if value is None:
            return ToolExecutionResult.error(f"Parameter '{param_name}' is required")
        
        if not isinstance(value, str):
            return ToolExecutionResult.error(
                f"Parameter '{param_name}' must be a string",
                f"Got: {type(value).__name__}"
            )
        
        if not value.strip():
            return ToolExecutionResult.error(f"Parameter '{param_name}' cannot be empty")
        
        return ToolExecutionResult.success(f"Parameter '{param_name}' is valid")
    
    @staticmethod
    def validate_optional_string(value: Any, param_name: str) -> ToolExecutionResult:
        """Validate that parameter is a string or None."""
        if value is None:
            return ToolExecutionResult.success(f"Parameter '{param_name}' is None (valid)")
        
        if not isinstance(value, str):
            return ToolExecutionResult.error(
                f"Parameter '{param_name}' must be a string or None",
                f"Got: {type(value).__name__}"
            )
        
        return ToolExecutionResult.success(f"Parameter '{param_name}' is valid")
    
    @staticmethod
    def validate_language_parameter(language: str) -> ToolExecutionResult:
        """Validate programming language parameter."""
        valid_languages = {
            Constants.LANGUAGE_PYTHON,
            Constants.LANGUAGE_CPP,
            Constants.LANGUAGE_C,
            Constants.LANGUAGE_AUTO
        }
        
        if language not in valid_languages:
            return ToolExecutionResult.error(
                f"Invalid language: {language}",
                f"Valid options: {', '.join(valid_languages)}"
            )
        
        return ToolExecutionResult.success(f"Language '{language}' is valid")


class ConfigValidator:
    """Validator for configuration data."""
    
    @staticmethod
    def validate_config_structure(config: dict[str, Any], required_keys: list[str]) -> ToolExecutionResult:
        """Validate that configuration has required structure."""
        if not isinstance(config, dict):
            return ToolExecutionResult.error("Configuration must be a dictionary")
        
        missing_keys = [key for key in required_keys if key not in config]
        if missing_keys:
            return ToolExecutionResult.error(
                "Missing required configuration keys",
                f"Missing: {', '.join(missing_keys)}"
            )
        
        return ToolExecutionResult.success("Configuration structure is valid") 