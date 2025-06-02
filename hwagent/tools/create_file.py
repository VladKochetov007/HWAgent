"""MCP tool for creating files."""

import os
import asyncio
from pathlib import Path
from typing import Any

import mcp.types as types
from mcp.server import Server

from ..utils.config import config


async def create_file_tool(
    name: str,
    arguments: dict[str, Any]
) -> list[types.TextContent]:
    """
    Create a new file with specified content.
    
    Args:
        arguments: Dictionary containing:
            - file_path: Path where to create the file
            - content: Content to write to the file
            - encoding: File encoding (default: utf-8)
    """
    try:
        file_path = arguments.get("file_path")
        content = arguments.get("content", "")
        encoding = arguments.get("encoding", "utf-8")
        
        if not file_path:
            return [types.TextContent(
                type="text",
                text="Error: file_path is required"
            )]
        
        # Convert to Path object and resolve
        path = Path(file_path)
        
        # Security check - ensure file is within current working directory only
        current_dir = Path.cwd().resolve()
        
        # If path is absolute, reject it
        if path.is_absolute():
            return [types.TextContent(
                type="text",
                text=f"Error: Absolute paths not allowed. Use relative paths only. Path: {path}"
            )]
        
        # Resolve relative path from current directory
        try:
            resolved_path = (current_dir / path).resolve()
            # Ensure the resolved path is within current directory
            if not resolved_path.is_relative_to(current_dir):
                return [types.TextContent(
                    type="text",
                    text=f"Error: Path escapes session directory. Use relative paths only. Path: {path}"
                )]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error: Invalid path. Path: {path}, Error: {str(e)}"
            )]
        
        path = resolved_path
        
        # Check file size limit
        max_size = config.agent_settings["react_agent"]["max_file_size"]
        if len(content.encode(encoding)) > max_size:
            return [types.TextContent(
                type="text",
                text=f"Error: File content exceeds maximum size limit ({max_size} bytes)"
            )]
        
        # Create parent directories if they don't exist
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write the file
        with open(path, 'w', encoding=encoding) as f:
            f.write(content)
        
        return [types.TextContent(
            type="text",
            text=f"Successfully created file: {path}\nSize: {len(content)} characters"
        )]
        
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"Error creating file: {str(e)}"
        )]


def register_create_file_tool(server: Server) -> None:
    """Register the create_file tool with the MCP server."""
    
    @server.call_tool()
    async def create_file(name: str, arguments: dict) -> list[types.TextContent]:
        if name != "create_file":
            raise ValueError(f"Unknown tool: {name}")
        return await create_file_tool(name, arguments)
    
    # Update server tools list
    server._tools = getattr(server, '_tools', [])
    server._tools.append(types.Tool(
        name="create_file",
        description="Create a new file with specified content and encoding",
        inputSchema={
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path where to create the file (relative to working directory or in tmp)"
                },
                "content": {
                    "type": "string", 
                    "description": "Content to write to the file"
                },
                "encoding": {
                    "type": "string",
                    "description": "File encoding (default: utf-8)",
                    "default": "utf-8"
                }
            },
            "required": ["file_path"]
        }
    )) 