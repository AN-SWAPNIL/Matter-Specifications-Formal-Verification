import os
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain.chat_models import init_chat_model 
import json


MODEL_NAME = "gemini-2.5-flash"
MODEL_PROVIDER = "google_genai"
fsm_generator = init_chat_model(MODEL_NAME, model_provider=MODEL_PROVIDER)
judge = init_chat_model(MODEL_NAME, model_provider=MODEL_PROVIDER)

def judge_fsm(fsm, user_input):
    prompt = f"""
You are a judge that evaluates the correctness of a finite state machine (FSM) based on its behavior. You will be given an FSM described in JSON format and behavioral description of a protocol called Matter.
Your task is to determine if the FSM correctly implements the protocol based on the provided user input and expected output.
Your output format should be json parsable and strictly follow this format:
{{
    "correct": true/false,
    "explanation": "Your explanation or reasoning here"
}}
Now evaluate the following FSM and user input:
FSM: {fsm}
User Input: {user_input}
"""
    print(f"Judge prompt: {prompt}")
    response = judge.invoke(prompt)
    return response.content

def generate_fsm(cluster_info):
    FSM_GENERATION_PROMPT_TEMPLATE = f"""
You are a Matter IoT protocol expert who generates precise Finite State Machine models from Matter Application Cluster specifications.

CLUSTER SPECIFICATION TO ANALYZE:
{cluster_info}

**UNIVERSAL FSM GENERATION APPROACH:**

**STEP 1: CLUSTER BEHAVIORAL ANALYSIS**
Analyze the cluster specification to determine behavioral patterns:
- **Attribute-driven states**: States correspond to meaningful attribute value combinations
- **Command semantics**: Extract behavioral logic from "effect_on_receipt" descriptions  
- **Timer-based transitions**: Identify countdown timers and automatic state changes
- **Conditional logic**: Commands with if/then/else branches require multiple transitions
- **Feature constraints**: Only use features defined in the specification

**STEP 2: STATE IDENTIFICATION**
Define states based on cluster attributes and operational conditions:
- States represent actual device behavior, not internal processing
- Use attribute values to determine state invariants
- Include timer states if countdown attributes exist
- Model fault/error states if specified in cluster
- Ensure states reflect physical/logical device condition

**STEP 3: TRANSITION MODELING**
Create transitions from command specifications:
- Parse "effect_on_receipt" for exact behavioral steps
- Split conditional commands into multiple guarded transitions
- Model timer expiry as automatic transitions
- Include proper guard conditions for all branching logic
- Set response_command to null (Application Cluster specification)
- **Model event generation**: Include events in transition actions when specified
- **Use data type constraints**: Apply enum values and bitmap constraints in guards
- **Handle scene behaviors**: Model scene store/recall for scene-capable attributes
- **Include stay transitions**: Model state continuation for commands that extend/reset timers
- **Enforce feature constraints**: Block commands when features prohibit execution

**STEP 4: ADVANCED BEHAVIORAL MODELING**
Enhance FSM with detailed cluster information:
- **Data Type Integration**: Use extracted enums for state values, bitmaps for feature validation
- **Quality Flag Handling**: Model read-only vs read-write attribute behaviors
- **Constraint Validation**: Apply attribute constraints as state invariants
- **Feature Enforcement**: Add guard conditions that respect feature flags and limitations
- **Timer Decrement Logic**: Model internal timer decrements with appropriate resolution
- **Event-Driven Transitions**: Model transitions triggered by cluster events
- **Scene Capability**: Include scene store/recall behaviors for scene-capable attributes
- **Fabric Sensitivity**: Model fabric-scoped attribute access patterns

**STEP 5: TIMER SEMANTICS**
For clusters with timer attributes:
- Model timer countdown behavior with correct resolution
- Create timer expiry transitions when timer reaches zero
- Include internal timer decrement transitions (stay transitions)
- Distinguish between different timer types and their resolutions
- Include timer start/stop logic in command actions
- Model timer reset behaviors for command extensions

**STEP 6: FEATURE VALIDATION**
Apply feature constraints correctly:
- Only use features explicitly defined in cluster specification
- Model feature-dependent command availability with guard conditions
- Include feature validation that blocks prohibited commands
- Avoid inventing non-existent features
- Enforce feature limitations in transition guards

**REQUIRED FSM STRUCTURE:**
{{
  "fsm_model": {{
    "cluster_name": "[extracted from specification]",
    "cluster_id": "[hex ID from specification]", 
    "category": "[cluster category]",
    "states": [
      {{
        "name": "[state name]",
        "description": "[clear behavioral description]",
        "is_initial": true/false,
        "invariants": ["[attribute constraints in this state]"],
        "attributes_monitored": ["[relevant cluster attributes]"]
      }}
    ],
    "transitions": [
      {{
        "from_state": "[source state]",
        "to_state": "[target state]",
        "trigger": "[command name or timer/event]",
        "guard_condition": "[boolean condition with data type constraints]",
        "actions": ["[attribute updates]", "[event generation if applicable]"],
        "response_command": null
      }}
    ],
    "initial_state": "[appropriate default state]",
    "attributes_used": ["[all referenced attributes with quality flags]"],
    "commands_handled": ["[all cluster commands]"],
    "events_generated": ["[cluster events from specification]"],
    "data_types_used": ["[enums, bitmaps, structures referenced]"],
    "scene_behaviors": ["[scene store/recall actions if applicable]"],
    "generation_timestamp": "[current timestamp]",
    "source_metadata": {{
      "extraction_method": "AI_behavioral_analysis",
      "source_pages": "[from cluster_info]",
      "section_number": "[from cluster_info]"
    }}
  }}
}}

**ANALYSIS METHODOLOGY:**
1. Identify cluster type: state-based, timer-driven, mode-based, measurement, etc.
2. Extract key attributes that define operational states (consider quality flags)
3. Analyze command effects for precise behavioral logic including conditional branches
4. **Integrate data types**: Use enums for state values, bitmaps for feature checks, structures for complex data
5. Map states to meaningful attribute combinations with proper constraints
6. Model conditional command branches as separate transitions with data type validation
7. Add timer-based automatic transitions with correct resolution and decrement logic
8. **Include event modeling**: Add event generation and event-driven transitions
9. **Model scene behaviors**: Include scene store/recall for scene-capable attributes
10. **Add stay transitions**: Include state continuation for timer extensions and command repetitions
11. **Enforce feature constraints**: Add guard conditions that block prohibited commands
12. Validate against specification features and constraints
13. Ensure complete coverage of commands, events, and data type interactions

**CRITICAL ACCURACY REQUIREMENTS:**
- States reflect actual device behavior from specification
- Transitions implement exact command semantics with complete guard conditions
- Guard conditions capture all conditional logic including feature enforcement
- Timer behaviors model correct countdown, expiry, and internal decrement
- Features constrain commands as specified with proper blocking
- All attribute interactions are accurate and complete
- Include both state-changing and stay transitions where appropriate
- Model timer reset and extension behaviors correctly
- Use null for response_command in Application Clusters

Focus on Matter specification accuracy over generic patterns. Generate FSM by analyzing the provided cluster specification systematically.

Return ONLY the JSON structure. No explanations, no markdown blocks, no additional text.

"""
    feedback = None

    max_retries = 10
    for attempt in range(max_retries):
        if feedback:
            FEEDBACK_PROMPT_TEMPLATE = f"""
    The previously generated FSM was judged incorrect. Here is the feedback from the judge:
    {feedback}
    If you find any mistakes in the previous FSM, correct them based on this feedback.
    """
            prompt = FSM_GENERATION_PROMPT_TEMPLATE + "\n" + FEEDBACK_PROMPT_TEMPLATE
        else:
            prompt = FSM_GENERATION_PROMPT_TEMPLATE
            print("==================================================================================================")
        print(f"Attempt {attempt + 1} to generate FSM...")
        print(f"Current prompt: {prompt[:50]}")
        try:
            response = fsm_generator.invoke(prompt)
            print(f"FSM generation response: {response.content[:100]}")
            judge_response = judge_fsm(response.content, cluster_info)
            print("******************************************************")
            if '"correct": true' in judge_response:
                print(f"Judge response: {judge_response}")
                return response.content
            else:
                print(f"FSM judged incorrect. Judge response: {judge_response}. Retrying ({attempt + 1}/{max_retries})...")
                feedback = judge_response
        except Exception as e:
            print(f"Error generating FSM: {e}. Retrying ({attempt + 1}/{max_retries})...")
    return None

if __name__ == "__main__":
    cluster_info = None
    with open("cluster_info.json", "r") as f:
        cluster_info = json.load(f)
    
    fsm = generate_fsm(cluster_info)
    if fsm:
        print("Generated FSM:")
        print(fsm)
        with open(f"generated_fsm_{MODEL_NAME}_{MODEL_PROVIDER}.txt", "w") as f:
            f.write(str(fsm))
    else:
        print("Failed to generate a correct FSM after multiple attempts.")
    