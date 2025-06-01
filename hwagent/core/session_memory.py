"""
Session Memory System for HWAgent
Handles conversation memory within a single session only - no persistence between page reloads.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass


@dataclass
class ConversationEntry:
    """Single conversation entry with metadata"""
    timestamp: str
    user_query: str
    agent_response: str
    tools_used: List[str]
    task_type: str
    success: bool = True
    error_message: Optional[str] = None


class SessionMemory:
    """Manages conversation memory within a single session only"""
    
    def __init__(self):
        """Initialize session memory system"""
        self.session_id = self._generate_session_id()
        self.conversations: List[ConversationEntry] = []
        self.session_start_time = datetime.now()
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        return str(uuid.uuid4())[:8]
    
    def add_conversation_entry(self, user_query: str, agent_response: str, 
                             tools_used: List[str], task_type: str = "general",
                             success: bool = True, error_message: Optional[str] = None) -> None:
        """Add new conversation entry"""
        entry = ConversationEntry(
            timestamp=datetime.now().isoformat(),
            user_query=user_query,
            agent_response=agent_response,
            tools_used=tools_used,
            task_type=task_type,
            success=success,
            error_message=error_message
        )
        
        self.conversations.append(entry)
    
    def get_recent_conversations(self, limit: int = 10) -> List[ConversationEntry]:
        """Get recent conversation entries"""
        return self.conversations[-limit:] if self.conversations else []
    
    def get_conversations_by_task_type(self, task_type: str, limit: int = 5) -> List[ConversationEntry]:
        """Get recent conversations of specific task type"""
        matching = [entry for entry in self.conversations 
                   if entry.task_type == task_type]
        return matching[-limit:] if matching else []
    
    def get_context_summary(self) -> Dict[str, Any]:
        """Get summary of current session context"""
        if not self.conversations:
            return {
                "session_id": self.session_id,
                "total_exchanges": 0,
                "task_types": [],
                "tools_used": [],
                "success_rate": 0.0,
                "recent_patterns": [],
                "summary": "No conversation entries found.",
                "entry_count": 0,
                "session_duration": "0 minutes",
                "recent_tool_usage": [],
                "key_topics": [],
                "conversation_flow": []
            }
        
        # Basic statistics
        task_types = list(set(entry.task_type for entry in self.conversations))
        tools_used = list(set(tool for entry in self.conversations 
                             for tool in entry.tools_used))
        successful = sum(1 for entry in self.conversations if entry.success)
        success_rate = successful / len(self.conversations) if self.conversations else 0
        
        # Recent patterns analysis
        recent_patterns = self._analyze_recent_patterns()
        
        # Session duration calculation
        duration_minutes = int((datetime.now() - self.session_start_time).total_seconds() / 60)
        session_duration = f"{duration_minutes} minutes" if duration_minutes > 0 else "< 1 minute"
        
        # Recent tool usage (last 10 tools used across all entries)
        recent_tool_usage = []
        for entry in reversed(self.conversations):
            for tool in reversed(entry.tools_used):
                if tool not in recent_tool_usage:
                    recent_tool_usage.append(tool)
                if len(recent_tool_usage) >= 10:
                    break
            if len(recent_tool_usage) >= 10:
                break
        
        # Extract key topics from user queries
        key_topics = self._extract_key_topics()
        
        # Conversation flow analysis
        conversation_flow = self._analyze_conversation_flow()
        
        # Generate intelligent summary
        summary = self._generate_session_summary()
        
        return {
            "session_id": self.session_id,
            "total_exchanges": len(self.conversations),
            "task_types": task_types,
            "tools_used": tools_used,
            "success_rate": success_rate,
            "recent_patterns": recent_patterns,
            "summary": summary,
            "entry_count": len(self.conversations),
            "session_duration": session_duration,
            "recent_tool_usage": recent_tool_usage,
            "key_topics": key_topics,
            "conversation_flow": conversation_flow
        }
    
    def _extract_key_topics(self) -> List[str]:
        """Extract key topics from conversation queries"""
        if not self.conversations:
            return []
        
        # Simple keyword extraction from user queries
        topics = []
        common_words = {'что', 'как', 'где', 'когда', 'почему', 'какой', 'которая', 'который', 
                       'what', 'how', 'where', 'when', 'why', 'which', 'that', 'this', 'the', 
                       'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
                       'мне', 'меня', 'я', 'мой', 'моя', 'моё', 'you', 'your', 'my', 'mine', 'i', 'me'}
        
        for entry in self.conversations[-10:]:  # Last 10 entries
            words = entry.user_query.lower().split()
            meaningful_words = [word.strip('.,!?:;()[]{}') for word in words 
                              if len(word) > 3 and word.lower() not in common_words]
            topics.extend(meaningful_words[:3])  # Take first 3 meaningful words
        
        # Count frequency and return most common
        from collections import Counter
        topic_counts = Counter(topics)
        return [topic for topic, _ in topic_counts.most_common(8)]
    
    def _analyze_conversation_flow(self) -> List[str]:
        """Analyze conversation flow patterns"""
        if not self.conversations:
            return []
        
        patterns = []
        
        # Analyze task type progression
        if len(self.conversations) >= 2:
            task_sequence = [entry.task_type for entry in self.conversations[-5:]]
            if len(set(task_sequence)) == 1:
                patterns.append(f"Focused on {task_sequence[0]} tasks")
            else:
                patterns.append(f"Mixed tasks: {' → '.join(set(task_sequence))}")
        
        # Analyze tool usage patterns
        recent_tools = []
        for entry in self.conversations[-3:]:
            recent_tools.extend(entry.tools_used)
        
        if recent_tools:
            if len(set(recent_tools)) <= 2:
                patterns.append(f"Consistent tool usage: {', '.join(set(recent_tools))}")
            else:
                patterns.append(f"Diverse tool usage: {len(set(recent_tools))} different tools")
        
        # Analyze success patterns
        recent_success = [entry.success for entry in self.conversations[-5:]]
        if all(recent_success):
            patterns.append("All recent tasks successful")
        elif not any(recent_success):
            patterns.append("Recent tasks encountering issues")
        else:
            patterns.append("Mixed success rate in recent tasks")
        
        return patterns[:4]  # Return top 4 patterns
    
    def _generate_session_summary(self) -> str:
        """Generate intelligent session summary"""
        if not self.conversations:
            return "New session - no conversation history yet."
        
        total = len(self.conversations)
        task_types = list(set(entry.task_type for entry in self.conversations))
        tools_used = list(set(tool for entry in self.conversations 
                             for tool in entry.tools_used))
        success_rate = sum(1 for entry in self.conversations if entry.success) / total
        
        # Build summary
        summary_parts = []
        
        # Session overview
        if total == 1:
            summary_parts.append("Started new conversation session.")
        else:
            summary_parts.append(f"Session with {total} exchanges.")
        
        # Task diversity
        if len(task_types) == 1:
            summary_parts.append(f"Focused on {task_types[0]} tasks.")
        else:
            summary_parts.append(f"Working on {len(task_types)} types of tasks: {', '.join(task_types)}.")
        
        # Tool usage
        if tools_used:
            if len(tools_used) <= 3:
                summary_parts.append(f"Primary tools: {', '.join(tools_used)}.")
            else:
                summary_parts.append(f"Using {len(tools_used)} different tools extensively.")
        
        # Success rate
        if success_rate >= 0.9:
            summary_parts.append("High success rate.")
        elif success_rate >= 0.7:
            summary_parts.append("Good progress with some challenges.")
        else:
            summary_parts.append("Encountering difficulties, may need different approach.")
        
        return " ".join(summary_parts)
    
    def _analyze_recent_patterns(self) -> List[str]:
        """Analyze recent conversation patterns"""
        patterns = []
        
        if len(self.conversations) < 2:
            return patterns
        
        recent_entries = self.conversations[-5:]  # Last 5 entries
        
        # Check for repeated task types
        task_types = [entry.task_type for entry in recent_entries]
        task_counts = {}
        for task in task_types:
            task_counts[task] = task_counts.get(task, 0) + 1
        
        dominant_task = max(task_counts.items(), key=lambda x: x[1])
        if dominant_task[1] >= 3:
            patterns.append(f"Recent focus on {dominant_task[0]} tasks")
        
        # Check tool usage patterns
        all_tools = []
        for entry in recent_entries:
            all_tools.extend(entry.tools_used)
        
        if all_tools:
            tool_counts = {}
            for tool in all_tools:
                tool_counts[tool] = tool_counts.get(tool, 0) + 1
            
            frequently_used = [tool for tool, count in tool_counts.items() if count >= 2]
            if frequently_used:
                patterns.append(f"Frequently using: {', '.join(frequently_used)}")
        
        # Check for error trends
        errors = [entry for entry in recent_entries if not entry.success]
        if len(errors) >= 2:
            patterns.append("Recent error pattern detected")
        
        return patterns[:3]  # Return top 3 patterns
    
    def reset_session(self) -> None:
        """Reset session (equivalent to page reload)"""
        self.session_id = self._generate_session_id()
        self.conversations = []
        self.session_start_time = datetime.now()


# Global session memory instance
_session_memory: Optional[SessionMemory] = None


def get_session_memory() -> SessionMemory:
    """Get global session memory instance"""
    global _session_memory
    if _session_memory is None:
        _session_memory = SessionMemory()
    return _session_memory


def reset_session_memory() -> None:
    """Reset session memory (equivalent to page reload)"""
    global _session_memory
    if _session_memory is not None:
        _session_memory.reset_session()
    else:
        _session_memory = SessionMemory() 