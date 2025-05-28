"""
Message Manager for handling application messages.
Following Single Responsibility Principle - handles only message loading and formatting.
"""

from typing import Any
from hwagent.config_loader import load_yaml_config
from hwagent.core.exceptions import ConfigurationError


class MessageManager:
    """Manages application messages from configuration files."""
    
    def __init__(self, messages_config_path: str = "hwagent/config/messages.yaml"):
        """
        Initialize MessageManager with messages configuration.
        
        Args:
            messages_config_path: Path to messages configuration file
        """
        self.config_path = messages_config_path
        self._messages = self._load_messages()
    
    def _load_messages(self) -> dict[str, Any]:
        """Load messages from configuration file."""
        try:
            return load_yaml_config(self.config_path)
        except Exception as e:
            raise ConfigurationError(f"Failed to load messages from {self.config_path}", str(e))
    
    def get_message(self, section: str, key: str, default: str | None = None) -> str:
        """
        Get a message from configuration.
        
        Args:
            section: Message section (e.g., 'react_agent', 'tool_manager')
            key: Message key within section
            default: Default message if not found
            
        Returns:
            Formatted message string
        """
        section_messages = self._messages.get(section, {})
        message = section_messages.get(key, default)
        
        if message is None:
            raise KeyError(f"Message not found: {section}.{key}")
        
        return message
    
    def get_nested_message(self, section: str, subsection: str, key: str, default: str | None = None) -> str:
        """
        Get a nested message from configuration.
        
        Args:
            section: Main section (e.g., 'react_agent')
            subsection: Subsection (e.g., 'parser')
            key: Message key within subsection
            default: Default message if not found
            
        Returns:
            Formatted message string
        """
        section_messages = self._messages.get(section, {})
        subsection_messages = section_messages.get(subsection, {})
        message = subsection_messages.get(key, default)
        
        if message is None:
            raise KeyError(f"Message not found: {section}.{subsection}.{key}")
        
        return message
    
    def format_message(self, section: str, key: str, **kwargs) -> str:
        """
        Get and format a message with provided arguments.
        
        Args:
            section: Message section
            key: Message key
            **kwargs: Arguments for string formatting
            
        Returns:
            Formatted message string
        """
        message_template = self.get_message(section, key)
        return message_template.format(**kwargs)
    
    def format_nested_message(self, section: str, subsection: str, key: str, **kwargs) -> str:
        """
        Get and format a nested message with provided arguments.
        
        Args:
            section: Main section
            subsection: Subsection
            key: Message key
            **kwargs: Arguments for string formatting
            
        Returns:
            Formatted message string
        """
        message_template = self.get_nested_message(section, subsection, key)
        return message_template.format(**kwargs)
    
    def get_section(self, section: str) -> dict[str, Any]:
        """
        Get entire message section.
        
        Args:
            section: Section name
            
        Returns:
            Dictionary with all messages in section
        """
        return self._messages.get(section, {}) 