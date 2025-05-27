import os
import importlib
import inspect
from typing import Any
from pathlib import Path

from .config_loader import load_yaml_config
from .tools import BaseTool


class ToolManager:
    def __init__(self, tools_dir: str = "hwagent/tools", prompts_config_path: str = "hwagent/config/prompts.yaml"):
        self.tools_dir = tools_dir
        self.tool_instances: dict[str, BaseTool] = {}
        self.tool_classes: dict[str, type[BaseTool]] = {}
        
        # Load configuration including tmp_directory
        try:
            prompts_cfg = load_yaml_config(prompts_config_path)
            self.messages = prompts_cfg.get("agent_messages", {}).get("tool_manager", {})
            self.config = prompts_cfg.get("config", {})
            self.tmp_directory = self.config.get("tmp_directory", "hwagent/tmp")
        except Exception:
            self.messages = {}
            self.config = {}
            self.tmp_directory = "hwagent/tmp"
        
        # Ensure tmp directory exists
        os.makedirs(self.tmp_directory, exist_ok=True)
        
        self._discover_and_load_tools()

    def _discover_and_load_tools(self):
        """Automatically discover and load all *Tool classes from the tools directory."""
        tools_path = Path(self.tools_dir)
        if not tools_path.exists():
            print(f"Warning: Tools directory {self.tools_dir} does not exist.")
            return

        # Get all Python files in tools directory
        for py_file in tools_path.glob("*.py"):
            if py_file.name.startswith("__"):
                continue  # Skip __init__.py and other special files
            
            module_name = py_file.stem
            try:
                # Import the module dynamically
                module_path = f"hwagent.tools.{module_name}"
                module = importlib.import_module(module_path)
                
                # Find all classes that end with "Tool" and inherit from BaseTool
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if (name.endswith("Tool") and 
                        issubclass(obj, BaseTool) and 
                        obj is not BaseTool):
                        
                        tool_name = obj.get_name()
                        self.tool_classes[tool_name] = obj
                        
                        # Check if tool constructor accepts tmp_directory parameter
                        try:
                            sig = inspect.signature(obj.__init__)
                            if 'tmp_directory' in sig.parameters:
                                self.tool_instances[tool_name] = obj(tmp_directory=self.tmp_directory)
                            else:
                                self.tool_instances[tool_name] = obj()
                        except Exception as e:
                            print(f"Error instantiating tool {tool_name}: {e}")
                            continue
                        
                        print(f"Loaded tool: {tool_name} from {module_name}")
                        
            except Exception as e:
                print(f"Error loading tools from {module_name}: {e}")

        if not self.tool_instances:
            print("Warning: No tools were discovered and loaded.")

    @property 
    def tools(self) -> dict[str, BaseTool]:
        """Get dictionary of tool instances for backward compatibility."""
        return self.tool_instances

    def get_tool_definitions_for_prompt(self) -> str:
        """Get tool definitions formatted for LLM prompt."""
        if not self.tool_instances:
            return "No tools available."
        
        tools_for_prompt = []
        for tool_name, tool_instance in self.tool_instances.items():
            tool_class = self.tool_classes[tool_name]
            tools_for_prompt.append({
                "name": tool_name,
                "description": tool_class.get_description(),
                "parameters": tool_class.get_parameters()
            })
        
        import json
        return json.dumps({"tools": tools_for_prompt}, indent=2)

    def get_tools_for_api(self) -> list[dict[str, Any]]:
        """Returns tool definitions in the format required by OpenAI API's 'tools' parameter."""
        if not self.tool_instances:
            return []
        
        api_tools = []
        for tool_name, tool_instance in self.tool_instances.items():
            tool_class = self.tool_classes[tool_name]
            parameters = tool_class.get_parameters()
            
            properties = {}
            required_params = []
            
            for param_name, param_def in parameters.items():
                properties[param_name] = {
                    "type": param_def["type"],
                    "description": param_def["description"]
                }
                # For now, assume all parameters are required
                # You could extend BaseTool to specify optional parameters
                required_params.append(param_name)
            
            api_tools.append({
                "type": "function",
                "function": {
                    "name": tool_name,
                    "description": tool_class.get_description(),
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                        "required": required_params
                    }
                }
            })
        
        return api_tools

    def execute_tool(self, tool_name: str, parameters: dict[str, Any]) -> str:
        """Execute a tool by name with given parameters."""
        if tool_name not in self.tool_instances:
            return f"Error: Tool '{tool_name}' not found."
        
        tool_instance = self.tool_instances[tool_name]
        try:
            return tool_instance.execute(**parameters)
        except Exception as e:
            return f"Error executing tool '{tool_name}': {e}" 