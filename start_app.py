#!/usr/bin/env python3
"""
Universal HWAgent launcher: API server + Frontend with agent reasoning output
"""

import subprocess
import sys
import time
import signal
import threading
import webbrowser
import os
from pathlib import Path
import requests
import uvicorn
import asyncio
from multiprocessing import Process

class ServerManager:
    def __init__(self):
        self.api_process = None
        self.frontend_process = None
        self.running = True
        
    def check_dependencies(self):
        """Check dependencies"""
        print("🔍 Checking dependencies...")
        
        required_packages = [
            ('fastapi', 'fastapi'),
            ('uvicorn', 'uvicorn'),
            ('Pillow', 'PIL'),
            ('requests', 'requests')
        ]
        
        missing_packages = []
        
        for package_name, import_name in required_packages:
            try:
                __import__(import_name)
            except ImportError:
                missing_packages.append(package_name)
        
        if missing_packages:
            print(f"❌ Missing packages: {', '.join(missing_packages)}")
            print("Install them with:")
            print(f"pip install {' '.join(missing_packages)}")
            return False
        
        print("✅ All dependencies are installed")
        return True
    
    def check_frontend(self):
        """Check if frontend exists"""
        frontend_dir = Path("frontend")
        frontend_file = frontend_dir / "index.html"
        
        if frontend_file.exists():
            print("✅ Frontend found at frontend/index.html")
            return True
        else:
            print("⚠️ Frontend not found at frontend/index.html")
            print("   Frontend server will be skipped")
            return False
    
    def run_api_server_verbose(self):
        """Start API server with verbose logs in main process"""
        print("🚀 Starting API server with verbose agent logging...")
        
        # Set environment variable for verbose logging
        os.environ['HWAGENT_VERBOSE'] = '1'
        
        try:
            # Import and run API server directly
            import api_server
            
            # Configure uvicorn config to display logs
            config = uvicorn.Config(
                app=api_server.app,
                host="0.0.0.0",
                port=8000,
                log_level="info",
                access_log=True,
                reload=False  # Disable reload to avoid multiprocessing issues
            )
            
            server = uvicorn.Server(config)
            
            print("🧠 Agent thinking process will be displayed in terminal")
            print("📝 All agent reasoning steps will be visible below")
            print("=" * 70)
            
            # Start server (blocking call)
            server.run()
            
        except KeyboardInterrupt:
            print("\n🛑 API server stopped by user")
        except Exception as e:
            print(f"❌ Failed to start API server: {e}")
            raise
    
    def start_frontend_server(self):
        """Start frontend server in separate process"""
        frontend_dir = Path("frontend")
        if not frontend_dir.exists() or not (frontend_dir / "index.html").exists():
            print("⚠️ Frontend directory or index.html not found, skipping frontend server")
            return False
        
        print("🌐 Starting frontend server on localhost:3000...")
        
        cmd = [
            sys.executable, "-m", "http.server",
            "3000",
            "--bind", "0.0.0.0",
            "--directory", str(frontend_dir)
        ]
        
        try:
            self.frontend_process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,  # Suppress frontend server output
                stderr=subprocess.DEVNULL,
                universal_newlines=True
            )
            return True
        except Exception as e:
            print(f"❌ Failed to start frontend server: {e}")
            return False
    
    def open_browser_delayed(self):
        """Open browser with delay"""
        def delayed_open():
            time.sleep(8)  # Increased delay for API server
            try:
                # Try frontend first, if not available then API
                frontend_url = "http://localhost:3000"
                api_url = "http://localhost:8000"
                
                try:
                    requests.get(frontend_url, timeout=2)
                    url = frontend_url
                    print(f"\n🌐 Opening frontend at {url}")
                except:
                    url = api_url
                    print(f"\n🌐 Opening API interface at {url}")
                
                webbrowser.open(url)
            except Exception as e:
                print(f"\n⚠️ Could not open browser: {e}")
        
        thread = threading.Thread(target=delayed_open, daemon=True)
        thread.start()
    
    def stop_servers(self):
        """Stop servers"""
        print("\n🛑 Shutting down servers...")
        self.running = False
        
        if self.frontend_process:
            self.frontend_process.terminate()
            try:
                self.frontend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.frontend_process.kill()
        
        print("✅ Servers stopped")
    
    def run(self):
        """Main startup loop with detailed agent reasoning output"""
        print("🤖 HWAgent Full Stack Launcher with Verbose Agent Thinking")
        print("=" * 70)
        
        # Check dependencies
        if not self.check_dependencies():
            sys.exit(1)
        
        # Check frontend
        frontend_available = self.check_frontend()
        
        # Create necessary directories
        Path("uploads").mkdir(exist_ok=True)
        
        try:
            # Start frontend server in background if available
            if frontend_available:
                self.start_frontend_server()
            
            # Start browser with delay
            self.open_browser_delayed()
            
            print(f"\n🎉 Services will be available at:")
            print(f"   🔧 API Server: http://localhost:8000")
            if frontend_available:
                print(f"   🌐 Frontend: http://localhost:3000")
            print(f"   📖 API Docs: http://localhost:8000/docs")
            
            print(f"\n🧠 AGENT THINKING MODE ENABLED")
            print(f"   • All agent reasoning will be displayed below")
            print(f"   • Step-by-step execution will be visible")
            if frontend_available:
                print(f"   • Use web interface to submit tasks")
            else:
                print(f"   • Use API directly or add frontend/index.html")
            
            print(f"\n🛑 Press Ctrl+C to stop all servers")
            print("=" * 70)
            
            # Start API server with verbose logs (blocking call)
            self.run_api_server_verbose()
        
        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(f"\n❌ Error: {e}")
        finally:
            self.stop_servers()

def main():
    manager = ServerManager()
    
    # Handle signals
    def signal_handler(signum, frame):
        manager.stop_servers()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    manager.run()

if __name__ == "__main__":
    main()
