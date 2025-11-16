#!/usr/bin/env python3
"""
Matter Cluster FSM Generator with LLM-as-Judge
Generates Finite State Machine models with iterative refinement based on judge feedback
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain.chat_models import init_chat_model

# Configuration imports
from config import (
    GOOGLE_API_KEY,
    GEMINI_MODEL,
    GEMINI_TEMPERATURE,
    GEMINI_MAX_OUTPUT_TOKENS,
    FSM_GENERATION_PROMPT_TEMPLATE
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set API key from config
if not os.environ.get("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

# Initialize models with config settings
MODEL_NAME = GEMINI_MODEL  # Use from config.py
MODEL_PROVIDER = "google_genai"

try:
    fsm_generator = init_chat_model(
        MODEL_NAME,
        model_provider=MODEL_PROVIDER,
        temperature=GEMINI_TEMPERATURE,
        max_tokens=GEMINI_MAX_OUTPUT_TOKENS
    )
    judge = init_chat_model(
        MODEL_NAME,
        model_provider=MODEL_PROVIDER,
        temperature=GEMINI_TEMPERATURE
    )
except Exception as e:
    logger.error(f"Error initializing models: {e}")
    raise

def clean_json_response(response: str, cluster_name: str = "Unknown") -> str:
    """
    Clean JSON response by removing markdown code blocks and extra whitespace.
    
    Args:
        response: Raw LLM response
        cluster_name: Name of cluster for logging
        
    Returns:
        Cleaned JSON string
    """
    clean_response = response.strip()
    
    # Remove code block markers
    if clean_response.startswith('```json'):
        clean_response = clean_response[7:]
    elif clean_response.startswith('```'):
        clean_response = clean_response[3:]
    
    if clean_response.endswith('```'):
        clean_response = clean_response[:-3]
    
    clean_response = clean_response.strip()
    
    # Validate JSON structure
    if not clean_response.startswith('{'):
        logger.warning(f"Invalid FSM response format for cluster {cluster_name}")
        return ""
    
    return clean_response

def judge_fsm(fsm: str, user_input: str) -> str:
    """
    Evaluate the correctness of a generated FSM.
    
    Args:
        fsm: Generated FSM in JSON format
        user_input: Original cluster information
        
    Returns:
        Judge's evaluation response
    """
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
    try:
        response = judge.invoke(prompt)
        return response.content
    except Exception as e:
        logger.error(f"Judge evaluation error: {str(e)}")
        return json.dumps({"correct": False, "explanation": f"Judge error: {str(e)}"})

def generate_fsm(cluster_info: Dict[str, Any], max_retries: int = 10) -> Optional[Dict[str, Any]]:
    """
    Generate FSM with iterative refinement based on judge feedback.
    
    Args:
        cluster_info: Detailed cluster specification
        max_retries: Maximum number of generation attempts
        
    Returns:
        Generated FSM model as dictionary, or None if failed
    """
    import time
    
    cluster_name = "Unknown"
    if isinstance(cluster_info, dict):
        cluster_name = cluster_info.get('cluster_info', {}).get('cluster_name', 'Unknown')
    
    cluster_info_str = json.dumps(cluster_info, indent=2, ensure_ascii=False) if isinstance(cluster_info, dict) else str(cluster_info)
    base_prompt = FSM_GENERATION_PROMPT_TEMPLATE.format(cluster_info=cluster_info_str)
    
    feedback = None
    retry_delay = 1  # Initial retry delay in seconds

    for attempt in range(max_retries):
        if feedback:
            prompt = base_prompt + f"""

The previously generated FSM was judged incorrect. Here is the feedback from the judge:
{feedback}

Please correct the FSM based on this feedback and generate an improved version.
"""
        else:
            prompt = base_prompt
        
        try:
            response = fsm_generator.invoke(prompt)
            clean_response = clean_json_response(response.content, cluster_name)
            
            if not clean_response:
                logger.warning(f"Invalid response format, retrying...")
                time.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 10)  # Exponential backoff, max 10s
                continue
            
            try:
                fsm_data = json.loads(clean_response)
            except json.JSONDecodeError as json_error:
                logger.warning(f"JSON parse error: {json_error}, retrying...")
                time.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 10)
                continue
            
            judge_response = judge_fsm(clean_response, cluster_info_str)
            
            if '"correct": true' in judge_response.lower():
                logger.info(f"✓ FSM approved (attempt {attempt + 1})")
                
                if 'fsm_model' in fsm_data:
                    fsm_data['fsm_model']['generation_timestamp'] = datetime.now().isoformat()
                    fsm_data['fsm_model']['generation_attempts'] = attempt + 1
                    fsm_data['fsm_model']['judge_approved'] = True
                
                return fsm_data
            else:
                feedback = judge_response
                
        except Exception as e:
            logger.error(f"Generation error (attempt {attempt + 1}): {e}")
            time.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, 10)
    
    logger.error(f"Failed to generate approved FSM for {cluster_name} after {max_retries} attempts")
    return None

if __name__ == "__main__":
    import sys
    
    # Default paths matching cluster_fsm_generator_old.py structure
    input_file = "cluster_details/1.5_OnOff_Cluster_detail.json"
    output_dir = "fsm_models"  # Output directory like cluster_fsm_generator_old.py
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_dir = sys.argv[2]
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        with open(input_file, "r", encoding='utf-8') as f:
            cluster_info = json.load(f)
        
        # Generate FSM with judge feedback loop
        fsm_data = generate_fsm(cluster_info)
        
        if fsm_data:
            # Extract cluster name and section number for output file
            cluster_name = "unknown"
            section_number = None
            
            if 'fsm_model' in fsm_data:
                cluster_name = fsm_data['fsm_model'].get('cluster_name', 'unknown')
            
            # Try to get section number from metadata
            if isinstance(cluster_info, dict):
                metadata = cluster_info.get('metadata', {})
                section_number = metadata.get('section_number', None)
            
            # Sanitize cluster name for filename (matching cluster_fsm_generator_old.py)
            safe_cluster_name = "".join(c for c in cluster_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_cluster_name = safe_cluster_name.replace(' ', '_')
            
            # Create filename base with section number (matching cluster_fsm_generator_old.py format)
            if section_number:
                filename_base = f"{section_number}_{safe_cluster_name}"
            else:
                filename_base = f"{safe_cluster_name}"
            
            # Output filepath (matching cluster_fsm_generator_old.py format: {section}_{name}_fsm.json)
            json_output = os.path.join(output_dir, f"{filename_base}_fsm.json")
            
            # Save FSM JSON file
            with open(json_output, "w", encoding='utf-8') as f:
                json.dump(fsm_data, f, indent=2, ensure_ascii=False)
            logger.info(f"✓ Saved FSM to: {json_output}")
            
            # Print summary
            print("\n" + "="*80)
            print("FSM GENERATION SUCCESSFUL")
            print("="*80)
            print(f"Cluster: {cluster_name}")
            if section_number:
                print(f"Section: {section_number}")
            if 'fsm_model' in fsm_data:
                print(f"States: {len(fsm_data['fsm_model'].get('states', []))}")
                print(f"Transitions: {len(fsm_data['fsm_model'].get('transitions', []))}")
                print(f"Commands: {len(fsm_data['fsm_model'].get('commands_handled', []))}")
                print(f"Generation attempts: {fsm_data['fsm_model'].get('generation_attempts', 'N/A')}")
            print(f"Output file: {json_output}")
            print(f"Output directory: {os.path.abspath(output_dir)}")
            print("="*80 + "\n")
            
        else:
            logger.error("Failed to generate a correct FSM after multiple attempts")
            print("\n" + "="*80)
            print("FSM GENERATION FAILED")
            print("="*80)
            print("The FSM could not be approved by the judge after maximum retries.")
            print("Please check the logs for details.")
            print("="*80 + "\n")
            sys.exit(1)
            
    except FileNotFoundError:
        logger.error(f"Input file not found: {input_file}")
        print(f"Error: Could not find input file '{input_file}'")
        print("Usage: python llm_as_judge.py [input_file.json] [output_dir]")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"Error: {e}")
        sys.exit(1)
    