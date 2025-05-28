"""
Conversation Manager for handling conversation history.
Following Single Responsibility Principle - handles only conversation state.
"""

from typing import Any
from hwagent.core.models import ConversationMessage
from hwagent.core.message_manager import MessageManager


class ConversationManager:
    """Manages conversation history and context."""
    
    def __init__(self, message_manager: MessageManager):
        """
        Initialize ConversationManager.
        
        Args:
            message_manager: Message manager for display messages
        """
        self.message_manager = message_manager
        self.conversation_history: list[dict[str, Any]] = []
    
    def initialize_with_system_prompt(self, system_prompt: str) -> None:
        """
        Initialize conversation with system prompt.
        
        Args:
            system_prompt: System prompt to initialize conversation
        """
        if not self.conversation_history:
            self.conversation_history = [
                {"role": "system", "content": system_prompt}
            ]
    
    def add_user_message(self, content: str) -> None:
        """
        Add user message to conversation history.
        
        Args:
            content: User message content
        """
        self.conversation_history.append({"role": "user", "content": content})
    
    def add_assistant_message(self, message_obj: Any) -> None:
        """
        Add assistant message to conversation history.
        
        Args:
            message_obj: Assistant message object from OpenAI API
        """
        self.conversation_history.append(message_obj.model_dump(exclude_none=True))
    
    def add_tool_result(self, tool_call_id: str, tool_name: str, content: str) -> None:
        """
        Add tool execution result to conversation history.
        
        Args:
            tool_call_id: ID of the tool call
            tool_name: Name of the executed tool
            content: Tool execution result content
        """
        self.conversation_history.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": tool_name,
            "content": content
        })
    
    def add_system_note(self, content: str) -> None:
        """
        Add system note to conversation history.
        
        Args:
            content: System note content
        """
        self.conversation_history.append({"role": "assistant", "content": content})
    
    def get_conversation_history(self) -> list[dict[str, Any]]:
        """
        Get complete conversation history.
        
        Returns:
            List of conversation messages
        """
        return self.conversation_history.copy()
    
    def clear_conversation(self) -> None:
        """Clear conversation history but keep system prompt."""
        system_prompt = None
        if self.conversation_history and self.conversation_history[0]["role"] == "system":
            system_prompt = self.conversation_history[0]
        
        self.conversation_history = []
        if system_prompt:
            self.conversation_history.append(system_prompt)
    
    def get_context_summary(self) -> str:
        """
        Get summary of current conversation context.
        
        Returns:
            Formatted context summary string
        """
        if len(self.conversation_history) <= 1:
            return self.message_manager.get_message("react_agent", "no_conversation_history")
        
        # Count message types
        user_messages = len([msg for msg in self.conversation_history if msg["role"] == "user"])
        assistant_messages = len([msg for msg in self.conversation_history if msg["role"] == "assistant"])
        tool_messages = len([msg for msg in self.conversation_history if msg["role"] == "tool"])
        
        return self.message_manager.format_message(
            "react_agent", "context_summary",
            user_messages=user_messages,
            assistant_messages=assistant_messages,
            tool_messages=tool_messages
        )
    
    def has_conversation_history(self) -> bool:
        """
        Check if conversation has any history beyond system prompt.
        
        Returns:
            True if conversation has history, False otherwise
        """
        return len(self.conversation_history) > 1 