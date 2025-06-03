from hwagent.agent import get_agent

def main():
    agent = get_agent()
    user_input = input("Enter your task: ")
    agent.run(user_input, stream=False)

if __name__ == "__main__":
    main()