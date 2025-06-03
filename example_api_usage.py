#!/usr/bin/env python3
"""
Example usage of HWAgent API with attached files parsing
"""

import requests
import json
import time
from typing import Generator

API_BASE = "http://localhost:8000"

def run_task_example():
    """Example of running a task with file attachments"""
    
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
        print(f"📝 Result: {result['result']}\n")
        
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

def stream_task_example():
    """Example of streaming task execution"""
    
    task = "Calculate the area under the curve y = x^2 from 0 to 2 using integration. Create a plot and save as PNG."
    
    print("\n" + "="*50)
    print("🎬 Streaming example")
    print("="*50)
    print(f"Task: {task}\n")
    
    # Stream task execution
    response = requests.post(
        f"{API_BASE}/stream-task",
        json={"task": task, "max_steps": 8},
        stream=True
    )
    
    if response.status_code == 200:
        print("📡 Streaming agent execution...\n")
        
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
                            print(f"   📝 {step_data['action_output'][:200]}...")
                            if step_data.get('has_files'):
                                print(f"   📎 Final files: {step_data['files']}")
                        
                        elif step_data['step_type'] == 'error':
                            print(f"❌ Error: {step_data['error']}")
                            
                    except json.JSONDecodeError:
                        continue
    else:
        print(f"❌ Streaming error: {response.status_code}")

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
    print("🧪 HWAgent API Usage Examples")
    print("="*50)
    
    # Check if API is running
    try:
        health_response = requests.get(f"{API_BASE}/health")
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"✅ API is running - Status: {health_data['status']}")
            print(f"   Agent type: {health_data.get('agent_type', 'Unknown')}")
            print(f"   Max steps: {health_data.get('max_steps', 'Unknown')}\n")
        else:
            print("❌ API health check failed")
            exit(1)
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API. Make sure the server is running:")
        print("   python api_server.py")
        exit(1)
    
    # Run examples
    run_task_example()
    stream_task_example()
    list_all_files()
    
    print("\n✨ Examples completed!") 