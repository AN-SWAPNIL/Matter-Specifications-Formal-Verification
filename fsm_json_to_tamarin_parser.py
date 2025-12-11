"""
FSM JSON to Tamarin Code Parser
================================
Converts Matter FSM JSON files to Tamarin protocol specifications.

Author: FSM Generator Team
Date: December 2024
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime


class FSMToTamarinParser:
    """Parser that converts FSM JSON to Tamarin protocol code."""
    
    def __init__(self, json_path: str):
        """Initialize parser with FSM JSON file."""
        self.json_path = json_path
        self.fsm_data = self._load_json()
        self.cluster_name = self._sanitize_name(self.fsm_data.get("cluster_name", "Unknown"))
        self.states = self.fsm_data.get("states", [])
        self.transitions = self.fsm_data.get("transitions", [])
        self.initial_state = self.fsm_data.get("initial_state", "")
        self.attributes = self.fsm_data.get("attributes_used", [])
        self.commands = self.fsm_data.get("commands_handled", [])
        
    def _load_json(self) -> Dict[str, Any]:
        """Load and parse the FSM JSON file."""
        print(f"📂 Loading FSM from: {self.json_path}")
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle nested structure if it exists
            if "fsm_model" in data:
                data = data["fsm_model"]
            
            print(f"✅ Loaded FSM with {len(data.get('states', []))} states and {len(data.get('transitions', []))} transitions")
            return data
        except Exception as e:
            print(f"❌ Error loading JSON: {e}")
            sys.exit(1)
    
    def _sanitize_name(self, name: str) -> str:
        """Sanitize names for Tamarin syntax."""
        # Replace spaces and special characters with underscores
        sanitized = name.replace(" ", "_").replace("/", "_").replace("-", "_")
        # Remove any remaining invalid characters
        sanitized = ''.join(c for c in sanitized if c.isalnum() or c == '_')
        return sanitized
    
    def _generate_functions(self) -> str:
        """Generate Tamarin function declarations."""
        functions = []
        
        # Boolean values (avoid reserved keywords)
        functions.append("b_true/0, b_false/0")
        
        # State enumerations
        state_funcs = [f"st_{self._sanitize_name(s['name'])}/0" for s in self.states]
        functions.append(", ".join(state_funcs))
        
        # Command/trigger enumerations
        cmd_funcs = [f"cmd_{self._sanitize_name(cmd)}/0" for cmd in self.commands]
        if cmd_funcs:
            functions.append(", ".join(cmd_funcs))
        
        # Timer value abstractions (if needed for timing)
        functions.append("tv_zero/0, tv_pos/0, tv_ffff/0")
        
        return "functions: " + ",\n           ".join(functions)
    
    def _generate_init_rule(self) -> str:
        """Generate initial state rule."""
        init_state = self.initial_state or (self.states[0]['name'] if self.states else "Unknown")
        init_state_func = f"st_{self._sanitize_name(init_state)}"
        
        # Initialize attributes - simplified version
        # In production, you'd parse attribute initial values from FSM
        attr_init = ", ".join(["b_false"] * len(self.attributes)) if self.attributes else ""
        
        rule = f"""
rule Init_{self.cluster_name}:
  let tid = ~tid
  in
  [ Fr(~tid) ]
  --[ ClusterInit(tid, '{self.cluster_name}') ]->
  [ St(tid, {init_state_func}, {attr_init}) ]
"""
        return rule
    
    def _generate_transition_rule(self, trans: Dict[str, Any], index: int) -> str:
        """Generate a Tamarin rule from a transition."""
        from_state = self._sanitize_name(trans.get("from_state", "Unknown"))
        to_state = self._sanitize_name(trans.get("to_state", "Unknown"))
        trigger = self._sanitize_name(trans.get("trigger", "Event"))
        guard = trans.get("guard_condition", "true")
        actions = trans.get("actions", [])
        
        rule_name = f"Trans_{from_state}_to_{to_state}_{trigger}_{index}"
        
        # Build premise
        premise = f"[ St(tid, st_{from_state}, attrs) ]"
        
        # Build guard (simplified - in production parse complex guards)
        guard_str = ""
        if guard and guard.lower() != "true":
            guard_str = f"  // Guard: {guard}\n"
        
        # Build action facts
        action_facts = f"[ StateTransition(tid, st_{from_state}, st_{to_state}, cmd_{trigger}) ]"
        
        # Build conclusion
        conclusion = f"[ St(tid, st_{to_state}, attrs_new) ]"
        
        # Build rule (FIX: action facts and arrow must be on same line)
        rule = f"""
rule {rule_name}:
  let attrs = <attr1, attr2>  // Placeholder: expand with actual attributes
      attrs_new = attrs  // Placeholder: update based on actions
  in
{guard_str}  {premise}
  --{action_facts}->
  {conclusion}
"""
        
        if actions:
            rule += f"  // Actions: {', '.join(actions[:3])}{'...' if len(actions) > 3 else ''}\n"
        
        return rule
    
    def _generate_transition_rules(self) -> str:
        """Generate all transition rules."""
        rules = []
        for idx, trans in enumerate(self.transitions):
            try:
                rule = self._generate_transition_rule(trans, idx)
                rules.append(rule)
            except Exception as e:
                print(f"⚠️  Warning: Could not generate rule for transition {idx}: {e}")
        
        return "\n".join(rules)
    
    def _generate_lemmas(self) -> str:
        """Generate basic lemmas for verification."""
        lemmas = []
        
        # Sources lemma - ensures all transitions originate from init
        lemmas.append("""
lemma sources [sources]:
  "All tid s1 s2 cmd #i. 
    StateTransition(tid, s1, s2, cmd) @ #i 
    ==> 
    Ex #j. ClusterInit(tid, '""" + self.cluster_name + """') @ #j & #j < #i"
""")
        
        # Executability lemma - proves the model can execute
        lemmas.append("""
lemma executability [exists-trace]:
  "Ex tid s1 s2 cmd #i #j. 
    ClusterInit(tid, '""" + self.cluster_name + """') @ #i 
    & StateTransition(tid, s1, s2, cmd) @ #j 
    & #i < #j"
""")
        
        return "\n".join(lemmas)
    
    def generate_tamarin_code(self) -> str:
        """Generate complete Tamarin protocol code."""
        print(f"🔧 Generating Tamarin code for {self.cluster_name}...")
        
        theory_name = f"{self.cluster_name}_Matter_FSM"
        
        # Build the theory
        code_parts = []
        
        # Header
        code_parts.append(f"theory {theory_name}")
        code_parts.append("begin")
        code_parts.append("")
        
        # Built-ins
        code_parts.append("builtins: hashing, symmetric-encryption")
        code_parts.append("")
        
        # Functions
        code_parts.append(self._generate_functions())
        code_parts.append("")
        
        # Init rule
        code_parts.append(self._generate_init_rule())
        code_parts.append("")
        
        # Transition rules
        code_parts.append("// ========== State Transition Rules ==========")
        code_parts.append(self._generate_transition_rules())
        code_parts.append("")
        
        # Lemmas
        code_parts.append("// ========== Lemmas ==========")
        code_parts.append(self._generate_lemmas())
        code_parts.append("")
        
        # End
        code_parts.append("end")
        
        tamarin_code = "\n".join(code_parts)
        print(f"✅ Generated {len(tamarin_code)} characters of Tamarin code")
        
        return tamarin_code
    
    def save_tamarin_code(self, output_path: str, tamarin_code: str) -> None:
        """Save generated Tamarin code to file."""
        print(f"💾 Saving Tamarin code to: {output_path}")
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(tamarin_code)
            print(f"✅ Saved successfully")
        except Exception as e:
            print(f"❌ Error saving file: {e}")
            sys.exit(1)
    
    def validate_tamarin_code(self, tamarin_file: str) -> Tuple[bool, str]:
        """
        Validate Tamarin code using tamarin-prover in WSL.
        
        Returns:
            Tuple of (is_valid, output_message)
        """
        print(f"\n🔍 Validating Tamarin code...")
        print(f"   File: {tamarin_file}")
        
        # Convert Windows path to WSL path
        win_path = Path(tamarin_file).absolute()
        wsl_path = str(win_path).replace('\\', '/')
        # Convert drive letter (e.g., D:\ to /mnt/d/)
        if ':' in wsl_path:
            drive = wsl_path[0].lower()
            wsl_path = f"/mnt/{drive}/{wsl_path[3:]}"
        
        print(f"   WSL path: {wsl_path}")
        
        try:
            # Run tamarin-prover in WSL
            cmd = [
                "wsl",
                "/home/linuxbrew/.linuxbrew/bin/tamarin-prover",
                wsl_path,
                "--parse"
            ]
            
            print(f"   🔧 Running: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            is_valid = result.returncode == 0
            
            print(f"   Return code: {result.returncode}")
            print(f"   {'✅ VALID' if is_valid else '❌ INVALID'}")
            
            output = []
            output.append(f"{'='*70}")
            output.append(f"Validation Status: {'✅ VALID' if is_valid else '❌ INVALID'}")
            output.append(f"Return Code: {result.returncode}")
            output.append(f"{'='*70}")
            
            if result.stdout:
                output.append(f"\n📤 STDOUT:\n{result.stdout}")
            
            if result.stderr:
                output.append(f"\n⚠️  STDERR:\n{result.stderr}")
            
            return is_valid, "\n".join(output)
            
        except FileNotFoundError:
            error_msg = "❌ Error: 'wsl' command not found. Make sure WSL is installed."
            print(f"   {error_msg}")
            return False, error_msg
        
        except subprocess.TimeoutExpired:
            error_msg = "❌ Error: Tamarin parsing timed out after 60 seconds."
            print(f"   {error_msg}")
            return False, error_msg
        
        except Exception as e:
            error_msg = f"❌ Unexpected error: {str(e)}"
            print(f"   {error_msg}")
            return False, error_msg


def main():
    """Main execution function."""
    print("="*70)
    print("🚀 FSM to Tamarin Parser")
    print("="*70)
    print()
    
    # Configuration
    INPUT_JSON = "./codes/fsm_models/1.5_OnOff_Cluster_fsm.json"
    OUTPUT_DIR = "./parsed_tamarin_output"
    
    # Create output directory
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    
    # Check if input file exists
    if not Path(INPUT_JSON).exists():
        print(f"❌ Error: Input file not found: {INPUT_JSON}")
        sys.exit(1)
    
    try:
        # Create parser
        parser = FSMToTamarinParser(INPUT_JSON)
        
        # Generate Tamarin code
        tamarin_code = parser.generate_tamarin_code()
        
        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"{OUTPUT_DIR}/{parser.cluster_name}_{timestamp}.spthy"
        parser.save_tamarin_code(output_file, tamarin_code)
        
        print()
        print("="*70)
        print("📋 Generated Tamarin Code Preview:")
        print("="*70)
        print(tamarin_code[:1000])
        print("...")
        print()
        
        # Validate the generated code
        is_valid, validation_output = parser.validate_tamarin_code(output_file)
        
        print()
        print("="*70)
        print("📊 Validation Results:")
        print("="*70)
        print(validation_output)
        print()
        
        # Summary
        print("="*70)
        print("✅ Parser Execution Complete!")
        print("="*70)
        print(f"📄 Output file: {output_file}")
        print(f"📊 Validation: {'✅ PASSED' if is_valid else '❌ FAILED'}")
        print(f"📁 Output directory: {OUTPUT_DIR}")
        print()
        
        if not is_valid:
            print("⚠️  Note: The generated code has syntax errors.")
            print("   This is expected for a basic parser - you may need to manually refine the code.")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
