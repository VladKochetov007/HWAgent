import yaml
import os
from openai import OpenAI

# --- Configuration Loading ---
def load_config(config_path: str) -> dict:
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

# --- Main Chatbot Logic ---
def main():
    """Runs the terminal-based chatbot."""
    try:
        api_config = load_config("hwagent/config/api.yaml")
        prompts_config = load_config("hwagent/config/prompts.yaml")
    except FileNotFoundError:
        print("Error: One or both configuration files (api.yaml, prompts.yaml) not found.")
        print("Ensure the files are located in the hwagent/config/ directory.")
        return
    except yaml.YAMLError as e:
        print(f"Error reading YAML configuration: {e}")
        return

    # Extract API and prompt details
    openrouter_config = api_config.get("openrouter", {})
    base_url = openrouter_config.get("base_url")
    model_name = openrouter_config.get("model")

    if not base_url or not model_name:
        print("Error: 'base_url' or 'model' not found in api.yaml under 'openrouter'.")
        return

    # It's good practice to use environment variables for API keys
    # However, the user's config doesn't specify where to get the key.
    # For this example, we'll try to get it from an environment variable OPENROUTER_API_KEY.
    # The user will need to set this environment variable.
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: Environment variable OPENROUTER_API_KEY not set.")
        print("Please set it before running the bot: export OPENROUTER_API_KEY='your_api_key'")
        return

    system_prompt = prompts_config.get("tech_solver", {}).get("system_prompt", "You are a helpful assistant.")

    try:
        client = OpenAI(
            base_url=base_url,
            api_key=api_key,
        )
    except Exception as e:
        print(f"Error initializing OpenAI client: {e}")
        return

    print("Chatbot started! Type 'exit' to quit.")
    print(f"System prompt: {system_prompt.strip()}")

    # Initialize conversation history with the system prompt
    conversation_history: list[dict[str, str]] = [{"role": "system", "content": system_prompt.strip()}]

    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            print("Chatbot shutting down. Goodbye!")
            break

        # Add user message to history
        conversation_history.append({"role": "user", "content": user_input})

        try:
            completion = client.chat.completions.create(
                model=model_name,
                messages=conversation_history,
            )
            if completion.choices and completion.choices[0].message:
                assistant_response = completion.choices[0].message.content
                print(f"Bot: {assistant_response}")
                # Add assistant response to history
                if assistant_response: # Ensure we don't add empty responses
                     conversation_history.append({"role": "assistant", "content": assistant_response})
            else:
                print("Bot: Failed to get a response from the model.")
                # Remove the last user message if the API call failed to prevent issues on retry
                conversation_history.pop()

        except Exception as e:
            print(f"Error calling API: {e}")
            # Remove the last user message if the API call failed
            if conversation_history and conversation_history[-1]["role"] == "user":
                conversation_history.pop()


if __name__ == "__main__":
    main()
