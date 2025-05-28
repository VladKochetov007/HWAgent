# HWAgent - Quick Start

## Quick guide to launching and using

### 1. Launching the Server

```bash
# Ensure dependencies are installed
pip install -r requirements_api.txt

# Set your API key
export OPENROUTER_API_KEY="your_api_key_here"

# Run the server
python run_api_server.py
```

### 2. Accessing the Web Interface

Open in your browser: **http://127.0.0.1:5000**

### 3. Usage

#### Web Interface
- 💬 **Chat**: Enter questions in the text field at the bottom
- ⚙️ **Settings**: Switch between streaming and standard mode
- 🛠️ **Tools**: View available agent tools
- 📊 **Session**: Information about the current session
- 🗑️ **Clear**: Clear conversation context
- 💾 **Export**: Save chat history to JSON

#### Hotkeys
- `Ctrl + Enter` - Send message
- `Shift + Enter` - New line

#### Agent Capabilities
- ✅ Mathematical calculations
- ✅ Python code creation and execution
- ✅ File operations
- ✅ Web search
- ✅ Shell command execution
- ✅ Data analysis

### 4. API Endpoints

#### Main Endpoints
- `GET /api/health` - Health check
- `POST /api/sessions` - Create a session
- `POST /api/sessions/{id}/messages` - Send a message
- `GET /api/tools` - List available tools

#### API Usage Example
```bash
# Create a session
curl -X POST http://127.0.0.1:5000/api/sessions

# Send a message
curl -X POST http://127.0.0.1:5000/api/sessions/{session_id}/messages \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello! Calculate 2+2"}'
```

### 5. Troubleshooting

#### Server Fails to Start
1. Check that all dependencies are installed.
2. Ensure the `OPENROUTER_API_KEY` environment variable is set.
3. Verify that port 5000 is free.

#### Web Interface Does Not Load
1. Make sure the server is running.
2. Check accessibility: `curl http://127.0.0.1:5000/api/health`
3. Clear your browser cache.

#### WebSocket Not Working
1. Check the browser console for connection errors.
2. Ensure there is no firewall blocking the connection.
3. Try refreshing the page.

### 6. Configuration

#### Environment Variables
```bash
# Required
export OPENROUTER_API_KEY="your_key"

# Optional
export HOST="0.0.0.0"      # Server host
export PORT="8080"         # Server port  
export DEBUG="true"        # Debug mode
```

#### Access from Other Devices
```bash
# Run with network access
export HOST="0.0.0.0"
python run_api_server.py
```

### 7. Features

- 🔄 **Streaming**: Real-time responses via WebSocket
- 📱 **Responsive**: Works on mobile devices
- 🔒 **Sessions**: Isolated contexts for each user
- 💾 **Export**: Save conversation history
- 🛠️ **Tools**: Full suite of tools for task solving

### 8. Support

If you encounter problems:
1. Check server logs in the terminal.
2. Open the browser's developer console (F12).
3. Ensure the configuration is correct.

**Ready!** 🎉 Now you can use HWAgent through the convenient web interface. 