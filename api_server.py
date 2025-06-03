from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, AsyncGenerator
import json
import asyncio
import uvicorn
import os
from pathlib import Path
from hwagent.agent import get_agent
from smolagents.memory import ActionStep
from smolagents.agent_types import AgentType

app = FastAPI(
    title="HWAgent Streaming API",
    description="Streaming API for Hardware Agent with real-time step-by-step execution",
    version="1.0.0"
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

class TaskRequest(BaseModel):
    task: str
    max_steps: Optional[int] = None
    additional_args: Optional[dict] = None
    images: Optional[list[str]] = None

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
    files: list[str] = []  # List of file paths
    has_files: bool = False

class TaskResponse(BaseModel):
    success: bool
    result: str
    task: str
    files: list[str] = []
    has_attachments: bool = False
    file_count: int = 0

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
    images: Optional[list[str]] = None
) -> AsyncGenerator[str, None]:
    """Stream agent execution steps as Server-Sent Events"""
    try:
        agent = get_agent()
        
        # Override max_steps if provided
        if max_steps:
            agent.max_steps = max_steps
        
        # Run agent in streaming mode
        for step in agent.run(
            task=task,
            stream=True,
            reset=True,
            additional_args=additional_args,
            images=images
        ):
            step_data = format_step_data(step)
            
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
            "files": []
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
    """
    try:
        agent = get_agent()
        
        # Override max_steps if provided
        if max_steps := request.max_steps:
            agent.max_steps = max_steps
        
        # Run agent without streaming
        result = agent.run(
            task=request.task,
            stream=False,
            reset=True,
            additional_args=request.additional_args,
            images=request.images
        )
        
        # Extract files from result
        files = extract_files_from_content(str(result))
        
        # Log file extraction for debugging
        if files:
            print(f"📎 Extracted {len(files)} attached files: {files}")
        
        return {
            "success": True,
            "result": str(result),
            "task": request.task,
            "files": files,
            "has_attachments": len(files) > 0,
            "file_count": len(files)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "HWAgent Streaming API is running"}

@app.get("/health")
async def health():
    """Health check with agent status"""
    try:
        agent = get_agent()
        return {
            "status": "healthy",
            "agent_type": type(agent).__name__,
            "max_steps": agent.max_steps
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
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
    """Serve generated files"""
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    # Basic security check - don't serve files outside current directory
    abs_file_path = os.path.abspath(file_path)
    current_dir = os.path.abspath(".")
    if not abs_file_path.startswith(current_dir):
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Determine content type
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
        }
        content_type = content_type_map.get(ext, 'text/plain')
        
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

if __name__ == "__main__":
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 