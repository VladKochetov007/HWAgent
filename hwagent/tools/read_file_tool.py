"""
Read File Tool - reads content from existing files.
Refactored to use core components and follow SOLID principles.
"""

from typing import Any
from hwagent.core import FileOperationTool, ToolExecutionResult, Constants


class ReadFileTool(FileOperationTool):
    """Tool for reading content from existing files in temporary directory."""
    
    @property
    def name(self) -> str:
        return "read_file"
    
    @property
    def description(self) -> str:
        return "Read and return the content of an existing file from the temporary directory"
    
    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "filepath": {
                    "type": "string",
                    "description": "Relative path to the file within temporary directory. Can be multiline for complex paths."
                }
            },
            "required": ["filepath"]
        }
    
    def _execute_impl(self, **kwargs) -> ToolExecutionResult:
        """Read file content."""
        filepath = kwargs["filepath"]
        
        # Ensure file exists
        exists_result = self._ensure_file_exists(filepath)
        if exists_result.is_error():
            return exists_result
        
        full_path = self._get_full_path(filepath)
        
        try:
            # Check file size before reading
            from hwagent.core import FilePathValidator
            size_result = FilePathValidator.validate_file_size(full_path)
            if size_result.is_error():
                return ToolExecutionResult.error(
                    f"reading file '{filepath}'",
                    size_result.details
                )
            
            # Read file content
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Get file info for metadata
            file_info = self._get_file_info(filepath)
            file_info["content_length"] = len(content)
            file_info["lines_count"] = content.count('\n') + 1 if content else 0
            
            return ToolExecutionResult.success(
                f"read file: {filepath}",
                f"Content: {content}",
                data=file_info
            )
            
        except UnicodeDecodeError:
            return ToolExecutionResult.error(
                f"reading file '{filepath}'",
                "File contains non-UTF-8 content"
            )
        except OSError as e:
            return ToolExecutionResult.error(
                f"reading file '{filepath}'",
                str(e)
            ) 