#!/usr/bin/env python3
"""
HWAgent API Server Launcher
Simple script to run the new REST API server with proper environment setup.
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from hwagent.api_server import run_server

def main():
    """Main function to run the API server."""
    print("Starting HWAgent API Server...")
    print("=" * 50)
    
    # Check environment variables
    api_key = os.environ.get('OPENROUTER_API_KEY')
    if not api_key:
        print("❌ Error: OPENROUTER_API_KEY environment variable not set")
        print("Please set it with: export OPENROUTER_API_KEY='your_api_key'")
        return 1
    
    # Set default environment variables if not present
    os.environ.setdefault('HOST', '127.0.0.1')
    os.environ.setdefault('PORT', '5000')
    os.environ.setdefault('DEBUG', 'False')
    
    host = os.environ.get('HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    print(f"🚀 Server configuration:")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   Debug: {debug}")
    print(f"   API Key: {'✅ Set' if api_key else '❌ Missing'}")
    print("=" * 50)
    
    try:
        # Create static directory if it doesn't exist
        static_dir = current_dir / 'static'
        static_dir.mkdir(exist_ok=True)
        
        print(f"📁 Static files directory: {static_dir}")
        print(f"🌐 Access the web interface at: http://{host}:{port}")
        print(f"📡 API endpoints available at: http://{host}:{port}/api/")
        print(f"🔗 Health check: http://{host}:{port}/api/health")
        print("=" * 50)
        print("Press Ctrl+C to stop the server")
        print()
        
        # Run the server
        run_server(host=host, port=port, debug=debug)
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        return 0
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main()) 