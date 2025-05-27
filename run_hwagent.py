#!/usr/bin/env python3
"""
HWAgent Runner - запуск агента из корня проекта
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add current directory to Python path to enable absolute imports
sys.path.insert(0, os.getcwd())

if __name__ == "__main__":
    from hwagent.main import main
    main() 