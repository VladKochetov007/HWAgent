import os
from pathlib import Path
from . import BaseTool


class CreateFileTool(BaseTool):
    """Creates a new file with the specified content in the tmp directory. Use this when you need to generate a new file."""
    
    def __init__(self, tmp_directory: str = "hwagent/tmp"):
        self.tmp_directory = tmp_directory
        os.makedirs(self.tmp_directory, exist_ok=True)
    
    def execute(self, filepath: str, content: str) -> str:
        """Execute file creation.
        
        Args:
            filepath: The filename or relative path within tmp directory
            content: The content to write into the new file
            
        Returns:
            str: Success message or error message starting with 'Error:'
        """
        if not filepath or not isinstance(filepath, str):
            return "Error: 'filepath' (string) parameter is required for create_file."
        
        if content is None or not isinstance(content, str):
            return "Error: 'content' (string) parameter is required for create_file."

        try:
            # Ensure file is within tmp directory
            if ".." in filepath or os.path.isabs(filepath):
                return f"Error: Invalid filepath '{filepath}'. Must be a relative path without '..'."
            
            # Construct full path within tmp directory
            full_path = os.path.join(self.tmp_directory, filepath)
            
            # Create intermediate directories if needed
            dir_name = os.path.dirname(full_path)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)
                
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            # Return the path relative to tmp for tool consistency
            return f"Successfully created file: {filepath} (in {self.tmp_directory})"
        except Exception as e:
            return f"Error creating file '{filepath}': {e}" 