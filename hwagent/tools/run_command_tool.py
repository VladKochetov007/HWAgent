"""
Tool for executing shell commands.
"""

import subprocess
from typing import Any, Dict

from hwagent.core import (
    BaseTool,
    Constants,
    ToolExecutionResult
)


class RunCommandTool(BaseTool):
    """Tool to execute a shell command."""
    name = "run_command"
    description = "Executes a shell command and returns its standard output and standard error. Use for tasks like compiling code, running scripts, etc."

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The shell command to execute."
                }
            },
            "required": ["command"]
        }

    def __init__(self, tmp_directory: str = Constants.DEFAULT_TMP_DIRECTORY):
        # tmp_directory is kept in __init__ for consistency with BaseTool, 
        # but not used in _execute_impl for this simplified version.
        super().__init__(tmp_directory)

    def _execute_impl(self, **kwargs: Any) -> ToolExecutionResult:
        command = kwargs.get("command")
        if not command:
            return ToolExecutionResult.error("Missing command parameter.", "'command' is required.")

        try:
            process = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=60, # 60-second timeout
                check=False # Do not raise CalledProcessError for non-zero exit codes, handle manually
                # cwd=self.tmp_directory is removed to run in agent's CWD
            )
            
            output = f"Exit Code: {process.returncode}\n"
            if process.stdout:
                output += f"Standard Output:\n{process.stdout}\n"
            if process.stderr:
                output += f"Standard Error:\n{process.stderr}\n"
            
            if process.returncode == 0:
                return ToolExecutionResult.success(output, "Command executed successfully.")
            else:
                return ToolExecutionResult.error(output, f"Command failed with exit code {process.returncode}.")

        except subprocess.TimeoutExpired:
            return ToolExecutionResult.error(
                "Command timed out after 60 seconds.", 
                "TimeoutExpired"
            )
        except Exception as e:
            return ToolExecutionResult.error(
                f"Error executing command '{command}': {str(e)}", 
                e.__class__.__name__
            ) 