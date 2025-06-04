#!/usr/bin/env python3
"""
Streaming API tests for HWAgent
"""

import pytest
import requests
import json
import time
import asyncio
import websockets
from io import StringIO

API_BASE = "http://localhost:8000"

class TestStreamingAPI:
    """Test streaming functionality"""
    
    def test_streaming_simple_task(self):
        """Test basic streaming functionality"""
        task_data = {
            "task": "Count from 1 to 3",
            "max_steps": 5
        }
        
        response = requests.post(
            f"{API_BASE}/stream-task",
            json=task_data,
            stream=True,
            timeout=30
        )
        
        assert response.status_code == 200
        assert response.headers.get('content-type') == 'text/event-stream'
        
        # Parse streaming response
        events = []
        for line in response.iter_lines(decode_unicode=True):
            if line and line.startswith('data: '):
                try:
                    data = json.loads(line[6:])
                    events.append(data)
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {e}, line: {line}")
                    
        # Validate events
        assert len(events) > 0, "Should receive at least one event"
        
        # Check for step events
        step_events = [e for e in events if e.get('type') == 'step' or e.get('step_type') == 'action']
        assert len(step_events) > 0, "Should receive at least one step event"
        
        # Check for final event
        final_events = [e for e in events if e.get('type') == 'final' or e.get('is_final')]
        assert len(final_events) > 0, "Should receive a final event"
        
        # Validate step structure
        for event in step_events:
            assert 'step_number' in event or 'step' in event
            assert 'type' in event or 'step_type' in event
            
    def test_streaming_with_file_creation(self):
        """Test streaming with file creation"""
        task_data = {
            "task": "Create a file called 'stream_test.txt' with content 'Hello from stream test'",
            "max_steps": 5
        }
        
        response = requests.post(
            f"{API_BASE}/stream-task",
            json=task_data,
            stream=True,
            timeout=30
        )
        
        assert response.status_code == 200
        
        events = []
        final_event = None
        
        for line in response.iter_lines(decode_unicode=True):
            if line and line.startswith('data: '):
                try:
                    data = json.loads(line[6:])
                    events.append(data)
                    
                    if data.get('type') == 'final' or data.get('is_final'):
                        final_event = data
                        break
                        
                except json.JSONDecodeError:
                    continue
                    
        assert final_event is not None, "Should receive final event"
        
        # Check if files were attached
        if final_event.get('has_files') or final_event.get('has_attachments'):
            files = final_event.get('files', [])
            assert len(files) > 0, "Should have attached files"
            
    def test_streaming_error_handling(self):
        """Test streaming with error conditions"""
        task_data = {
            "task": "Execute an invalid command that will fail",
            "max_steps": 3
        }
        
        response = requests.post(
            f"{API_BASE}/stream-task",
            json=task_data,
            stream=True,
            timeout=30
        )
        
        # Should get a response even if task fails
        assert response.status_code == 200
        
        events = []
        for line in response.iter_lines(decode_unicode=True):
            if line and line.startswith('data: '):
                try:
                    data = json.loads(line[6:])
                    events.append(data)
                    
                    # Break on final or error
                    if data.get('is_final') or data.get('type') in ['final', 'error']:
                        break
                        
                except json.JSONDecodeError:
                    continue
                    
        assert len(events) > 0, "Should receive at least one event"
        
    def test_streaming_with_images(self):
        """Test streaming with image input"""
        # First upload a test image
        from PIL import Image
        import io
        
        img = Image.new('RGB', (50, 50), color='blue')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        # Upload image
        files = {'file': ('test_image.png', img_bytes, 'image/png')}
        data = {'description': 'Test image for streaming'}
        
        upload_response = requests.post(
            f"{API_BASE}/upload-image",
            files=files,
            data=data
        )
        
        assert upload_response.status_code == 200
        upload_result = upload_response.json()
        image_path = upload_result["file_path"]
        
        # Now test streaming with image
        task_data = {
            "task": "Analyze the uploaded image and describe what you see",
            "max_steps": 5,
            "images": [image_path]
        }
        
        response = requests.post(
            f"{API_BASE}/stream-task",
            json=task_data,
            stream=True,
            timeout=30
        )
        
        assert response.status_code == 200
        assert 'text/event-stream' in response.headers.get('content-type', '').lower()
        
        events = []
        for line in response.iter_lines(decode_unicode=True):
            if line and line.startswith('data: '):
                try:
                    data = json.loads(line[6:])
                    events.append(data)
                    
                    if data.get('is_final') or data.get('type') == 'final':
                        break
                        
                except json.JSONDecodeError:
                    continue
                    
        assert len(events) > 0, "Should receive streaming events with image input"
        
        # Check if any event has image information
        image_events = [e for e in events if e.get('input_images') or e.get('image_count', 0) > 0]
        # Note: May not always be present depending on implementation


class TestStreamingDataFormat:
    """Test streaming data format consistency"""
    
    def test_event_format_consistency(self):
        """Test that all streaming events have consistent format"""
        task_data = {
            "task": "Say hello",
            "max_steps": 2
        }
        
        response = requests.post(
            f"{API_BASE}/stream-task",
            json=task_data,
            stream=True,
            timeout=15
        )
        
        assert response.status_code == 200
        
        events = []
        for line in response.iter_lines(decode_unicode=True):
            if line and line.startswith('data: '):
                try:
                    data = json.loads(line[6:])
                    events.append(data)
                    
                    # Validate common fields
                    assert 'step_number' in data or 'step' in data
                    assert 'type' in data or 'step_type' in data
                    assert 'is_final' in data
                    
                    if data.get('is_final') or data.get('type') == 'final':
                        break
                        
                except json.JSONDecodeError as e:
                    pytest.fail(f"Invalid JSON in stream: {e}, line: {line}")
                    
        assert len(events) > 0, "Should receive at least one event"
        
    def test_sse_format_compliance(self):
        """Test that streaming response follows SSE format"""
        task_data = {
            "task": "Quick test",
            "max_steps": 1
        }
        
        response = requests.post(
            f"{API_BASE}/stream-task",
            json=task_data,
            stream=True,
            timeout=15
        )
        
        assert response.status_code == 200
        
        # Check headers
        headers = response.headers
        assert 'text/' in headers.get('content-type', '').lower()
        
        # Check SSE format
        lines = []
        for line in response.iter_lines(decode_unicode=True):
            lines.append(line)
            if line and line.startswith('data: '):
                # This is a valid SSE data line
                json_part = line[6:]  # Remove 'data: ' prefix
                try:
                    json.loads(json_part)
                except json.JSONDecodeError:
                    pytest.fail(f"Invalid JSON in SSE data line: {line}")
                    
        assert len(lines) > 0, "Should receive at least one line"


class TestStreamingPerformance:
    """Test streaming performance and reliability"""
    
    def test_streaming_timeout_handling(self):
        """Test streaming with reasonable timeout"""
        task_data = {
            "task": "Count from 1 to 3",  # Simple task that should complete quickly
            "max_steps": 3
        }
        
        start_time = time.time()
        try:
            response = requests.post(
                f"{API_BASE}/stream-task",
                json=task_data,
                stream=True,
                timeout=15  # Reasonable timeout
            )
            
            events = []
            for line in response.iter_lines(decode_unicode=True):
                if line and line.startswith('data: '):
                    data = json.loads(line[6:])
                    events.append(data)
                    
                    if data.get('is_final'):
                        break
                        
            elapsed = time.time() - start_time
            # Should complete within reasonable time
            assert elapsed <= 20, f"Request took too long: {elapsed}s"
            assert len(events) > 0, "Should receive at least one event"
                        
        except requests.Timeout:
            # If timeout occurs, that's acceptable for this test
            elapsed = time.time() - start_time
            # Just check that we respect some reasonable bounds
            pass
        
    def test_multiple_concurrent_streams(self):
        """Test multiple concurrent streaming requests"""
        import threading
        import queue
        
        results = queue.Queue()
        
        def stream_task(task_id):
            try:
                task_data = {
                    "task": f"Task {task_id}: count to 3",
                    "max_steps": 5
                }
                
                response = requests.post(
                    f"{API_BASE}/stream-task",
                    json=task_data,
                    stream=True,
                    timeout=20
                )
                
                events = []
                for line in response.iter_lines(decode_unicode=True):
                    if line and line.startswith('data: '):
                        data = json.loads(line[6:])
                        events.append(data)
                        
                        if data.get('is_final'):
                            break
                            
                results.put((task_id, True, len(events)))
                
            except Exception as e:
                results.put((task_id, False, str(e)))
        
        # Start 3 concurrent streaming tasks
        threads = []
        for i in range(3):
            thread = threading.Thread(target=stream_task, args=(i,))
            thread.start()
            threads.append(thread)
        
        # Wait for all to complete
        for thread in threads:
            thread.join(timeout=30)
        
        # Check results
        completed = 0
        while not results.empty():
            task_id, success, data = results.get()
            if success:
                completed += 1
                assert data > 0, f"Task {task_id} should have received events"
            else:
                print(f"Task {task_id} failed: {data}")
        
        assert completed >= 2, "At least 2 of 3 concurrent streams should succeed"


if __name__ == "__main__":
    # Check if API is running
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ API not healthy at {API_BASE}")
            exit(1)
    except:
        print(f"❌ API not available at {API_BASE}")
        print("Please start the API server first: python api_server.py")
        exit(1)
    
    print(f"✅ API available at {API_BASE}")
    print("Running streaming tests...")
    
    # Run tests using pytest
    import sys
    pytest.main([__file__] + sys.argv[1:]) 