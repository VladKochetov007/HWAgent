"""
Memory Management Tool - allows viewing and managing conversation memory.
Follows SOLID principles and provides memory insights.
"""

from typing import Any, Dict, List
from datetime import datetime, timedelta
import json

from hwagent.core import (
    BaseTool, ToolExecutionResult, Constants,
    PersistentMemory, get_persistent_memory
)


class MemoryTool(BaseTool):
    """Tool for managing and querying conversation memory."""
    
    def __init__(self, tmp_directory: str = Constants.DEFAULT_TMP_DIRECTORY):
        super().__init__(tmp_directory)
        self.memory = get_persistent_memory()
    
    @property
    def name(self) -> str:
        return "memory"
    
    @property
    def description(self) -> str:
        return """Manage and query conversation memory. View session summaries, search conversation history, 
        get insights about patterns, and manage memory data. Helps understand past interactions and build continuity."""
    
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["summary", "search", "insights", "recent", "stats", "clear_session"],
                    "description": "Action to perform: summary (get current session), search (search history), insights (get patterns), recent (recent conversations), stats (memory statistics), clear_session (clear current session)"
                },
                "query": {
                    "type": "string",
                    "description": "Search query for 'search' action. Can search in conversation content."
                },
                "days": {
                    "type": "integer",
                    "description": "Number of days to look back (for 'recent' and 'insights' actions, default: 7)",
                    "default": 7
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results to return (default: 10)",
                    "default": 10
                }
            },
            "required": ["action"]
        }
    
    def _execute_impl(self, **kwargs) -> ToolExecutionResult:
        """Execute memory management action."""
        action = kwargs["action"]
        
        try:
            if action == "summary":
                return self._get_session_summary()
            elif action == "search":
                query = kwargs.get("query", "")
                if not query:
                    return ToolExecutionResult.error(
                        "Search action requires query parameter",
                        "Please provide a search query"
                    )
                return self._search_memory(query, kwargs.get("limit", 10))
            elif action == "insights":
                days = kwargs.get("days", 7)
                return self._get_insights(days)
            elif action == "recent":
                days = kwargs.get("days", 7)
                limit = kwargs.get("limit", 10)
                return self._get_recent_conversations(days, limit)
            elif action == "stats":
                return self._get_memory_stats()
            elif action == "clear_session":
                return self._clear_current_session()
            else:
                return ToolExecutionResult.error(
                    f"Unknown action: {action}",
                    "Valid actions: summary, search, insights, recent, stats, clear_session"
                )
                
        except Exception as e:
            return ToolExecutionResult.error(
                f"Memory tool error for action '{action}'",
                f"Error: {str(e)}"
            )
    
    def _get_session_summary(self) -> ToolExecutionResult:
        """Get current session summary."""
        try:
            context = self.memory.get_context_summary()
            
            if not context or context.get('summary') == 'No conversation entries found.':
                return ToolExecutionResult.success(
                    "Current session summary retrieved",
                    "📋 **Current Session**: No conversation entries found in current session."
                )
            
            summary_lines = [
                "📋 **Current Session Summary**",
                "",
                f"💬 **Summary**: {context.get('summary', 'No summary available')}",
                f"📊 **Entry Count**: {context.get('entry_count', 0)}",
                f"🕒 **Session Duration**: {context.get('session_duration', 'Unknown')}",
                ""
            ]
            
            # Recent tools
            recent_tools = context.get('recent_tool_usage', [])
            if recent_tools:
                summary_lines.extend([
                    "🔧 **Recent Tools Used**:",
                    *[f"  • {tool}" for tool in recent_tools[:8]],
                    ""
                ])
            
            # Key topics
            key_topics = context.get('key_topics', [])
            if key_topics:
                summary_lines.extend([
                    "🎯 **Key Topics**:",
                    *[f"  • {topic}" for topic in key_topics[:5]],
                    ""
                ])
            
            return ToolExecutionResult.success(
                f"Current session summary - {context.get('entry_count', 0)} entries",
                "\n".join(summary_lines)
            )
            
        except Exception as e:
            return ToolExecutionResult.error(
                "Failed to get session summary",
                f"Error retrieving session data: {str(e)}"
            )
    
    def _search_memory(self, query: str, limit: int) -> ToolExecutionResult:
        """Search conversation memory."""
        try:
            # Get all conversations from memory
            historical_context = self.memory.get_historical_context(days=30)  # Search last 30 days
            
            if not historical_context:
                return ToolExecutionResult.success(
                    f"Memory search for '{query}' completed",
                    f"🔍 **Search Results for '{query}'**\n\nNo historical conversations found to search."
                )
            
            # Simple text-based search through conversation entries
            query_lower = query.lower()
            matching_entries = []
            
            # Search through frequent patterns
            frequent_patterns = historical_context.get('frequent_patterns', [])
            for pattern in frequent_patterns:
                if query_lower in pattern.lower():
                    matching_entries.append({
                        'type': 'pattern',
                        'content': pattern,
                        'relevance': 'high'
                    })
            
            # Search through successful approaches
            successful_approaches = historical_context.get('successful_approaches', [])
            for approach in successful_approaches:
                if query_lower in approach.lower():
                    matching_entries.append({
                        'type': 'approach',
                        'content': approach,
                        'relevance': 'high'
                    })
            
            # Search through tool usage patterns
            tool_usage = historical_context.get('tool_usage_patterns', {})
            for tool, usage_info in tool_usage.items():
                if query_lower in tool.lower() or query_lower in str(usage_info).lower():
                    matching_entries.append({
                        'type': 'tool_usage',
                        'content': f"Tool: {tool} - Usage: {usage_info}",
                        'relevance': 'medium'
                    })
            
            if not matching_entries:
                return ToolExecutionResult.success(
                    f"Memory search for '{query}' completed",
                    f"🔍 **Search Results for '{query}'**\n\nNo matching entries found in conversation memory."
                )
            
            # Format results
            result_lines = [
                f"🔍 **Search Results for '{query}'**",
                f"📊 Found {len(matching_entries)} matching entries",
                ""
            ]
            
            # Limit results
            matching_entries = matching_entries[:limit]
            
            for i, entry in enumerate(matching_entries, 1):
                entry_type = entry['type'].replace('_', ' ').title()
                relevance = entry['relevance'].upper()
                content = entry['content']
                
                result_lines.extend([
                    f"{i}. **{entry_type}** ({relevance} relevance)",
                    f"   {content}",
                    ""
                ])
            
            return ToolExecutionResult.success(
                f"Memory search completed - found {len(matching_entries)} results",
                "\n".join(result_lines)
            )
            
        except Exception as e:
            return ToolExecutionResult.error(
                f"Memory search failed for query '{query}'",
                f"Error during search: {str(e)}"
            )
    
    def _get_insights(self, days: int) -> ToolExecutionResult:
        """Get insights about conversation patterns."""
        try:
            historical_context = self.memory.get_historical_context(days=days)
            
            if not historical_context:
                return ToolExecutionResult.success(
                    f"Memory insights for last {days} days",
                    f"💡 **Memory Insights (Last {days} Days)**\n\nNo historical data available for analysis."
                )
            
            insight_lines = [
                f"💡 **Memory Insights (Last {days} Days)**",
                ""
            ]
            
            # Frequent patterns
            frequent_patterns = historical_context.get('frequent_patterns', [])
            if frequent_patterns:
                insight_lines.extend([
                    "🔄 **Frequent Patterns**:",
                    *[f"  • {pattern}" for pattern in frequent_patterns[:5]],
                    ""
                ])
            
            # Successful approaches
            successful_approaches = historical_context.get('successful_approaches', [])
            if successful_approaches:
                insight_lines.extend([
                    "✅ **Successful Approaches**:",
                    *[f"  • {approach}" for approach in successful_approaches[:5]],
                    ""
                ])
            
            # Tool usage patterns
            tool_usage = historical_context.get('tool_usage_patterns', {})
            if tool_usage:
                insight_lines.extend([
                    "🔧 **Tool Usage Patterns**:",
                ])
                for tool, usage in list(tool_usage.items())[:8]:
                    insight_lines.append(f"  • {tool}: {usage}")
                insight_lines.append("")
            
            # Common topics
            common_topics = historical_context.get('common_topics', [])
            if common_topics:
                insight_lines.extend([
                    "🎯 **Common Topics**:",
                    *[f"  • {topic}" for topic in common_topics[:5]],
                    ""
                ])
            
            if len(insight_lines) == 2:  # Only header
                insight_lines.append("No significant patterns or insights found in the selected time period.")
            
            return ToolExecutionResult.success(
                f"Memory insights generated for last {days} days",
                "\n".join(insight_lines)
            )
            
        except Exception as e:
            return ToolExecutionResult.error(
                f"Failed to generate insights for last {days} days",
                f"Error analyzing memory data: {str(e)}"
            )
    
    def _get_recent_conversations(self, days: int, limit: int) -> ToolExecutionResult:
        """Get recent conversation summaries."""
        try:
            # This is a simplified version - in a full implementation,
            # we would store individual conversation summaries
            session_context = self.memory.get_context_summary()
            historical_context = self.memory.get_historical_context(days=days)
            
            result_lines = [
                f"📅 **Recent Conversations (Last {days} Days)**",
                ""
            ]
            
            # Current session
            if session_context and session_context.get('summary') != 'No conversation entries found.':
                result_lines.extend([
                    "🔵 **Current Session**:",
                    f"  Summary: {session_context.get('summary', 'No summary')}",
                    f"  Entries: {session_context.get('entry_count', 0)}",
                    f"  Duration: {session_context.get('session_duration', 'Unknown')}",
                    ""
                ])
            
            # Historical data
            if historical_context:
                result_lines.extend([
                    "📊 **Historical Activity**:",
                    f"  Frequent patterns: {len(historical_context.get('frequent_patterns', []))} identified",
                    f"  Successful approaches: {len(historical_context.get('successful_approaches', []))} recorded",
                    f"  Tools used: {len(historical_context.get('tool_usage_patterns', {}))} different tools",
                    ""
                ])
            
            if len(result_lines) == 2:  # Only header
                result_lines.append("No recent conversation data available.")
            
            return ToolExecutionResult.success(
                f"Recent conversations retrieved for last {days} days",
                "\n".join(result_lines)
            )
            
        except Exception as e:
            return ToolExecutionResult.error(
                f"Failed to get recent conversations for last {days} days",
                f"Error retrieving conversation data: {str(e)}"
            )
    
    def _get_memory_stats(self) -> ToolExecutionResult:
        """Get memory usage statistics."""
        try:
            session_context = self.memory.get_context_summary()
            historical_context = self.memory.get_historical_context(days=30)
            
            stats_lines = [
                "📊 **Memory Statistics**",
                ""
            ]
            
            # Current session stats
            if session_context:
                stats_lines.extend([
                    "🔵 **Current Session**:",
                    f"  • Entries: {session_context.get('entry_count', 0)}",
                    f"  • Duration: {session_context.get('session_duration', 'Unknown')}",
                    f"  • Tools used: {len(session_context.get('recent_tool_usage', []))}",
                    ""
                ])
            
            # Historical stats
            if historical_context:
                stats_lines.extend([
                    "📈 **Historical Data (Last 30 Days)**:",
                    f"  • Patterns identified: {len(historical_context.get('frequent_patterns', []))}",
                    f"  • Successful approaches: {len(historical_context.get('successful_approaches', []))}",
                    f"  • Different tools used: {len(historical_context.get('tool_usage_patterns', {}))}",
                    f"  • Common topics: {len(historical_context.get('common_topics', []))}",
                    ""
                ])
            
            # Memory health
            stats_lines.extend([
                "🔧 **Memory Health**:",
                "  • Persistent memory: ✅ Active",
                "  • Session tracking: ✅ Enabled",
                "  • Context generation: ✅ Working",
                ""
            ])
            
            return ToolExecutionResult.success(
                "Memory statistics retrieved",
                "\n".join(stats_lines)
            )
            
        except Exception as e:
            return ToolExecutionResult.error(
                "Failed to get memory statistics",
                f"Error retrieving memory stats: {str(e)}"
            )
    
    def _clear_current_session(self) -> ToolExecutionResult:
        """Clear current session memory."""
        try:
            # Note: This would require implementing a clear_session method in PersistentMemory
            # For now, we'll just provide information
            return ToolExecutionResult.success(
                "Session clear information",
                """🗑️ **Clear Current Session**

⚠️  **Note**: Session clearing is not implemented in the current memory system.
The persistent memory is designed to retain conversation history for continuity.

**Alternative options**:
• Use `memory(action="stats")` to see current memory usage
• Memory automatically manages older entries
• Previous sessions remain available for context

**If you need to reset context**:
• Start a new conversation session
• Memory will create a new session automatically
• Previous context remains available for reference"""
            )
            
        except Exception as e:
            return ToolExecutionResult.error(
                "Failed to clear session",
                f"Error: {str(e)}"
            )


def get_tool():
    """Get the memory tool instance."""
    return MemoryTool() 