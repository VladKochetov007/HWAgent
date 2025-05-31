"""
Test suite for quote removal functionality in LaTeX tools.
Verifies that all LaTeX tools correctly remove unwanted quotes from content.
"""

import pytest
import tempfile
import os
from unittest.mock import patch

from hwagent.tools.unified_latex_tool import UnifiedLaTeXTool
from hwagent.tools.simple_latex_tool import SimpleLaTeXTool
from hwagent.tools.latex_fix_tool import LaTeXFixTool
from hwagent.tools.latex_compile_tool import LaTeXCompileTool
from hwagent.core.models import ExecutionStatus


class TestQuoteRemoval:
    """Test quote removal functionality across all LaTeX tools"""
    
    def setup_method(self):
        """Setup test environment"""
        self.tmp_dir = tempfile.mkdtemp()
        self.unified_tool = UnifiedLaTeXTool(self.tmp_dir)
        self.simple_tool = SimpleLaTeXTool(self.tmp_dir)
        self.fix_tool = LaTeXFixTool(self.tmp_dir)
        self.compile_tool = LaTeXCompileTool(self.tmp_dir)
    
    def test_single_quote_removal(self):
        """Test removal of single quotes from beginning and end"""
        content = """'\\documentclass{article}
\\usepackage{amsmath}
\\begin{document}
\\section{Test}
Test content with math: $E = mc^2$
\\end{document}'"""
        
        expected = """\\documentclass{article}
\\usepackage{amsmath}
\\begin{document}
\\section{Test}
Test content with math: $E = mc^2$
\\end{document}"""
        
        # Test unified tool (using LaTeXContentProcessor)
        from hwagent.tools.unified_latex_tool import LaTeXContentProcessor
        result = LaTeXContentProcessor.clean_content(content)
        assert result == expected
        
        # Test simple tool
        result = self.simple_tool._remove_unwanted_quotes(content)
        assert result == expected
        
        # Test fix tool  
        result = self.fix_tool._remove_unwanted_quotes(content)
        assert result == expected
        
        # Test compile tool
        result = self.compile_tool._remove_unwanted_quotes(content)
        assert result == expected
    
    def test_double_quote_removal(self):
        """Test removal of double quotes from beginning and end"""
        content = '''"\\documentclass{article}
\\begin{document}
Hello world
\\end{document}"'''
        
        expected = """\\documentclass{article}
\\begin{document}
Hello world
\\end{document}"""
        
        # Test all tools
        from hwagent.tools.unified_latex_tool import LaTeXContentProcessor
        assert LaTeXContentProcessor.clean_content(content) == expected
        assert self.simple_tool._remove_unwanted_quotes(content) == expected
        assert self.fix_tool._remove_unwanted_quotes(content) == expected
        assert self.compile_tool._remove_unwanted_quotes(content) == expected
    
    def test_backtick_removal(self):
        """Test removal of backticks from beginning and end"""
        content = """`\\documentclass{article}
\\begin{document}
Code example
\\end{document}`"""
        
        expected = """\\documentclass{article}
\\begin{document}
Code example
\\end{document}"""
        
        # Test all tools
        from hwagent.tools.unified_latex_tool import LaTeXContentProcessor
        assert LaTeXContentProcessor.clean_content(content) == expected
        assert self.simple_tool._remove_unwanted_quotes(content) == expected
        assert self.fix_tool._remove_unwanted_quotes(content) == expected
        assert self.compile_tool._remove_unwanted_quotes(content) == expected
    
    def test_multiple_quote_removal(self):
        """Test removal of multiple quotes of same type"""
        content = """'''\\documentclass{article}
\\begin{document}
Multiple quotes test
\\end{document}'''"""
        
        expected = """\\documentclass{article}
\\begin{document}
Multiple quotes test
\\end{document}"""
        
        # Test all tools
        from hwagent.tools.unified_latex_tool import LaTeXContentProcessor
        assert LaTeXContentProcessor.clean_content(content) == expected
        assert self.simple_tool._remove_unwanted_quotes(content) == expected
        assert self.fix_tool._remove_unwanted_quotes(content) == expected
        assert self.compile_tool._remove_unwanted_quotes(content) == expected
    
    def test_mixed_quote_removal(self):
        """Test removal of different types of quotes"""
        content = """'"\\documentclass{article}
\\begin{document}
Mixed quotes test
\\end{document}"'"""
        
        expected = """\\documentclass{article}
\\begin{document}
Mixed quotes test
\\end{document}"""
        
        # Test all tools
        from hwagent.tools.unified_latex_tool import LaTeXContentProcessor
        assert LaTeXContentProcessor.clean_content(content) == expected
        assert self.simple_tool._remove_unwanted_quotes(content) == expected
        assert self.fix_tool._remove_unwanted_quotes(content) == expected
        assert self.compile_tool._remove_unwanted_quotes(content) == expected
    
    def test_no_quotes_to_remove(self):
        """Test content without quotes at beginning/end"""
        content = """\\documentclass{article}
\\begin{document}
No quotes to remove
\\end{document}"""
        
        # Content should remain unchanged
        from hwagent.tools.unified_latex_tool import LaTeXContentProcessor
        assert LaTeXContentProcessor.clean_content(content) == content
        assert self.simple_tool._remove_unwanted_quotes(content) == content
        assert self.fix_tool._remove_unwanted_quotes(content) == content
        assert self.compile_tool._remove_unwanted_quotes(content) == content
    
    def test_quotes_in_middle_preserved(self):
        """Test that quotes in the middle of content are preserved"""
        content = """\\documentclass{article}
\\begin{document}
He said "Hello world" to the 'audience'.
Code: `print('test')`
\\end{document}"""
        
        # Content should remain unchanged (no quotes at edges)
        from hwagent.tools.unified_latex_tool import LaTeXContentProcessor
        assert LaTeXContentProcessor.clean_content(content) == content
        assert self.simple_tool._remove_unwanted_quotes(content) == content
        assert self.fix_tool._remove_unwanted_quotes(content) == content
        assert self.compile_tool._remove_unwanted_quotes(content) == content
    
    def test_empty_content(self):
        """Test handling of empty content"""
        content = ""
        
        # Should handle empty content gracefully
        from hwagent.tools.unified_latex_tool import LaTeXContentProcessor
        assert LaTeXContentProcessor.clean_content(content) == content
        assert self.simple_tool._remove_unwanted_quotes(content) == content
        assert self.fix_tool._remove_unwanted_quotes(content) == content
        assert self.compile_tool._remove_unwanted_quotes(content) == content
    
    def test_whitespace_handling(self):
        """Test that whitespace is properly handled after quote removal"""
        content = """'  \\documentclass{article}
\\begin{document}
Test
\\end{document}  '"""
        
        expected = """\\documentclass{article}
\\begin{document}
Test
\\end{document}"""
        
        # Should remove quotes and strip whitespace
        from hwagent.tools.unified_latex_tool import LaTeXContentProcessor
        assert LaTeXContentProcessor.clean_content(content) == expected
        assert self.simple_tool._remove_unwanted_quotes(content) == expected
        assert self.fix_tool._remove_unwanted_quotes(content) == expected
        assert self.compile_tool._remove_unwanted_quotes(content) == expected


class TestQuoteRemovalIntegration:
    """Integration tests for quote removal in full tool execution"""
    
    def setup_method(self):
        """Setup test environment"""
        self.tmp_dir = tempfile.mkdtemp()
        self.simple_tool = SimpleLaTeXTool(self.tmp_dir)
        self.fix_tool = LaTeXFixTool(self.tmp_dir)
    
    @patch('subprocess.run')
    def test_simple_tool_quote_removal_integration(self, mock_run):
        """Test quote removal in SimpleLaTeXTool full execution"""
        # Mock successful compilation
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Success"
        mock_run.return_value.stderr = ""
        
        content_with_quotes = """'''\\documentclass{article}
\\begin{document}
\\section{Test}
Hello world: $E = mc^2$
\\end{document}'''"""
        
        result = self.simple_tool.execute(
            filepath="test.tex",
            content=content_with_quotes,
            compile=False  # Skip compilation for this test
        )
        
        # Check that execution was successful
        assert result.status == ExecutionStatus.SUCCESS
        assert "quotes removed" in result.message
        assert result.data["quotes_removed"] is True
        
        # Verify file was created without quotes
        filepath = os.path.join(self.tmp_dir, "test.tex")
        with open(filepath, 'r', encoding='utf-8') as f:
            file_content = f.read()
        
        assert not file_content.startswith("'")
        assert not file_content.endswith("'")
        assert "\\documentclass{article}" in file_content
    
    def test_fix_tool_quote_removal_integration(self):
        """Test quote removal in LaTeXFixTool full execution"""
        # Create a test file with quotes
        content_with_quotes = """'''\\documentclass{article}
\\begin{document}
\\section{Test}
Test content
\\end{document}'''"""
        
        filepath = os.path.join(self.tmp_dir, "test.tex")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content_with_quotes)
        
        result = self.fix_tool.execute(
            filepath="test.tex",
            task_type="general"
        )
        
        # Check that execution was successful
        assert result.status == ExecutionStatus.SUCCESS
        assert "quotes removed" in result.message
        assert result.data["quotes_removed"] is True
        
        # Verify file was fixed
        with open(filepath, 'r', encoding='utf-8') as f:
            fixed_content = f.read()
        
        assert not fixed_content.startswith("'")
        assert not fixed_content.endswith("'")
        assert "\\documentclass{article}" in fixed_content


class TestMathematicalPackageEnhancement:
    """Test mathematical package enhancement functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.tmp_dir = tempfile.mkdtemp()
        self.simple_tool = SimpleLaTeXTool(self.tmp_dir)
    
    def test_missing_packages_added(self):
        """Test that missing mathematical packages are added"""
        content = """\\documentclass{article}
\\begin{document}
\\section{Math}
$E = mc^2$
\\end{document}"""
        
        enhanced = self.simple_tool._ensure_mathematical_packages(content)
        
        # Check that required packages were added
        assert "\\usepackage{amsmath}" in enhanced
        assert "\\usepackage{amsfonts}" in enhanced
        assert "\\usepackage{amssymb}" in enhanced
        assert "\\usepackage{amsthm}" in enhanced
        assert "\\usepackage{mathtools}" in enhanced
        assert "\\usepackage{graphicx}" in enhanced
        assert "\\usepackage{geometry}" in enhanced
    
    def test_existing_packages_not_duplicated(self):
        """Test that existing packages are not duplicated"""
        content = """\\documentclass{article}
\\usepackage{amsmath}
\\usepackage{graphicx}
\\begin{document}
\\section{Math}
$E = mc^2$
\\end{document}"""
        
        enhanced = self.simple_tool._ensure_mathematical_packages(content)
        
        # Count occurrences of existing packages
        amsmath_count = enhanced.count("\\usepackage{amsmath}")
        graphicx_count = enhanced.count("\\usepackage{graphicx}")
        
        assert amsmath_count == 1, "amsmath should not be duplicated"
        assert graphicx_count == 1, "graphicx should not be duplicated"
        
        # But missing packages should be added
        assert "\\usepackage{amsfonts}" in enhanced
        assert "\\usepackage{amssymb}" in enhanced
    
    @patch('subprocess.run')
    def test_package_enhancement_integration(self, mock_run):
        """Test package enhancement in full tool execution"""
        # Mock successful compilation
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Success"
        mock_run.return_value.stderr = ""
        
        content = """\\documentclass{article}
\\begin{document}
\\section{Math}
$E = mc^2$
\\end{document}"""
        
        result = self.simple_tool.execute(
            filepath="test.tex",
            content=content,
            compile=False
        )
        
        assert result.status == ExecutionStatus.SUCCESS
        assert "packages enhanced" in result.message
        assert result.data["packages_enhanced"] is True
        
        # Verify packages were added to file
        filepath = os.path.join(self.tmp_dir, "test.tex")
        with open(filepath, 'r', encoding='utf-8') as f:
            file_content = f.read()
        
        assert "\\usepackage{amsmath}" in file_content
        assert "\\usepackage{graphicx}" in file_content


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 