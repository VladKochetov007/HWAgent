"""API client utilities for external services."""

import aiohttp
import asyncio
from typing import Any
from .config import config


class OpenRouterClient:
    """Async client for OpenRouter API."""
    
    def __init__(self):
        self.base_url = config.api_config["openrouter"]["base_url"]
        self.api_key = config.openrouter_api_key
        self.thinking_model = config.api_config["openrouter"]["thinking_model"]
        self.simple_model = config.api_config["openrouter"]["simple_model"]
    
    async def _make_request(self, model: str, messages: list[dict], **kwargs) -> dict[str, Any]:
        """Make request to OpenRouter API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/yourusername/hwagent",
            "X-Title": "HWAgent"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 4000),
            **kwargs
        }
        
        timeout = aiohttp.ClientTimeout(total=config.agent_settings["react_agent"]["thinking_timeout"])
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"OpenRouter API error: {response.status} - {error_text}")
                
                result = await response.json()
                return result
    
    async def thinking_completion(self, messages: list[dict], **kwargs) -> str:
        """Get completion from thinking model."""
        result = await self._make_request(self.thinking_model, messages, **kwargs)
        return result["choices"][0]["message"]["content"]
    
    async def simple_completion(self, messages: list[dict], **kwargs) -> str:
        """Get completion from simple model."""
        result = await self._make_request(self.simple_model, messages, **kwargs)
        return result["choices"][0]["message"]["content"]


class LangSearchClient:
    """Async client for LangSearch API."""
    
    def __init__(self):
        self.api_key = config.langsearch_api_key
        self.base_url = "https://api.langsearch.ai/v1"
    
    async def search(self, query: str, max_results: int | None = None) -> list[dict[str, Any]]:
        """Search the web using LangSearch API."""
        if max_results is None:
            max_results = config.agent_settings["react_agent"]["web_search"]["max_results"]
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "query": query,
            "limit": max_results
        }
        
        timeout = aiohttp.ClientTimeout(
            total=config.agent_settings["react_agent"]["web_search"]["timeout"]
        )
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                f"{self.base_url}/search",
                headers=headers,
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"LangSearch API error: {response.status} - {error_text}")
                
                result = await response.json()
                return result.get("results", [])


# Global client instances
openrouter_client = OpenRouterClient()
langsearch_client = LangSearchClient() 