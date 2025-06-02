"""Tests for ReAct agent functionality."""

import asyncio
import pytest
from unittest.mock import patch, AsyncMock

from hwagent.core import ReActAgent
from hwagent.utils.config import config


class TestReActAgent:
    """Test ReAct agent functionality."""
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self):
        """Test agent initialization and context management."""
        async with ReActAgent() as agent:
            assert agent.agent_id is not None
            assert agent.working_dir is not None
            assert agent.working_dir.exists()
            assert agent.max_iterations == config.agent_settings["react_agent"]["max_iterations"]
    
    @pytest.mark.asyncio
    async def test_agent_cleanup(self):
        """Test agent cleanup removes working directory."""
        agent = ReActAgent()
        await agent.__aenter__()
        working_dir = agent.working_dir
        
        assert working_dir.exists()
        
        await agent.__aexit__(None, None, None)
        
        # Check if cleanup was configured to remove directory
        cleanup_enabled = config.agent_settings["react_agent"]["cleanup_tmp_dirs"]
        if cleanup_enabled:
            assert not working_dir.exists()
    
    def test_parse_action_valid(self):
        """Test parsing valid action from response."""
        agent = ReActAgent()
        
        response = """
        Thought: I need to create a file
        Action: create_file
        Action Input: {"file_path": "test.py", "content": "print('hello')"}
        """
        
        action, action_input = agent.parse_action(response)
        
        assert action == "create_file"
        assert action_input == {"file_path": "test.py", "content": "print('hello')"}
    
    def test_parse_action_invalid_json(self):
        """Test parsing action with invalid JSON."""
        agent = ReActAgent()
        
        response = """
        Action: create_file
        Action Input: not valid json
        """
        
        action, action_input = agent.parse_action(response)
        
        assert action == "create_file"
        assert action_input == {"input": "not valid json"}
    
    def test_should_continue_final_answer(self):
        """Test should_continue with final answer."""
        agent = ReActAgent()
        
        response = "Final Answer: The solution is 42"
        assert not agent.should_continue(response)
        
        response = "I need to continue working"
        assert agent.should_continue(response)
    
    @pytest.mark.asyncio
    async def test_execute_tool_create_file(self):
        """Test executing create_file tool."""
        async with ReActAgent() as agent:
            result = await agent.execute_tool("create_file", {
                "file_path": str(agent.working_dir / "test.txt"),
                "content": "Hello, World!"
            })
            
            assert "Successfully created file" in result
            assert (agent.working_dir / "test.txt").exists()
    
    @pytest.mark.asyncio
    async def test_execute_tool_unknown(self):
        """Test executing unknown tool."""
        async with ReActAgent() as agent:
            result = await agent.execute_tool("unknown_tool", {})
            
            assert "Unknown tool" in result


class TestAgentHomeworkSolving:
    """Test agent on specific homework problems."""
    
    @pytest.mark.asyncio
    async def test_simple_math_problem(self):
        """Test solving a simple math problem."""
        problem = "Calculate the area of a circle with radius 5"
        
        # Mock the OpenRouter API calls
        with patch('hwagent.utils.api_client.openrouter_client.thinking_completion') as mock_thinking:
            mock_thinking.side_effect = [
                """Thought: I need to calculate the area of a circle with radius 5
Action: create_file
Action Input: {"file_path": "calculate_area.py", "content": "import math\\nradius = 5\\narea = math.pi * radius ** 2\\nprint(f'Area of circle with radius {radius}: {area:.2f}')"}""",
                
                """Thought: Now I'll execute the Python script to get the result
Action: execute_command
Action Input: {"command": "python calculate_area.py"}""",
                
                """Final Answer: The area of a circle with radius 5 is 78.54 square units.

The formula for the area of a circle is A = πr², where r is the radius.
With radius = 5:
A = π × 5² = π × 25 = 78.54 square units (rounded to 2 decimal places)"""
            ]
            
            async with ReActAgent() as agent:
                result = await agent.solve(problem)
                
                assert result['completed']
                assert result['total_iterations'] <= 3
                assert len(result['steps']) >= 2
                
                # Check that file creation and execution steps occurred
                actions = [step['action'] for step in result['steps'] if step['action']]
                assert 'create_file' in actions
                assert 'execute_command' in actions
    
    @pytest.mark.asyncio 
    async def test_research_problem(self):
        """Test solving a problem requiring web search."""
        problem = "What is the capital of Australia and its population?"
        
        # Mock the API calls
        with patch('hwagent.utils.api_client.openrouter_client.thinking_completion') as mock_thinking, \
             patch('hwagent.utils.api_client.langsearch_client.search') as mock_search:
            
            mock_search.return_value = [
                {
                    "title": "Canberra - Capital of Australia",
                    "url": "https://example.com/canberra",
                    "snippet": "Canberra is the capital city of Australia with a population of approximately 430,000 people."
                }
            ]
            
            mock_thinking.side_effect = [
                """Thought: I need to search for information about Australia's capital and its population
Action: search_web
Action Input: {"query": "capital of Australia population"}""",
                
                """Final Answer: The capital of Australia is Canberra, with a population of approximately 430,000 people.

Canberra is located in the Australian Capital Territory (ACT) and serves as the seat of the Australian government."""
            ]
            
            async with ReActAgent() as agent:
                result = await agent.solve(problem)
                
                assert result['completed']
                assert len(result['steps']) >= 1
                
                # Check that web search occurred
                actions = [step['action'] for step in result['steps'] if step['action']]
                assert 'search_web' in actions
    
    @pytest.mark.asyncio
    async def test_programming_problem(self):
        """Test solving a programming problem."""
        problem = "Write a Python function to find the factorial of a number and test it with n=5"
        
        # Mock the API calls
        with patch('hwagent.utils.api_client.openrouter_client.thinking_completion') as mock_thinking, \
             patch('hwagent.utils.api_client.openrouter_client.simple_completion') as mock_simple:
            
            mock_simple.return_value = """def factorial(n):
    if n == 0 or n == 1:
        return 1
    else:
        return n * factorial(n - 1)

# Test with n=5
result = factorial(5)
print(f"Factorial of 5 is: {result}")"""
            
            mock_thinking.side_effect = [
                """Thought: I need to create a Python function for factorial calculation
Action: create_file
Action Input: {"file_path": "factorial.py", "content": "# Initial file for factorial function"}""",
                
                """Thought: Now I'll edit the file to add the factorial function and test
Action: edit_file
Action Input: {"file_path": "factorial.py", "instruction": "Write a recursive factorial function and test it with n=5"}""",
                
                """Thought: Let me run the program to test it
Action: execute_command
Action Input: {"command": "python factorial.py"}""",
                
                """Final Answer: Here's the Python function to find the factorial of a number:

```python
def factorial(n):
    if n == 0 or n == 1:
        return 1
    else:
        return n * factorial(n - 1)
```

When tested with n=5, the factorial is 120 (5! = 5 × 4 × 3 × 2 × 1 = 120)."""
            ]
            
            async with ReActAgent() as agent:
                result = await agent.solve(problem)
                
                assert result['completed']
                assert len(result['steps']) >= 3
                
                # Check that file operations and execution occurred
                actions = [step['action'] for step in result['steps'] if step['action']]
                assert 'create_file' in actions
                assert 'edit_file' in actions
                assert 'execute_command' in actions 