import os
from . import BaseTool


class DeleteFileTool(BaseTool):
    """Deletes an existing file from the tmp directory. Use this when you need to remove a file from the filesystem."""
    
    def __init__(self, tmp_directory: str = "hwagent/tmp"):
        self.tmp_directory = tmp_directory
        os.makedirs(self.tmp_directory, exist_ok=True)
    
    def execute(self, filepath: str) -> str:
        """Execute file deletion.
        
        Args:
            filepath: The filename or relative path within tmp directory
            
        Returns:
            str: Success message or error message starting with 'Error:'
        """
        if not filepath or not isinstance(filepath, str):
            return "Error: 'filepath' (string) parameter is required for delete_file."

        try:
            if ".." in filepath or os.path.isabs(filepath):
                return f"Error: Invalid filepath '{filepath}'. Must be a relative path without '..'."
            
            # Construct full path within tmp directory
            full_path = os.path.join(self.tmp_directory, filepath)
            
            if not os.path.exists(full_path):
                return f"Error: File '{filepath}' does not exist in {self.tmp_directory}."
            
            if not os.path.isfile(full_path):
                return f"Error: '{filepath}' is not a file."
                
            os.remove(full_path)
            return f"Successfully deleted file: {filepath} (from {self.tmp_directory})"
        except Exception as e:
            return f"Error deleting file '{filepath}': {e}" 