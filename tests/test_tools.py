"""Tests for MCP tools functionality."""

import asyncio
import tempfile
import pytest
from pathlib import Path

from hwagent.tools.create_file import create_file_tool
from hwagent.tools.edit_file import edit_file_tool
from hwagent.tools.execute_command import execute_command_tool
from hwagent.tools.search_web import search_web_tool


class TestCreateFileTool:
    """Test create_file tool."""
    
    @pytest.mark.asyncio
    async def test_create_file_success(self):
        """Test successful file creation."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = str(Path(tmp_dir) / "test.txt")
            content = "Hello, World!"
            
            result = await create_file_tool("create_file", {
                "file_path": file_path,
                "content": content
            })
            
            assert len(result) == 1
            assert "Successfully created file" in result[0].text
            
            # Verify file was created
            assert Path(file_path).exists()
            with open(file_path, 'r') as f:
                assert f.read() == content
    
    @pytest.mark.asyncio
    async def test_create_file_missing_path(self):
        """Test error when file path is missing."""
        result = await create_file_tool("create_file", {
            "content": "test"
        })
        
        assert len(result) == 1
        assert "Error: file_path is required" in result[0].text
    
    @pytest.mark.asyncio
    async def test_create_file_large_content(self):
        """Test error when content is too large."""
        large_content = "x" * (11 * 1024 * 1024)  # 11MB
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = str(Path(tmp_dir) / "large.txt")
            
            result = await create_file_tool("create_file", {
                "file_path": file_path,
                "content": large_content
            })
            
            assert len(result) == 1
            assert "exceeds maximum size limit" in result[0].text


class TestExecuteCommandTool:
    """Test execute_command tool."""
    
    @pytest.mark.asyncio
    async def test_execute_simple_command(self):
        """Test executing a simple command."""
        result = await execute_command_tool("execute_command", {
            "command": "echo 'Hello, World!'"
        })
        
        assert len(result) == 1
        assert "Hello, World!" in result[0].text
        assert "Exit code: 0" in result[0].text
    
    @pytest.mark.asyncio
    async def test_execute_blocked_command(self):
        """Test blocking dangerous commands."""
        result = await execute_command_tool("execute_command", {
            "command": "sudo rm -rf /"
        })
        
        assert len(result) == 1
        assert "Command blocked for security reasons" in result[0].text
    
    @pytest.mark.asyncio
    async def test_execute_command_timeout(self):
        """Test command timeout."""
        result = await execute_command_tool("execute_command", {
            "command": "sleep 200",
            "timeout": 1
        })
        
        assert len(result) == 1
        assert "timed out" in result[0].text
    
    @pytest.mark.asyncio
    async def test_execute_nonexistent_command(self):
        """Test executing non-existent command."""
        result = await execute_command_tool("execute_command", {
            "command": "nonexistent_command_12345"
        })
        
        assert len(result) == 1
        assert "Command not found" in result[0].text


class TestSearchWebTool:
    """Test search_web tool."""
    
    @pytest.mark.asyncio
    async def test_search_web_missing_query(self):
        """Test error when query is missing."""
        result = await search_web_tool("search_web", {})
        
        assert len(result) == 1
        assert "Error: query is required" in result[0].text
    
    @pytest.mark.asyncio
    async def test_search_web_empty_query(self):
        """Test error when query is empty."""
        result = await search_web_tool("search_web", {
            "query": "   "
        })
        
        assert len(result) == 1
        assert "Error: query cannot be empty" in result[0].text
    
    @pytest.mark.asyncio
    async def test_search_web_invalid_max_results(self):
        """Test error with invalid max_results."""
        result = await search_web_tool("search_web", {
            "query": "test",
            "max_results": -1
        })
        
        assert len(result) == 1
        assert "must be a positive integer" in result[0].text


class TestEditFileTool:
    """Test edit_file tool."""
    
    @pytest.mark.asyncio
    async def test_edit_file_missing_file(self):
        """Test error when file doesn't exist."""
        result = await edit_file_tool("edit_file", {
            "file_path": "/tmp/nonexistent_file.txt",
            "instruction": "Add a comment"
        })
        
        assert len(result) == 1
        assert "File does not exist" in result[0].text
    
    @pytest.mark.asyncio
    async def test_edit_file_missing_instruction(self):
        """Test error when instruction is missing."""
        result = await edit_file_tool("edit_file", {
            "file_path": "/tmp/test.txt"
        })
        
        assert len(result) == 1
        assert "Error: instruction is required" in result[0].text 