import getpass
import os
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain.chat_models import init_chat_model 

if not os.environ.get("GOOGLE_API_KEY"):
  os.environ["GOOGLE_API_KEY"] = getpass.getpass("Enter API key for Google Gemini: ")


fsm_generator = init_chat_model("gemini-2.5-flash", model_provider="google_genai")
judge = init_chat_model("gemini-2.5-flash", model_provider="google_genai")

def judge_fsm(fsm, user_input):
    system_prompt = SystemMessage(content="""
You are a judge that evaluates the correctness of a finite state machine (FSM) based on its behavior. You will be given an FSM described in JSON format and behavioral description of a protocol called Matter.
Your task is to determine if the FSM correctly implements the protocol based on the provided user input and expected output.
Your output format should be:
{
    "correct": true/false,
    "explanation": "Your explanation or reasoning here"
}
""")
    user_message = HumanMessage(content=user_input)
    ai_message = AIMessage(content=f"FSM: {fsm}")
    response = judge([system_prompt, user_message, ai_message])
    return response.content

def generate_fsm(specification):
    prompt = f"""
    You are an expert in designing finite state machines (FSMs) for Matter protocol.
    specification: {specification}
    previous FSMs: {None}
    Response from judge: {None}
    """
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = fsm_generator([HumanMessage(content=prompt)])
            judge_response = judge_fsm(response.content, specification)
            if '"correct": true' in judge_response:
                return response.content
            else:
                print(f"FSM judged incorrect. Judge response: {judge_response}. Retrying ({attempt + 1}/{max_retries})...")
                prompt = f"""
                You are an expert in designing finite state machines (FSMs) for Matter protocol.
                specification: {specification}
                previous FSMs: {response.content}
                Response from judge: {judge_response}
                """ 
        except Exception as e:
            print(f"Error generating FSM: {e}. Retrying ({attempt + 1}/{max_retries})...")
    return None
