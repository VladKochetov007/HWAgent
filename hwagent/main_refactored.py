"""
Refactored main script using MessageManager and refactored ReActAgent.
"""

import os
from openai import OpenAI

from hwagent.config_loader import load_yaml_config
from hwagent.tool_manager import ToolManager
from hwagent.react_agent_refactored import ReActAgent
from hwagent.core import MessageManager


class ChatbotController:
    """Controls the main chatbot flow. Following SRP."""
    
    def __init__(self):
        """Initialize ChatbotController."""
        self.message_manager = MessageManager()
        self.agent: ReActAgent | None = None
    
    def initialize_chatbot(self) -> bool:
        """
        Initialize chatbot components.
        
        Returns:
            True if successful, False if failed
        """
        try:
            # Load configurations
            api_config = load_yaml_config("hwagent/config/api.yaml")
            prompts_config = load_yaml_config("hwagent/config/prompts.yaml")
            
        except Exception:
            print(self.message_manager.get_message("main", "config_load_fail_error"))
            return False
        
        # Validate API configuration
        openrouter_config = api_config.get("openrouter", {})
        base_url = openrouter_config.get("base_url")
        model_name = openrouter_config.get("model")
        
        if not base_url or not model_name:
            print(self.message_manager.get_message("main", "api_config_missing_error"))
            return False
        
        # Check API key
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            print(self.message_manager.get_message("main", "api_key_missing_error"))
            print(self.message_manager.get_message("main", "api_key_missing_instruction"))
            return False
        
        # Get prompts
        base_system_prompt = prompts_config.get("tech_solver", {}).get("system_prompt", "You are a helpful AI assistant.")
        agent_react_prompts = prompts_config.get("agent_messages", {}).get("react_agent", {})
        
        # Initialize components
        try:
            client = OpenAI(base_url=base_url, api_key=api_key)
            tool_manager = ToolManager()
            
            if not tool_manager.get_tool_count():
                print(self.message_manager.get_message("main", "tool_manager_init_warning"))
            
            self.agent = ReActAgent(
                client, model_name, tool_manager, 
                base_system_prompt, agent_react_prompts, 
                enable_streaming=True
            )
            
        except Exception as e:
            error_msg = self.message_manager.format_message(
                "main", "client_agent_init_error", error=e
            )
            print(error_msg)
            return False
        
        return True
    
    def print_startup_info(self, base_system_prompt: str) -> None:
        """Print startup information."""
        print(self.message_manager.get_message("main", "chatbot_started_message"))
        
        prompt_snippet = base_system_prompt[:200] if isinstance(base_system_prompt, str) else str(base_system_prompt)[:200]
        print(self.message_manager.format_message(
            "main", "base_prompt_display", prompt_snippet=prompt_snippet
        ))
        
        print("\n" + self.message_manager.get_message("main", "special_commands_header"))
        print(self.message_manager.get_message("main", "command_clear"))
        print(self.message_manager.get_message("main", "command_context"))
        print(self.message_manager.get_message("main", "command_stream"))
        print(self.message_manager.get_message("main", "command_exit"))
        print()
    
    def handle_special_command(self, user_input: str) -> bool:
        """
        Handle special commands.
        
        Args:
            user_input: User input string
            
        Returns:
            True if command was handled, False if not a special command
        """
        if not self.agent:
            return False
        
        if user_input.lower() in ["exit", "/exit"]:
            print(self.message_manager.get_message("main", "chatbot_shutdown_message"))
            return True
        
        elif user_input.lower() == "/clear":
            self.agent.clear_context()
            return False  # Continue running
        
        elif user_input.lower() == "/context":
            print(self.agent.get_context_summary())
            return False  # Continue running
        
        elif user_input.lower().startswith("/stream"):
            self._handle_stream_command(user_input)
            return False  # Continue running
        
        return False  # Not a special command
    
    def _handle_stream_command(self, user_input: str) -> None:
        """Handle streaming toggle command."""
        if not self.agent:
            return
        
        parts = user_input.lower().split()
        if len(parts) > 1:
            if parts[1] == "on":
                self.agent.set_streaming_enabled(True)
            elif parts[1] == "off":
                self.agent.set_streaming_enabled(False)
            else:
                print(self.message_manager.get_message("react_agent", "streaming_usage_help"))
        else:
            status = "enabled" if self.agent.enable_streaming else "disabled"
            print(self.message_manager.format_message(
                "react_agent", "streaming_status", status=status
            ))
    
    def run_chat_loop(self) -> None:
        """Run the main chat loop."""
        if not self.agent:
            print("Error: Agent not initialized")
            return
        
        while True:
            user_input = input("You: ")
            
            # Handle special commands
            if self.handle_special_command(user_input):
                break  # Exit command
            
            if not user_input.strip():
                continue
            
            # Process user request
            assistant_response = self.agent.process_user_request(user_input)
            
            # Print response if not streaming (streaming prints as it goes)
            if not self.agent.enable_streaming:
                bot_prefix = self.message_manager.get_message("react_agent", "bot_prefix")
                print(f"{bot_prefix}{assistant_response}")


def main():
    """Main function to run the chatbot."""
    controller = ChatbotController()
    
    # Initialize chatbot
    if not controller.initialize_chatbot():
        return
    
    # Print startup info
    # We'll get the base prompt from the agent's configuration
    controller.print_startup_info("System prompt loaded")
    
    # Run chat loop
    controller.run_chat_loop()


if __name__ == "__main__":
    main() 