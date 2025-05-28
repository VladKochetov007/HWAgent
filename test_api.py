#!/usr/bin/env python3
"""
Simple test to check the HWAgent REST API.
Checks main endpoints and functionality.
"""

import requests
import json
import time
import sys
from typing import Dict, Any


class APITester:
    """Simple tester for HWAgent API."""
    
    def __init__(self, base_url: str = "http://127.0.0.1:5000"):
        self.base_url = base_url
        self.session_id: str | None = None
        
    def test_health(self) -> bool:
        """Test the health endpoint."""
        print("🔍 Testing health endpoint...")
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health OK: {data['status']}")
                return True
            else:
                print(f"❌ Health failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Health error: {e}")
            return False
    
    def test_create_session(self) -> bool:
        """Create a new session."""
        print("🔍 Creating a new session...")
        try:
            response = requests.post(f"{self.base_url}/api/sessions", timeout=10)
            if response.status_code == 201:
                data = response.json()
                self.session_id = data["session_id"]
                print(f"✅ Session created: {self.session_id}")
                return True
            else:
                print(f"❌ Error creating session: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error creating session: {e}")
            return False
    
    def test_session_info(self) -> bool:
        """Get session information."""
        if not self.session_id:
            print("❌ No active session to test")
            return False
            
        print("🔍 Getting session information...")
        try:
            response = requests.get(
                f"{self.base_url}/api/sessions/{self.session_id}",
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Session information retrieved: {data}")
                return True
            else:
                print(f"❌ Error retrieving information: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error retrieving information: {e}")
            return False
    
    def test_send_message(self) -> bool:
        """Send a message."""
        if not self.session_id:
            print("❌ No active session to send a message")
            return False
            
        print("🔍 Sending a test message...")
        try:
            message_data = {
                "message": "Hello! Can you calculate 2 + 2?"
            }
            response = requests.post(
                f"{self.base_url}/api/sessions/{self.session_id}/messages",
                json=message_data,
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Response received: {data['response'][:100]}...")
                return True
            else:
                print(f"❌ Error sending message: {response.status_code}")
                if response.text:
                    print(f"Details: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error sending message: {e}")
            return False
    
    def test_tools_endpoint(self) -> bool:
        """Test the tools endpoint."""
        print("🔍 Getting list of tools...")
        try:
            response = requests.get(f"{self.base_url}/api/tools", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Tools found: {data['count']}")
                for tool in data['tools'][:3]:  # Show first 3
                    print(f"  - {tool['name']}: {tool['description']}")
                return True
            else:
                print(f"❌ Error getting tools: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error getting tools: {e}")
            return False
    
    def test_context_management(self) -> bool:
        """Test context management."""
        if not self.session_id:
            print("❌ No active session for context management")
            return False
            
        print("🔍 Testing context management...")
        try:
            # Get context
            response = requests.get(
                f"{self.base_url}/api/sessions/{self.session_id}/context",
                timeout=5
            )
            if response.status_code == 200:
                print("✅ Context retrieved")
            
            # Clear context
            response = requests.delete(
                f"{self.base_url}/api/sessions/{self.session_id}/context",
                timeout=5
            )
            if response.status_code == 200:
                print("✅ Context cleared")
                return True
            else:
                print(f"❌ Error clearing context: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error in context management: {e}")
            return False
    
    def test_delete_session(self) -> bool:
        """Delete a session."""
        if not self.session_id:
            print("❌ No active session to delete")
            return False
            
        print("🔍 Deleting session...")
        try:
            response = requests.delete(
                f"{self.base_url}/api/sessions/{self.session_id}",
                timeout=5
            )
            if response.status_code == 200:
                print("✅ Session deleted")
                self.session_id = None
                return True
            else:
                print(f"❌ Error deleting session: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error deleting session: {e}")
            return False
    
    def run_all_tests(self) -> None:
        """Run all tests."""
        print("🚀 Starting HWAgent REST API tests\n")
        print(f"Testing server: {self.base_url}")
        print("=" * 50)
        
        tests = [
            ("Health Check", self.test_health),
            ("Create Session", self.test_create_session),
            ("Session Information", self.test_session_info),
            ("List Tools", self.test_tools_endpoint),
            ("Send Message", self.test_send_message),
            ("Context Management", self.test_context_management),
            ("Delete Session", self.test_delete_session),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n{test_name}:")
            try:
                if test_func():
                    passed += 1
                time.sleep(1)  # Short pause between tests
            except KeyboardInterrupt:
                print("\n❌ Testing interrupted by user")
                break
            except Exception as e:
                print(f"❌ Unexpected error in test '{test_name}': {e}")
        
        print("\n" + "=" * 50)
        print(f"📊 Results: {passed}/{total} tests passed successfully")
        
        if passed == total:
            print("🎉 All tests passed successfully!")
        elif passed > total // 2:
            print("⚠️ Most tests passed, but there are issues")
        else:
            print("❌ Many tests failed, check the server")

def main():
    """Main function."""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://127.0.0.1:5000"
    
    print(f"HWAgent API Tester")
    print(f"Server: {base_url}")
    
    tester = APITester(base_url)
    tester.run_all_tests()


if __name__ == "__main__":
    main() 