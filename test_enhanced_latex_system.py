#!/usr/bin/env python3
"""
Test Enhanced LaTeX System
Tests the new Smart LaTeX Generator and improved LaTeX workflow
"""

import os
import sys
from hwagent.tools.smart_latex_generator_tool import SmartLaTeXGenerator
from hwagent.tools.latex_compile_tool import LaTeXCompileTool
from hwagent.tools.latex_fix_tool import LaTeXFixTool

def test_smart_latex_generator():
    """Test the Smart LaTeX Generator with different task types"""
    
    print("🚀 Testing Smart LaTeX Generator")
    print("=" * 50)
    
    generator = SmartLaTeXGenerator()
    
    # Test cases for different task types
    test_cases = [
        {
            "name": "Math Problem",
            "filepath": "test_math.tex",
            "title": "Вычисление Интеграла", 
            "content_sections": {
                "problem_statement": "Требуется вычислить интеграл \\(\\int (x^2 + 1) dx\\)",
                "methodology": "Используем правило степени для интегрирования",
                "solution_steps": "\\[\\int (x^2 + 1) dx = \\int x^2 dx + \\int 1 dx = \\frac{x^3}{3} + x + C\\]",
                "computational_verification": "Проверка с помощью Python и sympy",
                "analysis": "Результат соответствует аналитическому решению",
                "conclusion": "Интеграл успешно вычислен"
            },
            "task_type": "math",
            "language": "russian"
        },
        {
            "name": "Programming Problem",
            "filepath": "test_programming.tex",
            "title": "Sorting Algorithm Implementation",
            "content_sections": {
                "problem_description": "Implement and analyze quicksort algorithm",
                "algorithm_design": "Divide-and-conquer approach with pivot selection",
                "implementation": "Python implementation with optimization",
                "testing": "Test with various input sizes and patterns",
                "performance_analysis": "Time complexity: O(n log n) average, O(n²) worst case",
                "conclusions": "Quicksort is efficient for most practical applications"
            },
            "task_type": "programming",
            "language": "english"
        }
    ]
    
    success_count = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}: {test_case['name']}")
        print("-" * 30)
        
        result = generator.execute(
            filepath=test_case["filepath"],
            title=test_case["title"],
            content_sections=test_case["content_sections"],
            task_type=test_case["task_type"],
            language=test_case["language"]
        )
        
        if result.is_success():
            print(f"✅ {result.message}")
            success_count += 1
            
            # Check if file was created
            if os.path.exists(test_case["filepath"]):
                print(f"✅ File created: {test_case['filepath']}")
                
                # Check file content
                with open(test_case["filepath"], 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Basic content checks
                checks = [
                    ("documentclass", "\\documentclass" in content),
                    ("inputenc", "inputenc" in content),
                    ("babel", "babel" in content),
                    ("begin document", "\\begin{document}" in content),
                    ("end document", "\\end{document}" in content),
                    ("title", test_case["title"] in content or "title" in content.lower()),
                ]
                
                for check_name, check_result in checks:
                    status = "✅" if check_result else "❌"
                    print(f"  {status} {check_name}")
            else:
                print(f"❌ File not created: {test_case['filepath']}")
        else:
            print(f"❌ {result.message}")
            if result.details:
                print(f"   Details: {result.details}")
    
    print(f"\n📊 Smart LaTeX Generator Test Results: {success_count}/{len(test_cases)} passed")
    return success_count == len(test_cases)

def test_latex_compilation():
    """Test LaTeX compilation of generated files"""
    
    print("\n🔧 Testing LaTeX Compilation")
    print("=" * 50)
    
    compiler = LaTeXCompileTool()
    
    test_files = [
        "test_math.tex",
        "test_programming.tex"
    ]
    
    success_count = 0
    
    for filepath in test_files:
        if os.path.exists(f"tmp/{filepath}"):
            print(f"\n📄 Compiling: {filepath}")
            
            result = compiler.execute(filepath=filepath)
            
            if result.is_success():
                print(f"✅ {result.message}")
                
                # Check if PDF was created
                pdf_path = f"tmp/{filepath.replace('.tex', '.pdf')}"
                if os.path.exists(pdf_path):
                    print(f"✅ PDF created: {pdf_path}")
                    success_count += 1
                else:
                    print(f"❌ PDF not found: {pdf_path}")
            else:
                print(f"❌ Compilation failed: {result.message}")
                if result.details:
                    print(f"   Details: {result.details}")
        else:
            print(f"⚠️  File not found: tmp/{filepath}")
    
    print(f"\n📊 LaTeX Compilation Results: {success_count}/{len([f for f in test_files if os.path.exists(f'tmp/{f}')])} passed")
    return success_count > 0

def test_latex_fix_tool():
    """Test the LaTeX Fix Tool with intentionally broken LaTeX"""
    
    print("\n🔧 Testing LaTeX Fix Tool")
    print("=" * 50)
    
    # Create intentionally broken LaTeX file
    broken_latex = """\\\\documentclass{article}
\\\\usepackage[utf8]{inputenc}
\\\\usepackage{amsmath}

\\\\title{Broken LaTeX Test}
\\\\author{Test}

\\\\begin{document}
\\\\maketitle

## This is markdown syntax (should be \\section{})
**This is bold** (should be \\textbf{})

Math: $$x^2 + 1$$ (should be \\[ \\])

\\\\end{document}"""
    
    broken_file = "broken_test.tex"
    
    # Create broken file
    os.makedirs("tmp", exist_ok=True)
    with open(f"tmp/{broken_file}", 'w', encoding='utf-8') as f:
        f.write(broken_latex)
    
    print(f"📝 Created broken LaTeX file: tmp/{broken_file}")
    
    # Test fix tool
    fix_tool = LaTeXFixTool()
    result = fix_tool.execute(filepath=f"tmp/{broken_file}", task_type="general")
    
    if result.is_success():
        print(f"✅ {result.message}")
        
        # Check if file was fixed
        with open(f"tmp/{broken_file}", 'r', encoding='utf-8') as f:
            fixed_content = f.read()
        
        # Check fixes
        fixes_applied = [
            ("Double backslashes fixed", "\\\\documentclass" not in fixed_content),
            ("Proper document structure", "\\documentclass" in fixed_content),
            ("UTF-8 encoding", "inputenc" in fixed_content),
            ("Document environment", "\\begin{document}" in fixed_content and "\\end{document}" in fixed_content)
        ]
        
        for fix_name, fix_result in fixes_applied:
            status = "✅" if fix_result else "❌"
            print(f"  {status} {fix_name}")
        
        return True
    else:
        print(f"❌ Fix failed: {result.message}")
        return False

def test_end_to_end_workflow():
    """Test complete end-to-end workflow"""
    
    print("\n🔄 Testing End-to-End Workflow")
    print("=" * 50)
    
    # 1. Generate LaTeX with Smart Generator
    generator = SmartLaTeXGenerator()
    
    test_file = "end_to_end_test.tex"
    
    result = generator.execute(
        filepath=test_file,
        title="Комплексный тест системы",
        content_sections={
            "problem_statement": "Протестировать полный workflow создания LaTeX документа",
            "methodology": "Использовать Smart LaTeX Generator + компиляцию + исправление ошибок",
            "solution": "Создать документ, скомпилировать в PDF, проверить результат",
            "verification_testing": "Автоматические тесты всех компонентов",
            "results_summary": "Система работает корректно и создает качественные документы"
        },
        task_type="general",
        language="russian"
    )
    
    if not result.is_success():
        print(f"❌ Generation failed: {result.message}")
        return False
    
    print("✅ Step 1: LaTeX generated successfully")
    
    # 2. Compile to PDF
    compiler = LaTeXCompileTool()
    compile_result = compiler.execute(filepath=test_file)
    
    if not compile_result.is_success():
        print(f"❌ Compilation failed: {compile_result.message}")
        
        # 3. Try to fix and recompile
        print("🔧 Attempting to fix LaTeX errors...")
        fix_tool = LaTeXFixTool()
        fix_result = fix_tool.execute(filepath=f"tmp/{test_file}", task_type="general")
        
        if fix_result.is_success():
            print("✅ Step 2: LaTeX errors fixed")
            
            # Retry compilation
            compile_result = compiler.execute(filepath=test_file)
            if compile_result.is_success():
                print("✅ Step 3: PDF compiled after fixing")
            else:
                print(f"❌ Compilation still failed: {compile_result.message}")
                return False
        else:
            print(f"❌ Fix failed: {fix_result.message}")
            return False
    else:
        print("✅ Step 2: PDF compiled successfully")
    
    # 4. Verify PDF exists
    pdf_file = f"tmp/{test_file.replace('.tex', '.pdf')}"
    if os.path.exists(pdf_file):
        print(f"✅ Step 3: PDF verified: {pdf_file}")
        return True
    else:
        print(f"❌ PDF not found: {pdf_file}")
        return False

def cleanup_test_files():
    """Clean up test files"""
    test_files = [
        "tmp/test_math.tex", "tmp/test_math.pdf",
        "tmp/test_programming.tex", "tmp/test_programming.pdf", 
        "tmp/broken_test.tex", "tmp/broken_test.pdf",
        "tmp/end_to_end_test.tex", "tmp/end_to_end_test.pdf",
        "tmp/test_math.tex.backup",
        "tmp/broken_test.tex.backup",
        "tmp/end_to_end_test.tex.backup"
    ]
    
    for file in test_files:
        if os.path.exists(file):
            os.remove(file)
            print(f"🗑️  Removed: {file}")
    
    # Remove tmp directory if empty
    try:
        if os.path.exists("tmp") and not os.listdir("tmp"):
            os.rmdir("tmp")
            print("🗑️  Removed empty tmp directory")
    except OSError:
        pass

if __name__ == "__main__":
    print("🧪 Enhanced LaTeX System Test Suite")
    print("=" * 60)
    
    try:
        # Run all tests
        results = []
        
        results.append(("Smart LaTeX Generator", test_smart_latex_generator()))
        results.append(("LaTeX Compilation", test_latex_compilation()))
        results.append(("LaTeX Fix Tool", test_latex_fix_tool()))
        results.append(("End-to-End Workflow", test_end_to_end_workflow()))
        
        # Print summary
        print("\n" + "=" * 60)
        print("🎯 TEST SUMMARY")
        print("=" * 60)
        
        passed = 0
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
            if result:
                passed += 1
        
        print(f"\n📊 Overall Results: {passed}/{len(results)} tests passed")
        
        if passed == len(results):
            print("\n🎉 ALL TESTS PASSED! Enhanced LaTeX system is working correctly!")
        else:
            print(f"\n⚠️  {len(results) - passed} tests failed. Please check the issues above.")
        
        # Clean up
        print("\n🧹 Cleaning up test files...")
        cleanup_test_files()
        
        sys.exit(0 if passed == len(results) else 1)
        
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        sys.exit(1) 