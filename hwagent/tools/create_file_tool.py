"""
Create File Tool - creates new files with specified content.
Refactored to use core components and follow SOLID principles.
"""

from typing import Any
from hwagent.core import FileOperationTool, ToolExecutionResult, ParameterValidator, SecurityValidator
from pathlib import Path


class CreateFileTool(FileOperationTool):
    """Tool for creating new files with specified content"""
    
    def _remove_unwanted_quotes(self, content: str) -> str:
        """Remove unwanted quotes from beginning and end of content"""