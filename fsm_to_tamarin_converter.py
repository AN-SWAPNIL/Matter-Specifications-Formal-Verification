import subprocess
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate

# 1. Define the Custom Tool
@tool
def run_tamarin_parse(file_path: str) -> str:
    """
    Runs the 'tamarin-prover parse' command on a specified .spthy file path.
    Use this to check a protocol file for syntax errors or parsing issues.
    Returns the standard output and error logs from the compiler.
    """
    # Security Note: We use a list for the command to avoid shell=True (prevents injection)
    command = ["tamarin-prover", "parse", file_path]
    
    try:
        # Run the command with a timeout to prevent hanging
        result = subprocess.run(
            command, 
            capture_output=True, 
            text=True, 
            timeout=60
        )
        
        # Combine stdout and stderr to give the LLM full context
        output = f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
        
        if result.returncode == 0:
            return f"Command executed successfully.\n{output}"
        else:
            return f"Command failed with return code {result.returncode}.\n{output}"

    except FileNotFoundError:
        return "Error: 'tamarin-prover' executable not found. Is it installed and in your PATH?"
    except subprocess.TimeoutExpired:
        return "Error: The parsing command timed out."
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"

# 2. Setup the LLM and Agent
# Replace with your actual API key or environment variable
llm = ChatOpenAI(model="gpt-4o", temperature=0)

tools = [run_tamarin_parse]

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a formal verification assistant. You can run Tamarin commands to check protocols."),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

# 3. Create the Agent
agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# 4. Run the Agent
# Example: Asking the agent to parse a specific file
response = agent_executor.invoke({
    "input": "Can you run the parse command on the file 'protocols/nsl.spthy' and tell me if it is valid?"
})

print(response["output"])