# """
# Delete File Tool - deletes existing files.
# Refactored to use core components and follow SOLID principles.
# """

# import os
# from typing import Any
# from hwagent.core import FileOperationTool, ToolExecutionResult


# class DeleteFileTool(FileOperationTool):
#     """Tool for deleting existing files from temporary directory."""
    
#     @property
#     def name(self) -> str:
#         return "delete_file"
    
#     @property
#     def description(self) -> str:
#         return "Delete an existing file from the temporary directory"
    
#     @property
#     def parameters_schema(self) -> dict[str, Any]:
#         return {
#             "type": "object",
#             "properties": {
#                 "filepath": {
#                     "type": "string",
#                     "description": "Relative path to the file within temporary directory to delete. Can be multiline for complex paths."
#                 }
#             },
#             "required": ["filepath"]
#         }
    
#     def _execute_impl(self, **kwargs) -> ToolExecutionResult:
#         """Delete file."""
#         filepath = kwargs["filepath"]
        
#         # Ensure file exists before deletion
#         exists_result = self._ensure_file_exists(filepath)
#         if exists_result.is_error():
#             return exists_result
        
#         full_path = self._get_full_path(filepath)
        
#         try:
#             # Get file info before deletion for confirmation
#             file_info = self._get_file_info(filepath)
            
#             # Delete the file
#             os.remove(full_path)
            
#             return ToolExecutionResult.success(
#                 f"deleted file: {filepath}",
#                 f"Removed file of {file_info.get('size_bytes', 0)} bytes",
#                 data={"deleted_file": filepath, "previous_info": file_info}
#             )
            
#         except OSError as e:
#             return ToolExecutionResult.error(
#                 f"deleting file '{filepath}'",
#                 str(e)
#             ) 