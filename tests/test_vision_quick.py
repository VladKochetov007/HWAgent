#!/usr/bin/env python3
"""
Quick test for Vision functionality
"""

import requests
import json
import subprocess
import sys
from pathlib import Path

API_BASE = "http://localhost:8000"

def check_api():
    """Check if API is running"""
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def generate_test_images():
    """Generate test images"""
    print("🎨 Generating test images...")
    script_path = Path("tests/create_test_images.py")
    result = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ Test images generated")
        return True
    else:
        print(f"❌ Error generating images: {result.stderr}")
        return False

def test_simple_vision():
    """Test basic vision functionality"""
    print("\n🖼️ Testing vision capabilities...")
    
    # Generate test images
    if not generate_test_images():
        return False
    
    # Test with red circle
    test_image_path = Path("tests/test_images/red_circle.png")
    if not test_image_path.exists():
        print("❌ Test image not found")
        return False
    
    # Upload image
    print("📤 Uploading test image...")
    with open(test_image_path, 'rb') as img_file:
        files = {'file': ('red_circle.png', img_file, 'image/png')}
        data = {'description': 'Test red circle'}
        
        upload_response = requests.post(f"{API_BASE}/upload-image", files=files, data=data)
        if upload_response.status_code != 200:
            print(f"❌ Upload failed: {upload_response.status_code}")
            return False
        
        upload_result = upload_response.json()
        image_path = upload_result["file_path"]
        print(f"✅ Image uploaded: {image_path}")
    
    # Test vision analysis
    print("🔍 Testing vision analysis...")
    task_data = {
        "task": "What do you see in this image? Describe the shape and color.",
        "max_steps": 3,
        "images": [image_path]
    }
    
    response = requests.post(f"{API_BASE}/run-task", json=task_data, timeout=30)
    if response.status_code != 200:
        print(f"❌ Vision test failed: {response.status_code}")
        return False
    
    result = response.json()
    if not result["success"]:
        print(f"❌ Task failed: {result}")
        return False
    
    print(f"🎯 Vision result: {result['result']}")
    
    # Check if result contains expected elements
    result_text = result['result'].lower()
    if "red" in result_text:
        print("✅ Color detected correctly")
    else:
        print("⚠️ Color not clearly detected")
    
    if "circle" in result_text:
        print("✅ Shape detected correctly")
    else:
        print("⚠️ Shape not clearly detected")
    
    return True

def test_streaming_vision():
    """Test streaming with vision"""
    print("\n🌊 Testing streaming vision...")
    
    # Use mixed shapes image
    test_image_path = Path("tests/test_images/mixed_shapes.png")
    if not test_image_path.exists():
        print("❌ Mixed shapes image not found")
        return False
    
    # Upload image
    with open(test_image_path, 'rb') as img_file:
        files = {'file': ('mixed_shapes.png', img_file, 'image/png')}
        data = {'description': 'Test mixed shapes'}
        
        upload_response = requests.post(f"{API_BASE}/upload-image", files=files, data=data)
        if upload_response.status_code != 200:
            print(f"❌ Upload failed: {upload_response.status_code}")
            return False
        
        upload_result = upload_response.json()
        image_path = upload_result["file_path"]
    
    # Test streaming
    task_data = {
        "task": "Analyze this image and describe all shapes and their colors.",
        "max_steps": 4,
        "images": [image_path]
    }
    
    print("🔄 Starting streaming analysis...")
    response = requests.post(f"{API_BASE}/stream-task", json=task_data, stream=True, timeout=30)
    
    if response.status_code != 200:
        print(f"❌ Streaming failed: {response.status_code}")
        return False
    
    events = []
    final_result = None
    
    for line in response.iter_lines(decode_unicode=True):
        if line and line.startswith('data: '):
            try:
                data = json.loads(line[6:])
                events.append(data)
                
                step_info = f"Step {data.get('step_number', '?')}: {data.get('step_type', 'unknown')}"
                print(f"📦 {step_info}")
                
                if data.get('is_final') or data.get('type') == 'final':
                    final_result = data.get('result') or data.get('action_output', '')
                    break
                    
            except json.JSONDecodeError:
                continue
    
    print(f"🎯 Final streaming result: {final_result}")
    print(f"✅ Received {len(events)} streaming events")
    
    return True

def main():
    """Main test function"""
    print("🚀 HWAgent Vision Test")
    print("=" * 50)
    
    if not check_api():
        print("❌ API not available. Please start: python api_server.py")
        return False
    
    print("✅ API is running")
    
    # Test basic vision
    if not test_simple_vision():
        print("❌ Basic vision test failed")
        return False
    
    # Test streaming vision
    if not test_streaming_vision():
        print("❌ Streaming vision test failed")
        return False
    
    print("\n🎉 All vision tests passed!")
    print("\n💡 Next steps:")
    print("  - Try uploading your own images via the web interface")
    print("  - Test with different shapes and colors")
    print("  - Try complex scenes with multiple objects")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 