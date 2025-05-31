"""
Unified LaTeX Tool
Comprehensive LaTeX document creation and compilation with flexible language support.
Reports compilation errors without automatic fixes - lets LLM decide how to resolve issues.
"""

import os
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
from hwagent.core.base_tool import BaseTool
from hwagent.core.models import ToolExecutionResult
from hwagent.core.constants import Constants


class LaTeXErrorReporter:
    """Reports LaTeX compilation errors without attempting fixes"""
    
    @staticmethod
    def parse_compilation_output(stdout: str, stderr: str, return_code: int) -> Dict[str, Any]:
        """Parse LaTeX compilation output and extract detailed error information"""
        
        # Combine output for analysis
        full_output = f"{stdout}\n{stderr}" if stderr else stdout
        
        errors = []
        warnings = []
        missing_files = []
        syntax_issues = []
        
        # Extract errors and warnings with more precision
        lines = full_output.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # LaTeX error pattern with detailed parsing
            if line.startswith('!'):
                error_info = LaTeXErrorReporter._parse_detailed_error(lines, i)
                if error_info:
                    errors.append(error_info)
                    i += error_info.get('lines_consumed', 1)
                else:
                    i += 1
            
            # File not found errors
            elif 'File `' in line and 'not found' in line:
                file_match = re.search(r"File `([^']+)' not found", line)
                if file_match:
                    missing_files.append({
                        'type': 'missing_file',
                        'filename': file_match.group(1),
                        'message': line.strip()
                    })
                i += 1
            
            # Package not found
            elif 'Package' in line and 'not found' in line:
                pkg_match = re.search(r"Package ([^\s]+) not found", line) 
                if pkg_match:
                    missing_files.append({
                        'type': 'missing_package', 
                        'package': pkg_match.group(1),
                        'message': line.strip()
                    })
                i += 1
            
            # Undefined control sequence
            elif 'Undefined control sequence' in line:
                # Try to get the next line for more context
                context = lines[i+1].strip() if i+1 < len(lines) else ""
                command_match = re.search(r'\\([a-zA-Z]+)', context)
                syntax_issues.append({
                    'type': 'undefined_command',
                    'command': command_match.group(0) if command_match else 'unknown',
                    'message': line.strip(),
                    'context': context
                })
                i += 1
            
            # Cyrillic encoding errors (NEW)
            elif ('unavailable in encoding OT1' in line or 
                  'CYRT unavailable' in line or 
                  'encoding OT1' in line and 'unavailable' in line):
                # Look for the specific command or character causing the issue
                next_lines = []
                for j in range(i+1, min(i+4, len(lines))):
                    if j < len(lines):
                        next_lines.append(lines[j].strip())
                
                # Find the problematic command
                problem_cmd = 'unknown'
                for next_line in next_lines:
                    cmd_match = re.search(r'\\([A-Z]{2,})', next_line)
                    if cmd_match:
                        problem_cmd = cmd_match.group(0)
                        break
                
                syntax_issues.append({
                    'type': 'cyrillic_encoding_error',
                    'encoding': 'OT1',
                    'problem_command': problem_cmd,
                    'message': line.strip(),
                    'context': next_lines,
                    'solution_hint': 'Need T2A fontenc package for Cyrillic support'
                })
                i += 1
            
            # Math mode errors
            elif 'Missing $' in line or 'Extra $' in line:
                syntax_issues.append({
                    'type': 'math_mode_error',
                    'message': line.strip()
                })
                i += 1
            
            # Missing brace errors
            elif 'Missing }' in line or 'Missing {' in line or 'Runaway argument' in line:
                syntax_issues.append({
                    'type': 'brace_error',
                    'message': line.strip()
                })
                i += 1
            
            # Warnings
            elif any(keyword in line for keyword in ['Warning:', 'warning:', 'Overfull', 'Underfull']):
                warnings.append({
                    'type': 'warning',
                    'message': line.strip()
                })
                i += 1
            
            else:
                i += 1
        
        # Categorize compilation result
        compilation_successful = (return_code == 0 and 
                                len([e for e in errors if e.get('severity') != 'warning']) == 0)
        
        return {
            'compilation_successful': compilation_successful,
            'return_code': return_code,
            'errors': errors,
            'warnings': warnings, 
            'missing_files': missing_files,
            'syntax_issues': syntax_issues,
            'total_issues': len(errors) + len(missing_files) + len(syntax_issues),
            'raw_output': {
                'stdout': stdout,
                'stderr': stderr
            }
        }
    
    @staticmethod
    def _parse_detailed_error(lines: list[str], start_idx: int) -> Dict[str, Any] | None:
        """Parse a detailed LaTeX error starting at the given line"""
        if start_idx >= len(lines):
            return None
        
        error_line = lines[start_idx].strip()
        if not error_line.startswith('!'):
            return None
        
        error_info = {
            'type': 'latex_error',
            'severity': 'error',
            'message': error_line[1:].strip(),
            'line_number': None,
            'source_line': None,
            'context': [],
            'lines_consumed': 1
        }
        
        # Parse following lines for context
        for i in range(start_idx + 1, min(start_idx + 8, len(lines))):
            line = lines[i].strip()
            
            # Line number and source information
            if line.startswith('l.'):
                line_match = re.search(r'l\.(\d+)\s*(.*)', line)
                if line_match:
                    error_info['line_number'] = int(line_match.group(1))
                    error_info['source_line'] = line_match.group(2).strip()
                    error_info['context'].append(f"Line {line_match.group(1)}: {line_match.group(2)}")
                    error_info['lines_consumed'] = i - start_idx + 1
            
            # Additional context
            elif line and not line.startswith(('Type H', 'Enter file', ' ...', '?', '<*>')):
                if len(error_info['context']) < 3:
                    error_info['context'].append(line)
                    error_info['lines_consumed'] = i - start_idx + 1
            
            # Stop conditions
            elif not line or line.startswith('?'):
                break
        
        return error_info


class LaTeXTemplateGenerator:
    """Generates LaTeX document templates for different task types and languages"""
    
    @staticmethod
    def get_template(task_type: str, language: str, title: str = "Document") -> str:
        """Generate LaTeX template based on task type and language"""
        
        # Base packages for all documents
        base_packages = [
            "\\usepackage[utf8]{inputenc}",
            "\\usepackage{amsmath,amssymb,amsfonts}",
            "\\usepackage{geometry}",
            "\\usepackage{hyperref}",
            "\\usepackage{graphicx}",
            "\\usepackage{xcolor}"
        ]
        
        # Language-specific packages
        language_packages = LaTeXTemplateGenerator._get_language_packages(language)
        
        # Task-specific packages
        task_packages = LaTeXTemplateGenerator._get_task_packages(task_type)
        
        # Combine all packages
        all_packages = base_packages + language_packages + task_packages
        
        # Generate document structure
        sections = LaTeXTemplateGenerator._get_default_sections(task_type, language)
        
        template = f"""\\documentclass[12pt,a4paper]{{article}}

{chr(10).join(all_packages)}

\\geometry{{a4paper, margin=1in}}

{LaTeXTemplateGenerator._get_code_styling(task_type)}

\\title{{{title}}}
\\author{{AI Technical Assistant}}
\\date{{\\today}}

\\begin{{document}}
\\maketitle
\\tableofcontents
\\newpage

{chr(10).join(sections)}

\\end{{document}}"""
        
        return template
    
    @staticmethod
    def _get_language_packages(language: str) -> list[str]:
        """Get basic language packages - LLM can specify additional packages as needed"""
        packages = []
        
        # Basic font encoding (T1 is universal for most European languages)
        packages.append("\\usepackage[T1]{fontenc}")
        
        # Babel for language support (LLM specifies the language)
        if language and language.lower() != 'none':
            packages.append(f"\\usepackage[{language.lower()}]{{babel}}")
        
        return packages
    
    @staticmethod
    def _get_task_packages(task_type: str) -> List[str]:
        """Get task-specific packages"""
        if task_type in ['math', 'physics']:
            return [
                "\\usepackage{algorithm}",
                "\\usepackage{algorithmic}",
                "\\usepackage{tikz}",
                "\\usepackage{pgfplots}"
            ]
        elif task_type in ['programming', 'computer_science']:
            return [
                "\\usepackage{listings}",
                "\\usepackage{algorithm}",
                "\\usepackage{algorithmic}"
            ]
        elif task_type in ['analysis', 'statistics']:
            return [
                "\\usepackage{booktabs}",
                "\\usepackage{array}",
                "\\usepackage{longtable}",
                "\\usepackage{multirow}"
            ]
        else:
            return ["\\usepackage{listings}"]
    
    @staticmethod
    def _get_code_styling(task_type: str) -> str:
        """Get code styling configuration if needed"""
        if task_type in ['programming', 'computer_science', 'math']:
            return """% Code styling configuration
\\definecolor{codegray}{rgb}{0.5,0.5,0.5}
\\definecolor{codepurple}{rgb}{0.58,0,0.82}
\\definecolor{backcolour}{rgb}{0.95,0.95,0.92}

\\lstdefinestyle{mystyle}{
    backgroundcolor=\\color{backcolour},   
    commentstyle=\\color{codegray},
    keywordstyle=\\color{blue},
    numberstyle=\\tiny\\color{codegray},
    stringstyle=\\color{codepurple},
    basicstyle=\\ttfamily\\footnotesize,
    breakatwhitespace=false,         
    breaklines=true,                 
    captionpos=b,                    
    keepspaces=true,                 
    numbers=left,                    
    numbersep=5pt,                  
    showspaces=false,                
    showstringspaces=false,
    showtabs=false,                  
    tabsize=2
}

\\lstset{style=mystyle}
"""
        return ""
    
    @staticmethod
    def _get_default_sections(task_type: str, language: str) -> List[str]:
        """Get default sections for template - LLM can customize as needed"""
        
        # Basic section templates that LLM can translate/modify
        section_templates = {
            'math': [
                "\\section{Problem Statement}\n% TODO: Describe the problem\n",
                "\\section{Methodology}\n% TODO: Describe solution approach\n",
                "\\section{Solution}\n% TODO: Step-by-step solution\n",
                "\\section{Verification}\n% TODO: Verify results\n",
                "\\section{Conclusion}\n% TODO: Conclusions\n"
            ],
            'programming': [
                "\\section{Problem Description}\n% TODO: Describe programming task\n",
                "\\section{Algorithm}\n% TODO: Describe solution algorithm\n",
                "\\section{Implementation}\n% TODO: Code and explanations\n",
                "\\section{Testing}\n% TODO: Tests and results\n",
                "\\section{Conclusion}\n% TODO: Conclusions\n"
            ],
            'analysis': [
                "\\section{Introduction}\n% TODO: Research question\n",
                "\\section{Methodology}\n% TODO: Analysis methods\n",
                "\\section{Results}\n% TODO: Present findings\n",
                "\\section{Discussion}\n% TODO: Interpret results\n",
                "\\section{Conclusion}\n% TODO: Conclusions and recommendations\n"
            ],
            'general': [
                "\\section{Introduction}\n% TODO: Introduction\n",
                "\\section{Main Content}\n% TODO: Main content\n",
                "\\section{Conclusion}\n% TODO: Conclusion\n"
            ]
        }
        
        return section_templates.get(task_type.lower(), section_templates['general'])


class LaTeXContentProcessor:
    """Handles LaTeX content preprocessing including quote removal"""
    
    @staticmethod
    def clean_content(content: str) -> str:
        """Remove unwanted quotes from beginning and end of content"""
        if not content:
            return content
        
        # Remove single quotes (') from beginning and end
        # Can be 1, 2, 3 or more quotes
        content = LaTeXContentProcessor._remove_quotes_pattern(content, "'")
        
        # Remove double quotes (") from beginning and end  
        content = LaTeXContentProcessor._remove_quotes_pattern(content, '"')
        
        # Remove backticks (`) from beginning and end
        content = LaTeXContentProcessor._remove_quotes_pattern(content, '`')
        
        return content.strip()
    
    @staticmethod
    def _remove_quotes_pattern(content: str, quote_char: str) -> str:
        """Remove specific quote character from beginning and end"""
        # Remove from beginning
        while content.startswith(quote_char):
            content = content[1:]
        
        # Remove from end
        while content.endswith(quote_char):
            content = content[:-1]
        
        return content
    
    @staticmethod
    def ensure_mathematical_packages(content: str) -> str:
        """Ensure all necessary mathematical packages are included"""
        
        # Required mathematical packages
        required_math_packages = [
            r'\usepackage{amsmath}',
            r'\usepackage{amsfonts}', 
            r'\usepackage{amssymb}',
            r'\usepackage{amsthm}',
            r'\usepackage{mathtools}',
            r'\usepackage{graphicx}',
            r'\usepackage{geometry}'
        ]
        
        # Find documentclass line
        documentclass_match = re.search(r'\\documentclass.*?\{.*?\}', content)
        if not documentclass_match:
            return content
        
        # Check which packages are already included
        existing_packages = set()
        for package in required_math_packages:
            if package in content:
                existing_packages.add(package)
        
        # Add missing packages after documentclass
        missing_packages = [pkg for pkg in required_math_packages if pkg not in existing_packages]
        
        if missing_packages:
            insert_pos = documentclass_match.end()
            packages_block = '\n' + '\n'.join(missing_packages) + '\n'
            content = content[:insert_pos] + packages_block + content[insert_pos:]
        
        return content


class UnifiedLaTeXTool(BaseTool):
    """Unified LaTeX document creation and compilation tool with enhanced features"""
    
    def __init__(self, tmp_directory: str = Constants.DEFAULT_TMP_DIRECTORY):
        super().__init__(tmp_directory)
        self.compiler_timeout = 30
        self.max_retry_attempts = 3
    
    @property
    def name(self) -> str:
        return "unified_latex"
    
    @property
    def description(self) -> str:
        return """Comprehensive LaTeX document creation and compilation tool with:
- Automatic quote removal from content
- Enhanced mathematical package support
- Multiple compilation attempts with error recovery
- Multi-language template generation
- Flexible compilation engine selection
- Detailed error reporting and analysis

Operations:
- create: Create document from content with automatic preprocessing
- template: Generate language-specific template
- compile: Compile existing LaTeX document to PDF

Features:
- Removes unwanted quotes from content beginning/end
- Automatically includes required mathematical packages
- Retry compilation on failure with fixes
- Support for English/Russian/multilingual documents
- Safe compilation with batch mode and timeouts"""
    
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["create", "template", "compile"],
                    "description": "Operation to perform: create document, generate template, or compile existing file"
                },
                "filepath": {
                    "type": "string",
                    "description": "Path to LaTeX file (required for all operations)"
                },
                "content": {
                    "type": "string",
                    "description": "LaTeX content (required for 'create' operation)"
                },
                "title": {
                    "type": "string",
                    "description": "Document title (optional, default: 'Document')"
                },
                "language": {
                    "type": "string",
                    "description": "Document language (any language supported by babel, e.g., 'english', 'russian', 'german', 'french', 'spanish', 'chinese', 'japanese', etc.)",
                    "default": "english"
                },
                "task_type": {
                    "type": "string",
                    "enum": ["math", "programming", "analysis", "general"],
                    "description": "Type of document task for appropriate template and packages"
                },
                "engine": {
                    "type": "string",
                    "enum": ["pdflatex", "xelatex", "lualatex"],
                    "description": "LaTeX compilation engine (default: pdflatex)"
                }
            },
            "required": ["operation", "filepath"]
        }
    
    def _execute_impl(self, **kwargs) -> ToolExecutionResult:
        """Execute the specified LaTeX operation"""
        operation = kwargs["operation"]
        
        if operation == "create":
            return self._create_document(**kwargs)
        elif operation == "template":
            return self._generate_template(**kwargs)
        elif operation == "compile":
            return self._compile_document(**kwargs)
        else:
            return ToolExecutionResult.error(
                f"Unknown operation: {operation}",
                f"Supported operations: create, template, compile"
            )
    
    def _create_document(self, **kwargs) -> ToolExecutionResult:
        """Create LaTeX document from provided content with preprocessing"""
        filepath = kwargs["filepath"]
        content = kwargs["content"]
        compile_after = kwargs.get("compile", True)
        engine = kwargs.get("engine", "pdflatex")
        
        # Ensure .tex extension
        if not filepath.endswith('.tex'):
            filepath += '.tex'
        
        try:
            # Preprocess content: remove quotes and ensure math packages
            cleaned_content = LaTeXContentProcessor.clean_content(content)
            enhanced_content = LaTeXContentProcessor.ensure_mathematical_packages(cleaned_content)
            
            # Write content to file
            full_path = self._get_full_path(filepath)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(enhanced_content)
            
            result_data = {
                "operation": "create",
                "tex_file": filepath,
                "file_size": len(enhanced_content.encode('utf-8')),
                "content_processed": True,
                "quotes_removed": content != cleaned_content,
                "math_packages_added": cleaned_content != enhanced_content,
                "compiled": False,
                "pdf_file": None
            }
            
            message = f"LaTeX document created: {filepath} ({result_data['file_size']} bytes)"
            if result_data["quotes_removed"]:
                message += " [quotes removed]"
            if result_data["math_packages_added"]:
                message += " [math packages added]"
            
            # Compile if requested with retry logic
            if compile_after:
                compile_result = self._compile_with_retry(filepath, engine)
                result_data.update(compile_result)
                
                if compile_result["compilation_successful"]:
                    message += f" and compiled successfully to PDF"
                else:
                    message += " (compilation failed after retries - see error details)"
            
            return ToolExecutionResult.success(message, self._format_result(result_data), result_data)
            
        except Exception as e:
            return ToolExecutionResult.error(
                f"Failed to create LaTeX document: {str(e)}",
                f"Error creating {filepath}: {str(e)}"
            )
    
    def _generate_template(self, **kwargs) -> ToolExecutionResult:
        """Generate LaTeX template based on task type and language"""
        filepath = kwargs["filepath"]
        task_type = kwargs.get("task_type", "general")
        language = kwargs.get("language", "english")
        title = kwargs.get("title", "Document")
        compile_after = kwargs.get("compile", True)
        engine = kwargs.get("engine", "pdflatex")
        
        # Ensure .tex extension
        if not filepath.endswith('.tex'):
            filepath += '.tex'
        
        try:
            # Generate template content
            template_content = LaTeXTemplateGenerator.get_template(task_type, language, title)
            
            # Write template to file
            full_path = self._get_full_path(filepath)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(template_content)
            
            result_data = {
                "operation": "template",
                "tex_file": filepath,
                "task_type": task_type,
                "language": language,
                "title": title,
                "file_size": len(template_content.encode('utf-8')),
                "compiled": False,
                "pdf_file": None
            }
            
            message = f"LaTeX template generated: {filepath} ({task_type}/{language})"
            
            # Compile if requested
            if compile_after:
                compile_result = self._perform_compilation(filepath, engine)
                result_data.update(compile_result)
                
                if compile_result["compilation_successful"]:
                    message += " and compiled successfully to PDF"
                else:
                    message += " (compilation failed - see error details)"
            
            return ToolExecutionResult.success(message, self._format_result(result_data), result_data)
            
        except Exception as e:
            return ToolExecutionResult.error(
                f"Failed to generate LaTeX template: {str(e)}",
                f"Error generating template {filepath}: {str(e)}"
            )
    
    def _compile_document(self, **kwargs) -> ToolExecutionResult:
        """Compile existing LaTeX document to PDF with retry logic"""
        filepath = kwargs["filepath"]
        engine = kwargs.get("engine", "pdflatex")
        
        # Ensure .tex extension
        if not filepath.endswith('.tex'):
            filepath += '.tex'
        
        try:
            # Check if file exists
            full_path = self._get_full_path(filepath)
            if not os.path.exists(full_path):
                return ToolExecutionResult.error(
                    f"LaTeX file not found: {filepath}",
                    f"File {filepath} does not exist in the working directory"
                )
            
            # Preprocess existing file for better compilation
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Clean and enhance content
            cleaned_content = LaTeXContentProcessor.clean_content(content)
            enhanced_content = LaTeXContentProcessor.ensure_mathematical_packages(cleaned_content)
            
            # Write back if changed
            if enhanced_content != content:
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(enhanced_content)
            
            # Perform compilation with retry
            compile_result = self._compile_with_retry(filepath, engine)
            
            result_data = {
                "operation": "compile",
                "tex_file": filepath,
                "engine": engine,
                "content_enhanced": enhanced_content != content,
                **compile_result
            }
            
            if compile_result["compilation_successful"]:
                message = f"LaTeX compilation successful: {filepath} -> {compile_result['pdf_file']}"
            else:
                message = f"LaTeX compilation failed: {filepath} (see error details after {compile_result.get('retry_attempts', 1)} attempts)"
            
            return ToolExecutionResult.success(message, self._format_result(result_data), result_data)
            
        except Exception as e:
            return ToolExecutionResult.error(
                f"Failed to compile LaTeX document: {str(e)}",
                f"Error compiling {filepath}: {str(e)}"
            )
    
    def _compile_with_retry(self, filepath: str, engine: str) -> Dict[str, Any]:
        """Compile document with automatic retry and basic fixes"""
        
        retry_attempts = 0
        last_result = None
        
        while retry_attempts < self.max_retry_attempts:
            retry_attempts += 1
            
            # Perform compilation
            compile_result = self._perform_compilation(filepath, engine)
            last_result = compile_result
            
            # If successful, return immediately
            if compile_result["compilation_successful"]:
                compile_result["retry_attempts"] = retry_attempts
                return compile_result
            
            # If failed and not last attempt, try basic fixes
            if retry_attempts < self.max_retry_attempts:
                try:
                    self._apply_basic_fixes(filepath, compile_result)
                except Exception as e:
                    # If fixing fails, continue with next attempt
                    pass
        
        # All attempts failed
        last_result["retry_attempts"] = retry_attempts
        last_result["all_attempts_failed"] = True
        return last_result
    
    def _apply_basic_fixes(self, filepath: str, compile_result: Dict[str, Any]) -> None:
        """Apply basic fixes based on compilation errors"""
        
        full_path = self._get_full_path(filepath)
        
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        fixes_applied = []
        
        # Fix 1: Add missing packages based on errors
        for error in compile_result.get("errors", []):
            if "undefined control sequence" in error.get("message", "").lower():
                # Add common packages that might be missing
                if "\\bm{" in content and "\\usepackage{bm}" not in content:
                    content = self._add_package_after_documentclass(content, "\\usepackage{bm}")
                    fixes_applied.append("added bm package")
                
                if "\\boldsymbol{" in content and "\\usepackage{amsmath}" not in content:
                    content = self._add_package_after_documentclass(content, "\\usepackage{amsmath}")
                    fixes_applied.append("added amsmath package")
        
        # Fix 2: Encoding issues for Cyrillic
        for error in compile_result.get("syntax_issues", []):
            if error.get("type") == "cyrillic_encoding_error":
                if "\\usepackage[T2A]{fontenc}" not in content:
                    content = self._add_package_after_documentclass(content, "\\usepackage[T2A]{fontenc}")
                    fixes_applied.append("added T2A fontenc")
                if "\\usepackage[russian]{babel}" not in content:
                    content = self._add_package_after_documentclass(content, "\\usepackage[russian]{babel}")
                    fixes_applied.append("added russian babel")
        
        # Fix 3: Double backslash issues
        if "\\\\\\\\" in content:  # Four backslashes
            content = content.replace("\\\\\\\\", "\\\\")
            fixes_applied.append("fixed quadruple backslashes")
        
        # Write back if any fixes were applied
        if content != original_content and fixes_applied:
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
    
    def _add_package_after_documentclass(self, content: str, package: str) -> str:
        """Add a package line after documentclass"""
        documentclass_match = re.search(r'\\documentclass.*?\{.*?\}', content)
        if documentclass_match:
            insert_pos = documentclass_match.end()
            return content[:insert_pos] + '\n' + package + content[insert_pos:]
        return content
    
    def _perform_compilation(self, filepath: str, engine: str) -> Dict[str, Any]:
        """Perform LaTeX compilation and return results"""
        full_path = self._get_full_path(filepath)
        directory = os.path.dirname(full_path)
        tex_filename = os.path.basename(filepath)
        pdf_filename = tex_filename.replace('.tex', '.pdf')
        
        # Compilation command
        cmd = [
            engine,
            '-interaction=batchmode',
            '-file-line-error',
            '-synctex=1',
            '-output-directory', directory,
            tex_filename
        ]
        
        try:
            # Run compilation
            result = subprocess.run(
                cmd,
                cwd=directory,
                capture_output=True,
                text=True,
                timeout=self.compiler_timeout,
                input=''
            )
            
            # Parse compilation results
            compilation_info = LaTeXErrorReporter.parse_compilation_output(
                result.stdout, result.stderr, result.returncode
            )
            
            # Check for PDF output
            pdf_path = os.path.join(directory, pdf_filename)
            pdf_exists = os.path.exists(pdf_path)
            pdf_size = os.path.getsize(pdf_path) if pdf_exists else 0
            
            return {
                "compilation_successful": compilation_info["compilation_successful"] and pdf_exists,
                "pdf_file": pdf_filename if pdf_exists else None,
                "pdf_size": pdf_size,
                "engine": engine,
                "errors": compilation_info["errors"],
                "warnings": compilation_info["warnings"],
                "raw_output": compilation_info["raw_output"]
            }
            
        except subprocess.TimeoutExpired:
            return {
                "compilation_successful": False,
                "pdf_file": None,
                "pdf_size": 0,
                "engine": engine,
                "errors": [{"type": "timeout", "message": f"Compilation timed out after {self.compiler_timeout} seconds"}],
                "warnings": [],
                "raw_output": {"stdout": "", "stderr": "Timeout"}
            }
        except Exception as e:
            return {
                "compilation_successful": False,
                "pdf_file": None,
                "pdf_size": 0,
                "engine": engine,
                "errors": [{"type": "system_error", "message": str(e)}],
                "warnings": [],
                "raw_output": {"stdout": "", "stderr": str(e)}
            }
    
    def _format_result(self, data: Dict[str, Any]) -> str:
        """Format operation result with detailed error information"""
        lines = []
        
        # Operation info
        lines.append(f"Operation: {data['operation']}")
        lines.append(f"LaTeX file: {data['tex_file']}")
        
        if 'task_type' in data:
            lines.append(f"Task type: {data['task_type']}")
        if 'language' in data:
            lines.append(f"Language: {data['language']}")
        if 'file_size' in data:
            lines.append(f"File size: {data['file_size']} bytes")
        
        # Compilation results
        if 'compilation_successful' in data:
            if data['compilation_successful']:
                lines.append(f"✅ Compilation successful")
                if data.get('pdf_file'):
                    lines.append(f"PDF file: {data['pdf_file']} ({data.get('pdf_size', 0)} bytes)")
            else:
                lines.append(f"❌ Compilation failed")
                
                # Report detailed errors
                errors = data.get('errors', [])
                if errors:
                    lines.append(f"\n🔴 CRITICAL ERRORS ({len(errors)}):")
                    for i, error in enumerate(errors[:8], 1):
                        lines.append(f"{i}. {error.get('message', '')}")
                        if error.get('line_number'):
                            lines.append(f"   📍 Line: {error['line_number']}")
                        if error.get('source_line'):
                            lines.append(f"   📄 Source: {error['source_line']}")
                        if error.get('context'):
                            context_str = ' | '.join(error['context'][:2])
                            lines.append(f"   🔍 Context: {context_str}")
                
                # Report missing files/packages
                missing_files = data.get('missing_files', [])
                if missing_files:
                    lines.append(f"\n📦 MISSING FILES/PACKAGES ({len(missing_files)}):")
                    for missing in missing_files[:5]:
                        if missing.get('type') == 'missing_package':
                            lines.append(f"• Package: {missing.get('package', 'unknown')}")
                        else:
                            lines.append(f"• File: {missing.get('filename', 'unknown')}")
                
                # Report syntax issues
                syntax_issues = data.get('syntax_issues', [])
                if syntax_issues:
                    lines.append(f"\n⚠️ SYNTAX ISSUES ({len(syntax_issues)}):")
                    for issue in syntax_issues[:5]:
                        issue_type = issue.get('type', 'unknown')
                        if issue_type == 'undefined_command':
                            lines.append(f"• Undefined command: {issue.get('command', '')}")
                        elif issue_type == 'math_mode_error':
                            lines.append(f"• Math mode error: {issue.get('message', '')}")
                        elif issue_type == 'brace_error':
                            lines.append(f"• Brace error: {issue.get('message', '')}")
                        else:
                            lines.append(f"• {issue.get('message', '')}")
                
                # Report warnings (limited)
                warnings = data.get('warnings', [])
                if warnings and len(warnings) <= 5:
                    lines.append(f"\n💡 WARNINGS ({len(warnings)}):")
                    for warning in warnings[:3]:
                        lines.append(f"• {warning.get('message', '')}")
                
                # Summary
                total_issues = data.get('total_issues', 0)
                if total_issues > 0:
                    lines.append(f"\n📊 Total issues: {total_issues}")
                    
                    # Recommendations
                    lines.append("\n🔧 RECOMMENDATIONS:")
                    if missing_files:
                        lines.append("• Install missing packages or remove \\usepackage statements")
                    if syntax_issues:
                        lines.append("• Fix syntax errors (missing braces, undefined commands)")
                    if errors:
                        lines.append("• Review and fix critical LaTeX errors listed above")
        
        return '\n'.join(lines)


# Export the tool
def get_tool():
    """Factory function to get the tool instance"""
    return UnifiedLaTeXTool() 