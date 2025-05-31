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
from datetime import datetime, UTC
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

# Create Flask app with static folder configuration
app = Flask(__name__, static_folder='../static', static_url_path='/static')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'hwagent-secret-key-default')
CORS(app, origins="*")

# Configure SocketIO
socketio = SocketIO(
    app, 
    cors_allowed_origins="*", 
    async_mode='threading',
    logger=False,  # Reduced logging noise
    engineio_logger=False
)

# Global storage for agents and sessions
agents: Dict[str, 'StreamingReActAgent'] = {}
active_sessions: Dict[str, Dict[str, Any]] = {}

# Global agent template for initialization
global_agent_template = None


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
        if not self.session_id:
            return
            
        try:
            # Check if session is connected
            if (self.session_id in active_sessions and 
                active_sessions[self.session_id].get('connected', False)):
                
                # Check if socketio server is available
                if hasattr(socketio, 'server') and socketio.server:
                    socketio.emit(event, data, room=self.session_id)
            
        except Exception as e:
            # Suppress the error to prevent breaking the flow
            logger.debug(f"Failed to emit event {event} to session {self.session_id}: {e}")
            # Mark session as disconnected if emission fails
            if self.session_id in active_sessions:
                active_sessions[self.session_id]['connected'] = False
    
    def emit_thought_stream(self, thought_type: str, content: str, metadata: dict = None):
        """Emit thought stream event with type and content."""
        if not self.session_id:
            return
            
        try:
            # Check if session is connected
            if (self.session_id in active_sessions and 
                active_sessions[self.session_id].get('connected', False)):
                
                data = {
                    'type': thought_type,
                    'content': content,
                    'timestamp': datetime.now(UTC).isoformat(),
                    'metadata': metadata or {}
                }
                
                # Check if we can safely emit before doing so
                if hasattr(socketio, 'server') and socketio.server:
                    socketio.emit('thought_stream', data, room=self.session_id)
                    
        except Exception as e:
            # Silently handle emission errors to prevent breaking the flow
            logger.debug(f"Failed to emit thought stream to session {self.session_id}: {e}")
            # Mark session as disconnected if emission fails
            if self.session_id in active_sessions:
                active_sessions[self.session_id]['connected'] = False
    
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
            self.emit_thought_stream('system', 'Начинаю обработку запроса...', {'user_input': user_input})
            
            # Override the iteration processor to add streaming
            original_processor = self.iteration_processor
            self.iteration_processor = StreamingIterationProcessor(
                llm_client=self.iteration_processor.llm_client,
                response_parser=self.iteration_processor.response_parser,
                tool_executor=self.iteration_processor.tool_executor,
                display_manager=self.iteration_processor.display_manager,
                agent=self
            )
            
            # Use parent's process_user_request but with streaming processor
            response = self.process_user_request(user_input)
            
            # Restore original processor
            self.iteration_processor = original_processor
            
            self.current_response = response
            self.emit_thought_stream('final_answer', response)
            self.emit_event('stream_complete', {'response': response})
            
        except Exception as e:
            error_msg = f"Error processing request: {str(e)}"
            logger.error(error_msg)
            self.emit_thought_stream('error', error_msg)
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


class StreamingIterationProcessor:
    """Extended IterationProcessor with streaming capabilities."""
    
    def __init__(self, llm_client, response_parser, tool_executor, display_manager, agent):
        self.llm_client = llm_client
        self.response_parser = response_parser
        self.tool_executor = tool_executor
        self.display_manager = display_manager
        self.agent = agent  # Reference to streaming agent
    
    def process_iteration(self, iteration: int, conversation_manager, tools_for_api) -> str | None:
        """Process a single iteration with streaming updates."""
        self.agent.emit_thought_stream('iteration_start', f'Итерация {iteration}', {'iteration': iteration})
        
        try:
            # Get LLM response
            self.agent.emit_thought_stream('system', 'Отправляю запрос к LLM...')
            assistant_content, assistant_message = self.llm_client.get_llm_response(
                conversation_manager.get_conversation_history(),
                tools_for_api
            )
            
            # Add to conversation
            conversation_manager.add_assistant_message(assistant_message)
            
            # Parse response
            parsed_response = self.response_parser.parse_llm_response(assistant_content)
            
            # Stream parsed components
            if parsed_response.thought:
                self.agent.emit_thought_stream('thought', parsed_response.thought)
            
            if parsed_response.plan:
                plan_text = "\n".join([f"{i+1}. {step}" for i, step in enumerate(parsed_response.plan)])
                self.agent.emit_thought_stream('plan', plan_text, {'steps': parsed_response.plan})
            
            if parsed_response.final_answer:
                self.agent.emit_thought_stream('final_answer', parsed_response.final_answer)
            
            # Handle response based on type
            return self._handle_parsed_response(
                assistant_message, parsed_response, conversation_manager
            )
            
        except Exception as e:
            return self._handle_iteration_error(e, conversation_manager)
    
    def _handle_parsed_response(self, assistant_message, parsed_response, conversation_manager) -> str | None:
        """Handle parsed response with streaming updates."""
        # API tool calls have priority
        if assistant_message.tool_calls:
            self.agent.emit_thought_stream('tool_execution', 'Выполняю инструменты...', 
                                         {'tool_calls': [tc.function.name for tc in assistant_message.tool_calls]})
            self.tool_executor.execute_api_tool_calls(assistant_message.tool_calls, conversation_manager)
            return None
        
        # Text-based tool call (warning case)
        elif parsed_response.has_tool_call():
            self.agent.emit_thought_stream('warning', f'Некорректный вызов инструмента: {parsed_response.tool_call_name}')
            self._handle_malformed_tool_call(parsed_response, conversation_manager)
            return None
        
        # Final answer
        elif parsed_response.has_final_answer():
            return parsed_response.final_answer
        
        # No clear action
        else:
            self.agent.emit_thought_stream('warning', 'Нет четкого действия в ответе')
            return self._handle_no_action_response(assistant_message.content, conversation_manager)
    
    def _handle_malformed_tool_call(self, parsed_response, conversation_manager) -> None:
        """Handle malformed tool calls."""
        from hwagent.core import MessageManager
        message_manager = MessageManager()
        tool_name = parsed_response.tool_call_name
        
        corrective_feedback = message_manager.format_message(
            "react_agent", "malformed_tool_call_feedback",
            tool_name=tool_name
        )
        conversation_manager.add_system_note(corrective_feedback)
    
    def _handle_no_action_response(self, content: str, conversation_manager) -> str | None:
        """Handle response with no clear action."""
        if content.strip():
            from hwagent.core import MessageManager
            message_manager = MessageManager()
            note = message_manager.get_message("react_agent", "bot_text_but_no_action_note")
            conversation_manager.add_system_note(note)
            return None
        else:
            from hwagent.core import MessageManager
            message_manager = MessageManager()
            note = message_manager.get_message("react_agent", "model_empty_response_system_note")
            conversation_manager.add_system_note(note)
            return None
    
    def _handle_iteration_error(self, error: Exception, conversation_manager) -> str:
        """Handle iteration errors."""
        from hwagent.core import MessageManager
        message_manager = MessageManager()
        error_msg = message_manager.format_message(
            "react_agent", "agent_processing_error", error=str(error)
        )
        self.agent.emit_thought_stream('error', f'Ошибка в итерации: {str(error)}')
        conversation_manager.add_system_note(error_msg)
        return f"An error occurred during processing: {str(error)}"


def initialize_global_agent() -> Optional[StreamingReActAgent]:
    """Initialize global agent template."""
    global global_agent_template
    
    if global_agent_template is not None:
        return global_agent_template
    
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
        base_system_prompt = prompts_config.get("minimal_test", {}).get(
            "system_prompt", "You are a helpful AI assistant."
        )
        agent_react_prompts = {}  # Simplified - no additional prompts for now
        
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
        
        # Store individual components on the template for easier access
        # when creating session agents
        global_agent_template = agent
        global_agent_template._client_instance = client
        global_agent_template._model_name_instance = model_name
        global_agent_template._tool_manager_instance = tool_manager
        global_agent_template._base_system_prompt_instance = base_system_prompt
        global_agent_template._agent_prompts_instance = agent_react_prompts
        
        logger.info(f"Global agent initialized successfully with {tool_manager.get_tool_count()} tools")
        return agent
        
    except Exception as e:
        logger.error(f"Failed to initialize global agent: {e}")
        return None


def create_session_agent(session_id: str) -> Optional[StreamingReActAgent]:
    """Create a new agent instance for a session."""
    try:
        if global_agent_template is None:
            base_agent = initialize_global_agent()
            if not base_agent:
                return None
        
        # Create new agent instance using stored components from the template
        agent = StreamingReActAgent(
            client=global_agent_template._client_instance,
            model_name=global_agent_template._model_name_instance,
            tool_manager=global_agent_template._tool_manager_instance,
            base_system_prompt=global_agent_template._base_system_prompt_instance,
            agent_prompts=global_agent_template._agent_prompts_instance,
            enable_streaming=True
        )
        
        agent.set_session_id(session_id)
        return agent
        
    except Exception as e:
        logger.error(f"Failed to create session agent: {e}")
        return None


def get_or_create_agent(session_id: str) -> Optional[StreamingReActAgent]:
    """Get existing agent or create new one for session."""
    if session_id not in agents:
        agent = create_session_agent(session_id)
        if agent:
            agents[session_id] = agent
        else:
            return None
    return agents[session_id]


# Static files handling
@app.route('/')
def serve_index():
    """Serve the main HTML page."""
    try:
        static_dir = Path(__file__).parent.parent / 'static'
        if not static_dir.exists():
            return jsonify({'error': 'Static directory not found'}), 404
        
        index_file = static_dir / 'index.html'
        if not index_file.exists():
            return jsonify({'error': 'index.html not found'}), 404
            
        return send_from_directory(str(static_dir), 'index.html')
    except Exception as e:
        logger.error(f"Error serving index: {e}")
        return jsonify({'error': 'Failed to serve index page'}), 500


@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files."""
    try:
        static_dir = Path(__file__).parent.parent / 'static'
        return send_from_directory(str(static_dir), filename)
    except Exception as e:
        logger.error(f"Error serving static file {filename}: {e}")
        return jsonify({'error': 'File not found'}), 404


# API Endpoints
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now(UTC).isoformat(),
        'version': '1.0.0',
        'active_sessions': len(active_sessions),
        'agents_loaded': len(agents)
    })


@app.route('/api/sessions', methods=['POST'])
def create_session():
    """Create a new chat session."""
    try:
        session_id = str(uuid.uuid4())
        
        # Initialize global agent if not done
        if global_agent_template is None:
            init_agent = initialize_global_agent()
            if not init_agent:
                return jsonify({'error': 'Failed to initialize agent system'}), 500
        
        # Create session record
        active_sessions[session_id] = {
            'created_at': datetime.now(UTC).isoformat(),
            'last_activity': datetime.now(UTC).isoformat(),
            'message_count': 0
        }
        
        return jsonify({
            'session_id': session_id,
            'created_at': active_sessions[session_id]['created_at'],
            'tools_available': global_agent_template.tool_manager.get_tool_count() if global_agent_template else 0
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        return jsonify({'error': 'Failed to create session'}), 500


@app.route('/api/sessions/<session_id>', methods=['GET'])
def get_session_info(session_id: str):
    """Get session information."""
    if session_id not in active_sessions:
        return jsonify({'error': 'Session not found'}), 404
    
    session_info = active_sessions[session_id].copy()
    agent = agents.get(session_id)
    if agent and hasattr(agent, 'get_context_summary'):
        try:
            session_info['context_summary'] = agent.get_context_summary()
        except:
            session_info['context_summary'] = "No context available"
    
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
        active_sessions[session_id]['last_activity'] = datetime.now(UTC).isoformat()
        active_sessions[session_id]['message_count'] += 1
        
        return jsonify({
            'response': response,
            'timestamp': datetime.now(UTC).isoformat(),
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
            active_sessions[session_id]['last_activity'] = datetime.now(UTC).isoformat()
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
    
    try:
        context_summary = agent.get_context_summary() if hasattr(agent, 'get_context_summary') else "No context available"
        return jsonify({
            'context_summary': context_summary,
            'session_id': session_id
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/sessions/<session_id>/context', methods=['DELETE'])
def clear_context(session_id: str):
    """Clear session context."""
    if session_id not in active_sessions:
        return jsonify({'error': 'Session not found'}), 404
    
    agent = agents.get(session_id)
    if not agent:
        return jsonify({'error': 'Agent not found'}), 404
    
    try:
        if hasattr(agent, 'clear_context'):
            agent.clear_context()
        return jsonify({'message': 'Context cleared'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/tools', methods=['GET'])
def get_tools():
    """Get available tools information."""
    try:
        if global_agent_template is None:
            initialize_global_agent()
        
        if global_agent_template and global_agent_template.tool_manager:
            tool_manager = global_agent_template.tool_manager
            tools_info = []
            
            # Correctly access tool definitions via the registry
            tool_definitions = tool_manager.registry.get_all_tool_definitions()
            
            for tool_def_obj in tool_definitions:
                # Assuming ToolDefinition has attributes: name, description, parameters
                # (or a method to convert to dict)
                # For simplicity, let's assume it's a dict-like object or has a to_dict() method
                if hasattr(tool_def_obj, 'to_dict'):
                    tool_def = tool_def_obj.to_dict()
                elif isinstance(tool_def_obj, dict): # If it's already a dict
                    tool_def = tool_def_obj
                else: # Fallback if direct attributes are expected (as in original code)
                     tool_def = {
                        "name": getattr(tool_def_obj, 'name', 'Unknown Tool'),
                        "description": getattr(tool_def_obj, 'description', ''),
                        "parameters": getattr(tool_def_obj, 'parameters', {})
                    }

                tools_info.append({
                    'name': tool_def.get('name'),
                    'description': tool_def.get('description', ''),
                    'parameters': tool_def.get('parameters', {}).get('properties', {}) # Align with ToolDefinition structure
                })
            
            return jsonify({
                'tools': tools_info,
                'count': len(tools_info)
            })
        else:
            return jsonify({
                'tools': [],
                'count': 0,
                'error': 'Tool manager not available'
            })
        
    except Exception as e:
        logger.error(f"Error getting tools: {e}")
        return jsonify({'error': str(e)}), 500


# Filesystem API for tmp directory
TMP_DIR_PATH = Path(__file__).parent.parent / 'tmp'
TMP_DIR_PATH.mkdir(exist_ok=True) # Ensure tmp directory exists

@app.route('/api/fs/tmp/list', methods=['GET'])
def list_tmp_directory():
    """List files and directories in hwagent/tmp/."""
    path_param = request.args.get('path', '.') # Relative path within tmp
    logger.info(f"Listing tmp directory for path: '{path_param}'")
    try:
        # Security: Resolve to absolute path and ensure it's within TMP_DIR_PATH
        requested_path = TMP_DIR_PATH.joinpath(path_param).resolve()
        logger.debug(f"Resolved requested path: {requested_path}")

        if not str(requested_path).startswith(str(TMP_DIR_PATH.resolve())):
            logger.warning(f"Access denied for path: {requested_path}. Outside allowed: {TMP_DIR_PATH.resolve()}")
            return jsonify({'error': 'Access denied: Path is outside the allowed directory.'}), 403
        if not requested_path.exists():
            logger.warning(f"Path not found: {requested_path}")
            return jsonify({'error': 'Path not found'}), 404

        items = []
        for item in requested_path.iterdir():
            items.append({
                'name': item.name,
                'path': str(item.relative_to(TMP_DIR_PATH)), # Ensure path is relative to TMP_DIR_PATH for client
                'is_dir': item.is_dir(),
                'size': item.stat().st_size if item.is_file() else None,
                'modified': datetime.fromtimestamp(item.stat().st_mtime).isoformat()
            })
        logger.info(f"Found {len(items)} items in '{path_param}'")
        return jsonify({'files': items}) # Return as an object with 'files' key
    except Exception as e:
        logger.error(f"Error listing tmp directory for path '{path_param}': {e}", exc_info=True)
        return jsonify({'error': f'Failed to list directory: {str(e)}'}), 500

@app.route('/api/fs/tmp/get', methods=['GET'])
def get_tmp_file():
    """Get content of a file from hwagent/tmp/."""
    file_path_str = request.args.get('path')
    logger.info(f"Request to get tmp file: '{file_path_str}'")
    if not file_path_str:
        logger.warning("File path not provided for /api/fs/tmp/get")
        return jsonify({'error': 'File path is required'}), 400

    try:
        # Security: Resolve and check path
        file_path = TMP_DIR_PATH.joinpath(file_path_str).resolve()
        logger.debug(f"Resolved file path for get: {file_path}")

        if not str(file_path).startswith(str(TMP_DIR_PATH.resolve())):
            logger.warning(f"Access denied for get file: {file_path}. Outside allowed: {TMP_DIR_PATH.resolve()}")
            return jsonify({'error': 'Access denied: Path is outside the allowed directory.'}), 403
        if not file_path.is_file():
            logger.warning(f"Path is not a file or does not exist for get: {file_path}")
            return jsonify({'error': 'Path is not a file or does not exist'}), 404
        
        MAX_FILE_SIZE = 5 * 1024 * 1024 
        if file_path.stat().st_size > MAX_FILE_SIZE:
            logger.warning(f"File too large: {file_path}, size: {file_path.stat().st_size}")
            return jsonify({'error': f'File is too large (max {MAX_FILE_SIZE // (1024*1024)}MB)'}), 400

        logger.info(f"Sending file: {file_path_str}")
        # Send file for inline display if possible, otherwise as attachment
        return send_from_directory(TMP_DIR_PATH, file_path_str, as_attachment=False)

    except Exception as e:
        logger.error(f"Error getting tmp file '{file_path_str}': {e}", exc_info=True)
        return jsonify({'error': f'Failed to get file: {str(e)}'}), 500

@app.route('/api/fs/tmp/delete', methods=['DELETE'])
def delete_tmp_item():
    """Delete a file or directory from hwagent/tmp/."""
    item_path_str = request.args.get('path')
    logger.info(f"Request to delete tmp item: '{item_path_str}'")
    if not item_path_str:
        logger.warning("Item path not provided for /api/fs/tmp/delete")
        return jsonify({'error': 'Item path is required'}), 400
    try:
        item_path = TMP_DIR_PATH.joinpath(item_path_str).resolve()
        logger.debug(f"Resolved item path for delete: {item_path}")

        if not str(item_path).startswith(str(TMP_DIR_PATH.resolve())):
            logger.warning(f"Access denied for delete item: {item_path}. Outside allowed: {TMP_DIR_PATH.resolve()}")
            return jsonify({'error': 'Access denied: Path is outside the allowed directory.'}), 403
        if item_path == TMP_DIR_PATH.resolve(): 
             logger.warning("Attempt to delete root tmp directory blocked.")
             return jsonify({'error': 'Cannot delete the root tmp directory.'}), 400
        if not item_path.exists():
            logger.warning(f"Item not found for delete: {item_path}")
            return jsonify({'error': 'Item not found'}), 404
        
        if item_path.is_file():
            item_path.unlink()
            logger.info(f"Deleted file: {item_path}")
            return jsonify({'message': f'File {item_path_str} deleted successfully'})
        elif item_path.is_dir():
            if not any(item_path.iterdir()): 
                item_path.rmdir()
                logger.info(f"Deleted empty directory: {item_path}")
                return jsonify({'message': f'Directory {item_path_str} deleted successfully'})
            else:
                logger.warning(f"Attempt to delete non-empty directory: {item_path}")
                return jsonify({'error': 'Directory is not empty. Only empty directories can be deleted.'}), 400
        else:
            logger.warning(f"Path is not a file or directory for delete: {item_path}")
            return jsonify({'error': 'Path is not a file or directory'}), 400

    except Exception as e:
        logger.error(f"Error deleting tmp item '{item_path_str}': {e}", exc_info=True)
        return jsonify({'error': f'Failed to delete item: {str(e)}'}), 500

# WebSocket Events
@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection."""
    session_id = request.sid
    logger.info(f"WebSocket connected: {session_id}")
    
    try:
        # Join room for this session
        join_room(session_id)
        
        # Initialize session if not exists
        if session_id not in active_sessions:
            active_sessions[session_id] = {
                'created_at': datetime.now(UTC).isoformat(),
                'last_activity': datetime.now(UTC).isoformat(),
                'message_count': 0,
                'connection_type': 'websocket',
                'connected': True
            }
        else:
            active_sessions[session_id]['connected'] = True
        
        # Small delay to ensure connection is ready
        time.sleep(0.05)
        
        emit('connected', {'session_id': session_id})
        logger.debug(f"WebSocket connection established for session: {session_id}")
        
    except Exception as e:
        logger.error(f"Error in WebSocket connect handler: {e}")
        emit('error', {'message': 'Connection failed'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection."""
    session_id = request.sid
    logger.info(f"WebSocket disconnected: {session_id}")
    
    try:
        # Leave room
        leave_room(session_id)
        
        # Mark session as disconnected
        if session_id in active_sessions:
            active_sessions[session_id]['connected'] = False
            
        logger.debug(f"WebSocket disconnection handled for session: {session_id}")
        
    except Exception as e:
        logger.error(f"Error in WebSocket disconnect handler: {e}")


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
        # Give WebSocket connection time to fully establish
        time.sleep(0.1)
        
        # Start streaming response
        emit('stream_start', {'message': 'Processing your request...'})
        
        # Process with streaming enabled
        agent.enable_streaming = True
        response = agent.process_user_request(user_message)
        
        # Send complete response
        emit('stream_complete', {
            'response': response,
            'timestamp': datetime.now(UTC).isoformat()
        })
        
        # Update session
        if session_id in active_sessions:
            active_sessions[session_id]['last_activity'] = datetime.now(UTC).isoformat()
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
    
    try:
        if hasattr(agent, 'clear_context'):
            agent.clear_context()
        emit('context_cleared', {'message': 'Context has been cleared'})
    except Exception as e:
        emit('error', {'message': str(e)})


@socketio.on('get_context')
def handle_get_context():
    """Handle context request via WebSocket."""
    session_id = request.sid
    
    agent = agents.get(session_id)
    if not agent:
        emit('error', {'message': 'Agent not found'})
        return
    
    try:
        context_summary = agent.get_context_summary() if hasattr(agent, 'get_context_summary') else "No context available"
        emit('context_summary', {'summary': context_summary})
    except Exception as e:
        emit('error', {'message': str(e)})


def run_server(host='127.0.0.1', port=5000, debug=False):
    """Run the Flask-SocketIO server."""
    # Initialize global agent on startup
    logger.info("Initializing HWAgent system...")
    if initialize_global_agent():
        logger.info("✅ HWAgent system initialized successfully")
    else:
        logger.error("❌ Failed to initialize HWAgent system")
        return
    
    # Create static directory if it doesn't exist
    static_dir = Path(__file__).parent.parent / 'static'
    static_dir.mkdir(exist_ok=True)
    
    logger.info(f"Starting HWAgent API Server on {host}:{port}")
    logger.info(f"Debug mode: {debug}")
    logger.info(f"Static files: {static_dir}")
    
    socketio.run(
        app,
        host=host,
        port=port,
        debug=debug,
        allow_unsafe_werkzeug=True
    )


if __name__ == '__main__':
    run_server(
        host=os.environ.get('HOST', '127.0.0.1'),
        port=int(os.environ.get('PORT', 5000)),
        debug=os.environ.get('DEBUG', 'False').lower() == 'true'
    ) 