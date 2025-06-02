"""MCP Tools package for HWAgent."""

from mcp.server import Server
from mcp.server.lowlevel import NotificationOptions
from mcp.server.models import InitializationOptions

from .create_file import register_create_file_tool
from .edit_file import register_edit_file_tool
from .execute_command import register_execute_command_tool
from .search_web import register_search_web_tool
from .final_answer import register_final_answer_tool


def create_mcp_server() -> Server:
    """Create and configure MCP server with all tools."""
    server = Server("hwagent-tools")
    
    # Register all tools
    register_create_file_tool(server)
    register_edit_file_tool(server)
    register_execute_command_tool(server)
    register_search_web_tool(server)
    register_final_answer_tool(server)
    
    return server


__all__ = [
    "create_mcp_server",
    "register_create_file_tool",
    "register_edit_file_tool", 
    "register_execute_command_tool",
    "register_search_web_tool",
    "register_final_answer_tool"
]
