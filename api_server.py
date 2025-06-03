from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, AsyncGenerator, List
import json
import asyncio
import uvicorn
import os
import shutil
import uuid
from pathlib import Path
from hwagent.agent import get_agent
from smolagents.memory import ActionStep
from smolagents.agent_types import AgentType
import base64
import io
from PIL import Image
from io import BytesIO

app = FastAPI(
    title="HWAgent Streaming API with Vision Support",
    description="Streaming API for Hardware Agent with real-time step-by-step execution and Vision Language Model support",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for frontend
frontend_dir = Path(__file__).parent / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

# Create uploads directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

class TaskRequest(BaseModel):
    task: str
    max_steps: Optional[int] = None
    additional_args: Optional[dict] = None
    images: Optional[List[str]] = None  # List of image file paths or base64 encoded images

class FileInfo(BaseModel):
    path: str
    name: str
    size: int
    size_human: str
    extension: str
    modified: float
    exists: bool

class StepResponse(BaseModel):
    step_number: int
    step_type: str  # "action", "final_result", "error", "unknown"
    observations: Optional[str] = None
    action_output: Optional[str] = None
    error: Optional[str] = None
    duration: Optional[float] = None
    is_final: bool = False
    files: List[str] = []  # List of file paths
    has_files: bool = False
    input_images: List[str] = []  # List of input image paths
    image_count: int = 0

class TaskResponse(BaseModel):
    success: bool
    result: str
    task: str
    files: List[str] = []
    has_attachments: bool = False
    file_count: int = 0
    input_images: List[str] = []
    image_count: int = 0
    has_images: bool = False

class ImageUploadResponse(BaseModel):
    success: bool
    file_path: str
    file_name: str
    message: str

def extract_files_from_content(content: str) -> list[str]:
    """Extract file paths from agent output"""
    if not content:
        return []
    
    import re
    
    # First, try to extract files from ATTACHED_FILES format (highest priority)
    attached_files_pattern = r'ATTACHED_FILES:\s*(.+?)(?:\n|$)'
    attached_match = re.search(attached_files_pattern, content, re.IGNORECASE)
    
    files = []
    if attached_match:
        # Parse the attached files list: `file1`, `file2`, `file3`
        attached_line = attached_match.group(1).strip()
        # Extract file paths between backticks
        file_matches = re.findall(r'`([^`]+)`', attached_line)
        files.extend(file_matches)
    
    # If no ATTACHED_FILES found, fall back to general file detection patterns
    if not files:
        file_patterns = [
            r'(?:created|saved|wrote|generated)\s+(?:file\s+)?[\'"`]?([^\'"`\s]+\.[a-zA-Z0-9]+)[\'"`]?',
            r'[\'"`]([^\'"`\s]*\.[a-zA-Z0-9]+)[\'"`]\s+(?:created|saved|wrote|generated)',
            r'(?:file|path):\s*[\'"`]?([^\'"`\s]+\.[a-zA-Z0-9]+)[\'"`]?',
            r'([a-zA-Z0-9_.-]+\.(?:pdf|tex|py|txt|png|jpg|jpeg|gif|svg|html|css|js|json|yaml|yml|md))\b',
        ]
        
        for pattern in file_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            files.extend(matches)
    
    # Filter out common false positives and ensure files exist
    valid_files = []
    for file_path in files:
        # Clean up the file path
        file_path = file_path.strip().strip('`"\'')
        
        if os.path.exists(file_path) and os.path.isfile(file_path):
            valid_files.append(file_path)
    
    return list(dict.fromkeys(valid_files))  # Remove duplicates while preserving order

def format_step_data(step) -> dict:
    """Format agent step data for API response"""
    if isinstance(step, ActionStep):
        # Extract files from observations and output
        files = []
        if step.observations:
            files.extend(extract_files_from_content(step.observations))
        if step.action_output:
            files.extend(extract_files_from_content(str(step.action_output)))
        
        return {
            "step_number": step.step_number,
            "step_type": "action",
            "observations": step.observations,
            "action_output": str(step.action_output) if step.action_output is not None else None,
            "error": str(step.error) if step.error else None,
            "duration": step.duration,
            "is_final": False,
            "files": files,
            "has_files": len(files) > 0
        }
    elif isinstance(step, AgentType) or isinstance(step, str):
        # Extract files from final result
        files = extract_files_from_content(str(step))
        
        # Log final result file extraction
        if files:
            print(f"📎 Final result contains {len(files)} attached files: {files}")
        
        return {
            "step_number": -1,
            "step_type": "final_result",
            "observations": None,
            "action_output": str(step),
            "error": None,
            "duration": None,
            "is_final": True,
            "files": files,
            "has_files": len(files) > 0
        }
    else:
        return {
            "step_number": -1,
            "step_type": "unknown",
            "observations": None,
            "action_output": str(step),
            "error": None,
            "duration": None,
            "is_final": True,
            "files": [],
            "has_files": False
        }

async def stream_agent_execution(
    task: str,
    max_steps: Optional[int] = None,
    additional_args: Optional[dict] = None,
    images: Optional[List[str]] = None
) -> AsyncGenerator[str, None]:
    """Stream agent execution steps as Server-Sent Events"""
    try:
        agent = get_agent()
        
        # Override max_steps if provided
        if max_steps:
            agent.max_steps = max_steps
        
        # Process and validate images
        processed_images = prepare_images_for_agent(images or [])
        
        if processed_images:
            print(f"🖼️ Processing {len(processed_images)} images: {processed_images}")
        
        # Prepare additional_args with image_paths
        agent_additional_args = additional_args.copy() if additional_args else {}
        if processed_images:
            agent_additional_args["image_paths"] = processed_images
            print(f"📤 Passing images to agent via additional_args['image_paths']")
        
        # Run agent in streaming mode
        for step in agent.run(
            task=task,
            stream=True,
            reset=True,
            additional_args=agent_additional_args  # Pass images via additional_args
        ):
            step_data = format_step_data(step)
            
            # Add image info to step data
            if processed_images:
                step_data["input_images"] = processed_images
                step_data["image_count"] = len(processed_images)
            
            # Format as Server-Sent Event
            yield f"data: {json.dumps(step_data)}\n\n"
            
            # Add small delay to prevent overwhelming the client
            await asyncio.sleep(0.1)
            
            # Break if this is the final step
            if step_data.get("is_final", False):
                break
                
    except Exception as e:
        error_data = {
            "step_number": -1,
            "step_type": "error",
            "observations": None,
            "action_output": None,
            "error": str(e),
            "duration": None,
            "is_final": True,
            "files": [],
            "input_images": processed_images if 'processed_images' in locals() else [],
            "image_count": len(processed_images) if 'processed_images' in locals() else 0
        }
        yield f"data: {json.dumps(error_data)}\n\n"

@app.post("/stream-task")
async def stream_task(request: TaskRequest):
    """
    Stream agent execution for a given task.
    Returns Server-Sent Events with step-by-step progress.
    """
    return StreamingResponse(
        stream_agent_execution(
            task=request.task,
            max_steps=request.max_steps,
            additional_args=request.additional_args,
            images=request.images
        ),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )

@app.post("/run-task")
async def run_task(request: TaskRequest):
    """
    Run agent task and return final result (non-streaming).
    Now supports Vision Language Models with image input.
    """
    try:
        agent = get_agent()
        
        # Override max_steps if provided
        if max_steps := request.max_steps:
            agent.max_steps = max_steps
        
        # Process and validate images
        processed_images = prepare_images_for_agent(request.images or [])
        
        if processed_images:
            print(f"🖼️ Processing {len(processed_images)} images for task: {processed_images}")
        
        # Prepare additional_args with image_paths
        agent_additional_args = request.additional_args.copy() if request.additional_args else {}
        if processed_images:
            agent_additional_args["image_paths"] = processed_images
            print(f"📤 Passing images to agent via additional_args['image_paths']")
        
        # Run agent without streaming
        result = agent.run(
            task=request.task,
            stream=False,
            reset=True,
            additional_args=agent_additional_args  # Pass images via additional_args
        )
        
        # Extract files from result
        files = extract_files_from_content(str(result))
        
        # Log file extraction for debugging
        if files:
            print(f"📎 Extracted {len(files)} attached files: {files}")
        
        response_data = {
            "success": True,
            "result": str(result),
            "task": request.task,
            "files": files,
            "has_attachments": len(files) > 0,
            "file_count": len(files),
            "input_images": processed_images,
            "image_count": len(processed_images),
            "has_images": len(processed_images) > 0
        }
        
        return response_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "HWAgent Streaming API is running"}

@app.get("/health")
async def health():
    """Health check with agent status and vision capabilities"""
    try:
        agent = get_agent()
        
        # Check if agent supports vision
        vision_supported = hasattr(agent, 'run') and True  # Modern smolagents support vision by default
        
        return {
            "status": "healthy",
            "agent_type": type(agent).__name__,
            "max_steps": agent.max_steps,
            "vision_supported": vision_supported,
            "supported_image_formats": ["PNG", "JPEG", "JPG", "GIF", "BMP", "WEBP"],
            "upload_directory": str(UPLOAD_DIR),
            "api_version": "2.0.0"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "vision_supported": False
        }

@app.get("/files/info/{file_path:path}")
async def get_file_info(file_path: str):
    """Get information about a file without downloading it"""
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    # Basic security check
    abs_file_path = os.path.abspath(file_path)
    current_dir = os.path.abspath(".")
    if not abs_file_path.startswith(current_dir):
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        stat = os.stat(file_path)
        file_size = stat.st_size
        modified_time = stat.st_mtime
        
        return {
            "path": file_path,
            "name": Path(file_path).name,
            "size": file_size,
            "size_human": format_file_size(file_size),
            "extension": Path(file_path).suffix.lower(),
            "modified": modified_time,
            "exists": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting file info: {str(e)}")

def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    if size_bytes == 0:
        return "0 B"
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

@app.get("/files/{file_path:path}")
async def get_file(file_path: str):
    """Serve files with proper content type"""
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    # Basic security check - don't serve files outside current directory
    abs_file_path = os.path.abspath(file_path)
    current_dir = os.path.abspath(".")
    if not abs_file_path.startswith(current_dir):
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        # Determine content type and read mode
        ext = Path(file_path).suffix.lower()
        content_type_map = {
            '.py': 'text/plain',
            '.js': 'application/javascript',
            '.html': 'text/html',
            '.css': 'text/css',
            '.json': 'application/json',
            '.txt': 'text/plain',
            '.md': 'text/markdown',
            '.yaml': 'text/yaml',
            '.yml': 'text/yaml',
            '.tex': 'text/x-tex',
            '.pdf': 'application/pdf',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.svg': 'image/svg+xml',
            '.bmp': 'image/bmp',
            '.webp': 'image/webp',
        }
        content_type = content_type_map.get(ext, 'application/octet-stream')
        
        # Binary files that should be read in binary mode
        binary_extensions = {'.pdf', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.bmp', '.webp', '.ico', '.zip', '.tar', '.gz', '.exe', '.bin'}
        is_binary = ext in binary_extensions
        
        if is_binary:
            # Read binary files in binary mode
            with open(file_path, 'rb') as f:
                content = f.read()
            
            return StreamingResponse(
                BytesIO(content),
                media_type=content_type,
                headers={"Content-Disposition": f"inline; filename={Path(file_path).name}"}
            )
        else:
            # Read text files in text mode with UTF-8 encoding
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return StreamingResponse(
                iter([content]),
                media_type=content_type,
                headers={"Content-Disposition": f"inline; filename={Path(file_path).name}"}
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")

@app.get("/files")
async def list_files():
    """List all files in the current working directory"""
    try:
        current_dir = Path(".")
        files = []
        
        for file_path in current_dir.rglob("*"):
            if file_path.is_file() and not file_path.name.startswith('.'):
                try:
                    stat = file_path.stat()
                    files.append({
                        "path": str(file_path),
                        "name": file_path.name,
                        "size": stat.st_size,
                        "size_human": format_file_size(stat.st_size),
                        "extension": file_path.suffix.lower(),
                        "modified": stat.st_mtime,
                        "relative_path": str(file_path.relative_to(current_dir))
                    })
                except:
                    continue
        
        # Sort by modification time (newest first)
        files.sort(key=lambda x: x["modified"], reverse=True)
        
        return {
            "files": files,
            "count": len(files),
            "working_directory": str(current_dir.absolute())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing files: {str(e)}")

def validate_image_file(file_path: str) -> bool:
    """Validate if the file is a valid image"""
    try:
        with Image.open(file_path) as img:
            img.verify()
        return True
    except Exception:
        return False

def process_base64_image(base64_data: str, file_name: str = None) -> str:
    """Process base64 encoded image and save to file"""
    try:
        # Remove data URL prefix if present
        if base64_data.startswith('data:'):
            base64_data = base64_data.split(',')[1]
        
        # Decode base64
        image_data = base64.b64decode(base64_data)
        
        # Generate file name if not provided
        if not file_name:
            file_name = f"{uuid.uuid4()}.png"
        
        file_path = UPLOAD_DIR / file_name
        
        # Save the image
        with open(file_path, 'wb') as f:
            f.write(image_data)
        
        # Validate the image
        if not validate_image_file(str(file_path)):
            os.remove(file_path)
            raise ValueError("Invalid image data")
        
        return str(file_path)
    except Exception as e:
        raise ValueError(f"Error processing base64 image: {str(e)}")

def prepare_images_for_agent(images: List[str]) -> List[str]:
    """Prepare and validate images for agent processing"""
    if not images:
        return []
    
    processed_images = []
    for image in images:
        if image.startswith('data:') or (len(image) > 100 and '/' not in image):
            # Looks like base64 data
            try:
                file_path = process_base64_image(image)
                processed_images.append(file_path)
            except ValueError as e:
                print(f"⚠️ Skipping invalid base64 image: {e}")
                continue
        else:
            # Assume it's a file path
            if os.path.exists(image) and validate_image_file(image):
                processed_images.append(image)
            else:
                print(f"⚠️ Skipping invalid image file: {image}")
                continue
    
    return processed_images

@app.post("/upload-images")
async def upload_multiple_images(files: List[UploadFile] = File(...)):
    """Upload multiple images and return their file paths"""
    try:
        uploaded_files = []
        
        for file in files:
            # Check if it's an image
            if not file.content_type or not file.content_type.startswith('image/'):
                continue
            
            # Read the uploaded file
            file_content = await file.read()
            
            # Generate a unique file name
            file_name = f"{uuid.uuid4()}_{file.filename}"
            file_path = UPLOAD_DIR / file_name
            
            # Save the file
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            # Validate the image
            if validate_image_file(str(file_path)):
                uploaded_files.append({
                    "file_path": str(file_path),
                    "file_name": file_name,
                    "original_name": file.filename
                })
            else:
                os.remove(file_path)
        
        return {
            "success": True,
            "uploaded_files": uploaded_files,
            "count": len(uploaded_files),
            "message": f"Successfully uploaded {len(uploaded_files)} images"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading images: {str(e)}")

@app.post("/upload-image")
async def upload_image(file: UploadFile = File(...), description: str = Form(...)):
    """Upload an image and return the file path"""
    try:
        # Read the uploaded file
        file_content = await file.read()
        
        # Generate a unique file name
        file_name = f"{uuid.uuid4()}_{file.filename}"
        file_path = UPLOAD_DIR / file_name
        
        # Save the file
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        return {
            "success": True,
            "file_path": str(file_path),
            "file_name": file_name,
            "message": f"Image uploaded successfully. File path: {file_path}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading image: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 