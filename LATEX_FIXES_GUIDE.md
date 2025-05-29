# LaTeX Fixes Guide for HWAgent

## Проблемы и их решения

### 1. Основная проблема: Двойные слеши (`\\`)

**Симптомы:**
- Ошибки типа "There's no line here to end"
- Ошибки типа "Missing \begin{document}"
- LaTeX команды с двойными слешами: `\\documentclass`, `\\usepackage`, `\\begin`, etc.

**Причины:**
1. **Неправильное экранирование в промптах** - когда LLM генерирует LaTeX код, он может добавлять лишние слеши
2. **Проблемы в шаблонах** - использование `{{` вместо `{` в raw strings
3. **Ошибки в обработке строк** - неправильное экранирование при создании файлов

**Решения:**

#### В промптах (`hwagent/config/prompts.yaml`):
```yaml
# ✅ ПРАВИЛЬНО - четкие инструкции
- ✅ NEVER use double backslashes `\\` except for line breaks
- ❌ AVOID: `\\documentclass`, `\\usepackage`, `\\begin`, `\\end` (use single backslash)
- 🔧 USE latex_fix tool if ANY compilation errors occur
```

#### В LaTeX Fix Tool (`hwagent/tools/latex_fix_tool.py`):
- Улучшен метод `_fix_double_backslashes()` для обработки всех случаев
- Добавлены проверки в `_is_severely_broken()` для выявления проблем
- Улучшена финальная очистка в `_final_cleanup()`

### 2. Ошибки "Missing $ inserted"

**Симптомы:**
- LaTeX не может обработать символы `_` и `^` вне математического режима

**Решения:**
- Автоматическое экранирование: `x_1` → `x\_1` или `\(x_1\)`
- Преобразование в математический режим: `x^2` → `\(x^2\)`

### 3. Смешанный Markdown и LaTeX синтаксис

**Симптомы:**
- Заголовки с `##` вместо `\section{}`
- Жирный текст с `**` вместо `\textbf{}`
- Списки с `-` вместо `\item`

**Решения:**
- Автоматическое преобразование в методе `_convert_markdown_to_latex()`

### 4. Отсутствующая структура документа

**Симптомы:**
- Отсутствует `\documentclass`
- Отсутствует `\begin{document}` или `\end{document}`

**Решения:**
- Автоматическое добавление структуры в методе `_fix_structure()`
- Использование шаблонов для полной регенерации

## Инструменты для исправления

### 1. LaTeX Fix Tool
```python
from hwagent.tools.latex_fix_tool import LaTeXFixTool

tool = LaTeXFixTool()
result = tool.execute(filepath="problem.tex", task_type="math")
```

**Возможности:**
- Исправление двойных слешей
- Исправление математических обозначений
- Преобразование Markdown в LaTeX
- Добавление отсутствующей структуры
- Полная регенерация с использованием шаблонов

### 2. Smart LaTeX Generator
```python
from hwagent.tools.smart_latex_generator_tool import SmartLaTeXGenerator

tool = SmartLaTeXGenerator()
result = tool.execute(
    filepath="document.tex",
    title="Заголовок",
    content_sections={
        "problem_statement": "Описание задачи...",
        "solution": "Решение..."
    },
    task_type="math",
    language="russian"
)
```

**Преимущества:**
- Правильная структура с самого начала
- Автоматическое экранирование
- Поддержка разных типов документов
- Многоязычность

### 3. LaTeX Compile Tool
```python
from hwagent.tools.latex_compile_tool import LaTeXCompileTool

tool = LaTeXCompileTool()
result = tool.execute(filepath="document.tex")
```

**Возможности:**
- Компиляция в PDF
- Детальные сообщения об ошибках
- Предложения по исправлению
- Поддержка разных движков LaTeX

## Рекомендуемый workflow

### 1. Создание нового документа
```python
# Используйте Smart LaTeX Generator
generator = SmartLaTeXGenerator()
result = generator.execute(...)
```

### 2. Исправление существующего документа
```python
# 1. Попробуйте исправить
fix_tool = LaTeXFixTool()
fix_result = fix_tool.execute(filepath="document.tex")

# 2. Скомпилируйте
compile_tool = LaTeXCompileTool()
compile_result = compile_tool.execute(filepath="document.tex")

# 3. Если не удалось - повторите исправление
if not compile_result.is_success():
    fix_result = fix_tool.execute(filepath="document.tex", task_type="math")
    compile_result = compile_tool.execute(filepath="document.tex")
```

## Настройка промптов

### Ключевые правила для LLM:
1. **Никогда не используйте двойные слеши** кроме принудительных переносов строк
2. **Всегда используйте latex_fix** при ошибках компиляции
3. **Предпочитайте smart_latex_generator** для создания новых документов
4. **Проверяйте синтаксис** перед финальной отправкой

### Примеры правильных инструкций:
```yaml
- ✅ Use `\documentclass{article}` NOT `\\documentclass{article}`
- ✅ Use `\section{Title}` NOT `## Title`
- ✅ Use `\textbf{bold}` NOT `**bold**`
- ✅ Use `\[ math \]` NOT `$$ math $$`
```

## Тестирование

Запустите тест для проверки исправлений:
```bash
python test_latex_fixes.py
```

Этот тест создает файлы с типичными проблемами и проверяет их исправление и компиляцию.

## Заключение

Основные проблемы с LaTeX в HWAgent связаны с:
1. **Двойными слешами** - решается улучшенным LaTeX Fix Tool
2. **Смешанным синтаксисом** - решается автоматическим преобразованием
3. **Неправильными промптами** - решается обновленными инструкциями

Используйте Smart LaTeX Generator для новых документов и LaTeX Fix Tool для исправления существующих. 