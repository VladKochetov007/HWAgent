# HWAgent - Enhanced AI Assistant with Memory and Advanced Search

An intelligent AI assistant with persistent memory, enhanced web search capabilities, and specialized tools for academic and technical tasks.

## 🚀 Key Features

### 🧠 Persistent Memory System
- **Cross-session continuity**: Remembers previous conversations and solutions
- **Pattern recognition**: Learns from successful approaches and avoids failed ones
- **Contextual insights**: Provides personalized recommendations based on usage patterns
- **Memory search**: Find previous solutions and discussions by topic

### 🔍 Enhanced Web Search
- **Current information priority**: Automatically searches for recent and up-to-date content
- **Multiple search strategies**: Uses various approaches to find the most relevant results
- **Temporal analysis**: Prioritizes recent sources and filters outdated information
- **Technical focus**: Optimized for finding current best practices and documentation

### 📝 Specialized Tools
- **Unified LaTeX**: Advanced document creation with multiple engines and languages
- **Code generation**: Modern Python with pattern matching and new-style typing
- **Academic support**: Research assistance with current information
- **Technical documentation**: Automated generation with proper formatting

## 🛠 Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/HWAgent.git
cd HWAgent
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
# Required for enhanced web search
export LANGSEARCH_API_KEY="your_api_key_here"

# Optional: Configure memory storage location
export HWAGENT_MEMORY_PATH="/path/to/memory/storage"
```

## 🎯 Quick Start

### Basic Usage
```python
from hwagent import HWAgent

# Initialize agent with memory and enhanced search
agent = HWAgent(enable_memory=True, enhanced_search=True)

# The agent automatically uses memory context and enhanced search
response = agent.process("Help me create a LaTeX document for my math homework")
```

### Memory Features
```python
# Check what the agent remembers
agent.memory(action="summary")

# Search previous conversations
agent.memory(action="search", query="LaTeX")

# Get insights about your patterns
agent.memory(action="insights", days=7)
```

### Enhanced Search
```python
# Search for current information
agent.enhanced_web_search(query="Python 3.12 new features", count=5)

# The agent automatically uses enhanced strategies for better results
```

## 📚 Documentation

- **[User Guide](USER_GUIDE_MEMORY_SEARCH.md)**: Complete guide to memory and search features
- **[Technical Documentation](MEMORY_AND_SEARCH_IMPROVEMENTS.md)**: Detailed implementation overview
- **[API Reference](docs/api_reference.md)**: Complete API documentation

## 🔧 Configuration

### Memory System
The memory system is automatically enabled and requires no configuration. Memory data is stored locally and includes:
- Conversation history with context
- Tool usage patterns
- Success/failure tracking
- Session summaries and insights

### Enhanced Search
Configure the enhanced search system:
```yaml
# hwagent/config/prompts.yaml
search_strategies:
  temporal_priority: true
  multiple_attempts: true
  result_analysis: true
  freshness_boost: true
```

## 🎨 Advanced Features

### LaTeX Document Creation
```python
# Create documents with automatic compilation
agent.unified_latex(
    operation="create",
    task_type="math",
    language="russian",
    title="Математический анализ"
)
```

### Memory-Aware Problem Solving
The agent automatically:
- Checks memory for similar previous tasks
- Builds on successful approaches
- Avoids known problematic solutions
- Provides continuity across sessions

### Current Information Research
```python
# Enhanced search automatically prioritizes recent content
agent.enhanced_web_search(query="React 18 best practices 2024")
```

## 🧪 Testing

Run the comprehensive test suite:
```bash
# Test core functionality
python -m pytest tests/

# Test memory and search enhancements
python test_enhanced_memory_search.py

# Test LaTeX tools
python test_latex_tools.py
```

## 📈 Benefits

### For Students
- **Homework continuity**: Builds on previous assignments and solutions
- **Learning patterns**: Adapts to your learning style and preferences
- **Current information**: Always finds the most recent and relevant resources
- **Academic formatting**: Automated LaTeX generation for papers and assignments

### For Developers
- **Code consistency**: Remembers your coding patterns and preferences
- **Best practices**: Finds current best practices and documentation
- **Problem solving**: Builds incrementally on previous solutions
- **Technical accuracy**: Prioritizes official and recent technical sources

### For Researchers
- **Research continuity**: Maintains context across research sessions
- **Current developments**: Finds the latest research and developments
- **Pattern recognition**: Identifies successful research approaches
- **Documentation**: Automated generation of research documents

## 🔄 Migration from Previous Versions

The enhanced system is fully backward compatible:
- Existing tools continue to work unchanged
- Memory system activates automatically
- Enhanced search is used when available
- No configuration changes required

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- LangSearch API for enhanced web search capabilities
- LaTeX community for document processing tools
- Python community for modern language features

## 📞 Support

- **Documentation**: Check the [User Guide](USER_GUIDE_MEMORY_SEARCH.md) for common questions
- **Issues**: Report bugs and request features via GitHub Issues
- **Discussions**: Join community discussions in GitHub Discussions

---

**Latest Update**: Enhanced memory system and advanced web search capabilities for improved continuity and current information retrieval.

## 🚀 Возможности

- **Интеллектуальный чат** с поддержкой потокового вывода
- **Файловый менеджер** для работы с временными файлами
- **LaTeX компиляция и линтинг** с автоматическим исправлением ошибок
- **Адаптивный интерфейс** с поддержкой мобильных устройств
- **Складывающееся боковое меню** с настройками и инструментами
- **WebSocket соединение** для реального времени
- **REST API** для интеграции
- **Поддержка множества инструментов** (создание файлов, выполнение кода, веб-поиск, LaTeX)

## 📋 Требования

- Python 3.8+
- OpenRouter API ключ (или другой совместимый LLM API)
- **LaTeX дистрибутив** (TeX Live, MiKTeX, или аналогичный) для компиляции LaTeX файлов

## 🛠️ Доступные инструменты

- **create_file** - Создание файлов
- **read_file** - Чтение файлов
- **execute_code** - Выполнение Python кода
- **list_files** - Просмотр файлов в директории
- **delete_file** - Удаление файлов
- **web_search** - Поиск в интернете
- **run_command** - Выполнение команд терминала
- **latex_compile** - Компиляция LaTeX файлов в PDF с детектированием ошибок
- **latex_fix** - Автоматическое исправление типичных ошибок LaTeX

### 📝 LaTeX инструменты

#### **latex_compile**
- Компиляция `.tex` файлов в PDF
- Поддержка движков: `pdflatex`, `xelatex`, `lualatex`
- Детальный анализ ошибок с предложениями по исправлению
- Режим только линтинга (без компиляции)
- Дополнительные параметры компиляции

#### **latex_fix**
- Автоматическое исправление типичных ошибок:
  - Отсутствующие `\documentclass` и `\begin{document}`
  - Типичные опечатки в командах
  - Несбалансированные скобки
  - Отсутствующие пакеты для команд
  - Проблемы с математическим режимом
- Создание резервных копий
- Замена на минимальный рабочий документ

### 3. Установка LaTeX (для компиляции документов)

#### Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install texlive-full
```

#### Fedora/CentOS:
```bash
sudo dnf install texlive-scheme-full
```

#### macOS:
```bash
# Установка MacTeX через Homebrew
brew install --cask mactex
```

#### Windows:
- Скачайте и установите [MiKTeX](https://miktex.org/) или [TeX Live](https://www.tug.org/texlive/)

### 4. Запуск сервера
