"""
Validators for HWAgent components.
Following SRP - each validator has single responsibility.
"""

import os
from pathlib import Path
from typing import Any
import re

from hwagent.core.constants import Constants
from hwagent.core.exceptions import ValidationError
from hwagent.core.models import ToolExecutionResult, ExecutionStatus


class SecurityValidator:
    """Validator for security-related checks to prevent dangerous operations."""
    
    @staticmethod
    def validate_python_code_safety(code: str) -> ToolExecutionResult:
        """Check Python code for dangerous patterns."""
        dangerous_patterns = [
            r'import\s+(os|subprocess|shutil)',
            r'from\s+(os|subprocess|shutil)\s+import',
            r'__import__\s*\(',
            r'eval\s*\(',
            r'exec\s*\(',
            r'open\s*\([^)]*["\'][/\\]',  # Opening files with absolute paths
            r'os\.system\s*\(',
            r'subprocess\.',
            r'shutil\.rmtree',
            r'os\.remove',
            r'os\.unlink',
            r'pathlib\.Path.*\.unlink',
            r'Path\([^)]*\)\.unlink',  # Direct Path().unlink() calls
            r'\.write18',  # LaTeX shell escape
            # Additional patterns to prevent HTTP requests and file operations
            r'requests\.',  # HTTP requests library
            r'urllib\.request',  # URL library
            r'urllib\.urlopen',
            r'http\.client',
            r'httplib',
            r'DELETE.*api/fs/tmp/delete',  # Direct API call
            r'localhost:5000',  # Local API server
            r'127\.0\.0\.1:5000',  # Local API server IP
            r'\.delete\(',  # Any delete method calls
            r'pathlib\.Path.*\.rmdir',  # Directory removal
            r'os\.rmdir',  # Directory removal
            r'tempfile\.mktemp',  # Insecure temporary files
        ]
        
        lines = code.split('\n')
        warnings = []
        
        for i, line in enumerate(lines, 1):
            line_stripped = line.strip()
            # Skip comments
            if line_stripped.startswith('#'):
                continue
                
            for pattern in dangerous_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    warnings.append(f"Line {i}: Potentially dangerous pattern '{pattern}' detected")
        
        if warnings:
            return ToolExecutionResult.error(
                "Dangerous code patterns detected",
                "\n".join(warnings)
            )
        
        return ToolExecutionResult.success("Python code safety check passed")
    
    @staticmethod
    def validate_latex_safety(content: str) -> ToolExecutionResult:
        """Check LaTeX content for dangerous commands."""
        dangerous_commands = Constants.DANGEROUS_LATEX_COMMANDS
        warnings = []
        
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            line_stripped = line.strip()
            # Skip comments
            if line_stripped.startswith('%'):
                continue
                
            for dangerous_cmd in dangerous_commands:
                if dangerous_cmd in line:
                    warnings.append(f"Line {i}: Dangerous LaTeX command '{dangerous_cmd}' detected")
        
        if warnings:
            return ToolExecutionResult.error(
                "Dangerous LaTeX commands detected",
                "\n".join(warnings)
            )
        
        return ToolExecutionResult.success("LaTeX safety check passed")
    
    @staticmethod
    def validate_shell_command_safety(command: str | list[str]) -> ToolExecutionResult:
        """Check shell commands for dangerous operations."""
        if isinstance(command, list):
            command_str = ' '.join(command)
        else:
            command_str = command
        
        dangerous_commands = Constants.DANGEROUS_COMMANDS
        command_lower = command_str.lower()
        
        for dangerous_cmd in dangerous_commands:
            if dangerous_cmd in command_lower:
                return ToolExecutionResult.error(
                    f"Dangerous command detected: '{dangerous_cmd}'",
                    f"Full command: {command_str}"
                )
        
        # Check for shell injection patterns
        shell_injection_patterns = [
            r'[;&|`$]',  # Command separators and substitution
            r'\$\(',     # Command substitution
            r'>\s*/dev',  # Writing to devices
            r'<\s*/dev',  # Reading from devices
        ]
        
        for pattern in shell_injection_patterns:
            if re.search(pattern, command_str):
                return ToolExecutionResult.error(
                    "Potential shell injection detected",
                    f"Pattern '{pattern}' found in: {command_str}"
                )
        
        return ToolExecutionResult.success("Shell command safety check passed")
    
    @staticmethod
    def validate_file_content_safety(content: str, file_extension: str = "") -> ToolExecutionResult:
        """General file content safety validation."""
        # Check for potential binary content
        if '\x00' in content:
            return ToolExecutionResult.error(
                "Binary content detected",
                "File appears to contain binary data"
            )
        
        # Check file size in memory
        content_size = len(content.encode('utf-8'))
        if content_size > Constants.MAX_FILE_SIZE_BYTES:
            return ToolExecutionResult.error(
                "Content too large",
                f"Size: {content_size} bytes, Max: {Constants.MAX_FILE_SIZE_BYTES} bytes"
            )
        
        # File type specific checks
        if file_extension.lower() in ['.py']:
            return SecurityValidator.validate_python_code_safety(content)
        elif file_extension.lower() in ['.tex', '.latex']:
            return SecurityValidator.validate_latex_safety(content)
        
        return ToolExecutionResult.success("File content safety check passed")


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
    def validate_multiline_string(value: Any, param_name: str, required: bool = True) -> ToolExecutionResult:
        """Validate that parameter is a string (can be multiline)."""
        if value is None:
            if required:
                return ToolExecutionResult.error(f"Parameter '{param_name}' is required")
            else:
                return ToolExecutionResult.success(f"Parameter '{param_name}' is None (valid)")
        
        if not isinstance(value, str):
            return ToolExecutionResult.error(
                f"Parameter '{param_name}' must be a string",
                f"Got: {type(value).__name__}"
            )
        
        if required and not value.strip():
            return ToolExecutionResult.error(f"Parameter '{param_name}' cannot be empty")
        
        # Normalize line endings for multiline strings
        normalized_value = value.replace('\r\n', '\n').replace('\r', '\n')
        
        return ToolExecutionResult.success(f"Parameter '{param_name}' is valid (multiline supported)")
    
    @staticmethod
    def normalize_multiline_parameter(value: str) -> str:
        """Normalize multiline parameter by standardizing line endings."""
        if not isinstance(value, str):
            return value
        
        # Normalize line endings: \r\n and \r -> \n
        normalized = value.replace('\r\n', '\n').replace('\r', '\n')
        
        # Strip leading/trailing whitespace but preserve internal formatting
        return normalized.strip()
    
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
    
    @staticmethod
    def validate_search_count(count: int) -> ToolExecutionResult:
        """Validate search results count parameter."""
        if not isinstance(count, int):
            return ToolExecutionResult.error(
                "Search count must be an integer",
                f"Got: {type(count).__name__}"
            )
        
        if count < Constants.MIN_SEARCH_COUNT or count > Constants.MAX_SEARCH_COUNT:
            return ToolExecutionResult.error(
                f"Search count must be between {Constants.MIN_SEARCH_COUNT} and {Constants.MAX_SEARCH_COUNT}",
                f"Got: {count}"
            )
        
        return ToolExecutionResult.success(f"Search count '{count}' is valid")
    
    @staticmethod
    def validate_freshness_parameter(freshness: str) -> ToolExecutionResult:
        """Validate search freshness parameter."""
        valid_freshness = {
            Constants.FRESHNESS_ONE_DAY,
            Constants.FRESHNESS_ONE_WEEK,
            Constants.FRESHNESS_ONE_MONTH,
            Constants.FRESHNESS_ONE_YEAR,
            Constants.FRESHNESS_NO_LIMIT
        }
        
        if freshness not in valid_freshness:
            return ToolExecutionResult.error(
                f"Invalid freshness: {freshness}",
                f"Valid options: {', '.join(valid_freshness)}"
            )
        
        return ToolExecutionResult.success(f"Freshness '{freshness}' is valid")


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