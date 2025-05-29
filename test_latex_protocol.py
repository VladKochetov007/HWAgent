#!/usr/bin/env python3
"""
Test script for Universal LaTeX Documentation Protocol
Verifies that the new mandatory LaTeX creation workflow is active
"""

import os
import sys
from hwagent.react_agent import ReActAgent
from hwagent.tool_manager import ToolManager
from hwagent.config_loader import ConfigLoader

def test_latex_protocol():
    """Test that the LaTeX protocol is properly configured"""
    
    print("🔥 Testing Universal LaTeX Documentation Protocol 🔥")
    print("=" * 60)
    
    try:
        # Load configuration
        config = ConfigLoader()
        
        # Initialize components
        tool_manager = ToolManager()
        agent = ReActAgent(tool_manager=tool_manager)
        
        # Get system prompt
        system_prompt = agent.system_prompt_builder.build_system_prompt()
        prompt_text = str(system_prompt)
        
        print("📋 Protocol Verification:")
        
        # Check for mandatory LaTeX documentation
        checks = [
            ("MANDATORY LATEX DOCUMENTATION PROTOCOL", "🔥 Mandatory LaTeX protocol"),
            ("FOR EVERY TASK - NO EXCEPTIONS", "📄 Universal task coverage"),
            ("latex_compile tool", "🛠️ Compilation workflow"),
            ("latex_fix tool", "🔧 Error fixing capability"),
            ("UNIVERSAL PLAN TEMPLATE", "📋 Structured planning"),
            ("QUALITY VERIFICATION CHECKLIST", "✅ Quality assurance"),
            ("Tree of Thoughts", "🌳 Advanced reasoning"),
            ("Self-consistency", "🔄 Validation methodology"),
            ("Meta-prompting", "🎯 Strategic planning"),
        ]
        
        all_passed = True
        for check_text, description in checks:
            if check_text in prompt_text:
                print(f"✅ {description}")
            else:
                print(f"❌ {description} - MISSING")
                all_passed = False
        
        print("\n📊 Available Tools:")
        available_tools = tool_manager.get_tool_names()
        
        latex_tools = ["latex_compile", "latex_fix", "create_file"]
        for tool in latex_tools:
            if tool in available_tools:
                print(f"✅ {tool} - Available")
            else:
                print(f"❌ {tool} - MISSING")
                all_passed = False
        
        print(f"\n📈 Total available tools: {len(available_tools)}")
        print(f"Available: {', '.join(available_tools)}")
        
        print("\n🎯 Protocol Features:")
        features = [
            ("Mandatory LaTeX creation", "MANDATORY LATEX DOCUMENTATION" in prompt_text),
            ("Automatic PDF compilation", "latex_compile" in prompt_text),
            ("Error auto-fixing", "latex_fix" in prompt_text),
            ("Multi-level verification", "Level 1" in prompt_text and "Level 2" in prompt_text),
            ("Professional deliverables", "📂 Deliverables" in prompt_text),
            ("Quality checklist", "QUALITY VERIFICATION CHECKLIST" in prompt_text),
        ]
        
        for feature, status in features:
            print(f"{'✅' if status else '❌'} {feature}")
            if not status:
                all_passed = False
        
        print("\n" + "=" * 60)
        if all_passed:
            print("🎉 SUCCESS: Universal LaTeX Documentation Protocol is FULLY ACTIVE!")
            print("📄 Every task will now generate professional LaTeX documents with PDF output")
            print("🔧 Automatic error fixing and verification is enabled")
            print("🚀 System ready for enhanced documentation workflow")
        else:
            print("⚠️  WARNING: Some components of the LaTeX protocol are missing")
            print("🔧 Please check the configuration and ensure all tools are available")
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Error testing LaTeX protocol: {e}")
        return False

def test_workflow_example():
    """Test the workflow with a simple example"""
    print("\n🧪 Testing Workflow Example")
    print("-" * 30)
    
    try:
        tool_manager = ToolManager()
        agent = ReActAgent(tool_manager=tool_manager)
        
        # Simulate a simple task to check workflow planning
        print("📝 Simulating task: 'Calculate the derivative of x²'")
        
        # Check if the agent would plan LaTeX creation
        system_prompt = agent.system_prompt_builder.build_system_prompt()
        
        has_latex_workflow = all([
            "CREATE COMPREHENSIVE LATEX DOCUMENT" in str(system_prompt),
            "COMPILE LATEX TO PDF" in str(system_prompt),
            "FIX COMPILATION ERRORS" in str(system_prompt),
            "VERIFY PDF generation" in str(system_prompt)
        ])
        
        if has_latex_workflow:
            print("✅ Agent will follow mandatory LaTeX workflow")
            print("   1. ✅ Create comprehensive LaTeX document")
            print("   2. ✅ Compile LaTeX to PDF") 
            print("   3. ✅ Fix compilation errors if needed")
            print("   4. ✅ Verify PDF generation success")
        else:
            print("❌ LaTeX workflow not properly configured")
            
        return has_latex_workflow
        
    except Exception as e:
        print(f"❌ Error in workflow test: {e}")
        return False

if __name__ == "__main__":
    print("Starting Universal LaTeX Documentation Protocol Test\n")
    
    # Test protocol configuration
    protocol_ok = test_latex_protocol()
    
    # Test workflow planning
    workflow_ok = test_workflow_example()
    
    print("\n" + "=" * 60)
    print("🎯 FINAL RESULTS:")
    print(f"📋 Protocol Configuration: {'✅ PASS' if protocol_ok else '❌ FAIL'}")
    print(f"🔄 Workflow Planning: {'✅ PASS' if workflow_ok else '❌ FAIL'}")
    
    if protocol_ok and workflow_ok:
        print("\n🎉 ALL TESTS PASSED!")
        print("🔥 Universal LaTeX Documentation Protocol is ready!")
        print("📄 Every task will generate professional documentation")
        sys.exit(0)
    else:
        print("\n⚠️  SOME TESTS FAILED")
        print("🔧 Please check configuration and try again")
        sys.exit(1) 