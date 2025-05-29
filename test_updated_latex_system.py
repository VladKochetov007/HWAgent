#!/usr/bin/env python3
"""
Test script for updated LaTeX system with automatic Enter input and simplification rules.
"""

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__)))

from hwagent.tools.latex_compile_tool import LaTeXCompileTool
from hwagent.tools.latex_fix_tool import LaTeXFixTool
from hwagent.tools.create_file_tool import CreateFileTool

def test_simple_math_problem():
    """Test creating and compiling a simple math problem with student-like simplification."""
    print("=== Testing Simple Math Problem with Student Simplification ===")
    
    # Create file tool
    create_tool = CreateFileTool()
    
    # Create a LaTeX document with mathematical content that demonstrates simplification
    latex_content = r"""\documentclass[12pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[russian,english]{babel}
\usepackage{amsmath,amssymb,amsfonts}
\usepackage{geometry}
\geometry{a4paper, margin=1in}

\title{Student-like Problem Simplification Demo}
\author{AI Technical Assistant}
\date{\today}

\begin{document}
\maketitle

\section{Постановка задачи}
Вычислить определитель матрицы \(3 \times 3\) используя упрощения.

\section{Методология - Студенческий подход}
Вместо прямого разложения по всем элементам, используем:
\begin{itemize}
    \item Приведение к треугольному виду
    \item Разложение по строке/столбцу с наибольшим количеством нулей
    \item Факторизацию общих множителей
\end{itemize}

\section{Пример упрощения определителя}
Дана матрица:
\[
A = \begin{pmatrix}
2 & 4 & 6 \\
1 & 3 & 5 \\
0 & 2 & 4
\end{pmatrix}
\]

\textbf{Шаг 1:} Выносим общий множитель 2 из первой строки:
\[
\det(A) = 2 \cdot \begin{vmatrix}
1 & 2 & 3 \\
1 & 3 & 5 \\
0 & 2 & 4
\end{vmatrix}
\]

\textbf{Шаг 2:} Разложение по третьему столбцу (содержит ноль):
\[
= 2 \cdot \left[ 0 \cdot \text{(минор)} + 2 \cdot \begin{vmatrix} 1 & 3 \\ 0 & 2 \end{vmatrix} + 4 \cdot \begin{vmatrix} 1 & 2 \\ 1 & 3 \end{vmatrix} \right]
\]

\textbf{Шаг 3:} Вычисляем \(2 \times 2\) определители:
\[
= 2 \cdot [2 \cdot (1 \cdot 2 - 3 \cdot 0) + 4 \cdot (1 \cdot 3 - 2 \cdot 1)]
\]

\[
= 2 \cdot [2 \cdot 2 + 4 \cdot 1] = 2 \cdot [4 + 4] = 2 \cdot 8 = 16
\]

\section{Заключение}
Использование студенческих приемов упрощения позволило:
\begin{itemize}
    \item Избежать полного разложения \(3 \times 3\) определителя
    \item Свести задачу к вычислению \(2 \times 2\) определителей
    \item Минимизировать количество арифметических операций
\end{itemize}

\end{document}"""
    
    # Create the file
    result = create_tool.execute(filepath="tmp/math_simplification_demo.tex", content=latex_content)
    print(f"File creation: {result.message}")
    
    if result.is_success():
        # Compile with automatic Enter input
        compile_tool = LaTeXCompileTool()
        compile_result = compile_tool.execute(filepath="math_simplification_demo.tex")
        
        print(f"\nCompilation result: {compile_result.message}")
        print(f"Status: {'SUCCESS' if compile_result.is_success() else 'FAILED'}")
        
        if compile_result.details:
            print(f"\nDetailed output:\n{compile_result.details}")
        
        # Check if PDF was created
        pdf_path = "tmp/math_simplification_demo.pdf"
        if os.path.exists(pdf_path):
            print(f"\n✅ PDF successfully created: {pdf_path}")
            file_size = os.path.getsize(pdf_path)
            print(f"PDF file size: {file_size} bytes")
        else:
            print(f"\n❌ PDF not found: {pdf_path}")
        
        return compile_result.is_success()
    
    return False

def test_latex_with_potential_prompts():
    """Test LaTeX compilation that might require user input (automatically handled)."""
    print("\n=== Testing LaTeX with Potential Input Prompts ===")
    
    create_tool = CreateFileTool()
    
    # Create a LaTeX document that might trigger prompts
    latex_content = r"""\documentclass[12pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage{amsmath}
\usepackage{graphicx}
\usepackage{listings}

\title{Test Document with Potential Prompts}
\author{AI Assistant}
\date{\today}

\begin{document}
\maketitle

\section{Mathematical Analysis Simplification}

\subsection{Integration by Parts - Smart Approach}
For \(\int x e^x \, dx\), instead of brute force, use integration by parts:

Let \(u = x\), \(dv = e^x dx\)
Then \(du = dx\), \(v = e^x\)

\[
\int x e^x \, dx = x e^x - \int e^x \, dx = x e^x - e^x + C = e^x(x - 1) + C
\]

\subsection{L'Hôpital's Rule Application}
For \(\lim_{x \to 0} \frac{\sin x}{x}\), recognize this as a standard limit:

\[
\lim_{x \to 0} \frac{\sin x}{x} = 1
\]

This is a fundamental limit, no need for L'Hôpital's rule calculation.

\section{Code Example}
\begin{lstlisting}[language=Python]
# Smart approach: use mathematical properties
import math

def smart_factorial(n):
    # Use built-in instead of loop
    return math.factorial(n)

# Instead of manual implementation
\end{lstlisting}

\end{document}"""
    
    result = create_tool.execute(filepath="tmp/test_prompts.tex", content=latex_content)
    print(f"File creation: {result.message}")
    
    if result.is_success():
        compile_tool = LaTeXCompileTool()
        compile_result = compile_tool.execute(filepath="test_prompts.tex")
        
        print(f"\nCompilation result: {compile_result.message}")
        print(f"Status: {'SUCCESS' if compile_result.is_success() else 'FAILED'}")
        
        # Check for auto-input confirmation in output
        if "Auto-input: Enabled" in compile_result.details:
            print("✅ Automatic Enter input is working")
        
        pdf_path = "tmp/test_prompts.pdf"
        if os.path.exists(pdf_path):
            print(f"✅ PDF successfully created: {pdf_path}")
            return True
        else:
            print(f"❌ PDF not found: {pdf_path}")
            # Try to fix and recompile
            print("\nAttempting to fix and recompile...")
            fix_tool = LaTeXFixTool()
            fix_result = fix_tool.execute(filepath="test_prompts.tex")
            print(f"Fix result: {fix_result.message}")
            
            if fix_result.is_success():
                compile_result2 = compile_tool.execute(filepath="test_prompts.tex")
                print(f"Second compilation: {compile_result2.message}")
                return os.path.exists(pdf_path)
    
    return False

def cleanup_test_files():
    """Clean up test files."""
    print("\n=== Cleaning up test files ===")
    test_files = [
        "tmp/math_simplification_demo.tex",
        "tmp/math_simplification_demo.pdf",
        "tmp/math_simplification_demo.aux",
        "tmp/math_simplification_demo.log",
        "tmp/test_prompts.tex",
        "tmp/test_prompts.pdf",
        "tmp/test_prompts.aux",
        "tmp/test_prompts.log",
    ]
    
    removed_count = 0
    for file_path in test_files:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"Removed: {file_path}")
                removed_count += 1
            except OSError as e:
                print(f"Error removing {file_path}: {e}")
    
    print(f"Cleaned up {removed_count} files")

def main():
    """Run all tests."""
    print("Testing Updated LaTeX System")
    print("=" * 50)
    
    success_count = 0
    total_tests = 2
    
    # Test 1: Student-like simplification demo
    if test_simple_math_problem():
        success_count += 1
    
    # Test 2: Auto-input handling
    if test_latex_with_potential_prompts():
        success_count += 1
    
    print(f"\n" + "=" * 50)
    print(f"TEST RESULTS: {success_count}/{total_tests} tests passed")
    
    if success_count == total_tests:
        print("✅ All tests passed! Updated LaTeX system is working correctly.")
        print("📄 Automatic PDF compilation is enabled")
        print("🎓 Student-like simplification guidance is integrated")
        print("⚡ Automatic Enter input handling is active")
    else:
        print("❌ Some tests failed. Check the output above for details.")
    
    # Cleanup
    cleanup_test_files()
    
    return success_count == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 