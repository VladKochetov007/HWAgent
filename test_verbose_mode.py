#!/usr/bin/env python3
"""
Test script to verify verbose agent reasoning mode
"""

import requests
import time
import json

def test_api_health():
    """Test API health endpoint"""
    print("🔍 Testing API health...")
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API is healthy: {data['agent_type']}")
            print(f"🖼️ Vision support: {data.get('vision_supported', False)}")
            return True
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error connecting to API: {e}")
        return False

def test_simple_task():
    """Test simple task execution"""
    print("\n🧮 Testing simple task...")
    try:
        payload = {
            "task": "Calculate 2 + 2 and explain the result",
            "max_steps": 2
        }
        
        print("📤 Sending request to API...")
        response = requests.post(
            "http://localhost:8000/run-task",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Task completed successfully!")
            print(f"📝 Result: {result['result'][:100]}...")
            if result.get('has_attachments'):
                print(f"📎 Generated files: {result['files']}")
            return True
        else:
            print(f"❌ Task failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error executing task: {e}")
        return False

def test_programming_task():
    """Test programming task that should show thinking process"""
    print("\n💻 Testing programming task...")
    try:
        payload = {
            "task": "Write a Python function to check if a number is prime. Test it with a few examples.",
            "max_steps": 5
        }
        
        print("📤 Sending programming task...")
        print("🧠 Check terminal running start_app.py for agent reasoning steps...")
        
        response = requests.post(
            "http://localhost:8000/run-task",
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Programming task completed!")
            print(f"📝 Result length: {len(result['result'])} characters")
            if result.get('has_attachments'):
                print(f"📎 Generated files: {result['files']}")
            return True
        else:
            print(f"❌ Programming task failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error executing programming task: {e}")
        return False

def main():
    """Main test function"""
    print("🤖 HWAgent Verbose Mode Test")
    print("=" * 50)
    
    # Test API health
    if not test_api_health():
        print("❌ API is not accessible. Make sure start_app.py is running.")
        return
    
    print("\n📋 Running tests...")
    print("💡 Agent thinking process should be visible in the terminal running start_app.py")
    print("💡 Look for detailed step-by-step reasoning output")
    
    # Test simple task
    test_simple_task()
    time.sleep(2)
    
    # Test programming task
    test_programming_task()
    
    print("\n🎉 Tests completed!")
    print("💡 If you can see agent reasoning steps in the start_app.py terminal, verbose mode is working!")
    print("🚀 Try the web interface at http://localhost:3000")

if __name__ == "__main__":
    main() 