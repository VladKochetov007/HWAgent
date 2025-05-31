"""
Tools package for HWAgent
Exports all available tools for use by the tool manager.
"""

# Core tool functionality
from hwagent.core.base_tool import BaseTool, FileOperationTool

# File operation tools
from .create_file_tool import CreateFileTool
from .read_file_tool import ReadFileTool
from .delete_file_tool import DeleteFileTool
from .list_files_tool import ListFilesTool

# Execution tools
from .execute_code_tool import ExecuteCodeTool

# Web tools
from .web_search_tool import WebSearchTool
from .enhanced_web_search_tool import EnhancedWebSearchTool
from .memory_tool import MemoryTool

# Unified LaTeX tool (replaces all separate LaTeX tools)
from .unified_latex_tool import UnifiedLaTeXTool

# Export all tools
__all__ = [
    "BaseTool",
    "FileOperationTool",
    "CreateFileTool", 
    "ReadFileTool",
    "DeleteFileTool",
    "ListFilesTool",
    "ExecuteCodeTool",
    "WebSearchTool",
    "EnhancedWebSearchTool",
    "MemoryTool",
    "UnifiedLaTeXTool"
]

# Legacy support - deprecated tools (will be removed in future versions)
# These are kept for backward compatibility but should not be used in new code
try:
    from .simple_latex_tool import SimpleLaTeXTool
    from .smart_latex_generator_tool import SmartLaTeXGenerator
    from .latex_compile_tool import LaTeXCompileTool
    from .latex_fix_tool import LaTeXFixTool
    
    __all__.extend([
        "SimpleLaTeXTool",
        "SmartLaTeXGenerator", 
        "LaTeXCompileTool",
        "LaTeXFixTool"
    ])
except ImportError:
    # Legacy tools not available, which is fine
    pass 