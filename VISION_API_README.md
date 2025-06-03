# HWAgent API with Vision Language Models Support

Updated API version now supports Vision Language Models (VLMs) according to the latest [smolagents](https://huggingface.co/blog/smolagents-can-see) capabilities and modern [VLM 2025 trends](https://huggingface.co/blog/vlms-2025).

## 🆕 New Features

### 🖼️ Image Support
- Image upload via API
- Image analysis using Vision Language Models
- Support for multiple images in a single request
- Base64 encoding and regular file upload

### 📋 Supported Formats
- PNG, JPEG, JPG, GIF, BMP, WEBP
- Automatic image validation
- Secure processing and storage

## 🔧 New API Endpoints

### Image Upload

#### Single Upload
```http
POST /upload-image
Content-Type: multipart/form-data

file: [image file]
description: "Description of the image"
```

#### Multiple Upload
```http
POST /upload-images
Content-Type: multipart/form-data

files: [array of image files]
```

### Tasks with Images

#### Regular Request with Images
```http
POST /run-task
Content-Type: application/json

{
    "task": "Analyze this image and describe what you see",
    "images": ["path/to/image.jpg", "data:image/png;base64,iVBOR..."],
    "max_steps": 8
}
```

#### Streaming Request with Images
```http
POST /stream-task
Content-Type: application/json

{
    "task": "Create a lesson plan based on this diagram",
    "images": ["uploads/diagram.png"],
    "max_steps": 10
}
```

## 💡 Usage Examples

### Python Example

```python
import requests

# 1. Upload image
with open('my_image.jpg', 'rb') as f:
    files = {'file': f}
    data = {'description': 'Math diagram'}
    upload_response = requests.post(
        'http://localhost:8000/upload-image', 
        files=files, 
        data=data
    )
    image_path = upload_response.json()['file_path']

# 2. Analyze image
task_response = requests.post(
    'http://localhost:8000/run-task',
    json={
        "task": "Analyze this mathematical diagram and explain the concepts",
        "images": [image_path],
        "max_steps": 6
    }
)

result = task_response.json()
print(f"Analysis: {result['result']}")
if result['has_attachments']:
    print(f"Generated files: {result['files']}")
```

### JavaScript Example

```javascript
// Upload image
const formData = new FormData();
formData.append('file', imageFile);
formData.append('description', 'Analysis target');

const uploadResponse = await fetch('/upload-image', {
    method: 'POST',
    body: formData
});
const {file_path} = await uploadResponse.json();

// Analyze with image
const taskResponse = await fetch('/run-task', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        task: "What mathematical concepts are shown in this image?",
        images: [file_path],
        max_steps: 8
    })
});

const result = await taskResponse.json();
console.log('Analysis:', result.result);
```

## 🎯 Practical Applications

### 📊 Chart and Graph Analysis
```json
{
    "task": "Analyze this graph and extract the data points. Create a CSV file with the values.",
    "images": ["chart.png"]
}
```

### 📝 Handwritten Text Analysis
```json
{
    "task": "Read the handwritten mathematical problem and solve it step by step.",
    "images": ["handwritten_math.jpg"]
}
```

### 🔬 Scientific Image Analysis
```json
{
    "task": "Identify the chemical structures in this diagram and explain their properties.",
    "images": ["chemistry_diagram.png"]
}
```

### 📐 Geometric Analysis
```json
{
    "task": "Measure the angles and calculate the area of shapes in this geometry problem.",
    "images": ["geometry_problem.jpg"]
}
```

## 📊 Response Structure

Updated API responses now include image information:

```json
{
    "success": true,
    "result": "Analysis of the image shows...",
    "task": "Analyze this mathematical diagram",
    "files": ["analysis_report.pdf", "extracted_data.csv"],
    "has_attachments": true,
    "file_count": 2,
    "input_images": ["uploads/diagram.png"],
    "image_count": 1,
    "has_images": true
}
```

## 🔍 Capability Check

Check vision support in your API:

```http
GET /health
```

Response:
```json
{
    "status": "healthy",
    "agent_type": "CodeAgent",
    "max_steps": 6,
    "vision_supported": true,
    "supported_image_formats": ["PNG", "JPEG", "JPG", "GIF", "BMP", "WEBP"],
    "upload_directory": "uploads",
    "api_version": "2.0.0"
}
```

## 🚀 Running Examples

```bash
# Install dependencies
pip install Pillow  # For creating test images

# Start API server
python api_server.py

# In another terminal - run examples
python example_api_usage.py
```

## ⚠️ Important Notes

1. **File Size**: Recommended not to upload images larger than 10MB
2. **Security**: API validates file types and validates images
3. **Performance**: VLM processing may take more time
4. **Storage**: Uploaded images are saved in `uploads/` folder

## 🔗 Useful Links

- [Smolagents with vision support](https://huggingface.co/blog/smolagents-can-see)
- [Vision Language Models 2025](https://huggingface.co/blog/vlms-2025)
- [API Documentation](http://localhost:8000/docs) (after starting server)

## 📈 What's Next?

Planned improvements:
- Video file support
- Batch processing of multiple images
- Result analysis caching
- Integration with external vision models 