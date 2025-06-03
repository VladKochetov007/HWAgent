#!/usr/bin/env python3
"""
Example usage of HWAgent API with Vision Language Model support
"""

import requests
import json
from pathlib import Path

API_BASE = "http://localhost:8000"

def create_sample_image():
    """Create a simple sample image for testing"""
    try:
        from PIL import Image, ImageDraw
        import io
        
        # Create a simple image with text
        img = Image.new('RGB', (400, 200), color='white')
        draw = ImageDraw.Draw(img)
        
        # Draw some geometric shapes and text
        draw.rectangle([50, 50, 150, 100], fill='blue', outline='black')
        draw.circle([300, 100], 50, fill='red', outline='black')
        draw.text((50, 120), "Sample Image for VLM", fill='black')
        draw.text((50, 140), "Blue rectangle and red circle", fill='gray')
        
        # Save to bytes
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        # Save to file for uploading
        sample_path = Path("sample_image.png")
        with open(sample_path, 'wb') as f:
            f.write(img_bytes.getvalue())
        
        return str(sample_path)
    except ImportError:
        print("⚠️ PIL not available, skipping image creation")
        return None

def upload_image_example():
    """Example of uploading an image"""
    print("📤 Image Upload Example")
    print("="*30)
    
    # Create a sample image
    sample_image = create_sample_image()
    if not sample_image:
        print("❌ Could not create sample image")
        return None
    
    try:
        # Upload the image
        with open(sample_image, 'rb') as f:
            files = {'file': f}
            data = {'description': 'Sample geometric shapes image'}
            response = requests.post(f"{API_BASE}/upload-image", files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Image uploaded successfully!")
            print(f"   File path: {result['file_path']}")
            print(f"   File name: {result['file_name']}")
            return result['file_path']
        else:
            print(f"❌ Upload failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return None
    finally:
        # Clean up sample file
        if Path(sample_image).exists():
            Path(sample_image).unlink()

def vision_task_example():
    """Example of running a vision task with image analysis"""
    
    # Upload an image first
    image_path = upload_image_example()
    if not image_path:
        print("❌ Cannot proceed without uploaded image")
        return
    
    print("\n🖼️ Vision Task Example")
    print("="*30)
    
    # Example task that analyzes the uploaded image
    task = """
    Analyze the uploaded image in detail. Please:
    1. Describe what you see in the image
    2. Identify any geometric shapes, colors, and text
    3. Count the number of objects
    4. Create a detailed report in markdown format
    5. If possible, create a Python script that could generate similar shapes
    
    Be very specific about positions, colors, and dimensions.
    """
    
    print("🚀 Sending vision task to agent...")
    print(f"Task: {task}")
    print(f"Image: {image_path}\n")
    
    # Send task with image to API
    response = requests.post(
        f"{API_BASE}/run-task",
        json={
            "task": task,
            "max_steps": 8,
            "images": [image_path]  # Include the uploaded image
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        
        print("✅ Vision task completed successfully!")
        print(f"📝 Result: {result['result'][:500]}...")  # Show first 500 chars
        
        if result.get('has_images', False):
            print(f"\n🖼️ Input images ({result['image_count']}):")
            for img in result['input_images']:
                print(f"   📷 {img}")
        
        if result.get('has_attachments', False):
            print(f"\n📎 Generated files ({result['file_count']}):")
            for i, file_path in enumerate(result['files'], 1):
                print(f"   {i}. {file_path}")
        
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)

def stream_vision_task_example():
    """Example of streaming a vision task"""
    
    # For this example, we'll use base64 encoded simple image
    # In real usage, you'd upload actual images
    print("\n🎬 Streaming Vision Example")
    print("="*40)
    
    # Simple task asking about image content
    task = """
    Look at this image and tell me what mathematical concepts could be taught using it.
    Create a lesson plan and some practice problems.
    """
    
    # Create a simple image and encode it
    sample_image = create_sample_image()
    if not sample_image:
        print("❌ Cannot create sample image for streaming example")
        return
    
    try:
        print(f"Task: {task}")
        print(f"Using image: {sample_image}\n")
        
        # Stream task execution with image
        response = requests.post(
            f"{API_BASE}/stream-task",
            json={
                "task": task, 
                "max_steps": 6,
                "images": [sample_image]
            },
            stream=True
        )
        
        if response.status_code == 200:
            print("📡 Streaming vision task execution...\n")
            
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        try:
                            step_data = json.loads(line_str[6:])  # Remove 'data: ' prefix
                            
                            if step_data['step_type'] == 'action':
                                print(f"🔄 Step {step_data['step_number']}:")
                                if step_data.get('observations'):
                                    print(f"   📊 Observations: {step_data['observations'][:100]}...")
                                if step_data.get('has_files'):
                                    print(f"   📎 Files created: {step_data['files']}")
                            
                            elif step_data['step_type'] == 'final_result':
                                print(f"\n✅ Final Result:")
                                print(f"   📝 {step_data['action_output'][:300]}...")
                                if step_data.get('has_files'):
                                    print(f"   📎 Final files: {step_data['files']}")
                                if step_data.get('image_count', 0) > 0:
                                    print(f"   🖼️ Processed {step_data['image_count']} images")
                            
                            elif step_data['step_type'] == 'error':
                                print(f"❌ Error: {step_data['error']}")
                                
                        except json.JSONDecodeError:
                            continue
        else:
            print(f"❌ Streaming error: {response.status_code}")
    
    finally:
        # Clean up
        if Path(sample_image).exists():
            Path(sample_image).unlink()

def run_task_example():
    """Example of running a task with file attachments (no vision)"""
    
    # Example task that should generate files
    task = """
    Create a simple mathematical report about quadratic equations.
    Include:
    1. A LaTeX document with mathematical formulas
    2. A Python script to solve quadratic equations
    3. Compile the LaTeX to PDF
    
    Show examples and explanations.
    """
    
    print("🚀 Sending task to agent...")
    print(f"Task: {task}\n")
    
    # Send task to API
    response = requests.post(
        f"{API_BASE}/run-task",
        json={
            "task": task,
            "max_steps": 10
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        
        print("✅ Task completed successfully!")
        print(f"📝 Result: {result['result'][:200]}...\n")
        
        if result.get('has_attachments', False):
            print(f"📎 Found {result['file_count']} attached files:")
            for i, file_path in enumerate(result['files'], 1):
                print(f"   {i}. {file_path}")
                
                # Get file info
                info_response = requests.get(f"{API_BASE}/files/info/{file_path}")
                if info_response.status_code == 200:
                    info = info_response.json()
                    print(f"      - Size: {info['size_human']}")
                    print(f"      - Type: {info['extension']}")
                else:
                    print(f"      - Could not get file info")
            
            print(f"\n📂 Files are available at:")
            for file_path in result['files']:
                print(f"   {API_BASE}/files/{file_path}")
        else:
            print("📎 No files were attached to the result")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)

def list_all_files():
    """List all files in working directory"""
    print("\n" + "="*50)
    print("📂 All files in working directory")
    print("="*50)
    
    response = requests.get(f"{API_BASE}/files")
    if response.status_code == 200:
        data = response.json()
        print(f"Working directory: {data['working_directory']}")
        print(f"Total files: {data['count']}\n")
        
        for file_info in data['files'][:10]:  # Show first 10 files
            print(f"📄 {file_info['name']}")
            print(f"   Path: {file_info['relative_path']}")
            print(f"   Size: {file_info['size_human']}")
            print(f"   Type: {file_info['extension']}")
            print()
    else:
        print(f"❌ Error listing files: {response.status_code}")

if __name__ == "__main__":
    print("🧪 HWAgent API with Vision Support - Usage Examples")
    print("="*60)
    
    # Check if API is running
    try:
        health_response = requests.get(f"{API_BASE}/health")
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"✅ API is running - Status: {health_data['status']}")
            print(f"   Agent type: {health_data.get('agent_type', 'Unknown')}")
            print(f"   Max steps: {health_data.get('max_steps', 'Unknown')}")
            print(f"   Vision support: {health_data.get('vision_supported', False)}")
            print(f"   Supported formats: {', '.join(health_data.get('supported_image_formats', []))}")
            print(f"   API version: {health_data.get('api_version', '1.0.0')}\n")
        else:
            print("❌ API health check failed")
            exit(1)
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API. Make sure the server is running:")
        print("   python api_server.py")
        exit(1)
    
    # Run examples
    print("Running examples...")
    vision_task_example()
    stream_vision_task_example()
    run_task_example()
    list_all_files()
    
    print("\n✨ All examples completed!")
