"""MCP tool for editing files using LLM."""

import os
import asyncio
from pathlib import Path
from typing import Any

import mcp.types as types
from mcp.server import Server

from ..utils.config import config
from ..utils.api_client import openrouter_client


async def edit_file_tool(
    name: str,
    arguments: dict[str, Any]
) -> list[types.TextContent]:
    """
    Edit an existing file using LLM assistance.
    
    Args:
        arguments: Dictionary containing:
            - file_path: Path to the file to edit
            - instruction: Instruction for how to edit the file
            - encoding: File encoding (default: utf-8)
    """
    try:
        file_path = arguments.get("file_path")
        instruction = arguments.get("instruction")
        encoding = arguments.get("encoding", "utf-8")
        
        if not file_path:
            return [types.TextContent(
                type="text",
                text="Error: file_path is required"
            )]
        
        if not instruction:
            return [types.TextContent(
                type="text",
                text="Error: instruction is required"
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
        
        # Check if file exists
        if not path.exists():
            return [types.TextContent(
                type="text",
                text=f"Error: File does not exist: {path}"
            )]
        
        # Read current file content
        try:
            with open(path, 'r', encoding=encoding) as f:
                current_content = f.read()
        except UnicodeDecodeError:
            return [types.TextContent(
                type="text",
                text=f"Error: Could not decode file with encoding {encoding}"
            )]
        
        # Check file size limit
        max_size = config.agent_settings["react_agent"]["max_file_size"]
        if len(current_content.encode(encoding)) > max_size:
            return [types.TextContent(
                type="text",
                text=f"Error: File exceeds maximum size limit ({max_size} bytes)"
            )]
        
        # Prepare messages for LLM
        system_prompt = config.prompts["simple"]["system_prompt"]
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"""Please edit the following file according to the instruction.

File path: {path}
Instruction: {instruction}

Current file content:
```
{current_content}
```

Please provide only the complete edited file content, without any explanations or markdown code blocks."""}
        ]
        
        # Get edited content from LLM
        try:
            edited_content = await openrouter_client.simple_completion(messages)
            
            # Remove potential markdown code blocks
            if edited_content.startswith("```") and edited_content.endswith("```"):
                lines = edited_content.split('\n')
                if len(lines) > 2:
                    # Remove first and last lines if they are markdown delimiters
                    if lines[0].startswith("```") and lines[-1] == "```":
                        edited_content = '\n'.join(lines[1:-1])
            
            # Write the edited content back to file
            with open(path, 'w', encoding=encoding) as f:
                f.write(edited_content)
            
            return [types.TextContent(
                type="text",
                text=f"Successfully edited file: {path}\nInstruction applied: {instruction}\nNew size: {len(edited_content)} characters"
            )]
            
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error calling LLM for file editing: {str(e)}"
            )]
        
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"Error editing file: {str(e)}"
        )]


def register_edit_file_tool(server: Server) -> None:
    """Register the edit_file tool with the MCP server."""
    
    @server.call_tool()
    async def edit_file(name: str, arguments: dict) -> list[types.TextContent]:
        if name != "edit_file":
            raise ValueError(f"Unknown tool: {name}")
        return await edit_file_tool(name, arguments)
    
    # Update server tools list
    server._tools = getattr(server, '_tools', [])
    server._tools.append(types.Tool(
        name="edit_file",
        description="Edit an existing file using LLM assistance with specific instructions",
        inputSchema={
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the file to edit (must exist)"
                },
                "instruction": {
                    "type": "string",
                    "description": "Clear instruction for how to edit the file"
                },
                "encoding": {
                    "type": "string",
                    "description": "File encoding (default: utf-8)",
                    "default": "utf-8"
                }
            },
            "required": ["file_path", "instruction"]
        }
    )) 