# HWAgent - Homework Solving Agent

Асинхронный ReAct агент для решения домашних заданий с использованием Model Context Protocol (MCP) инструментов.

## Features

- 🤖 **ReAct Agent**: Reasoning and Acting approach with up to 25 iterations
- 🔧 **MCP Tools**: Model Context Protocol integration for tool execution
- 📁 **File Management**: Create and edit files with LLM assistance  
- ⚡ **Code Execution**: Safe command execution with security restrictions
- 🌐 **Web Search**: LangSearch API integration for information retrieval
- 🔒 **Security**: Built-in safety measures for command execution
- 📊 **Multiple Instances**: Isolated tmp directories for concurrent agents
- 🚀 **Async/Await**: Full asynchronous operation

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/HWAgent.git
cd HWAgent
```

2. Create virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

## Configuration

### Environment Variables (.env)
```bash
# OpenRouter API Configuration  
OPENROUTER_API_KEY=your-openrouter-api-key
LANGSEARCH_API_KEY=your-langsearch-api-key

# Logging
LOG_LEVEL=INFO

# Application
DEBUG=False
```

### Configuration Files

- `hwagent/config/api.yaml` - API endpoints and models
- `hwagent/config/agent_settings.yaml` - Agent behavior settings
- `hwagent/config/prompts.yaml` - System prompts for different models

## Usage

### Command Line Interface

Solve a problem directly from command line:
```bash
python run_agent.py --mode cli --problem "Calculate the area of a circle with radius 5"
```

With custom agent ID:
```bash
python run_agent.py --mode cli --problem "Write Python function for factorial" --agent-id "my-agent-123"
```

### API Server

Start the web API server:
```bash
python run_agent.py --mode api --host 0.0.0.0 --port 5000
```

API endpoints:
- `GET /health` - Health check
- `GET /tools` - List available tools
- `POST /solve` - Solve homework problem

Example API request:
```bash
curl -X POST http://localhost:5000/solve \
  -H "Content-Type: application/json" \
  -d '{
    "problem": "Write a Python function to calculate fibonacci numbers",
    "agent_id": "optional-custom-id"
  }'
```

### Python API

Use directly in Python code:
```python
import asyncio
from hwagent import ReActAgent

async def solve_homework():
    async with ReActAgent() as agent:
        result = await agent.solve("Calculate 2^10 using Python")
        print(f"Completed: {result['completed']}")
        print(f"Steps: {result['total_iterations']}")

asyncio.run(solve_homework())
```

## Available Tools

### 1. create_file
Create new files with any content and extension.

**Parameters:**
- `file_path`: Path where to create the file
- `content`: Content to write to the file  
- `encoding`: File encoding (default: utf-8)

### 2. edit_file
Edit existing files using LLM assistance.

**Parameters:**
- `file_path`: Path to the file to edit
- `instruction`: Clear instruction for how to edit the file
- `encoding`: File encoding (default: utf-8)

### 3. execute_command
Execute system commands with security restrictions.

**Parameters:**
- `command`: Command to execute
- `working_dir`: Working directory (optional)
- `timeout`: Command timeout in seconds (optional)

### 4. search_web
Search the web using LangSearch API.

**Parameters:**
- `query`: Search query
- `max_results`: Maximum number of results (optional)

## Security Features

- **Command Blocking**: Dangerous commands like `rm -rf`, `sudo`, etc. are blocked
- **Path Restrictions**: File operations limited to working directory and tmp folders
- **Size Limits**: File size limits to prevent abuse
- **Timeouts**: Command execution timeouts to prevent hanging
- **Safe Parsing**: Secure command parsing without shell injection

## Testing

Run tests:
```bash
pytest tests/ -v
```

Run specific test categories:
```bash
# Test tools functionality
pytest tests/test_tools.py -v

# Test agent functionality
pytest tests/test_agent.py -v
```

## Project Structure

```
HWAgent/
├── hwagent/
│   ├── config/           # Configuration files
│   │   ├── agent_settings.yaml
│   │   ├── api.yaml
│   │   └── prompts.yaml
│   ├── core/            # Core agent logic
│   │   └── react_agent.py
│   ├── tools/           # MCP tools (one per file)
│   │   ├── create_file.py
│   │   ├── edit_file.py
│   │   ├── execute_command.py
│   │   └── search_web.py
│   ├── utils/           # Utilities
│   │   ├── config.py
│   │   └── api_client.py
│   ├── api/             # Web API
│   │   └── agent_api.py
│   └── main.py          # Main entry point
├── tests/               # Tests
│   ├── test_tools.py
│   └── test_agent.py
├── run_agent.py         # Executable script
├── requirements.txt
└── README.md
```

## Configuration Details

### Agent Settings (agent_settings.yaml)
```yaml
react_agent:
  max_iterations: 25              # Maximum ReAct iterations
  thinking_timeout: 300           # LLM response timeout
  tool_execution_timeout: 120     # Tool execution timeout
  tmp_dir_prefix: "hwagent_"      # Temp directory prefix
  cleanup_tmp_dirs: true          # Cleanup on exit
  max_file_size: 10485760        # Max file size (10MB)
  blocked_commands:               # Security blocked commands
    - "rm -rf /"
    - "sudo"
  web_search:
    max_results: 10
    timeout: 30
```

### API Configuration (api.yaml)
```yaml
openrouter:
  base_url: https://openrouter.ai/api/v1
  thinking_model: google/gemini-2.5-flash-preview-05-20:thinking
  simple_model: meta-llama/llama-3.2-3b-instruct
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Troubleshooting

### Common Issues

1. **API Key Errors**: Ensure your API keys are correctly set in `.env`
2. **Permission Errors**: Check file permissions for tmp directories
3. **Command Blocked**: Review security settings in agent_settings.yaml
4. **Timeout Issues**: Adjust timeout settings in configuration

### Debug Mode

Enable debug logging:
```bash
export DEBUG=True
export LOG_LEVEL=DEBUG
python run_agent.py --mode cli --problem "your problem"
```

## Examples

### Mathematical Problem
```bash
python run_agent.py --mode cli --problem "Find the derivative of x^3 + 2x^2 - 5x + 1"
```

### Programming Task  
```bash
python run_agent.py --mode cli --problem "Write a Python class for a binary search tree with insert, search, and delete methods"
```

### Research Question
```bash
python run_agent.py --mode cli --problem "What are the latest developments in quantum computing in 2024?"
```

### Data Analysis
```bash
python run_agent.py --mode cli --problem "Create a Python script to analyze a CSV file with sales data and generate visualizations"
```

