#!/usr/bin/env python3
"""
Matter Cluster FSM Generator with LLM-as-Judge
Two-Pass Generation: FSM first, then Security Properties

Research Basis:
- Decomposed Prompting (DecomP): Breaking complex tasks into sub-tasks improves LLM accuracy
- Least-to-Most Prompting: Solving simpler problems first helps with complex reasoning
- Tamarin best practices: Separate protocol model from security properties

Pass 1: Generate FSM behavioral model (states, transitions, actions)
Pass 2: Generate security properties using FSM + cluster details for context
"""

import os
import json
import logging
import time
import sys
from typing import Dict, Any, Optional
from datetime import datetime
from langchain.chat_models import init_chat_model

# Configuration imports
from config import (
    API_KEY,
    LLM_MODEL,
    MODEL_PROVIDER,
    LLM_TEMPERATURE,
    LLM_MAX_OUTPUT_TOKENS,
    FSM_GENERATION_PROMPT_PASS1_FSM_ONLY,
    FSM_SECURITY_PROPERTIES_PROMPT_PASS2,
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class FSMGenerator:
    """
    Two-Pass FSM Generator with LLM-as-Judge.
    
    Pass 1: Generate FSM behavioral model (states, transitions, actions)
           - Focuses entirely on FSM structure
           - Security properties left empty
           - More detailed transitions due to reduced cognitive load
           
    Pass 2: Generate security properties
           - Input: FSM + cluster details
           - Analyzes existing transitions to derive properties
           - References actual FSM elements in formal specifications
    """

    def __init__(self,
                 api_key: str = API_KEY,
                 model: str = LLM_MODEL,
                 provider: str = MODEL_PROVIDER,
                 temperature: float = LLM_TEMPERATURE,
                 max_tokens: int = LLM_MAX_OUTPUT_TOKENS,
                 fsm_prompt_template: str = FSM_GENERATION_PROMPT_PASS1_FSM_ONLY,
                 security_prompt_template: str = FSM_SECURITY_PROPERTIES_PROMPT_PASS2,
                 two_pass_mode: bool = True):
        self.api_key = api_key
        self.model = model
        self.provider = provider
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.fsm_prompt_template = fsm_prompt_template
        self.security_prompt_template = security_prompt_template
        self.two_pass_mode = two_pass_mode

        # Ensure API key env variable (backwards-compatible)
        if not os.environ.get("GOOGLE_API_KEY") and self.api_key:
            os.environ["GOOGLE_API_KEY"] = self.api_key

        # Initialize LLM clients
        try:
            self.fsm_generator = init_chat_model(
                self.model,
                model_provider=self.provider,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            self.judge = init_chat_model(
                self.model,
                model_provider=self.provider,
                temperature=self.temperature
            )
            logger.info(f"Initialized models: {self.model} from {self.provider}")
            logger.info(f"Two-pass mode: {'ENABLED' if self.two_pass_mode else 'DISABLED'}")
        except Exception as e:
            logger.error(f"Error initializing models: {e}")
            raise

    def clean_json_response(self, response: str, cluster_name: str = "Unknown") -> str:
        """Clean JSON response by removing markdown code blocks and extra whitespace."""
        clean_response = response.strip()
        if clean_response.startswith('```json'):
            clean_response = clean_response[7:]
        elif clean_response.startswith('```'):
            clean_response = clean_response[3:]
        if clean_response.endswith('```'):
            clean_response = clean_response[:-3]
        clean_response = clean_response.strip()

        if not clean_response.startswith('{'):
            logger.warning(f"Invalid FSM response format for cluster {cluster_name}")
            return ""
        return clean_response

    def judge_fsm(self, fsm: str, user_input: str, is_fsm_only: bool = False) -> str:
        """Evaluate the correctness of a generated FSM using the judge model."""
        
        if is_fsm_only:
            # Judge prompt for Pass 1 (FSM only)
            prompt = f"""
You are a judge evaluating a finite state machine (FSM) for a Matter IoT protocol cluster.

EVALUATION CRITERIA:
1. States correctly represent cluster behavioral conditions
2. Transitions cover all commands from specification
3. Guard conditions match specification logic
4. Actions are atomic assignments (no if/else, no loops)
5. Timer behaviors correctly modeled (expiry and decrement)
6. Feature constraints enforced in guards
7. Initial state properly defined
8. All commands from specification are handled

Output JSON format:
{{
    "correct": true/false,
    "explanation": "Brief evaluation summary"
}}

FSM:
{fsm}

Cluster Specification:
{user_input}
"""
        else:
            # Original judge prompt for complete FSM validation
            prompt = f"""
You are a judge evaluating a finite state machine (FSM) for a Matter IoT protocol.

Evaluate based on:
- States represent actual device behaviors
- Transitions cover specification requirements
- Guard conditions are correct
- Actions are atomic
- FSM structure is complete and correct

Output JSON format:
{{
    "correct": true/false,
    "explanation": "Brief evaluation summary"
}}

FSM:
{fsm}

Specification:
{user_input}
"""
        try:
            response = self.judge.invoke(prompt)
            time.sleep(30)
            return response.content
        except Exception as e:
            logger.error(f"Error during judge evaluation: {e}")
            return json.dumps({"correct": False, "explanation": f"Judge error: {str(e)}"})

    def generate_security_properties(self, fsm_data: Dict[str, Any], cluster_info: Dict[str, Any], max_retries: int = 3) -> Dict[str, Any]:
        """
        PASS 2: Generate security properties using FSM context.
        
        This pass analyzes the FSM model and cluster specification to derive
        formal security properties that reference actual FSM elements.
        """
        cluster_name = fsm_data.get('fsm_model', {}).get('cluster_name', 'Unknown')
        logger.info(f"[PASS 2] Generating security properties for: {cluster_name}")
        
        fsm_model_str = json.dumps(fsm_data, indent=2, ensure_ascii=False)
        cluster_info_str = json.dumps(cluster_info, indent=2, ensure_ascii=False) if isinstance(cluster_info, dict) else str(cluster_info)
        
        prompt = self.security_prompt_template.format(
            fsm_model=fsm_model_str,
            cluster_info=cluster_info_str
        )
        
        for attempt in range(max_retries):
            logger.info(f"[PASS 2] Security properties attempt {attempt + 1}/{max_retries}")
            
            try:
                response = self.fsm_generator.invoke(prompt)
                time.sleep(15)  # Shorter wait for Pass 2
                
                clean_response = self.clean_json_response(response.content, cluster_name)
                if not clean_response.startswith('{'):
                    logger.warning("[PASS 2] Invalid response format, retrying...")
                    continue
                
                security_data = json.loads(clean_response)
                
                # Extract security_properties array
                if 'security_properties' in security_data:
                    properties = security_data['security_properties']
                    logger.info(f"[PASS 2] ✓ Generated {len(properties)} security properties")
                    return {"security_properties": properties}
                else:
                    logger.warning("[PASS 2] No security_properties field found, retrying...")
                    continue
                    
            except json.JSONDecodeError as e:
                logger.warning(f"[PASS 2] JSON parse error: {e}, retrying...")
                continue
            except Exception as e:
                logger.error(f"[PASS 2] Error: {e}")
                continue
        
        logger.warning(f"[PASS 2] Failed to generate security properties after {max_retries} attempts, using empty array")
        return {"security_properties": []}

    def merge_fsm_and_security(self, fsm_data: Dict[str, Any], security_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge FSM model with security properties.
        
        Updates the FSM's security_properties field with properties from Pass 2.
        """
        if 'fsm_model' in fsm_data:
            fsm_data['fsm_model']['security_properties'] = security_data.get('security_properties', [])
            
            # Update metadata to indicate two-pass generation
            if 'metadata' not in fsm_data['fsm_model']:
                fsm_data['fsm_model']['metadata'] = {}
            fsm_data['fsm_model']['metadata']['two_pass_generation'] = True
            fsm_data['fsm_model']['metadata']['security_properties_count'] = len(
                security_data.get('security_properties', [])
            )
        
        return fsm_data

    def generate_fsm(self, cluster_info: Dict[str, Any], max_retries: int = 10) -> Optional[Dict[str, Any]]:
        """
        Generate FSM with optional two-pass approach.
        
        If two_pass_mode is enabled:
          - Pass 1: Generate FSM behavioral model (states, transitions, actions)
          - Pass 2: Generate security properties using FSM + cluster details
          - Merge: Combine FSM and security properties
        
        If two_pass_mode is disabled:
          - Single pass generation (original behavior)
        """
        cluster_name = "Unknown"
        if isinstance(cluster_info, dict):
            cluster_name = cluster_info.get('cluster_info', {}).get('cluster_name', 'Unknown')

        cluster_info_str = json.dumps(cluster_info, indent=2, ensure_ascii=False) if isinstance(cluster_info, dict) else str(cluster_info)
        
        if self.two_pass_mode:
            logger.info(f"="*60)
            logger.info(f"TWO-PASS GENERATION for cluster: {cluster_name}")
            logger.info(f"="*60)
            
            # ===================== PASS 1: FSM Generation =====================
            logger.info(f"\n[PASS 1] Generating FSM behavioral model...")
            base_prompt = self.fsm_prompt_template.format(cluster_info=cluster_info_str)
        else:
            # Single-pass mode (backward compatibility)
            logger.info(f"Generating FSM for cluster: {cluster_name} (single-pass mode)")
            base_prompt = self.fsm_prompt_template.format(cluster_info=cluster_info_str)

        feedback = None
        last_fsm_data = None
        last_judge_feedback = None
        previous_fsm_str = None
        
        for attempt in range(max_retries):
            if feedback and previous_fsm_str:
                feedback_section = f"""

The previously generated FSM was judged incorrect. Here is the feedback from the judge:
{feedback}

PREVIOUSLY GENERATED FSM:
{previous_fsm_str}

Please correct the FSM based on this feedback and generate an improved version.
Address the specific issues mentioned in the feedback while maintaining correct FSM structure.
"""
                prompt = base_prompt + feedback_section
            else:
                prompt = base_prompt

            logger.info(f"[PASS 1] Attempt {attempt + 1}/{max_retries}")

            try:
                response = self.fsm_generator.invoke(prompt)
                time.sleep(30)

                clean_response = self.clean_json_response(response.content, cluster_name)
                if not clean_response.startswith('{'):
                    logger.warning("[PASS 1] Invalid response format, retrying...")
                    continue

                try:
                    fsm_data = json.loads(clean_response)
                    last_fsm_data = fsm_data  # Store last valid FSM
                    previous_fsm_str = json.dumps(fsm_data, indent=2, ensure_ascii=False)  # Store for next iteration
                except json.JSONDecodeError as json_error:
                    logger.warning(f"[PASS 1] JSON parse error: {json_error}, retrying...")
                    continue

                # Judge FSM (Pass 1 uses FSM-only judging)
                judge_response = self.judge_fsm(clean_response, cluster_info_str, is_fsm_only=self.two_pass_mode)
                last_judge_feedback = judge_response

                if '"correct": true' in judge_response.lower():
                    logger.info(f"[PASS 1] ✓ FSM approved (attempt {attempt + 1})")
                    if 'metadata' not in fsm_data.get('fsm_model', {}):
                        fsm_data.setdefault('fsm_model', {})['metadata'] = {}

                    fsm_data['fsm_model']['metadata']['generation_timestamp'] = datetime.now().isoformat()
                    fsm_data['fsm_model']['metadata']['generation_attempts'] = attempt + 1
                    fsm_data['fsm_model']['metadata']['judge_approved'] = True
                    fsm_data['fsm_model']['metadata']['pass1_approved'] = True
                    
                    # ===================== PASS 2: Security Properties =====================
                    if self.two_pass_mode:
                        logger.info(f"\n[PASS 2] Generating security properties...")
                        security_data = self.generate_security_properties(fsm_data, cluster_info)
                        fsm_data = self.merge_fsm_and_security(fsm_data, security_data)
                        logger.info(f"[PASS 2] ✓ Security properties merged")
                    
                    return fsm_data
                else:
                    logger.warning("[PASS 1] ✗ Rejected, retrying with feedback...")
                    feedback = judge_response

            except Exception as e:
                logger.error(f"[PASS 1] Error during generation attempt: {e}")

        logger.error(f"Failed to generate approved FSM for {cluster_name} after {max_retries} attempts")
        
        # Save the last generated FSM even if not approved
        if last_fsm_data:
            logger.warning(f"Saving last generated FSM (unapproved) for {cluster_name}")
            if 'metadata' not in last_fsm_data.get('fsm_model', {}):
                last_fsm_data.setdefault('fsm_model', {})['metadata'] = {}
            
            last_fsm_data['fsm_model']['metadata']['generation_timestamp'] = datetime.now().isoformat()
            last_fsm_data['fsm_model']['metadata']['generation_attempts'] = max_retries
            last_fsm_data['fsm_model']['metadata']['judge_approved'] = False
            last_fsm_data['fsm_model']['metadata']['last_judge_feedback'] = last_judge_feedback
            
            # Still run Pass 2 for unapproved FSM if in two-pass mode
            if self.two_pass_mode:
                logger.info(f"\n[PASS 2] Generating security properties for unapproved FSM...")
                security_data = self.generate_security_properties(last_fsm_data, cluster_info)
                last_fsm_data = self.merge_fsm_and_security(last_fsm_data, security_data)
            
            return last_fsm_data
        
        return None

    def save_fsm_file(self, fsm_data: Dict[str, Any], cluster_info: Dict[str, Any], output_dir: str) -> Optional[str]:
        """Save FSM JSON to `output_dir` using the same filename scheme as before."""
        try:
            cluster_name = "unknown"
            section_number = None
            if 'fsm_model' in fsm_data:
                cluster_name = fsm_data['fsm_model'].get('cluster_name', 'unknown')

            if isinstance(cluster_info, dict):
                metadata = cluster_info.get('metadata', {})
                section_number = metadata.get('section_number', None)

            safe_cluster_name = "".join(c for c in cluster_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_cluster_name = safe_cluster_name.replace(' ', '_')

            if section_number:
                filename_base = f"{section_number}_{safe_cluster_name}"
            else:
                filename_base = f"{safe_cluster_name}"

            os.makedirs(output_dir, exist_ok=True)
            json_output = os.path.join(output_dir, f"{filename_base}_fsm.json")

            with open(json_output, 'w', encoding='utf-8') as f:
                json.dump(fsm_data, f, indent=2, ensure_ascii=False)

            logger.info(f"✓ Saved FSM to: {json_output}")
            return json_output
        except Exception as e:
            logger.error(f"Error saving FSM file: {e}")
            return None

    def run(self, input_file: str, output_dir: str = "fsm_models") -> int:
        """Run the generation pipeline from an input cluster detail file and save output to `output_dir`.

        Returns exit code 0 on success, 1 on failure.
        """
        logger.info(f"Loading cluster information from: {input_file}")
        logger.info(f"Output directory: {output_dir}")
        logger.info(f"Generation mode: {'Two-Pass' if self.two_pass_mode else 'Single-Pass'}")

        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                cluster_info = json.load(f)

            logger.info("Cluster information loaded successfully")
            fsm_data = self.generate_fsm(cluster_info)

            if not fsm_data:
                logger.error("Failed to generate any valid FSM after multiple attempts")
                print("\n" + "="*80)
                print("FSM GENERATION FAILED")
                print("="*80)
                print("No valid FSM could be generated after maximum retries.")
                print("Please check the logs for details.")
                print("="*80 + "\n")
                return 1

            json_output = self.save_fsm_file(fsm_data, cluster_info, output_dir)
            
            # Check if FSM was approved
            is_approved = fsm_data.get('fsm_model', {}).get('metadata', {}).get('judge_approved', False)

            # Print summary
            print("\n" + "="*80)
            if is_approved:
                print("FSM GENERATION SUCCESSFUL (APPROVED)")
            else:
                print("FSM GENERATION COMPLETED (NOT APPROVED - NEEDS REVIEW)")
            print("="*80)
            
            cluster_name = fsm_data.get('fsm_model', {}).get('cluster_name', 'unknown')
            print(f"Cluster: {cluster_name}")
            
            metadata = fsm_data.get('fsm_model', {}).get('metadata', {})
            if isinstance(cluster_info, dict):
                section_number = cluster_info.get('metadata', {}).get('section_number')
                if section_number:
                    print(f"Section: {section_number}")

            fsm = fsm_data.get('fsm_model', {})
            
            # Core FSM statistics
            print(f"\n--- FSM Model Statistics ---")
            print(f"States: {len(fsm.get('states', []))}")
            print(f"Transitions: {len(fsm.get('transitions', []))}")
            print(f"Commands: {len(fsm.get('commands_handled', []))}")
            print(f"Definitions: {len(fsm.get('definitions', []))}")
            print(f"References: {len(fsm.get('references', []))}")
            
            # Security properties statistics
            security_props = fsm.get('security_properties', [])
            print(f"\n--- Security Properties ---")
            print(f"Total properties: {len(security_props)}")
            if security_props:
                # Count by type
                prop_types = {}
                for prop in security_props:
                    ptype = prop.get('property_type', 'unknown')
                    prop_types[ptype] = prop_types.get(ptype, 0) + 1
                for ptype, count in sorted(prop_types.items()):
                    print(f"  - {ptype}: {count}")
            
            # Generation metadata
            print(f"\n--- Generation Metadata ---")
            print(f"Mode: {'Two-Pass' if metadata.get('two_pass_generation', False) else 'Single-Pass'}")
            print(f"FSM generation attempts: {metadata.get('generation_attempts', 'N/A')}")
            print(f"Pass 1 (FSM) approved: {metadata.get('pass1_approved', metadata.get('judge_approved', 'N/A'))}")
            if metadata.get('two_pass_generation'):
                print(f"Pass 2 (Security) properties: {metadata.get('security_properties_count', 0)}")
            
            print(f"\n--- Output ---")
            print(f"Output file: {json_output}")
            print(f"Output directory: {os.path.abspath(output_dir)}")
            print("="*80 + "\n")
            return 0

        except FileNotFoundError:
            logger.error(f"Input file not found: {input_file}")
            print(f"Error: Could not find input file '{input_file}'")
            print("Usage: python cluster_fsm_generator.py [input_file.json] [output_dir]")
            return 1
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            print(f"Error: {e}")
            return 1


def main():
    """
    Main entry point for FSM generation.
    
    Usage:
        python cluster_fsm_generator_for_llm.py [input_file.json] [output_dir] [--single-pass]
        
    Arguments:
        input_file: Path to cluster detail JSON file (default: cluster_details/1.5_OnOff_Cluster_detail.json)
        output_dir: Output directory for FSM files (default: fsm_models)
        --single-pass: Disable two-pass generation (default: two-pass enabled)
    
    Two-Pass Mode (default):
        - Pass 1: Generate FSM behavioral model (states, transitions)
        - Pass 2: Generate security properties using FSM context
        - Results in MORE transitions and BETTER security property coverage
        
    Single-Pass Mode (legacy):
        - Generate FSM and security properties together
        - May result in fewer transitions due to LLM cognitive load
    """
    input_file = "cluster_details/1.5_OnOff_Cluster_detail.json"
    output_dir = "fsm_models"
    two_pass_mode = True  # Default: use two-pass generation
    
    # Parse arguments
    args = sys.argv[1:]
    non_flag_args = []
    
    for arg in args:
        if arg == "--single-pass":
            two_pass_mode = False
        elif arg == "--two-pass":
            two_pass_mode = True
        elif arg == "--help" or arg == "-h":
            print(main.__doc__)
            sys.exit(0)
        else:
            non_flag_args.append(arg)
    
    if len(non_flag_args) > 0:
        input_file = non_flag_args[0]
    if len(non_flag_args) > 1:
        output_dir = non_flag_args[1]

    generator = FSMGenerator(two_pass_mode=two_pass_mode)
    exit_code = generator.run(input_file, output_dir)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()