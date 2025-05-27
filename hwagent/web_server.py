#!/usr/bin/env python3
"""
Web server for HWAgent - provides HTTP and WebSocket API for frontend integration.
"""

import os
import sys
import json
import asyncio
import logging
from typing import Any, Dict
from pathlib import Path
import time

from flask import Flask, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to Python path
sys.path.insert(0, os.getcwd())

from hwagent.tool_manager import ToolManager
from hwagent.react_agent import ReActAgent
from hwagent.config_loader import load_yaml_config
from openai import OpenAI

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'hwagent-secret-key')
CORS(app, origins="*")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Global variables for agent
agent = None
tool_manager = None


class StreamingReActAgent(ReActAgent):
    """Extended ReActAgent with WebSocket streaming capability."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.socket_session_id = None
        self.max_retries = 3
        self.retry_delay = 1.0  # seconds
    
    def set_socket_session(self, session_id: str):
        """Set socket session ID for streaming."""
        self.socket_session_id = session_id
    
    def emit_to_frontend(self, event: str, data: Any):
        """Emit data to frontend via WebSocket."""
        if self.socket_session_id:
            try:
                socketio.emit(event, data, room=self.socket_session_id)
            except Exception as e:
                logger.error(f"Failed to emit to frontend: {e}")

    def _api_call_with_retry(self, completion_params: dict, max_retries: int = 3):
        """Make API call with retry logic for network errors."""
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                if completion_params.get("stream", False):
                    return self.client.chat.completions.create(**completion_params)
                else:
                    return self.client.chat.completions.create(**completion_params)
            except Exception as e:
                last_exception = e
                error_msg = str(e).lower()
                
                # Check if it's a retryable error
                if any(retryable in error_msg for retryable in [
                    'connection', 'timeout', 'network', '502', '503', '504', 
                    'bad gateway', 'service unavailable', 'gateway timeout'
                ]):
                    if attempt < max_retries - 1:
                        wait_time = self.retry_delay * (2 ** attempt)  # exponential backoff
                        logger.warning(f"API call failed (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {wait_time}s...")
                        self.emit_to_frontend('status', {
                            'message': f'Сетевая ошибка, переподключение... (попытка {attempt + 1}/{max_retries})',
                            'type': 'retry'
                        })
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"API call failed after {max_retries} attempts: {e}")
                        self.emit_to_frontend('status', {
                            'message': 'Сетевые проблемы, попробуйте позже',
                            'type': 'error'
                        })
                else:
                    # Non-retryable error
                    logger.error(f"Non-retryable API error: {e}")
                    self.emit_to_frontend('error', {'message': f'Ошибка API: {str(e)}'})
                
                raise last_exception
        
        # Should not reach here, but just in case
        raise last_exception

    def _parse_streamed_tool_calls(self, tool_calls_buffer: dict) -> list:
        """Parse and validate streamed tool calls."""
        final_tool_calls = []
        
        for index in sorted(tool_calls_buffer.keys()):
            tool_call = tool_calls_buffer[index]
            
            # Validate tool call completeness
            if not tool_call.get("id") or not tool_call.get("function", {}).get("name"):
                logger.warning(f"Incomplete tool call at index {index}: {tool_call}")
                continue
            
            try:
                # Validate JSON arguments
                args_str = tool_call["function"].get("arguments", "{}")
                if args_str.strip():
                    json.loads(args_str)  # Validate JSON
                
                class ToolCall:
                    def __init__(self, id_, type_, function):
                        self.id = id_
                        self.type = type_
                        self.function = Function(function["name"], function["arguments"])
                
                class Function:
                    def __init__(self, name, arguments):
                        self.name = name
                        self.arguments = arguments
                
                final_tool_calls.append(ToolCall(
                    tool_call["id"],
                    tool_call["type"],
                    tool_call["function"]
                ))
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in tool call arguments: {e}")
                self.emit_to_frontend('tool_call_error', {
                    'message': f'Ошибка парсинга аргументов инструмента: {e}'
                })
                continue
        
        return final_tool_calls

    def _stream_response(self, completion_stream) -> tuple[str, list]:
        """Override streaming with WebSocket emission and improved error handling."""
        accumulated_content = ""
        tool_calls_buffer = {}
        final_tool_calls = []
        
        # Emit start of streaming
        self.emit_to_frontend('stream_start', {'type': 'assistant'})
        
        try:
            for chunk in completion_stream:
                if not chunk.choices:
                    continue
                    
                choice = chunk.choices[0]
                delta = choice.delta
                
                # Handle content streaming
                if delta.content:
                    accumulated_content += delta.content
                    # Emit each chunk to frontend
                    self.emit_to_frontend('stream_chunk', {
                        'content': delta.content,
                        'type': 'content'
                    })
                
                # Handle tool calls streaming with validation
                if delta.tool_calls:
                    for tool_call_delta in delta.tool_calls:
                        index = tool_call_delta.index
                        
                        if index not in tool_calls_buffer:
                            tool_calls_buffer[index] = {
                                "id": "",
                                "type": "function",
                                "function": {"name": "", "arguments": ""}
                            }
                        
                        if tool_call_delta.id:
                            tool_calls_buffer[index]["id"] = tool_call_delta.id
                        
                        if tool_call_delta.function:
                            if tool_call_delta.function.name:
                                tool_calls_buffer[index]["function"]["name"] += tool_call_delta.function.name
                            if tool_call_delta.function.arguments:
                                tool_calls_buffer[index]["function"]["arguments"] += tool_call_delta.function.arguments
                
                # Check if streaming is finished
                if choice.finish_reason:
                    break
                    
        except Exception as e:
            logger.error(f"Error during streaming: {e}")
            self.emit_to_frontend('error', {'message': f'Ошибка стриминга: {str(e)}'})
            
        # Parse and validate tool calls
        final_tool_calls = self._parse_streamed_tool_calls(tool_calls_buffer)
        
        # Emit end of streaming
        self.emit_to_frontend('stream_end', {'type': 'assistant'})
        
        return accumulated_content, final_tool_calls

    def process_user_request(self, user_input: str) -> str:
        """Override to emit iteration info to frontend with improved error handling."""
        # Add user message to persistent history
        self.persistent_conversation_history.append({"role": "user", "content": user_input})
        
        # Emit user message to frontend
        self.emit_to_frontend('user_message', {'content': user_input})

        tools_for_api = self.tool_manager.get_tools_for_api()

        for iteration in range(self.MAX_ITERATIONS):
            # Emit iteration start
            self.emit_to_frontend('iteration_start', {
                'iteration': iteration + 1,
                'max_iterations': self.MAX_ITERATIONS
            })
            
            try:
                completion_params: dict[str, Any] = {
                    "model": self.model_name,
                    "messages": self.persistent_conversation_history,
                    "stream": self.enable_streaming
                }
                if tools_for_api:
                    completion_params["tools"] = tools_for_api
                    completion_params["tool_choice"] = "auto"

                # Use retry logic for API calls
                if self.enable_streaming:
                    completion_stream = self._api_call_with_retry(completion_params)
                    assistant_response_text_content, tool_calls = self._stream_response(completion_stream)
                    
                    class AssistantMessage:
                        def __init__(self, content, tool_calls):
                            self.content = content
                            self.tool_calls = tool_calls if tool_calls else None
                            
                        def model_dump(self, exclude_none=True):
                            result = {"role": "assistant", "content": self.content}
                            if self.tool_calls and not exclude_none:
                                result["tool_calls"] = [
                                    {
                                        "id": tc.id,
                                        "type": tc.type,
                                        "function": {
                                            "name": tc.function.name,
                                            "arguments": tc.function.arguments
                                        }
                                    } for tc in self.tool_calls
                                ]
                            return result
                    
                    assistant_message_obj = AssistantMessage(assistant_response_text_content, tool_calls)
                else:
                    completion = self._api_call_with_retry(completion_params)
                    
                    if not (completion.choices and completion.choices[0].message):
                        error_msg = self.messages.get("failed_to_get_model_response_error", "Не удалось получить ответ от модели")
                        self.persistent_conversation_history.append({"role": "assistant", "content": f"[System Error: {error_msg}]"})
                        self.emit_to_frontend('error', {'message': error_msg})
                        return error_msg

                    assistant_message_obj = completion.choices[0].message
                    assistant_response_text_content = assistant_message_obj.content or ""
                    
                    # Emit non-streaming response
                    self.emit_to_frontend('assistant_message', {'content': assistant_response_text_content})

                # Add assistant message to persistent history
                self.persistent_conversation_history.append(assistant_message_obj.model_dump(exclude_none=True))

                parsed_text_parts = self._parse_llm_response(assistant_response_text_content)

                # Emit parsed parts to frontend
                if parsed_text_parts.thought:
                    self.emit_to_frontend('thought', {'content': parsed_text_parts.thought})
                if parsed_text_parts.plan:
                    self.emit_to_frontend('plan', {'content': parsed_text_parts.plan})

                if assistant_message_obj.tool_calls:
                    for tool_call_api_obj in assistant_message_obj.tool_calls:
                        tool_call_id = tool_call_api_obj.id
                        tool_name_from_api = tool_call_api_obj.function.name
                        tool_params_str_from_api = tool_call_api_obj.function.arguments
                        
                        # Emit tool call start
                        self.emit_to_frontend('tool_call_start', {
                            'id': tool_call_id,
                            'name': tool_name_from_api,
                            'arguments': tool_params_str_from_api
                        })
                        
                        try:
                            tool_params_dict = json.loads(tool_params_str_from_api)
                        except json.JSONDecodeError as e:
                            error_msg = self.messages.get("failed_to_parse_tool_args_error", "Ошибка парсинга аргументов инструмента: {error}").format(
                                tool_name=tool_name_from_api, error=e, args=tool_params_str_from_api)
                            self.persistent_conversation_history.append({
                                "role": "tool", 
                                "tool_call_id": tool_call_id, 
                                "name": tool_name_from_api, 
                                "content": error_msg
                            })
                            self.emit_to_frontend('tool_call_error', {'message': error_msg})
                            continue
                        
                        try:
                            raw_tool_output = self.tool_manager.execute_tool(tool_name_from_api, tool_params_dict)
                            
                            # Emit tool call result
                            self.emit_to_frontend('tool_call_result', {
                                'id': tool_call_id,
                                'result': raw_tool_output.content if hasattr(raw_tool_output, 'content') else str(raw_tool_output)
                            })
                            
                            formatted_tool_output_content = str(raw_tool_output)
                            
                        except Exception as e:
                            error_msg = f"Ошибка выполнения инструмента {tool_name_from_api}: {str(e)}"
                            formatted_tool_output_content = error_msg
                            self.emit_to_frontend('tool_call_error', {'message': error_msg})

                        # Add tool result to conversation
                        self.persistent_conversation_history.append({
                            "role": "tool",
                            "tool_call_id": tool_call_id,
                            "name": tool_name_from_api,
                            "content": formatted_tool_output_content
                        })

                    # Continue to next iteration if tools were called
                    continue

                # Final answer reached - emit and return
                self.emit_to_frontend('final_answer', {'content': assistant_response_text_content})
                return assistant_response_text_content

            except Exception as e:
                error_msg = f"Ошибка на итерации {iteration + 1}: {str(e)}"
                logger.error(error_msg)
                self.emit_to_frontend('error', {'message': error_msg})
                
                # Add error to conversation history
                self.persistent_conversation_history.append({
                    "role": "assistant", 
                    "content": f"[System Error: {error_msg}]"
                })
                return error_msg

        # Max iterations reached
        max_iter_msg = f"Достигнуто максимальное количество итераций ({self.MAX_ITERATIONS})"
        self.emit_to_frontend('max_iterations', {'message': max_iter_msg})
        return max_iter_msg


def initialize_agent():
    """Initialize the HWAgent with configuration."""
    global agent, tool_manager
    
    try:
        # Load configuration
        api_config = load_yaml_config("hwagent/config/api.yaml")
        prompts_config = load_yaml_config("hwagent/config/prompts.yaml")
        
        # Get API configuration
        openrouter_config = api_config.get("openrouter", {})
        base_url = openrouter_config.get("base_url")
        model_name = openrouter_config.get("model")
        
        if not base_url or not model_name:
            raise ValueError("Missing API configuration")
        
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("Missing OPENROUTER_API_KEY environment variable")
        
        # Initialize components
        client = OpenAI(base_url=base_url, api_key=api_key)
        tool_manager = ToolManager()
        
        base_system_prompt = prompts_config.get("tech_solver", {}).get("system_prompt", "You are a helpful AI assistant.")
        agent_react_prompts = prompts_config.get("agent_messages", {}).get("react_agent", {})
        
        agent = StreamingReActAgent(
            client, 
            model_name, 
            tool_manager, 
            base_system_prompt, 
            agent_react_prompts, 
            enable_streaming=True
        )
        
        logger.info(f"Agent initialized successfully with {tool_manager.get_tool_count()} tools")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize agent: {e}")
        return False


# HTTP Routes
@app.route('/')
def serve_index():
    """Serve the main frontend page."""
    return send_from_directory('../frontend', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static frontend files."""
    return send_from_directory('../frontend', filename)

@app.route('/api/health')
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'agent_initialized': agent is not None,
        'tools_count': tool_manager.get_tool_count() if tool_manager else 0
    })

@app.route('/api/tools')
def get_tools():
    """Get available tools."""
    if not tool_manager:
        return jsonify({'error': 'Tool manager not initialized'}), 500
    
    return jsonify({
        'tools': tool_manager.get_tool_names(),
        'count': tool_manager.get_tool_count()
    })


# WebSocket Events
@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    logger.info(f"Client connected: {request.sid}")
    emit('connected', {'status': 'connected', 'session_id': request.sid})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on('send_message')
def handle_message(data):
    """Handle incoming message from frontend."""
    try:
        if not agent:
            emit('error', {'message': 'Agent not initialized'})
            return
        
        user_message = data.get('message', '').strip()
        if not user_message:
            emit('error', {'message': 'Empty message'})
            return
        
        # Capture session ID before starting background task
        session_id = request.sid
        
        # Set socket session for streaming
        agent.set_socket_session(session_id)
        
        # Process message in a separate thread to avoid blocking
        def process_message():
            try:
                response = agent.process_user_request(user_message)
                socketio.emit('message_complete', {'response': response}, room=session_id)
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                socketio.emit('error', {'message': str(e)}, room=session_id)
        
        # Start processing in background
        socketio.start_background_task(process_message)
        
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        emit('error', {'message': str(e)})

@socketio.on('clear_context')
def handle_clear_context():
    """Handle context clearing request."""
    if agent:
        agent.clear_context()
        emit('context_cleared', {'status': 'cleared'})
    else:
        emit('error', {'message': 'Agent not initialized'})

@socketio.on('get_context_summary')
def handle_get_context_summary():
    """Handle context summary request."""
    if agent:
        summary = agent.get_context_summary()
        emit('context_summary', {'summary': summary})
    else:
        emit('error', {'message': 'Agent not initialized'})


if __name__ == '__main__':
    # Initialize agent
    if not initialize_agent():
        logger.error("Failed to initialize agent. Exiting.")
        sys.exit(1)
    
    # Start server
    host = os.environ.get('HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', 8000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting HWAgent Web Server on {host}:{port}")
    socketio.run(app, host=host, port=port, debug=debug) 