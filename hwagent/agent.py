from smolagents import CodeAgent, OpenAIServerModel
from hwagent.tools import ShellTool, EditFileTool, CreateFileTool
import os
import yaml
from dotenv import load_dotenv

load_dotenv()

with open('hwagent/config/prompts.yaml', 'r') as f:
    prompts = yaml.safe_load(f)

with open('hwagent/config/api.yaml', 'r') as f:
    api_config = yaml.safe_load(f)

with open('hwagent/config/agent_settings.yaml', 'r') as f:
    agent_settings = yaml.safe_load(f)

def get_agent():
    shell_tool = ShellTool()
    create_file_tool = CreateFileTool()
    edit_file_tool = EditFileTool(
        model=api_config['openrouter']['simple_model'],
        api_base=api_config['openrouter']['base_url'],
        api_key=os.getenv("OPENROUTER_API_KEY"),
        system_prompt=prompts['simple']['system_prompt'],
        temperature=api_config['model_parameters']['simple_temperature']
    )

    # Check if verbose mode is enabled
    verbose_mode = os.getenv('HWAGENT_VERBOSE', '0') == '1'
    verbosity_level = 2 if verbose_mode else 1  # Higher verbosity for thinking process
    
    if verbose_mode:
        print("🧠 Agent verbose mode enabled - all thinking steps will be displayed")

    agent = CodeAgent(
        tools=[shell_tool, edit_file_tool, create_file_tool],
        model=OpenAIServerModel(
            model_id=api_config['openrouter']['thinking_model'],
            api_base=api_config['openrouter']['base_url'],
            api_key=os.getenv("OPENROUTER_API_KEY"),
            temperature=api_config['model_parameters']['thinking_temperature']
        ),
        instructions=prompts['thinking']['system_prompt'],
        add_base_tools=True,
        additional_authorized_imports=agent_settings['agent_settings']['additional_authorized_imports'],
        max_steps=agent_settings['agent_settings']['max_steps'],
        verbosity_level=verbosity_level  # Set verbosity based on environment
    )
    
    # Pass image_paths to the agent state for vision tasks
    if verbose_mode:
        print("🖼️ Vision capabilities enabled - agent can process images via image_paths variable")
    
    return agent