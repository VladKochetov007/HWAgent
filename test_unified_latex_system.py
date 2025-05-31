#!/usr/bin/env python3
"""
Test script for the new unified LaTeX system with memory integration.
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from hwagent.tools.unified_latex_tool import UnifiedLaTeXTool
from hwagent.core.persistent_memory import get_persistent_memory


def test_unified_latex_tool():
    """Test the unified LaTeX tool functionality"""
    print("=== Testing Unified LaTeX Tool ===")
    
    # Initialize tool
    tool = UnifiedLaTeXTool()
    print(f"Tool name: {tool.name}")
    print(f"Tool description: {tool.description[:100]}...")
    
    # Test template generation
    print("\n--- Testing Template Generation ---")
    template_result = tool._execute_impl(
        operation="template",
        filepath="test_template.tex",
        task_type="math",
        language="english",
        title="Test Mathematical Document",
        compile=False  # Don't compile for faster testing
    )
    
    print(f"Template result: {template_result.success}")
    print(f"Message: {template_result.message}")
    if template_result.details:
        print(f"Details: {template_result.details[:200]}...")
    
    # Test document creation
    print("\n--- Testing Document Creation ---")
    latex_content = r"""
\documentclass{article}
\usepackage[utf8]{inputenc}
\usepackage{amsmath}

\title{Test Document}
\author{Test Author}
\date{\today}

\begin{document}
\maketitle

\section{Introduction}
This is a test document.

\section{Mathematics}
Here is a simple equation:
\begin{equation}
E = mc^2
\end{equation}

\end{document}
"""
    
    create_result = tool._execute_impl(
        operation="create",
        filepath="test_document.tex",
        content=latex_content,
        compile=False  # Don't compile for faster testing
    )
    
    print(f"Create result: {create_result.success}")
    print(f"Message: {create_result.message}")
    if create_result.details:
        print(f"Details: {create_result.details[:200]}...")
    
    print("\n--- Template Generation Complete ---")


def test_persistent_memory():
    """Test the persistent memory system"""
    print("\n=== Testing Persistent Memory System ===")
    
    try:
        # Get memory instance
        memory = get_persistent_memory()
        print(f"Memory instance created successfully")
        
        # Add a test conversation entry
        memory.add_conversation_entry(
            user_query="Test LaTeX document creation",
            agent_response="Created LaTeX document successfully",
            tools_used=["unified_latex"],
            task_type="math",
            success=True
        )
        print("Added test conversation entry")
        
        # Get context summary
        context = memory.get_context_summary()
        print(f"Session context: {context}")
        
        # Get recent conversations
        recent = memory.get_recent_conversations(limit=3)
        print(f"Recent conversations: {len(recent)} entries")
        
        print("--- Memory System Test Complete ---")
        
    except Exception as e:
        print(f"Memory test failed: {e}")


def test_error_reporting():
    """Test LaTeX error reporting without fixes"""
    print("\n=== Testing Error Reporting ===")
    
    tool = UnifiedLaTeXTool()
    
    # Create intentionally broken LaTeX
    broken_latex = r"""
\documentclass{article}
\usepackage[utf8]{inputenc}

\title{Broken Document}
\author{Test}

\begin{document}
\maketitle

\section{Broken Math}
This will fail: \invalidcommand{broken}

\begin{equation
E = mc^2
\end{equation}

\unknown{command}

\end{document}
"""
    
    # Test with broken content (should report errors, not fix them)
    result = tool._execute_impl(
        operation="create",
        filepath="broken_test.tex", 
        content=broken_latex,
        compile=True  # Try to compile to see error reporting
    )
    
    print(f"Broken LaTeX result: {result.success}")
    print(f"Message: {result.message}")
    if result.details:
        print("Error details (should show compilation errors):")
        print(result.details)
    
    print("--- Error Reporting Test Complete ---")


def cleanup_test_files():
    """Clean up test files"""
    test_files = [
        "test_template.tex",
        "test_document.tex", 
        "broken_test.tex",
        "test_template.pdf",
        "test_document.pdf",
        "broken_test.pdf"
    ]
    
    for filename in test_files:
        if os.path.exists(filename):
            try:
                os.remove(filename)
                print(f"Cleaned up: {filename}")
            except OSError:
                pass


if __name__ == "__main__":
    print("Testing Enhanced HWAgent LaTeX System")
    print("=====================================")
    
    try:
        test_unified_latex_tool()
        test_persistent_memory()
        test_error_reporting()
        
        print("\n=== All Tests Completed ===")
        print("✅ Unified LaTeX tool tested")
        print("✅ Persistent memory tested") 
        print("✅ Error reporting tested")
        print("\nKey improvements implemented:")
        print("- Single unified LaTeX tool replacing 4 separate tools")
        print("- Multi-language and multi-task support")
        print("- Error reporting without automatic fixes")
        print("- Persistent conversation memory across sessions")
        print("- Enhanced context awareness")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        cleanup_test_files() 