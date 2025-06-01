"""
Session-based Conversation Manager for handling conversation history with session memory.
Memory is kept only for the current session and is lost on page reload.
"""

from typing import Any, Dict, List, Optional
from hwagent.core.models import ConversationMessage
from hwagent.core.message_manager import MessageManager
from hwagent.core.session_memory import get_session_memory, SessionMemory


class SessionConversationManager:
    """Session-based conversation manager with in-memory persistence only"""
    
    def __init__(self, message_manager: MessageManager, enable_memory: bool = True):
        """
        Initialize session conversation manager.
        
        Args:
            message_manager: Message manager for display messages
            enable_memory: Whether to enable session memory features
        """
        self.message_manager = message_manager
        self.conversation_history: List[Dict[str, Any]] = []
        self.enable_memory = enable_memory
        self.session_memory: Optional[SessionMemory] = None
        self.current_user_query: Optional[str] = None
        self.current_tools_used: List[str] = []
        
        if self.enable_memory:
            try:
                self.session_memory = get_session_memory()
            except Exception as e:
                print(f"Warning: Could not initialize session memory: {e}")
                self.enable_memory = False
    
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
        Add user message to conversation history and track for memory.
        
        Args:
            content: User message content
        """
        self.conversation_history.append({"role": "user", "content": content})
        
        # Store current query for later memory persistence
        if self.enable_memory:
            self.current_user_query = content
            self.current_tools_used = []  # Reset tools used for new query
    
    def add_assistant_message(self, message_obj: Any) -> None:
        """
        Add assistant message to conversation history.
        
        Args:
            message_obj: Assistant message object from OpenAI API
        """
        self.conversation_history.append(message_obj.model_dump(exclude_none=True))
    
    def add_tool_result(self, tool_call_id: str, tool_name: str, content: str) -> None:
        """
        Add tool execution result to conversation history and track tool usage.
        
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
        
        # Track tool usage for memory
        if self.enable_memory and tool_name not in self.current_tools_used:
            self.current_tools_used.append(tool_name)
    
    def add_system_note(self, content: str) -> None:
        """
        Add system note to conversation history.
        
        Args:
            content: System note content
        """
        self.conversation_history.append({"role": "assistant", "content": content})
    
    def complete_conversation_turn(self, agent_response: str, task_type: str = "general", 
                                  success: bool = True, error_message: Optional[str] = None) -> None:
        """Complete a conversation turn and store in session memory"""
        if not self.enable_memory or not self.session_memory or not self.current_user_query:
            return
        
        try:
            self.session_memory.add_conversation_entry(
                user_query=self.current_user_query,
                agent_response=agent_response,
                tools_used=self.current_tools_used.copy(),
                task_type=task_type,
                success=success,
                error_message=error_message
            )
            
            # Reset current tracking
            self.current_user_query = None
            self.current_tools_used = []
            
        except Exception as e:
            print(f"Warning: Could not store conversation turn in session memory: {e}")
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
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
        
        # Also reset session memory
        if self.enable_memory and self.session_memory:
            self.session_memory.reset_session()
    
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
    
    def get_session_conversation_summary(self, max_entries: int = 5) -> str:
        """Get a brief summary of session conversation for memory context"""
        if not self.enable_memory or not self.session_memory:
            return "Session memory not available."
        
        try:
            context = self.session_memory.get_context_summary()
            
            if context["total_exchanges"] == 0:
                return "New session - no conversation history yet."
            
            # Format session summary
            summary_lines = [
                f"📊 Session Summary (ID: {context['session_id']}):",
                f"• Total exchanges: {context['total_exchanges']}",
                f"• Session duration: {context['session_duration']}",
                f"• Success rate: {context['success_rate']:.1%}"
            ]
            
            if context["task_types"]:
                summary_lines.append(f"• Task types: {', '.join(context['task_types'])}")
            
            if context["recent_tool_usage"]:
                tools_str = ', '.join(context['recent_tool_usage'][:5])
                summary_lines.append(f"• Recent tools: {tools_str}")
            
            if context["key_topics"]:
                topics_str = ', '.join(context['key_topics'][:4])
                summary_lines.append(f"• Key topics: {topics_str}")
            
            if context["conversation_flow"]:
                summary_lines.append(f"• Flow patterns: {'; '.join(context['conversation_flow'][:2])}")
            
            # Add overall summary
            summary_lines.append(f"• Summary: {context['summary']}")
            
            return "\n".join(summary_lines)
            
        except Exception as e:
            return f"Error getting session conversation summary: {str(e)}"
    
    def get_recent_similar_conversations(self, task_type: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Get recent conversations of similar task type from session memory"""
        if not self.enable_memory or not self.session_memory:
            return []
        
        try:
            similar_entries = self.session_memory.get_conversations_by_task_type(task_type, limit)
            return [
                {
                    "user_query": entry.user_query,
                    "agent_response": entry.agent_response[:200] + "..." if len(entry.agent_response) > 200 else entry.agent_response,
                    "tools_used": entry.tools_used,
                    "timestamp": entry.timestamp,
                    "success": entry.success
                }
                for entry in similar_entries
            ]
        except Exception as e:
            print(f"Warning: Could not retrieve similar conversations: {e}")
            return []
    
    def get_memory_status(self) -> Dict[str, Any]:
        """Get session memory status information"""
        if not self.enable_memory or not self.session_memory:
            return {
                "enabled": False,
                "reason": "Session memory not available",
                "session_id": None,
                "total_entries": 0
            }
        
        try:
            context = self.session_memory.get_context_summary()
            return {
                "enabled": True,
                "session_id": context["session_id"],
                "total_entries": context["total_exchanges"],
                "session_duration": context["session_duration"],
                "success_rate": context["success_rate"],
                "memory_type": "session_only"
            }
        except Exception as e:
            return {
                "enabled": False,
                "reason": f"Error accessing session memory: {str(e)}",
                "session_id": None,
                "total_entries": 0
            }
    
    def get_conversation_context_for_prompt(self) -> str:
        """Get conversation context for inclusion in system prompt"""
        if not self.enable_memory or not self.session_memory:
            return ""
        
        try:
            context = self.session_memory.get_context_summary()
            
            if context["total_exchanges"] == 0:
                return ""
            
            # Build context string for prompt
            context_parts = [
                f"📋 SESSION CONTEXT (Session: {context['session_id']}):",
                f"Current session has {context['total_exchanges']} exchanges over {context['session_duration']}."
            ]
            
            if context["task_types"]:
                context_parts.append(f"Recent task types: {', '.join(context['task_types'])}.")
            
            if context["recent_tool_usage"]:
                context_parts.append(f"Recently used tools: {', '.join(context['recent_tool_usage'][:5])}.")
            
            if context["key_topics"]:
                context_parts.append(f"Key topics discussed: {', '.join(context['key_topics'][:4])}.")
            
            if context["conversation_flow"]:
                context_parts.append(f"Conversation patterns: {'; '.join(context['conversation_flow'][:2])}.")
            
            context_parts.append(f"Session summary: {context['summary']}")
            
            # Add recent patterns if any
            if context["recent_patterns"]:
                context_parts.append(f"Recent patterns: {'; '.join(context['recent_patterns'])}.")
            
            return "\n".join(context_parts)
            
        except Exception as e:
            return f"Note: Session context unavailable ({str(e)})" 