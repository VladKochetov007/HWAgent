"""
Simple LaTeX compilation tool that shows real compilation errors.
"""

import os
import subprocess
from pathlib import Path
from typing import Any

from hwagent.core.base_tool import FileOperationTool
from hwagent.core.models import ToolExecutionResult, ExecutionStatus
from hwagent.core.constants import Constants


class LaTeXCompileTool(FileOperationTool):
    """
    Simple LaTeX compilation tool that shows real compilation output.
    """
    
    def __init__(self, tmp_directory: str = Constants.DEFAULT_TMP_DIRECTORY):
        super().__init__(tmp_directory)
        self.timeout = 60  # 60 seconds timeout
    
    @property
    def name(self) -> str:
        return "latex_compile"
    
    @property
    def description(self) -> str:
        return """Compile LaTeX files to PDF. Shows last 300 lines of compilation output.
        
        Features:
        - Automatic quote removal from LaTeX content  
        - Simple compilation with pdftex/pdflatex/xelatex/lualatex (pdftex by default)
        - All errors and warnings are shown directly
        - Shows last 300 lines of output for debugging
        - Non-interactive mode (nonstopmode) for all engines"""
    
    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "filepath": {
                    "type": "string",
                    "description": "Path to the LaTeX file to compile (relative to tmp directory)"
                },
                "engine": {
                    "type": "string",
                    "description": "LaTeX engine to use",
                    "enum": ["pdftex", "pdflatex", "xelatex", "lualatex"],
                    "default": "pdftex"
                }
            },
            "required": ["filepath"]
        }
    
    def validate_parameters(self, parameters: dict[str, Any]) -> ToolExecutionResult:
        """Validate LaTeX compilation parameters."""
        # Call parent validation
        base_result = super().validate_parameters(parameters)
        if base_result.is_error():
            return base_result
        
        # Validate filepath exists
        filepath = parameters.get("filepath")
        file_exists_result = self._ensure_file_exists(filepath)
        if file_exists_result.is_error():
            return file_exists_result
        
        # Check if file has LaTeX extension
        if not filepath.lower().endswith(('.tex', '.latex')):
            return ToolExecutionResult.error(
                "Invalid file type",
                f"File {filepath} must have .tex or .latex extension"
            )
        
        return ToolExecutionResult.success("Parameters validated", "")
    
    def _execute_impl(self, **kwargs) -> ToolExecutionResult:
        """Execute LaTeX compilation"""
        filepath = kwargs["filepath"]
        engine = kwargs.get("engine", "pdftex")
        
        validation_result = self.validate_parameters(kwargs)
        if validation_result.status == ExecutionStatus.ERROR:
            return validation_result
        
        try:
            full_path = self._get_full_path(filepath)
            
            # Automatic quote removal from LaTeX content
            preprocessing_result = self._preprocess_latex_file(full_path)
            preprocessing_message = ""
            if preprocessing_result.message != "No changes needed":
                preprocessing_message = f"Preprocessing: {preprocessing_result.message}\n"
            
            file_name = os.path.basename(filepath)
            file_stem = Path(filepath).stem
            
            # Simple pdflatex command
            cmd = [
                engine,
                '-interaction=nonstopmode',  # Don't stop on errors
                '-file-line-error',         # Show file and line for errors
                file_name
            ]
            
            # Run compilation
            result = subprocess.run(
                cmd,
                cwd=self.tmp_directory,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',  # Replace invalid UTF-8 with replacement character
                timeout=self.timeout
            )
            
            # Combine stdout and stderr
            all_output = ""
            if result.stdout:
                all_output += result.stdout
            if result.stderr:
                all_output += "\n" + result.stderr
            
            # Get last 300 lines
            output_lines = all_output.split('\n')
            if len(output_lines) > 300:
                shown_output = '\n'.join(output_lines[-300:])
                output_header = f"[Showing last 300 lines of {len(output_lines)} total lines]\n\n"
            else:
                shown_output = all_output
                output_header = ""
            
            # Check if PDF was created
            pdf_path = os.path.join(self.tmp_directory, f"{file_stem}.pdf")
            pdf_exists = os.path.exists(pdf_path)
            
            # Analyze compilation output for errors
            has_errors = self._has_compilation_errors(all_output)
            
            # Format output
            final_output = f"=== LaTeX Compilation: {file_name} ===\n"
            final_output += f"Engine: {engine}\n"
            final_output += f"Command: {' '.join(cmd)}\n"
            final_output += f"Exit Code: {result.returncode}\n"
            final_output += f"PDF Created: {'Yes' if pdf_exists else 'No'}\n"
            final_output += f"Errors Detected: {'Yes' if has_errors else 'No'}\n"
            if preprocessing_message:
                final_output += f"{preprocessing_message}"
            final_output += f"\n{output_header}{shown_output}"
            
            # Determine success based on exit code, PDF existence, and error analysis
            if result.returncode == 0 and pdf_exists and not has_errors:
                return ToolExecutionResult.success(
                    f"✓ LaTeX compilation successful: {file_name}",
                    final_output
                )
            elif pdf_exists and not has_errors:
                return ToolExecutionResult.success(
                    f"⚠ LaTeX compilation completed with warnings: {file_name}",
                    final_output
                )
            elif pdf_exists and has_errors:
                return ToolExecutionResult.error(
                    f"✗ LaTeX compilation failed with errors (PDF created but contains errors): {file_name}",
                    final_output
                )
            else:
                return ToolExecutionResult.error(
                    f"✗ LaTeX compilation failed: {file_name}",
                    final_output
                )
                
        except subprocess.TimeoutExpired:
            return ToolExecutionResult.error(
                f"LaTeX compilation timeout: {filepath}",
                f"Compilation timed out after {self.timeout} seconds"
            )
        except FileNotFoundError:
            return ToolExecutionResult.error(
                f"LaTeX engine not found: {engine}",
                f"LaTeX engine '{engine}' not found. Please install a LaTeX distribution (e.g., TeX Live, MiKTeX)"
            )
        except Exception as e:
            return ToolExecutionResult.error(
                f"LaTeX compilation error: {str(e)}",
                f"Error compiling {filepath}: {str(e)}"
            )
    
    def _preprocess_latex_file(self, filepath: str) -> ToolExecutionResult:
        """Remove unwanted quotes from LaTeX file content"""
        try:
            # Read original content
            with open(filepath, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # Remove unwanted quotes
            processed_content = self._remove_unwanted_quotes(original_content)
            
            # Write back if changed
            if original_content != processed_content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(processed_content)
                
                return ToolExecutionResult.success(
                    "quotes removed",
                    f"Removed unwanted quotes from {os.path.basename(filepath)}"
                )
            else:
                return ToolExecutionResult.success(
                    "No changes needed",
                    f"File {os.path.basename(filepath)} was already clean"
                )
                
        except Exception as e:
            return ToolExecutionResult.error(
                f"Preprocessing failed: {str(e)}",
                f"Error preprocessing {filepath}: {str(e)}"
            )
    
    def _remove_unwanted_quotes(self, content: str) -> str:
        """Remove unwanted quotes from beginning and end of content"""
        if not content:
            return content
        
        # Remove different types of quotes from beginning and end
        quote_chars = ['"', "'", '`']
        
        for quote_char in quote_chars:
            # Remove triple quotes first (most common issue)
            triple_quote = quote_char * 3
            if content.startswith(triple_quote) and content.endswith(triple_quote):
                content = content[3:-3]
                break
            
            # Remove single quotes from beginning and end
            while content.startswith(quote_char) and content.endswith(quote_char):
                content = content[1:-1]
        
        # Clean up any remaining whitespace
        content = content.strip()
        
        return content 
    
    def _has_compilation_errors(self, output: str) -> bool:
        """
        Analyze LaTeX compilation output to detect actual errors.
        Returns True if there are serious errors that should fail compilation.
        """
        if not output:
            return False
        
        # Convert to lowercase for case-insensitive matching
        output_lower = output.lower()
        
        # Critical error patterns that indicate real compilation failures
        error_patterns = [
            "! undefined control sequence",
            "! missing",
            "! extra",
            "! improper",
            "! illegal",
            "! paragraph ended before",
            "! file ended while scanning",
            "! too many }",
            "! missing } inserted",
            "! missing $ inserted",
            "! display math should end with $$",
            "! you can't use",
            "! command",
            "! environment",
            "! latex error:",
            "! package",
            "! class",
            "fatal error",
            "emergency stop",
            "! ==> fatal error occurred",
            "unicode character",
            "not set up for use with latex",
            "inputenc error",
            "! file not found",
            "! i can't find file",
            "! package babel error",
            "! math version",
            "! font",
            "encoding scheme",
            "cannot be used with"
        ]
        
        # Check for error patterns
        for pattern in error_patterns:
            if pattern in output_lower:
                return True
        
        # Check for "! " at the beginning of lines (LaTeX error indicator)
        lines = output.split('\n')
        for line in lines:
            line_stripped = line.strip()
            if line_stripped.startswith('! ') and len(line_stripped) > 2:
                return True
        
        return False 