"""
Smart LaTeX Generator Tool
Creates properly formatted LaTeX documents with intelligent content placement and error prevention.
"""

import re
import os
from typing import Dict, List, Optional, Any
from hwagent.core.base_tool import BaseTool
from hwagent.core.models import ToolExecutionResult
from hwagent.core.constants import Constants

class SmartLaTeXGenerator(BaseTool):
    """Smart LaTeX generator that creates properly formatted documents with intelligent content processing."""
    
    def __init__(self, tmp_directory: str = Constants.DEFAULT_TMP_DIRECTORY):
        super().__init__(tmp_directory)
    
    @property
    def name(self) -> str:
        return "smart_latex_generator"
    
    @property
    def description(self) -> str:
        return "Smart LaTeX document generator with basic universal setup. LLM customizes language, content, and formatting as needed."
    
    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "name": "smart_latex_generator",
            "description": "Generates LaTeX documents with smart formatting and language support. Automatically handles document structure, mathematical notation, and language-specific requirements.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "The file path for the LaTeX document"
                    },
                    "title": {
                        "type": "string",
                        "description": "The title of the document"
                    },
                    "content_sections": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "section_type": {"type": "string"},
                                "content": {"type": "string"}
                            },
                            "required": ["section_type", "content"]
                        },
                        "description": "List of content sections with type and content"
                    },
                    "task_type": {
                        "type": "string",
                        "enum": ["math", "programming", "analysis", "general"],
                        "default": "math",
                        "description": "Type of academic task"
                    },
                    "language": {
                        "type": "string",
                        "description": "Document language (any language supported by babel, e.g., 'english', 'russian', 'german', 'french', 'spanish', 'chinese', 'japanese', etc.)",
                        "default": "english"
                    }
                },
                "required": ["filepath", "title", "content_sections"]
            }
        }
    
    def _execute_impl(self, **kwargs) -> ToolExecutionResult:
        """Implementation of the abstract execute method"""
        filepath = kwargs["filepath"]
        title = kwargs["title"]
        content_sections = kwargs["content_sections"]
        task_type = kwargs.get("task_type", "math")
        language = kwargs.get("language", "english")
        
        try:
            # Generate the LaTeX document
            latex_content = self._generate_document(title, content_sections, task_type, language)
            
            # Get full path using the base class method
            full_path = self._get_full_path(filepath)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            # Write the file with proper encoding
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(latex_content)
            
            return ToolExecutionResult.success(
                f"Smart LaTeX document generated successfully: {filepath}",
                f"Created {task_type} document with {len(content_sections)} sections"
            )
            
        except Exception as e:
            return ToolExecutionResult.error(
                f"Error generating LaTeX document: {str(e)}",
                f"Failed to create {filepath}: {str(e)}"
            )
    
    def _generate_document(self, title: str, content_sections: Dict[str, str], 
                          task_type: str, language: str) -> str:
        """Generate the complete LaTeX document"""
        
        # Get the appropriate preamble
        preamble = self._get_preamble(task_type, language)
        
        # Build document header
        header = self._build_header(title)
        
        # Build document body
        body = self._build_body(content_sections, task_type, language)
        
        # Combine all parts
        return f"{preamble}\n\n{header}\n\n\\begin{{document}}\n\\maketitle\n\\tableofcontents\n\\newpage\n\n{body}\n\n\\end{{document}}\n"
    
    def _get_preamble(self, task_type: str, language: str) -> str:
        """Get appropriate document preamble - universal approach"""
        
        # Base packages
        base_packages = [
            "\\usepackage[utf8]{inputenc}",
            "\\usepackage[T1]{fontenc}",  # Universal for most European languages
            "\\usepackage{amsmath,amssymb,amsfonts}",
            "\\usepackage{geometry}",
            "\\usepackage{hyperref}",
            "\\usepackage{graphicx}",
            "\\usepackage{xcolor}"
        ]
        
        # Language support (LLM can specify specific language and additional packages)
        if language and language.lower() not in ['none', 'english']:
            base_packages.append(f"\\usepackage[{language.lower()}]{{babel}}")
        
        # Task-specific packages
        if task_type in ["math", "programming"]:
            base_packages.extend([
                "\\usepackage{listings}",
                "\\usepackage{algorithm}",
                "\\usepackage{algorithmic}"
            ])
        
        if task_type == "analysis":
            base_packages.extend([
                "\\usepackage{booktabs}",
                "\\usepackage{array}",
                "\\usepackage{longtable}"
            ])
        
        # Geometry settings
        geometry = "\\geometry{a4paper, margin=1in}"
        
        # Code styling (if needed)
        code_style = ""
        if task_type in ["math", "programming"]:
            code_style = """
% Code styling
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
        
        return "\\documentclass[12pt,a4paper]{article}\n\n" + \
               "\n".join(base_packages) + f"\n\n{geometry}\n{code_style}"
    
    def _build_header(self, title: str) -> str:
        """Build document header"""
        clean_title = self._escape_latex(title)
        return f"\\title{{{clean_title}}}\n\\author{{AI Technical Assistant}}\n\\date{{\\today}}"
    
    def _build_body(self, content_sections: Dict[str, str], task_type: str, language: str) -> str:
        """Build document body with intelligent section ordering"""
        
        # Define standard section order based on task type
        section_orders = {
            "math": [
                "problem_statement", "methodology", "solution_steps", 
                "computational_verification", "analysis", "conclusion"
            ],
            "programming": [
                "problem_description", "algorithm_design", "implementation", 
                "testing", "performance_analysis", "conclusions"
            ],
            "analysis": [
                "research_question", "methodology", "data_analysis", 
                "findings", "statistical_analysis", "conclusions_recommendations"
            ],
            "general": [
                "task_definition", "methodology", "solution", 
                "verification_testing", "results_summary"
            ]
        }
        
        # Get section titles based on language
        section_titles = self._get_section_titles(language)
        
        # Build sections in proper order
        body_parts = []
        standard_order = section_orders.get(task_type, section_orders["general"])
        
        # Add sections in standard order
        for section_key in standard_order:
            if section_key in content_sections:
                title = section_titles.get(section_key, section_key.replace('_', ' ').title())
                content = self._process_content(content_sections[section_key])
                body_parts.append(f"\\section{{{title}}}\n{content}")
        
        # Add any remaining sections not in standard order
        for section_key, content in content_sections.items():
            if section_key not in standard_order:
                title = section_titles.get(section_key, section_key.replace('_', ' ').title())
                processed_content = self._process_content(content)
                body_parts.append(f"\\section{{{title}}}\n{processed_content}")
        
        return "\n\n".join(body_parts)
    
    def _get_section_titles(self, language: str) -> Dict[str, str]:
        """Get section titles - LLM can translate these as needed"""
        
        # Basic English section titles that LLM can translate
        return {
            "problem_statement": "Problem Statement",
            "methodology": "Methodology",
            "solution_steps": "Solution Steps",
            "computational_verification": "Computational Verification",
            "analysis": "Analysis",
            "conclusion": "Conclusion",
            "problem_description": "Problem Description",
            "algorithm_design": "Algorithm Design",
            "implementation": "Implementation",
            "testing": "Testing",
            "performance_analysis": "Performance Analysis",
            "conclusions": "Conclusions",
            "research_question": "Research Question",
            "data_analysis": "Data Analysis",
            "findings": "Findings",
            "statistical_analysis": "Statistical Analysis",
            "conclusions_recommendations": "Conclusions and Recommendations",
            "task_definition": "Task Definition",
            "solution": "Solution",
            "verification_testing": "Verification and Testing",
            "results_summary": "Results Summary"
        }
    
    def _process_content(self, content: str) -> str:
        """Process content to ensure proper LaTeX formatting"""
        
        # Escape special characters first
        content = self._escape_latex(content)
        
        # Convert markdown-style formatting to LaTeX
        content = self._convert_markdown_to_latex(content)
        
        # Process mathematical expressions
        content = self._process_math_expressions(content)
        
        # Process code blocks
        content = self._process_code_blocks(content)
        
        # Clean up formatting
        content = self._cleanup_formatting(content)
        
        return content
    
    def _escape_latex(self, text: str) -> str:
        """Escape special LaTeX characters"""
        # Don't escape if already in math mode or contains LaTeX commands
        if '\\(' in text or '\\[' in text or '\\begin{' in text:
            return text
        
        # Special character mapping
        replacements = {
            '&': '\\&',
            '%': '\\%',
            '$': '\\$',
            '#': '\\#',
            '^': '\\textasciicircum{}',
            '_': '\\_',
            '{': '\\{',
            '}': '\\}',
            '~': '\\textasciitilde{}',
            '\\': '\\textbackslash{}'
        }
        
        # Apply replacements only to text content (not math)
        result = text
        for char, replacement in replacements.items():
            if char not in ['$', '^', '_', '{', '}']:  # Keep math characters for processing
                result = result.replace(char, replacement)
        
        return result
    
    def _convert_markdown_to_latex(self, content: str) -> str:
        """Convert markdown formatting to LaTeX"""
        
        # Headers (should not occur in sections, but just in case)
        content = re.sub(r'^### (.*?)$', r'\\subsubsection{\1}', content, flags=re.MULTILINE)
        content = re.sub(r'^## (.*?)$', r'\\subsection{\1}', content, flags=re.MULTILINE)
        content = re.sub(r'^# (.*?)$', r'\\section{\1}', content, flags=re.MULTILINE)
        
        # Bold and italic
        content = re.sub(r'\*\*(.*?)\*\*', r'\\textbf{\1}', content)
        content = re.sub(r'\*(.*?)\*', r'\\textit{\1}', content)
        
        # Lists
        content = re.sub(r'^- (.*?)$', r'\\item \1', content, flags=re.MULTILINE)
        content = re.sub(r'^(\d+)\. (.*?)$', r'\\item \2', content, flags=re.MULTILINE)
        
        # Wrap consecutive items in list environments
        content = self._wrap_lists(content)
        
        return content
    
    def _wrap_lists(self, content: str) -> str:
        """Wrap consecutive \\item entries in proper list environments"""
        
        lines = content.split('\n')
        result_lines = []
        in_list = False
        
        for line in lines:
            if line.strip().startswith('\\item'):
                if not in_list:
                    result_lines.append('\\begin{itemize}')
                    in_list = True
                result_lines.append(line)
            else:
                if in_list:
                    result_lines.append('\\end{itemize}')
                    in_list = False
                result_lines.append(line)
        
        if in_list:
            result_lines.append('\\end{itemize}')
        
        return '\n'.join(result_lines)
    
    def _process_math_expressions(self, content: str) -> str:
        """Process mathematical expressions to ensure proper LaTeX formatting"""
        
        # Convert $...$ to \(...\) for inline math
        content = re.sub(r'(?<!\\)\$([^$]+?)\$', r'\\(\1\\)', content)
        
        # Convert $$...$$ to \[...\] for display math  
        content = re.sub(r'(?<!\\)\$\$([^$]+?)\$\$', r'\\[\1\\]', content, flags=re.DOTALL)
        
        # Fix common math notation issues
        content = re.sub(r'\\int_\{([^}]+)\}\^\{([^}]+)\}', r'\\int_{\1}^{\2}', content)
        
        return content
    
    def _process_code_blocks(self, content: str) -> str:
        """Process code blocks and convert to LaTeX listings"""
        
        # Convert markdown code blocks to LaTeX listings
        def replace_code_block(match):
            language = match.group(1) if match.group(1) else 'text'
            code = match.group(2)
            return f'\\begin{{lstlisting}}[language={language.title()}]\n{code}\n\\end{{lstlisting}}'
        
        # Handle fenced code blocks
        content = re.sub(r'```(\w+)?\n(.*?)\n```', replace_code_block, content, flags=re.DOTALL)
        
        # Handle inline code
        content = re.sub(r'`([^`]+)`', r'\\texttt{\1}', content)
        
        return content
    
    def _cleanup_formatting(self, content: str) -> str:
        """Final cleanup of formatting"""
        
        # Remove excessive whitespace
        content = re.sub(r'\n\s*\n\s*\n+', r'\n\n', content)
        
        # Ensure proper spacing around environments
        content = re.sub(r'\n(\\begin\{)', r'\n\n\1', content)
        content = re.sub(r'(\\end\{[^}]+\})\n', r'\1\n\n', content)
        
        return content.strip()


# Register the tool (this would be added to the tool manager)
def get_tool():
    """Factory function to get the tool instance"""
    return SmartLaTeXGenerator() 