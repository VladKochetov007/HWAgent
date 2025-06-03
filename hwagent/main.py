from smolagents import CodeAgent, OpenAIServerModel
from hwagent.tools import ShellTool, EditFileTool, CreateFileTool
import os
import yaml
from dotenv import load_dotenv

def main():
    load_dotenv()

    with open('hwagent/config/prompts.yaml', 'r') as f:
        prompts = yaml.safe_load(f)

    with open('hwagent/config/api.yaml', 'r') as f:
        api_config = yaml.safe_load(f)

    with open('hwagent/config/agent_settings.yaml', 'r') as f:
        agent_settings = yaml.safe_load(f)

    shell_tool = ShellTool()
    create_file_tool = CreateFileTool()
    edit_file_tool = EditFileTool(
        model=api_config['openrouter']['simple_model'],
        api_base=api_config['openrouter']['base_url'],
        api_key=os.getenv("OPENROUTER_API_KEY"),
        system_prompt=prompts['simple']['system_prompt']
    )


    agent = CodeAgent(
        tools=[shell_tool, edit_file_tool, create_file_tool],
        model=OpenAIServerModel(
            model_id=api_config['openrouter']['thinking_model'],
            api_base=api_config['openrouter']['base_url'],
            api_key=os.getenv("OPENROUTER_API_KEY"),
            messages=[{"role": "system", "content": prompts['thinking']['system_prompt']}]
        ),
        add_base_tools=True,
        additional_authorized_imports=agent_settings['agent_settings']['additional_authorized_imports'],
        max_steps=agent_settings['agent_settings']['max_steps']
    )

    user_input = input("Enter your task: ")
    agent.run(user_input, stream=False)