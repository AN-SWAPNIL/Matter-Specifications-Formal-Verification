"""
fsm_normalizer_with_judge.py
FSM Normalizer (Generator LLM) + FSM Judge (Verifier LLM)
with automatic retry feedback loop.

Uses Gemini 2.5 Flash for both generator & judge with LangChain.
"""

import json
import os
import re
from typing import Dict, Any, List, Tuple

# LangChain imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

# ===============================
# Config
# ===============================
FSM_INPUT_PATH = "1.5_OnOff_Cluster_fsm_gpt_5_1.json"
OUTPUT_PATH = "normalized_fsm_output.json"

MODEL_GENERATOR = "gemini-2.5-flash"
MODEL_JUDGE = "gemini-2.5-flash"

MAX_ROUNDS = 3      # generator → judge → generator → ...
TEMPERATURE = 0.0
INCLUDE_THOUGHTS = False

if not os.environ.get("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = "AIzaSyABvDYLDLd880La-U1phLJ20JpyjIuz0vQ"

# ===============================
# System Prompt: Generator
# ===============================
SYSTEM_PROMPT_GENERATOR = r"""
You are an expert in formal verification, FSM theory, embedded-system specs, and model checking.

Your goal: Convert the given incomplete FSM into a fully explicit, deterministic FSM.

Strict rules (summary):

1. No conditional actions ("if", "then", "else") → split transitions.
2. Expand states to encode all conditions (timers, flags, attributes).
3. Normalize guards (mutually exclusive).
4. Actions must be unconditional and deterministic.
5. Loops allowed only if deterministic.
6. No nondeterminism for same (state, trigger).
7. State invariants must always hold.
8. Exactly one initial state.
9. Remove unreachable or contradictory states.
10. Final output MUST be a **single JSON object** with keys:
   - states
   - transitions
   - initial_state
   - notes

NO prose outside the JSON. Only the JSON object.

If a previous judge's feedback is provided, incorporate it to improve the next version.
"""

# ===============================
# User Prompt Template: Generator
# ===============================
USER_PROMPT_GENERATOR = """
Convert the following FSM into a fully deterministic FSM per the system rules.

FSM Input:
---
{fsm_text}
---

Judge Feedback to incorporate (if any):
---
{judge_feedback}
---

Return ONLY the final FSM JSON object, nothing else.
"""

# ===============================
# System Prompt: Judge LLM
# ===============================
SYSTEM_PROMPT_JUDGE = r"""
You are an FSM verification judge. You evaluate whether a generated FSM is valid for formal verification.

Return STRICT JSON:

{
  "is_valid": true/false,
  "errors": [ "...", ... ],
  "warnings": [ "...", ... ],
  "suggestions": "..."
}

Check the following:

1. JSON correctness.
2. Must contain states, transitions, initial_state.
3. initial_state must exist in states.
4. No "if", "then", "else" anywhere in actions.
5. Guards must be explicit (no hidden branching).
6. No nondeterministic transitions (same (state,trigger) with overlapping guards).
7. All states referenced by transitions exist.
8. Exactly one initial state.
9. No unreachable or contradictory states (best-effort).
10. Check for loops: deterministic only.
11. States must have unique names.
12. transitions must have unconditional actions.

Be strict. A single violation → is_valid = false.
"""

# ===============================
# User Prompt: Judge
# ===============================
USER_PROMPT_JUDGE = """
Evaluate the following FSM:

{fsm_output}

Return ONLY the JSON specified by the system.
"""


# ===============================
# Helper: Run the generator LLM
# ===============================

def extract_valid_json(text: str) -> Dict[str, Any]:
    """
    Extract the first valid JSON object from an LLM response.
    Does:
      - Find all {...} candidate JSON blocks
      - Cleans common LLM mistakes
      - Returns the first parsable JSON
    """
    # Find all candidate JSON objects using greedy and non-greedy patterns
    candidates = re.findall(r"\{.*?\}", text, flags=re.DOTALL)

    if not candidates:
        raise RuntimeError("No JSON-like structure found in LLM output.")

    for c in candidates:
        cleaned = (
            c
            .replace("\t", " ")
            .replace("\r", " ")
            .replace("\n", " ")
        )

        # Remove trailing commas before } or ]
        cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass  # try the next candidate

    raise RuntimeError(
        "Could not parse ANY JSON block from LLM output. Last candidate:\n" +
        candidates[-1][:2000]
    )

def run_generator(fsm_text: str, judge_feedback: str) -> Dict[str, Any]:
    gen = ChatGoogleGenerativeAI(
        model=MODEL_GENERATOR,
        temperature=TEMPERATURE,
        include_thoughts=INCLUDE_THOUGHTS,
    )

    messages = [
        SystemMessage(content=SYSTEM_PROMPT_GENERATOR),
        HumanMessage(content=USER_PROMPT_GENERATOR.format(
            fsm_text=fsm_text,
            judge_feedback=judge_feedback,
        ))
    ]

    result = gen.invoke(messages)
    text = result.content if hasattr(result, "content") else str(result)

    return extract_valid_json(text)




# ===============================
# Helper: Run the judge LLM
# ===============================
def run_judge(fsm_output: Dict[str, Any]) -> Dict[str, Any]:
    judge = ChatGoogleGenerativeAI(
        model=MODEL_JUDGE,
        temperature=0.0,
        include_thoughts=INCLUDE_THOUGHTS,
    )

    text = json.dumps(fsm_output, indent=2)

    messages = [
        SystemMessage(content=SYSTEM_PROMPT_JUDGE),
        HumanMessage(content=USER_PROMPT_JUDGE.format(fsm_output=text)),
    ]

    result = judge.invoke(messages)
    text_out = result.content if hasattr(result, "content") else str(result)

    return extract_valid_json(text_out)



# ===============================
# MAIN LOOP
# ===============================
def main():
    # load input FSM
    with open(FSM_INPUT_PATH, "r", encoding="utf-8") as f:
        original_text = f.read()

    try:
        root = json.loads(original_text)
        fsm_text = json.dumps(root.get("fsm_model", root), indent=2)
    except Exception:
        fsm_text = original_text

    judge_feedback = "None"
    final_fsm = None

    for round_idx in range(1, MAX_ROUNDS + 1):
        print(f"\n==============================")
        print(f" ROUND {round_idx}: GENERATING FSM")
        print(f"==============================")

        # Step 1: generator
        candidate = run_generator(fsm_text, judge_feedback)

        print("Generated FSM. Sending to judge...")

        # Step 2: judge
        judge_result = run_judge(candidate)

        print("\nJUDGE RESULT:", judge_result)

        if judge_result.get("is_valid", False):
            print("\n🎉 FSM VALIDATED SUCCESSFULLY!")
            final_fsm = candidate
            break

        # else retry with feedback
        judge_feedback = json.dumps(judge_result, indent=2)

    if final_fsm:
        with open(OUTPUT_PATH, "w", encoding="utf-8") as out:
            json.dump(final_fsm, out, indent=2)

        print(f"\nSaved VALID FSM to {OUTPUT_PATH}")
    else:
        print("\n❌ Could not produce a valid FSM after retries.")
        print("Last judge feedback was:\n", judge_feedback)


if __name__ == "__main__":
    main()
