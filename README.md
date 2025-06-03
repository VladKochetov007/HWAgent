# 🤖 HWAgent AI Assistant - Full Stack

Complete HWAgent stack with support for both regular text tasks and Vision Language Models for working with images.

## 🚀 Quick Start

```bash
python start_app.py
```

This script automatically:
- ✅ Checks dependencies
- 🚀 Starts API server (localhost:8000)
- 🌐 Starts frontend (localhost:3000)
- 📁 Creates minimal web interface if it doesn't exist
- 🌐 Opens browser automatically

## 🎯 Features

### 💻 Text Tasks (without images)
- 🧮 **Programming** - creating code in Python, JavaScript, etc.
- 📚 **Education** - explanations of concepts and terms
- 🔍 **Analysis** - research and comparisons
- ✍️ **Creative Writing** - writing texts and stories
- 📊 **Calculations** - mathematical computations
- 📋 **Planning** - creating plans and strategies

### 🖼️ Vision Tasks (with images)
- 📷 **Image Analysis** - content description
- 📝 **Text Recognition** - OCR from images
- 📐 **Math Solving** - formulas and equations from pictures
- 📊 **Data Extraction** - analysis of charts and graphs
- 🎓 **Educational Materials** - creating content based on images

### 🌐 Web Interface
- 📤 **Optional image upload** (not required!)
- 🎯 **Ready templates** for text and vision tasks
- ⚡ **Normal/Streaming** execution modes
- 📁 **File downloads** created by the agent
- 🔄 **Reactive interface** with notifications

## 🌐 Access

After startup, available at:
- **Web Interface**: http://localhost:3000
- **API Server**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 🎯 Usage Examples

### Text Tasks (no images needed)

1. **Programming:**
   ```
   "Write a Python function that calculates the factorial of a number"
   ```

2. **Education:**
   ```
   "Explain the concept of machine learning in simple terms"
   ```

3. **Analysis:**
   ```
   "Analyze the pros and cons of renewable energy sources"
   ```

4. **Mathematics:**
   ```
   "Calculate the compound interest for $1000 invested at 5% annually for 10 years"
   ```

### Vision Tasks (require images)

1. **Image Analysis:**
   ```
   "Analyze this image and describe what you see in detail"
   ```

2. **Text Recognition:**
   ```
   "Extract all text from this image and transcribe it"
   ```

3. **Math Solving:**
   ```
   "Solve the mathematical equation shown in this image step by step"
   ```

4. **Code Creation:**
   ```
   "Based on this diagram, create Python code that implements the shown algorithm"
   ```

## ⚙️ Technical Details

### Architecture
- **Backend**: FastAPI + smolagents + OpenRouter
- **Frontend**: Vanilla HTML/CSS/JS
- **AI Models**: Google Gemini Flash Preview (vision), Llama 3.2 (text)
- **File Processing**: PIL, OpenCV support

### API Endpoints
- `POST /run-task` - Execute task (with or without images)
- `POST /stream-task` - Streaming execution
- `POST /upload-image` - Upload image (optional)
- `GET /files/{path}` - Download files
- `GET /health` - System status

### Supported Formats
- **Images**: PNG, JPEG, JPG, GIF, BMP, WEBP (optional)
- **Output Files**: PDF, Python, LaTeX, TXT, JSON, etc.

## 🛠️ Configuration

### Environment Variables
```bash
export OPENROUTER_API_KEY="your_key_here"
```

### Model Configuration
Edit `hwagent/config/api.yaml`:
```yaml
openrouter:
  thinking_model: google/gemini-2.5-flash-preview-05-20:thinking
  simple_model: meta-llama/llama-3.2-3b-instruct
```

## 🛑 Stopping

Press `Ctrl+C` in terminal to stop all services.

## 🐛 Troubleshooting

### Ports Busy
```bash
# Stop processes on ports
sudo lsof -ti:8000 | xargs kill -9
sudo lsof -ti:3000 | xargs kill -9
```

### Missing Dependencies
```bash
pip install fastapi uvicorn Pillow requests
```

### Agent Issues
Check configuration in `hwagent/config/` folder

---

**💡 New:** The agent now works both with and without images! Image upload is completely optional - you can solve regular tasks without visual content. 🎉 