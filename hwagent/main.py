import os
from openai import OpenAI

from .config_loader import load_yaml_config
from .tool_manager import ToolManager
from .react_agent import ReActAgent

# --- Main Chatbot Logic ---
def main():
    """Runs the terminal-based chatbot with ReAct agent logic."""
    prompts_config = {}
    main_prompts_defaults = {
        "config_load_fail_error": "Failed to load initial configurations. Exiting.",
        "api_config_missing_error": "Error: 'base_url' or 'model' not found in api.yaml under 'openrouter'.",
        "api_key_missing_error": "Error: Environment variable OPENROUTER_API_KEY not set.",
        "api_key_missing_instruction": "Please set it before running the bot: export OPENROUTER_API_KEY='your_api_key'",
        "tool_manager_init_warning": "Warning: ToolManager initialized but no tools were loaded. Tool functionality will be limited.",
        "client_agent_init_error": "Error initializing OpenAI client or Agent: {error}",
        "chatbot_started_message": "ReAct Chatbot started! Type 'exit' to quit.",
        "base_prompt_display": "Base system prompt being used by agent: {prompt_snippet}...",
        "chatbot_shutdown_message": "Chatbot shutting down. Goodbye!"
    }
    try:
        api_config = load_yaml_config("hwagent/config/api.yaml")
        prompts_config = load_yaml_config("hwagent/config/prompts.yaml")
    except Exception:
        print(prompts_config.get("agent_messages", {}).get("main", {}).get("config_load_fail_error", main_prompts_defaults["config_load_fail_error"]))
        return

    main_prompts = prompts_config.get("agent_messages", {}).get("main", main_prompts_defaults)
    
    openrouter_config = api_config.get("openrouter", {})
    base_url = openrouter_config.get("base_url")
    model_name = openrouter_config.get("model")

    if not base_url or not model_name:
        print(main_prompts.get("api_config_missing_error", main_prompts_defaults["api_config_missing_error"]))
        return

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print(main_prompts.get("api_key_missing_error", main_prompts_defaults["api_key_missing_error"]))
        print(main_prompts.get("api_key_missing_instruction", main_prompts_defaults["api_key_missing_instruction"]))
        return

    base_system_prompt = prompts_config.get("tech_solver", {}).get("system_prompt", "You are a helpful AI assistant.")
    agent_react_prompts = prompts_config.get("agent_messages", {}).get("react_agent", {})
    # ToolManager loads its own prompts internally using default path

    try:
        client = OpenAI(base_url=base_url, api_key=api_key)
        # ToolManager now automatically discovers tools from hwagent/tools/ directory
        tool_manager = ToolManager() 
        if not tool_manager.tools:
            print(main_prompts.get("tool_manager_init_warning", main_prompts_defaults["tool_manager_init_warning"]))

        agent = ReActAgent(client, model_name, tool_manager, base_system_prompt, agent_react_prompts, enable_streaming=True)

    except Exception as e:
        err_tpl = main_prompts.get("client_agent_init_error", main_prompts_defaults["client_agent_init_error"])
        print(err_tpl.format(error=e))
        return

    print(main_prompts.get("chatbot_started_message", main_prompts_defaults["chatbot_started_message"]))
    prompt_snippet_to_display = base_system_prompt[:200] if isinstance(base_system_prompt, str) else str(base_system_prompt)[:200]
    print(main_prompts.get("base_prompt_display", main_prompts_defaults["base_prompt_display"]).format(prompt_snippet=prompt_snippet_to_display))
    
    print("\nSpecial commands:")
    print("  /clear - Clear conversation context")
    print("  /context - Show context summary")
    print("  /stream on/off - Enable/disable streaming")
    print("  /exit or 'exit' - Exit the chatbot")
    print()

    while True:
        user_input = input("You: ")
        
        # Handle special commands
        if user_input.lower() in ["exit", "/exit"]:
            print(main_prompts.get("chatbot_shutdown_message", main_prompts_defaults["chatbot_shutdown_message"]))
            break
        elif user_input.lower() == "/clear":
            agent.clear_context()
            continue
        elif user_input.lower() == "/context":
            print(agent.get_context_summary())
            continue
        elif user_input.lower().startswith("/stream"):
            parts = user_input.lower().split()
            if len(parts) > 1:
                if parts[1] == "on":
                    agent.enable_streaming = True
                    print("Streaming enabled.")
                elif parts[1] == "off":
                    agent.enable_streaming = False
                    print("Streaming disabled.")
                else:
                    print("Usage: /stream on or /stream off")
            else:
                status = "enabled" if agent.enable_streaming else "disabled"
                print(f"Streaming is currently {status}.")
            continue

        if not user_input.strip():
            continue

        assistant_final_response = agent.process_user_request(user_input)
        if not agent.enable_streaming:  # Only print if not streaming (streaming prints as it goes)
            print(f"Bot: {assistant_final_response}")

if __name__ == "__main__":
    # With relative imports, this script should be run as a module from the parent directory:
    # From HWAgent/ directory: python -m hwagent.main
    # Running directly with `python main.py` from hwagent/ may not work due to relative imports.
    main()
