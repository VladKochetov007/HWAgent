#!/usr/bin/env python3
"""
Vision capability tests for HWAgent
"""

import pytest
import requests
import json
import os
from pathlib import Path
import subprocess
import sys

API_BASE = "http://localhost:8000"

class TestVisionCapabilities:
    """Test vision functionality with geometric shapes"""
    
    @classmethod
    def setup_class(cls):
        """Generate test images before running tests"""
        print("🎨 Generating test images...")
        test_images_script = Path(__file__).parent / "create_test_images.py"
        result = subprocess.run([sys.executable, str(test_images_script)], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error generating test images: {result.stderr}")
        else:
            print("✅ Test images generated successfully")
    
    def test_simple_shape_recognition(self):
        """Test recognition of simple geometric shapes"""
        test_images_dir = Path("tests/test_images")
        
        # Test with red circle
        red_circle_path = test_images_dir / "red_circle.png"
        assert red_circle_path.exists(), "Red circle test image not found"
        
        # Upload the image first
        with open(red_circle_path, 'rb') as img_file:
            files = {'file': ('red_circle.png', img_file, 'image/png')}
            data = {'description': 'Test red circle'}
            
            upload_response = requests.post(f"{API_BASE}/upload-image", files=files, data=data)
            assert upload_response.status_code == 200
            
            upload_result = upload_response.json()
            image_path = upload_result["file_path"]
        
        # Test vision recognition
        task_data = {
            "task": "Analyze this image and tell me what shape and color you see. Be specific about the shape (circle, triangle, rectangle, square) and the exact color.",
            "max_steps": 3,
            "images": [image_path]
        }
        
        response = requests.post(f"{API_BASE}/run-task", json=task_data, timeout=30)
        assert response.status_code == 200
        
        result = response.json()
        assert result["success"] is True
        
        # Check that the response mentions both the shape and color
        result_text = result["result"].lower()
        assert "circle" in result_text, f"Shape 'circle' not detected in: {result_text}"
        assert "red" in result_text, f"Color 'red' not detected in: {result_text}"
        
        print(f"✅ Shape recognition test passed: {result['result']}")
    
    def test_color_differentiation(self):
        """Test differentiation between different colors of the same shape"""
        test_images_dir = Path("tests/test_images")
        
        # Test multiple colored triangles
        colors_to_test = ["blue", "green", "yellow"]
        
        for color in colors_to_test:
            triangle_path = test_images_dir / f"{color}_triangle.png"
            assert triangle_path.exists(), f"{color} triangle test image not found"
            
            # Upload the image
            with open(triangle_path, 'rb') as img_file:
                files = {'file': (f'{color}_triangle.png', img_file, 'image/png')}
                data = {'description': f'Test {color} triangle'}
                
                upload_response = requests.post(f"{API_BASE}/upload-image", files=files, data=data)
                assert upload_response.status_code == 200
                
                upload_result = upload_response.json()
                image_path = upload_result["file_path"]
            
            # Test color recognition
            task_data = {
                "task": "What color is the triangle in this image? Answer with just the color name.",
                "max_steps": 2,
                "images": [image_path]
            }
            
            response = requests.post(f"{API_BASE}/run-task", json=task_data, timeout=30)
            assert response.status_code == 200
            
            result = response.json()
            assert result["success"] is True
            
            result_text = result["result"].lower()
            assert color in result_text, f"Color '{color}' not detected in: {result_text}"
            
            print(f"✅ Color recognition test passed for {color}: {result['result']}")
    
    def test_multiple_shapes_analysis(self):
        """Test analysis of image with multiple shapes"""
        test_images_dir = Path("tests/test_images")
        mixed_shapes_path = test_images_dir / "mixed_shapes.png"
        assert mixed_shapes_path.exists(), "Mixed shapes test image not found"
        
        # Upload the image
        with open(mixed_shapes_path, 'rb') as img_file:
            files = {'file': ('mixed_shapes.png', img_file, 'image/png')}
            data = {'description': 'Test mixed shapes'}
            
            upload_response = requests.post(f"{API_BASE}/upload-image", files=files, data=data)
            assert upload_response.status_code == 200
            
            upload_result = upload_response.json()
            image_path = upload_result["file_path"]
        
        # Test multiple shape recognition
        task_data = {
            "task": "Describe all the shapes and their colors in this image. List each shape separately.",
            "max_steps": 4,
            "images": [image_path]
        }
        
        response = requests.post(f"{API_BASE}/run-task", json=task_data, timeout=30)
        assert response.status_code == 200
        
        result = response.json()
        assert result["success"] is True
        
        result_text = result["result"].lower()
        
        # Check that all expected shapes and colors are mentioned
        expected_items = ["circle", "triangle", "square", "red", "blue", "green"]
        for item in expected_items:
            assert item in result_text, f"Expected item '{item}' not found in: {result_text}"
        
        print(f"✅ Multiple shapes analysis test passed: {result['result']}")
    
    def test_streaming_with_vision(self):
        """Test streaming functionality with vision input"""
        test_images_dir = Path("tests/test_images")
        pattern_path = test_images_dir / "checkerboard_pattern.png"
        assert pattern_path.exists(), "Checkerboard pattern test image not found"
        
        # Upload the image
        with open(pattern_path, 'rb') as img_file:
            files = {'file': ('checkerboard_pattern.png', img_file, 'image/png')}
            data = {'description': 'Test checkerboard pattern'}
            
            upload_response = requests.post(f"{API_BASE}/upload-image", files=files, data=data)
            assert upload_response.status_code == 200
            
            upload_result = upload_response.json()
            image_path = upload_result["file_path"]
        
        # Test streaming with vision
        task_data = {
            "task": "Describe the pattern in this image. What type of pattern is it?",
            "max_steps": 3,
            "images": [image_path]
        }
        
        response = requests.post(f"{API_BASE}/stream-task", json=task_data, stream=True, timeout=30)
        assert response.status_code == 200
        
        events = []
        final_result = None
        
        for line in response.iter_lines(decode_unicode=True):
            if line and line.startswith('data: '):
                try:
                    data = json.loads(line[6:])
                    events.append(data)
                    
                    if data.get('is_final') or data.get('type') == 'final':
                        final_result = data.get('result') or data.get('action_output', '')
                        break
                        
                except json.JSONDecodeError:
                    continue
        
        assert len(events) > 0, "Should receive streaming events"
        assert final_result is not None, "Should receive final result"
        
        result_text = final_result.lower()
        # Check for pattern-related terms
        pattern_terms = ["pattern", "checkerboard", "square", "black", "white"]
        found_terms = [term for term in pattern_terms if term in result_text]
        assert len(found_terms) >= 2, f"Should detect pattern elements, found: {found_terms} in: {result_text}"
        
        print(f"✅ Streaming vision test passed: {final_result}")
    
    def test_shape_comparison(self):
        """Test comparison between different shapes"""
        test_images_dir = Path("tests/test_images")
        
        # Upload two different shapes
        square_path = test_images_dir / "purple_square.png"
        circle_path = test_images_dir / "orange_circle.png"
        
        assert square_path.exists() and circle_path.exists(), "Test shapes not found"
        
        uploaded_images = []
        for shape_path, name in [(square_path, "purple_square"), (circle_path, "orange_circle")]:
            with open(shape_path, 'rb') as img_file:
                files = {'file': (f'{name}.png', img_file, 'image/png')}
                data = {'description': f'Test {name}'}
                
                upload_response = requests.post(f"{API_BASE}/upload-image", files=files, data=data)
                assert upload_response.status_code == 200
                
                upload_result = upload_response.json()
                uploaded_images.append(upload_result["file_path"])
        
        # Test comparison
        task_data = {
            "task": "Compare these two images. What shapes do you see and what are their colors? How are they different?",
            "max_steps": 4,
            "images": uploaded_images
        }
        
        response = requests.post(f"{API_BASE}/run-task", json=task_data, timeout=30)
        assert response.status_code == 200
        
        result = response.json()
        assert result["success"] is True
        
        result_text = result["result"].lower()
        
        # Check that both shapes and colors are mentioned
        expected_items = ["square", "circle", "purple", "orange"]
        for item in expected_items:
            assert item in result_text, f"Expected item '{item}' not found in: {result_text}"
        
        print(f"✅ Shape comparison test passed: {result['result']}")


class TestVisionErrorHandling:
    """Test error handling in vision scenarios"""
    
    def test_vision_with_no_images(self):
        """Test vision-related task without providing images"""
        task_data = {
            "task": "Describe the shapes and colors in the image",
            "max_steps": 2,
            "images": []  # No images provided
        }
        
        response = requests.post(f"{API_BASE}/run-task", json=task_data, timeout=20)
        assert response.status_code == 200
        
        result = response.json()
        # Should handle gracefully - agent should explain no image was provided
        assert result["success"] is True
        
        result_text = result["result"].lower()
        # Should mention something about no image or unable to see
        vision_related_terms = ["image", "see", "visual", "picture", "provided"]
        found = any(term in result_text for term in vision_related_terms)
        assert found, f"Should mention vision limitation, got: {result_text}"
        
        print(f"✅ No images test passed: {result['result']}")
    
    def test_vision_with_invalid_image_path(self):
        """Test with invalid image path"""
        task_data = {
            "task": "Describe this image",
            "max_steps": 2,
            "images": ["nonexistent_image.png"]
        }
        
        response = requests.post(f"{API_BASE}/run-task", json=task_data, timeout=20)
        # Should either succeed with explanation or return error
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            result = response.json()
            # If it succeeds, should handle gracefully
            print(f"✅ Invalid image path handled gracefully: {result['result']}")
        else:
            print("✅ Invalid image path returned expected error")


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
    print("Running vision tests...")
    
    # Run tests using pytest
    pytest.main([__file__] + sys.argv[1:]) 