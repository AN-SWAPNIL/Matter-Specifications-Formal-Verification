#!/usr/bin/env python3
"""
Generalized FSM to Tamarin Parser - Version 2.0
Parses enhanced FSM JSON (with action_facts) and generates Tamarin protocol code
for SECURITY ANALYSIS.

New Features:
- Supports action_facts_emitted in transitions
- Generates parameterized action labels
- Proper message passing (In/Out facts)
- Fresh value generation
- Security lemmas from security_properties
- Validates consistency between action_facts and security_properties

Usage:
    python generalized_fsm_parser_v2.py input_fsm.json output.spthy
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
import subprocess
import os


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class ActionFact:
    """Represents a defined action fact."""
    name: str
    params: List[str]
    description: str = ""


@dataclass
class Transition:
    """Parsed transition with all components."""
    transition_id: str
    from_state: str
    to_state: str
    trigger: str
    guard_condition: str
    input_message: Optional[Dict[str, Any]]
    output_message: Optional[Dict[str, Any]]
    action_facts_emitted: List[Dict[str, Any]]
    state_updates: List[Dict[str, Any]]
    description: str


@dataclass
class SecurityProperty:
    """Parsed security property."""
    property_id: str
    property_name: str
    property_type: str
    description: str
    formula_type: str
    formula: Dict[str, Any]
    referenced_action_facts: List[str]
    source: str


# =============================================================================
# VALIDATOR
# =============================================================================

class FSMValidator:
    """Validates FSM structure and consistency."""
    
    def __init__(self, fsm_data: Dict[str, Any]):
        self.fsm = fsm_data.get('fsm_model', {})
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate(self) -> Tuple[bool, List[str], List[str]]:
        """Run all validations. Returns (is_valid, errors, warnings)."""
        self._validate_required_fields()
        self._validate_action_facts_consistency()
        self._validate_security_properties_references()
        self._validate_transition_structure()
        
        return len(self.errors) == 0, self.errors, self.warnings
    
    def _validate_required_fields(self):
        """Check required fields exist."""
        required = ['cluster_name', 'states', 'transitions', 'initial_state']
        for field in required:
            if field not in self.fsm:
                self.errors.append(f"Missing required field: {field}")
    
    def _validate_action_facts_consistency(self):
        """Check that emitted action facts are defined."""
        defined_facts = set()
        for fact in self.fsm.get('action_facts', []):
            defined_facts.add(fact.get('name', ''))
        
        for trans in self.fsm.get('transitions', []):
            for emitted in trans.get('action_facts_emitted', []):
                fact_name = emitted.get('name', '')
                if fact_name and fact_name not in defined_facts:
                    self.warnings.append(
                        f"Transition {trans.get('transition_id', '?')} emits undefined action fact: {fact_name}"
                    )
    
    def _validate_security_properties_references(self):
        """Check security properties only reference defined action facts."""
        defined_facts = set()
        for fact in self.fsm.get('action_facts', []):
            defined_facts.add(fact.get('name', ''))
        
        for prop in self.fsm.get('security_properties', []):
            for ref in prop.get('referenced_action_facts', []):
                if ref not in defined_facts:
                    self.warnings.append(
                        f"Security property {prop.get('property_id', '?')} references undefined action fact: {ref}"
                    )
    
    def _validate_transition_structure(self):
        """Validate transition structure."""
        state_names = {s.get('name') for s in self.fsm.get('states', [])}
        
        for trans in self.fsm.get('transitions', []):
            from_state = trans.get('from_state', '')
            to_state = trans.get('to_state', '')
            
            if from_state and from_state not in state_names:
                self.errors.append(f"Transition references unknown from_state: {from_state}")
            if to_state and to_state not in state_names:
                self.errors.append(f"Transition references unknown to_state: {to_state}")


# =============================================================================
# TAMARIN CODE GENERATOR (V2)
# =============================================================================

class TamarinGeneratorV2:
    """Generates Tamarin protocol code from enhanced FSM JSON."""
    
    def __init__(self, fsm_data: Dict[str, Any]):
        self.fsm = fsm_data.get('fsm_model', {})
        self.cluster_name = self.fsm.get('cluster_name', 'Unknown')
        self.action_facts: Dict[str, ActionFact] = self._parse_action_facts()
        self.fresh_values: Set[str] = self._extract_fresh_values()
        self.input_bound: Set[str] = self._extract_input_bound()
        self.features: Set[str] = self._extract_features()
        self.attribute_names: Set[str] = self._extract_attributes()
    
    def _parse_action_facts(self) -> Dict[str, ActionFact]:
        """Parse action fact definitions."""
        facts = {}
        for fact_def in self.fsm.get('action_facts', []):
            name = fact_def.get('name', '')
            if name:
                facts[name] = ActionFact(
                    name=name,
                    params=fact_def.get('params', []),
                    description=fact_def.get('description', '')
                )
        return facts
    
    def _extract_fresh_values(self) -> Set[str]:
        """Extract fresh value names."""
        fresh = set()
        variables = self.fsm.get('variables', {})
        for fv in variables.get('fresh_values', []):
            fresh.add(fv.get('name', ''))
        return fresh
    
    def _extract_input_bound(self) -> Set[str]:
        """Extract input-bound variable names."""
        bound = set()
        variables = self.fsm.get('variables', {})
        for ib in variables.get('input_bound', []):
            bound.add(ib.get('name', ''))
        return bound
    
    def _extract_features(self) -> Set[str]:
        """Extract feature flag names from FSM."""
        features = set()
        for feat in self.fsm.get('features', []):
            features.add(feat.get('name', ''))
        return features
    
    def _extract_attributes(self) -> Set[str]:
        """Extract attribute names from state_updates across all transitions."""
        attrs = set()
        for trans in self.fsm.get('transitions', []):
            for update in trans.get('state_updates', []):
                attrs.add(update.get('attribute', ''))
        return attrs
    
    def _sanitize_name(self, name: str) -> str:
        """Sanitize names for Tamarin (alphanumeric + underscore)."""
        if not name:
            return "unknown"
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', name)
        if sanitized and sanitized[0].isdigit():
            sanitized = f"s{sanitized}"
        return sanitized
    
    def generate(self) -> str:
        """Generate complete Tamarin code."""
        sections = [
            self._generate_header(),
            self._generate_builtins(),
            self._generate_functions(),
            self._generate_restrictions(),
            self._generate_init_rule(),
            self._generate_fresh_value_rules(),
            self._generate_transition_rules(),
            self._generate_lemmas(),
            "end"
        ]
        return '\n\n'.join(filter(None, sections))
    
    def _generate_header(self) -> str:
        """Generate theory header with documentation."""
        theory_name = self._sanitize_name(self.cluster_name.replace(' ', '_'))
        
        # Count action facts used
        action_fact_count = len(self.action_facts)
        security_prop_count = len(self.fsm.get('security_properties', []))
        
        return f"""theory {theory_name}
begin

/*
 * Tamarin Protocol Security Model for {self.cluster_name}
 * Generated from Enhanced FSM JSON (v2.0)
 * Generated: {datetime.now().isoformat()}
 * 
 * Cluster ID: {self.fsm.get('cluster_id', 'N/A')}
 * Revision: {self.fsm.get('revision', 'N/A')}
 * 
 * Model Statistics:
 * - States: {len(self.fsm.get('states', []))}
 * - Transitions: {len(self.fsm.get('transitions', []))}
 * - Action Facts: {action_fact_count}
 * - Security Properties: {security_prop_count}
 * 
 * This model supports security analysis with:
 * - Parameterized action facts for precise tracing
 * - Message passing (In/Out) for protocol modeling
 * - Fresh value generation for cryptographic material
 * - Verifiable security lemmas
 */"""
    
    def _generate_builtins(self) -> str:
        """Generate builtins declaration."""
        return "builtins: hashing, symmetric-encryption"
    
    def _generate_functions(self) -> str:
        """Generate function declarations."""
        lines = [
            "// ============================================================================",
            "// Functions",
            "// ============================================================================",
            "",
            "// Boolean and null constants",
            "functions: true/0, false/0, null/0",
            "",
            "// Empty value marker",
            "functions: empty/0",
            "",
            "// Response status",
            "functions: SUCCESS/0, FAILURE/0"
        ]
        return '\n'.join(lines)
    
    def _generate_restrictions(self) -> str:
        """Generate Tamarin restrictions."""
        return """// ============================================================================
// Restrictions
// ============================================================================

// Equality check
restriction Equality:
    "All x y #i. Eq(x, y)@i ==> x = y"

// Inequality check  
restriction Inequality:
    "All x y #i. Neq(x, y)@i ==> not(x = y)"

// Once restriction for unique events
restriction Once:
    "All x #i #j. Once(x)@i & Once(x)@j ==> #i = #j"
"""
    
    def _generate_init_rule(self) -> str:
        """Generate initialization rule with feature configuration."""
        initial_state = self.fsm.get('initial_state', '')
        if not initial_state:
            return ""
        
        state_name = self._sanitize_name(initial_state)
        
        # Generate feature config facts if features exist
        config_facts = []
        if self.features:
            for feat in sorted(self.features):
                # Use abstract variable that can be instantiated as 'true' or 'false'
                config_facts.append(f"!FeatureConfig(~endpoint_id, '{feat}', feature_{feat.lower()})")
        
        config_lines = ""
        if config_facts:
            config_lines = ",\n        " + ",\n        ".join(config_facts)
        
        feature_comment = ""
        if self.features:
            feature_comment = "\n// Feature flags (feature_X) are abstract terms that represent true/false configuration"
        
        return f"""// ============================================================================
// Initialization
// ============================================================================
{feature_comment}
rule Server_Init:
    [ Fr(~endpoint_id) ]
    --[ ServerInit(~endpoint_id), Once(<'server_init', ~endpoint_id>) ]->
    [
        !Server(~endpoint_id),
        ServerState(~endpoint_id, '{state_name}'),
        RateLimitCounter(~endpoint_id, 'zero'),
        Out(~endpoint_id){config_lines}  // Endpoint is public - adversary can address server
    ]
"""
    
    def _generate_fresh_value_rules(self) -> str:
        """Generate rules for fresh value creation."""
        rules = [
            "// ============================================================================",
            "// Fresh Value Generation",
            "// ============================================================================"
        ]
        
        # Add rules for common fresh values
        rules.append("""
rule Create_TempAccountIdentifier:
    let temp_id = h(<~account, ~nonce>)
    in
    [ Fr(~account), Fr(~nonce), Fr(~setup_pin), Fr(~validity) ]
    --[ 
        TempIdCreated(temp_id, ~account),
        AccountRegistered(~account, temp_id, ~setup_pin)
    ]->
    [
        !AccountMapping(temp_id, ~account, ~setup_pin, ~validity),
        Out(temp_id)  // Attacker can observe temp_id
    ]

rule TempId_Expires:
    [ !AccountMapping(temp_id, account, setup_pin, validity) ]
    --[ TempIdExpired(temp_id) ]->
    [ !AccountMapping_Expired(temp_id, account, setup_pin) ]
""")
        
        return '\n'.join(rules)
    
    def _generate_transition_rules(self) -> str:
        """Generate rules for all transitions."""
        rules = [
            "// ============================================================================",
            "// Protocol Transitions",
            "// ============================================================================"
        ]
        
        transitions = self.fsm.get('transitions', [])
        for trans in transitions:
            rule = self._generate_single_rule(trans)
            if rule:
                rules.append(rule)
        
        return '\n\n'.join(rules)
    
    def _generate_single_rule(self, trans: Dict[str, Any]) -> str:
        """Generate a single Tamarin rule from a transition."""
        trans_id = trans.get('transition_id', 'T?')
        from_state = self._sanitize_name(trans.get('from_state', ''))
        to_state = self._sanitize_name(trans.get('to_state', ''))
        trigger = self._sanitize_name(trans.get('trigger', ''))
        description = trans.get('description', '')
        guard_condition = trans.get('guard_condition', 'TRUE')
        
        # Build rule name
        rule_name = f"{trigger}_{from_state}_to_{to_state}_{trans_id}"
        
        # Variables that are actually bound from known sources in THIS rule
        bound_variables = set()
        bound_variables.add('endpoint')  # Always bound from ServerState
        
        # Parse guard_features and guard_attributes
        guard_features = trans.get('guard_features', [])
        guard_attributes = trans.get('guard_attributes', [])
        
        # Parse input message bindings - these are bound from In fact
        input_msg = trans.get('input_message', {})
        input_bindings = input_msg.get('bindings', {}) if input_msg else {}
        for var in input_bindings.keys():
            bound_variables.add(var)
        
        # Collect ALL variables referenced in action facts
        all_action_vars = set()
        for af in trans.get('action_facts_emitted', []):
            for arg in af.get('args', []):
                if not arg.startswith("'"):  # Skip string literals
                    all_action_vars.add(arg)
        
        # Collect variables from output message values
        output_msg = trans.get('output_message', {})
        if output_msg:
            for v in output_msg.get('values', {}).values():
                if isinstance(v, str) and not v.startswith("'") and v not in ['SUCCESS', 'FAILURE', '']:
                    all_action_vars.add(v)
        
        # Identify unbound variables (in action facts but not bound from premise)
        unbound_vars = all_action_vars - bound_variables
        
        # Classify unbound variables
        # - UPPERCASE names -> treat as constants (string literals)
        # - lowercase names -> need to be bound (either from adversary input or as fresh)
        constant_vars = {v for v in unbound_vars if v.isupper() or v == 'TRUE' or v == 'FALSE'}
        
        # Variables that should be fresh (from FSM definition)
        fresh_vars_needed = {v for v in unbound_vars if v in self.fresh_values}
        
        # All remaining unbound vars need to come from adversary
        adversary_input_vars = unbound_vars - constant_vars - fresh_vars_needed
        
        # Fresh values that need Fr() in premise
        fresh_vars_in_rule = list(fresh_vars_needed)
        
        # Also include fresh values that ARE bound (from input_bindings)
        for var in bound_variables:
            if var in self.fresh_values and var not in fresh_vars_in_rule:
                fresh_vars_in_rule.append(var)
        
        # Build let bindings for fresh values in this rule
        let_bindings = []
        for var in fresh_vars_in_rule:
            let_bindings.append(f"        {var} = ~{var}")
        
        # Build premise (LHS)
        premise_facts = []
        
        # Server state
        premise_facts.append(f"ServerState(endpoint, '{from_state}')")
        
        # Feature guard facts (add !FeatureConfig facts based on guard_features)
        for guard_feat in guard_features:
            feat_name = guard_feat.get('name', '')
            feat_value = guard_feat.get('value', 'TRUE')
            if feat_name:
                # Convert TRUE/FALSE to 'true'/'false' terms
                term_value = feat_value.lower() if feat_value in ['TRUE', 'FALSE'] else feat_value
                premise_facts.append(f"!FeatureConfig(endpoint, '{feat_name}', '{term_value}')")
        
        # Attribute guard facts (TODO: implement attribute state modeling)
        # For now, we'll add as comments to show they exist
        attr_guard_comments = []
        for guard_attr in guard_attributes:
            attr_name = guard_attr.get('name', '')
            operator = guard_attr.get('operator', '==')
            value = guard_attr.get('value', '')
            if attr_name:
                attr_guard_comments.append(f"// Guard: {attr_name} {operator} {value}")
        
        # Input message (if any)
        if input_msg and input_msg.get('name'):
            msg_name = input_msg.get('name', '')
            # Construct message term from bindings
            if input_bindings:
                binding_vars = ', '.join(input_bindings.keys())
                premise_facts.append(f"In(<'{msg_name}', endpoint, {binding_vars}>)")
            else:
                premise_facts.append(f"In(<'{msg_name}', endpoint>)")
        
        # Add adversary-controlled inputs for unbound variables (except constants)
        # This allows the adversary to control these values in security analysis
        for var in sorted(adversary_input_vars):
            premise_facts.append(f"In({var})")
        
        # Fresh values needed
        for var in fresh_vars_in_rule:
            premise_facts.append(f"Fr(~{var})")
        
        # Server reference
        premise_facts.append("!Server(endpoint)")
        
        # Build action labels from action_facts_emitted
        action_labels = []
        
        # Add transition trigger as basic action label
        action_labels.append(f"{trigger}(endpoint)")
        
        # Add StateTransition action for reachability lemmas
        action_labels.append(f"StateTransition(endpoint, '{from_state}', '{to_state}')")
        
        for af in trans.get('action_facts_emitted', []):
            fact_name = af.get('name', '')
            args = af.get('args', [])
            if fact_name:
                # Process args - convert UPPERCASE constants to string literals
                processed_args = []
                for arg in args:
                    if arg in constant_vars:
                        # Convert to string constant
                        processed_args.append(f"'{arg}'")
                    else:
                        processed_args.append(arg)
                args_str = ', '.join(processed_args) if processed_args else ''
                action_labels.append(f"{fact_name}({args_str})")
        
        # Build conclusion (RHS)
        conclusion_facts = []
        
        # New server state
        conclusion_facts.append(f"ServerState(endpoint, '{to_state}')")
        
        # Preserve feature config facts in conclusion (persistent facts stay)
        for guard_feat in guard_features:
            feat_name = guard_feat.get('name', '')
            feat_value = guard_feat.get('value', 'TRUE')
            if feat_name:
                term_value = feat_value.lower() if feat_value in ['TRUE', 'FALSE'] else feat_value
                conclusion_facts.append(f"!FeatureConfig(endpoint, '{feat_name}', '{term_value}')")
        
        # Output message (if any)
        if output_msg and output_msg.get('name'):
            msg_name = output_msg.get('name', '')
            values = output_msg.get('values', {})
            if values:
                # Replace symbolic names with actual variables/constants
                processed_values = []
                for v in values.values():
                    if v == 'SUCCESS':
                        processed_values.append('SUCCESS')
                    elif v == 'FAILURE':
                        processed_values.append('FAILURE')
                    elif v == '' or v is None:
                        # Empty value - use 'empty' constant
                        processed_values.append('empty')
                    elif v in bound_variables or v in adversary_input_vars:
                        # Variable is bound from premise or adversary input
                        if v in self.fresh_values:
                            processed_values.append(v)  # Already bound via let
                        else:
                            processed_values.append(v)
                    elif v in self.fresh_values:
                        # Variable is fresh but not yet added - add it
                        fresh_vars_in_rule.append(v)
                        bound_variables.add(v)
                        processed_values.append(v)
                    elif v in constant_vars or v.isupper():
                        # Treat as constant
                        processed_values.append(f"'{v}'")
                    else:
                        # Unknown variable - use a constant string (ensure non-empty)
                        safe_v = v if v else 'empty'
                        processed_values.append(f"'{safe_v}'")
                # Filter out any remaining empty entries and join
                processed_values = [pv for pv in processed_values if pv]
                if processed_values:
                    value_list = ', '.join(processed_values)
                    conclusion_facts.append(f"Out(<'{msg_name}', {value_list}>)")
                else:
                    conclusion_facts.append(f"Out(<'{msg_name}', empty>)")
            else:
                conclusion_facts.append(f"Out(<'{msg_name}', SUCCESS>)")
        
        # Server reference (persistent)
        conclusion_facts.append("!Server(endpoint)")
        
        # Format the rule
        let_section = ""
        if let_bindings:
            let_section = "    let\n" + '\n'.join(let_bindings) + "\n    in\n"
        
        # Add guard comments at the top
        guard_comments = ""
        if guard_condition and guard_condition != "TRUE":
            guard_comments = f"// Guard: {guard_condition}\n"
        if attr_guard_comments:
            guard_comments += '\n'.join(attr_guard_comments) + "\n"
        
        premise_str = ',\n        '.join(premise_facts)
        action_str = ',\n        '.join(action_labels)
        conclusion_str = ',\n        '.join(conclusion_facts)
        
        rule = f"""// {description}
{guard_comments}rule {rule_name}:
{let_section}    [
        {premise_str}
    ]
    --[
        {action_str}
    ]->
    [
        {conclusion_str}
    ]"""
        
        return rule
    
    def _generate_lemmas(self) -> str:
        """Generate verification lemmas."""
        lemmas = [
            "// ============================================================================",
            "// Verification Lemmas",
            "// ============================================================================"
        ]
        
        # Basic reachability lemmas
        initial_state = self._sanitize_name(self.fsm.get('initial_state', ''))
        
        lemmas.append(f"""
// Basic reachability - server can initialize
lemma server_init_reachable:
    exists-trace
    "Ex endpoint #i. ServerInit(endpoint)@i"
""")
        
        # State reachability - using StateTransition action fact
        for state in self.fsm.get('states', []):
            state_name = self._sanitize_name(state.get('name', ''))
            state_desc = state.get('description', state_name)
            
            # Find transitions that lead TO this state
            to_transitions = [t for t in self.fsm.get('transitions', []) 
                            if self._sanitize_name(t.get('to_state', '')) == state_name]
            
            if to_transitions:
                # Use StateTransition action for reachability
                lemmas.append(f"""
// Reachability: {state_desc}
lemma state_{state_name}_reachable:
    exists-trace
    "Ex endpoint from_state #i. StateTransition(endpoint, from_state, '{state_name}')@i"
""")
            elif state.get('is_initial', False):
                # Initial state is reachable via ServerInit
                lemmas.append(f"""
// Reachability: {state_desc} (initial state)
lemma state_{state_name}_reachable:
    exists-trace
    "Ex endpoint #i. ServerInit(endpoint)@i"
""")
        
        # Security properties
        security_props = self.fsm.get('security_properties', [])
        if security_props:
            lemmas.append("\n// ============================================================================")
            lemmas.append("// Security Properties")
            lemmas.append("// ============================================================================\n")
            
            for prop in security_props:
                lemma = self._generate_security_lemma(prop)
                if lemma:
                    lemmas.append(lemma)
        
        return '\n'.join(lemmas)
    
    def _generate_security_lemma(self, prop: Dict[str, Any]) -> str:
        """Generate Tamarin lemma from security property."""
        prop_name = prop.get('property_name', 'unknown')
        prop_type = prop.get('property_type', 'safety')
        description = prop.get('description', '')
        formula_type = prop.get('formula_type', '')
        formula = prop.get('formula', {})
        source = prop.get('source', '')
        
        # Check if all referenced action facts are defined
        referenced = prop.get('referenced_action_facts', [])
        undefined = [ref for ref in referenced if ref not in self.action_facts]
        
        if undefined:
            # Generate as comment if references undefined facts
            return f"""/*
 * UNVERIFIABLE: {prop_name}
 * Type: {prop_type}
 * Description: {description}
 * Source: {source}
 * 
 * References undefined action facts: {', '.join(undefined)}
 * Add these to action_facts or modify security_properties.
 */
"""
        
        # Build Tamarin formula
        tamarin_formula = self._build_formula(formula, formula_type)
        
        if not tamarin_formula:
            return f"""/*
 * UNPARSEABLE: {prop_name}
 * Type: {prop_type}
 * Description: {description}
 * Could not parse formula of type: {formula_type}
 */
"""
        
        return f"""// {prop_name}: {description}
// Source: {source}
// Type: {prop_type}
lemma {prop_name}:
    "{tamarin_formula}"
"""
    
    def _build_formula(self, formula: Dict[str, Any], formula_type: str) -> str:
        """Build Tamarin formula from structured specification.
        
        IMPORTANT: Tamarin requires all variables to be 'guarded' - they must appear
        in the trigger/antecedent of the formula. Variables that only appear in the
        consequent must be existentially quantified there.
        """
        trigger = formula.get('trigger', {})
        requirement = formula.get('requirement', {})
        requirements = formula.get('requirements', [])
        consequence = formula.get('consequence', {})
        
        # Collect variables from trigger (these are guarded/universally quantified)
        trigger_vars = set()
        if trigger:
            for arg in trigger.get('args', []):
                if not arg.startswith("'"):
                    trigger_vars.add(arg)
        
        # Build trigger fact
        trigger_fact = self._build_fact_string(trigger) if trigger else ""
        
        # Universal variables are ONLY those in the trigger
        var_decl = ' '.join(sorted(trigger_vars)) if trigger_vars else 'x'
        
        if formula_type == 'requires_previous':
            # All trigger_vars #i. Trigger@i ==> Ex extra_vars #j. Requirement@j & #j < #i
            req_vars = set()
            if requirement:
                for arg in requirement.get('args', []):
                    if not arg.startswith("'"):
                        req_vars.add(arg)
            # Extra vars need existential quantification
            extra_vars = req_vars - trigger_vars
            extra_decl = ' '.join(sorted(extra_vars)) if extra_vars else ''
            req_fact = self._build_fact_string(requirement)
            if extra_decl:
                return f"All {var_decl} #i. {trigger_fact}@i ==> Ex {extra_decl} #j. {req_fact}@j & #j < #i"
            else:
                return f"All {var_decl} #i. {trigger_fact}@i ==> Ex #j. {req_fact}@j & #j < #i"
        
        elif formula_type == 'requires_simultaneous':
            # All trigger_vars #i. Trigger@i ==> Ex extra_vars. Requirement@i
            req_vars = set()
            if requirement:
                for arg in requirement.get('args', []):
                    if not arg.startswith("'"):
                        req_vars.add(arg)
            extra_vars = req_vars - trigger_vars
            extra_decl = ' '.join(sorted(extra_vars)) if extra_vars else ''
            req_fact = self._build_fact_string(requirement)
            if extra_decl:
                return f"All {var_decl} #i. {trigger_fact}@i ==> Ex {extra_decl}. {req_fact}@i"
            else:
                return f"All {var_decl} #i. {trigger_fact}@i ==> {req_fact}@i"
        
        elif formula_type == 'requires_all':
            # All trigger_vars #i. Trigger@i ==> Req1@i & Req2@i & ...
            req_parts = []
            for req in requirements:
                req_vars = set()
                for arg in req.get('args', []):
                    if not arg.startswith("'"):
                        req_vars.add(arg)
                extra_vars = req_vars - trigger_vars
                extra_decl = ' '.join(sorted(extra_vars)) if extra_vars else ''
                rf = self._build_fact_string(req)
                if extra_decl:
                    req_parts.append(f"(Ex {extra_decl}. {rf}@i)")
                else:
                    req_parts.append(f"{rf}@i")
            req_str = ' & '.join(req_parts)
            return f"All {var_decl} #i. {trigger_fact}@i ==> {req_str}"
        
        elif formula_type == 'leads_to':
            # All trigger_vars #i. Trigger@i ==> Ex extra_vars #j. Consequence@j & #i < #j
            cons_vars = set()
            if consequence:
                for arg in consequence.get('args', []):
                    if not arg.startswith("'"):
                        cons_vars.add(arg)
            extra_vars = cons_vars - trigger_vars
            extra_decl = ' '.join(sorted(extra_vars)) if extra_vars else ''
            cons_fact = self._build_fact_string(consequence)
            if extra_decl:
                return f"All {var_decl} #i. {trigger_fact}@i ==> Ex {extra_decl} #j. {cons_fact}@j & #i < #j"
            else:
                return f"All {var_decl} #i. {trigger_fact}@i ==> Ex #j. {cons_fact}@j & #i < #j"
        
        elif formula_type == 'never':
            # not(Ex vars #i. Event@i)
            event = formula.get('event', {})
            event_fact = self._build_fact_string(event)
            event_vars = set()
            for arg in event.get('args', []):
                if not arg.startswith("'"):
                    event_vars.add(arg)
            event_var_decl = ' '.join(sorted(event_vars)) if event_vars else 'x'
            return f"not(Ex {event_var_decl} #i. {event_fact}@i)"
        
        elif formula_type == 'always':
            # All trigger_vars #i. Condition@i ==> Consequence@i
            condition = formula.get('condition', {})
            cond_vars = set()
            for arg in condition.get('args', []):
                if not arg.startswith("'"):
                    cond_vars.add(arg)
            cond_var_decl = ' '.join(sorted(cond_vars)) if cond_vars else 'x'
            cond_fact = self._build_fact_string(condition)
            cons_fact = self._build_fact_string(consequence)
            # Check for extra vars in consequence
            cons_vars = set()
            if consequence:
                for arg in consequence.get('args', []):
                    if not arg.startswith("'"):
                        cons_vars.add(arg)
            extra_vars = cons_vars - cond_vars
            extra_decl = ' '.join(sorted(extra_vars)) if extra_vars else ''
            if extra_decl:
                return f"All {cond_var_decl} #i. {cond_fact}@i ==> Ex {extra_decl}. {cons_fact}@i"
            else:
                return f"All {cond_var_decl} #i. {cond_fact}@i ==> {cons_fact}@i"
        
        return ""
    
    def _build_fact_string(self, fact_spec: Dict[str, Any]) -> str:
        """Build fact string from specification."""
        if not fact_spec:
            return ""
        fact_name = fact_spec.get('fact', '')
        args = fact_spec.get('args', [])
        if not fact_name:
            return ""
        args_str = ', '.join(args) if args else ''
        return f"{fact_name}({args_str})"


# =============================================================================
# MAIN PARSER CLASS
# =============================================================================

class GeneralizedFSMParserV2:
    """Main parser class for enhanced FSM JSON."""
    
    def __init__(self, fsm_file: Path):
        self.fsm_file = fsm_file
        self.fsm_data = None
        self.is_v2_format = False
    
    def load_fsm(self) -> Dict[str, Any]:
        """Load and validate FSM JSON."""
        with open(self.fsm_file, 'r', encoding='utf-8') as f:
            self.fsm_data = json.load(f)
        
        if 'fsm_model' not in self.fsm_data:
            raise ValueError("Invalid FSM: missing 'fsm_model' root")
        
        # Detect FSM version
        fsm = self.fsm_data['fsm_model']
        metadata = fsm.get('metadata', {})
        self.is_v2_format = (
            'action_facts' in fsm or 
            metadata.get('fsm_version') == '2.0' or
            metadata.get('tamarin_compatible') == True
        )
        
        return self.fsm_data
    
    def validate(self) -> Tuple[bool, List[str], List[str]]:
        """Validate FSM structure."""
        if not self.fsm_data:
            self.load_fsm()
        
        validator = FSMValidator(self.fsm_data)
        return validator.validate()
    
    def parse(self) -> str:
        """Parse FSM and generate Tamarin code."""
        if not self.fsm_data:
            self.load_fsm()
        
        # Use V2 generator if enhanced format, otherwise fallback
        if self.is_v2_format:
            generator = TamarinGeneratorV2(self.fsm_data)
        else:
            # Fallback to legacy format handling
            print("⚠ WARNING: FSM appears to be legacy format (v1). Using v2 generator with limited support.")
            generator = TamarinGeneratorV2(self.fsm_data)
        
        return generator.generate()
    
    def save_tamarin_code(self, output_file: Path, code: str):
        """Save generated Tamarin code."""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(code)
        print(f"✓ Saved Tamarin code to: {output_file}")
    
    def validate_tamarin_code(self, tamarin_file: Path) -> Tuple[bool, str]:
        """Validate Tamarin code using tamarin-prover."""
        try:
            wsl_path = str(tamarin_file).replace('\\', '/').replace('D:', '/mnt/d')
            result = subprocess.run(
                ['wsl', '/home/linuxbrew/.linuxbrew/bin/tamarin-prover', '--parse', wsl_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode == 0, result.stdout + result.stderr
        except FileNotFoundError:
            return False, "Tamarin prover not found (WSL may not be available)"
        except Exception as e:
            return False, f"Validation error: {e}"


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Main entry point."""
    # if len(sys.argv) < 2:
    #     print("Enhanced FSM to Tamarin Parser v2.0")
    #     print("=" * 50)
    #     print("\nUsage: python generalized_fsm_parser_v2.py input_fsm.json [output.spthy]")
    #     print("\nThis parser supports the enhanced FSM format with:")
    #     print("  - action_facts: Defined security-relevant events")
    #     print("  - action_facts_emitted: Events emitted per transition")
    #     print("  - security_properties: Verifiable lemma specifications")
    #     print("\nExample:")
    #     print("  python generalized_fsm_parser_v2.py fsm_models/cluster_fsm.json output.spthy")
    #     sys.exit(1)
    print(os.listdir())
    print(os.getcwd())
    input_file = Path("D:\\Academics\\LLM Guided Matter\\FSM_Generator\\codes\\fsm_models_v2\\1.5_OnOff_Cluster_fsm.json")
    # input_file = Path("D:\\Academics\\LLM Guided Matter\\FSM_Generator\\codes\\fsm_models_v2\\6.2_Account_Login_Cluster_fsm.json")
    # if not input_file.exists():
    #     print(f"Error: Input file not found: {input_file}")
    #     sys.exit(1)
    
    output_file = Path(sys.argv[2]) if len(sys.argv) > 2 else input_file.with_suffix('.spthy')
    
    print("=" * 70)
    print("Enhanced FSM to Tamarin Parser v2.0")
    print("=" * 70)
    print(f"\nInput:  {input_file}")
    print(f"Output: {output_file}")
    
    try:
        # Load FSM
        parser = GeneralizedFSMParserV2(input_file)
        parser.load_fsm()
        
        fsm = parser.fsm_data['fsm_model']
        print(f"\n✓ Loaded FSM: {fsm.get('cluster_name', 'Unknown')}")
        print(f"  Format: {'v2.0 (enhanced)' if parser.is_v2_format else 'v1.0 (legacy)'}")
        print(f"  States: {len(fsm.get('states', []))}")
        print(f"  Transitions: {len(fsm.get('transitions', []))}")
        print(f"  Action Facts: {len(fsm.get('action_facts', []))}")
        print(f"  Security Properties: {len(fsm.get('security_properties', []))}")
        
        # Validate
        print("\nValidating FSM structure...")
        valid, errors, warnings = parser.validate()
        
        if errors:
            print(f"\n✗ Validation FAILED with {len(errors)} error(s):")
            for err in errors:
                print(f"  ERROR: {err}")
            sys.exit(1)
        
        if warnings:
            print(f"\n⚠ Validation passed with {len(warnings)} warning(s):")
            for warn in warnings:
                print(f"  WARNING: {warn}")
        else:
            print("✓ Validation passed")
        
        # Generate Tamarin code
        print("\nGenerating Tamarin code...")
        tamarin_code = parser.parse()
        parser.save_tamarin_code(output_file, tamarin_code)
        print(f"✓ Generated {len(tamarin_code.splitlines())} lines of Tamarin code")
        
        # Validate Tamarin syntax
        print("\nValidating Tamarin syntax...")
        tamarin_valid, tamarin_msg = parser.validate_tamarin_code(output_file)
        if tamarin_valid:
            print("✓ Tamarin syntax validation passed")
        else:
            print(f"⚠ Tamarin validation: {tamarin_msg[:300]}")
        
        print("\n" + "=" * 70)
        print("PARSING COMPLETE")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
