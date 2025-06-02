"""
Tools package for HWAgent
Exports all available tools for use by the tool manager.
"""

# Core tool functionality
from hwagent.core.base_tool import BaseTool, FileOperationTool

# File operation tools
from .create_file_tool import CreateFileTool
from .read_file_tool import ReadFileTool

# Execution tools
from .execute_code_tool import ExecuteCodeTool

# Web tools
from .web_search_tool import WebSearchTool
from .enhanced_web_search_tool import EnhancedWebSearchTool
from .memory_tool import MemoryTool

# Export all tools
__all__ = [
    "BaseTool",
    "FileOperationTool",
    "CreateFileTool", 
    "ReadFileTool",
    "WebSearchTool",
    "EnhancedWebSearchTool",
    "MemoryTool"
]

# Legacy support - deprecated tools (will be removed in future versions)
# These are kept for backward compatibility but should not be used in new code
try:
    from .latex_compile_tool import LaTeXCompileTool
    
    __all__.extend([
        "LaTeXCompileTool",
    ])
except ImportError:
    # Legacy tools not available, which is fine
    pass 