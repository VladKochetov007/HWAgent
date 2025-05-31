"""
Simple LaTeX Tool
Clean and reliable tool for creating and compiling LaTeX documents.
"""

import os
import re
import subprocess
from typing import Dict, Any, Optional
from hwagent.core.base_tool import FileOperationTool
from hwagent.core.models import ToolExecutionResult, ExecutionStatus
from hwagent.core.constants import Constants


class SimpleLaTeXTool(FileOperationTool):
    """
    Simple LaTeX tool for creating and compiling documents.
    Focuses on reliability over automatic "intelligence".
    """
    
    @property
    def name(self) -> str:
        return "simple_latex"
    
    @property
    def description(self) -> str:
        return r"""Create and compile LaTeX documents with enhanced error handling.
        
        This tool creates LaTeX files and compiles them to PDF using batchmode to prevent 
        hanging on user input. Provides detailed error analysis for LLM processing.
        
        Parameters:
        - filepath: Name of the LaTeX file (will be created in current directory)
        - content: Complete LaTeX document content (including \documentclass and \begin{document})
        - compile: Whether to compile to PDF (default: true)
        
        IMPORTANT: 
        - Content should be complete LaTeX document starting with \documentclass
        - Use proper LaTeX escaping for special characters
        - For Russian/Cyrillic: include proper babel and fontenc packages
        - If compilation fails, the tool provides structured error analysis
        - No user interaction required - automatic error handling prevents hanging
        - Use single backslashes in LaTeX commands (e.g., \section{} not \\section{})"""
    
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "filepath": {
                    "type": "string",
                    "description": "Name of LaTeX file (e.g., 'document.tex')"
                },
                "content": {
                    "type": "string",
                    "description": "Complete LaTeX document content"
                },
                "compile": {
                    "type": "boolean",
                    "description": "Whether to compile to PDF",
                    "default": True
                }
            },
            "required": ["filepath", "content"]
        }
    
    def _execute_impl(self, **kwargs) -> ToolExecutionResult:
        """Execute LaTeX document creation and compilation"""
        
        filepath = kwargs["filepath"]
        content = kwargs["content"]
        compile_pdf = kwargs.get("compile", True)
        
        try:
            # Ensure .tex extension
            if not filepath.endswith('.tex'):
                filepath += '.tex'
            
            # Write file directly without modifications
            full_path = self._get_full_path(filepath)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            result_data = {
                "tex_file": filepath,
                "compiled": False,
                "pdf_file": None,
                "pdf_size": 0,
                "compilation_log": ""
            }
            
            message = f"LaTeX document created: {filepath}"
            
            # Compile if requested
            if compile_pdf:
                pdf_result = self._compile_pdf(filepath)
                result_data.update(pdf_result)
                
                if pdf_result["compiled"]:
                    message += f" and compiled to PDF ({pdf_result['pdf_size']} bytes)"
                else:
                    message += " (PDF compilation failed - see compilation_log)"
            
            details = self._format_details(result_data)
            
            return ToolExecutionResult.success(message, details, data=result_data)
            
        except Exception as e:
            return ToolExecutionResult.error(
                f"Failed to create LaTeX document: {str(e)}",
                f"Error processing {filepath}: {str(e)}"
            )
    
    def _compile_pdf(self, filepath: str) -> Dict[str, Any]:
        """Compile LaTeX file to PDF"""
        
        full_path = self._get_full_path(filepath)
        directory = os.path.dirname(full_path)
        tex_filename = os.path.basename(filepath)
        pdf_filename = tex_filename.replace('.tex', '.pdf')
        
        # Use pdflatex for compilation
        cmd = [
            'pdflatex',
            '-interaction=batchmode',
            '-file-line-error',
            '-synctex=1',
            '-output-directory', directory,
            tex_filename
        ]
        
        try:
            # Change to the directory containing the .tex file
            result = subprocess.run(
                cmd,
                cwd=directory,
                capture_output=True,
                text=True,
                timeout=30,
                input=''
            )
            
            pdf_path = os.path.join(directory, pdf_filename)
            pdf_size = 0
            
            if os.path.exists(pdf_path):
                pdf_size = os.path.getsize(pdf_path)
                compiled = True
                compilation_log = "✅ Compilation successful"
            else:
                compiled = False
                # Enhanced error parsing for LLM analysis
                error_analysis = self._analyze_latex_errors(result.stdout, result.stderr)
                compilation_log = f"❌ Compilation failed\n\n{error_analysis}"
            
            return {
                "compiled": compiled,
                "pdf_file": pdf_filename if compiled else None,
                "pdf_size": pdf_size,
                "compilation_log": compilation_log,
                "exit_code": result.returncode,
                "raw_stdout": result.stdout,
                "raw_stderr": result.stderr
            }
            
        except subprocess.TimeoutExpired:
            return {
                "compiled": False,
                "pdf_file": None,
                "pdf_size": 0,
                "compilation_log": "❌ Compilation timed out (30 seconds)",
                "exit_code": -1
            }
        except Exception as e:
            return {
                "compiled": False,
                "pdf_file": None,
                "pdf_size": 0,
                "compilation_log": f"❌ Compilation error: {str(e)}",
                "exit_code": -1
            }
    
    def _format_details(self, data: Dict[str, Any]) -> str:
        """Format result details"""
        
        details = [f"LaTeX file: {data['tex_file']}"]
        
        if data.get("compiled"):
            details.extend([
                f"PDF file: {data['pdf_file']}",
                f"PDF size: {data['pdf_size']} bytes",
                "✅ Compilation successful"
            ])
        else:
            details.append("❌ PDF compilation failed")
            if data.get("compilation_log"):
                details.append(f"Error log:\n{data['compilation_log']}")
        
        return "\n".join(details)

    def _analyze_latex_errors(self, stdout: str, stderr: str) -> str:
        """Analyze LaTeX compilation errors for LLM processing"""
        
        # Try to read the .log file for more detailed error information
        log_content = ""
        try:
            # Look for .log file in the directory
            for filename in os.listdir(os.path.dirname(self._get_full_path("dummy"))):
                if filename.endswith('.log'):
                    log_path = os.path.join(os.path.dirname(self._get_full_path("dummy")), filename)
                    with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                        log_content = f.read()
                    break
        except:
            pass
        
        # Combine all output sources
        full_output = f"{stdout}\n{stderr}\n{log_content}".strip()
        
        if not full_output:
            return "No compilation output available. Possible system-level error."
        
        errors = []
        warnings = []
        missing_packages = []
        syntax_errors = []
        
        lines = full_output.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # LaTeX error detection patterns
            if line.startswith('!'):
                error_info = self._parse_latex_error(lines, i)
                if error_info:
                    errors.append(error_info)
                    i += error_info.get('lines_consumed', 1)
                else:
                    i += 1
            
            # Package errors
            elif 'File `' in line and 'not found' in line:
                package_match = re.search(r"File `([^']+)' not found", line)
                if package_match:
                    missing_packages.append(f"Missing file/package: {package_match.group(1)}")
                i += 1
            
            # LaTeX warnings
            elif any(keyword in line.lower() for keyword in ['warning:', 'overfull', 'underfull']):
                warning = self._parse_warning(line)
                if warning:
                    warnings.append(warning)
                i += 1
            
            # Undefined control sequence
            elif 'Undefined control sequence' in line:
                syntax_errors.append(f"Undefined command: {line}")
                i += 1
            
            # Missing $ inserted
            elif 'Missing $' in line:
                syntax_errors.append(f"Math mode error: {line}")
                i += 1
            
            # Runaway argument
            elif 'Runaway argument' in line:
                syntax_errors.append(f"Runaway argument (missing brace?): {line}")
                i += 1
            
            else:
                i += 1
        
        return self._format_error_analysis(errors, warnings, missing_packages, syntax_errors, len(lines))
    
    def _parse_latex_error(self, lines: list[str], start_idx: int) -> dict | None:
        """Parse a LaTeX error starting at the given line index"""
        if start_idx >= len(lines):
            return None
        
        error_line = lines[start_idx].strip()
        if not error_line.startswith('!'):
            return None
        
        error_info = {
            'type': 'LaTeX Error',
            'message': error_line[1:].strip(),
            'line_number': None,
            'context': [],
            'lines_consumed': 1
        }
        
        # Look for additional context in following lines
        for i in range(start_idx + 1, min(start_idx + 6, len(lines))):
            line = lines[i].strip()
            
            # Line number information
            if line.startswith('l.'):
                line_match = re.search(r'l\.(\d+)', line)
                if line_match:
                    error_info['line_number'] = int(line_match.group(1))
                    error_info['context'].append(line)
                    error_info['lines_consumed'] = i - start_idx + 1
            
            # Context information
            elif line and not line.startswith(('Type H', 'Enter file', ' ...', '?')):
                if len(error_info['context']) < 3:
                    error_info['context'].append(line)
                    error_info['lines_consumed'] = i - start_idx + 1
            
            # Stop at empty line or interactive prompt
            elif not line or line.startswith('?'):
                break
        
        return error_info
    
    def _parse_warning(self, line: str) -> str | None:
        """Parse LaTeX warning"""
        # Extract useful warning information
        if 'Warning:' in line:
            warning_match = re.search(r'Warning:\s*(.+)', line)
            if warning_match:
                return f"Warning: {warning_match.group(1)}"
        elif 'Overfull' in line:
            return f"Layout issue: {line}"
        elif 'Underfull' in line:
            return f"Layout issue: {line}"
        
        return line if line.strip() else None
    
    def _format_error_analysis(self, errors: list, warnings: list, missing_packages: list, 
                             syntax_errors: list, total_lines: int) -> str:
        """Format comprehensive error analysis"""
        
        analysis = ["=== DETAILED COMPILATION ANALYSIS ==="]
        
        # Critical errors first
        if errors:
            analysis.append(f"\n🔴 CRITICAL ERRORS ({len(errors)}):")
            for i, error in enumerate(errors[:10], 1):  # Limit to first 10 errors
                analysis.append(f"{i}. {error['type']}: {error['message']}")
                if error.get('line_number'):
                    analysis.append(f"   📍 Line {error['line_number']}")
                if error.get('context'):
                    analysis.append(f"   📄 Context: {' | '.join(error['context'][:2])}")
                analysis.append("")
        
        # Missing packages/files
        if missing_packages:
            analysis.append(f"📦 MISSING PACKAGES/FILES ({len(missing_packages)}):")
            for package in missing_packages[:5]:
                analysis.append(f"• {package}")
            analysis.append("")
        
        # Syntax errors
        if syntax_errors:
            analysis.append(f"⚠️ SYNTAX ERRORS ({len(syntax_errors)}):")
            for error in syntax_errors[:5]:
                analysis.append(f"• {error}")
            analysis.append("")
        
        # Warnings (only if not too many)
        if warnings and len(warnings) <= 8:
            analysis.append(f"💡 WARNINGS ({len(warnings)}):")
            for warning in warnings[:5]:
                analysis.append(f"• {warning}")
            analysis.append("")
        
        # Summary and recommendations
        analysis.append("=== SUMMARY & RECOMMENDATIONS ===")
        total_issues = len(errors) + len(missing_packages) + len(syntax_errors)
        analysis.append(f"📊 Total issues found: {total_issues}")
        analysis.append(f"📄 Log file lines processed: {total_lines}")
        
        if missing_packages:
            analysis.append("🔧 Action: Install missing packages or remove \\usepackage commands")
        if errors or syntax_errors:
            analysis.append("🔧 Action: Fix LaTeX syntax errors (missing braces, undefined commands)")
        if not errors and not missing_packages and not syntax_errors:
            analysis.append("🔧 Action: Check for system-level compilation issues")
        
        return "\n".join(analysis) 