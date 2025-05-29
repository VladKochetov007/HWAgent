"""
Agent Configuration Manager
Handles loading and accessing agent behavior settings from YAML configuration.
"""

from pathlib import Path
from typing import Any, Dict
import yaml


class AgentConfig:
    """Manages agent configuration settings."""
    
    def __init__(self, config_path: str = "hwagent/config/agent_settings.yaml"):
        self.config_path = config_path
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            config_file = Path(self.config_path)
            if not config_file.exists():
                # Return default configuration if file doesn't exist
                return self._get_default_config()
            
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # Merge with defaults to ensure all keys exist
            default_config = self._get_default_config()
            return self._merge_configs(default_config, config)
            
        except Exception as e:
            print(f"Warning: Failed to load agent config from {self.config_path}: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration values."""
        return {
            "react_agent": {
                "max_iterations": 25,
                "max_empty_responses": 25,
                "max_total_empty_responses": 25,
                "max_consecutive_errors": 5,
                "response_timeout": 60,
                "tool_execution_timeout": 120,
                "messages": {
                    "max_iterations_reached": "Agent reached maximum iteration limit. Please rephrase your request or clear context.",
                    "too_many_empty_responses": "Too many consecutive empty responses. Please rephrase your request or clear context.",
                    "too_many_total_empty_responses": "Too many total empty responses in session. Recommended to clear context and start fresh.",
                    "too_many_consecutive_errors": "Too many consecutive errors. Please check system status.",
                    "context_cleared": "Context has been cleared successfully.",
                    "streaming_enabled": "Streaming responses enabled.",
                    "streaming_disabled": "Streaming responses disabled."
                },
                "debug": {
                    "enabled": False,
                    "verbose_parsing": False,
                    "verbose_iteration": False,
                    "log_tool_calls": False,
                    "log_empty_responses": False
                }
            },
            "early_termination": {
                "enabled": True,
                "conditions": {
                    "consecutive_empty_limit": 25,
                    "total_empty_limit": 25,
                    "consecutive_error_limit": 5
                }
            }
        }
    
    def _merge_configs(self, default: Dict[str, Any], loaded: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge loaded config with default config."""
        if not loaded:
            return default
        
        merged = default.copy()
        for key, value in loaded.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value
        
        return merged
    
    def get_react_agent_config(self) -> Dict[str, Any]:
        """Get ReAct agent specific configuration."""
        return self._config.get("react_agent", {})
    
    def get_early_termination_config(self) -> Dict[str, Any]:
        """Get early termination configuration."""
        return self._config.get("early_termination", {})
    
    def get_max_iterations(self) -> int:
        """Get maximum iterations limit."""
        return self.get_react_agent_config().get("max_iterations", 25)
    
    def get_max_empty_responses(self) -> int:
        """Get maximum consecutive empty responses limit."""
        return self.get_react_agent_config().get("max_empty_responses", 25)
    
    def get_max_total_empty_responses(self) -> int:
        """Get maximum total empty responses limit."""
        return self.get_react_agent_config().get("max_total_empty_responses", 25)
    
    def get_max_consecutive_errors(self) -> int:
        """Get maximum consecutive errors limit."""
        return self.get_react_agent_config().get("max_consecutive_errors", 5)
    
    def get_message(self, message_key: str) -> str:
        """Get system message by key."""
        messages = self.get_react_agent_config().get("messages", {})
        return messages.get(message_key, f"System message not found: {message_key}")
    
    def reload_config(self) -> None:
        """Reload configuration from file."""
        self._config = self._load_config()
    
    def is_debug_enabled(self) -> bool:
        """Check if debug logging is enabled."""
        return self.get_react_agent_config().get("debug", {}).get("enabled", False)
    
    def is_verbose_parsing_enabled(self) -> bool:
        """Check if verbose parsing logging is enabled."""
        return self.get_react_agent_config().get("debug", {}).get("verbose_parsing", False)
    
    def is_verbose_iteration_enabled(self) -> bool:
        """Check if verbose iteration logging is enabled."""
        return self.get_react_agent_config().get("debug", {}).get("verbose_iteration", False)
    
    def is_tool_call_logging_enabled(self) -> bool:
        """Check if tool call logging is enabled."""
        return self.get_react_agent_config().get("debug", {}).get("log_tool_calls", False)
    
    def is_empty_response_logging_enabled(self) -> bool:
        """Check if empty response logging is enabled."""
        return self.get_react_agent_config().get("debug", {}).get("log_empty_responses", False)
    
    def is_smart_completion_enabled(self) -> bool:
        """Check if smart completion is enabled."""
        return self.get_react_agent_config().get("smart_completion", {}).get("enabled", False)
    
    def get_early_completion_threshold(self) -> float:
        """Get early completion confidence threshold."""
        return self.get_react_agent_config().get("smart_completion", {}).get("early_completion_threshold", 0.8)
    
    def get_iteration_warning_threshold(self) -> float:
        """Get iteration warning threshold."""
        return self.get_react_agent_config().get("smart_completion", {}).get("iteration_warning_threshold", 0.8)
    
    def should_show_remaining_iterations(self) -> bool:
        """Check if remaining iterations should be shown to agent."""
        return self.get_react_agent_config().get("smart_completion", {}).get("show_remaining_iterations", True)
    
    def get_iteration_warning_message(self, current_iteration: int, max_iterations: int) -> str:
        """Get iteration warning message."""
        template = self.get_message("iteration_warning")
        return template.format(current_iteration=current_iteration, max_iterations=max_iterations)
    
    def get_final_attempt_warning(self, current_iteration: int, max_iterations: int) -> str:
        """Get final attempt warning message."""
        template = self.get_message("final_attempt_warning")
        return template.format(current_iteration=current_iteration, max_iterations=max_iterations)
    
    def get_polite_completion_request(self) -> str:
        """Get polite completion request message."""
        return self.get_message("polite_completion_request")


# Global instance for easy access
_global_agent_config = None


def get_agent_config() -> AgentConfig:
    """Get global agent configuration instance."""
    global _global_agent_config
    if _global_agent_config is None:
        _global_agent_config = AgentConfig()
    return _global_agent_config


def reload_agent_config() -> None:
    """Reload global agent configuration."""
    global _global_agent_config
    if _global_agent_config is not None:
        _global_agent_config.reload_config()
    else:
        _global_agent_config = AgentConfig() 