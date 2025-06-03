"""MCP tool for executing system commands."""

import asyncio
import subprocess
import shlex
from pathlib import Path
from typing import Any

import mcp.types as types
from mcp.server import Server

from ..utils.config import config


async def execute_command_tool(
    name: str,
    arguments: dict[str, Any]
) -> list[types.TextContent]:
    """
    Execute a system command with security restrictions.
    
    Args:
        arguments: Dictionary containing:
            - command: Command to execute
            - working_dir: Working directory (default: current directory)
            - timeout: Command timeout in seconds (default: from config)
    """
    try:
        command = arguments.get("command")
        working_dir = arguments.get("working_dir")
        timeout = arguments.get("timeout")
        
        if not command:
            return [types.TextContent(
                type="text",
                text="Error: command is required"
            )]
        
        # Security checks - blocked commands
        blocked_commands = config.agent_settings["react_agent"]["blocked_commands"]
        command_lower = command.lower().strip()
        
        for blocked in blocked_commands:
            if blocked.lower() in command_lower:
                return [types.TextContent(
                    type="text",
                    text=f"Error: Command blocked for security reasons: {blocked}"
                )]
        
        # Additional security checks
        dangerous_patterns = [
            "rm -rf", "format", "fdisk", "mkfs", "dd if=", ">/dev/", 
            "shutdown", "reboot", "init 0", "init 6", "halt",
            "passwd", "useradd", "userdel", "usermod",
            "chmod 777", "chown root", "sudo su"
        ]
        
        for pattern in dangerous_patterns:
            if pattern in command_lower:
                return [types.TextContent(
                    type="text",
                    text=f"Error: Potentially dangerous command blocked: {pattern}"
                )]
        
        # Set timeout
        if timeout is None:
            timeout = config.agent_settings["react_agent"]["tool_execution_timeout"]
        
        # Set working directory
        if working_dir:
            working_dir = Path(working_dir)
            
            # If working_dir is absolute, reject it
            if working_dir.is_absolute():
                return [types.TextContent(
                    type="text",
                    text=f"Error: Absolute working directory paths not allowed. Working directory: {working_dir}"
                )]
            
            # Resolve relative path from current directory
            current_dir = Path.cwd().resolve()
            try:
                resolved_working_dir = (current_dir / working_dir).resolve()
                # Ensure the resolved path is within current directory
                if not resolved_working_dir.is_relative_to(current_dir):
                    return [types.TextContent(
                        type="text",
                        text=f"Error: Working directory escapes session directory. Working directory: {working_dir}"
                    )]
                working_dir = resolved_working_dir
            except Exception as e:
                return [types.TextContent(
                    type="text",
                    text=f"Error: Invalid working directory path. Path: {working_dir}, Error: {str(e)}"
                )]
            
            if not working_dir.exists():
                return [types.TextContent(
                    type="text",
                    text=f"Error: Working directory does not exist: {working_dir}"
                )]
        else:
            working_dir = Path.cwd()
        
        # Execute command
        try:
            # Use shell=False for better security, parse command manually
            if isinstance(command, str):
                # Try to parse command safely
                try:
                    cmd_parts = shlex.split(command)
                except ValueError as e:
                    return [types.TextContent(
                        type="text",
                        text=f"Error: Invalid command syntax: {str(e)}"
                    )]
            else:
                cmd_parts = command
            
            # Run the command
            process = await asyncio.create_subprocess_exec(
                *cmd_parts,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return [types.TextContent(
                    type="text",
                    text=f"Error: Command timed out after {timeout} seconds"
                )]
            
            # Decode output
            stdout_text = stdout.decode('utf-8', errors='replace') if stdout else ""
            stderr_text = stderr.decode('utf-8', errors='replace') if stderr else ""
            
            # Check output size limit
            max_output_size = config.agent_settings["react_agent"]["max_command_output"]
            total_output_size = len(stdout_text.encode('utf-8')) + len(stderr_text.encode('utf-8'))
            
            # Prepare result
            result_parts = []
            result_parts.append(f"Command: {command}")
            result_parts.append(f"Working directory: {working_dir}")
            result_parts.append(f"Exit code: {process.returncode}")
            
            if total_output_size > max_output_size:
                result_parts.append(f"⚠️ WARNING: Command output is large ({total_output_size} bytes)")
            
            if stdout_text:
                result_parts.append(f"STDOUT:\n{stdout_text}")
            
            if stderr_text:
                result_parts.append(f"STDERR:\n{stderr_text}")
            
            if not stdout_text and not stderr_text:
                result_parts.append("No output")
            
            return [types.TextContent(
                type="text",
                text="\n\n".join(result_parts)
            )]
            
        except FileNotFoundError:
            return [types.TextContent(
                type="text",
                text=f"Error: Command not found: {cmd_parts[0] if cmd_parts else command}"
            )]
        except PermissionError:
            return [types.TextContent(
                type="text",
                text=f"Error: Permission denied to execute: {command}"
            )]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error executing command: {str(e)}"
            )]
        
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"Error in execute_command: {str(e)}"
        )]


def register_execute_command_tool(server: Server) -> None:
    """Register the execute_command tool with the MCP server."""
    
    @server.call_tool()
    async def execute_command(name: str, arguments: dict) -> list[types.TextContent]:
        if name != "execute_command":
            raise ValueError(f"Unknown tool: {name}")
        return await execute_command_tool(name, arguments)
    
    # Update server tools list
    server._tools = getattr(server, '_tools', [])
    server._tools.append(types.Tool(
        name="execute_command",
        description="Execute system commands with security restrictions. ALWAYS use non-interactive mode - never use commands that require user input or interaction. Use automatic/batch mode parameters.",
        inputSchema={
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Command to execute. CRITICAL: Always use non-interactive parameters. Examples: 'pdflatex -interaction=nonstopmode file.tex', 'pip install --yes package', 'apt-get install -y package', 'git clone --quiet repo'. Never use commands that wait for user input."
                },
                "working_dir": {
                    "type": "string",
                    "description": "Working directory for command execution (optional, defaults to current directory)"
                },
                "timeout": {
                    "type": "integer",
                    "description": "Command timeout in seconds (optional, defaults to config setting)"
                }
            },
            "required": ["command"]
        }
    )) 