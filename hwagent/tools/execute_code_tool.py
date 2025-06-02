"""
Execute Code Tool - executes code files in various languages.
Refactored to use core components and follow SOLID principles.
"""

import os
import subprocess
from pathlib import Path
from typing import Any
import sys

from hwagent.core import (
    FileOperationTool, ToolExecutionResult, Constants, 
    ParameterValidator, FilePathValidator, SecurityValidator
)


class CodeExecutor:
    """Handles code execution for different languages. Following SRP."""
    
    def __init__(self, tmp_directory: str, timeout: int = Constants.EXECUTION_TIMEOUT_SECONDS):
        self.tmp_directory = tmp_directory
        self.timeout = timeout
    
    def execute_python(self, filepath: str) -> ToolExecutionResult:
        """Execute Python code file."""
        # Handle paths that already contain tmp_directory prefix
        if filepath.startswith(self.tmp_directory + "/"):
            # Path already includes tmp_directory, use as is
            full_path = filepath
            relative_path = filepath[len(self.tmp_directory) + 1:]
        else:
            # Normal relative path, add tmp_directory
            full_path = os.path.join(self.tmp_directory, filepath)
            relative_path = filepath
        
        try:
            # Read and validate Python code
            with open(full_path, "r", encoding="utf-8") as f:
                code_content = f.read()
            
            # Security check
            security_result = SecurityValidator.validate_python_code_safety(code_content)
            if security_result.is_error():
                return ToolExecutionResult.error(
                    f"executing Python file: {relative_path}",
                    f"Security validation failed: {security_result.details}"
                )
            
            # Execute Python code
            python_executable = sys.executable
            restricted_args = [
                python_executable, "-u", "-X", "dev",
                "-c", f"exec(open('{full_path}').read())"
            ]
            print(f"Executing command: {' '.join(restricted_args)}")
            
            result = subprocess.run(
                restricted_args,
                cwd=self.tmp_directory,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            output_lines = []
            if result.stdout:
                output_lines.append(f"STDOUT:\n{result.stdout}")
            if result.stderr:
                output_lines.append(f"STDERR:\n{result.stderr}")
            
            output = "\n".join(output_lines) if output_lines else "No output"
            
            if result.returncode == 0:
                return ToolExecutionResult.success(
                    f"executed Python file: {relative_path}",
                    output
                )
            else:
                return ToolExecutionResult.error(
                    f"executing Python file: {relative_path}",
                    f"Exit code {result.returncode}\n{output}"
                )
        
        except FileNotFoundError:
            return ToolExecutionResult.error(
                f"executing Python file: {relative_path}",
                f"File not found: {full_path}"
            )
        except subprocess.TimeoutExpired:
            return ToolExecutionResult.error(
                f"executing Python file: {relative_path}",
                f"Execution timeout after {self.timeout} seconds"
            )
        except Exception as e:
            return ToolExecutionResult.error(
                f"executing Python file: {relative_path}",
                str(e)
            )
    
    def execute_compiled_language(self, filepath: str, language: str) -> ToolExecutionResult:
        """Execute compiled language (C/C++) file."""
        # Handle paths that already contain tmp_directory prefix
        if filepath.startswith(self.tmp_directory + "/"):
            # Path already includes tmp_directory, use as is
            full_path = filepath
            relative_path = filepath[len(self.tmp_directory) + 1:]
        else:
            # Normal relative path, add tmp_directory
            full_path = os.path.join(self.tmp_directory, filepath)
            relative_path = filepath
        
        try:
            # Determine compiler and output executable name
            if language == Constants.LANGUAGE_CPP:
                compiler = "g++"
                compiler_flags = ["-std=c++17", "-Wall", "-Wextra"]
            else:  # C
                compiler = "gcc"
                compiler_flags = ["-std=c11", "-Wall", "-Wextra"]
            
            # Create executable name (remove extension, add .exe if needed)
            base_name = Path(relative_path).stem
            executable_name = f"{base_name}.exe" if os.name == 'nt' else base_name
            executable_path = os.path.join(self.tmp_directory, executable_name)
            
            # Compile the code
            compile_cmd = [compiler] + compiler_flags + ["-o", executable_path, full_path]
            
            compile_result = subprocess.run(
                compile_cmd,
                cwd=self.tmp_directory,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            if compile_result.returncode != 0:
                return ToolExecutionResult.error(
                    f"compiling {language} file: {relative_path}",
                    f"Compilation failed:\n{compile_result.stderr}"
                )
            
            # Execute the compiled program
            if os.name == 'nt':
                execute_cmd = [executable_path]
            else:
                execute_cmd = [f"./{executable_name}"]
            
            execute_result = subprocess.run(
                execute_cmd,
                cwd=self.tmp_directory,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            output_lines = []
            if compile_result.stdout:
                output_lines.append(f"COMPILE OUTPUT:\n{compile_result.stdout}")
            if execute_result.stdout:
                output_lines.append(f"EXECUTION OUTPUT:\n{execute_result.stdout}")
            if execute_result.stderr:
                output_lines.append(f"EXECUTION STDERR:\n{execute_result.stderr}")
            
            output = "\n".join(output_lines) if output_lines else "No output"
            
            # Clean up executable
            try:
                os.remove(executable_path)
            except OSError:
                pass  # Ignore cleanup errors
            
            if execute_result.returncode == 0:
                return ToolExecutionResult.success(
                    f"executed {language} file: {relative_path}",
                    output
                )
            else:
                return ToolExecutionResult.error(
                    f"executing {language} file: {relative_path}",
                    f"Exit code {execute_result.returncode}\n{output}"
                )
        
        except FileNotFoundError as e:
            return ToolExecutionResult.error(
                f"executing {language} file: {relative_path}",
                f"File not found or compiler missing: {str(e)}"
            )
        except subprocess.TimeoutExpired:
            return ToolExecutionResult.error(
                f"executing {language} file: {relative_path}",
                f"Execution timeout after {self.timeout} seconds"
            )
        except Exception as e:
            return ToolExecutionResult.error(
                f"executing {language} file: {relative_path}",
                str(e)
            )


class LanguageDetector:
    """Detects programming language from file extension. Following SRP."""
    
    @staticmethod
    def detect_language(filepath: str) -> str | None:
        """Detect programming language from file extension."""
        ext = Path(filepath).suffix.lower()
        
        if ext in Constants.PYTHON_EXTENSIONS:
            return Constants.LANGUAGE_PYTHON
        elif ext in Constants.CPP_EXTENSIONS:
            return Constants.LANGUAGE_CPP
        elif ext in Constants.C_EXTENSIONS:
            return Constants.LANGUAGE_C
        
        return None


class ExecuteCodeTool(FileOperationTool):
    """Tool for executing code files in various programming languages."""
    
    def __init__(self, tmp_directory: str = Constants.DEFAULT_TMP_DIRECTORY):
        super().__init__(tmp_directory)
        self.code_executor = CodeExecutor(tmp_directory)
        self.language_detector = LanguageDetector()
    
    @property
    def name(self) -> str:
        return "execute_code"
    
    @property
    def description(self) -> str:
        return "Execute code files (Python, C++, C) from the temporary directory and return output"
    
    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "filepath": {
                    "type": "string",
                    "description": "Relative path to the code file within temporary directory. Can be multiline for complex paths."
                },
                "language": {
                    "type": "string",
                    "description": f"Programming language: {Constants.LANGUAGE_PYTHON}, {Constants.LANGUAGE_CPP}, {Constants.LANGUAGE_C}, or {Constants.LANGUAGE_AUTO} to auto-detect. Can be multiline.",
                    "default": Constants.LANGUAGE_AUTO
                }
            },
            "required": ["filepath"]
        }
    
    def validate_parameters(self, parameters: dict[str, Any]) -> ToolExecutionResult:
        """Validate execute code parameters."""
        # Validate common file parameters
        base_result = super().validate_parameters(parameters)
        if base_result.is_error():
            return base_result
        
        # Validate language parameter
        language = parameters.get("language", Constants.LANGUAGE_AUTO)
        language_result = ParameterValidator.validate_language_parameter(language)
        if language_result.is_error():
            return language_result
        
        return ToolExecutionResult.success("All parameters validated successfully")
    
    def _execute_impl(self, **kwargs) -> ToolExecutionResult:
        """Execute code file."""
        filepath = kwargs["filepath"]
        language = kwargs.get("language", Constants.LANGUAGE_AUTO)
        
        # Ensure file exists
        exists_result = self._ensure_file_exists(filepath)
        if exists_result.is_error():
            return exists_result
        
        # Auto-detect language if needed
        if language == Constants.LANGUAGE_AUTO:
            detected_language = self.language_detector.detect_language(filepath)
            if not detected_language:
                ext = Path(filepath).suffix.lower()
                return ToolExecutionResult.error(
                    f"executing file: {filepath}",
                    f"Cannot auto-detect language for extension '{ext}'. "
                    f"Supported: {', '.join(Constants.PYTHON_EXTENSIONS + Constants.CPP_EXTENSIONS + Constants.C_EXTENSIONS)}"
                )
            language = detected_language
        
        # Execute based on language - pass relative filepath, not full_path
        if language == Constants.LANGUAGE_PYTHON:
            return self.code_executor.execute_python(filepath)
        elif language in (Constants.LANGUAGE_CPP, Constants.LANGUAGE_C):
            return self.code_executor.execute_compiled_language(filepath, language)
        else:
            return ToolExecutionResult.error(
                f"executing file: {filepath}",
                f"Unsupported language: {language}"
            ) 