import os
import subprocess
import tempfile
from pathlib import Path
from hwagent.tools import BaseTool, ToolRegister


@ToolRegister
class ExecuteCodeTool(BaseTool):
    """Executes code files (Python, C++, etc.) from the tmp directory and returns the output. Use this to run your code and see results."""
    
    def __init__(self, tmp_directory: str = "tmp"):
        self.tmp_directory = tmp_directory
        os.makedirs(self.tmp_directory, exist_ok=True)
    
    def execute(self, filepath: str, language: str = "auto") -> str:
        """Execute a code file.
        
        Args:
            filepath: The filename or relative path within tmp directory
            language: The programming language ('python', 'cpp', 'auto' to detect from extension)
            
        Returns:
            str: Execution output and result or error message starting with 'Error:'
        """
        if not filepath or not isinstance(filepath, str):
            return "Error: 'filepath' (string) parameter is required for execute_code."

        try:
            if ".." in filepath or os.path.isabs(filepath):
                return f"Error: Invalid filepath '{filepath}'. Must be a relative path without '..'."
            
            # Construct full path within tmp directory
            full_path = os.path.join(self.tmp_directory, filepath)
            
            if not os.path.exists(full_path):
                return f"Error: File '{filepath}' does not exist in {self.tmp_directory}."
            
            if not os.path.isfile(full_path):
                return f"Error: '{filepath}' is not a file."

            # Auto-detect language from file extension
            if language == "auto":
                ext = Path(filepath).suffix.lower()
                if ext == ".py":
                    language = "python"
                elif ext in [".cpp", ".cc", ".cxx"]:
                    language = "cpp"
                elif ext == ".c":
                    language = "c"
                else:
                    return f"Error: Cannot auto-detect language for file extension '{ext}'. Supported: .py, .cpp, .cc, .cxx, .c"

            # Execute based on language
            if language == "python":
                return self._execute_python(full_path, filepath)
            elif language in ["cpp", "c"]:
                return self._execute_cpp(full_path, filepath, language)
            else:
                return f"Error: Unsupported language '{language}'. Supported: python, cpp, c"

        except Exception as e:
            return f"Error executing '{filepath}': {e}"

    def _execute_python(self, full_path: str, display_path: str) -> str:
        """Execute Python file."""
        try:
            # Execute from the tmp directory for proper relative imports
            file_name = os.path.basename(full_path)
            
            result = subprocess.run(
                ["python", file_name],
                cwd=self.tmp_directory,
                capture_output=True,
                text=True,
                timeout=30  # 30 second timeout
            )
            
            output = f"=== Python Execution: {display_path} ===\n"
            output += f"Exit Code: {result.returncode}\n"
            
            if result.stdout:
                output += f"\n--- STDOUT ---\n{result.stdout}"
            
            if result.stderr:
                output += f"\n--- STDERR ---\n{result.stderr}"
            
            if result.returncode == 0:
                output += f"\n✓ Execution completed successfully"
            else:
                output += f"\n✗ Execution failed with exit code {result.returncode}"
            
            return output
            
        except subprocess.TimeoutExpired:
            return f"Error: Python execution of '{display_path}' timed out (30 seconds)"
        except Exception as e:
            return f"Error executing Python file '{display_path}': {e}"

    def _execute_cpp(self, full_path: str, display_path: str, language: str) -> str:
        """Execute C++ file (compile and run)."""
        try:
            file_path = Path(full_path)
            file_stem = file_path.stem
            
            # Create temporary executable in tmp directory
            executable_path = os.path.join(self.tmp_directory, f"{file_stem}.out")
            
            try:
                # Compile
                compiler = "g++" if language == "cpp" else "gcc"
                compile_cmd = [compiler, os.path.basename(full_path), "-o", os.path.basename(executable_path)]
                
                compile_result = subprocess.run(
                    compile_cmd,
                    cwd=self.tmp_directory,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                output = f"=== C++ Compilation: {display_path} ===\n"
                output += f"Compile Command: {' '.join(compile_cmd)}\n"
                output += f"Exit Code: {compile_result.returncode}\n"
                
                if compile_result.stderr:
                    output += f"\n--- COMPILE STDERR ---\n{compile_result.stderr}"
                
                if compile_result.returncode != 0:
                    output += f"\n✗ Compilation failed"
                    return output
                
                output += f"\n✓ Compilation successful\n"
                
                # Run executable
                run_result = subprocess.run(
                    [f"./{os.path.basename(executable_path)}"],
                    cwd=self.tmp_directory,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                output += f"\n=== Execution ===\n"
                output += f"Exit Code: {run_result.returncode}\n"
                
                if run_result.stdout:
                    output += f"\n--- STDOUT ---\n{run_result.stdout}"
                
                if run_result.stderr:
                    output += f"\n--- STDERR ---\n{run_result.stderr}"
                
                if run_result.returncode == 0:
                    output += f"\n✓ Execution completed successfully"
                else:
                    output += f"\n✗ Execution failed with exit code {run_result.returncode}"
                
                return output
                
            finally:
                # Clean up executable
                try:
                    if os.path.exists(executable_path):
                        os.unlink(executable_path)
                except OSError:
                    pass
                    
        except subprocess.TimeoutExpired:
            return f"Error: C++ compilation/execution of '{display_path}' timed out (30 seconds)"
        except Exception as e:
            return f"Error compiling/executing C++ file '{display_path}': {e}" 