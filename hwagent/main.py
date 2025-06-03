"""Main entry point for HWAgent."""

import asyncio
import argparse
import sys
from pathlib import Path

from .utils.config import config
from .core import ReActAgent
from .api import api


# ANSI color codes for terminal output
class Colors:
    GRAY = '\033[90m'
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    RESET = '\033[0m'


async def solve_problem_cli(problem: str, agent_id: str | None = None) -> None:
    """Solve problem via CLI."""
    print(f"🤖 HWAgent starting...")
    print(f"📝 Problem: {problem}")
    print(f"🔧 Agent ID: {agent_id or 'auto-generated'}")
    print("-" * 60)
    
    async with ReActAgent(agent_id=agent_id) as agent:
        print(f"📁 Working directory: {agent.working_dir}")
        print(f"{Colors.GRAY}{'='*60}")
        print(f"🧠 AGENT THINKING PROCESS")
        print(f"{'='*60}{Colors.RESET}")
        
        # Use verbose mode to show real-time progress
        result = await agent.solve(problem, verbose=True)
        
        print(f"{Colors.GRAY}{'='*60}{Colors.RESET}")
        print("🎯 SOLUTION COMPLETE")
        print("-" * 60)
        print(f"✅ Completed: {result['completed']}")
        print(f"🔄 Total iterations: {result['total_iterations']}")
        print(f"📁 Working directory: {result['working_directory']}")
        
        # Show summary if there were multiple steps
        if result['total_iterations'] > 1:
            print("\n📋 EXECUTION SUMMARY:")
            for step in result['steps']:
                print(f"\n🔸 Step {step['iteration']}")
                print(f"{Colors.GRAY}💭 Thought: {step['thought']}{Colors.RESET}")
                
                if step['action']:
                    print(f"{Colors.BLUE}⚡ Action: {step['action']}{Colors.RESET}")
                    print(f"{Colors.YELLOW}📥 Input: {step['action_input']}{Colors.RESET}")
                
                if step['observation']:
                    obs_text = step['observation']
                    # Show full observation with length info
                    print(f"{Colors.GREEN}👁️ Result ({len(obs_text)} chars):")
                    print(f"{Colors.GREEN}{obs_text}{Colors.RESET}")
                    print()
        
        print(f"\n{Colors.BOLD}📂 Files created in: {result['working_directory']}{Colors.RESET}")


def main():
    """Main function with CLI argument parsing."""
    parser = argparse.ArgumentParser(description="HWAgent - Homework Solving Agent")
    parser.add_argument("--mode", choices=["cli", "api"], default="cli", 
                       help="Run mode: cli for command line, api for web server")
    parser.add_argument("--problem", type=str, 
                       help="Problem to solve (required for cli mode)")
    parser.add_argument("--agent-id", type=str, 
                       help="Agent ID (optional)")
    parser.add_argument("--host", default="127.0.0.1", 
                       help="API server host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=5000, 
                       help="API server port (default: 5000)")
    parser.add_argument("--debug", action="store_true", 
                       help="Enable debug mode")
    
    args = parser.parse_args()
    
    if args.mode == "cli":
        if not args.problem:
            print("❌ Error: --problem is required for CLI mode")
            sys.exit(1)
        
        try:
            asyncio.run(solve_problem_cli(args.problem, args.agent_id))
        except KeyboardInterrupt:
            print(f"\n{Colors.RED}🛑 Interrupted by user{Colors.RESET}")
            sys.exit(0)
        except Exception as e:
            print(f"{Colors.RED}❌ Error: {str(e)}{Colors.RESET}")
            sys.exit(1)
    
    elif args.mode == "api":
        print(f"🚀 Starting HWAgent API server...")
        print(f"🌐 Host: {args.host}")
        print(f"🔌 Port: {args.port}")
        print(f"🐛 Debug: {args.debug}")
        print(f"📝 Endpoints:")
        print(f"  - GET  /health  - Health check")
        print(f"  - GET  /tools   - List available tools")
        print(f"  - POST /solve   - Solve homework problem")
        print("-" * 60)
        
        try:
            api.run(host=args.host, port=args.port, debug=args.debug)
        except KeyboardInterrupt:
            print(f"\n{Colors.RED}🛑 API server stopped{Colors.RESET}")
            sys.exit(0)


if __name__ == "__main__":
    main() 