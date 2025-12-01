#!/usr/bin/env python3
"""
FSM to Tamarin Model Converter with LLM-as-Judge
Converts FSM JSON models to Tamarin prover theories
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
    FSM_TO_TAMARIN_PROMPT_TEMPLATE
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class FSMToTamarinConverter:
    """Class wrapper for FSM to Tamarin conversion and judge loop."""

    def __init__(self,
                 api_key: str = API_KEY,
                 model: str = LLM_MODEL,
                 provider: str = MODEL_PROVIDER,
                 temperature: float = LLM_TEMPERATURE,
                 max_tokens: int = LLM_MAX_OUTPUT_TOKENS,
                 prompt_template: str = FSM_TO_TAMARIN_PROMPT_TEMPLATE):
        self.api_key = api_key
        self.model = model
        self.provider = provider
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.prompt_template = prompt_template

        # Ensure API key env variable (backwards-compatible)
        if not os.environ.get("GOOGLE_API_KEY") and self.api_key:
            os.environ["GOOGLE_API_KEY"] = self.api_key

        # Initialize LLM clients
        try:
            self.converter = init_chat_model(
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
        except Exception as e:
            logger.error(f"Error initializing models: {e}")
            raise

    def clean_tamarin_response(self, response: str, cluster_name: str = "Unknown") -> str:
        """Clean Tamarin response by removing markdown code blocks."""
        clean_response = response.strip()
        
        # Remove markdown code blocks
        if clean_response.startswith('```tamarin'):
            clean_response = clean_response[10:]
        elif clean_response.startswith('```theory'):
            clean_response = clean_response[9:]
        elif clean_response.startswith('```'):
            clean_response = clean_response[3:]
        
        if clean_response.endswith('```'):
            clean_response = clean_response[:-3]
        
        clean_response = clean_response.strip()

        # Basic validation - Tamarin theories start with "theory"
        if not clean_response.startswith('theory'):
            logger.warning(f"Invalid Tamarin response format for cluster {cluster_name}")
            return ""
        return clean_response

    def judge_tamarin(self, tamarin_model: str, fsm_json: str) -> str:
        """Evaluate the correctness of a Tamarin conversion using the judge model."""
        prompt = f"""
You are a judge that evaluates the correctness of a Tamarin prover model conversion from an FSM JSON.

Your task is to determine if the Tamarin model correctly translates the FSM structure and semantics.

Evaluation criteria:
1. **Syntax correctness**: Valid Tamarin syntax (theory, builtins, functions, rules, lemmas)
2. **State preservation**: All FSM states mapped to Tamarin facts
3. **Transition fidelity**: All FSM transitions converted to Tamarin rules with correct guards
4. **Action facts**: State changes and events captured as action facts
5. **Lemmas**: Safety/liveness properties derived from FSM invariants
6. **Completeness**: All FSM elements (states, transitions, commands, events) covered

Your output format should be json parsable and strictly follow this format:
{{
    "correct": true/false,
    "explanation": "Your explanation or reasoning here"
}}

Now evaluate the following conversion:

TAMARIN MODEL:
{tamarin_model}

SOURCE FSM JSON:
{fsm_json}
"""
        try:
            response = self.judge.invoke(prompt)
            time.sleep(30)
            return response.content
        except Exception as e:
            logger.error(f"Error during judge evaluation: {e}")
            return json.dumps({"correct": False, "explanation": f"Judge error: {str(e)}"})

    def convert_fsm_to_tamarin(self, fsm_data: Dict[str, Any], max_retries: int = 10) -> Optional[Dict[str, Any]]:
        """Convert FSM JSON to Tamarin model with iterative refinement based on judge feedback."""
        cluster_name = "Unknown"
        if isinstance(fsm_data, dict) and 'fsm_model' in fsm_data:
            cluster_name = fsm_data['fsm_model'].get('cluster_name', 'Unknown')

        logger.info(f"Converting FSM to Tamarin for cluster: {cluster_name}")

        fsm_json_str = json.dumps(fsm_data, indent=2, ensure_ascii=False) if isinstance(fsm_data, dict) else str(fsm_data)
        base_prompt = self.prompt_template.replace("{fsm_json}", fsm_json_str)

        feedback = None
        last_valid_response = None  # Track last valid Tamarin model
        best_attempt = 0
        
        for attempt in range(max_retries):
            if feedback:
                feedback_section = f"""

The previously converted Tamarin model was judged incorrect. Here is the feedback from the judge:
{feedback}

Please correct the Tamarin model based on this feedback and generate an improved version.
"""
                prompt = base_prompt + feedback_section
            else:
                prompt = base_prompt

            logger.info(f"Attempt {attempt + 1}/{max_retries}")

            try:
                response = self.converter.invoke(prompt)
                time.sleep(30)

                clean_response = self.clean_tamarin_response(response.content, cluster_name)
                if not clean_response.startswith('theory'):
                    logger.warning("Invalid response format, retrying...")
                    continue

                # Save this as a valid attempt
                last_valid_response = clean_response
                best_attempt = attempt + 1

                # Judge the Tamarin conversion
                judge_response = self.judge_tamarin(clean_response, fsm_json_str)

                if '"correct": true' in judge_response.lower():
                    logger.info(f"✓ Tamarin conversion approved (attempt {attempt + 1})")
                    
                    # Build result structure
                    tamarin_data = {
                        "tamarin_model": {
                            "cluster_name": cluster_name,
                            "theory_code": clean_response,
                            "metadata": {
                                "generation_timestamp": datetime.now().isoformat(),
                                "generation_attempts": attempt + 1,
                                "judge_approved": True,
                                "conversion_source": "fsm_json"
                            }
                        }
                    }
                    
                    # Add FSM source metadata if available
                    if isinstance(fsm_data, dict) and 'fsm_model' in fsm_data:
                        fsm_metadata = fsm_data['fsm_model'].get('metadata', {})
                        if fsm_metadata:
                            tamarin_data['tamarin_model']['metadata']['fsm_metadata'] = fsm_metadata
                    
                    return tamarin_data
                else:
                    logger.warning("✗ Rejected, retrying with feedback...")
                    feedback = judge_response

            except Exception as e:
                logger.error(f"Error during conversion attempt: {e}")

        logger.error(f"Failed to convert FSM to Tamarin for {cluster_name} after {max_retries} attempts")
        
        # If we have at least one valid response, return it even without judge approval
        if last_valid_response:
            logger.warning(f"Returning last valid Tamarin model from attempt {best_attempt} (not judge-approved)")
            tamarin_data = {
                "tamarin_model": {
                    "cluster_name": cluster_name,
                    "theory_code": last_valid_response,
                    "metadata": {
                        "generation_timestamp": datetime.now().isoformat(),
                        "generation_attempts": best_attempt,
                        "judge_approved": False,
                        "conversion_source": "fsm_json",
                        "note": "Best attempt saved - judge approval not obtained"
                    }
                }
            }
            
            # Add FSM source metadata if available
            if isinstance(fsm_data, dict) and 'fsm_model' in fsm_data:
                fsm_metadata = fsm_data['fsm_model'].get('metadata', {})
                if fsm_metadata:
                    tamarin_data['tamarin_model']['metadata']['fsm_metadata'] = fsm_metadata
            
            return tamarin_data
        
        return None

    def save_tamarin_file(self, tamarin_data: Dict[str, Any], fsm_data: Dict[str, Any], output_dir: str) -> Optional[str]:
        """Save Tamarin model to output directory with both .spthy and .json formats."""
        try:
            cluster_name = "unknown"
            section_number = None
            
            if 'tamarin_model' in tamarin_data:
                cluster_name = tamarin_data['tamarin_model'].get('cluster_name', 'unknown')

            # Try to get section number from FSM metadata
            if isinstance(fsm_data, dict) and 'fsm_model' in fsm_data:
                fsm_metadata = fsm_data['fsm_model'].get('metadata', {})
                source_meta = fsm_metadata.get('source_metadata', {})
                section_number = source_meta.get('section_number', None)

            safe_cluster_name = "".join(c for c in cluster_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_cluster_name = safe_cluster_name.replace(' ', '_')

            if section_number:
                filename_base = f"{section_number}_{safe_cluster_name}"
            else:
                filename_base = f"{safe_cluster_name}"

            os.makedirs(output_dir, exist_ok=True)
            
            # Save .spthy file (Tamarin source)
            spthy_output = os.path.join(output_dir, f"{filename_base}_tamarin.spthy")
            theory_code = tamarin_data['tamarin_model'].get('theory_code', '')
            with open(spthy_output, 'w', encoding='utf-8') as f:
                f.write(theory_code)
            logger.info(f"✓ Saved Tamarin theory to: {spthy_output}")
            
            # Save JSON file (with metadata)
            json_output = os.path.join(output_dir, f"{filename_base}_tamarin.json")
            with open(json_output, 'w', encoding='utf-8') as f:
                json.dump(tamarin_data, f, indent=2, ensure_ascii=False)
            logger.info(f"✓ Saved Tamarin JSON to: {json_output}")

            return spthy_output
        except Exception as e:
            logger.error(f"Error saving Tamarin files: {e}")
            return None

    def run(self, input_file: str, output_dir: str = "tamarin_models") -> int:
        """Run the conversion pipeline from an FSM JSON file and save output to `output_dir`.

        Returns exit code 0 on success, 1 on failure.
        """
        logger.info(f"Loading FSM JSON from: {input_file}")
        logger.info(f"Output directory: {output_dir}")

        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                fsm_data = json.load(f)

            logger.info("FSM JSON loaded successfully")
            tamarin_data = self.convert_fsm_to_tamarin(fsm_data)

            if not tamarin_data:
                logger.error("Failed to convert FSM to Tamarin after multiple attempts")
                print("\n" + "="*80)
                print("FSM TO TAMARIN CONVERSION FAILED")
                print("="*80)
                print("The Tamarin model could not be approved by the judge after maximum retries.")
                print("No valid Tamarin theory was generated.")
                print("Please check the logs for details.")
                print("="*80 + "\n")
                return 1

            spthy_output = self.save_tamarin_file(tamarin_data, fsm_data, output_dir)

            # Print summary
            print("\n" + "="*80)
            print("FSM TO TAMARIN CONVERSION SUCCESSFUL")
            print("="*80)
            cluster_name = tamarin_data.get('tamarin_model', {}).get('cluster_name', 'unknown')
            print(f"Cluster: {cluster_name}")
            
            metadata = tamarin_data.get('tamarin_model', {}).get('metadata', {})
            fsm_meta = metadata.get('fsm_metadata', {})
            source_meta = fsm_meta.get('source_metadata', {}) if fsm_meta else {}
            
            if source_meta.get('section_number'):
                print(f"Section: {source_meta['section_number']}")
            if source_meta.get('source_pages'):
                print(f"Source pages: {source_meta['source_pages']}")
            
            # Count FSM elements
            if isinstance(fsm_data, dict) and 'fsm_model' in fsm_data:
                fsm_model = fsm_data['fsm_model']
                print(f"FSM states: {len(fsm_model.get('states', []))}")
                print(f"FSM transitions: {len(fsm_model.get('transitions', []))}")
            
            # Count rules and lemmas in theory
            theory_code = tamarin_data.get('tamarin_model', {}).get('theory_code', '')
            rule_count = theory_code.count('\nrule ')
            lemma_count = theory_code.count('\nlemma ')
            
            print(f"Tamarin rules: {rule_count}")
            print(f"Tamarin lemmas: {lemma_count}")
            print(f"Conversion attempts: {metadata.get('generation_attempts', 'N/A')}")
            print(f"Judge approved: {metadata.get('judge_approved', 'N/A')}")
            if not metadata.get('judge_approved', True):
                print(f"⚠️  WARNING: {metadata.get('note', 'Model not judge-approved')}")
            print(f"Output file: {spthy_output}")
            print(f"Output directory: {os.path.abspath(output_dir)}")
            print("="*80 + "\n")
            return 0

        except FileNotFoundError:
            logger.error(f"Input file not found: {input_file}")
            print(f"Error: Could not find input file '{input_file}'")
            print("Usage: python fsm_to_tamarin_converter.py [fsm_file.json] [output_dir]")
            return 1
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            print(f"Error: {e}")
            return 1


def main():
    input_file = "fsm_models_g2.5f/1.5_OnOff_Cluster_fsm.json"
    output_dir = "tamarin_models_from_fsm"
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_dir = sys.argv[2]

    converter = FSMToTamarinConverter()
    exit_code = converter.run(input_file, output_dir)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
