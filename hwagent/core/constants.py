"""
Constants used throughout HWAgent.
Following SRP - single source of truth for all constants.
"""

from typing import Final


class Constants:
    """Central location for all constants used in HWAgent."""
    
    # File and directory constants
    DEFAULT_TMP_DIRECTORY: Final[str] = "tmp"
    CONFIG_DIR: Final[str] = "hwagent/config"
    TOOLS_DIR: Final[str] = "hwagent/tools"
    
    # Configuration file paths
    API_CONFIG_PATH: Final[str] = f"{CONFIG_DIR}/api.yaml"
    PROMPTS_CONFIG_PATH: Final[str] = f"{CONFIG_DIR}/prompts.yaml"
    
    # Environment variables
    OPENROUTER_API_KEY: Final[str] = "OPENROUTER_API_KEY"
    
    # Agent configuration
    MAX_ITERATIONS: Final[int] = 7
    DEFAULT_STREAMING_ENABLED: Final[bool] = True
    EXECUTION_TIMEOUT_SECONDS: Final[int] = 30
    
    # File validation
    FORBIDDEN_PATH_SEGMENTS: Final[tuple[str, ...]] = ("..", )
    MAX_FILE_SIZE_BYTES: Final[int] = 10 * 1024 * 1024  # 10MB
    
    # Response parsing markers
    THOUGHT_MARKER: Final[str] = "THOUGHT:"
    PLAN_MARKER: Final[str] = "PLAN:"
    TOOL_CALL_MARKER: Final[str] = "TOOL_CALL:"
    FINAL_ANSWER_MARKER: Final[str] = "FINAL_ANSWER:"
    
    # Tool execution
    TOOL_ERROR_PREFIX: Final[str] = "Error:"
    TOOL_SUCCESS_PREFIX: Final[str] = "Successfully"
    
    # Special commands
    COMMAND_PREFIX: Final[str] = "/"
    EXIT_COMMANDS: Final[tuple[str, ...]] = ("exit", "/exit")
    CLEAR_COMMAND: Final[str] = "/clear"
    CONTEXT_COMMAND: Final[str] = "/context"
    STREAM_COMMAND: Final[str] = "/stream"
    
    # Stream command options
    STREAM_ON: Final[str] = "on"
    STREAM_OFF: Final[str] = "off"
    
    # Message roles
    ROLE_SYSTEM: Final[str] = "system"
    ROLE_USER: Final[str] = "user"
    ROLE_ASSISTANT: Final[str] = "assistant"
    ROLE_TOOL: Final[str] = "tool"
    
    # Tool choice options
    TOOL_CHOICE_AUTO: Final[str] = "auto"
    TOOL_CHOICE_NONE: Final[str] = "none"
    
    # File extensions
    PYTHON_EXTENSIONS: Final[tuple[str, ...]] = (".py",)
    CPP_EXTENSIONS: Final[tuple[str, ...]] = (".cpp", ".cc", ".cxx")
    C_EXTENSIONS: Final[tuple[str, ...]] = (".c",)
    
    # Supported languages
    LANGUAGE_PYTHON: Final[str] = "python"
    LANGUAGE_CPP: Final[str] = "cpp"
    LANGUAGE_C: Final[str] = "c"
    LANGUAGE_AUTO: Final[str] = "auto"
    
    # Compiler commands
    COMPILER_GCC: Final[str] = "gcc"
    COMPILER_GPP: Final[str] = "g++"
    PYTHON_EXECUTABLE: Final[str] = "python" 