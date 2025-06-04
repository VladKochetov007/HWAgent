#!/usr/bin/env python3
"""
Test runner for HWAgent API tests
"""

import sys
import subprocess
import requests
import time
import os
from pathlib import Path

API_BASE = "http://localhost:8000"

def check_api_available():
    """Check if API is available"""
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def wait_for_api(timeout=30):
    """Wait for API to become available"""
    print("⏳ Waiting for API to become available...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        if check_api_available():
            print("✅ API is available!")
            return True
        time.sleep(1)
    
    return False

def run_tests():
    """Run all tests"""
    if not check_api_available():
        print(f"❌ API not available at {API_BASE}")
        print("Starting API server...")
        
        # Try to start API server
        try:
            api_process = subprocess.Popen([
                sys.executable, "api_server.py"
            ], cwd=Path(__file__).parent.parent)
            
            # Wait for API to become available
            if not wait_for_api():
                print("❌ Failed to start API server")
                api_process.terminate()
                return False
                
        except Exception as e:
            print(f"❌ Failed to start API server: {e}")
            print("Please start the API server manually: python api_server.py")
            return False
    
    print(f"✅ API available at {API_BASE}")
    
    # Get test directory
    test_dir = Path(__file__).parent
    
    # Run tests with pytest
    try:
        print("\n🧪 Running basic API tests...")
        result1 = subprocess.run([
            sys.executable, "-m", "pytest", 
            str(test_dir / "test_api_basic.py"),
            "-v", "--tb=short"
        ], cwd=test_dir.parent)
        
        print("\n🌊 Running streaming tests...")
        result2 = subprocess.run([
            sys.executable, "-m", "pytest", 
            str(test_dir / "test_streaming.py"),
            "-v", "--tb=short"
        ], cwd=test_dir.parent)
        
        # Overall result
        if result1.returncode == 0 and result2.returncode == 0:
            print("\n✅ All tests passed!")
            return True
        else:
            print("\n❌ Some tests failed!")
            return False
            
    except Exception as e:
        print(f"❌ Failed to run tests: {e}")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1) 