"""
Persistent Memory System for HWAgent
Handles long-term conversation memory and context persistence across sessions.
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict

from hwagent.core.constants import Constants


@dataclass
class ConversationEntry:
    """Single conversation entry with metadata"""
    timestamp: str
    user_query: str
    agent_response: str
    tools_used: List[str]
    task_type: str
    session_id: str
    success: bool = True
    error_message: Optional[str] = None


@dataclass
class SessionSummary:
    """Summary of conversation session"""
    session_id: str
    start_time: str
    end_time: str
    total_exchanges: int
    task_types: List[str]
    tools_used: List[str]
    success_rate: float


class PersistentMemory:
    """Manages persistent conversation memory and context"""
    
    def __init__(self, memory_dir: str = "conversation_memory"):
        """Initialize persistent memory system"""
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(exist_ok=True)
        
        self.session_id = self._generate_session_id()
        self.current_session_file = self.memory_dir / "current_session.json"
        self.sessions_file = self.memory_dir / "sessions.json"
        
        # Load existing conversations
        self.current_session = self._load_current_session()
        self.sessions = self._load_sessions()
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def _load_current_session(self) -> list[ConversationEntry]:
        """Load current session conversations"""
        try:
            if self.current_session_file.exists():
                with open(self.current_session_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    conversations = []
                    
                    # Handle different data formats
                    if isinstance(data, list):
                        # Old format: direct list of conversation entries
                        entries_data = data
                    elif isinstance(data, dict) and 'conversations' in data:
                        # New format: dict with conversations key
                        entries_data = data['conversations']
                    elif isinstance(data, dict) and 'entries' in data:
                        # Alternative format: dict with entries key
                        entries_data = data['entries']
                    else:
                        # Unknown format, try to extract entries
                        entries_data = []
                    
                    for entry_data in entries_data:
                        # Handle backward compatibility - add session_id if missing
                        if isinstance(entry_data, dict):
                            if 'session_id' not in entry_data:
                                entry_data['session_id'] = self.session_id
                            conversations.append(ConversationEntry(**entry_data))
                    
                    return conversations
        except Exception as e:
            print(f"Warning: Could not load current session: {e}")
        return []
    
    def _load_sessions(self) -> list:
        """Load sessions index"""
        try:
            if self.sessions_file.exists():
                with open(self.sessions_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load sessions index: {e}")
        return []
    
    def _save_current_session(self) -> None:
        """Save current session to disk"""
        try:
            with open(self.current_session_file, 'w', encoding='utf-8') as f:
                json.dump([asdict(entry) for entry in self.current_session], f, 
                         indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Could not save current session: {e}")
    
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
            session_id=self.session_id,
            success=success,
            error_message=error_message
        )
        
        self.current_session.append(entry)
        self._save_current_session()
    
    def get_recent_conversations(self, limit: int = 10) -> List[ConversationEntry]:
        """Get recent conversation entries"""
        return self.current_session[-limit:] if self.current_session else []
    
    def get_conversations_by_task_type(self, task_type: str, limit: int = 5) -> List[ConversationEntry]:
        """Get recent conversations of specific task type"""
        matching = [entry for entry in self.current_session 
                   if entry.task_type == task_type]
        return matching[-limit:] if matching else []
    
    def get_context_summary(self) -> Dict[str, Any]:
        """Get summary of current session context"""
        if not self.current_session:
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
        task_types = list(set(entry.task_type for entry in self.current_session))
        tools_used = list(set(tool for entry in self.current_session 
                             for tool in entry.tools_used))
        successful = sum(1 for entry in self.current_session if entry.success)
        success_rate = successful / len(self.current_session) if self.current_session else 0
        
        # Recent patterns analysis
        recent_patterns = self._analyze_recent_patterns()
        
        # Session duration calculation
        start_time = datetime.fromisoformat(self.current_session[0].timestamp)
        end_time = datetime.fromisoformat(self.current_session[-1].timestamp)
        duration_minutes = int((end_time - start_time).total_seconds() / 60)
        session_duration = f"{duration_minutes} minutes" if duration_minutes > 0 else "< 1 minute"
        
        # Recent tool usage (last 10 tools used across all entries)
        recent_tool_usage = []
        for entry in reversed(self.current_session):
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
            "total_exchanges": len(self.current_session),
            "task_types": task_types,
            "tools_used": tools_used,
            "success_rate": success_rate,
            "recent_patterns": recent_patterns,
            "summary": summary,
            "entry_count": len(self.current_session),
            "session_duration": session_duration,
            "recent_tool_usage": recent_tool_usage,
            "key_topics": key_topics,
            "conversation_flow": conversation_flow
        }
    
    def _extract_key_topics(self) -> List[str]:
        """Extract key topics from user queries in current session"""
        topics = []
        
        # Common topic keywords
        topic_keywords = {
            "mathematics": ["math", "calculate", "equation", "integral", "derivative", "matrix", "математика", "уравнение", "вычисли"],
            "programming": ["code", "program", "python", "javascript", "algorithm", "код", "программа", "алгоритм"],
            "physics": ["physics", "force", "energy", "velocity", "физика", "сила", "энергия"],
            "data_analysis": ["data", "chart", "graph", "analyze", "statistics", "данные", "анализ", "график"],
            "documents": ["document", "pdf", "latex", "report", "документ", "отчет"],
            "homework": ["homework", "assignment", "exercise", "домашнее", "задание", "упражнение"],
            "research": ["research", "study", "investigate", "исследование", "изучение"]
        }
        
        # Count occurrences of topic keywords
        topic_counts = {}
        for entry in self.current_session:
            query_lower = entry.user_query.lower()
            for topic, keywords in topic_keywords.items():
                count = sum(1 for keyword in keywords if keyword in query_lower)
                if count > 0:
                    topic_counts[topic] = topic_counts.get(topic, 0) + count
        
        # Return top topics
        sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
        topics = [topic for topic, count in sorted_topics[:5]]  # Top 5 topics
        
        return topics
    
    def _analyze_conversation_flow(self) -> List[str]:
        """Analyze the flow and progression of conversation"""
        if len(self.current_session) < 2:
            return []
        
        flow_patterns = []
        
        # Check for task progression
        task_sequence = [entry.task_type for entry in self.current_session]
        if len(set(task_sequence)) > 1:
            flow_patterns.append(f"Task progression: {' → '.join(task_sequence[-3:])}")
        
        # Check for tool evolution
        tool_usage_by_entry = [entry.tools_used for entry in self.current_session if entry.tools_used]
        if len(tool_usage_by_entry) > 1:
            recent_tools = []
            for tools in tool_usage_by_entry[-3:]:  # Last 3 entries with tools
                recent_tools.extend(tools)
            unique_recent = list(dict.fromkeys(recent_tools))  # Preserve order, remove duplicates
            if len(unique_recent) > 1:
                flow_patterns.append(f"Tool evolution: {' → '.join(unique_recent[-3:])}")
        
        # Check for complexity progression
        query_lengths = [len(entry.user_query.split()) for entry in self.current_session]
        if len(query_lengths) >= 3:
            recent_lengths = query_lengths[-3:]
            if recent_lengths[-1] > recent_lengths[0] * 1.5:
                flow_patterns.append("Increasing query complexity")
            elif recent_lengths[-1] < recent_lengths[0] * 0.7:
                flow_patterns.append("Simplifying query pattern")
        
        return flow_patterns
    
    def _generate_session_summary(self) -> str:
        """Generate intelligent summary of current session"""
        if not self.current_session:
            return "No conversation entries found."
        
        entry_count = len(self.current_session)
        successful_count = sum(1 for entry in self.current_session if entry.success)
        
        # Determine primary task type
        task_types = [entry.task_type for entry in self.current_session]
        primary_task = max(set(task_types), key=task_types.count) if task_types else "general"
        
        # Determine primary tools
        all_tools = [tool for entry in self.current_session for tool in entry.tools_used]
        tool_counts = {}
        for tool in all_tools:
            tool_counts[tool] = tool_counts.get(tool, 0) + 1
        primary_tools = sorted(tool_counts.items(), key=lambda x: x[1], reverse=True)[:2]
        
        # Build summary
        summary_parts = [
            f"{entry_count} exchanges",
            f"{successful_count}/{entry_count} successful"
        ]
        
        if primary_task != "general":
            summary_parts.append(f"primarily {primary_task}")
        
        if primary_tools:
            top_tool = primary_tools[0][0]
            summary_parts.append(f"using {top_tool}")
            if len(primary_tools) > 1:
                summary_parts.append(f"and {primary_tools[1][0]}")
        
        return f"Session with {', '.join(summary_parts)}"
    
    def _analyze_recent_patterns(self) -> List[str]:
        """Analyze patterns in recent conversations"""
        patterns = []
        
        if len(self.current_session) < 2:
            return patterns
        
        recent = self.current_session[-5:]  # Last 5 entries
        
        # Check for repeated task types
        task_types = [entry.task_type for entry in recent]
        most_common_task = max(set(task_types), key=task_types.count) if task_types else None
        if most_common_task and task_types.count(most_common_task) > 2:
            patterns.append(f"Frequent {most_common_task} tasks")
        
        # Check for tool usage patterns
        all_tools = [tool for entry in recent for tool in entry.tools_used]
        if all_tools:
            most_used_tool = max(set(all_tools), key=all_tools.count)
            if all_tools.count(most_used_tool) > 2:
                patterns.append(f"Heavy use of {most_used_tool}")
        
        # Check for error patterns
        recent_errors = [entry for entry in recent if not entry.success]
        if len(recent_errors) > 1:
            patterns.append("Recent error trend detected")
        
        return patterns
    
    def archive_current_session(self) -> bool:
        """Archive current session and start new one"""
        if not self.current_session:
            return True
        
        try:
            # Create session summary
            summary = self._create_session_summary()
            
            # Save to archive
            archive_file = self.memory_dir / f"session_{self.session_id}.json"
            with open(archive_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "summary": asdict(summary),
                    "conversations": [asdict(entry) for entry in self.current_session]
                }, f, indent=2, ensure_ascii=False)
            
            # Update sessions index
            self._update_sessions_index(summary)
            
            # Clear current session
            self.current_session = []
            self.session_id = self._generate_session_id()
            
            # Remove current session file
            if self.current_session_file.exists():
                self.current_session_file.unlink()
            
            return True
            
        except Exception as e:
            print(f"Error archiving session: {e}")
            return False
    
    def _create_session_summary(self) -> SessionSummary:
        """Create summary of current session"""
        if not self.current_session:
            return SessionSummary(
                session_id=self.session_id,
                start_time=datetime.now().isoformat(),
                end_time=datetime.now().isoformat(),
                total_exchanges=0,
                task_types=[],
                tools_used=[],
                success_rate=0.0
            )
        
        start_time = self.current_session[0].timestamp
        end_time = self.current_session[-1].timestamp
        task_types = list(set(entry.task_type for entry in self.current_session))
        tools_used = list(set(tool for entry in self.current_session 
                             for tool in entry.tools_used))
        successful = sum(1 for entry in self.current_session if entry.success)
        success_rate = successful / len(self.current_session)
        
        return SessionSummary(
            session_id=self.session_id,
            start_time=start_time,
            end_time=end_time,
            total_exchanges=len(self.current_session),
            task_types=task_types,
            tools_used=tools_used,
            success_rate=success_rate
        )
    
    def _update_sessions_index(self, summary: SessionSummary) -> None:
        """Update sessions index with new summary"""
        try:
            # Load existing index
            index = []
            if self.sessions_file.exists():
                with open(self.sessions_file, 'r', encoding='utf-8') as f:
                    index = json.load(f)
            
            # Add new summary
            index.append(asdict(summary))
            
            # Keep only last 50 sessions in index
            index = index[-50:]
            
            # Save updated index
            with open(self.sessions_file, 'w', encoding='utf-8') as f:
                json.dump(index, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Error updating sessions index: {e}")
    
    def get_historical_context(self, days: int = 7) -> Dict[str, Any]:
        """Get historical context from previous sessions"""
        try:
            if not self.sessions_file.exists():
                return {"total_sessions": 0, "patterns": [], "frequent_tasks": []}
            
            with open(self.sessions_file, 'r', encoding='utf-8') as f:
                sessions = json.load(f)
            
            # Filter sessions from last N days
            cutoff_date = datetime.now() - timedelta(days=days)
            recent_sessions = [
                session for session in sessions
                if datetime.fromisoformat(session['end_time']) > cutoff_date
            ]
            
            if not recent_sessions:
                return {"total_sessions": 0, "patterns": [], "frequent_tasks": []}
            
            # Analyze patterns
            all_task_types = []
            all_tools = []
            total_exchanges = 0
            
            for session in recent_sessions:
                all_task_types.extend(session.get('task_types', []))
                all_tools.extend(session.get('tools_used', []))
                total_exchanges += session.get('total_exchanges', 0)
            
            # Find frequent task types
            frequent_tasks = []
            if all_task_types:
                task_counts = {}
                for task in all_task_types:
                    task_counts[task] = task_counts.get(task, 0) + 1
                frequent_tasks = sorted(task_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            
            return {
                "total_sessions": len(recent_sessions),
                "total_exchanges": total_exchanges,
                "frequent_tasks": frequent_tasks,
                "patterns": [f"{count} {task} sessions" for task, count in frequent_tasks]
            }
            
        except Exception as e:
            print(f"Error getting historical context: {e}")
            return {"total_sessions": 0, "patterns": [], "frequent_tasks": []}
    
    def cleanup_old_archives(self, days: int = 30) -> int:
        """Clean up archive files older than specified days"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            deleted_count = 0
            
            for archive_file in self.memory_dir.glob("session_*.json"):
                try:
                    # Extract timestamp from filename
                    timestamp_str = archive_file.stem.replace("session_", "")
                    file_date = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    
                    if file_date < cutoff_date:
                        archive_file.unlink()
                        deleted_count += 1
                        
                except (ValueError, OSError):
                    continue  # Skip files with invalid names or permission issues
            
            return deleted_count
            
        except Exception as e:
            print(f"Error cleaning up archives: {e}")
            return 0


# Global instance
_persistent_memory: Optional[PersistentMemory] = None


def get_persistent_memory() -> PersistentMemory:
    """Get global persistent memory instance"""
    global _persistent_memory
    if _persistent_memory is None:
        _persistent_memory = PersistentMemory()
    return _persistent_memory


def reset_persistent_memory() -> None:
    """Reset global persistent memory instance"""
    global _persistent_memory
    _persistent_memory = None 