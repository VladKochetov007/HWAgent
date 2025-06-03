# 🚀 HWAgent Launcher Scripts

Two universal scripts created for launching HWAgent system:

## 📁 Files

### `start_app.py` - Full Stack
🤖 **Complete launcher** with automatic setup:

**Features:**
- ✅ Check all dependencies
- 🚀 API server (localhost:8000)
- 🌐 Frontend server (localhost:3000)  
- 📁 Auto-create web interface
- 🌐 Auto-open browser
- 🛑 Graceful shutdown of both services

**Usage:**
```bash
python start_app.py
```

### `run_api.py` - API Only
⚡ **Quick launch** for development and testing:

**Features:**
- 🚀 API server only
- 📖 Swagger documentation
- ⚡ Fast startup
- 🔄 Hot reload

**Usage:**
```bash
python run_api.py
```

## 🌐 Web Interface

### Features
- 📤 **Drag & Drop** image upload
- 🎯 **Ready templates** for tasks
- ⚡ **Normal/Streaming** modes
- 📊 **Real-time** status indicators
- 📁 **Download** created files
- 🔔 **Toast** notifications
- 📱 **Responsive** design

### Design
- 🎨 Glassmorphism effects
- 🌈 Gradient elements
- ✨ Smooth animations
- 📊 Status indicators
- 🎯 Intuitive UX

## 🛠️ Architecture

```
start_app.py
├── 🔍 Dependency Check
├── 📁 Directory Setup
├── 🚀 API Server (uvicorn)
├── 🌐 Frontend Server (http.server)
├── ⏳ Health Monitoring
├── 🌐 Browser Launch
└── 🛑 Signal Handling
```

## 📊 Monitoring

### Automatic checks:
- 🟢 API Health Check every 30 sec
- 📡 Real-time connection status  
- 🔄 Automatic restart on failures
- ⚠️ Error notifications

### Logging:
- ✅ Successful operations
- ❌ Error reporting  
- 📊 Performance metrics
- 🔍 Debug information

## 🎯 Vision API Features

### Supported tasks:
- 📷 **Image Analysis** - content analysis
- 📝 **Text Recognition** - OCR extraction  
- 📐 **Math Solving** - equation solving
- 📊 **Data Extraction** - chart analysis
- 🎓 **Educational Content** - material creation

### File formats:
- **Input**: PNG, JPEG, JPG, GIF, BMP, WEBP
- **Output**: PDF, Python, LaTeX, TXT, JSON, CSV

## 🔧 Technical Details

### Backend Stack:
- **Framework**: FastAPI + uvicorn
- **Agent**: smolagents CodeAgent
- **AI**: OpenRouter (Gemini Flash Preview)
- **Vision**: PIL, OpenCV support

### Frontend Stack:
- **Core**: Vanilla HTML/CSS/JavaScript
- **Styling**: CSS Grid, Flexbox, Animations
- **API**: Fetch, Server-Sent Events
- **UX**: Drag & Drop, Toast notifications

## 🚦 Ports and Access

| Service | Port | URL | Description |
|---------|------|-----|-------------|
| API | 8000 | http://localhost:8000 | REST API endpoints |
| Docs | 8000 | http://localhost:8000/docs | Swagger UI |
| Health | 8000 | http://localhost:8000/health | Status check |
| Frontend | 3000 | http://localhost:3000 | Web interface |

## 🛡️ Security

- 🔒 Local-only binding by default
- 🚫 No external dependency injection
- ✅ Input validation and sanitization
- 🔐 Environment variables for API keys

---

**💡 Result:** Full-featured system for working with Vision AI agent through web interface or direct API calls! 