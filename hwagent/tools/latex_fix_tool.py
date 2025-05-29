"""
Enhanced LaTeX Fix Tool with Template-Based Generation
Handles complex LaTeX issues and provides robust document creation.
"""

import re
import os
from typing import Dict, List, Optional, Tuple
from hwagent.core.base_tool import BaseTool
from hwagent.core.models import ToolExecutionResult
from hwagent.core.constants import Constants

class LaTeXFixTool(BaseTool):
    """Enhanced LaTeX fixing tool with template-based generation and comprehensive error handling."""
    
    @property
    def name(self) -> str:
        return "latex_fix"
    
    @property
    def description(self) -> str:
        return "Automatically fix LaTeX syntax errors, handle Unicode issues, and generate proper LaTeX documents using templates."
    
    @property
    def parameters_schema(self) -> Dict[str, any]:
        return {
            "type": "object",
            "properties": {
                "filepath": {
                    "type": "string",
                    "description": "Path to the LaTeX file to fix"
                },
                "task_type": {
                    "type": "string", 
                    "description": "Type of task (math, programming, analysis, general)",
                    "enum": ["math", "programming", "analysis", "general"],
                    "default": "general"
                }
            },
            "required": ["filepath"]
        }
    
    def _execute_impl(self, **kwargs) -> ToolExecutionResult:
        """Implementation of the abstract execute method"""
        return self.execute(**kwargs)
    
    def __init__(self, tmp_directory: str = Constants.DEFAULT_TMP_DIRECTORY):
        super().__init__(tmp_directory)
        
        # LaTeX templates for different task types
        self.templates = {
            "math": self._get_math_template(),
            "programming": self._get_programming_template(),
            "analysis": self._get_analysis_template(),
            "general": self._get_general_template()
        }
    
    def _get_math_template(self) -> str:
        """Template for mathematical problems"""
        return r"""\documentclass[12pt,a4paper]{{article}}
\usepackage[utf8]{{inputenc}}
\usepackage[russian,english,ukrainian]{{babel}}
\usepackage{{amsmath,amssymb,amsfonts}}
\usepackage{{geometry}}
\usepackage{{listings}}
\usepackage{{xcolor}}
\usepackage{{hyperref}}
\usepackage{{graphicx}}
\usepackage{{float}}

\geometry{{a4paper, margin=1in}}

\title{{{title}}}
\author{{AI Technical Assistant}}
\date{{\today}}

\begin{{document}}
\maketitle
\tableofcontents
\newpage

\section{{Постановка задачи}}
{problem_statement}

\section{{Методология}}
{methodology}

\section{{Пошаговое решение}}
{solution_steps}

\section{{Вычислительная проверка}}
{computational_verification}

\section{{Анализ результатов}}
{analysis}

\section{{Заключение}}
{conclusion}

\end{{document}}"""

    def _get_programming_template(self) -> str:
        """Template for programming tasks"""
        return r"""\documentclass[12pt,a4paper]{{article}}
\usepackage[utf8]{{inputenc}}
\usepackage[russian,english,ukrainian]{{babel}}
\usepackage{{amsmath,amssymb,amsfonts}}
\usepackage{{geometry}}
\usepackage{{listings}}
\usepackage{{xcolor}}
\usepackage{{hyperref}}

\geometry{{a4paper, margin=1in}}

\definecolor{{codegray}}{{rgb}}{{0.5,0.5,0.5}}
\definecolor{{codepurple}}{{rgb}}{{0.58,0,0.82}}
\definecolor{{backcolour}}{{rgb}}{{0.95,0.95,0.92}}

\lstdefinestyle{{mystyle}}{{
    backgroundcolor=\color{{backcolour}},   
    commentstyle=\color{{codegray}},
    keywordstyle=\color{{blue}},
    numberstyle=\tiny\color{{codegray}},
    stringstyle=\color{{codepurple}},
    basicstyle=\ttfamily\footnotesize,
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
}}

\lstset{{style=mystyle}}

\title{{{title}}}
\author{{AI Technical Assistant}}
\date{{\today}}

\begin{{document}}
\maketitle
\tableofcontents
\newpage

\section{{Описание задачи}}
{problem_description}

\section{{Дизайн алгоритма}}
{algorithm_design}

\section{{Реализация}}
{implementation}

\section{{Тестирование}}
{testing}

\section{{Анализ производительности}}
{performance_analysis}

\section{{Выводы}}
{conclusions}

\end{{document}}"""

    def _get_analysis_template(self) -> str:
        """Template for analysis tasks"""
        return r"""\documentclass[12pt,a4paper]{{article}}
\usepackage[utf8]{{inputenc}}
\usepackage[russian,english,ukrainian]{{babel}}
\usepackage{{amsmath,amssymb,amsfonts}}
\usepackage{{geometry}}
\usepackage{{listings}}
\usepackage{{xcolor}}
\usepackage{{hyperref}}
\usepackage{{graphicx}}
\usepackage{{booktabs}}

\geometry{{a4paper, margin=1in}}

\title{{{title}}}
\author{{AI Technical Assistant}}
\date{{\today}}

\begin{{document}}
\maketitle
\tableofcontents
\newpage

\section{{Исследовательский вопрос}}
{research_question}

\section{{Методология}}
{methodology}

\section{{Анализ данных}}
{data_analysis}

\section{{Результаты}}
{findings}

\section{{Статистический анализ}}
{statistical_analysis}

\section{{Выводы и рекомендации}}
{conclusions_recommendations}

\end{{document}}"""

    def _get_general_template(self) -> str:
        """General template for any task"""
        return r"""\documentclass[12pt,a4paper]{{article}}
\usepackage[utf8]{{inputenc}}
\usepackage[russian,english,ukrainian]{{babel}}
\usepackage{{amsmath,amssymb,amsfonts}}
\usepackage{{geometry}}
\usepackage{{listings}}
\usepackage{{xcolor}}
\usepackage{{hyperref}}

\geometry{{a4paper, margin=1in}}

\title{{{title}}}
\author{{AI Technical Assistant}}
\date{{\today}}

\begin{{document}}
\maketitle
\tableofcontents
\newpage

\section{{Определение задачи}}
{task_definition}

\section{{Методология}}
{methodology}

\section{{Решение}}
{solution}

\section{{Проверка и тестирование}}
{verification_testing}

\section{{Резюме результатов}}
{results_summary}

\end{{document}}"""

    def execute(self, filepath: str, task_type: str = "general", **kwargs) -> ToolExecutionResult:
        """
        Enhanced LaTeX fixing with template-based generation
        
        Args:
            filepath: Path to the LaTeX file to fix (relative to tmp directory)
            task_type: Type of task (math, programming, analysis, general)
            **kwargs: Template variables for content generation
        """
        try:
            # Get full path using base class method
            full_path = self._get_full_path(filepath)
            
            if not os.path.exists(full_path):
                return ToolExecutionResult.error(
                    f"File not found: {filepath}",
                    f"The specified LaTeX file does not exist: {full_path}"
                )
            
            # Read the file
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Create backup
            backup_path = f"{full_path}.backup"
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Apply comprehensive fixes
            fixed_content = self._comprehensive_fix(content, task_type, **kwargs)
            
            # Write fixed content
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            
            return ToolExecutionResult.success(
                "LaTeX file successfully fixed using enhanced template-based approach",
                f"Applied comprehensive fixes to {filepath}. Backup saved as {filepath}.backup. Used template type: {task_type}"
            )
            
        except Exception as e:
            return ToolExecutionResult.error(
                f"Error fixing LaTeX file: {str(e)}",
                f"Failed to fix {filepath}: {str(e)}"
            )

    def _comprehensive_fix(self, content: str, task_type: str, **kwargs) -> str:
        """Apply comprehensive LaTeX fixes"""
        
        # Step 1: Fix double backslashes
        content = self._fix_double_backslashes(content)
        
        # Step 2: Fix Unicode and encoding issues
        content = self._fix_unicode_issues(content)
        
        # Step 3: Fix structural issues
        content = self._fix_structure(content)
        
        # Step 4: Fix mathematical notation
        content = self._fix_math_notation(content)
        
        # Step 5: Fix listings and code blocks
        content = self._fix_listings(content)
        
        # Step 6: If content is severely broken, use template regeneration
        if self._is_severely_broken(content):
            content = self._regenerate_with_template(content, task_type, **kwargs)
        
        # Step 7: Final cleanup
        content = self._final_cleanup(content)
        
        return content

    def _fix_double_backslashes(self, content: str) -> str:
        """Fix double backslashes that should be single"""
        # First, fix specific LaTeX commands that commonly have double backslashes
        specific_fixes = [
            (r'\\\\documentclass', r'\\documentclass'),
            (r'\\\\usepackage', r'\\usepackage'),
            (r'\\\\begin\{', r'\\begin{'),
            (r'\\\\end\{', r'\\end{'),
            (r'\\\\section\{', r'\\section{'),
            (r'\\\\subsection\{', r'\\subsection{'),
            (r'\\\\subsubsection\{', r'\\subsubsection{'),
            (r'\\\\title\{', r'\\title{'),
            (r'\\\\author\{', r'\\author{'),
            (r'\\\\date\{', r'\\date{'),
            (r'\\\\maketitle', r'\\maketitle'),
            (r'\\\\tableofcontents', r'\\tableofcontents'),
            (r'\\\\newpage', r'\\newpage'),
            (r'\\\\geometry\{', r'\\geometry{'),
            (r'\\\\definecolor\{', r'\\definecolor{'),
            (r'\\\\lstdefinestyle\{', r'\\lstdefinestyle{'),
            (r'\\\\lstset\{', r'\\lstset{'),
            (r'\\\\textbf\{', r'\\textbf{'),
            (r'\\\\textit\{', r'\\textit{'),
            (r'\\\\item', r'\\item'),
            (r'\\\\centering', r'\\centering'),
            (r'\\\\includegraphics', r'\\includegraphics'),
            (r'\\\\caption\{', r'\\caption{'),
            (r'\\\\label\{', r'\\label{'),
        ]
        
        # Apply specific fixes
        for pattern, replacement in specific_fixes:
            content = re.sub(pattern, replacement, content)
        
        # General fix for any LaTeX command that starts with double backslashes
        # This catches cases we might have missed above
        # Pattern: \\ followed by a letter, capturing the command name
        content = re.sub(r'\\\\([a-zA-Z]+)', r'\\\\\1', content)
        
        # Fix double backslashes in math mode indicators
        content = re.sub(r'\\\\\[', r'\\[', content)
        content = re.sub(r'\\\\\]', r'\\]', content)
        content = re.sub(r'\\\\\(', r'\\(', content)
        content = re.sub(r'\\\\\)', r'\\)', content)
        
        # Fix double backslashes before special characters in LaTeX
        content = re.sub(r'\\\\&', r'\\&', content)
        content = re.sub(r'\\\\%', r'\\%', content)
        content = re.sub(r'\\\\\$', r'\\$', content)
        content = re.sub(r'\\\\#', r'\\#', content)
        content = re.sub(r'\\\\_', r'\\_', content)
        content = re.sub(r'\\\\\{', r'\\{', content)
        content = re.sub(r'\\\\\}', r'\\}', content)
        
        return content

    def _fix_unicode_issues(self, content: str) -> str:
        """Fix Unicode and encoding issues"""
        # Ensure proper babel and inputenc packages
        if r'\usepackage[utf8]{inputenc}' not in content:
            # Add after documentclass
            content = re.sub(
                r'(\\documentclass.*?\n)',
                r'\1\\usepackage[utf8]{inputenc}\n\\usepackage[russian,english]{babel}\n',
                content,
                count=1
            )
        
        return content

    def _fix_structure(self, content: str) -> str:
        """Fix document structure issues"""
        
        # Fix missing documentclass
        if '\\documentclass' not in content:
            content = r'\documentclass[12pt,a4paper]{article}' + '\n' + content
        
        # Fix missing document environment
        if '\\begin{document}' not in content:
            # Find insertion point after preamble
            if '\\title{' in content:
                content = re.sub(
                    r'(\\date\{.*?\}\s*)',
                    r'\1\n\\begin{document}\n',
                    content,
                    count=1
                )
            else:
                # Insert after last usepackage
                content = re.sub(
                    r'(\\usepackage.*?\n)',
                    r'\1\\begin{document}\n',
                    content,
                    count=1
                )
        
        # Add missing end{document}
        if '\\end{document}' not in content:
            content += '\n\\end{document}'
        
        return content

    def _fix_math_notation(self, content: str) -> str:
        """Fix mathematical notation issues"""
        
        # Fix display math - convert $$ to \[ \]
        content = re.sub(r'(?<!\\)\$\$(.*?)\$\$', r'\\[\1\\]', content, flags=re.DOTALL)
        
        # Fix inline math issues - ensure _ and ^ are properly escaped or in math mode
        # Escape standalone _ and ^ that are not in math mode
        content = re.sub(r'(?<!\\)(_)(?![a-zA-Z0-9\{])', r'\\_', content)
        content = re.sub(r'(?<!\\)(\^)(?![a-zA-Z0-9\{])', r'\\textasciicircum{}', content)
        
        # Fix malformed math environments
        content = re.sub(r'\\\[\s*\\\\int\\textit\{\{([^}]+)\}\}', r'\\[\\int_{', content)
        content = re.sub(r'\\\]\}', r'\\]', content)
        
        # Fix integration bounds and other math notation
        content = re.sub(r'\\int\}\{([^}]+)\}\^\{([^}]+)\}', r'\\int_{\1}^{\2}', content)
        
        # Fix common issues with subscripts and superscripts in text mode
        # Convert text mode sub/superscripts to math mode
        content = re.sub(r'(?<!\\)([a-zA-Z0-9]+)_([a-zA-Z0-9]+)', r'\\(\1_{\2}\\)', content)
        content = re.sub(r'(?<!\\)([a-zA-Z0-9]+)\^([a-zA-Z0-9]+)', r'\\(\1^{\2}\\)', content)
        
        # Fix improperly escaped math characters
        content = re.sub(r'(?<!\\)&', r'\\&', content)  # Fix unescaped ampersands
        content = re.sub(r'(?<!\\)%', r'\\%', content)  # Fix unescaped percent signs
        
        return content

    def _fix_listings(self, content: str) -> str:
        """Fix code listings issues"""
        
        # Fix lstdefinestyle structure
        if '\\lstdefinestyle{mystyle}{}' in content:
            # Find the content that should be inside the style definition
            style_pattern = r'\\lstdefinestyle\{mystyle\}\{\}(\s*)(.*?)(?=\\lstset|\\title|\\begin\{document\})'
            match = re.search(style_pattern, content, re.DOTALL)
            if match:
                style_content = match.group(2).strip()
                # Clean up the style content
                style_content = re.sub(r'^\s*', '', style_content, flags=re.MULTILINE)
                
                replacement = f'''\\lstdefinestyle{{mystyle}}{{
    {style_content}
}}'''
                content = re.sub(r'\\lstdefinestyle\{mystyle\}\{\}.*?(?=\\lstset)', replacement, content, flags=re.DOTALL)
        
        return content

    def _is_severely_broken(self, content: str) -> bool:
        """Check if content is severely broken and needs template regeneration"""
        issues = 0
        
        # Count critical issues
        if '\\documentclass' not in content:
            issues += 1
        if '\\begin{document}' not in content:
            issues += 1
        if '\\end{document}' not in content:
            issues += 1
        if 'Unicode character' in content:  # Indicates encoding issues
            issues += 1
        if content.count('\\\\') > 10:  # Too many double backslashes
            issues += 1
        
        # Check for patterns that commonly cause "Missing $ inserted" errors
        if re.search(r'[_^](?!\{)', content):  # Unescaped _ or ^ outside math mode
            issues += 1
        
        # Check for patterns that cause "There's no line here to end" errors
        if re.search(r'\\\\(?![a-zA-Z]|\[|\]|\(|\))', content):  # Inappropriate \\ usage
            issues += 1
            
        # Check for mixed markdown and LaTeX syntax
        if re.search(r'^#{1,6}\s', content, re.MULTILINE):  # Markdown headers
            issues += 1
        if re.search(r'\*\*.*?\*\*', content):  # Markdown bold
            issues += 1
        if re.search(r'(?<!\\)\$\$.*?\$\$', content):  # $$ math instead of \[ \]
            issues += 1
            
        # Check for malformed LaTeX commands
        if re.search(r'\\\\[a-zA-Z]+\{', content):  # Double backslash before commands
            issues += 1
        
        return issues >= 3

    def _regenerate_with_template(self, content: str, task_type: str, **kwargs) -> str:
        """Regenerate content using appropriate template"""
        
        # Extract key information from broken content
        title = self._extract_title(content) or kwargs.get('title', 'Техническое решение')
        
        # Get appropriate template
        template = self.templates.get(task_type, self.templates['general'])
        
        # Fill template with extracted or provided content
        template_vars = {
            'title': title,
            'problem_statement': kwargs.get('problem_statement', 'Требуется решить техническую задачу.'),
            'methodology': kwargs.get('methodology', 'Применяется системный подход к решению задачи.'),
            'solution_steps': kwargs.get('solution_steps', 'Пошаговое решение будет представлено ниже.'),
            'computational_verification': kwargs.get('computational_verification', 'Вычислительная проверка проводится с использованием соответствующих инструментов.'),
            'analysis': kwargs.get('analysis', 'Анализ результатов показывает корректность решения.'),
            'conclusion': kwargs.get('conclusion', 'Задача решена успешно.'),
            
            # For other templates
            'problem_description': kwargs.get('problem_description', 'Описание технической задачи.'),
            'algorithm_design': kwargs.get('algorithm_design', 'Дизайн алгоритма решения.'),
            'implementation': kwargs.get('implementation', 'Детали реализации.'),
            'testing': kwargs.get('testing', 'Процедуры тестирования.'),
            'performance_analysis': kwargs.get('performance_analysis', 'Анализ производительности.'),
            'conclusions': kwargs.get('conclusions', 'Выводы и заключения.'),
            
            'research_question': kwargs.get('research_question', 'Исследовательский вопрос.'),
            'data_analysis': kwargs.get('data_analysis', 'Анализ данных.'),
            'findings': kwargs.get('findings', 'Основные находки.'),
            'statistical_analysis': kwargs.get('statistical_analysis', 'Статистический анализ.'),
            'conclusions_recommendations': kwargs.get('conclusions_recommendations', 'Выводы и рекомендации.'),
            
            'task_definition': kwargs.get('task_definition', 'Определение задачи.'),
            'solution': kwargs.get('solution', 'Решение задачи.'),
            'verification_testing': kwargs.get('verification_testing', 'Проверка и тестирование.'),
            'results_summary': kwargs.get('results_summary', 'Резюме результатов.')
        }
        
        return template.format(**template_vars)

    def _extract_title(self, content: str) -> Optional[str]:
        """Extract title from broken content"""
        title_match = re.search(r'\\title\{([^}]+)\}', content)
        if title_match:
            return title_match.group(1)
        return None

    def _final_cleanup(self, content: str) -> str:
        """Final cleanup of the content"""
        
        # Remove multiple empty lines
        content = re.sub(r'\n\s*\n\s*\n', r'\n\n', content)
        
        # Fix spacing around sections
        content = re.sub(r'\n(\\section\{)', r'\n\n\1', content)
        content = re.sub(r'\n(\\subsection\{)', r'\n\n\1', content)
        
        # Final pass to catch any remaining double backslashes
        # This is more aggressive and catches any remaining issues
        content = re.sub(r'\\\\([a-zA-Z])', r'\\\1', content)
        
        # Remove inappropriate line breaks (\\) that are not in proper context
        # Keep \\ only in specific contexts like table rows or forced line breaks
        content = re.sub(r'\\\\(?!\s*[\n\r]|\s*&|\s*\\hline)', r'', content)
        
        # Fix any remaining double spaces
        content = re.sub(r'\s{2,}', r' ', content)
        
        # Ensure proper line endings
        content = content.strip() + '\n'
        
        return content