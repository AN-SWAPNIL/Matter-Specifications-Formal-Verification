#!/usr/bin/env python3
"""
Matter Cluster Tamarin Model Generator with LLM-as-Judge
Generates Tamarin prover models directly from cluster specifications
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
    TAMARIN_GENERATION_PROMPT_TEMPLATE
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TamarinGenerator:
    """Class wrapper for Tamarin model generation and judge loop."""

    def __init__(self,
                 api_key: str = API_KEY,
                 model: str = LLM_MODEL,
                 provider: str = MODEL_PROVIDER,
                 temperature: float = LLM_TEMPERATURE,
                 max_tokens: int = LLM_MAX_OUTPUT_TOKENS,
                 prompt_template: str = TAMARIN_GENERATION_PROMPT_TEMPLATE):
        self.api_key = api_key
        self.model = model
        self.provider = provider
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.prompt_template = prompt_template

        # Ensure API key env variable (backwards-compatible)
        if not os.environ.get("OPENAI_API_KEY") and self.api_key:
            os.environ["OPENAI_API_KEY"] = self.api_key

        # Initialize LLM clients
        try:
            self.tamarin_generator = init_chat_model(
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

    def judge_tamarin(self, tamarin_model: str, user_input: str) -> str:
        """Evaluate the correctness of a generated Tamarin model using the judge model."""
        prompt = f"""
You are a judge that evaluates the correctness of a Tamarin prover model based on its representation of protocol behavior.
You will be given a Tamarin theory and the cluster specification it should model.

Your task is to determine if the Tamarin model correctly implements the cluster behavior based on the provided specification.

Evaluation criteria:
1. **Syntax correctness**: Valid Tamarin syntax (theory declaration, builtins, functions, rules, lemmas)
2. **State modeling**: Facts correctly represent cluster states and attributes
3. **Transition rules**: Rules model state transitions from commands with proper guards
4. **Action facts**: Action facts capture behavioral events for verification
5. **Lemmas**: Security/safety properties correctly formulated
6. **Completeness**: All commands, states, and transitions covered

Your output format should be json parsable and strictly follow this format:
{{
    "correct": true/false,
    "explanation": "Your explanation or reasoning here"
}}

Now evaluate the following Tamarin model and cluster specification:

TAMARIN MODEL:
{tamarin_model}

CLUSTER SPECIFICATION:
{user_input}
"""
        try:
            response = self.judge.invoke(prompt)
            time.sleep(30)
            return response.content
        except Exception as e:
            logger.error(f"Error during judge evaluation: {e}")
            return json.dumps({"correct": False, "explanation": f"Judge error: {str(e)}"})

    def generate_tamarin(self, cluster_info: Dict[str, Any], max_retries: int = 10) -> Optional[Dict[str, Any]]:
        """Generate Tamarin model with iterative refinement based on judge feedback."""
        cluster_name = "Unknown"
        if isinstance(cluster_info, dict):
            cluster_name = cluster_info.get('cluster_info', {}).get('cluster_name', 'Unknown')

        logger.info(f"Generating Tamarin model for cluster: {cluster_name}")

        cluster_info_str = json.dumps(cluster_info, indent=2, ensure_ascii=False) if isinstance(cluster_info, dict) else str(cluster_info)
        # Use string replacement instead of .format() to avoid KeyError with template placeholders
        base_prompt = self.prompt_template.replace('{cluster_info}', cluster_info_str)

        feedback = None
        last_valid_response = None  # Track last valid Tamarin model
        best_attempt = 0
        
        for attempt in range(max_retries):
            if feedback:
                feedback_section = f"""

The previously generated Tamarin model was judged incorrect. Here is the feedback from the judge:
{feedback}

Please correct the Tamarin model based on this feedback and generate an improved version.
"""
                prompt = base_prompt + feedback_section
            else:
                prompt = base_prompt

            logger.info(f"Attempt {attempt + 1}/{max_retries}")

            try:
                response = self.tamarin_generator.invoke(prompt)
                time.sleep(30)

                clean_response = self.clean_tamarin_response(response.content, cluster_name)
                if not clean_response.startswith('theory'):
                    logger.warning("Invalid response format, retrying...")
                    continue

                # Save this as a valid attempt
                last_valid_response = clean_response
                best_attempt = attempt + 1

                # Judge the Tamarin model
                judge_response = self.judge_tamarin(clean_response, cluster_info_str)

                if '"correct": true' in judge_response.lower():
                    logger.info(f"✓ Tamarin model approved (attempt {attempt + 1})")
                    
                    # Build result structure
                    tamarin_data = {
                        "tamarin_model": {
                            "cluster_name": cluster_name,
                            "theory_code": clean_response,
                            "metadata": {
                                "generation_timestamp": datetime.now().isoformat(),
                                "generation_attempts": attempt + 1,
                                "judge_approved": True
                            }
                        }
                    }
                    
                    # Add source metadata if available
                    if isinstance(cluster_info, dict) and 'metadata' in cluster_info:
                        source_metadata = cluster_info['metadata']
                        tamarin_data['tamarin_model']['metadata']['source_metadata'] = {
                            "source_pages": source_metadata.get('source_pages', 'N/A'),
                            "section_number": source_metadata.get('section_number', 'N/A'),
                            "category": source_metadata.get('category', 'N/A')
                        }
                    
                    return tamarin_data
                else:
                    logger.warning("✗ Rejected, retrying with feedback...")
                    feedback = judge_response

            except Exception as e:
                logger.error(f"Error during generation attempt: {e}")

        logger.error(f"Failed to generate approved Tamarin model for {cluster_name} after {max_retries} attempts")
        
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
                        "note": "Best attempt saved - judge approval not obtained"
                    }
                }
            }
            
            # Add source metadata if available
            if isinstance(cluster_info, dict) and 'metadata' in cluster_info:
                source_metadata = cluster_info['metadata']
                tamarin_data['tamarin_model']['metadata']['source_metadata'] = {
                    "source_pages": source_metadata.get('source_pages', 'N/A'),
                    "section_number": source_metadata.get('section_number', 'N/A'),
                    "category": source_metadata.get('category', 'N/A')
                }
            
            return tamarin_data
        
        return None

    def save_tamarin_file(self, tamarin_data: Dict[str, Any], cluster_info: Dict[str, Any], output_dir: str) -> Optional[str]:
        """Save Tamarin model to output directory with both .spthy and .json formats."""
        try:
            cluster_name = "unknown"
            section_number = None
            
            if 'tamarin_model' in tamarin_data:
                cluster_name = tamarin_data['tamarin_model'].get('cluster_name', 'unknown')

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
        """Run the generation pipeline from an input cluster detail file and save output to `output_dir`.

        Returns exit code 0 on success, 1 on failure.
        """
        logger.info(f"Loading cluster information from: {input_file}")
        logger.info(f"Output directory: {output_dir}")

        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                cluster_info = json.load(f)

            logger.info("Cluster information loaded successfully")
            tamarin_data = self.generate_tamarin(cluster_info)

            if not tamarin_data:
                logger.error("Failed to generate a correct Tamarin model after multiple attempts")
                print("\n" + "="*80)
                print("TAMARIN MODEL GENERATION FAILED")
                print("="*80)
                print("The Tamarin model could not be approved by the judge after maximum retries.")
                print("No valid Tamarin theory was generated.")
                print("Please check the logs for details.")
                print("="*80 + "\n")
                return 1

            spthy_output = self.save_tamarin_file(tamarin_data, cluster_info, output_dir)

            # Print summary
            print("\n" + "="*80)
            print("TAMARIN MODEL GENERATION SUCCESSFUL")
            print("="*80)
            cluster_name = tamarin_data.get('tamarin_model', {}).get('cluster_name', 'unknown')
            print(f"Cluster: {cluster_name}")
            
            metadata = tamarin_data.get('tamarin_model', {}).get('metadata', {})
            source_meta = metadata.get('source_metadata', {})
            if source_meta.get('section_number'):
                print(f"Section: {source_meta['section_number']}")
            if source_meta.get('source_pages'):
                print(f"Source pages: {source_meta['source_pages']}")
            
            # Count rules and lemmas in theory
            theory_code = tamarin_data.get('tamarin_model', {}).get('theory_code', '')
            rule_count = theory_code.count('\nrule ')
            lemma_count = theory_code.count('\nlemma ')
            
            print(f"Rules: {rule_count}")
            print(f"Lemmas: {lemma_count}")
            print(f"Generation attempts: {metadata.get('generation_attempts', 'N/A')}")
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
            print("Usage: python cluster_tamarin_generator.py [input_file.json] [output_dir]")
            return 1
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            print(f"Error: {e}")
            return 1


def main():
    input_file = "cluster_details_gpt5.1/1.5_OnOff_Cluster_detail.json"
    output_dir = "tamarin_models_from_cluster"
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_dir = sys.argv[2]

    generator = TamarinGenerator()
    exit_code = generator.run(input_file, output_dir)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
