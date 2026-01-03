#!/usr/bin/env python3
"""
FSM to ProVerif Model Converter with LLM-as-Judge
Converts FSM JSON models to ProVerif specifications for security verification.

ProVerif uses the applied pi-calculus to model security protocols and can verify:
- Reachability properties
- Secrecy properties  
- Correspondence assertions (authentication)
- Observational equivalence
"""

import os
import json
import logging
import time
import sys
import subprocess
import tempfile
import platform
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
    FSM_TO_PROVERIF_PROMPT_TEMPLATE,
    PROVERIF_JUDGE_PROMPT_TEMPLATE
)

MAX_TRIES = 10

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class FSMToProVerifConverter:
    """Class wrapper for FSM to ProVerif conversion and judge loop."""

    def __init__(self,
                 api_key: str = API_KEY,
                 model: str = LLM_MODEL,
                 provider: str = MODEL_PROVIDER,
                 temperature: float = LLM_TEMPERATURE,
                 max_tokens: int = LLM_MAX_OUTPUT_TOKENS,
                 prompt_template: str = FSM_TO_PROVERIF_PROMPT_TEMPLATE,
                 judge_template: str = PROVERIF_JUDGE_PROMPT_TEMPLATE):
        self.api_key = api_key
        self.model = model
        self.provider = provider
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.prompt_template = prompt_template
        self.judge_template = judge_template

        # Ensure API key env variable (backwards-compatible)
        if not os.environ.get("GOOGLE_API_KEY") and self.api_key:
            os.environ["GOOGLE_API_KEY"] = self.api_key
        if not os.environ.get("OPENAI_API_KEY") and self.api_key:
            os.environ["OPENAI_API_KEY"] = self.api_key

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

    def run_proverif_parse(self, proverif_code: str, cluster_name: str = "Unknown") -> Dict[str, Any]:
        """Run ProVerif on the generated code and return results."""
        tmp_file_path = None
        
        try:
            # Create temporary file with .pv extension
            with tempfile.NamedTemporaryFile(mode='w', suffix='.pv', delete=False, encoding='utf-8') as tmp_file:
                tmp_file.write(proverif_code)
                tmp_file_path = tmp_file.name
            
            # Run ProVerif with syntax check only (fast validation)
            # ProVerif doesn't have a --parse-only flag, so we run it normally but capture output
            result = subprocess.run(
                ['proverif', tmp_file_path],
                capture_output=True,
                text=True,
                timeout=120  # ProVerif can take longer
            )
            
            # Clean up temp file
            if tmp_file_path and os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
            
            # Check for success indicators in output
            parse_success = result.returncode == 0 or "RESULT" in result.stdout
            
            # Check for common error patterns
            has_errors = "Error:" in result.stderr or "Syntax error" in result.stderr or \
                        "Error:" in result.stdout or "parse error" in result.stdout.lower()
            
            if has_errors:
                parse_success = False
            
            # Print parse results for debugging
            print(f"\n{'='*80}")
            print(f"ProVerif parse result for {cluster_name}")
            print(f"{'='*80}")
            print(f"Success: {parse_success}")
            print(f"Return code: {result.returncode}")
            if result.stdout:
                print(f"\n--- STDOUT ---")
                print(result.stdout[:2000])  # First 2000 chars
            if result.stderr:
                print(f"\n--- STDERR ---")
                print(result.stderr[:1500])  # First 1500 chars

            print(f"{'='*80}\n")
                        
            return {
                "success": parse_success,
                "returncode": result.returncode,
                "stdout": result.stdout[-3000:] if result.stdout else "",  # Last 3000 chars
                "stderr": result.stderr[-2000:] if result.stderr else ""   # Last 2000 chars
            }
            
        except subprocess.TimeoutExpired:
            logger.warning(f"ProVerif timed out for {cluster_name}")
            return {
                "success": None,  # Unknown - might be valid but complex
                "returncode": -1,
                "stdout": "",
                "stderr": "Timeout: ProVerif did not complete within 120 seconds"
            }
        except FileNotFoundError:
            logger.warning("proverif not found in PATH - skipping parse validation")
            return {
                "success": None,
                "returncode": -1,
                "stdout": "",
                "stderr": "proverif not found in system PATH. Install from https://proverif.inria.fr/"
            }
        except Exception as e:
            logger.error(f"Error running proverif: {e}")
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": f"Error: {str(e)}"
            }
        finally:
            # Ensure cleanup
            if tmp_file_path and os.path.exists(tmp_file_path):
                try:
                    os.unlink(tmp_file_path)
                except:
                    pass
    
    def clean_proverif_response(self, response: str, cluster_name: str = "Unknown") -> str:
        """Clean ProVerif response by removing markdown code blocks."""
        clean_response = response.strip()
        
        # Remove markdown code blocks
        if clean_response.startswith('```proverif'):
            clean_response = clean_response[11:]
        elif clean_response.startswith('```pv'):
            clean_response = clean_response[5:]
        elif clean_response.startswith('```'):
            clean_response = clean_response[3:]
        
        if clean_response.endswith('```'):
            clean_response = clean_response[:-3]
        
        clean_response = clean_response.strip()

        # Basic validation - ProVerif files typically start with comments or type declarations
        valid_starts = ['(*', 'type ', 'const ', 'free ', 'fun ', 'event ', 'let ', 'process', 'query']
        is_valid = any(clean_response.startswith(s) for s in valid_starts)
        
        if not is_valid:
            logger.warning(f"Invalid ProVerif response format for cluster {cluster_name}")
            # Try to find where actual ProVerif code starts
            for start in valid_starts:
                idx = clean_response.find(start)
                if idx >= 0:
                    clean_response = clean_response[idx:]
                    break
        
        return clean_response

    def judge_proverif(self, proverif_model: str, fsm_json: str, parse_result: Optional[Dict[str, Any]] = None) -> str:
        """Evaluate the correctness of a ProVerif conversion using the judge model."""
        
        # Build parse result section
        parse_section = ""
        if parse_result:
            if parse_result.get("success") is None:
                parse_section = "\n## PROVERIF PARSER OUTPUT\n⚠️ ProVerif not available or timed out - syntax not validated\n"
            elif parse_result.get("success"):
                parse_section = "\n## PROVERIF PARSER OUTPUT\n✓ ProVerif execution successful - no syntax errors\n"
                if parse_result.get("stdout"):
                    # Extract query results
                    parse_section += f"Results (summary):\n{parse_result['stdout'][-1500:]}\n"
            else:
                parse_section = f"\n## PROVERIF PARSER OUTPUT\n✗ ProVerif FAILED (exit code {parse_result.get('returncode')})\n"
                if parse_result.get("stderr"):
                    parse_section += f"Errors:\n{parse_result['stderr']}\n"
                if parse_result.get("stdout"):
                    parse_section += f"Output:\n{parse_result['stdout'][-1000:]}\n"
        
        # Use replace instead of format to avoid issues with { } in JSON
        prompt = self.judge_template.replace("{proverif_model}", proverif_model).replace("{fsm_json}", fsm_json)
        
        # Add parse section to prompt
        prompt = f"{parse_section}\n{prompt}"
        
        try:
            response = self.judge.invoke(prompt)
            time.sleep(30)  # Rate limiting
            return response.content
        except Exception as e:
            logger.error(f"Error during judge evaluation: {e}")
            return json.dumps({"correct": False, "explanation": f"Judge error: {str(e)}"})

    def convert_fsm_to_proverif(self, fsm_data: Dict[str, Any], max_retries: int = MAX_TRIES) -> Optional[Dict[str, Any]]:
        """Convert FSM JSON to ProVerif model with iterative refinement based on judge feedback."""
        cluster_name = "Unknown"
        if isinstance(fsm_data, dict) and 'fsm_model' in fsm_data:
            cluster_name = fsm_data['fsm_model'].get('cluster_name', 'Unknown')

        logger.info(f"Converting FSM to ProVerif for cluster: {cluster_name}")

        fsm_json_str = json.dumps(fsm_data, indent=2, ensure_ascii=False) if isinstance(fsm_data, dict) else str(fsm_data)
        base_prompt = self.prompt_template.replace("{fsm_json}", fsm_json_str)

        feedback = None
        last_valid_response = None  # Track last valid ProVerif model
        best_attempt = 0
        previous_proverif_str = None
        last_judge_feedback = None
        
        for attempt in range(max_retries):
            if feedback and previous_proverif_str:
                # Extract parse errors if present in feedback
                parse_errors_hint = ""
                if '"syntax_fixes"' in feedback or 'FAILED' in feedback or 'Error' in feedback:
                    parse_errors_hint = "\n⚠️ CRITICAL: The previous model had SYNTAX ERRORS that prevented ProVerif from parsing it.\nFix these syntax errors FIRST before addressing semantic issues.\n"
                
                feedback_section = f"""

The previously converted ProVerif model was judged incorrect. Here is the feedback from the judge:
{feedback}

{parse_errors_hint}

PREVIOUSLY GENERATED PROVERIF MODEL:
{previous_proverif_str}

Please correct the ProVerif model based on this feedback and generate an improved version.
Address the specific issues mentioned in the feedback while maintaining correct ProVerif syntax.
If there were parse errors, fix the syntax first to ensure the model is parseable by proverif.
"""
                prompt = base_prompt + feedback_section
            else:
                prompt = base_prompt

            logger.info(f"Attempt {attempt + 1}/{max_retries}")

            try:
                response = self.converter.invoke(prompt)
                time.sleep(30)  # Rate limiting

                clean_response = self.clean_proverif_response(response.content, cluster_name)
                
                # Check for valid ProVerif code
                valid_starts = ['(*', 'type ', 'const ', 'free ', 'fun ', 'event ', 'let ', 'process', 'query']
                is_valid_start = any(clean_response.startswith(s) for s in valid_starts)
                
                if not is_valid_start and 'type ' not in clean_response[:500]:
                    logger.warning("Invalid response format, retrying...")
                    continue

                # Save this as a valid attempt
                last_valid_response = clean_response
                previous_proverif_str = clean_response  # Store for next iteration
                best_attempt = attempt + 1

                # Run ProVerif validation
                parse_result = self.run_proverif_parse(clean_response, cluster_name)
                logger.info(f"ProVerif parse result: {parse_result.get('success')}")
                
                # Judge the ProVerif conversion (with parse results)
                judge_response = self.judge_proverif(clean_response, fsm_json_str, parse_result)
                last_judge_feedback = judge_response  # Store last feedback

                # Check if judge approved (robust check)
                is_correct = False
                try:
                    if judge_response and isinstance(judge_response, str):
                        is_correct = '"correct": true' in judge_response.lower() or \
                                   '"correct":true' in judge_response.lower()
                except Exception as e:
                    logger.warning(f"Error checking judge response: {e}")
                    is_correct = False

                if is_correct:
                    logger.info(f"✓ ProVerif conversion approved (attempt {attempt + 1})")
                    
                    # Build result structure
                    proverif_data = {
                        "proverif_model": {
                            "cluster_name": cluster_name,
                            "model_code": clean_response,
                            "metadata": {
                                "generation_timestamp": datetime.now().isoformat(),
                                "generation_attempts": attempt + 1,
                                "judge_approved": True,
                                "conversion_source": "fsm_json",
                                "proverif_validated": parse_result.get("success", None)
                            }
                        }
                    }
                    
                    # Add FSM source metadata if available
                    if isinstance(fsm_data, dict) and 'fsm_model' in fsm_data:
                        fsm_metadata = fsm_data['fsm_model'].get('metadata', {})
                        if fsm_metadata:
                            proverif_data['proverif_model']['metadata']['fsm_metadata'] = fsm_metadata
                    
                    return proverif_data
                else:
                    logger.warning("✗ Rejected, retrying with feedback...")
                    feedback = judge_response

            except Exception as e:
                logger.error(f"Error during conversion attempt: {e}")

        logger.error(f"Failed to convert FSM to ProVerif for {cluster_name} after {max_retries} attempts")
        
        # If we have at least one valid response, return it even without judge approval
        if last_valid_response:
            logger.warning(f"Returning last valid ProVerif model from attempt {best_attempt} (not judge-approved)")
            proverif_data = {
                "proverif_model": {
                    "cluster_name": cluster_name,
                    "model_code": last_valid_response,
                    "metadata": {
                        "generation_timestamp": datetime.now().isoformat(),
                        "generation_attempts": best_attempt,
                        "judge_approved": False,
                        "conversion_source": "fsm_json",
                        "last_judge_feedback": last_judge_feedback,
                        "note": "Best attempt saved - judge approval not obtained"
                    }
                }
            }
            
            # Add FSM source metadata if available
            if isinstance(fsm_data, dict) and 'fsm_model' in fsm_data:
                fsm_metadata = fsm_data['fsm_model'].get('metadata', {})
                if fsm_metadata:
                    proverif_data['proverif_model']['metadata']['fsm_metadata'] = fsm_metadata
            
            return proverif_data
        
        return None

    def save_proverif_file(self, proverif_data: Dict[str, Any], fsm_data: Dict[str, Any], output_dir: str) -> Optional[str]:
        """Save ProVerif model to output directory with both .pv and .json formats."""
        try:
            cluster_name = "unknown"
            section_number = None
            
            if 'proverif_model' in proverif_data:
                cluster_name = proverif_data['proverif_model'].get('cluster_name', 'unknown')

            # Try to get section number from FSM metadata
            if isinstance(fsm_data, dict) and 'fsm_model' in fsm_data:
                fsm_metadata = fsm_data['fsm_model'].get('metadata', {})
                section_number = fsm_metadata.get('section_number', None)

            safe_cluster_name = "".join(c for c in cluster_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_cluster_name = safe_cluster_name.replace(' ', '_')

            if section_number:
                filename_base = f"{section_number}_{safe_cluster_name}"
            else:
                filename_base = f"{safe_cluster_name}"

            os.makedirs(output_dir, exist_ok=True)
            
            # Save .pv file (ProVerif source)
            pv_output = os.path.join(output_dir, f"{filename_base}_proverif.pv")
            model_code = proverif_data['proverif_model'].get('model_code', '')
            with open(pv_output, 'w', encoding='utf-8') as f:
                f.write(model_code)
            logger.info(f"✓ Saved ProVerif model to: {pv_output}")
            
            # Save JSON file (with metadata)
            json_output = os.path.join(output_dir, f"{filename_base}_proverif.json")
            with open(json_output, 'w', encoding='utf-8') as f:
                json.dump(proverif_data, f, indent=2, ensure_ascii=False)
            logger.info(f"✓ Saved ProVerif JSON to: {json_output}")

            return pv_output
        except Exception as e:
            logger.error(f"Error saving ProVerif files: {e}")
            return None

    def run(self, input_file: str, output_dir: str = "proverif_models") -> int:
        """Run the conversion pipeline from an FSM JSON file and save output to `output_dir`.

        Returns exit code 0 on success, 1 on failure.
        """
        logger.info(f"Loading FSM JSON from: {input_file}")
        logger.info(f"Output directory: {output_dir}")

        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                fsm_data = json.load(f)

            logger.info("FSM JSON loaded successfully")
            proverif_data = self.convert_fsm_to_proverif(fsm_data)

            if not proverif_data:
                logger.error("Failed to convert FSM to ProVerif after multiple attempts")
                print("\n" + "="*80)
                print("FSM TO PROVERIF CONVERSION FAILED")
                print("="*80)
                print("No valid ProVerif model could be generated.")
                print("Please check the logs for details.")
                print("="*80 + "\n")
                return 1

            pv_output = self.save_proverif_file(proverif_data, fsm_data, output_dir)
            
            # Check if approved
            is_approved = proverif_data.get('proverif_model', {}).get('metadata', {}).get('judge_approved', False)

            # Print summary
            print("\n" + "="*80)
            if is_approved:
                print("FSM TO PROVERIF CONVERSION SUCCESSFUL (APPROVED)")
            else:
                print("FSM TO PROVERIF CONVERSION COMPLETED (NOT APPROVED - NEEDS REVIEW)")
            print("="*80)
            cluster_name = proverif_data.get('proverif_model', {}).get('cluster_name', 'unknown')
            print(f"Cluster: {cluster_name}")
            
            metadata = proverif_data.get('proverif_model', {}).get('metadata', {})
            fsm_meta = metadata.get('fsm_metadata', {})
            
            if fsm_meta.get('section_number'):
                print(f"Section: {fsm_meta['section_number']}")
            if fsm_meta.get('source_pages'):
                print(f"Source pages: {fsm_meta['source_pages']}")
            
            # Count FSM elements
            if isinstance(fsm_data, dict) and 'fsm_model' in fsm_data:
                fsm_model = fsm_data['fsm_model']
                print(f"FSM states: {len(fsm_model.get('states', []))}")
                print(f"FSM transitions: {len(fsm_model.get('transitions', []))}")
            
            # Count ProVerif elements
            model_code = proverif_data.get('proverif_model', {}).get('model_code', '')
            type_count = model_code.count('type ')
            const_count = model_code.count('const ')
            event_count = model_code.count('event ')
            query_count = model_code.count('query ')
            
            print(f"ProVerif types: {type_count}")
            print(f"ProVerif constants: {const_count}")
            print(f"ProVerif events: {event_count}")
            print(f"ProVerif queries: {query_count}")
            print(f"Conversion attempts: {metadata.get('generation_attempts', 'N/A')}")
            print(f"Judge approved: {metadata.get('judge_approved', 'N/A')}")
            print(f"ProVerif validated: {metadata.get('proverif_validated', 'N/A')}")
            if not metadata.get('judge_approved', True):
                print(f"⚠️  WARNING: {metadata.get('note', 'Model not judge-approved')}")
            print(f"Output file: {pv_output}")
            print(f"Output directory: {os.path.abspath(output_dir)}")
            print("="*80 + "\n")
            return 0

        except FileNotFoundError:
            logger.error(f"Input file not found: {input_file}")
            print(f"Error: Could not find input file '{input_file}'")
            print("Usage: python cluster_proverif_generator.py [fsm_file.json] [output_dir]")
            return 1
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            print(f"Error: {e}")
            return 1


def main():
    """Main entry point."""
    input_file = "fsm_models/1.6_Level_Control_fsm.json"
    output_dir = "proverif_models"
    
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_dir = sys.argv[2]

    converter = FSMToProVerifConverter()
    exit_code = converter.run(input_file, output_dir)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
