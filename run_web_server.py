#!/usr/bin/env python3
"""
HWAgent Web Server - запуск веб-интерфейса для HWAgent
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add current directory to Python path to enable absolute imports
sys.path.insert(0, os.getcwd())

if __name__ == "__main__":
    from hwagent.web_server import app, socketio, initialize_agent
    
    # Initialize agent first
    print("🔧 Initializing HWAgent...")
    if not initialize_agent():
        print("❌ Failed to initialize agent. Exiting.")
        sys.exit(1)
    print("✅ Agent initialized successfully!")
    
    # Run the web server with SocketIO support
    print("🚀 Starting HWAgent Web Server...")
    print("📱 Frontend available at: http://localhost:5000")
    print("🔌 WebSocket endpoint: ws://localhost:5000")
    print("⚡ Press Ctrl+C to stop the server")
    
    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=True,
        allow_unsafe_werkzeug=True
    ) 