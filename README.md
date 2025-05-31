# HWAgent - Advanced AI Assistant for Technical Tasks

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Headless Compatible](https://img.shields.io/badge/Headless-Compatible-green.svg)](./work/TECHNICAL_OVERVIEW.md)
[![LaTeX Support](https://img.shields.io/badge/LaTeX-Universal-orange.svg)](./work/UNIVERSAL_LATEX_PROTOCOL.md)

> **HWAgent** - A headless-first AI assistant system specialized in technical tasks with automatic LaTeX documentation, enhanced plotting capabilities, and universal language support.

## 🌟 Key Features

### 🛡️ **Headless-First Design**
- **Complete GUI Independence**: No visual displays, perfect for servers
- **Automated Plotting**: All matplotlib operations save to files automatically  
- **Safe LaTeX Compilation**: Batch mode with timeout protection
- **Resource Management**: Automatic cleanup and memory management

### 📝 **Universal LaTeX System**
- **Automatic Documentation**: Every task generates professional LaTeX documents
- **Multi-Language Support**: English default with LLM-controlled localization
- **Intelligent Error Correction**: Advanced LaTeX error detection and fixing
- **Multiple Engines**: Support for pdflatex, xelatex, and lualatex

### 🧮 **Advanced Technical Capabilities**
- **Mathematical Computing**: SymPy, NumPy, SciPy integration
- **Data Analysis**: Pandas, statistical analysis, visualization
- **Programming Support**: Algorithm implementation and analysis
- **Physics Simulations**: Computational physics and modeling

### 🔧 **Robust Tool System**
- **Modular Architecture**: Extensible tool-based design
- **Error Recovery**: Intelligent error handling and correction
- **Timeout Protection**: Prevents system hanging
- **Safety-First**: Input validation and secure execution

## 🚀 Quick Start

### Installation
```bash
# Clone repository
git clone https://github.com/your-repo/HWAgent.git
cd HWAgent

# Install dependencies
pip install -r requirements.txt

# Configure API key
export OPENROUTER_API_KEY="your_api_key"

# Test installation
python -m hwagent --test-headless
```

### Basic Usage
```bash
# Web interface (recommended)
python app.py
# Open browser to http://localhost:8000

# Command line
python -m hwagent "Solve x^2 + 5x + 6 = 0 using quadratic formula"

# Python API
python -c "
from hwagent import HWAgent
agent = HWAgent()
result = agent.execute('Calculate integral of x^2 from 0 to 5')
print(f'Generated: {result.pdf_file}')
"
```

## 📊 Example Outputs

### Mathematical Problem
**Input**: "Find the derivative of f(x) = x³ + 2x² - 5x + 1"

**Generated Files**:
- `derivative_solution.tex` - Complete LaTeX derivation
- `derivative_solution.pdf` - Professional PDF document  
- `verification.py` - Python verification script
- `function_plot.png` - Function and derivative visualization

### Programming Task
**Input**: "Implement binary search algorithm with complexity analysis"

**Generated Files**:
- `binary_search_analysis.tex` - Algorithm documentation
- `binary_search_analysis.pdf` - Technical report
- `binary_search.py` - Implementation with comments
- `complexity_chart.png` - Performance visualization

### Data Analysis
**Input**: "Analyze correlation between temperature and sales data"

**Generated Files**:
- `correlation_analysis.tex` - Statistical report
- `correlation_analysis.pdf` - Professional document
- `analysis_script.py` - Data processing code
- `correlation_plot.png` - Statistical visualization
- `summary_stats.png` - Summary charts

## 🛠️ System Architecture

```
HWAgent/
├── hwagent/
│   ├── core/              # Core system components
│   │   ├── agent.py       # Main agent logic
│   │   ├── tools/         # Tool management
│   │   └── config/        # Configuration handling
│   ├── tools/             # Specialized tools
│   │   ├── unified_latex_tool.py    # Complete LaTeX workflow
│   │   ├── latex_compile_tool.py    # Compilation engine
│   │   ├── latex_fix_tool.py        # Error correction
│   │   ├── execute_code_tool.py     # Python execution
│   │   └── plotting_tools.py        # Visualization
│   ├── config/            # System configuration
│   │   ├── prompts.yaml   # LLM prompts and requirements
│   │   └── tools.yaml     # Tool specifications
│   └── ui/                # Web interface
│       ├── app.py         # Flask application
│       └── templates/     # Web templates
├── tests/                 # Comprehensive test suite
├── work/                  # Documentation
│   ├── README.md          # This file
│   ├── USER_GUIDE.md      # Detailed user guide
│   ├── TECHNICAL_OVERVIEW.md        # System architecture
│   ├── UNIVERSAL_LATEX_PROTOCOL.md  # LaTeX documentation system
│   ├── THOUGHT_STREAMING_GUIDE.md   # LLM interaction patterns
│   ├── VERIFICATION_REQUIREMENTS.md # Quality assurance
│   └── LATEX_FIXES_SUMMARY.md       # Error correction guide
└── requirements.txt       # Python dependencies
```

## 🔧 Configuration

### Environment Variables
```bash
# Required
export OPENROUTER_API_KEY="your_api_key"

# Optional
export HWAGENT_HEADLESS="true"          # Force headless mode
export HWAGENT_TIMEOUT="30"             # Timeout in seconds
export HWAGENT_LANGUAGE="english"       # Default language
export HWAGENT_TMP_PATH="/tmp/hwagent"   # Temporary files location
```

### Configuration File (`~/.hwagent/config.yaml`)
```yaml
api:
  provider: openrouter
  model: "anthropic/claude-3-sonnet"

system:
  headless: true
  timeout: 30
  auto_cleanup: true

latex:
  engine: "pdflatex"
  interaction_mode: "batchmode"
  font_encoding: "T1"

plotting:
  backend: "Agg"
  dpi: 300
  format: "png"
  
languages:
  default: "english"
  auto_detect: true
```

## 🛡️ Headless Operation Guarantees

### Matplotlib Safety
```python
# CRITICAL: Always set before pyplot imports
import matplotlib
matplotlib.use('Agg')  # Headless backend
import matplotlib.pyplot as plt

# All plotting saves to files
plt.figure()
plt.plot(data)
plt.savefig('output.png', dpi=300, bbox_inches='tight')
plt.close()  # Cleanup
# NEVER use plt.show() - will raise error
```

### LaTeX Compilation Safety
```bash
# All compilations use safe parameters
pdflatex -interaction=batchmode -file-line-error -synctex=1 document.tex
```

### Resource Protection
- **30-second timeouts** on all operations
- **Process isolation** prevents system hangs
- **Memory limits** prevent resource exhaustion
- **Automatic cleanup** of temporary files

## 📝 Universal LaTeX Protocol

### Language Support Architecture
```latex
% Base template (English)
\documentclass[11pt,a4paper]{article}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage[english]{babel}

% LLM adds as needed:
% Russian: \usepackage[T2A]{fontenc} \usepackage[russian]{babel}
% German:  \usepackage[german]{babel}
% French:  \usepackage[french]{babel}
```

### Document Templates
1. **Mathematical**: `\documentclass{amsart}` for equations and proofs
2. **Programming**: `\documentclass{article}` with `listings` package
3. **Analysis**: `\documentclass{report}` for data analysis
4. **Physics**: `\documentclass{article}` with `physics` package

### Error Correction System
- **Automatic Package Installation**: Missing package detection
- **Command Correction**: Fix undefined commands
- **Structure Repair**: Complete missing document elements
- **Math Mode Fixing**: Proper mathematical notation

## 🔍 Quality Assurance

### Testing Strategy
```bash
# Run full test suite
python -m pytest tests/ -v

# Test specific components
python -m pytest tests/test_headless_mode.py      # Headless operations
python -m pytest tests/test_latex_tools.py        # LaTeX system
python -m pytest tests/test_core_functionality.py # Core features
python -m pytest tests/test_error_recovery.py     # Error handling
```

### Quality Metrics
- **Compilation Success**: >95% automatic LaTeX compilation
- **Error Recovery**: >90% automatic error resolution
- **Headless Compliance**: 100% GUI-free operation
- **Response Time**: <30s for typical tasks

### Validation Checklist
- ✅ Headless backend set before plotting
- ✅ All figures saved to files, none displayed
- ✅ LaTeX compilation in batch mode
- ✅ All temporary files cleaned up
- ✅ No user interaction required
- ✅ Error logs captured and analyzed

## 🚀 Performance Optimization

### LaTeX Compilation
- **Engine Selection**: Automatic optimal engine choice
- **Package Caching**: Reduce redundant package loading
- **Parallel Compilation**: Multiple document support
- **Memory Management**: Efficient resource utilization

### Code Execution
- **Process Isolation**: Safe execution environments
- **Resource Monitoring**: CPU and memory tracking
- **Result Caching**: Avoid redundant computations
- **Timeout Management**: Prevent runaway processes

## 🔐 Security Features

### Execution Safety
- **Input Validation**: Sanitize all inputs
- **Command Whitelisting**: Only safe operations allowed
- **Path Validation**: Prevent directory traversal
- **Resource Limits**: CPU, memory, time constraints

### Data Protection
- **Local Processing**: All computations local
- **Secure API Communication**: HTTPS only
- **Temporary File Security**: Secure cleanup
- **Log Filtering**: Sensitive data protection

## 📖 Documentation

### User Guides
- **[User Guide](./work/USER_GUIDE.md)**: Complete usage instructions
- **[Technical Overview](./work/TECHNICAL_OVERVIEW.md)**: System architecture
- **[LaTeX Protocol](./work/UNIVERSAL_LATEX_PROTOCOL.md)**: Documentation system

### Developer Guides  
- **[Thought Streaming](./work/THOUGHT_STREAMING_GUIDE.md)**: LLM interaction patterns
- **[Verification](./work/VERIFICATION_REQUIREMENTS.md)**: Quality requirements
- **[LaTeX Fixes](./work/LATEX_FIXES_SUMMARY.md)**: Error correction guide

## 🤝 Contributing

### Development Setup
```bash
# Clone and setup development environment
git clone https://github.com/your-repo/HWAgent.git
cd HWAgent
python -m venv venv
source venv/bin/activate
pip install -e .
pip install -r requirements-dev.txt
```

### Code Standards
- **Language**: English for all code and comments
- **Python Style**: Modern Python 3.8+ features
- **Type Hints**: Use `|` instead of `Union`, `list[T]` instead of `List[T]`
- **Principles**: Follow KISS and DRY principles
- **Documentation**: Comprehensive docstrings and comments

### Testing Requirements
- All new features must include tests
- Maintain >90% code coverage
- Include headless mode tests
- Verify LaTeX compilation functionality

## 📞 Support

### Getting Help
- **Documentation**: Comprehensive guides in `work/` directory
- **Issues**: GitHub issue tracker for bugs and features
- **Discussions**: Community forum for usage questions
- **Support**: Direct email for critical issues

### Common Issues
- **LaTeX Errors**: Check `work/LATEX_FIXES_SUMMARY.md`
- **Headless Problems**: Verify matplotlib backend with `matplotlib.get_backend()`
- **API Issues**: Confirm `OPENROUTER_API_KEY` environment variable
- **Performance**: Check timeout settings and resource limits

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🎯 Project Status

- **Status**: Production Ready ✅
- **Headless Compatibility**: 100% ✅  
- **LaTeX Support**: Universal ✅
- **Error Recovery**: Advanced ✅
- **Performance**: Optimized ✅

---

**HWAgent** - Where AI meets technical excellence. Built for the headless future. 🚀

### Latest Updates

#### Version 2.0 - Headless-First Release
- ✨ Complete headless operation guarantee
- 📝 Universal LaTeX documentation system  
- 🛡️ Advanced error recovery and timeout protection
- 🌍 Multi-language support with English defaults
- 🔧 Modular tool architecture
- 📊 Enhanced plotting and visualization
- 🧮 Advanced mathematical computing capabilities
- 🔐 Security-focused design with input validation
- 📈 Performance optimization and resource management
- 📚 Comprehensive documentation and user guides 