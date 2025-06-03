#!/usr/bin/env python3
"""
Simple API-only launcher for HWAgent
For quick testing without frontend
"""

import uvicorn
import os

def main():
    print("🚀 HWAgent API Server")
    print("=" * 30)
    
    # Enable verbose mode for agent thinking
    os.environ['HWAGENT_VERBOSE'] = '1'
    
    print("🧠 Agent verbose mode enabled")
    print("🔧 Starting API server on localhost:8000...")
    print("📖 API documentation: http://localhost:8000/docs")
    print("🛑 Press Ctrl+C to stop")
    print()
    
    try:
        uvicorn.run(
            "api_server:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")

if __name__ == "__main__":
    main() 