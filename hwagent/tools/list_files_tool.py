import os
from . import BaseTool


class ListFilesTool(BaseTool):
    """Lists files and directories in the tmp directory or specified subdirectory. Use this to explore the filesystem structure."""
    
    def __init__(self, tmp_directory: str = "hwagent/tmp"):
        self.tmp_directory = tmp_directory
        os.makedirs(self.tmp_directory, exist_ok=True)
    
    def execute(self, directory: str = ".") -> str:
        """Execute directory listing.
        
        Args:
            directory: The directory path relative to tmp directory (defaults to tmp root)
            
        Returns:
            str: List of files and directories or error message starting with 'Error:'
        """
        if not isinstance(directory, str):
            return "Error: 'directory' must be a string."

        try:
            if ".." in directory or os.path.isabs(directory):
                return f"Error: Invalid directory path '{directory}'. Must be a relative path without '..'."
            
            # Construct full path within tmp directory
            if directory == ".":
                full_path = self.tmp_directory
                display_path = f"{self.tmp_directory}/"
            else:
                full_path = os.path.join(self.tmp_directory, directory)
                display_path = f"{self.tmp_directory}/{directory}/"
            
            if not os.path.exists(full_path):
                return f"Error: Directory '{directory}' does not exist in {self.tmp_directory}."
            
            if not os.path.isdir(full_path):
                return f"Error: '{directory}' is not a directory."
            
            items = []
            for item in sorted(os.listdir(full_path)):
                item_path = os.path.join(full_path, item)
                if os.path.isdir(item_path):
                    items.append(f"[DIR]  {item}/")
                else:
                    size = os.path.getsize(item_path)
                    items.append(f"[FILE] {item} ({size} bytes)")
            
            if not items:
                return f"Directory '{display_path}' is empty."
            
            return f"Contents of '{display_path}':\n" + "\n".join(items)
            
        except Exception as e:
            return f"Error listing directory '{directory}': {e}" 