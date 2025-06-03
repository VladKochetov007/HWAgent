import os
from smolagents import Tool
from smolagents.models import OpenAIServerModel


class EditFileTool(Tool):
    name = "edit_file"
    description = "Edits the content of a file given instructions."
    inputs = {
        "file_path": {
            "type": "string",
            "description": "Path to the file to edit"
        },
        "instruction": {
            "type": "string", 
            "description": "Instructions for how to edit the file"
        }
    }
    output_type = "string"

    def __init__(self, model: str, api_base: str, api_key: str, system_prompt: str):
        super().__init__()
        self.model = OpenAIServerModel(
            model_id=model,
            api_base=api_base,
            api_key=api_key,
            messages=[{"role": "system", "content": system_prompt}]
        )

    def forward(self, file_path: str, instruction: str) -> str:
        if not os.path.isfile(file_path):
            return f"File does not exist: {file_path}"

        try:
            with open(file_path, "r") as f:
                original_content = f.read()
        except Exception as e:
            return f"Failed to read file: {e}"

        prompt = (
            f"Here is the file content:\n\n"
            f"{original_content}\n\n"
            f"---\n\n"
            f"Instruction:\n{instruction}\n\n"
            f"output the full, edited file content."
        )

        try:
            response = self.model(prompt)
        except Exception as e:
            return f"LLM failed: {e}"

        try:
            with open(file_path, "w") as f:
                f.write(response)
            return "File edited successfully."
        except Exception as e:
            return f"Failed to write file: {e}"
