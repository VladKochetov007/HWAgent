import os
from smolagents import Tool

class CreateFileTool(Tool):
    name = "create_file"
    description = "Creates a new file with specified content."
    inputs = {
        "file_path": {
            "type": "string",
            "description": "Path where to create the file, relative to the current directory"
        },
        "content": {
            "type": "string",
            "description": "Content to write to the file"
        }
    }
    output_type = "string"

    def forward(self, file_path: str, content: str) -> str:
        try:
            if not file_path:
                return "Failed to create file: file_path cannot be empty"
                
            # Create directories if they don't exist
            dir_path = os.path.dirname(file_path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            
            # Write content to file
            with open(file_path, "w") as f:
                f.write(content)
            return f"File created successfully at {file_path}"
        except Exception as e:
            return f"Failed to create file: {e}"
