
class SecurityValidator:
    """Validator for security-related checks to prevent dangerous operations."""
    
    @staticmethod
    def validate_python_code_safety(code: str):
        """Check Python code for dangerous patterns."""
        dangerous_patterns = [
            r'import\s+(os|subprocess|shutil)',
            r'from\s+(os|subprocess|shutil)\s+import',
            r'__import__\s*\(',
            r'eval\s*\(',
            r'exec\s*\(',
            r'open\s*\([^)]*["\'][/\\]',  # Opening files with absolute paths
            r'os\.system\s*\(',
            r'subprocess\.',
            r'shutil\.rmtree',
            r'os\.remove',
            r'os\.unlink',
            r'pathlib\.Path.*\.unlink',
            r'Path\([^)]*\)\.unlink',  # Direct Path().unlink() calls
            r'\.write18',  # LaTeX shell escape
            # Additional patterns to prevent HTTP requests and file operations
            r'requests\.',  # HTTP requests library
            r'urllib\.request',  # URL library
            r'urllib\.urlopen',
            r'http\.client',
            r'httplib',
            r'DELETE.*api/fs/tmp/delete',  # Direct API call
            r'localhost:5000',  # Local API server
            r'127\.0\.0\.1:5000',  # Local API server IP
            r'\.delete\(',  # Any delete method calls
            r'pathlib\.Path.*\.rmdir',  # Directory removal
            r'os\.rmdir',  # Directory removal
            r'tempfile\.mktemp',  # Insecure temporary files
        ]
        