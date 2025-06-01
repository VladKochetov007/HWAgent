"""
Execute Code Tool - executes code files in various languages.
Refactored to use core components and follow SOLID principles.
"""

import os
import subprocess
from pathlib import Path
from typing import Any

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
        """Execute Python file with security checks."""
        try:
            # Read file content for security analysis
            full_path = os.path.join(self.tmp_directory, filepath)
            with open(full_path, 'r', encoding='utf-8') as f:
                code_content = f.read()
            
            # Security check for dangerous patterns
            security_result = SecurityValidator.validate_python_code_safety(code_content)
            if security_result.is_error():
                return ToolExecutionResult.error(
                    f"Security check failed for {filepath}",
                    security_result.details
                )
            
            file_name = os.path.basename(filepath)
            
            # Additional security: restrict Python execution
            restricted_args = [
                Constants.PYTHON_EXECUTABLE, 
                "-I",  # Isolate from user site-packages
                "-s",  # Don't add user site directory
                file_name
            ]
            
            result = subprocess.run(
                restricted_args,
                cwd=self.tmp_directory,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}  # Prevent .pyc files
            )
            
            output_lines = [f"=== Python Execution: {file_name} ==="]
            output_lines.append(f"Exit Code: {result.returncode}")
            
            if result.stdout:
                output_lines.extend(["", "--- STDOUT ---", result.stdout.rstrip()])
            
            if result.stderr:
                output_lines.extend(["", "--- STDERR ---", result.stderr.rstrip()])
            
            if result.returncode == 0:
                output_lines.append("\n✓ Execution completed successfully")
                status = ToolExecutionResult.success
            else:
                output_lines.append(f"\n✗ Execution failed with exit code {result.returncode}")
                status = ToolExecutionResult.error
            
            return status(
                f"executed Python file: {file_name}",
                "\n".join(output_lines)
            )
            
        except subprocess.TimeoutExpired:
            return ToolExecutionResult.error(
                f"executing Python file: {filepath}",
                f"Execution timed out after {self.timeout} seconds"
            )
        except Exception as e:
            return ToolExecutionResult.error(
                f"executing Python file: {filepath}",
                str(e)
            )
    
    def execute_compiled_language(self, filepath: str, language: str) -> ToolExecutionResult:
        """Execute C/C++ file (compile and run)."""
        try:
            file_path = Path(filepath)
            file_stem = file_path.stem
            executable_name = f"{file_stem}.out"
            executable_path = os.path.join(self.tmp_directory, executable_name)
            
            # Determine compiler
            compiler = Constants.COMPILER_GPP if language == Constants.LANGUAGE_CPP else Constants.COMPILER_GCC
            
            try:
                # Compile
                compile_cmd = [compiler, os.path.basename(filepath), "-o", executable_name]
                
                compile_result = subprocess.run(
                    compile_cmd,
                    cwd=self.tmp_directory,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout
                )
                
                output_lines = [f"=== {language.upper()} Compilation: {os.path.basename(filepath)} ==="]
                output_lines.append(f"Compile Command: {' '.join(compile_cmd)}")
                output_lines.append(f"Exit Code: {compile_result.returncode}")
                
                if compile_result.stderr:
                    output_lines.extend(["", "--- COMPILE STDERR ---", compile_result.stderr.rstrip()])
                
                if compile_result.returncode != 0:
                    output_lines.append("\n✗ Compilation failed")
                    return ToolExecutionResult.error(
                        f"compiling {language} file: {filepath}",
                        "\n".join(output_lines),
                    )
                
                output_lines.append("\n✓ Compilation successful")
                
                # Run executable
                run_result = subprocess.run(
                    [f"./{executable_name}"],
                    cwd=self.tmp_directory,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout
                )
                
                output_lines.extend(["", "=== Execution ==="])
                output_lines.append(f"Exit Code: {run_result.returncode}")
                
                if run_result.stdout:
                    output_lines.extend(["", "--- STDOUT ---", run_result.stdout.rstrip()])
                
                if run_result.stderr:
                    output_lines.extend(["", "--- STDERR ---", run_result.stderr.rstrip()])
                
                if run_result.returncode == 0:
                    output_lines.append("\n✓ Execution completed successfully")
                    status = ToolExecutionResult.success
                else:
                    output_lines.append(f"\n✗ Execution failed with exit code {run_result.returncode}")
                    status = ToolExecutionResult.error
                
                return status(
                    f"executed {language} file: {os.path.basename(filepath)}",
                    "\n".join(output_lines)
                )
                
            finally:
                # Clean up executable
                try:
                    if os.path.exists(executable_path):
                        os.unlink(executable_path)
                except OSError:
                    pass
                    
        except subprocess.TimeoutExpired:
            return ToolExecutionResult.error(
                f"compiling/executing {language} file: {filepath}",
                f"Operation timed out after {self.timeout} seconds"
            )
        except Exception as e:
            return ToolExecutionResult.error(
                f"compiling/executing {language} file: {filepath}",
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
        
        full_path = self._get_full_path(filepath)
        
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
        
        # Execute based on language
        if language == Constants.LANGUAGE_PYTHON:
            return self.code_executor.execute_python(full_path)
        elif language in (Constants.LANGUAGE_CPP, Constants.LANGUAGE_C):
            return self.code_executor.execute_compiled_language(full_path, language)
        else:
            return ToolExecutionResult.error(
                f"executing file: {filepath}",
                f"Unsupported language: {language}"
            ) 