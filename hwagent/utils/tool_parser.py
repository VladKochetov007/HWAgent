"""Utility for parsing tool descriptions from source code."""

import ast
import importlib
from pathlib import Path
from typing import Dict, Any
import mcp.types as types


def parse_tool_description(tool_module) -> Dict[str, Any]:
    """
    Parse tool description from its MCP Tool registration.
    
    Args:
        tool_module: The imported tool module
        
    Returns:
        Dictionary with tool name, description, and schema
    """
    # Look for tools in the module's _tools attribute or search for Tool objects
    tools = []
    
    # Check if module has _tools attribute
    if hasattr(tool_module, '_tools'):
        tools.extend(tool_module._tools)
    
    # Check for any Tool objects in module attributes
    for attr_name in dir(tool_module):
        attr = getattr(tool_module, attr_name)
        if isinstance(attr, types.Tool):
            tools.append(attr)
    
    # If no direct tools found, try to find them in server registration functions
    if not tools:
        # Look for register_*_tool functions
        for attr_name in dir(tool_module):
            if attr_name.startswith('register_') and attr_name.endswith('_tool'):
                # This is a registration function, but we need to extract the tool definition
                # Let's parse the source code to find the Tool() creation
                tools.extend(parse_tools_from_source(tool_module.__file__, attr_name))
    
    return tools


def parse_tools_from_source(file_path: str, func_name: str = None) -> list[types.Tool]:
    """
    Parse Tool definitions from Python source code.
    
    Args:
        file_path: Path to the Python file
        func_name: Optional function name to search within
        
    Returns:
        List of Tool objects found in the source
    """
    tools = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        tree = ast.parse(source)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Look for types.Tool() calls
                if (isinstance(node.func, ast.Attribute) and 
                    isinstance(node.func.value, ast.Name) and
                    node.func.value.id == 'types' and 
                    node.func.attr == 'Tool'):
                    
                    tool = extract_tool_from_ast_call(node)
                    if tool:
                        tools.append(tool)
    
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
    
    return tools


def extract_tool_from_ast_call(node: ast.Call) -> types.Tool | None:
    """
    Extract Tool object from AST Call node.
    
    Args:
        node: AST Call node representing types.Tool() call
        
    Returns:
        Tool object or None if parsing failed
    """
    try:
        # Extract arguments
        name = None
        description = None
        input_schema = None
        
        # Process keyword arguments
        for keyword in node.keywords:
            if keyword.arg == 'name':
                name = ast.literal_eval(keyword.value)
            elif keyword.arg == 'description':
                description = ast.literal_eval(keyword.value)
            elif keyword.arg == 'inputSchema':
                # This is more complex - need to evaluate the dict
                input_schema = ast.literal_eval(keyword.value)
        
        if name and description:
            return types.Tool(
                name=name,
                description=description,
                inputSchema=input_schema or {}
            )
    
    except Exception as e:
        print(f"Error extracting tool from AST: {e}")
    
    return None


def get_all_tool_descriptions() -> str:
    """
    Get formatted descriptions of all available tools by parsing their source code.
    
    Returns:
        Formatted string with all tool descriptions
    """
    tool_modules = [
        'hwagent.tools.create_file',
        'hwagent.tools.edit_file', 
        'hwagent.tools.execute_command',
        'hwagent.tools.search_web',
        'hwagent.tools.final_answer'
    ]
    
    tool_descriptions = []
    
    for module_name in tool_modules:
        try:
            # Import the module
            module = importlib.import_module(module_name)
            
            # Parse tools from the source file
            tools = parse_tools_from_source(module.__file__)
            
            for tool in tools:
                desc = format_tool_description(tool)
                tool_descriptions.append(desc)
                
        except Exception as e:
            print(f"Error processing {module_name}: {e}")
    
    return "\n\n".join(tool_descriptions)


def format_tool_description(tool: types.Tool) -> str:
    """
    Format a single tool description for the prompt.
    
    Args:
        tool: Tool object to format
        
    Returns:
        Formatted tool description string
    """
    lines = []
    lines.append(f"🔧 {tool.name}:")
    lines.append(f"Description: {tool.description}")
    lines.append(f"Action: {tool.name}")
    
    # Format input schema
    if tool.inputSchema and "properties" in tool.inputSchema:
        properties = tool.inputSchema["properties"]
        required = tool.inputSchema.get("required", [])
        
        # Build example JSON
        example_params = {}
        param_descriptions = []
        
        for param_name, param_info in properties.items():
            param_desc = param_info.get("description", "")
            param_type = param_info.get("type", "string")
            is_required = param_name in required
            
            # Add to example
            if param_type == "string":
                example_params[param_name] = f"your_{param_name}_here"
            elif param_type == "integer":
                example_params[param_name] = param_info.get("default", 10)
            elif param_type == "boolean":
                example_params[param_name] = param_info.get("default", True)
            else:
                example_params[param_name] = f"{param_type}_value"
            
            # Add to descriptions
            req_text = "REQUIRED" if is_required else "OPTIONAL"
            param_descriptions.append(f"  - {param_name}: {param_desc} ({req_text})")
        
        lines.append(f"Action Input: {example_params}")
        lines.append("Parameters:")
        lines.extend(param_descriptions)
    
    return "\n".join(lines) 