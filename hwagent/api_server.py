#!/usr/bin/env python3
"""
REST API Server for HWAgent with full streaming support.
Provides both HTTP REST endpoints and WebSocket streaming capabilities.
"""

import os
import sys
import json
import asyncio
import logging
import uuid
from typing import Any, Dict, List, Optional
from pathlib import Path
from datetime import datetime
import threading
import queue
import time

from flask import Flask, request, jsonify, send_from_directory, Response, stream_template
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to Python path
sys.path.insert(0, os.getcwd())

from hwagent.tool_manager import ToolManager
from hwagent.react_agent import ReActAgent
from hwagent.config_loader import load_yaml_config
from hwagent.core import MessageManager
from openai import OpenAI

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'hwagent-secret-key-2024')
CORS(app, origins="*")
socketio = SocketIO(
    app, 
    cors_allowed_origins="*", 
    async_mode='threading',
    logger=True,
    engineio_logger=True
)

# Global storage for agents and sessions
agents: Dict[str, 'StreamingReActAgent'] = {}
active_sessions: Dict[str, Dict[str, Any]] = {}


class StreamingReActAgent(ReActAgent):
    """Extended ReActAgent with REST API and WebSocket streaming capabilities."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session_id: Optional[str] = None
        self.max_retries = 3
        self.retry_delay = 1.0
        self.message_queue = queue.Queue()
        self.response_complete = threading.Event()
        self.current_response = ""
        self.is_streaming = False
        
    def set_session_id(self, session_id: str):
        """Set session ID for this agent instance."""
        self.session_id = session_id
        
    def emit_event(self, event: str, data: Any):
        """Emit event via WebSocket if session is connected."""
        if self.session_id:
            try:
                socketio.emit(event, data, room=self.session_id)
            except Exception as e:
                logger.error(f"Failed to emit event {event}: {e}")
    
    def start_streaming_response(self, user_input: str) -> str:
        """Start processing user request with streaming support."""
        self.is_streaming = True
        self.current_response = ""
        self.response_complete.clear()
        
        # Start processing in background thread
        thread = threading.Thread(
            target=self._process_with_streaming,
            args=(user_input,)
        )
        thread.daemon = True
        thread.start()
        
        return "Streaming started"
    
    def _process_with_streaming(self, user_input: str):
        """Process user request in background thread with streaming."""
        try:
            self.emit_event('stream_start', {'message': 'Processing your request...'})
            
            # Use parent's process_user_request but override streaming behavior
            response = self.process_user_request(user_input)
            
            self.current_response = response
            self.emit_event('stream_complete', {'response': response})
            
        except Exception as e:
            error_msg = f"Error processing request: {str(e)}"
            logger.error(error_msg)
            self.emit_event('error', {'message': error_msg})
            self.current_response = error_msg
        finally:
            self.is_streaming = False
            self.response_complete.set()
    
    def get_streaming_response(self, timeout: int = 300) -> str:
        """Wait for streaming response to complete."""
        if self.response_complete.wait(timeout):
            return self.current_response
        else:
            return "Request timed out"


def initialize_agent() -> Optional[StreamingReActAgent]:
    """Initialize agent with proper error handling."""
    try:
        # Load configurations
        api_config = load_yaml_config("hwagent/config/api.yaml")
        prompts_config = load_yaml_config("hwagent/config/prompts.yaml")
        
        # Validate API configuration
        openrouter_config = api_config.get("openrouter", {})
        base_url = openrouter_config.get("base_url")
        model_name = openrouter_config.get("model")
        
        if not base_url or not model_name:
            raise ValueError("Missing API configuration")
        
        # Check API key
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable not set")
        
        # Get prompts
        base_system_prompt = prompts_config.get("tech_solver", {}).get(
            "system_prompt", "You are a helpful AI assistant."
        )
        agent_react_prompts = prompts_config.get("agent_messages", {}).get("react_agent", {})
        
        # Initialize components
        client = OpenAI(base_url=base_url, api_key=api_key)
        tool_manager = ToolManager()
        
        agent = StreamingReActAgent(
            client=client,
            model_name=model_name,
            tool_manager=tool_manager,
            base_system_prompt=base_system_prompt,
            agent_prompts=agent_react_prompts,
            enable_streaming=True
        )
        
        logger.info(f"Agent initialized successfully with {tool_manager.get_tool_count()} tools")
        return agent
        
    except Exception as e:
        logger.error(f"Failed to initialize agent: {e}")
        return None


def get_or_create_agent(session_id: str) -> Optional[StreamingReActAgent]:
    """Get existing agent or create new one for session."""
    if session_id not in agents:
        agent = initialize_agent()
        if agent:
            agent.set_session_id(session_id)
            agents[session_id] = agent
        else:
            return None
    return agents[session_id]


# REST API Endpoints

@app.route('/')
def serve_index():
    """Serve the main HTML page."""
    return send_from_directory('static', 'index.html')


@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files."""
    return send_from_directory('static', filename)


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0',
        'active_sessions': len(active_sessions)
    })


@app.route('/api/sessions', methods=['POST'])
def create_session():
    """Create a new chat session."""
    session_id = str(uuid.uuid4())
    
    agent = get_or_create_agent(session_id)
    if not agent:
        return jsonify({'error': 'Failed to initialize agent'}), 500
    
    active_sessions[session_id] = {
        'created_at': datetime.utcnow().isoformat(),
        'last_activity': datetime.utcnow().isoformat(),
        'message_count': 0
    }
    
    return jsonify({
        'session_id': session_id,
        'created_at': active_sessions[session_id]['created_at'],
        'tools_available': agent.tool_manager.get_tool_count()
    })


@app.route('/api/sessions/<session_id>', methods=['GET'])
def get_session_info(session_id: str):
    """Get session information."""
    if session_id not in active_sessions:
        return jsonify({'error': 'Session not found'}), 404
    
    session_info = active_sessions[session_id].copy()
    agent = agents.get(session_id)
    if agent:
        session_info['context_summary'] = agent.get_context_summary()
    
    return jsonify(session_info)


@app.route('/api/sessions/<session_id>', methods=['DELETE'])
def delete_session(session_id: str):
    """Delete a session and cleanup resources."""
    if session_id in active_sessions:
        del active_sessions[session_id]
    
    if session_id in agents:
        del agents[session_id]
    
    return jsonify({'message': 'Session deleted'})


@app.route('/api/sessions/<session_id>/messages', methods=['POST'])
def send_message(session_id: str):
    """Send message to agent (non-streaming)."""
    if session_id not in active_sessions:
        return jsonify({'error': 'Session not found'}), 404
    
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({'error': 'Message is required'}), 400
    
    user_message = data['message']
    agent = get_or_create_agent(session_id)
    if not agent:
        return jsonify({'error': 'Failed to get agent'}), 500
    
    try:
        # Process message without streaming
        agent.enable_streaming = False
        response = agent.process_user_request(user_message)
        
        # Update session activity
        active_sessions[session_id]['last_activity'] = datetime.utcnow().isoformat()
        active_sessions[session_id]['message_count'] += 1
        
        return jsonify({
            'response': response,
            'timestamp': datetime.utcnow().isoformat(),
            'session_id': session_id
        })
        
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/sessions/<session_id>/stream', methods=['POST'])
def stream_message(session_id: str):
    """Send message to agent with Server-Sent Events streaming."""
    if session_id not in active_sessions:
        return jsonify({'error': 'Session not found'}), 404
    
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({'error': 'Message is required'}), 400
    
    def generate_stream():
        agent = get_or_create_agent(session_id)
        if not agent:
            yield f"data: {json.dumps({'error': 'Failed to get agent'})}\n\n"
            return
        
        try:
            # Enable streaming
            agent.enable_streaming = True
            
            # Start processing
            yield f"data: {json.dumps({'type': 'start', 'message': 'Processing...'})}\n\n"
            
            response = agent.process_user_request(data['message'])
            
            # Send final response
            yield f"data: {json.dumps({'type': 'complete', 'response': response})}\n\n"
            
            # Update session
            active_sessions[session_id]['last_activity'] = datetime.utcnow().isoformat()
            active_sessions[session_id]['message_count'] += 1
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return Response(
        generate_stream(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive'
        }
    )


@app.route('/api/sessions/<session_id>/context', methods=['GET'])
def get_context(session_id: str):
    """Get session context summary."""
    if session_id not in active_sessions:
        return jsonify({'error': 'Session not found'}), 404
    
    agent = agents.get(session_id)
    if not agent:
        return jsonify({'error': 'Agent not found'}), 404
    
    return jsonify({
        'context_summary': agent.get_context_summary(),
        'session_id': session_id
    })


@app.route('/api/sessions/<session_id>/context', methods=['DELETE'])
def clear_context(session_id: str):
    """Clear session context."""
    if session_id not in active_sessions:
        return jsonify({'error': 'Session not found'}), 404
    
    agent = agents.get(session_id)
    if not agent:
        return jsonify({'error': 'Agent not found'}), 404
    
    agent.clear_context()
    return jsonify({'message': 'Context cleared'})


@app.route('/api/tools', methods=['GET'])
def get_tools():
    """Get available tools information."""
    try:
        tool_manager = ToolManager()
        tools_info = []
        
        for tool_name, tool_class in tool_manager.tools.items():
            if hasattr(tool_class, 'get_definition'):
                tool_def = tool_class.get_definition()
                tools_info.append({
                    'name': tool_name,
                    'description': tool_def.get('description', ''),
                    'parameters': tool_def.get('parameters', {})
                })
        
        return jsonify({
            'tools': tools_info,
            'count': len(tools_info)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# WebSocket Events

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection."""
    session_id = request.sid
    logger.info(f"WebSocket connected: {session_id}")
    
    # Join room for this session
    join_room(session_id)
    
    # Initialize session if not exists
    if session_id not in active_sessions:
        active_sessions[session_id] = {
            'created_at': datetime.utcnow().isoformat(),
            'last_activity': datetime.utcnow().isoformat(),
            'message_count': 0,
            'connection_type': 'websocket'
        }
    
    emit('connected', {'session_id': session_id})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection."""
    session_id = request.sid
    logger.info(f"WebSocket disconnected: {session_id}")
    
    # Leave room
    leave_room(session_id)
    
    # Optionally cleanup session after disconnect
    # Could implement session timeout instead


@socketio.on('send_message')
def handle_websocket_message(data):
    """Handle WebSocket message with streaming response."""
    session_id = request.sid
    
    if 'message' not in data:
        emit('error', {'message': 'Message is required'})
        return
    
    user_message = data['message']
    
    # Get or create agent
    agent = get_or_create_agent(session_id)
    if not agent:
        emit('error', {'message': 'Failed to initialize agent'})
        return
    
    try:
        # Start streaming response
        emit('stream_start', {'message': 'Processing your request...'})
        
        # Process with streaming enabled
        agent.enable_streaming = True
        response = agent.process_user_request(user_message)
        
        # Send complete response
        emit('stream_complete', {
            'response': response,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        # Update session
        if session_id in active_sessions:
            active_sessions[session_id]['last_activity'] = datetime.utcnow().isoformat()
            active_sessions[session_id]['message_count'] += 1
        
    except Exception as e:
        logger.error(f"Error in WebSocket message handling: {e}")
        emit('error', {'message': str(e)})


@socketio.on('clear_context')
def handle_clear_context():
    """Handle context clearing via WebSocket."""
    session_id = request.sid
    
    agent = agents.get(session_id)
    if not agent:
        emit('error', {'message': 'Agent not found'})
        return
    
    agent.clear_context()
    emit('context_cleared', {'message': 'Context has been cleared'})


@socketio.on('get_context')
def handle_get_context():
    """Handle context request via WebSocket."""
    session_id = request.sid
    
    agent = agents.get(session_id)
    if not agent:
        emit('error', {'message': 'Agent not found'})
        return
    
    context_summary = agent.get_context_summary()
    emit('context_summary', {'summary': context_summary})


def run_server(host='127.0.0.1', port=5000, debug=False):
    """Run the Flask-SocketIO server."""
    logger.info(f"Starting HWAgent API Server on {host}:{port}")
    logger.info(f"Debug mode: {debug}")
    
    socketio.run(
        app,
        host=host,
        port=port,
        debug=debug,
        allow_unsafe_werkzeug=True
    )


if __name__ == '__main__':
    # Create static directory if it doesn't exist
    os.makedirs('static', exist_ok=True)
    
    run_server(
        host=os.environ.get('HOST', '127.0.0.1'),
        port=int(os.environ.get('PORT', 5000)),
        debug=os.environ.get('DEBUG', 'False').lower() == 'true'
    ) 