import subprocess
from smolagents import Tool

class ShellTool(Tool):
    name = "shell"
    description = """Execute a shell command and return the output. 
    Remember to use non-interactive command parameters (no user input required). 
    e.g. pdflatex --interaction=nonstopmode"""
    inputs = {
        "command": {
            "type": "string",
            "description": "Shell command to execute"
        }
    }
    output_type = "string"

    def forward(self, command: str) -> str:
        try:
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            return f"Command failed: {e.stderr.strip()}"
