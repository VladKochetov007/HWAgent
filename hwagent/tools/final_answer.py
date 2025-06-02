"""MCP tool for generating final answers with markdown explanations and file pinning."""

import os
import asyncio
from pathlib import Path
from typing import Any

import mcp.types as types
from mcp.server import Server

from ..utils.config import config


async def final_answer_tool(
    name: str,
    arguments: dict[str, Any]
) -> list[types.TextContent]:
    """
    Generate a final answer with markdown explanations and file pinning.
    
    Args:
        arguments: Dictionary containing:
            - summary: Brief summary of what was accomplished
            - explanation: Detailed markdown explanation of the solution
            - files_created: List of files created during the session
            - key_results: Important results or outputs to highlight
            - working_directory: Path to the session's working directory
    """
    try:
        summary = arguments.get("summary", "")
        explanation = arguments.get("explanation", "")
        files_created = arguments.get("files_created", [])
        key_results = arguments.get("key_results", [])
        working_directory = arguments.get("working_directory", "")
        
        if not summary:
            return [types.TextContent(
                type="text",
                text="Error: summary is required"
            )]
        
        if not explanation:
            return [types.TextContent(
                type="text",
                text="Error: explanation is required"
            )]
        
        # Create the final answer markdown
        markdown_content = generate_final_answer_markdown(
            summary, explanation, files_created, key_results, working_directory
        )
        
        # Create a final answer file in the working directory
        if working_directory:
            # Convert working_directory to proper path
            if working_directory == "./":
                work_dir = Path.cwd()
            else:
                work_dir = Path(working_directory)
                if not work_dir.is_absolute():
                    work_dir = Path.cwd() / work_dir
        else:
            work_dir = Path.cwd()
            
        final_answer_path = work_dir / "FINAL_ANSWER.md"
        try:
            with open(final_answer_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
        except Exception as e:
            # Non-critical error, continue without saving file
            pass
        
        return [types.TextContent(
            type="text",
            text=f"FINAL ANSWER GENERATED:\n\n{markdown_content}"
        )]
        
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"Error generating final answer: {str(e)}"
        )]


def generate_final_answer_markdown(
    summary: str,
    explanation: str,
    files_created: list[str],
    key_results: list[str],
    working_directory: str
) -> str:
    """
    Generate formatted markdown content for the final answer.
    
    Args:
        summary: Brief summary
        explanation: Detailed explanation
        files_created: List of created files
        key_results: List of key results
        working_directory: Working directory path
        
    Returns:
        Formatted markdown string
    """
    lines = []
    
    # Header
    lines.append("# 🎯 Final Answer")
    lines.append("")
    
    # Summary
    lines.append("## 📝 Summary")
    lines.append(summary)
    lines.append("")
    
    # Detailed explanation
    lines.append("## 📋 Detailed Explanation")
    lines.append(explanation)
    lines.append("")
    
    # Files created
    if files_created:
        lines.append("## 📁 Files Created")
        lines.append("")
        for file_path in files_created:
            # Show relative path from working directory
            if working_directory:
                try:
                    rel_path = Path(file_path).relative_to(Path(working_directory))
                    lines.append(f"- `{rel_path}`")
                except ValueError:
                    lines.append(f"- `{file_path}`")
            else:
                lines.append(f"- `{file_path}`")
        lines.append("")
    
    # Key results
    if key_results:
        lines.append("## 🔑 Key Results")
        lines.append("")
        for result in key_results:
            lines.append(f"- {result}")
        lines.append("")
    
    # Working directory info
    if working_directory:
        lines.append("## 📂 Session Directory")
        lines.append(f"All files are located in: `{working_directory}`")
        lines.append("")
        
        # Try to list all files in the directory
        try:
            work_path = Path(working_directory)
            if work_path.exists():
                all_files = list(work_path.rglob("*"))
                if all_files:
                    lines.append("### Complete File Listing:")
                    for file_path in sorted(all_files):
                        if file_path.is_file():
                            rel_path = file_path.relative_to(work_path)
                            file_size = file_path.stat().st_size
                            lines.append(f"- `{rel_path}` ({file_size} bytes)")
                    lines.append("")
        except Exception:
            # Non-critical error, skip file listing
            pass
    
    # Footer
    lines.append("---")
    lines.append("*Generated by HWAgent*")
    
    return "\n".join(lines)


def register_final_answer_tool(server: Server) -> None:
    """Register the final_answer tool with the MCP server."""
    
    @server.call_tool()
    async def final_answer(name: str, arguments: dict) -> list[types.TextContent]:
        if name != "final_answer":
            raise ValueError(f"Unknown tool: {name}")
        return await final_answer_tool(name, arguments)
    
    # Update server tools list
    server._tools = getattr(server, '_tools', [])
    server._tools.append(types.Tool(
        name="final_answer",
        description="Generate a comprehensive final answer with markdown explanations and file references",
        inputSchema={
            "type": "object",
            "properties": {
                "summary": {
                    "type": "string",
                    "description": "Brief summary of what was accomplished"
                },
                "explanation": {
                    "type": "string", 
                    "description": "Detailed markdown explanation of the solution and approach"
                },
                "files_created": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of file paths that were created during the session"
                },
                "key_results": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of important results, outputs, or findings"
                },
                "working_directory": {
                    "type": "string",
                    "description": "Path to the session's working directory"
                }
            },
            "required": ["summary", "explanation"]
        }
    )) 