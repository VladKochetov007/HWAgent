"""
List Files Tool - lists files and directories.
Refactored to use core components and follow SOLID principles.
"""

import os
from typing import Any
from hwagent.core import BaseTool, ToolExecutionResult, ParameterValidator


class ListFilesTool(BaseTool):
    """Tool for listing files and directories in temporary directory."""
    
    @property
    def name(self) -> str:
        return "list_files"
    
    @property
    def description(self) -> str:
        return "List files and directories in the temporary directory or specified subdirectory"
    
    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Optional subdirectory path within temporary directory (default: root). Can be multiline for complex paths."
                }
            },
            "required": []
        }
    
    def validate_parameters(self, parameters: dict[str, Any]) -> ToolExecutionResult:
        """Validate list files parameters."""
        base_result = super().validate_parameters(parameters)
        if base_result.is_error():
            return base_result
        
        # Path parameter is optional
        path = parameters.get("path", "")
        if path:
            path_result = ParameterValidator.validate_optional_string(path, "path")
            if path_result.is_error():
                return path_result
            
            # Validate path safety if provided
            if ".." in path or os.path.isabs(path):
                return ToolExecutionResult.error(
                    "Invalid path parameter",
                    "Path must be relative and not contain '..'"
                )
        
        return ToolExecutionResult.success("Parameters validated successfully")
    
    def _execute_impl(self, **kwargs) -> ToolExecutionResult:
        """List files and directories."""
        path = kwargs.get("path", "")
        
        # Determine target directory
        if path:
            target_dir = self._get_full_path(path)
        else:
            target_dir = self.tmp_directory
        
        try:
            # Check if target directory exists
            if not os.path.exists(target_dir):
                return ToolExecutionResult.error(
                    f"Directory not found: {path or 'root'}",
                    f"Full path: {target_dir}"
                )
            
            if not os.path.isdir(target_dir):
                return ToolExecutionResult.error(
                    f"Path is not a directory: {path or 'root'}",
                    f"Full path: {target_dir}"
                )
            
            # List directory contents
            items = []
            for item_name in sorted(os.listdir(target_dir)):
                item_path = os.path.join(target_dir, item_name)
                item_info = {
                    "name": item_name,
                    "type": "directory" if os.path.isdir(item_path) else "file"
                }
                
                if item_info["type"] == "file":
                    try:
                        stat = os.stat(item_path)
                        item_info["size_bytes"] = stat.st_size
                        item_info["modified_time"] = stat.st_mtime
                    except OSError:
                        pass
                
                items.append(item_info)
            
            # Format output
            if not items:
                content = f"Directory '{path or 'root'}' is empty."
            else:
                lines = [f"Contents of '{path or 'root'}':"]
                for item in items:
                    if item["type"] == "directory":
                        lines.append(f"  📁 {item['name']}/")
                    else:
                        size_info = f" ({item.get('size_bytes', 0)} bytes)" if 'size_bytes' in item else ""
                        lines.append(f"  📄 {item['name']}{size_info}")
                content = "\n".join(lines)
            
            return ToolExecutionResult.success(
                f"listed directory: {path or 'root'}",
                content,
                data={"items": items, "count": len(items)}
            )
            
        except OSError as e:
            return ToolExecutionResult.error(
                f"listing directory '{path or 'root'}'",
                str(e)
            ) 