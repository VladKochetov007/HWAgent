"""Configuration utilities for HWAgent."""

import os
import yaml
from pathlib import Path
from typing import Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration manager for HWAgent."""
    
    def __init__(self):
        self.config_dir = Path(__file__).parent.parent / "config"
        self._agent_settings = None
        self._api_config = None
        self._prompts = None
    
    def _load_yaml(self, filename: str) -> dict[str, Any]:
        """Load YAML configuration file."""
        filepath = self.config_dir / filename
        if not filepath.exists():
            raise FileNotFoundError(f"Configuration file not found: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    
    @property
    def agent_settings(self) -> dict[str, Any]:
        """Get agent settings from agent_settings.yaml."""
        if self._agent_settings is None:
            self._agent_settings = self._load_yaml("agent_settings.yaml")
        return self._agent_settings
    
    @property
    def api_config(self) -> dict[str, Any]:
        """Get API configuration from api.yaml."""
        if self._api_config is None:
            self._api_config = self._load_yaml("api.yaml")
        return self._api_config
    
    @property
    def prompts(self) -> dict[str, Any]:
        """Get prompts from prompts.yaml."""
        if self._prompts is None:
            self._prompts = self._load_yaml("prompts.yaml")
        return self._prompts
    
    @property
    def openrouter_api_key(self) -> str:
        """Get OpenRouter API key from environment."""
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable is required")
        return api_key
    
    @property
    def langsearch_api_key(self) -> str:
        """Get LangSearch API key from environment."""
        api_key = os.getenv("LANGSEARCH_API_KEY")
        if not api_key:
            raise ValueError("LANGSEARCH_API_KEY environment variable is required")
        return api_key
    
    @property
    def debug(self) -> bool:
        """Get debug mode from environment."""
        return os.getenv("DEBUG", "False").lower() == "true"
    
    @property
    def log_level(self) -> str:
        """Get log level from environment."""
        return os.getenv("LOG_LEVEL", "INFO")

# Global config instance
config = Config() 