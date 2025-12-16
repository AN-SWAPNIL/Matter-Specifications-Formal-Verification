#!/usr/bin/env python3
"""
Matter Cluster FSM Generator with LLM-as-Judge
Refactored to class-based `FSMGenerator` to match project style.
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
    FSM_GENERATION_PROMPT_TEMPLATE,
    FSM_JUDGE_PROMPT_TEMPLATE,
    FSM_GENERATION_PARSER_OPTIMIZED_PROMPT
)

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class FSMGenerator:
    """Class wrapper for FSM generation and judge loop."""

    def __init__(self,
                 api_key: str = API_KEY,
                 model: str = LLM_MODEL,
                 provider: str = MODEL_PROVIDER,
                 temperature: float = LLM_TEMPERATURE,
                 max_tokens: int = LLM_MAX_OUTPUT_TOKENS,
                 prompt_template: str = FSM_GENERATION_PROMPT_TEMPLATE,  # Changed to v2.0 prompt
                 judge_prompt_template: str = FSM_JUDGE_PROMPT_TEMPLATE):
        self.api_key = api_key
        self.model = model
        self.provider = provider
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.prompt_template = prompt_template
        self.judge_prompt_template = judge_prompt_template

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
            logger.info(
                f"Initialized models: {self.model} from {self.provider}")
        except Exception as e:
            logger.error(f"Error initializing models: {e}")
            raise

    def clean_json_response(self, response: str, cluster_name: str = "Unknown") -> str:
        """Clean JSON response by removing markdown code blocks and extra whitespace."""
        clean_response = response.strip()

        # Remove markdown code blocks
        if clean_response.startswith('```json'):
            clean_response = clean_response[7:]
        elif clean_response.startswith('```'):
            clean_response = clean_response[3:]
        if clean_response.endswith('```'):
            clean_response = clean_response[:-3]

        clean_response = clean_response.strip()

        # Remove any remaining markdown or comments
        lines = clean_response.split('\n')
        json_lines = []
        for line in lines:
            # Skip comment lines
            stripped = line.strip()
            if stripped.startswith('//') or stripped.startswith('#'):
                continue
            # Remove inline comments
            if '//' in line:
                line = line[:line.index('//')]
            json_lines.append(line)

        clean_response = '\n'.join(json_lines)

        if not clean_response.startswith('{'):
            logger.warning(
                f"Invalid FSM response format for cluster {cluster_name}")
            return ""
        return clean_response

    def judge_fsm(self, fsm: str, user_input: str) -> str:
        """Evaluate the correctness of a generated FSM using the judge model."""
        prompt = self.judge_prompt_template.format(
            fsm=fsm, cluster_info=user_input)
        try:
            response = self.judge.invoke(prompt)
            time.sleep(30)
            return response.content
        except Exception as e:
            logger.error(f"Error during judge evaluation: {e}")
            return json.dumps({"correct": False, "explanation": f"Judge error: {str(e)}"})

    def generate_fsm(self, cluster_info: Dict[str, Any], max_retries: int = 10) -> Optional[Dict[str, Any]]:
        """Generate FSM with iterative refinement based on judge feedback."""
        cluster_name = "Unknown"
        if isinstance(cluster_info, dict):
            cluster_name = cluster_info.get(
                'cluster_info', {}).get('cluster_name', 'Unknown')

        logger.info(f"Generating FSM for cluster: {cluster_name}")

        cluster_info_str = json.dumps(cluster_info, indent=2, ensure_ascii=False) if isinstance(
            cluster_info, dict) else str(cluster_info)
        base_prompt = self.prompt_template.format(
            cluster_info=cluster_info_str)

        feedback = None
        last_fsm_data = None
        last_judge_feedback = None
        previous_fsm_str = None

        for attempt in range(max_retries):
            if feedback and previous_fsm_str:
                print("Feedback from judge:")
                print(feedback)
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

            logger.info(f"Attempt {attempt + 1}/{max_retries}")

            try:
                response = self.fsm_generator.invoke(prompt)
                time.sleep(30)

                clean_response = self.clean_json_response(
                    response.content, cluster_name)
                if not clean_response.startswith('{'):
                    logger.warning("Invalid response format, retrying...")
                    continue

                try:
                    fsm_data = json.loads(clean_response)
                    last_fsm_data = fsm_data  # Store last valid FSM
                    previous_fsm_str = json.dumps(
                        fsm_data, indent=2, ensure_ascii=False)  # Store for next iteration
                except json.JSONDecodeError as json_error:
                    logger.warning(
                        f"JSON parse error: {json_error}, retrying...")
                    continue

                judge_response = self.judge_fsm(
                    clean_response, cluster_info_str)
                # print("Judge Response:", judge_response)
                last_judge_feedback = judge_response  # Store last feedback

                if '"correct": true' in judge_response.lower():
                    logger.info(f"✓ FSM approved (attempt {attempt + 1})")
                    if 'metadata' not in fsm_data.get('fsm_model', {}):
                        fsm_data.setdefault('fsm_model', {})['metadata'] = {}

                    fsm_data['fsm_model']['metadata']['generation_timestamp'] = datetime.now(
                    ).isoformat()
                    fsm_data['fsm_model']['metadata']['generation_attempts'] = attempt + 1
                    fsm_data['fsm_model']['metadata']['judge_approved'] = True
                    return fsm_data
                else:
                    logger.warning("✗ Rejected, retrying with feedback...")
                    feedback = judge_response

            except Exception as e:
                logger.error(f"Error during generation attempt: {e}")

        logger.error(
            f"Failed to generate approved FSM for {cluster_name} after {max_retries} attempts")

        # Save the last generated FSM even if not approved
        if last_fsm_data:
            logger.warning(
                f"Saving last generated FSM (unapproved) for {cluster_name}")
            if 'metadata' not in last_fsm_data.get('fsm_model', {}):
                last_fsm_data.setdefault('fsm_model', {})['metadata'] = {}

            last_fsm_data['fsm_model']['metadata']['generation_timestamp'] = datetime.now(
            ).isoformat()
            last_fsm_data['fsm_model']['metadata']['generation_attempts'] = max_retries
            last_fsm_data['fsm_model']['metadata']['judge_approved'] = False
            last_fsm_data['fsm_model']['metadata']['last_judge_feedback'] = last_judge_feedback
            return last_fsm_data

        return None

    def save_fsm_file(self, fsm_data: Dict[str, Any], cluster_info: Dict[str, Any], output_dir: str) -> Optional[str]:
        """Save FSM JSON to `output_dir` using the same filename scheme as before."""
        try:
            cluster_name = "unknown"
            section_number = None
            if 'fsm_model' in fsm_data:
                cluster_name = fsm_data['fsm_model'].get(
                    'cluster_name', 'unknown')

            if isinstance(cluster_info, dict):
                metadata = cluster_info.get('metadata', {})
                section_number = metadata.get('section_number', None)

            safe_cluster_name = "".join(
                c for c in cluster_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
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

        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                cluster_info = json.load(f)

            logger.info("Cluster information loaded successfully")
            fsm_data = self.generate_fsm(cluster_info)

            if not fsm_data:
                logger.error(
                    "Failed to generate any valid FSM after multiple attempts")
                print("\n" + "="*80)
                print("FSM GENERATION FAILED")
                print("="*80)
                print("No valid FSM could be generated after maximum retries.")
                print("Please check the logs for details.")
                print("="*80 + "\n")
                return 1

            json_output = self.save_fsm_file(
                fsm_data, cluster_info, output_dir)

            # Check if FSM was approved
            is_approved = fsm_data.get('fsm_model', {}).get(
                'metadata', {}).get('judge_approved', False)

            # Print summary
            print("\n" + "="*80)
            if is_approved:
                print("FSM GENERATION SUCCESSFUL (APPROVED)")
            else:
                print("FSM GENERATION COMPLETED (NOT APPROVED - NEEDS REVIEW)")
            print("="*80)
            cluster_name = fsm_data.get('fsm_model', {}).get(
                'cluster_name', 'unknown')
            print(f"Cluster: {cluster_name}")
            metadata = fsm_data.get('fsm_model', {}).get('metadata', {})
            if isinstance(cluster_info, dict):
                section_number = cluster_info.get(
                    'metadata', {}).get('section_number')
                if section_number:
                    print(f"Section: {section_number}")

            fsm = fsm_data.get('fsm_model', {})
            print(f"States: {len(fsm.get('states', []))}")
            print(f"Transitions: {len(fsm.get('transitions', []))}")
            print(f"Commands: {len(fsm.get('commands_handled', []))}")
            print(f"Definitions: {len(fsm.get('definitions', []))}")
            print(f"References: {len(fsm.get('references', []))}")
            print(
                f"Generation attempts: {metadata.get('generation_attempts', 'N/A')}")
            print(f"Judge approved: {metadata.get('judge_approved', 'N/A')}")
            print(f"Output file: {json_output}")
            print(f"Output directory: {os.path.abspath(output_dir)}")
            print("="*80 + "\n")
            return 0

        except FileNotFoundError:
            logger.error(f"Input file not found: {input_file}")
            print(f"Error: Could not find input file '{input_file}'")
            print(
                "Usage: python cluster_fsm_generator.py [input_file.json] [output_dir]")
            return 1
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            print(f"Error: {e}")
            return 1


def main():
    # input_file = "cluster_details/6.2_Account_Login_Cluster_detail.json"
    input_file = "cluster_details/1.5_OnOff_Cluster_detail.json"
    output_dir = "fsm_models_v2/"
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_dir = sys.argv[2]

    generator = FSMGenerator()
    exit_code = generator.run(input_file, output_dir)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
