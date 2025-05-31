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
        return "Enhanced LaTeX document fix tool with intelligent double-slash correction and English defaults. Handles template regeneration with universal language support via LLM control."
    
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
        """Mathematical template with universal language support"""
        return r"""\documentclass[12pt,a4paper]{{article}}
\usepackage[utf8]{{inputenc}}
\usepackage[T1,OT1]{{fontenc}}
\usepackage[english]{{babel}}
\usepackage{{amsmath,amssymb,amsfonts}}
\usepackage{{geometry}}
\usepackage{{graphicx}}
\usepackage{{float}}
\usepackage{{hyperref}}
\usepackage{{listings}}
\usepackage{{xcolor}}

\geometry{{a4paper, margin=1in}}

% Code styling
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
\author{{Technical Assistant}}
\date{{\today}}

\begin{{document}}
\maketitle
\tableofcontents
\newpage

\section{{Problem Statement}}
{problem_statement}

\section{{Methodology}}  
{methodology}

\section{{Solution}}
{solution_steps}

\section{{Computational Verification}}
{computational_verification}

\section{{Analysis}}
{analysis}

\section{{Conclusion}}
{conclusion}

\end{{document}}"""

    def _get_programming_template(self) -> str:
        """Programming template with universal language support"""
        return r"""\documentclass[12pt,a4paper]{{article}}
\usepackage[utf8]{{inputenc}}
\usepackage[T1,OT1]{{fontenc}}
\usepackage[english]{{babel}}
\usepackage{{amsmath,amssymb}}
\usepackage{{geometry}}
\usepackage{{graphicx}}
\usepackage{{float}}
\usepackage{{hyperref}}
\usepackage{{listings}}
\usepackage{{xcolor}}
\usepackage{{algorithm}}
\usepackage{{algorithmic}}

\geometry{{a4paper, margin=1in}}

% Code styling configuration
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
\author{{Technical Assistant}}
\date{{\today}}

\begin{{document}}
\maketitle
\tableofcontents
\newpage

\section{{Problem Description}}
{problem_description}

\section{{Algorithm Development}}
{algorithm_development}

\section{{Implementation}}
{implementation}

\section{{Code Listings}}
{code_listings}

\section{{Testing and Validation}}
{testing_validation}

\section{{Performance Analysis}}
{performance_analysis}

\section{{Conclusion}}
{conclusion}

\end{{document}}"""

    def _get_analysis_template(self) -> str:
        """Analysis template with universal language support"""
        return r"""\documentclass[12pt,a4paper]{{article}}
\usepackage[utf8]{{inputenc}}
\usepackage[T1,OT1]{{fontenc}}
\usepackage[english]{{babel}}
\usepackage{{amsmath,amssymb}}
\usepackage{{geometry}}
\usepackage{{graphicx}}
\usepackage{{float}}
\usepackage{{hyperref}}
\usepackage{{booktabs}}
\usepackage{{array}}
\usepackage{{longtable}}
\usepackage{{multirow}}
\usepackage{{listings}}
\usepackage{{xcolor}}

\geometry{{a4paper, margin=1in}}

% Code styling configuration
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
\author{{Technical Assistant}}
\date{{\today}}

\begin{{document}}
\maketitle
\tableofcontents
\newpage

\section{{Introduction}}
{introduction}

\section{{Data and Methodology}}
{data_methodology}

\section{{Analysis Results}}
{analysis_results}

\section{{Computational Verification}}
{computational_verification}

\section{{Discussion}}
{discussion}

\section{{Recommendations}}
{recommendations}

\section{{Conclusion}}
{conclusion}

\end{{document}}"""

    def _get_general_template(self) -> str:
        """General template with universal language support"""
        return r"""\documentclass[12pt,a4paper]{{article}}
\usepackage[utf8]{{inputenc}}
\usepackage[T1,OT1]{{fontenc}}
\usepackage[english]{{babel}}
\usepackage{{amsmath,amssymb}}
\usepackage{{geometry}}
\usepackage{{graphicx}}
\usepackage{{float}}
\usepackage{{hyperref}}
\usepackage{{listings}}
\usepackage{{xcolor}}

\geometry{{a4paper, margin=1in}}

% Code styling configuration
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
\author{{Technical Assistant}}
\date{{\today}}

\begin{{document}}
\maketitle
\tableofcontents
\newpage

\section{{Task Overview}}
{task_overview}

\section{{Methodology}}
{methodology}

\section{{Implementation}}
{implementation}

\section{{Results}}
{results}

\section{{Analysis}}
{analysis}

\section{{Conclusion}}
{conclusion}

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
        content = self._fix_encoding_issues(content)
        
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
        """Fix double backslashes that should be single - corrected regex logic"""
        
        # First pass: Fix specific LaTeX commands that commonly have double backslashes
        # In r-strings: r'\\\\' = 2 literal backslashes (\\), r'\\' = 1 literal backslash (\)
        # For regex: r'\\\\' matches \\, r'\\' replacement gives \
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
            (r'\\\\emph\{', r'\\emph{'),
            (r'\\\\item', r'\\item'),
            (r'\\\\centering', r'\\centering'),
            (r'\\\\includegraphics', r'\\includegraphics'),
            (r'\\\\caption\{', r'\\caption{'),
            (r'\\\\label\{', r'\\label{'),
            (r'\\\\ref\{', r'\\ref{'),
            (r'\\\\cite\{', r'\\cite{'),
            (r'\\\\footnote\{', r'\\footnote{'),
            (r'\\\\frac\{', r'\\frac{'),
            (r'\\\\sqrt\{', r'\\sqrt{'),
            (r'\\\\sum', r'\\sum'),
            (r'\\\\int', r'\\int'),
            (r'\\\\prod', r'\\prod'),
            (r'\\\\lim', r'\\lim'),
            (r'\\\\sin', r'\\sin'),
            (r'\\\\cos', r'\\cos'),
            (r'\\\\tan', r'\\tan'),
            (r'\\\\log', r'\\log'),
            (r'\\\\ln', r'\\ln'),
            (r'\\\\exp', r'\\exp'),
        ]
        
        # Apply specific fixes
        for pattern, replacement in specific_fixes:
            content = re.sub(pattern, replacement, content)
        
        # Second pass: General fix for LaTeX commands (be more careful)
        # Only fix \\ followed by a letter that starts a valid LaTeX command
        # This pattern is more conservative to avoid breaking valid \\ line breaks
        content = re.sub(r'\\\\([a-zA-Z][a-zA-Z0-9]*)\b', r'\\\1', content)
        
        # Third pass: Fix double backslashes in math mode delimiters
        content = re.sub(r'\\\\\[', r'\\[', content)
        content = re.sub(r'\\\\\]', r'\\]', content)
        content = re.sub(r'\\\\\(', r'\\(', content)
        content = re.sub(r'\\\\\)', r'\\)', content)
        
        # Fourth pass: Fix double backslashes before special characters in LaTeX
        # Only fix these when they're clearly wrong (not in valid contexts)
        content = re.sub(r'\\\\&(?!\s)', r'\\&', content)
        content = re.sub(r'\\\\%(?![^\\]*\\\\)', r'\\%', content)
        content = re.sub(r'\\\\\$(?![^\\]*\$)', r'\\$', content)
        content = re.sub(r'\\\\#(?![^\\]*#)', r'\\#', content)
        content = re.sub(r'\\\\_(?![^\\]*_)', r'\\_', content)
        content = re.sub(r'\\\\\{', r'\\{', content)
        content = re.sub(r'\\\\\}', r'\\}', content)
        
        # Fifth pass: Be more careful with line breaks \\
        # Don't remove \\ that are valid line breaks in specific contexts:
        # - At the end of table rows (followed by whitespace and &, \\ or \hline)
        # - In specific environments like center, flushleft, flushright
        # - In title pages or after \maketitle
        
        # Remove \\ that are clearly wrong (not in valid line break contexts)
        # This regex preserves \\ that are:
        # - At end of lines followed by whitespace
        # - In table contexts (followed by & or \hline)
        # - In proper line break contexts
        content = re.sub(r'\\\\(?!\s*(?:\n|&|\\hline|\\\\|\}|\]|\)|$))', r'', content)
        
        return content

    def _fix_encoding_issues(self, content: str) -> str:
        """Fix encoding issues in LaTeX documents - universal approach"""
        
        # Ensure UTF-8 input encoding is present
        if r'\usepackage[utf8]{inputenc}' not in content and r'\usepackage{inputenc}' not in content:
            # Add UTF-8 input encoding after documentclass
            content = re.sub(
                r'(\\documentclass\{[^}]*\})',
                r'\1\n\\usepackage[utf8]{inputenc}',
                content
            )
        
        # Ensure basic fontenc is present (LLM can specify more specific encoding if needed)
        if r'\usepackage{fontenc}' not in content and r'\usepackage[' not in content:
            content = re.sub(
                r'(\\usepackage\[utf8\]\{inputenc\})',
                r'\1\n\\usepackage[T1]{fontenc}',
                content
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
        """Check if document has severe issues - universal approach"""
        
        issues_count = 0
        
        # Critical LaTeX structure checks
        if not re.search(r'\\documentclass\{', content):
            issues_count += 3
        if not re.search(r'\\begin\{document\}', content):
            issues_count += 3
        if not re.search(r'\\end\{document\}', content):
            issues_count += 3
        
        # Basic encoding checks
        if not re.search(r'\\usepackage\[utf8\]\{inputenc\}', content):
            issues_count += 1
        
        # Common error patterns
        if re.search(r'\\\\[^a-zA-Z]', content):  # Double backslashes not followed by letters
            issues_count += 2
        if re.search(r'[{}](?!\w)', content):  # Unescaped braces
            issues_count += 1
        if re.search(r'%[^%\n]*[{}]', content):  # Braces in comments
            issues_count += 1
        
        return issues_count >= 5

    def _regenerate_with_template(self, content: str, task_type: str, **kwargs) -> str:
        """Regenerate content using appropriate template - English by default"""
        
        # Extract key information from broken content
        title = self._extract_title(content) or kwargs.get('title', 'Technical Solution')
        
        # Get appropriate template
        template = self.templates.get(task_type, self.templates['general'])
        
        # Fill template with extracted or provided content - English by default
        template_vars = {
            'title': title,
            'problem_statement': kwargs.get('problem_statement', 'A technical problem needs to be solved.'),
            'methodology': kwargs.get('methodology', 'A systematic approach is applied to solve the problem.'),
            'solution_steps': kwargs.get('solution_steps', 'Step-by-step solution will be presented below.'),
            'computational_verification': kwargs.get('computational_verification', 'Computational verification is performed using appropriate tools.'),
            'analysis': kwargs.get('analysis', 'Analysis of results shows correctness of the solution.'),
            'conclusion': kwargs.get('conclusion', 'The problem has been solved successfully.'),
            
            # For other templates
            'problem_description': kwargs.get('problem_description', 'Description of the technical problem.'),
            'algorithm_development': kwargs.get('algorithm_development', 'Algorithm development and design.'),
            'implementation': kwargs.get('implementation', 'Implementation details.'),
            'code_listings': kwargs.get('code_listings', 'Code listings and examples.'),
            'testing_validation': kwargs.get('testing_validation', 'Testing and validation procedures.'),
            'performance_analysis': kwargs.get('performance_analysis', 'Performance analysis.'),
            
            # For analysis template
            'task_overview': kwargs.get('task_overview', 'Overview of the task.'),
            'methodology': kwargs.get('methodology', 'Methodology used for analysis.'),
            'results': kwargs.get('results', 'Results and findings.'),
            
            'conclusion': kwargs.get('conclusion', 'Conclusions and final remarks.')
        }
        
        return template.format(**template_vars)

    def _extract_title(self, content: str) -> Optional[str]:
        """Extract title from broken content"""
        title_match = re.search(r'\\title\{([^}]+)\}', content)
        if title_match:
            return title_match.group(1)
        return None

    def _final_cleanup(self, content: str) -> str:
        """Final cleanup of the content - improved double slash handling"""
        
        # Remove multiple empty lines
        content = re.sub(r'\n\s*\n\s*\n', r'\n\n', content)
        
        # Fix spacing around sections
        content = re.sub(r'\n(\\section\{)', r'\n\n\1', content)
        content = re.sub(r'\n(\\subsection\{)', r'\n\n\1', content)
        
        # Final pass to catch any remaining wrong double backslashes
        # Be very conservative - only fix obvious command errors
        # Pattern: \\ followed by a lowercase letter that's clearly a LaTeX command
        content = re.sub(r'\\\\([a-z][a-zA-Z]+\{)', r'\\\1', content)
        
        # Remove clearly inappropriate line breaks (\\) that are not in proper context
        # Only remove \\ that are:
        # - Not followed by whitespace, newline, or end of string
        # - Not in table contexts (& or \hline)
        # - Not at proper line break positions
        # This preserves valid \\ line breaks while removing erroneous ones
        content = re.sub(r'\\\\(?![\\s]*(?:\n|\r|&|\\hline|\\\\|\}|\]|\)|$|\s))', r' ', content)
        
        # Fix any remaining multiple spaces (but preserve intentional spacing)
        content = re.sub(r'[ \t]{3,}', r'  ', content)  # Reduce excessive spaces but keep some
        
        # Ensure proper line endings
        content = content.strip() + '\n'
        
        return content