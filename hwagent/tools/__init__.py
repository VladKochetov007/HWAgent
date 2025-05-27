from abc import ABC, abstractmethod
from typing import Any
import inspect


# Global tool registry
_TOOL_REGISTRY: dict[str, type['BaseTool']] = {}


def ToolRegister(cls):
    """Decorator to register a tool class in the global registry."""
    if not issubclass(cls, BaseTool):
        raise TypeError(f"Class {cls.__name__} must inherit from BaseTool")
    
    tool_name = cls.get_name()
    _TOOL_REGISTRY[tool_name] = cls
    return cls


def get_registered_tools() -> dict[str, type['BaseTool']]:
    """Get all registered tool classes."""
    return _TOOL_REGISTRY.copy()


class BaseTool(ABC):
    """Base class for all tools in the HWAgent system."""
    
    @abstractmethod
    def execute(self, **kwargs) -> str:
        """Execute the tool with given parameters.
        
        Returns:
            str: Result message, either success or error starting with 'Error:'
        """
        pass
    
    @classmethod
    def get_name(cls) -> str:
        """Get tool name from class name (removes 'Tool' suffix)."""
        name = cls.__name__
        if name.endswith('Tool'):
            name = name[:-4]
        # Convert CamelCase to snake_case
        import re
        name = re.sub('([A-Z]+)', r'_\1', name).lower().strip('_')
        return name
    
    @classmethod
    def get_description(cls) -> str:
        """Get tool description from class docstring."""
        doc = cls.__doc__
        if doc:
            # Take first line or paragraph of docstring
            return doc.strip().split('\n')[0].strip()
        return f"Tool: {cls.get_name()}"
    
    @classmethod
    def get_parameters(cls) -> dict[str, dict[str, str]]:
        """Get parameters from execute method signature and docstring."""
        execute_method = cls.execute
        sig = inspect.signature(execute_method)
        params = {}
        
        # Parse docstring for parameter descriptions
        doc = execute_method.__doc__ or ""
        param_descriptions = cls._parse_param_descriptions(doc)
        
        for param_name, param in sig.parameters.items():
            if param_name in ('self', 'kwargs'):
                continue
                
            param_type = "string"  # Default type
            if param.annotation != inspect.Parameter.empty:
                if param.annotation == int:
                    param_type = "integer"
                elif param.annotation == float:
                    param_type = "number"
                elif param.annotation == bool:
                    param_type = "boolean"
                # Add more type mappings as needed
            
            params[param_name] = {
                "type": param_type,
                "description": param_descriptions.get(param_name, f"Parameter: {param_name}")
            }
        
        return params
    
    @classmethod
    def _parse_param_descriptions(cls, docstring: str) -> dict[str, str]:
        """Parse parameter descriptions from docstring."""
        descriptions = {}
        lines = docstring.split('\n')
        in_params_section = False
        
        for line in lines:
            line = line.strip()
            if line.lower().startswith('args:') or line.lower().startswith('parameters:'):
                in_params_section = True
                continue
            elif line.lower().startswith('returns:') or line.lower().startswith('return:'):
                in_params_section = False
                continue
            
            if in_params_section and ':' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    param_name = parts[0].strip()
                    description = parts[1].strip()
                    descriptions[param_name] = description
        
        return descriptions
