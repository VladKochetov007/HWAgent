# HWAgent - Advanced Homework Assistant

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**HWAgent** is an intelligent homework assistant system that specializes in solving complex academic tasks with automatic LaTeX documentation generation. The system excels at mathematical problems, programming assignments, data analysis, and research tasks while generating professional PDF documentation for every solution.

## 🚀 Key Features

### Enhanced LaTeX Tools
- **Automatic Quote Removal**: Intelligently removes unwanted quotes (`'`, `"`, `` ` ``) from LaTeX content
- **Mathematical Package Auto-inclusion**: Automatically adds required math packages (amsmath, amsfonts, amssymb, etc.)
- **Safe Compilation**: Batch mode compilation with timeout protection (no hanging)
- **Multi-engine Support**: pdflatex, xelatex, lualatex with automatic error recovery
- **Intelligent Error Parsing**: Provides detailed fix suggestions for common LaTeX issues

### Universal LaTeX Documentation Protocol
- **Mandatory PDF Generation**: Every task automatically generates professional LaTeX documentation
- **Multi-language Support**: Automatic Cyrillic and Unicode support
- **Template-based Generation**: Context-aware document templates for different task types
- **Quality Assurance**: Automatic verification and error correction

### Headless Operation
- **Zero User Interaction**: All tools run completely autonomously
- **Matplotlib Headless Mode**: Automatic `Agg` backend for graph generation
- **Safe Plot Handling**: Automatic figure saving and memory cleanup
- **No Display Dependencies**: Works in server environments without GUI

### Intelligent Task Solving
- **Multi-domain Expertise**: Mathematics, Physics, Programming, Data Analysis
- **Step-by-step Solutions**: Detailed solution methodology with verification
- **Code Generation**: Automatic script generation with proper documentation
- **Error Recovery**: Intelligent retry mechanisms for compilation failures

## 📦 Installation

### Prerequisites
- Python 3.11 or higher
- LaTeX distribution (TeX Live, MiKTeX, or MacTeX)
- Git

### Quick Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/HWAgent.git
cd HWAgent

# Install dependencies
pip install -r requirements.txt

# Verify LaTeX installation
pdflatex --version
```

### LaTeX Requirements
The system requires a working LaTeX installation with these packages:
- `amsmath`, `amsfonts`, `amssymb`, `amsthm` (automatically included)
- `mathtools`, `graphicx`, `geometry` (automatically included)
- `babel`, `fontenc` (for multilingual support)
- `listings`, `xcolor` (for code highlighting)

## 🎯 Quick Start

### Basic Usage

```python
from hwagent.core.agent import HWAgent

# Initialize the agent
agent = HWAgent()

# Solve a mathematical problem
result = agent.solve_task(
    "Solve the differential equation: dy/dx + 2y = 3x^2",
    task_type="math"
)

# LaTeX document and PDF are automatically generated
print(f"Solution: {result.solution}")
print(f"PDF generated: {result.pdf_path}")
```

### Working with LaTeX Tools

```python
from hwagent.tools import UnifiedLaTeXTool, LaTeXFixTool

# Create and compile LaTeX document with automatic preprocessing
latex_tool = UnifiedLaTeXTool()

# Content with quotes will be automatically cleaned
content = """'''
\\documentclass{article}
\\begin{document}
\\section{Test}
Hello world: $E = mc^2$
\\end{document}
'''"""

result = latex_tool.execute(
    filepath="test.tex",
    content=content,
    compile=True
)

# Quotes removed, math packages added, PDF compiled
print(result.message)  # Shows: "quotes removed, packages enhanced"
```

### Advanced Features

```python
# Fix existing LaTeX files with enhanced processing
fix_tool = LaTeXFixTool()

result = fix_tool.execute(
    filepath="document.tex",
    task_type="math"
)

# Comprehensive fixing including quote removal and package enhancement
print(f"Fixed: {result.metadata['quotes_removed']}")
print(f"Enhanced: {result.metadata['packages_enhanced']}")
```

## 🛠 Tool System

### LaTeX Tools

| Tool | Description | Key Features |
|------|-------------|--------------|
| `UnifiedLaTeXTool` | Complete LaTeX workflow | Quote removal, package enhancement, compilation |
| `SimpleLaTeXTool` | Reliable document creation | Clean processing, error analysis |
| `LaTeXCompileTool` | Advanced compilation | Multi-engine, preprocessing, error recovery |
| `LaTeXFixTool` | Document repair | Template regeneration, comprehensive fixing |

### Analysis Tools

| Tool | Description | Key Features |
|------|-------------|--------------|
| `PythonAnalysisTool` | Code analysis and execution | Headless matplotlib, safe execution |
| `MathSolverTool` | Mathematical problem solving | Symbolic computation, verification |
| `DataAnalysisTool` | Data processing and visualization | Automatic graph generation, statistics |

## 📚 Documentation Structure

Every task generates comprehensive documentation:

```
output/
├── solution.tex          # Main LaTeX document
├── solution.pdf          # Compiled PDF
├── verification.py       # Solution verification script
├── figures/              # Generated graphs and images
│   ├── plot_1.png
│   └── analysis_chart.png
└── data/                 # Supporting data files
    └── results.csv
```

## 🔧 Configuration

### Environment Setup

```bash
# Set environment variables
export HWAGENT_TMP_DIR="/tmp/hwagent"
export HWAGENT_OUTPUT_DIR="./output"
export MATPLOTLIB_BACKEND="Agg"  # Headless mode
```

### Agent Configuration

```python
# Configure agent behavior
config = {
    "latex_engine": "pdflatex",  # or "xelatex", "lualatex"
    "auto_compile": True,
    "remove_quotes": True,
    "enhance_packages": True,
    "timeout": 30,
    "retry_attempts": 3
}

agent = HWAgent(config=config)
```

## 🧪 Testing

```bash
# Run comprehensive tests
python -m pytest tests/ -v

# Test LaTeX tools specifically
python -m pytest tests/test_latex_tools.py -v

# Test quote removal functionality
python -m pytest tests/test_quote_removal.py -v
```

## 🔍 Troubleshooting

### Common Issues

1. **LaTeX Compilation Fails**
   - Ensure LaTeX distribution is installed
   - Check `pdflatex --version`
   - Verify write permissions in output directory

2. **Quotes Not Removed**
   - Check content format (should be string)
   - Verify tool initialization
   - Enable debug logging

3. **Matplotlib Display Errors**
   - Ensure `MATPLOTLIB_BACKEND=Agg` is set
   - Check headless mode configuration
   - Verify no display-related code in scripts

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable detailed logging for LaTeX tools
agent = HWAgent(debug=True)
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- All code and comments in English
- Use modern Python features (pattern matching, new-style typing)
- Follow KISS and DRY principles
- Add comprehensive tests for new features
- Ensure LaTeX tools handle quote removal correctly

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- LaTeX community for comprehensive documentation
- matplotlib developers for headless backend support
- Python community for modern language features
- Contributors who helped enhance the quote removal functionality

---

**HWAgent** - Making homework solutions professional, automatic, and reliable with enhanced LaTeX processing capabilities. 