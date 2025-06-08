#!/usr/bin/env python3
"""
Production API launcher for HWAgent
Optimized for VPS deployment
"""

import uvicorn
import os
import logging
from pathlib import Path

def setup_logging():
    """Setup logging for production"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "hwagent-api.log"),
            logging.StreamHandler()
        ]
    )

def main():
    print("🚀 HWAgent API Server (Production)")
    print("=" * 40)
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Enable verbose mode for agent thinking
    os.environ['HWAGENT_VERBOSE'] = '1'
    
    logger.info("🧠 Agent verbose mode enabled")
    logger.info("🔧 Starting production API server...")
    
    try:
        uvicorn.run(
            "api_server:app",
            host="0.0.0.0",
            port=8000,
            reload=False,  # Disable reload for production
            log_level="info",
            access_log=True,
            workers=1  # Single worker for now, can increase based on needs
        )
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"💥 Server error: {e}")
        raise

if __name__ == "__main__":
    main() 