import os
from . import BaseTool


class ReadFileTool(BaseTool):
    """Reads and returns the content of an existing file from the tmp directory. Use this to examine file contents or check results."""
    
    def __init__(self, tmp_directory: str = "hwagent/tmp"):
        self.tmp_directory = tmp_directory
        os.makedirs(self.tmp_directory, exist_ok=True)
    
    def execute(self, filepath: str) -> str:
        """Execute file reading.
        
        Args:
            filepath: The filename or relative path within tmp directory
            
        Returns:
            str: File content or error message starting with 'Error:'
        """
        if not filepath or not isinstance(filepath, str):
            return "Error: 'filepath' (string) parameter is required for read_file."

        try:
            if ".." in filepath or os.path.isabs(filepath):
                return f"Error: Invalid filepath '{filepath}'. Must be a relative path without '..'."
            
            # Construct full path within tmp directory
            full_path = os.path.join(self.tmp_directory, filepath)
            
            if not os.path.exists(full_path):
                return f"Error: File '{filepath}' does not exist in {self.tmp_directory}."
            
            if not os.path.isfile(full_path):
                return f"Error: '{filepath}' is not a file."
                
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Add some metadata for better user experience
            size = len(content)
            lines = content.count('\n') + 1 if content else 0
            
            return f"File: {filepath} ({size} chars, {lines} lines)\n" + "="*40 + "\n" + content
            
        except UnicodeDecodeError:
            return f"Error: File '{filepath}' contains binary data and cannot be read as text."
        except Exception as e:
            return f"Error reading file '{filepath}': {e}" 