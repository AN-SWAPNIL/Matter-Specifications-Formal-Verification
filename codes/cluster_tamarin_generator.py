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

MAX_TRIES = 10

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

    def run_tamarin_parse(self, tamarin_code: str, cluster_name: str = "Unknown") -> Dict[str, Any]:
        """Run tamarin-prover --parse on the generated code and return results."""
        import subprocess
        import tempfile
        import platform
        
        try:
            # Create temporary file with .spthy extension
            with tempfile.NamedTemporaryFile(mode='w', suffix='.spthy', delete=False, encoding='utf-8') as tmp_file:
                tmp_file.write(tamarin_code)
                tmp_file_path = tmp_file.name
            
            # Convert Windows path to WSL path if needed
            file_path_for_tamarin = tmp_file_path
            if platform.system() == "Windows":
                # Convert Windows path to WSL path (C:\path\to\file -> /mnt/c/path/to/file)
                file_path_for_tamarin = tmp_file_path.replace('\\', '/')
                if len(file_path_for_tamarin) > 1 and file_path_for_tamarin[1] == ':':
                    drive = file_path_for_tamarin[0].lower()
                    file_path_for_tamarin = f"/mnt/{drive}{file_path_for_tamarin[2:]}"
                logger.info(f"Converted path for WSL: {tmp_file_path} -> {file_path_for_tamarin}")
            
            # Run tamarin-prover --parse
            # Run tamarin-prover with well-formedness check
            # --prove=dummy loads theory and validates semantic correctness without proof search
            # This catches undeclared action facts and other semantic errors that --parse misses
            result = subprocess.run(
                ['wsl', '/home/linuxbrew/.linuxbrew/bin/tamarin-prover', file_path_for_tamarin, '--prove=dummy'],
                capture_output=True,
                text=True,
                timeout=60  # Longer timeout for semantic validation
            )
            
            # Clean up temp file
            os.unlink(tmp_file_path)
            
            # Check if theory loaded successfully (ignore WSL warnings in stderr)
            theory_loaded = "Theory loaded" in result.stdout or "Theory loaded" in result.stderr
            
            # Extract validation summary (everything after the parsed theory)
            stdout_text = result.stdout
            validation_summary = ""
            
            # Look for summary section or warning comments
            if "/*\nWARNING:" in stdout_text:
                # Extract from first WARNING comment to end
                warning_start = stdout_text.find("/*\nWARNING:")
                validation_summary = stdout_text[warning_start:]
            elif "summary of summaries:" in stdout_text:
                # Extract summary section
                summary_start = stdout_text.find("==============================================================================")
                if summary_start > 0:
                    validation_summary = stdout_text[summary_start:]
            
            # Check for errors
            has_errors = "Error:" in result.stderr or "error:" in result.stderr or \
                        "wellformedness check failed" in stdout_text or \
                        "WARNING:" in stdout_text
            
            parse_success = result.returncode == 0 and theory_loaded and not has_errors
            
            # Filter out WSL systemd warnings from stderr
            filtered_stderr = result.stderr
            if "wsl: Failed to start the systemd user session" in filtered_stderr or \
               "See journalctl for more details" in filtered_stderr:
                # Remove WSL warning lines, keep only actual Tamarin errors
                stderr_lines = filtered_stderr.split('\n')
                filtered_lines = [line for line in stderr_lines 
                                 if 'wsl:' not in line.lower() and 
                                    'systemd' not in line.lower() and 
                                    'journalctl' not in line.lower() and
                                    line.strip()]
                filtered_stderr = '\n'.join(filtered_lines)
                        
            return {
                "success": parse_success,
                "returncode": result.returncode,
                "stdout": validation_summary if validation_summary else stdout_text[-2000:],  # Last 2000 chars if no summary found
                "stderr": filtered_stderr if filtered_stderr.strip() else ""
            }
            
        except subprocess.TimeoutExpired:
            logger.warning(f"Tamarin parse timed out for {cluster_name}")
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": "Timeout: tamarin-prover did not complete within 30 seconds"
            }
        except FileNotFoundError:
            logger.warning("tamarin-prover not found in PATH - skipping parse validation")
            return {
                "success": None,
                "returncode": -1,
                "stdout": "",
                "stderr": "tamarin-prover not found in system PATH"
            }
        except Exception as e:
            logger.error(f"Error running tamarin-prover: {e}")
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": f"Error: {str(e)}"
            }
        finally:
            print(f"Tamarin parse stdout for {cluster_name}:\n{result}")
    
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

    def judge_tamarin(self, tamarin_model: str, fsm_json: str, parse_result: Optional[Dict[str, Any]] = None) -> str:
        """Evaluate the correctness of a Tamarin conversion using the judge model."""
        
        # Build parse result section
        parse_section = ""
        if parse_result:
            if parse_result.get("success") is None:
                parse_section = "\n## TAMARIN PARSER OUTPUT\n⚠️ tamarin-prover not available - syntax not validated\n"
            elif parse_result.get("success"):
                parse_section = "\n## TAMARIN PARSER OUTPUT\n✓ Parse successful - no syntax errors\n"
                if parse_result.get("stdout"):
                    parse_section += f"Output: {parse_result['stdout'][:1000]}\n"
            else:
                parse_section = f"\n## TAMARIN PARSER OUTPUT\n✗ Parse FAILED (exit code {parse_result.get('returncode')})\n"
                if parse_result.get("stderr"):
                    parse_section += f"Errors:\n{parse_result['stderr'][:1000]}\n"
                if parse_result.get("stdout"):
                    parse_section += f"Output:\n{parse_result['stdout'][:1000]}\n"
        
        prompt = f"""
You are an expert Tamarin prover judge evaluating FSM-to-Tamarin conversions for Matter protocol clusters.

Your task: Identify syntax/semantic errors and provide EXACT fixes with line-level guidance.
{parse_section}

## CRITICAL SYNTAX RULES

### 1. FACT ARGUMENT SYNTAX (MOST COMMON ERROR)
**Every argument MUST be separated by comma** - no exceptions!

**Common Parse Errors:**
- `unexpected "W" expecting "," or ")"` → Missing comma before variable starting with "W"
- `unexpected letter expecting ","` → Missing comma between arguments
- `unexpected "." expecting ","` → Period instead of comma (typo)

**Examples:**
```
❌ St(~tid, state, OnTime OffWaitTime, GSC)     // Missing comma before OffWaitTime
✅ St(~tid, state, OnTime, OffWaitTime, GSC)    // Correct

❌ !Config(~tid, f_LT f_DF, f_OFFONLY)          // Missing comma before f_DF  
✅ !Config(~tid, f_LT, f_DF, f_OFFONLY)         // Correct

❌ StateTransition(~tid st_OnIdle, st_OffIdle)  // Missing comma after ~tid
✅ StateTransition(~tid, st_OnIdle, st_OffIdle) // Correct
```

### 2. COMMENT SYNTAX
```
✅ // This is valid
✅ /* Block comment */
❌ // Section: Description  // Colon in comment can cause issues
❌ /*: Title */            // Leading colon causes parse error
```

### 3. VARIABLE NAMING
- No spaces: `OffWaitTime` NOT `Off Wait Time`
- Fresh vars: `~tid`
- Public vars: `$pk`
- Regular vars: lowercase start

### 4. OTHER SYNTAX RULES  
- Only ONE `functions:` block
- No `_` wildcards in premises
- No `|` disjunctions in premises
- No `not()` in premises (only in formulas)
- Consistent `St(...)` arity across all rules

## PARSE ERROR DIAGNOSIS

When you see parse error at **line X, column Y**:
1. **Locate the line** in the Tamarin model
2. **Identify the fact** at that position (St, !Config, StateTransition, etc.)
3. **Check for missing commas** between ALL arguments
4. **Provide exact corrected line**

### Example Diagnosis Process:
```
Parse Error: "line 274, column 24: unexpected W expecting , or )"

Step 1: Line 274 is likely a rule with a fact
Step 2: Column 24 suggests error mid-way through argument list
Step 3: Character "W" likely starts a variable like "OffWaitTime" or "WaitTime"
Step 4: Missing comma BEFORE this variable

Likely Error:
St(~tid, state, OnTime OffWaitTime, GSC)
                      ↑ Missing comma here

Correct Syntax:
St(~tid, state, OnTime, OffWaitTime, GSC)
```

## SEMANTIC CHECKS
- Every FSM state → `st_StateName/0` function
- Every FSM transition → Tamarin rule(s)
- Guards → pattern matching in premises
- Inequality guards: `X != value` MUST be split into separate rules per allowed value
- Action facts: Commands emit `Command(tid, 'CmdName')` and `StateTransition(tid, s1, s2)`
- Timer abstraction: `tv_zero/0`, `tv_pos/0`, `tv_ffff/0` (NO arithmetic)
- Config vs State: Immutable in `!Config(...)`, mutable in `St(...)`

## VERDICT LOGIC

**If parse FAILED:**
1. Extract line/column from error message
2. Analyze error type:
   - `unexpected "X" expecting ","` → Missing comma in fact arguments
   - `unexpected ":"` → Remove colon from comments  
   - `unexpected letter` → Variable naming or missing comma
3. Provide EXACT line correction with before/after
4. Set `"correct": false`

**If parse SUCCESS:**
1. Check semantic correctness
2. Verify FSM coverage
3. Set `"correct": true/false`

## OUTPUT FORMAT (JSON ONLY)

{{
    "correct": true/false,
    "explanation": "Detailed explanation with line-level diagnosis for parse errors",
    "issues": [
        "Line X: Specific issue description",
        "Check all St(...) and !Config(...) facts for missing commas"
    ],
    "parse_errors": ["Exact errors from tamarin-prover"],
    "syntax_fixes": [
        {{
            "line": 274,
            "error": "St(~tid, state, OnTime OffWaitTime, GSC)",
            "fix": "St(~tid, state, OnTime, OffWaitTime, GSC)",
            "explanation": "Added missing comma between arguments"
        }}
    ]
}}

Now evaluate:

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

    def convert_fsm_to_tamarin(self, fsm_data: Dict[str, Any], max_retries: int = MAX_TRIES) -> Optional[Dict[str, Any]]:
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
        previous_tamarin_str = None
        last_judge_feedback = None
        
        for attempt in range(max_retries):
            if feedback and previous_tamarin_str:
                # Extract parse errors if present in feedback
                parse_errors_hint = ""
                if '"parse_errors"' in feedback or 'Parse FAILED' in feedback or 'parse FAILED' in feedback:
                    parse_errors_hint = "\n⚠️ CRITICAL: The previous model had SYNTAX ERRORS that prevented Tamarin from parsing it.\nFix these syntax errors FIRST before addressing semantic issues.\n"
                
                feedback_section = f"""

The previously converted Tamarin model was judged incorrect. Here is the feedback from the judge:
{feedback}

{parse_errors_hint}

PREVIOUSLY GENERATED TAMARIN MODEL:
{previous_tamarin_str}

Please correct the Tamarin model based on this feedback and generate an improved version.
Address the specific issues mentioned in the feedback while maintaining correct Tamarin syntax.
If there were parse errors, fix the syntax first to ensure the model is parseable by tamarin-prover.
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
                previous_tamarin_str = clean_response  # Store for next iteration
                best_attempt = attempt + 1

                # Run tamarin-prover --parse validation
                parse_result = self.run_tamarin_parse(clean_response, cluster_name)
                logger.info(f"Parse result: {parse_result.get('success')}")
                
                # Judge the Tamarin conversion (with parse results)
                judge_response = self.judge_tamarin(clean_response, fsm_json_str, parse_result)
                last_judge_feedback = judge_response  # Store last feedback

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
                        "last_judge_feedback": last_judge_feedback,
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
            
            # Also save as .txt file
            txt_output = os.path.join(output_dir, f"{filename_base}_tamarin.txt")
            with open(txt_output, 'w', encoding='utf-8') as f:
                f.write(theory_code)
            logger.info(f"✓ Saved Tamarin theory to: {txt_output}")
            
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
                print("No valid Tamarin theory could be generated.")
                print("Please check the logs for details.")
                print("="*80 + "\n")
                return 1

            spthy_output = self.save_tamarin_file(tamarin_data, fsm_data, output_dir)
            
            # Check if approved
            is_approved = tamarin_data.get('tamarin_model', {}).get('metadata', {}).get('judge_approved', False)

            # Print summary
            print("\n" + "="*80)
            if is_approved:
                print("FSM TO TAMARIN CONVERSION SUCCESSFUL (APPROVED)")
            else:
                print("FSM TO TAMARIN CONVERSION COMPLETED (NOT APPROVED - NEEDS REVIEW)")
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
    input_file = "fsm_models/1.6_Level_Control_fsm.json"
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
