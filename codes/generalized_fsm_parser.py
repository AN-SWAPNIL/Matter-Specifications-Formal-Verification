#!/usr/bin/env python3
"""
Generalized FSM to Tamarin Parser
Parses FSM JSON (any Matter cluster) and generates Tamarin protocol code.

Architecture:
- JSON Loader: Validates and loads FSM structure
- Expression Parser: Parses guard conditions into Tamarin facts
- Action Parser: Parses actions into Tamarin transitions
- Tamarin Generator: Outputs .spthy code with functions, rules, lemmas

Usage:
    python generalized_fsm_parser.py input_fsm.json output.spthy
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime
import subprocess


@dataclass
class Attribute:
    """Represents an FSM attribute with its type."""
    name: str
    attr_type: str = "fact"  # fact, constant, or function
    tamarin_type: str = "Fresh"  # Fresh, Public, or specific type
    

@dataclass
class ParsedGuard:
    """Parsed guard condition with Tamarin facts."""
    facts: List[str]
    raw_expression: str
    

@dataclass
class ParsedAction:
    """Parsed action with Tamarin facts and transitions."""
    facts: List[str]
    raw_action: str
    

class ExpressionParser:
    """Parses guard conditions into Tamarin-compatible facts."""
    
    def __init__(self):
        self.operators = {
            '==': '=',
            '!=': 'not equal',
            '>=': 'greater or equal',
            '<=': 'less or equal',
            '>': 'greater',
            '<': 'less',
            '&&': 'and',
            '||': 'or'
        }
    
    def parse(self, expression: str, attributes: Dict[str, Attribute]) -> ParsedGuard:
        """
        Parse a guard condition expression into Tamarin facts.
        
        Examples:
            "OnOff == TRUE" -> "State(OnOff, 'true')"
            "OnTime > 0" -> "State(OnTime, t) where t > 0"
            "feature_LT == TRUE && OnOff == FALSE" -> Multiple facts
        """
        if not expression or expression.strip().upper() == "TRUE":
            return ParsedGuard(facts=[], raw_expression=expression)
        
        facts = []
        
        # Handle compound conditions (&&, ||)
        if '&&' in expression or '||' in expression:
            # For now, split by && and process each part
            # TODO: Handle || (disjunction) with separate rules
            parts = [p.strip() for p in expression.split('&&')]
            for part in parts:
                sub_facts = self._parse_simple_condition(part, attributes)
                facts.extend(sub_facts)
        else:
            facts = self._parse_simple_condition(expression, attributes)
        
        return ParsedGuard(facts=facts, raw_expression=expression)
    
    def _parse_simple_condition(self, condition: str, attributes: Dict[str, Attribute]) -> List[str]:
        """Parse a simple condition like 'OnOff == TRUE' or 'OnTime > 0'."""
        condition = condition.strip()
        
        # Check for comparison operators
        for op in ['==', '!=', '>=', '<=', '>', '<']:
            if op in condition:
                left, right = [s.strip() for s in condition.split(op, 1)]
                return self._create_fact(left, op, right, attributes)
        
        # Boolean attribute without explicit comparison
        if condition in attributes:
            return [f"State({condition}, 'true')"]
        
        return []
    
    def _create_fact(self, left: str, op: str, right: str, attributes: Dict[str, Attribute]) -> List[str]:
        """Create Tamarin fact from comparison."""
        facts = []
        
        # Normalize boolean values
        right_normalized = right.upper()
        if right_normalized in ['TRUE', 'FALSE']:
            right = 'true' if right_normalized == 'TRUE' else 'false'
            facts.append(f"State({left}, '{right}')")
        elif right.isdigit() or right == '0':
            if op == '==':
                facts.append(f"State({left}, '{right}')")
            elif op == '>':
                # For inequality constraints, use variable binding
                # Tamarin will need to check this in guard logic
                # For now, represent as State with variable and add constraint comment
                facts.append(f"State({left}, t{left})  /* where t{left} > {right} */")
            elif op == '<':
                facts.append(f"State({left}, t{left})  /* where t{left} < {right} */")
            elif op == '>=':
                facts.append(f"State({left}, t{left})  /* where t{left} >= {right} */")
            elif op == '<=':
                facts.append(f"State({left}, t{left})  /* where t{left} <= {right} */")
            elif op == '!=':
                facts.append(f"State({left}, t{left})  /* where not(t{left} = {right}) */")
        elif right.startswith('0x'):
            # Hex value
            facts.append(f"State({left}, '{right}')")
        else:
            # Variable or attribute comparison - split into two separate facts
            facts.append(f"State({left}, v{left})")
            facts.append(f"State({right}, v{right})")
        
        return facts


class ActionParser:
    """Parses actions into Tamarin state transitions."""
    
    def parse(self, action: str, attributes: Dict[str, Attribute]) -> ParsedAction:
        """
        Parse an action string into Tamarin facts.
        
        Examples:
            "OnOff := FALSE" -> "State(OnOff, 'false')"
            "OnTime := OnTimeField" -> "State(OnTime, vOnTimeField)"
            "OnTime := OnTime - 1" -> Special handling for arithmetic
        """
        facts = []
        action = action.strip()
        
        # Handle assignment: attr := value
        if ':=' in action:
            left, right = [s.strip() for s in action.split(':=', 1)]
            facts.append(self._create_assignment_fact(left, right, attributes))
        elif action.startswith('generate_event('):
            # Event generation
            event_name = action[15:-1]  # Extract event name from generate_event(...)
            facts.append(f"Event({event_name})")
        elif action == '':
            # Empty action (stay transition)
            pass
        else:
            # Function call or complex action - represent as action fact
            facts.append(f"Action('{action}')")
        
        return ParsedAction(facts=facts, raw_action=action)
    
    def _create_assignment_fact(self, attr: str, value: str, attributes: Dict[str, Attribute]) -> str:
        """Create Tamarin fact for assignment."""
        # Normalize boolean values
        value_upper = value.upper()
        if value_upper in ['TRUE', 'FALSE']:
            value = 'true' if value_upper == 'TRUE' else 'false'
            return f"State({attr}, '{value}')"
        elif value.isdigit() or value == '0':
            return f"State({attr}, '{value}')"
        elif value.startswith('0x'):
            return f"State({attr}, '{value}')"
        elif ' - ' in value or ' + ' in value:
            # Arithmetic: OnTime := OnTime - 1
            # For now, represent as fresh variable with constraint
            return f"State({attr}, tNew{attr})"
        elif 'max(' in value or 'min(' in value:
            # max/min functions - extract from timing_requirements or treat as fresh
            return f"State({attr}, tNew{attr})"
        else:
            # Variable assignment: OnTime := OnTimeField
            return f"State({attr}, v{value})"


class TamarinGenerator:
    """Generates Tamarin protocol code from parsed FSM."""
    
    def __init__(self, fsm_data: Dict[str, Any]):
        self.fsm = fsm_data.get('fsm_model', {})
        self.cluster_name = self.fsm.get('cluster_name', 'Unknown')
        self.expression_parser = ExpressionParser()
        self.action_parser = ActionParser()
        self.attributes = self._extract_attributes()
    
    def _extract_attributes(self) -> Dict[str, Attribute]:
        """Extract all attributes from FSM."""
        attrs = {}
        for attr_name in self.fsm.get('attributes_used', []):
            attrs[attr_name] = Attribute(name=attr_name)
        return attrs
    
    def _sanitize_name(self, name: str) -> str:
        """Sanitize names for Tamarin (alphanumeric + underscore)."""
        # Replace spaces and special chars with underscores
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', name)
        # Remove leading digits
        if sanitized and sanitized[0].isdigit():
            sanitized = f"s{sanitized}"
        return sanitized
    
    def generate(self) -> str:
        """Generate complete Tamarin code."""
        code_sections = [
            self._generate_header(),
            self._generate_builtins(),
            self._generate_functions(),
            self._generate_init_rule(),
            self._generate_transition_rules(),
            self._generate_lemmas(),
            "end"  # Close the theory
        ]
        
        return '\n\n'.join(filter(None, code_sections))
    
    def _generate_header(self) -> str:
        """Generate theory header."""
        theory_name = self._sanitize_name(self.cluster_name.replace(' ', '_'))
        return f"""theory {theory_name}
begin

/*
 * Tamarin Protocol Model for {self.cluster_name}
 * Generated from FSM JSON
 * Generated: {datetime.now().isoformat()}
 * 
 * Cluster ID: {self.fsm.get('cluster_id', 'N/A')}
 * States: {len(self.fsm.get('states', []))}
 * Transitions: {len(self.fsm.get('transitions', []))}
 */"""
    
    def _generate_builtins(self) -> str:
        """Generate builtins declaration."""
        return """builtins: diffie-hellman, signing, hashing"""
    
    def _generate_functions(self) -> str:
        """Generate function declarations from definitions."""
        functions = []
        
        # Add standard functions
        functions.append("// Attribute value functions")
        functions.append("functions: true/0, false/0, null/0")
        
        # Extract custom functions from definitions if needed
        definitions = self.fsm.get('definitions', [])
        for defn in definitions:
            term = defn.get('term', '')
            if 'function' in defn.get('usage_context', '').lower():
                # Custom function - would need more sophisticated parsing
                pass
        
        return '\n'.join(functions) if functions else ""
    
    def _generate_init_rule(self) -> str:
        """Generate initialization rule."""
        initial_state = self.fsm.get('initial_state', '')
        if not initial_state:
            return ""
        
        # Find initial state definition
        initial_state_obj = None
        for state in self.fsm.get('states', []):
            if state.get('name') == initial_state:
                initial_state_obj = state
                break
        
        if not initial_state_obj:
            return ""
        
        state_name = self._sanitize_name(initial_state)
        invariants = initial_state_obj.get('invariants', [])
        
        # Parse invariants to create initial state facts
        state_facts = []
        for inv in invariants:
            parsed = self.expression_parser.parse(inv, self.attributes)
            for fact in parsed.facts:
                # Add facts directly (no extra "State()" wrapping)
                if fact:
                    state_facts.append(fact)
        
        # Add current state fact
        if not state_facts:
            state_facts = []
        
        state_facts.append(f"State(CurrentState, '{state_name}')")
        
        # Format with proper indentation and commas
        formatted_facts = ',\n    '.join(state_facts)
        
        rule = f"""rule Init:
  [ Fr(~id) ]
  -->
  [
    {formatted_facts}
  ]"""
        
        return rule
    
    def _generate_transition_rules(self) -> str:
        """Generate rules for all transitions."""
        rules = []
        
        transitions = self.fsm.get('transitions', [])
        for i, transition in enumerate(transitions):
            rule = self._generate_single_transition_rule(transition, i)
            if rule:
                rules.append(rule)
        
        return '\n\n'.join(rules)
    
    def _generate_single_transition_rule(self, transition: Dict[str, Any], index: int) -> str:
        """Generate a single transition rule."""
        from_state = self._sanitize_name(transition.get('from_state', ''))
        to_state = self._sanitize_name(transition.get('to_state', ''))
        trigger = self._sanitize_name(transition.get('trigger', ''))
        guard = transition.get('guard_condition', 'TRUE')
        actions = transition.get('actions', [])
        
        rule_name = f"{trigger}_{from_state}_to_{to_state}_{index}"
        
        # Parse guard condition
        guard_parsed = self.expression_parser.parse(guard, self.attributes)
        
        # Parse actions
        action_facts = []
        for action in actions:
            parsed_action = self.action_parser.parse(action, self.attributes)
            action_facts.extend(parsed_action.facts)
        
        # Build premise (LHS) - facts consumed
        premise = [f"State(CurrentState, '{from_state}')"]
        for fact in guard_parsed.facts:
            if fact:  # Skip empty facts
                premise.append(fact)
        
        # Build conclusion (RHS) - facts produced
        conclusion = [f"State(CurrentState, '{to_state}')"]
        for fact in action_facts:
            if fact:
                conclusion.append(fact)
        
        # Format with proper indentation and commas
        formatted_premise = ',\n    '.join(premise)
        formatted_conclusion = ',\n    '.join(conclusion)
        
        # Add action label
        action_label = f"--[ {trigger}() ]->" if trigger else "-->" 
        
        rule = f"""rule {rule_name}:
  [
    {formatted_premise}
  ]
  {action_label}
  [
    {formatted_conclusion}
  ]"""
        
        return rule
    
    def _generate_lemmas(self) -> str:
        """Generate verification lemmas."""
        lemmas = []
        
        # Basic reachability lemma
        initial_state = self._sanitize_name(self.fsm.get('initial_state', ''))
        lemmas.append(f"""lemma init_reachable:
  exists-trace
  "Ex #i. State(CurrentState, '{initial_state}') @i"
""")
        
        # Safety property: states are exclusive (only one current state at a time)
        lemmas.append("""lemma state_exclusivity:
  "All s1 s2 #i #j. State(CurrentState, s1) @i & State(CurrentState, s2) @j & #i = #j ==> s1 = s2"
""")
        
        return '\n'.join(lemmas)


class GeneralizedFSMParser:
    """Main parser class."""
    
    def __init__(self, fsm_file: Path):
        self.fsm_file = fsm_file
        self.fsm_data = None
    
    def load_fsm(self) -> Dict[str, Any]:
        """Load and validate FSM JSON."""
        with open(self.fsm_file, 'r', encoding='utf-8') as f:
            self.fsm_data = json.load(f)
        
        # Validate structure
        if 'fsm_model' not in self.fsm_data:
            raise ValueError("Invalid FSM: missing 'fsm_model' root")
        
        fsm = self.fsm_data['fsm_model']
        required_fields = ['cluster_name', 'states', 'transitions', 'initial_state']
        for field in required_fields:
            if field not in fsm:
                raise ValueError(f"Invalid FSM: missing required field '{field}'")
        
        return self.fsm_data
    
    def parse(self) -> str:
        """Parse FSM and generate Tamarin code."""
        if not self.fsm_data:
            self.load_fsm()
        
        generator = TamarinGenerator(self.fsm_data)
        return generator.generate()
    
    def save_tamarin_code(self, output_file: Path, code: str):
        """Save generated Tamarin code."""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(code)
        print(f"✓ Saved Tamarin code to: {output_file}")
    
    def validate_tamarin_code(self, tamarin_file: Path) -> Tuple[bool, str]:
        """Validate Tamarin code using tamarin-prover (if available)."""
        try:
            # Try WSL tamarin-prover
            wsl_path = tamarin_file.as_posix().replace('D:', '/mnt/d').replace('\\', '/')
            result = subprocess.run(
                ['wsl', '/home/linuxbrew/.linuxbrew/bin/tamarin-prover', '--parse', wsl_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode == 0, result.stdout + result.stderr
        except Exception as e:
            return False, f"Validation skipped: {e}"


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python generalized_fsm_parser.py input_fsm.json [output.spthy]")
        print("\nExample:")
        print("  python generalized_fsm_parser.py fsm_models_parsable/1.5_OnOff_Cluster_fsm.json tamarin_output.spthy")
        sys.exit(1)
    
    input_file = Path(sys.argv[1])
    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}")
        sys.exit(1)
    
    # Determine output file
    if len(sys.argv) > 2:
        output_file = Path(sys.argv[2])
    else:
        output_file = input_file.with_suffix('.spthy')
    
    print(f"Parsing FSM: {input_file}")
    print(f"Output: {output_file}")
    print("=" * 60)
    
    try:
        # Parse FSM
        parser = GeneralizedFSMParser(input_file)
        parser.load_fsm()
        
        print(f"✓ Loaded FSM: {parser.fsm_data['fsm_model']['cluster_name']}")
        print(f"  States: {len(parser.fsm_data['fsm_model']['states'])}")
        print(f"  Transitions: {len(parser.fsm_data['fsm_model']['transitions'])}")
        print(f"  Commands: {len(parser.fsm_data['fsm_model']['commands_handled'])}")
        
        # Generate Tamarin code
        print("\nGenerating Tamarin code...")
        tamarin_code = parser.parse()
        
        # Save
        parser.save_tamarin_code(output_file, tamarin_code)
        
        print(f"\n✓ Generated {len(tamarin_code.splitlines())} lines of Tamarin code")
        
        # Validate
        print("\nValidating Tamarin syntax...")
        valid, message = parser.validate_tamarin_code(output_file)
        if valid:
            print("✓ Tamarin syntax validation passed")
        else:
            print(f"⚠ Validation result:\n{message[:500]}")
        
        print("\n" + "=" * 60)
        print("PARSING COMPLETE")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
