"""
Conversation Manager for handling conversation history with persistent memory integration.
Following Single Responsibility Principle - handles only conversation state.
"""

from typing import Any, Dict, List, Optional
from hwagent.core.models import ConversationMessage
from hwagent.core.message_manager import MessageManager

# Import persistent memory only when available
try:
    from hwagent.core.persistent_memory import get_persistent_memory, PersistentMemory
    PERSISTENT_MEMORY_AVAILABLE = True
except ImportError:
    PERSISTENT_MEMORY_AVAILABLE = False


class ConversationManager:
    """Base conversation manager interface"""
    
    def __init__(self, message_manager: MessageManager):
        """
        Initialize ConversationManager.
        
        Args:
            message_manager: Message manager for display messages
        """
        self.message_manager = message_manager
        self.conversation_history: List[Dict[str, Any]] = []
    
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


class ConversationManagerImpl(ConversationManager):
    """Enhanced conversation manager with persistent memory integration"""
    
    def __init__(self, message_manager: MessageManager, enable_persistence: bool = True):
        """
        Initialize enhanced conversation manager.
        
        Args:
            message_manager: Message manager for display messages
            enable_persistence: Whether to enable persistent memory features
        """
        super().__init__(message_manager)
        self.enable_persistence = enable_persistence and PERSISTENT_MEMORY_AVAILABLE
        self.persistent_memory: Optional[PersistentMemory] = None
        self.current_user_query: Optional[str] = None
        self.current_tools_used: List[str] = []
        
        if self.enable_persistence:
            try:
                self.persistent_memory = get_persistent_memory()
            except Exception as e:
                print(f"Warning: Could not initialize persistent memory: {e}")
                self.enable_persistence = False
    
    def add_user_message(self, content: str) -> None:
        """Add user message and track for persistence"""
        super().add_user_message(content)
        
        # Store current query for later persistence
        if self.enable_persistence:
            self.current_user_query = content
            self.current_tools_used = []  # Reset tools used for new query
    
    def add_tool_result(self, tool_call_id: str, tool_name: str, content: str) -> None:
        """Add tool result and track tool usage"""
        super().add_tool_result(tool_call_id, tool_name, content)
        
        # Track tool usage for persistence
        if self.enable_persistence and tool_name not in self.current_tools_used:
            self.current_tools_used.append(tool_name)
    
    def complete_conversation_turn(self, agent_response: str, task_type: str = "general", 
                                  success: bool = True, error_message: Optional[str] = None) -> None:
        """Complete a conversation turn and persist to memory"""
        if not self.enable_persistence or not self.persistent_memory or not self.current_user_query:
            return
        
        try:
            self.persistent_memory.add_conversation_entry(
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
            print(f"Warning: Could not persist conversation turn: {e}")
    
    def get_enhanced_context_summary(self) -> Dict[str, Any]:
        """Get enhanced context summary including persistent memory insights"""
        basic_summary = self.get_context_summary()
        
        if not self.enable_persistence or not self.persistent_memory:
            return {
                "current_session": basic_summary,
                "persistent_memory_available": False
            }
        
        try:
            # Get persistent memory context
            session_context = self.persistent_memory.get_context_summary()
            historical_context = self.persistent_memory.get_historical_context(days=7)
            
            return {
                "current_session": basic_summary,
                "persistent_memory_available": True,
                "session_context": session_context,
                "historical_context": historical_context,
                "context_insights": self._generate_context_insights(session_context, historical_context)
            }
            
        except Exception as e:
            print(f"Warning: Could not get enhanced context: {e}")
            return {
                "current_session": basic_summary,
                "persistent_memory_available": False,
                "error": str(e)
            }
    
    def _generate_context_insights(self, session_context: Dict[str, Any], 
                                  historical_context: Dict[str, Any]) -> List[str]:
        """Generate insights from conversation context"""
        insights = []
        
        # Session insights
        if session_context.get("total_exchanges", 0) > 5:
            insights.append(f"Active session with {session_context['total_exchanges']} exchanges")
        
        success_rate = session_context.get("success_rate", 0)
        if success_rate < 0.8 and session_context.get("total_exchanges", 0) > 2:
            insights.append(f"Low success rate ({success_rate:.1%}) - may need different approach")
        
        # Pattern insights
        patterns = session_context.get("recent_patterns", [])
        if patterns:
            insights.append(f"Recent patterns: {', '.join(patterns)}")
        
        # Historical insights
        if historical_context.get("total_sessions", 0) > 0:
            frequent_tasks = historical_context.get("frequent_tasks", [])
            if frequent_tasks:
                top_task = frequent_tasks[0]
                insights.append(f"Frequently works on {top_task[1]} tasks ({top_task[0]} recent sessions)")
        
        return insights
    
    def get_recent_similar_conversations(self, task_type: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Get recent conversations of similar task type for context"""
        if not self.enable_persistence or not self.persistent_memory:
            return []
        
        try:
            recent_conversations = self.persistent_memory.get_conversations_by_task_type(task_type, limit)
            return [
                {
                    "timestamp": conv.timestamp,
                    "user_query": conv.user_query[:200] + "..." if len(conv.user_query) > 200 else conv.user_query,
                    "tools_used": conv.tools_used,
                    "success": conv.success
                }
                for conv in recent_conversations
            ]
        except Exception as e:
            print(f"Warning: Could not get similar conversations: {e}")
            return []
    
    def archive_session(self) -> bool:
        """Archive current session and start fresh"""
        if not self.enable_persistence or not self.persistent_memory:
            return False
        
        try:
            return self.persistent_memory.archive_current_session()
        except Exception as e:
            print(f"Warning: Could not archive session: {e}")
            return False
    
    def get_memory_status(self) -> Dict[str, Any]:
        """Get status of persistent memory system"""
        if not self.enable_persistence:
            return {"enabled": False, "reason": "Persistent memory not available"}
        
        if not self.persistent_memory:
            return {"enabled": False, "reason": "Persistent memory not initialized"}
        
        try:
            context = self.persistent_memory.get_context_summary()
            historical = self.persistent_memory.get_historical_context()
            
            return {
                "enabled": True,
                "session_id": context.get("session_id"),
                "session_exchanges": context.get("total_exchanges", 0),
                "recent_sessions": historical.get("total_sessions", 0),
                "success_rate": context.get("success_rate", 0)
            }
        except Exception as e:
            return {"enabled": False, "error": str(e)}


# Backward compatibility alias
ConversationManagerImpl = ConversationManagerImpl 