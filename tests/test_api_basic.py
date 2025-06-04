#!/usr/bin/env python3
"""
Basic API tests for HWAgent Streaming API
"""

import pytest
import requests
import json
import time
import tempfile
import os
from pathlib import Path

API_BASE = "http://localhost:8000"
TEST_TIMEOUT = 30

class TestBasicAPI:
    """Test basic API functionality"""
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = requests.get(f"{API_BASE}/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "agent_type" in data
        assert "max_steps" in data
        assert "vision_supported" in data
        
    def test_root_endpoint(self):
        """Test root endpoint"""
        response = requests.get(f"{API_BASE}/")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        
    def test_files_list_endpoint(self):
        """Test files listing endpoint"""
        response = requests.get(f"{API_BASE}/files")
        assert response.status_code == 200
        
        data = response.json()
        assert "files" in data
        assert "count" in data
        assert isinstance(data["files"], list)

class TestTaskExecution:
    """Test task execution functionality"""
    
    def test_simple_sync_task(self):
        """Test simple synchronous task execution"""
        task_data = {
            "task": "Calculate 2 + 2 and return the result. No latex needed.",
            "max_steps": 3
        }
        
        response = requests.post(
            f"{API_BASE}/run-task",
            json=task_data,
            timeout=TEST_TIMEOUT
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "result" in data
        assert "task" in data
        assert data["task"] == task_data["task"]
        
    def test_file_creation_task(self):
        """Test task that creates files"""
        task_data = {
            "task": "Create a simple Python script named 'test_script.py' that prints 'Hello World'. No latex needed.",
            "max_steps": 5
        }
        
        response = requests.post(
            f"{API_BASE}/run-task",
            json=task_data,
            timeout=TEST_TIMEOUT
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        
        # Check if files were detected
        if data.get("has_attachments"):
            assert len(data["files"]) > 0
            
    def test_streaming_task(self):
        """Test streaming task execution"""
        task_data = {
            "task": "Print the numbers 1, 2, 3",
            "max_steps": 3
        }
        
        response = requests.post(
            f"{API_BASE}/stream-task",
            json=task_data,
            stream=True,
            timeout=TEST_TIMEOUT
        )
        
        assert response.status_code == 200
        
        # Check that we get streaming data
        step_count = 0
        final_received = False
        
        for line in response.iter_lines():
            if line and line.startswith(b'data: '):
                try:
                    data = json.loads(line[6:])
                    
                    if data.get("type") == "step" or data.get("step_type") == "action":
                        step_count += 1
                    elif data.get("type") == "final" or data.get("is_final"):
                        final_received = True
                        break
                        
                except json.JSONDecodeError:
                    continue
                    
        assert step_count > 0, "Should receive at least one step"
        assert final_received, "Should receive final result"

class TestFileOperations:
    """Test file upload and serving functionality"""
    
    def test_file_info_nonexistent(self):
        """Test file info for non-existent file"""
        response = requests.get(f"{API_BASE}/files/info/nonexistent.txt")
        assert response.status_code == 404
        
    def test_file_serving_nonexistent(self):
        """Test serving non-existent file"""
        response = requests.get(f"{API_BASE}/files/nonexistent.txt")
        assert response.status_code == 404
        
    def test_image_upload(self):
        """Test image upload functionality"""
        # Create a simple test image
        from PIL import Image
        import io
        
        # Create a simple 10x10 red image
        img = Image.new('RGB', (10, 10), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        files = {
            'file': ('test_image.png', img_bytes, 'image/png')
        }
        data = {
            'description': 'Test image upload'
        }
        
        response = requests.post(
            f"{API_BASE}/upload-image",
            files=files,
            data=data
        )
        
        assert response.status_code == 200
        result = response.json()
        
        assert result["success"] is True
        assert "file_path" in result
        assert "file_name" in result
        
        # Test that the uploaded file can be accessed
        file_path = result["file_path"]
        info_response = requests.get(f"{API_BASE}/files/info/{file_path}")
        assert info_response.status_code == 200

class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_invalid_task_request(self):
        """Test invalid task request"""
        # Empty task
        response = requests.post(f"{API_BASE}/run-task", json={})
        assert response.status_code in [400, 422]  # Validation error
        
        # Invalid max_steps
        response = requests.post(
            f"{API_BASE}/run-task",
            json={"task": "test", "max_steps": -1}
        )
        # Should either reject or handle gracefully
        
    def test_malformed_json(self):
        """Test malformed JSON request"""
        response = requests.post(
            f"{API_BASE}/run-task",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code in [400, 422]

# Utility functions for running tests
def check_api_available():
    """Check if API is available before running tests"""
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

if __name__ == "__main__":
    # Check if API is running
    if not check_api_available():
        print(f"❌ API not available at {API_BASE}")
        print("Please start the API server first: python api_server.py")
        exit(1)
    
    print(f"✅ API available at {API_BASE}")
    print("Running tests...")
    
    # Run tests using pytest
    import sys
    pytest.main([__file__] + sys.argv[1:]) 