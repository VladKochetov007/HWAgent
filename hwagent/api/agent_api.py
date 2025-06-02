"""API endpoints for HWAgent."""

import asyncio
import json
from typing import Any

from flask import Flask, request, jsonify
from flask_cors import CORS

from ..core import ReActAgent


class HWAgentAPI:
    """Flask API for HWAgent."""
    
    def __init__(self):
        self.app = Flask(__name__)
        CORS(self.app)
        self.setup_routes()
    
    def setup_routes(self):
        """Setup API routes."""
        
        @self.app.route('/health', methods=['GET'])
        def health():
            """Health check endpoint."""
            return jsonify({"status": "healthy", "service": "HWAgent"})
        
        @self.app.route('/solve', methods=['POST'])
        def solve_problem():
            """Solve homework problem endpoint."""
            try:
                data = request.get_json()
                
                if not data or 'problem' not in data:
                    return jsonify({
                        "error": "Missing 'problem' field in request body"
                    }), 400
                
                problem = data['problem']
                agent_id = data.get('agent_id')
                
                # Run async agent
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    result = loop.run_until_complete(self._solve_async(problem, agent_id))
                    return jsonify(result)
                finally:
                    loop.close()
                
            except Exception as e:
                return jsonify({
                    "error": f"Internal server error: {str(e)}"
                }), 500
        
        @self.app.route('/tools', methods=['GET']) 
        def list_tools():
            """List available tools."""
            tools = [
                {
                    "name": "create_file",
                    "description": "Create a new file with specified content and encoding"
                },
                {
                    "name": "edit_file", 
                    "description": "Edit an existing file using LLM assistance with specific instructions"
                },
                {
                    "name": "execute_command",
                    "description": "Execute system commands with security restrictions"
                },
                {
                    "name": "search_web",
                    "description": "Search the web for information using LangSearch API"
                }
            ]
            
            return jsonify({"tools": tools})
    
    async def _solve_async(self, problem: str, agent_id: str | None = None) -> dict[str, Any]:
        """Async helper to solve problem."""
        async with ReActAgent(agent_id=agent_id) as agent:
            result = await agent.solve(problem)
            return result
    
    def run(self, host: str = "127.0.0.1", port: int = 5000, debug: bool = False):
        """Run the Flask application."""
        self.app.run(host=host, port=port, debug=debug)


# Global API instance
api = HWAgentAPI() 