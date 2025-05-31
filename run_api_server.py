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

def check_dependencies():
    """Check if all required dependencies are available."""
    required_modules = [
        'flask',
        'flask_socketio',
        'flask_cors',
        'openai',
        'yaml'
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        print("❌ Missing required dependencies:")
        for module in missing_modules:
            print(f"   - {module}")
        print("\nInstall them with: pip install -r requirements_api.txt")
        return False
    
    return True

def check_configuration():
    """Check if configuration files exist."""
    config_files = [
        'hwagent/config/api.yaml',
        'hwagent/config/prompts.yaml'
    ]
    
    missing_files = []
    for config_file in config_files:
        if not Path(config_file).exists():
            missing_files.append(config_file)
    
    if missing_files:
        print("❌ Missing configuration files:")
        for file in missing_files:
            print(f"   - {file}")
        return False
    
    return True

def setup_directories():
    """Create necessary directories."""
    directories = [
        'static',
        'tmp'
    ]
    
    for directory in directories:
        dir_path = Path(directory)
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"📁 Created directory: {directory}")

def main():
    """Main function to run the API server."""
    print("🚀 HWAgent API Server Launcher")
    print("=" * 50)
    
    # Check dependencies
    print("🔍 Checking dependencies...")
    if not check_dependencies():
        return 1
    print("✅ All dependencies available")
    
    # Check configuration
    print("🔍 Checking configuration...")
    if not check_configuration():
        return 1
    print("✅ Configuration files found")
    
    # Check environment variables
    print("🔍 Checking environment...")
    api_key = os.environ.get('OPENROUTER_API_KEY')
    if not api_key:
        print("❌ Error: OPENROUTER_API_KEY environment variable not set")
        print("Please set it with: export OPENROUTER_API_KEY='your_api_key'")
        return 1
    print("✅ API key configured")
    
    # Setup directories
    print("🔍 Setting up directories...")
    setup_directories()
    print("✅ Directories ready")
    
    # Set default environment variables if not present
    os.environ.setdefault('HOST', '127.0.0.1')
    os.environ.setdefault('PORT', '5000')
    os.environ.setdefault('DEBUG', 'False')
    
    host = os.environ.get('HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    print("\n" + "=" * 50)
    print(f"🚀 Server configuration:")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   Debug: {debug}")
    print(f"   API Key: {'✅ Set' if api_key else '❌ Missing'}")
    print("=" * 50)
    
    try:
        # Import and run server
        print("🔄 Starting server...")
        from hwagent.api_server import run_server
        
        static_dir = current_dir / 'static'
        print(f"📁 Static files directory: {static_dir}")
        print(f"🌐 Web interface: http://{host}:{port}")
        print(f"📡 API endpoints: http://{host}:{port}/api/")
        print(f"🔗 Health check: http://{host}:{port}/api/health")
        print("=" * 50)
        print("✨ HWAgent is ready! Open your browser and start chatting!")
        print("Press Ctrl+C to stop the server")
        print()
        
        # Run the server
        run_server(host=host, port=port, debug=debug)
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        return 0
    except ImportError as e:
        print(f"❌ Error importing server module: {e}")
        print("Make sure you're in the correct directory and dependencies are installed.")
        return 1
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        print("Check the configuration and try again.")
        return 1

if __name__ == '__main__':
    sys.exit(main()) 