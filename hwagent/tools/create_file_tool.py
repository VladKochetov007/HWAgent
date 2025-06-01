"""
Create File Tool - creates new files with specified content.
Refactored to use core components and follow SOLID principles.
"""

from typing import Any
from hwagent.core import FileOperationTool, ToolExecutionResult, ParameterValidator, SecurityValidator
from pathlib import Path


class CreateFileTool(FileOperationTool):
    """Tool for creating new files with specified content in temporary directory."""
    
    @property
    def name(self) -> str:
        return "create_file"
    
    @property
    def description(self) -> str:
        return "Create a new file with specified content in the temporary directory"
    
    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "filepath": {
                    "type": "string",
                    "description": "Relative path for the new file within temporary directory. Can be multiline for complex paths."
                },
                "content": {
                    "type": "string", 
                    "description": "Content to write to the file. Supports multiline content with proper formatting."
                }
            },
            "required": ["filepath", "content"]
        }
    
    def validate_parameters(self, parameters: dict[str, Any]) -> ToolExecutionResult:
        """Validate create file specific parameters."""
        # Validate common file parameters (filepath)
        base_result = super().validate_parameters(parameters)
        if base_result.is_error():
            return base_result
        
        # Validate content parameter
        content = parameters.get("content")
        content_result = ParameterValidator.validate_required_string(content, "content")
        if content_result.is_error():
            return content_result
        
        # Security check: validate content safety
        filepath = parameters.get("filepath", "")
        file_extension = Path(filepath).suffix
        
        security_result = SecurityValidator.validate_file_content_safety(content, file_extension)
        if security_result.is_error():
            return ToolExecutionResult.error(
                f"Security validation failed for file: {filepath}",
                security_result.details
            )
        
        return ToolExecutionResult.success("All parameters validated successfully")
    
    def _execute_impl(self, **kwargs) -> ToolExecutionResult:
        """Create file with specified content."""
        filepath = kwargs["filepath"]
        content = kwargs["content"]
        
        # Remove unwanted quotes from content
        cleaned_content = self._remove_unwanted_quotes(content)
        
        full_path = self._get_full_path(filepath)
        
        try:
            # Ensure parent directory exists
            import os
            parent_dir = os.path.dirname(full_path)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)
            
            # Write file content
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(cleaned_content)
            
            # Get file info for response
            file_info = self._get_file_info(filepath)
            
            # Add information about quote removal if it occurred
            message = f"created file: {filepath}"
            if content != cleaned_content:
                message += " (unwanted quotes removed)"
            
            return ToolExecutionResult.success(
                message,
                f"Size: {file_info.get('size_bytes', 0)} bytes",
                data=file_info
            )
            
        except OSError as e:
            return ToolExecutionResult.error(
                f"creating file '{filepath}'",
                str(e)
            )
    
    def _remove_unwanted_quotes(self, content: str) -> str:
        """Remove unwanted quotes from beginning and end of content"""
        if not content:
            return content
        
        original_content = content
        
        # Remove different types of quotes from beginning and end
        quote_chars = ['"', "'", '`']
        
        for quote_char in quote_chars:
            # Remove triple quotes first
            triple_quote = quote_char * 3
            if content.startswith(triple_quote) and content.endswith(triple_quote):
                content = content[3:-3]
                break
            
            # Remove single quotes
            while content.startswith(quote_char) and content.endswith(quote_char):
                content = content[1:-1]
        
        # Clean up any remaining whitespace
        content = content.strip()
        
        return content 