#!/usr/bin/env python3
r"""
Test script for Cyrillic LaTeX error fixing functionality.
This tests the improved handling of "Command \CYRT unavailable in encoding OT1" errors.
"""

import os
import tempfile
from hwagent.tools.latex_fix_tool import LaTeXFixTool
from hwagent.tools.unified_latex_tool import UnifiedLaTeXTool

def test_cyrillic_error_detection_and_fix():
    """Test detection and fixing of Cyrillic encoding errors"""
    
    print("=== Testing Cyrillic LaTeX Error Detection and Fixing ===\n")
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        
        # Test 1: LaTeX document with Cyrillic text but missing T2A encoding
        print("1. Testing LaTeX with Cyrillic text but missing proper encoding...")
        
        broken_latex = r"""\documentclass{article}
\usepackage[utf8]{inputenc}
\usepackage[russian]{babel}
\usepackage{amsmath}

\title{Математическое решение}
\author{Тестовый автор}
\date{\today}

\begin{document}
\maketitle

\section{Введение}
Это тестовый документ с русским текстом для проверки исправления ошибок кириллицы.

\section{Математические формулы}
Рассмотрим функцию:
\[ f(x) = x^2 + 2x + 1 \]

\section{Заключение}
Результаты показывают правильность решения.

\end{document}"""
        
        # Save broken LaTeX file
        broken_file = os.path.join(temp_dir, "broken_cyrillic.tex")
        with open(broken_file, 'w', encoding='utf-8') as f:
            f.write(broken_latex)
        
        print(f"   Created broken LaTeX file: {broken_file}")
        
        # Test unified_latex compilation (should detect error)
        print("   Testing compilation with unified_latex tool...")
        
        unified_tool = UnifiedLaTeXTool(tmp_directory=temp_dir)
        compile_result = unified_tool._compile_document(
            filepath="broken_cyrillic.tex",
            engine="pdflatex"
        )
        
        print(f"   Compilation result: {compile_result.success}")
        if not compile_result.success:
            print(f"   Expected error detected: {compile_result.message}")
        
        # Test LaTeX fix tool
        print("   Testing latex_fix tool...")
        
        fix_tool = LaTeXFixTool(tmp_directory=temp_dir)
        fix_result = fix_tool.execute(
            filepath="broken_cyrillic.tex", 
            task_type="math"
        )
        
        print(f"   Fix result: {fix_result.success}")
        print(f"   Fix message: {fix_result.message}")
        
        # Verify fixed content
        print("   Checking fixed content...")
        with open(broken_file, 'r', encoding='utf-8') as f:
            fixed_content = f.read()
        
        # Check if proper packages were added
        has_t2a = r'\usepackage[T2A,OT1]{fontenc}' in fixed_content
        has_proper_babel = r'\usepackage[russian,english,ukrainian]{babel}' in fixed_content
        
        print(f"   T2A fontenc added: {has_t2a}")
        print(f"   Proper babel added: {has_proper_babel}")
        
        # Test compilation after fix
        print("   Testing compilation after fix...")
        compile_after_fix = unified_tool._compile_document(
            filepath="broken_cyrillic.tex",
            engine="pdflatex"
        )
        
        print(f"   Compilation after fix: {compile_after_fix.success}")
        if compile_after_fix.success:
            print("   ✅ PDF compilation successful after fix!")
        else:
            print(f"   ❌ Still has issues: {compile_after_fix.message}")
        
        print()
        
        # Test 2: Template generation with Russian language
        print("2. Testing template generation with Russian language...")
        
        template_result = unified_tool._generate_template(
            filepath="russian_template.tex",
            task_type="math",
            language="russian",
            title="Тестовый математический документ"
        )
        
        print(f"   Template generation: {template_result.success}")
        
        # Check template content
        template_file = os.path.join(temp_dir, "russian_template.tex")
        if os.path.exists(template_file):
            with open(template_file, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            has_correct_fontenc = r'\usepackage[T2A,OT1]{fontenc}' in template_content
            print(f"   Template has correct fontenc: {has_correct_fontenc}")
            
            # Try to compile template
            template_compile = unified_tool._compile_document(
                filepath="russian_template.tex",
                engine="pdflatex"
            )
            print(f"   Template compilation: {template_compile.success}")
        
        print()
        
        # Test 3: Direct fix of specific Cyrillic errors
        print("3. Testing specific Cyrillic error patterns...")
        
        specific_error_latex = r"""\documentclass{article}
\usepackage[utf8]{inputenc}
\title{Тест}
\begin{document}
\maketitle
Русский текст здесь.
\end{document}"""
        
        specific_file = os.path.join(temp_dir, "specific_error.tex")
        with open(specific_file, 'w', encoding='utf-8') as f:
            f.write(specific_error_latex)
        
        # Apply fix
        specific_fix = fix_tool.execute(
            filepath="specific_error.tex",
            task_type="general"
        )
        
        print(f"   Specific error fix: {specific_fix.success}")
        
        # Check if Cyrillic detection worked
        with open(specific_file, 'r', encoding='utf-8') as f:
            specific_fixed = f.read()
        
        cyrillic_detected = (r'\usepackage[T2A,OT1]{fontenc}' in specific_fixed and
                           r'babel' in specific_fixed)
        print(f"   Cyrillic support automatically added: {cyrillic_detected}")
        
        # Final compilation test
        final_compile = unified_tool._compile_document(
            filepath="specific_error.tex",
            engine="pdflatex"
        )
        print(f"   Final compilation: {final_compile.success}")
        
        print("\n=== Test Summary ===")
        print(f"✅ Cyrillic error detection: {'PASS' if not compile_result.success else 'FAIL'}")
        print(f"✅ LaTeX fix tool: {'PASS' if fix_result.success else 'FAIL'}")
        print(f"✅ Post-fix compilation: {'PASS' if compile_after_fix.success else 'FAIL'}")
        print(f"✅ Template generation: {'PASS' if template_result.success else 'FAIL'}")
        print(f"✅ Automatic Cyrillic detection: {'PASS' if cyrillic_detected else 'FAIL'}")
        
        return {
            'error_detection': not compile_result.success,
            'fix_applied': fix_result.success,
            'post_fix_compilation': compile_after_fix.success,
            'template_generation': template_result.success,
            'cyrillic_detection': cyrillic_detected
        }

if __name__ == "__main__":
    results = test_cyrillic_error_detection_and_fix()
    
    # Summary
    all_passed = all(results.values())
    print(f"\n{'='*50}")
    print(f"OVERALL RESULT: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    print(f"{'='*50}")
    
    if not all_passed:
        print("\nFailed tests:")
        for test_name, result in results.items():
            if not result:
                print(f"  - {test_name}") 