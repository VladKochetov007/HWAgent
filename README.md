# HWAgent - AI Agent with Web Interface

HWAgent is an intelligent AI agent that can perform various tasks using tools, with both command-line and web interfaces.

## Features

- 🤖 **ReAct Agent Pattern** - Think, Plan, Act cycle for complex reasoning
- 🛠️ **Multiple Tools** - File operations, code execution, web search
- 🌐 **Web Interface** - Real-time chat with streaming responses
- 🔌 **WebSocket Support** - Live communication between frontend and backend
- 📝 **Tool Calls Visualization** - See agent's tool usage in real-time
- 💬 **Context Management** - Persistent conversation history
- 🎨 **Modern UI** - Beautiful, responsive chat interface
- 🐍 **Automatic Script Generation** - Creates Python scripts for precise calculations
- 🔢 **Computation Accuracy** - Avoids LLM calculation errors by using code execution
- ✨ **Smart Task Detection** - Automatically identifies when to use scripts vs direct answers

## Available Tools

1. **create_file** - Create new files with specified content
2. **delete_file** - Delete existing files
3. **list_files** - List files in directories
4. **read_file** - Read file contents
5. **execute_code** - Execute Python code safely
6. **web_search** - Search the web for information (requires API key)

## Setup

### Prerequisites

- Python 3.12+
- Virtual environment (recommended)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd HWAgent
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   
   Create a `.env` file in the root directory:
   ```env
   OPENROUTER_API_KEY=your_openrouter_api_key_here
   LANGSEARCH_API_KEY=your_langsearch_api_key_here  # Optional, for web search
   ```

5. **Configure API settings** (optional)
   
   Edit `hwagent/config/api.yaml` to change the model or API endpoint:
   ```yaml
   openrouter:
     base_url: https://openrouter.ai/api/v1
     model: google/gemini-2.5-flash-preview
   ```

## Usage

### Command Line Interface

Run the agent from the command line:

```bash
python run_hwagent.py
```

This will start an interactive session where you can chat with the agent directly in the terminal.

### Web Interface

Start the web server:

```bash
python run_web_server.py
```

Then open your browser and navigate to:
- **Frontend**: http://localhost:5000
- **Health Check**: http://localhost:5000/api/health
- **Tools API**: http://localhost:5000/api/tools

## Web Interface Features

- **Real-time chat** with streaming responses
- **Agent reasoning visualization** - see THOUGHT and PLAN sections
- **Tool call monitoring** - watch the agent use tools in real-time
- **Context management** - clear context or get summary
- **File upload support** (planned)
- **Keyboard shortcuts**:
  - `/clear` + Tab - Clear context
  - `/context` + Tab - Get context summary

## Automatic Script Generation

HWAgent is designed to avoid LLM calculation errors by automatically creating and executing Python scripts for computational tasks. This ensures accuracy and reliability.

### When Scripts Are Created Automatically

The agent will create Python scripts for:

✅ **Mathematical calculations**
```
User: "Calculate the sum of squares from 1 to 1000"
Agent: Creates and executes a Python script with the calculation
```

✅ **Data analysis and processing**
```
User: "Parse this JSON data and find patterns"
Agent: Creates a script to process the JSON systematically
```

✅ **File processing tasks**
```
User: "Count words in all text files in a directory"
Agent: Creates a script to iterate through files and count words
```

✅ **Complex logical operations**
```
User: "Generate prime numbers up to 10000"
Agent: Creates an optimized Python script for prime generation
```

✅ **Unit conversions and formulas**
```
User: "Convert 100 mph to km/h and calculate fuel efficiency"
Agent: Creates a script with precise conversion formulas
```

### When Direct Answers Are Given

❌ **Simple factual questions**
```
User: "What is the capital of France?"
Agent: Direct answer - "Paris"
```

❌ **Concept explanations**
```
User: "Explain how machine learning works"
Agent: Direct explanation without code
```

### Script Quality Features

- **Error handling** - Scripts include try-catch blocks
- **Input validation** - Proper data type checking
- **Progress indicators** - For long-running computations
- **Intermediate outputs** - Shows step-by-step progress
- **Clean formatting** - Well-commented and readable code
- **Library usage** - Leverages numpy, pandas, requests when appropriate

### Example Workflow

1. **User asks**: "Calculate compound interest for $1000 at 5% for 10 years"
2. **Agent thinks**: This requires precise calculation → Create script
3. **Agent creates**: `compound_interest.py` with proper formula
4. **Agent executes**: Runs the script and gets exact result
5. **Agent responds**: Shows both the script and the calculated result

This approach eliminates common LLM issues like:
- Rounding errors in calculations
- Incorrect formula applications  
- Memory limitations for large computations
- Inconsistent results across similar problems

## API Endpoints

### HTTP Endpoints

- `GET /` - Serve frontend
- `GET /api/health` - Health check and status
- `GET /api/tools` - List available tools

### WebSocket Events

**Client → Server:**
- `send_message` - Send user message
- `clear_context` - Clear conversation history
- `get_context_summary` - Get context summary

**Server → Client:**
- `connected` - Connection established
- `user_message` - User message received
- `iteration_start` - Agent iteration started
- `thought` - Agent's thinking process
- `plan` - Agent's plan
- `stream_start/chunk/end` - Streaming response
- `tool_call_start/result/error` - Tool execution
- `final_answer` - Agent's final response
- `error` - Error messages

## Development

### Adding New Tools

1. Create a new tool class inheriting from `BaseTool`
2. Place it in `hwagent/tools/` with `_tool.py` suffix
3. Implement required methods: `name`, `description`, `get_parameters_schema`, `execute`
4. The tool will be automatically discovered and registered

Example tool structure:
```python
from hwagent.core import BaseTool, ToolExecutionResult

class MyCustomTool(BaseTool):
    @property
    def name(self) -> str:
        return "my_tool"
    
    @property 
    def description(self) -> str:
        return "Description of what this tool does"
    
    def get_parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "param1": {"type": "string", "description": "Parameter description"}
            },
            "required": ["param1"]
        }
    
    def execute(self, **kwargs) -> ToolExecutionResult:
        # Implementation here
        return ToolExecutionResult.success("Tool executed successfully")
```

### Architecture

The project follows SOLID principles and clean architecture:

- **Single Responsibility**: Each class has one reason to change
- **Open/Closed**: Tools can be added without modifying existing code
- **Liskov Substitution**: All tools implement the same interface
- **Interface Segregation**: Interfaces are focused and minimal
- **Dependency Inversion**: High-level modules don't depend on low-level modules

## Technologies Used

- **Backend**: Python 3.12, Flask, Flask-SocketIO, OpenAI API
- **Frontend**: HTML5, CSS3, JavaScript (ES6+), Socket.IO
- **AI Model**: Configurable (default: Google Gemini 2.5 Flash via OpenRouter)
- **Tools**: File system operations, Python code execution, web search

## Configuration

### Prompts

Agent behavior can be customized by editing `hwagent/config/prompts.yaml`. This includes:
- System prompts
- ReAct formatting instructions
- Error messages
- Critical analysis guidelines

### API Settings

API configuration is in `hwagent/config/api.yaml`:
- Model selection
- API endpoint
- Request parameters

## Troubleshooting

### Agent not initializing
- Check that `OPENROUTER_API_KEY` is set in `.env`
- Verify API configuration in `hwagent/config/api.yaml`
- Check logs for specific error messages

### Web search not working
- Ensure `LANGSEARCH_API_KEY` is set in `.env`
- Web search tool will show warnings if API key is missing

### Port conflicts
- Change port in `run_web_server.py` if 5000 is occupied
- Update frontend connections accordingly

## License

This project is open source and available under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.
