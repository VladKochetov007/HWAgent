"""
LaTeX Compile Tool - compiles LaTeX files to PDF and provides linting.
Automatically detects errors and suggests fixes for common LaTeX issues.
"""

import os
import re
import subprocess
from pathlib import Path
from typing import Any

from hwagent.core import (
    FileOperationTool, ToolExecutionResult, ExecutionStatus, Constants, 
    ParameterValidator, FilePathValidator
)


class LaTeXLinter:
    """Handles LaTeX linting and error detection. Following SRP."""
    
    @staticmethod
    def lint_latex_content(content: str) -> list[str]:
        """Lint LaTeX content and return list of warnings/suggestions."""
        warnings = []
        lines = content.split('\n')
        
        # Check for missing essential LaTeX structure
        if '\\documentclass' not in content:
            warnings.append("Missing \\documentclass declaration")
        
        if '\\begin{document}' not in content:
            warnings.append("Missing \\begin{document} environment")
        
        if '\\end{document}' not in content:
            warnings.append("Missing \\end{document} environment")
        
        # Check overall brace balance (not per line, as LaTeX allows multi-line structures)
        total_open_braces = content.count('{')
        total_close_braces = content.count('}')
        if total_open_braces != total_close_braces:
            warnings.append(f"Document has unmatched braces overall ({{ = {total_open_braces}, }} = {total_close_braces})")
        
        # Check for common typos only
        for i, line in enumerate(lines, 1):
            if '\\begn{' in line:
                warnings.append(f"Line {i}: Typo detected - \\begn{{ should be \\begin{{")
            
            if '\\ned{' in line:
                warnings.append(f"Line {i}: Typo detected - \\ned{{ should be \\end{{")
        
        return warnings


class LaTeXErrorParser:
    """Parses LaTeX compilation errors and suggests fixes."""
    
    @staticmethod
    def parse_latex_errors(error_output: str) -> list[dict[str, str]]:
        """Parse LaTeX error output and extract error information."""
        errors = []
        error_lines = error_output.split('\n')
        
        current_error = {}
        for line in error_lines:
            # LaTeX error pattern
            if line.startswith('!'):
                if current_error:
                    errors.append(current_error)
                current_error = {'type': 'error', 'message': line[1:].strip()}
            
            # Line number pattern
            elif 'l.' in line and current_error:
                match = re.search(r'l\.(\d+)', line)
                if match:
                    current_error['line'] = int(match.group(1))
                    current_error['context'] = line
            
            # Warning pattern
            elif 'Warning:' in line:
                errors.append({
                    'type': 'warning',
                    'message': line.strip()
                })
        
        if current_error:
            errors.append(current_error)
        
        return errors
    
    @staticmethod
    def suggest_fixes(errors: list[dict[str, str]]) -> list[str]:
        """Suggest fixes for common LaTeX errors."""
        suggestions = []
        
        for error in errors:
            message = error.get('message', '').lower()
            
            if 'undefined control sequence' in message:
                suggestions.append(
                    f"Fix suggestion: Check for typos in command names or add missing \\usepackage"
                )
            
            elif 'missing $' in message:
                suggestions.append(
                    f"Fix suggestion: Add missing $ for math mode or escape special characters"
                )
            
            elif 'environment' in message and 'undefined' in message:
                suggestions.append(
                    f"Fix suggestion: Check environment name spelling or add required package"
                )
            
            elif 'file not found' in message:
                suggestions.append(
                    f"Fix suggestion: Check file path and ensure the file exists"
                )
            
            elif 'unmatched' in message:
                suggestions.append(
                    f"Fix suggestion: Check for missing or extra braces, brackets, or parentheses"
                )
        
        return suggestions


class LaTeXCompiler:
    """Handles LaTeX compilation with different engines."""
    
    def __init__(self, tmp_directory: str, timeout: int = 30):
        self.tmp_directory = tmp_directory
        self.timeout = timeout
        self.engines = ['pdflatex', 'xelatex', 'lualatex']
    
    def compile_latex(self, filepath: str, engine: str = 'pdflatex', 
                     extra_args: list[str] = None) -> ToolExecutionResult:
        """Compile LaTeX file to PDF with automatic Enter input for prompts."""
        if extra_args is None:
            extra_args = []
        
        try:
            file_name = os.path.basename(filepath)
            file_stem = Path(filepath).stem
            
            # Enhanced pdflatex arguments with proper interaction handling
            cmd = [
                engine,
                '-interaction=batchmode',    # No interaction at all - prevents hanging
                '-file-line-error',         # Show file and line for errors
                '-synctex=1',               # Generate synctex for better error location
                *extra_args,
                file_name
            ]
            
            # Run directly without 'yes' command wrapper - batchmode handles input
            result = subprocess.run(
                cmd,
                cwd=self.tmp_directory,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                input=''  # Empty input to ensure no hanging
            )
            
            output_lines = [f"=== LaTeX Compilation: {file_name} ==="]
            output_lines.append(f"Engine: {engine}")
            output_lines.append(f"Command: {' '.join(cmd)}")
            output_lines.append(f"Exit Code: {result.returncode}")
            output_lines.append("Interaction: batchmode (no prompts)")
            
            # Check for PDF output
            pdf_path = os.path.join(self.tmp_directory, f"{file_stem}.pdf")
            pdf_exists = os.path.exists(pdf_path)
            
            if result.stdout:
                output_lines.extend(["", "--- COMPILATION OUTPUT ---", result.stdout])
            
            if result.stderr:
                output_lines.extend(["", "--- ERRORS/WARNINGS ---", result.stderr])
            
            # Parse errors and provide suggestions
            if result.returncode != 0 or result.stderr:
                errors = LaTeXErrorParser.parse_latex_errors(result.stderr or result.stdout)
                if errors:
                    output_lines.extend(["", "--- PARSED ERRORS ---"])
                    for i, error in enumerate(errors, 1):
                        output_lines.append(f"{i}. {error.get('type', 'error').upper()}: {error.get('message', '')}")
                        if 'line' in error:
                            output_lines.append(f"   Line: {error['line']}")
                        if 'context' in error:
                            output_lines.append(f"   Context: {error['context']}")
                    
                    suggestions = LaTeXErrorParser.suggest_fixes(errors)
                    if suggestions:
                        output_lines.extend(["", "--- SUGGESTED FIXES ---"])
                        for i, suggestion in enumerate(suggestions, 1):
                            output_lines.append(f"{i}. {suggestion}")
            
            if result.returncode == 0 and pdf_exists:
                output_lines.append(f"\n✓ Compilation successful! PDF created: {file_stem}.pdf")
                return ToolExecutionResult.success(
                    f"compiled LaTeX file: {file_name}",
                    "\n".join(output_lines)
                )
            elif pdf_exists:
                # PDF created despite warnings/errors - still success
                output_lines.append(f"\n✓ Compilation completed with warnings! PDF created: {file_stem}.pdf")
                return ToolExecutionResult.success(
                    f"compiled LaTeX file: {file_name} (with warnings)",
                    "\n".join(output_lines)
                )
            else:
                output_lines.append(f"\n✗ Compilation failed")
                return ToolExecutionResult(
                    status=ExecutionStatus.ERROR,
                    message=f"compiling LaTeX file: {file_name}",
                    details="\n".join(output_lines)
                )
                
        except subprocess.TimeoutExpired:
            return ToolExecutionResult.error(
                f"compiling LaTeX file: {filepath}",
                f"Compilation timed out after {self.timeout} seconds"
            )
        except FileNotFoundError:
            return ToolExecutionResult.error(
                f"compiling LaTeX file: {filepath}",
                f"LaTeX engine '{engine}' not found. Please install a LaTeX distribution (e.g., TeX Live, MiKTeX)"
            )
        except Exception as e:
            return ToolExecutionResult.error(
                f"compiling LaTeX file: {filepath}",
                str(e)
            )


class LaTeXCompileTool(FileOperationTool):
    """
    LaTeX compilation tool with automatic quote removal and enhanced package management.
    Compiles LaTeX files to PDF with intelligent error handling and preprocessing.
    """
    
    def __init__(self, tmp_directory: str = Constants.DEFAULT_TMP_DIRECTORY):
        super().__init__(tmp_directory)
        self.compiler = LaTeXCompiler(self.tmp_directory)
    
    @property
    def name(self) -> str:
        return "latex_compile"
    
    @property
    def description(self) -> str:
        return """Compile LaTeX files to PDF with automatic preprocessing and error analysis.
        
        Features:
        - Automatic quote removal from LaTeX content
        - Enhanced mathematical package inclusion
        - Multi-engine support (pdflatex, xelatex, lualatex)
        - Intelligent error parsing with fix suggestions
        - Safe compilation with timeout and batchmode
        
        The tool automatically preprocesses LaTeX files before compilation to ensure clean content."""
    
    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "filepath": {
                    "type": "string",
                    "description": "Path to the LaTeX file to compile (relative to tmp directory). Can be multiline."
                },
                "engine": {
                    "type": "string",
                    "description": "LaTeX engine to use",
                    "enum": ["pdflatex", "xelatex", "lualatex"],
                    "default": "pdflatex"
                },
                "lint_only": {
                    "type": "boolean",
                    "description": "Only perform linting without compilation",
                    "default": False
                },
                "extra_args": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Additional arguments to pass to LaTeX engine. Each argument can be multiline.",
                    "default": []
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
                "File must have .tex or .latex extension"
            )
        
        # Validate engine
        engine = parameters.get("engine", "pdflatex")
        if engine not in ["pdflatex", "xelatex", "lualatex"]:
            return ToolExecutionResult.error(
                "Invalid engine",
                f"Engine must be one of: pdflatex, xelatex, lualatex. Got: {engine}"
            )
        
        return ToolExecutionResult.success("LaTeX parameters validated successfully")
    
    def _execute_impl(self, **kwargs) -> ToolExecutionResult:
        """Execute LaTeX compilation with preprocessing"""
        filepath = kwargs["filepath"]
        engine = kwargs.get("engine", "pdflatex")
        extra_args = kwargs.get("extra_args", [])
        
        validation_result = self.validate_parameters(kwargs)
        if validation_result.status == ExecutionStatus.ERROR:
            return validation_result
        
        try:
            full_path = self._get_full_path(filepath)
            
            # Preprocess the LaTeX file before compilation
            preprocessing_result = self._preprocess_latex_file(full_path)
            if preprocessing_result.status == ExecutionStatus.ERROR:
                return preprocessing_result
            
            # Check for syntax issues with linter
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            warnings = LaTeXLinter.lint_latex_content(content)
            
            # Compile the preprocessed file
            result = self.compiler.compile_latex(filepath, engine, extra_args)
            
            # Add preprocessing info to result
            if warnings:
                warning_text = "\n--- LINTER WARNINGS ---\n" + "\n".join(warnings)
                if result.status == ExecutionStatus.SUCCESS:
                    result = ToolExecutionResult.success(
                        result.message + "\n" + warning_text,
                        result.details
                    )
                else:
                    result = ToolExecutionResult.error(
                        result.message,
                        result.details + "\n" + warning_text
                    )
            
            return result
            
        except Exception as e:
            return ToolExecutionResult.error(
                f"LaTeX compilation failed: {str(e)}",
                f"Error compiling {filepath} with {engine}: {str(e)}"
            )
    
    def _preprocess_latex_file(self, filepath: str) -> ToolExecutionResult:
        """Preprocess LaTeX file by removing quotes and ensuring mathematical packages"""
        try:
            # Read original content
            with open(filepath, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # Apply preprocessing
            processed_content = self._preprocess_content(original_content)
            
            # Write back if changed
            if original_content != processed_content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(processed_content)
                
                changes = []
                if self._had_quotes_removed(original_content, processed_content):
                    changes.append("quotes removed")
                if self._had_packages_enhanced(original_content, processed_content):
                    changes.append("packages enhanced")
                
                return ToolExecutionResult.success(
                    f"LaTeX file preprocessed: {' and '.join(changes)}",
                    f"Applied preprocessing to {os.path.basename(filepath)}"
                )
            else:
                return ToolExecutionResult.success(
                    "No preprocessing needed",
                    f"File {os.path.basename(filepath)} was already clean"
                )
                
        except Exception as e:
            return ToolExecutionResult.error(
                f"Preprocessing failed: {str(e)}",
                f"Error preprocessing {filepath}: {str(e)}"
            )
    
    def _preprocess_content(self, content: str) -> str:
        """Preprocess content by removing quotes and ensuring mathematical packages"""
        if not content:
            return content
        
        # Step 1: Remove unwanted quotes from beginning and end
        cleaned_content = self._remove_unwanted_quotes(content)
        
        # Step 2: Ensure mathematical packages are included
        enhanced_content = self._ensure_mathematical_packages(cleaned_content)
        
        return enhanced_content
    
    def _remove_unwanted_quotes(self, content: str) -> str:
        """Remove unwanted quotes from beginning and end of content"""
        if not content:
            return content
        
        # Remove different types of quotes
        quote_chars = ["'", '"', '`']
        
        for quote_char in quote_chars:
            # Remove from beginning
            while content.startswith(quote_char):
                content = content[1:]
            
            # Remove from end
            while content.endswith(quote_char):
                content = content[:-1]
        
        return content.strip()
    
    def _ensure_mathematical_packages(self, content: str) -> str:
        """Ensure necessary mathematical packages are included"""
        if not content or '\\documentclass' not in content:
            return content
        
        required_packages = [
            'amsmath', 'amsfonts', 'amssymb', 'amsthm', 
            'mathtools', 'graphicx', 'geometry'
        ]
        
        lines = content.split('\n')
        documentclass_idx = -1
        
        # Find documentclass line
        for i, line in enumerate(lines):
            if '\\documentclass' in line:
                documentclass_idx = i
                break
        
        if documentclass_idx == -1:
            return content
        
        # Check which packages are already included
        existing_packages = set()
        for line in lines:
            if '\\usepackage' in line:
                # Extract package name
                match = re.search(r'\\usepackage(?:\[[^\]]*\])?\{([^}]+)\}', line)
                if match:
                    existing_packages.add(match.group(1))
        
        # Add missing packages after documentclass
        insert_idx = documentclass_idx + 1
        new_packages = []
        
        for package in required_packages:
            if package not in existing_packages:
                new_packages.append(f'\\usepackage{{{package}}}')
        
        if new_packages:
            # Insert new packages after documentclass
            lines[insert_idx:insert_idx] = new_packages
        
        return '\n'.join(lines)
    
    def _had_quotes_removed(self, original: str, processed: str) -> bool:
        """Check if quotes were removed during processing"""
        if len(original) != len(processed):
            quote_chars = ["'", '"', '`']
            for quote_char in quote_chars:
                if (original.startswith(quote_char) or original.endswith(quote_char)):
                    return True
        return False
    
    def _had_packages_enhanced(self, original: str, processed: str) -> bool:
        """Check if mathematical packages were added"""
        original_packages = original.count('\\usepackage')
        processed_packages = processed.count('\\usepackage')
        return processed_packages > original_packages 