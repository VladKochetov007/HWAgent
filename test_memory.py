#!/usr/bin/env python3
"""
Test script for full conversation memory functionality.
"""

import os
import sys
import json
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from hwagent.core.persistent_memory import get_persistent_memory
from hwagent.core.conversation_manager import ConversationManagerImpl
from hwagent.core.message_manager import MessageManager

def test_memory_functionality():
    """Test the memory functionality"""
    print("🧠 Testing Full Conversation Memory System")
    print("=" * 50)
    
    # Initialize components
    message_manager = MessageManager()
    conversation_manager = ConversationManagerImpl(message_manager, enable_persistence=True)
    
    # Test 1: Check memory status
    print("\n1. Testing memory status...")
    memory_status = conversation_manager.get_memory_status()
    print(f"Memory enabled: {memory_status.get('enabled', False)}")
    if not memory_status.get('enabled'):
        print(f"Reason: {memory_status.get('reason', 'Unknown')}")
        return
    
    # Test 2: Add some conversation entries
    print("\n2. Adding test conversation entries...")
    
    # Simulate user queries and responses
    test_conversations = [
        {
            "user_query": "Solve the equation x^2 + 5x + 6 = 0",
            "agent_response": "I'll solve this quadratic equation using factoring. The equation x^2 + 5x + 6 = 0 factors to (x + 2)(x + 3) = 0, so x = -2 or x = -3.",
            "tools_used": ["latex_create", "latex_compile"],
            "task_type": "mathematics",
            "success": True
        },
        {
            "user_query": "Create a Python script to calculate factorial",
            "agent_response": "I'll create a Python script with a factorial function using recursion and iteration methods.",
            "tools_used": ["create_file", "run_python"],
            "task_type": "programming", 
            "success": True
        },
        {
            "user_query": "Plot a graph of y = x^2",
            "agent_response": "I'll create a matplotlib plot of the quadratic function y = x^2.",
            "tools_used": ["create_file", "run_python"],
            "task_type": "data_analysis",
            "success": True
        }
    ]
    
    for i, conv in enumerate(test_conversations, 1):
        print(f"   Adding conversation {i}...")
        conversation_manager.complete_conversation_turn(
            agent_response=conv["agent_response"],
            task_type=conv["task_type"],
            success=conv["success"]
        )
        
        # Simulate adding user message for next iteration
        if i < len(test_conversations):
            conversation_manager.current_user_query = test_conversations[i]["user_query"]
            conversation_manager.current_tools_used = test_conversations[i]["tools_used"]
    
    # Test 3: Get session summary
    print("\n3. Testing session conversation summary...")
    session_summary = conversation_manager.get_session_conversation_summary()
    print("Session Summary:")
    print(session_summary)
    
    # Test 4: Get context for prompt
    print("\n4. Testing conversation context for prompt...")
    prompt_context = conversation_manager.get_conversation_context_for_prompt()
    print("Prompt Context:")
    print(prompt_context)
    
    # Test 5: Test persistent memory context
    print("\n5. Testing persistent memory context...")
    try:
        persistent_memory = get_persistent_memory()
        context_summary = persistent_memory.get_context_summary()
        print("Context Summary Keys:", list(context_summary.keys()))
        print(f"Entry count: {context_summary.get('entry_count', 0)}")
        print(f"Success rate: {context_summary.get('success_rate', 0):.1%}")
        print(f"Key topics: {context_summary.get('key_topics', [])}")
        print(f"Recent tools: {context_summary.get('recent_tool_usage', [])}")
    except Exception as e:
        print(f"Error accessing persistent memory: {e}")
    
    # Test 6: Check memory files
    print("\n6. Checking memory files...")
    memory_dir = Path("conversation_memory")
    if memory_dir.exists():
        print(f"Memory directory exists: {memory_dir}")
        session_file = memory_dir / "current_session.json"
        if session_file.exists():
            print(f"Session file size: {session_file.stat().st_size} bytes")
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                print(f"Session entries: {len(session_data.get('entries', []))}")
            except Exception as e:
                print(f"Error reading session file: {e}")
        else:
            print("Session file does not exist")
    else:
        print("Memory directory does not exist")
    
    print("\n✅ Memory functionality test completed!")

if __name__ == "__main__":
    test_memory_functionality() 