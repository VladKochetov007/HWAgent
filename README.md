# HWAgent Streaming API with Vision Support

Hardware Agent with advanced streaming capabilities and Vision Language Model support for real-time task execution.

## 🎯 Key Features

- **🖼️ Vision Language Model Support** - Upload and analyze images with AI
- **🌊 Real-time Streaming** - Server-Sent Events for step-by-step execution 
- **📎 Smart File Detection** - Automatic file attachment detection
- **🔧 Hardware Operations** - Shell commands, file operations, code execution
- **🌐 Modern Web Interface** - Drag & drop image uploads, real-time streaming display
- **🧪 Comprehensive Testing** - Vision tests with geometric shapes
- **🎨 Clean User Experience** - System information automatically hidden from users

## 🚀 Quick Start

### Start the API Server
```bash
# With verbose output for debugging
HWAGENT_VERBOSE=1 python api_server.py

# Or normal mode
python api_server.py
```

### Start the Web Interface
```bash
# In another terminal
cd frontend && python -m http.server 3000
```

### Or Use the Demo Script
```bash
python demo_frontend.py
```

## 🖼️ Vision Capabilities

### Supported Image Formats
- PNG, JPEG, JPG, GIF, BMP, WEBP
- Base64 encoded images
- Drag & drop file uploads
- **📋 Clipboard paste (Ctrl+V)** - Perfect for screenshots

### Vision Features
- Shape and color recognition
- Multiple object analysis
- Image comparison
- Pattern detection
- Natural language descriptions in multiple languages

### Example Usage
```python
# Upload an image and analyze it
task_data = {
    "task": "Describe what you see in this image",
    "max_steps": 3,
    "images": ["path/to/image.png"]  # or base64 data
}
```

## 🌊 Streaming API

### Real-time Task Execution
```bash
curl -X POST "http://localhost:8000/stream-task" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Create a Python script and analyze an image", 
    "max_steps": 5,
    "images": ["uploads/image.png"]
  }'
```

### Response Format
```json
{
  "step_number": 1,
  "step_type": "action", 
  "observations": "Step details...",
  "action_output": "Result...",
  "files": ["generated_file.py"],
  "has_files": true,
  "input_images": ["uploaded_image.png"],
  "image_count": 1
}
```

## 📎 File Handling

### Automatic File Detection
- Files mentioned in agent responses are automatically detected
- `ATTACHED_FILES:` system information is hidden from users
- Files remain accessible via the `/files/` endpoint

### File Access
```bash
# Get file info
curl "http://localhost:8000/files/info/script.py"

# Download file  
curl "http://localhost:8000/files/script.py"

# List all files
curl "http://localhost:8000/files"
```

## 🧪 Testing

### Run All Tests
```bash
python tests/run_tests.py
```

### Test Categories
```bash
# Basic API functionality
python -m pytest tests/test_api_basic.py -v

# Streaming capabilities  
python -m pytest tests/test_streaming.py -v

# Vision functionality
python -m pytest tests/test_vision.py -v
```

### Quick Vision Test
```bash
# Generate test images and run vision tests
python tests/create_test_images.py
python test_vision_quick.py
```

## 📡 API Endpoints

### Core Endpoints
- `POST /run-task` - Execute task synchronously
- `POST /stream-task` - Execute task with streaming 
- `GET /health` - Health check with capabilities
- `GET /files` - List available files

### Vision Endpoints
- `POST /upload-image` - Upload single image
- `POST /upload-images` - Upload multiple images
- `GET /files/{path}` - Serve uploaded images

### Image Upload Example
```python
import requests

# Upload image
with open('image.png', 'rb') as f:
    files = {'file': ('image.png', f, 'image/png')}
    data = {'description': 'Test image'}
    response = requests.post('http://localhost:8000/upload-image', 
                           files=files, data=data)
    image_path = response.json()['file_path']

# Use in task
task_data = {
    "task": "Analyze this image",
    "images": [image_path]
}
```

## 🎨 Web Interface Features

- **Drag & Drop Image Upload** - Intuitive file handling
- **📋 Clipboard Paste Support** - Press Ctrl+V to paste images from clipboard
- **Real-time Streaming Display** - See agent progress live
- **Automatic File Links** - Generated files are clickable
- **Vision Task Support** - Optional image uploads for any task
- **Clean Result Display** - System information automatically hidden
- **Multi-language Support** - Works with Russian and English prompts

## 🔧 Configuration

### Environment Variables
```bash
# Enable verbose mode for debugging
HWAGENT_VERBOSE=1

# API keys (set in .env file)
OPENROUTER_API_KEY=your_key_here
```

### Agent Settings
See `hwagent/config/` for:
- `agent_settings.yaml` - Max steps, imports, etc.
- `api.yaml` - Model configuration  
- `prompts.yaml` - System prompts

## 🛠️ Development

### Project Structure
```
HWAgent/
├── api_server.py           # Main FastAPI server
├── hwagent/               # Core agent logic
├── frontend/              # Web interface files  
├── tests/                 # Comprehensive test suite
├── test_images/           # Generated test images
└── uploads/               # User uploaded files
```

### Adding New Features
1. Update agent logic in `hwagent/`
2. Add API endpoints in `api_server.py`
3. Create tests in `tests/`
4. Update frontend if needed

## 📋 Requirements

```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0  
smolagents
Pillow>=10.0.0
pydantic>=2.5.0
python-dotenv
```

## 🎯 Example Use Cases

### Vision Tasks
- **Document Analysis** - Extract text and analyze layouts
- **Quality Control** - Detect defects in manufacturing
- **Content Moderation** - Analyze images for compliance
- **Scientific Research** - Analyze experimental results

### Automation Tasks  
- **File Processing** - Batch operations with real-time progress
- **System Administration** - Server management with monitoring
- **Data Analysis** - Process datasets with step-by-step updates
- **Code Generation** - Create and test code with immediate feedback

## 🔍 Troubleshooting

### Common Issues
- **Vision not working**: Check image format and size
- **Streaming stops**: Verify network connection
- **Files not detected**: Check `ATTACHED_FILES:` format
- **API not responding**: Restart with `HWAGENT_VERBOSE=1`

### Debug Mode
```bash
# Enable verbose logging
HWAGENT_VERBOSE=1 python api_server.py

# Check API health
curl http://localhost:8000/health
```

---

**Made with ❤️ for advanced AI automation** 