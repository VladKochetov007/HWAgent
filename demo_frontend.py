#!/usr/bin/env python3
"""
Demo script to test frontend streaming functionality
"""

import webbrowser
import time
import subprocess
import sys
import requests
from pathlib import Path

def check_api_running():
    """Check if API is running"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def check_frontend_running():
    """Check if frontend is running"""
    try:
        response = requests.get("http://localhost:3000", timeout=5)
        return response.status_code == 200
    except:
        return False

def main():
    print("🚀 HWAgent Frontend Demo")
    print("=" * 50)
    
    # Check if API is running
    if not check_api_running():
        print("❌ API server not running on port 8000")
        print("Please start it with: python api_server.py")
        return
    
    print("✅ API server is running on port 8000")
    
    # Check if frontend is running
    if not check_frontend_running():
        print("❌ Frontend server not running on port 3000")
        print("Please start it with: python -m http.server 3000 --directory frontend")
        return
    
    print("✅ Frontend server is running on port 3000")
    
    # Test streaming API
    print("\n🧪 Testing streaming API...")
    try:
        response = requests.post(
            "http://localhost:8000/stream-task",
            json={"task": "Say hello and count to 3", "max_steps": 3},
            stream=True,
            timeout=30
        )
        
        if response.status_code == 200:
            print("✅ Streaming API is working correctly")
        else:
            print(f"❌ Streaming API returned status {response.status_code}")
            return
            
    except Exception as e:
        print(f"❌ Error testing streaming API: {e}")
        return
    
    # Open browser
    print("\n🌐 Opening browser...")
    print("URL: http://localhost:3000")
    print("\n📝 Try these test tasks in the frontend:")
    print("1. 'Count from 1 to 5' - Simple counting task")
    print("2. 'Create a Python script that prints Hello World' - File creation")
    print("3. 'Calculate 2 + 2 and explain the result' - Math task")
    print("4. Upload an image and ask 'Describe this image' - Vision task")
    
    print("\n💡 Watch the streaming output in real-time!")
    print("   - Each step will appear as it's processed")
    print("   - Files will be automatically detected and linked")
    print("   - Images can be uploaded via drag & drop")
    
    try:
        webbrowser.open("http://localhost:3000")
        print("\n✅ Browser opened successfully!")
        print("Press Ctrl+C to exit this demo")
        
        # Keep the script running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n👋 Demo ended. Servers are still running.")
        print("Stop them manually if needed:")
        print("- API: Ctrl+C in the api_server.py terminal")
        print("- Frontend: Ctrl+C in the frontend server terminal")

if __name__ == "__main__":
    main() 