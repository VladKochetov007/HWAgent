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
    LANGSEARCH_API_KEY: Final[str] = "LANGSEARCH_API_KEY"
    
    # Agent configuration
    MAX_ITERATIONS: Final[int] = 7
    MAX_REACT_ITERATIONS: Final[int] = 25
    DEFAULT_STREAMING_ENABLED: Final[bool] = True
    EXECUTION_TIMEOUT_SECONDS: Final[int] = 15
    
    # File validation
    FORBIDDEN_PATH_SEGMENTS: Final[tuple[str, ...]] = ("..", "/", "\\", "~")
    MAX_FILE_SIZE_BYTES: Final[int] = 10 * 1024 * 1024  # 10MB
    
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
    
    # LangSearch API
    LANGSEARCH_API_URL: Final[str] = "https://api.langsearch.com/v1/web-search"
    
    # Web search defaults
    DEFAULT_SEARCH_COUNT: Final[int] = 5
    MAX_SEARCH_COUNT: Final[int] = 10
    MIN_SEARCH_COUNT: Final[int] = 1
    
    # Search freshness options
    FRESHNESS_ONE_DAY: Final[str] = "oneDay"
    FRESHNESS_ONE_WEEK: Final[str] = "oneWeek"
    FRESHNESS_ONE_MONTH: Final[str] = "oneMonth"
    FRESHNESS_ONE_YEAR: Final[str] = "oneYear"
    FRESHNESS_NO_LIMIT: Final[str] = "noLimit"
    
    # Security restrictions
    DANGEROUS_COMMANDS: Final[tuple[str, ...]] = (
        "rm", "rmdir", "del", "format", "fdisk", "mkfs", "dd", 
        "shutdown", "reboot", "halt", "systemctl", "service",
        "sudo", "su", "chmod", "chown", "passwd", "useradd",
        "curl", "wget", "git", "pip", "npm", "apt", "yum",
        "mount", "umount", "kill", "killall", "pkill",
        # Additional file deletion and HTTP commands to prevent API abuse
        "unlink", "trash", "shred", "wipe", "erase",
        "http", "https", "DELETE", "POST", "PUT", "PATCH",
        "api/fs/tmp/delete", "localhost:5000", "127.0.0.1:5000",
        "python -m http", "python3 -m http", "nc ", "netcat",
        "telnet", "ssh", "scp", "rsync", "ftp", "sftp"
    )

    DANGEROUS_PYTHON_IMPORTS: Final[tuple[str, ...]] = (
        "os.system", "subprocess.call", "subprocess.run", "subprocess.Popen",
        "eval", "exec", "__import__", "shutil.rmtree", "os.remove",
        "os.unlink", "os.rmdir", "pathlib.Path.unlink"
    )

    DANGEROUS_LATEX_COMMANDS: Final[tuple[str, ...]] = (
        "\\write18", "\\immediate\\write18", "\\openin", "\\openout",
        "\\input|", "\\InputIfFileExists", "\\@@input"
    )

    # Execution timeouts (reduced for safety)
    LATEX_TIMEOUT_SECONDS: Final[int] = 10     # Specific for LaTeX 