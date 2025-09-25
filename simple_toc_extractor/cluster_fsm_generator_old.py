#!/usr/bin/env python3
"""
Matter Cluster FSM Generator
Generates Finite State Machine models for each Matter cluster from detailed JSON
Following Les Modeling Framework from USENIX Security Papers
Based on cluster_detail_extractor.py structure with Gemini AI
"""

import json
import logging
import os
import sys
import signal
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime

# LangChain and Gemini imports (following existing pattern)
from langchain_google_genai import GoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

# Configuration
from config import (
    GOOGLE_API_KEY, GEMINI_MODEL, GEMINI_TEMPERATURE, GEMINI_MAX_OUTPUT_TOKENS,
    CLUSTER_CATEGORIES, EMBEDDINGS_MODEL, CHUNK_SIZE, CHUNK_OVERLAP, VECTOR_SEARCH_K,
    FSM_GENERATION_PROMPT_TEMPLATE, PROMELA_GENERATION_PROMPT_TEMPLATE
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class FSMState:
    """Represents a state in the FSM"""
    name: str
    description: str
    is_initial: bool = False
    is_final: bool = False
    attributes_monitored: List[str] = None
    
    def __post_init__(self):
        if self.attributes_monitored is None:
            self.attributes_monitored = []

@dataclass
class FSMTransition:
    """Represents a transition in the FSM"""
    from_state: str
    to_state: str
    trigger: str
    guard_condition: str = ""
    actions: List[str] = None
    
    def __post_init__(self):
        if self.actions is None:
            self.actions = []

@dataclass
class FSMModel:
    """Complete FSM model for a cluster"""
    cluster_name: str
    cluster_id: str
    category: str
    states: List[FSMState]
    transitions: List[FSMTransition]
    initial_state: str
    attributes_used: List[str]
    commands_handled: List[str]
    events_generated: List[str]
    invariants: List[str]
    
    def __post_init__(self):
        if self.attributes_used is None:
            self.attributes_used = []
        if self.commands_handled is None:
            self.commands_handled = []
        if self.events_generated is None:
            self.events_generated = []
        if self.invariants is None:
            self.invariants = []

class MatterBehavioralPatternRecognizer:
    """Recognizes and fixes common Matter behavioral patterns to improve FSM accuracy for ALL cluster types"""
    
    @staticmethod
    def fix_on_off_cluster_patterns(fsm_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fix specific On/Off cluster behavioral patterns based on Matter spec"""
        if not isinstance(fsm_data, dict) or 'fsm_model' not in fsm_data:
            return fsm_data
            
        fsm_model = fsm_data['fsm_model']
        
        # Fix DelayedOff state semantics - should have OnOff=FALSE
        for state in fsm_model.get('states', []):
            if state.get('name') == 'DelayedOff':
                # DelayedOff means device is OFF with countdown timer
                state['description'] = "Device is off but OffWaitTime timer is counting down. OnOff attribute is FALSE."
                state['invariants'] = ["OnOff == FALSE", "OffWaitTime > 0"]
        
        # Fix TimedOn expiry transition - should go directly to Off, not DelayedOff
        for transition in fsm_model.get('transitions', []):
            if (transition.get('from_state') == 'TimedOn' and 
                transition.get('trigger') == 'OnTime timer expires'):
                transition['to_state'] = 'Off'
                transition['actions'] = ["OffWaitTime = 0", "OnOff = FALSE"]
        
        # Remove non-existent OFFONLY feature guards - only LT and DF exist
        for transition in fsm_model.get('transitions', []):
            guard = transition.get('guard_condition', '')
            if 'OFFONLY' in guard:
                transition['guard_condition'] = 'true'
        
        # Fix GlobalSceneControl invariants in On state - not always TRUE
        for state in fsm_model.get('states', []):
            if state.get('name') == 'On':
                invariants = state.get('invariants', [])
                state['invariants'] = [inv for inv in invariants if 'GlobalSceneControl == TRUE' not in inv]
        
        # Remove DefaultResponse (Interaction Model, not Application Cluster)
        for transition in fsm_model.get('transitions', []):
            if transition.get('response_command') == 'DefaultResponse':
                transition['response_command'] = None
        
        return fsm_data
    
    @staticmethod
    def fix_level_control_patterns(fsm_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fix Level Control cluster patterns"""
        if not isinstance(fsm_data, dict) or 'fsm_model' not in fsm_data:
            return fsm_data
            
        fsm_model = fsm_data['fsm_model']
        
        # Level Control specific states: Off (CurrentLevel=null), On (Level>0), Moving
        for state in fsm_model.get('states', []):
            if state.get('name') == 'Off':
                state['invariants'] = ["CurrentLevel == null", "OnOff == FALSE"]
            elif state.get('name') == 'Moving':
                state['description'] = "Level transition in progress with rate control"
                state['invariants'] = ["transition_active == true", "rate > 0"]
        
        # Fix MoveToLevel behaviors with OnOff coupling
        for transition in fsm_model.get('transitions', []):
            if 'MoveToLevel' in transition.get('trigger', ''):
                if 'WithOnOff' in transition.get('trigger', ''):
                    transition['actions'].append("OnOff = (TargetLevel > 0)")
        
        return fsm_data
    
    @staticmethod
    def fix_mode_based_patterns(fsm_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fix Mode-based cluster patterns (Mode Select, operational modes, etc.)"""
        if not isinstance(fsm_data, dict) or 'fsm_model' not in fsm_data:
            return fsm_data
            
        fsm_model = fsm_data['fsm_model']
        
        # Mode clusters should have states corresponding to each mode value
        # Fix startup behavior: should resume previous mode vs default mode
        for transition in fsm_model.get('transitions', []):
            if 'ChangeToMode' in transition.get('trigger', ''):
                # Add mode validation
                transition['guard_condition'] = 'requested_mode in supported_modes'
                if 'mode validation' not in transition.get('actions', []):
                    transition['actions'].append('validate mode is supported')
        
        return fsm_data
    
    @staticmethod
    def fix_measurement_cluster_patterns(fsm_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fix measurement/sensing cluster patterns"""
        if not isinstance(fsm_data, dict) or 'fsm_model' not in fsm_data:
            return fsm_data
            
        fsm_model = fsm_data['fsm_model']
        
        # Measurement clusters: Calibrating, Measuring, Fault states
        for state in fsm_model.get('states', []):
            if state.get('name') == 'Calibrating':
                state['description'] = "Sensor calibration in progress"
                state['invariants'] = ["calibration_active == true", "measurement_invalid == true"]
            elif state.get('name') == 'Fault':
                state['description'] = "Sensor fault detected, measurements invalid"
                state['invariants'] = ["fault_detected == true", "measurement_valid == false"]
        
        return fsm_data
    
    @staticmethod
    def fix_operational_state_patterns(fsm_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fix Operational State cluster patterns"""
        if not isinstance(fsm_data, dict) or 'fsm_model' not in fsm_data:
            return fsm_data
            
        fsm_model = fsm_data['fsm_model']
        
        # Operational states: Stopped, Running, Paused, Error
        standard_operational_states = ['Stopped', 'Running', 'Paused', 'Error']
        
        for state in fsm_model.get('states', []):
            if state.get('name') in standard_operational_states:
                if state.get('name') == 'Stopped':
                    state['invariants'] = ["OperationalState == 0x00", "operation_active == false"]
                elif state.get('name') == 'Running':
                    state['invariants'] = ["OperationalState == 0x01", "operation_active == true"]
                elif state.get('name') == 'Paused':
                    state['invariants'] = ["OperationalState == 0x02", "operation_suspended == true"]
                elif state.get('name') == 'Error':
                    state['invariants'] = ["OperationalState == 0x03", "error_condition == true"]
        
        return fsm_data
    
    @staticmethod
    def fix_identify_cluster_patterns(fsm_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fix Identify cluster patterns"""
        if not isinstance(fsm_data, dict) or 'fsm_model' not in fsm_data:
            return fsm_data
            
        fsm_model = fsm_data['fsm_model']
        
        # Identify cluster: timer-based with 1-second resolution
        for transition in fsm_model.get('transitions', []):
            if 'IdentifyTime' in transition.get('trigger', '') and 'timer' in transition.get('trigger', ''):
                # Identify timer decrements every 1 second (not 1/10 second like OnTime)
                transition['actions'] = ["IdentifyTime = IdentifyTime - 1", "update identification display"]
                
        return fsm_data
    
    @staticmethod
    def fix_door_lock_patterns(fsm_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fix Door Lock cluster patterns"""
        if not isinstance(fsm_data, dict) or 'fsm_model' not in fsm_data:
            return fsm_data
            
        fsm_model = fsm_data['fsm_model']
        
        # Door Lock states: Locked, Unlocked, Unlatched, etc.
        for state in fsm_model.get('states', []):
            if state.get('name') == 'Locked':
                state['invariants'] = ["LockState == 0x01", "door_locked == true"]
            elif state.get('name') == 'Unlocked':
                state['invariants'] = ["LockState == 0x02", "door_locked == false"]
        
        # Fix credential-based access
        for transition in fsm_model.get('transitions', []):
            if 'Lock' in transition.get('trigger', '') or 'Unlock' in transition.get('trigger', ''):
                if 'credential validation' not in transition.get('actions', []):
                    transition['actions'].append('validate credentials')
        
        return fsm_data
    
    @staticmethod
    def fix_thermostat_patterns(fsm_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fix Thermostat cluster patterns"""
        if not isinstance(fsm_data, dict) or 'fsm_model' not in fsm_data:
            return fsm_data
            
        fsm_model = fsm_data['fsm_model']
        
        # Thermostat modes: Off, Auto, Cool, Heat, etc.
        for state in fsm_model.get('states', []):
            if state.get('name') == 'Off':
                state['invariants'] = ["SystemMode == 0x00", "heating_active == false", "cooling_active == false"]
            elif state.get('name') == 'Heat':
                state['invariants'] = ["SystemMode == 0x04", "heating_available == true"]
            elif state.get('name') == 'Cool':
                state['invariants'] = ["SystemMode == 0x03", "cooling_available == true"]
        
        return fsm_data
    
    @staticmethod
    def fix_timer_based_patterns(fsm_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fix timer-based behavioral patterns common across clusters"""
        if not isinstance(fsm_data, dict) or 'fsm_model' not in fsm_data:
            return fsm_data
            
        fsm_model = fsm_data['fsm_model']
        
        # Ensure timer attributes have proper resolution and behavior
        timer_attributes = {
            'OnTime': '1/10 second resolution, auto-decrements to 0',
            'OffWaitTime': '1/10 second resolution, auto-decrements to 0', 
            'IdentifyTime': '1 second resolution, auto-decrements to 0',
            'DelayTime': '1/10 second resolution, for delayed operations',
            'TransitionTime': '1/10 second resolution, for gradual changes'
        }
        
        for transition in fsm_model.get('transitions', []):
            actions = transition.get('actions', [])
            trigger = transition.get('trigger', '')
            
            # Fix timer expiry semantics
            for timer_attr in timer_attributes:
                if f'{timer_attr} timer expires' in trigger or f'{timer_attr} == 0' in trigger:
                    transition['guard_condition'] = f"{timer_attr} == 0"
                    # Ensure transition happens when timer reaches 0
                    if f"stop {timer_attr.lower()}" not in actions:
                        actions.append(f"stop {timer_attr.lower()}")
                
                # Fix timer initialization
                if f'set {timer_attr}' in str(actions).lower():
                    for i, action in enumerate(actions):
                        if timer_attr in action and '=' in action:
                            # Ensure timer values are properly validated
                            if 'validate' not in action:
                                actions[i] = f"validate and {action}"
        
        return fsm_data
    
    @staticmethod
    def fix_conditional_command_patterns(fsm_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fix conditional command behaviors with proper if/then/else branches"""
        if not isinstance(fsm_data, dict) or 'fsm_model' not in fsm_data:
            return fsm_data
            
        fsm_model = fsm_data['fsm_model']
        
        # Look for commands with conditional behaviors and split into multiple transitions
        commands_with_conditions = ['OffWithEffect', 'OnWithRecallGlobalScene', 'OnWithTimedOff']
        
        new_transitions = []
        transitions_to_remove = []
        
        for transition in fsm_model.get('transitions', []):
            trigger = transition.get('trigger', '')
            
            if trigger == 'OffWithEffect':
                # Split into conditional branches based on GlobalSceneControl
                transitions_to_remove.append(transition)
                
                # Branch 1: GlobalSceneControl == TRUE
                new_transitions.append({
                    "from_state": transition['from_state'],
                    "to_state": "Off",
                    "trigger": "OffWithEffect",
                    "guard_condition": "GlobalSceneControl == TRUE",
                    "actions": [
                        "store global scene",
                        "GlobalSceneControl = FALSE", 
                        "OnOff = FALSE",
                        "OnTime = 0"
                    ],
                    "response_command": None
                })
                
                # Branch 2: GlobalSceneControl == FALSE
                new_transitions.append({
                    "from_state": transition['from_state'],
                    "to_state": "Off", 
                    "trigger": "OffWithEffect",
                    "guard_condition": "GlobalSceneControl == FALSE",
                    "actions": ["OnOff = FALSE"],
                    "response_command": None
                })
            
            elif trigger == 'OnWithRecallGlobalScene':
                # Split based on GlobalSceneControl
                transitions_to_remove.append(transition)
                
                # Branch 1: GlobalSceneControl == TRUE (discard command)
                new_transitions.append({
                    "from_state": transition['from_state'],
                    "to_state": transition['from_state'],  # Stay in same state
                    "trigger": "OnWithRecallGlobalScene",
                    "guard_condition": "GlobalSceneControl == TRUE",
                    "actions": ["discard command"],
                    "response_command": None
                })
                
                # Branch 2: GlobalSceneControl == FALSE (recall scene)
                new_transitions.append({
                    "from_state": transition['from_state'],
                    "to_state": "On",
                    "trigger": "OnWithRecallGlobalScene", 
                    "guard_condition": "GlobalSceneControl == FALSE",
                    "actions": [
                        "Scenes cluster recalls global scene",
                        "GlobalSceneControl = TRUE",
                        "if (OnTime == 0 && timers supported) OffWaitTime = 0"
                    ],
                    "response_command": None
                })
        
        # Remove old transitions and add new ones
        for transition in transitions_to_remove:
            fsm_model['transitions'].remove(transition)
        
        fsm_model['transitions'].extend(new_transitions)
        
        return fsm_data
    
    @staticmethod
    def apply_all_pattern_fixes(fsm_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply all behavioral pattern fixes to improve accuracy for ALL cluster types"""
        # Apply universal patterns first
        fsm_data = MatterBehavioralPatternRecognizer.fix_timer_based_patterns(fsm_data)
        fsm_data = MatterBehavioralPatternRecognizer.fix_conditional_command_patterns(fsm_data)
        
        # Extract cluster type from multiple possible sources
        cluster_name = ''
        if 'fsm_model' in fsm_data:
            cluster_name = fsm_data['fsm_model'].get('cluster_name', '').lower()
        if not cluster_name and 'cluster_info' in fsm_data:
            cluster_name = fsm_data['cluster_info'].get('name', '').lower()
        if not cluster_name and 'cluster_name' in fsm_data:
            cluster_name = fsm_data['cluster_name'].lower()
        
        # Apply cluster-specific fixes based on identified type
        if 'on/off' in cluster_name or 'onoff' in cluster_name:
            fsm_data = MatterBehavioralPatternRecognizer.fix_on_off_cluster_patterns(fsm_data)
        
        if 'level' in cluster_name and 'control' in cluster_name:
            fsm_data = MatterBehavioralPatternRecognizer.fix_level_control_patterns(fsm_data)
        
        if 'mode' in cluster_name or 'operational' in cluster_name:
            fsm_data = MatterBehavioralPatternRecognizer.fix_mode_based_patterns(fsm_data)
            fsm_data = MatterBehavioralPatternRecognizer.fix_operational_state_patterns(fsm_data)
        
        if any(keyword in cluster_name for keyword in ['temperature', 'pressure', 'humidity', 'illuminance', 'measurement']):
            fsm_data = MatterBehavioralPatternRecognizer.fix_measurement_cluster_patterns(fsm_data)
        
        if 'identify' in cluster_name:
            fsm_data = MatterBehavioralPatternRecognizer.fix_identify_cluster_patterns(fsm_data)
        
        if 'door' in cluster_name and 'lock' in cluster_name:
            fsm_data = MatterBehavioralPatternRecognizer.fix_door_lock_patterns(fsm_data)
        
        if 'thermostat' in cluster_name:
            fsm_data = MatterBehavioralPatternRecognizer.fix_thermostat_patterns(fsm_data)
        
        return fsm_data

class FSMValidationAndCorrection:
    """Validates and corrects FSM models to ensure specification compliance"""
    
    @staticmethod
    def validate_fsm_structure(fsm_data: Dict[str, Any]) -> List[str]:
        """Validate FSM structure and return list of errors"""
        errors = []
        
        if not isinstance(fsm_data, dict) or 'fsm_model' not in fsm_data:
            errors.append("Missing fsm_model key in FSM data")
            return errors
            
        fsm_model = fsm_data['fsm_model']
        
        # Check required fields
        required_fields = ['cluster_name', 'cluster_id', 'states', 'transitions', 'initial_state']
        for field in required_fields:
            if field not in fsm_model:
                errors.append(f"Missing required field: {field}")
        
        # Validate states
        states = fsm_model.get('states', [])
        if not states:
            errors.append("No states defined")
        else:
            state_names = [s.get('name') for s in states]
            initial_states = [s for s in states if s.get('is_initial', False)]
            
            if len(initial_states) != 1:
                errors.append(f"Must have exactly one initial state, found {len(initial_states)}")
            
            if fsm_model.get('initial_state') not in state_names:
                errors.append(f"Initial state '{fsm_model.get('initial_state')}' not found in states")
        
        # Validate transitions
        transitions = fsm_model.get('transitions', [])
        for i, transition in enumerate(transitions):
            from_state = transition.get('from_state')
            to_state = transition.get('to_state')
            
            if from_state not in state_names:
                errors.append(f"Transition {i}: from_state '{from_state}' not found in states")
            if to_state not in state_names:
                errors.append(f"Transition {i}: to_state '{to_state}' not found in states")
            
            if not transition.get('trigger'):
                errors.append(f"Transition {i}: missing trigger")
        
        return errors
    
    @staticmethod
    def correct_common_fsm_errors(fsm_data: Dict[str, Any]) -> Dict[str, Any]:
        """Automatically correct common FSM modeling errors"""
        if not isinstance(fsm_data, dict) or 'fsm_model' not in fsm_data:
            return fsm_data
            
        fsm_model = fsm_data['fsm_model']
        
        # Fix missing guard conditions
        for transition in fsm_model.get('transitions', []):
            guard_condition = transition.get('guard_condition')
            # Handle missing, empty, or invalid guard conditions
            if (not guard_condition or 
                (isinstance(guard_condition, str) and guard_condition.strip() == '') or
                (isinstance(guard_condition, bool) and guard_condition is True)):
                transition['guard_condition'] = 'true'
            elif isinstance(guard_condition, bool) and guard_condition is False:
                transition['guard_condition'] = 'false'
        
        # Fix missing actions lists
        for transition in fsm_model.get('transitions', []):
            if not transition.get('actions'):
                transition['actions'] = []
        
        # Fix missing attributes_monitored lists
        for state in fsm_model.get('states', []):
            if not state.get('attributes_monitored'):
                state['attributes_monitored'] = []
            if not state.get('invariants'):
                state['invariants'] = []
        
        # Ensure lists instead of None values
        list_fields = ['attributes_used', 'commands_handled', 'events_generated']
        for field in list_fields:
            if fsm_model.get(field) is None:
                fsm_model[field] = []
        
        return fsm_data
    
    @staticmethod
    def validate_matter_semantics(fsm_data: Dict[str, Any]) -> List[str]:
        """Validate Matter-specific semantic correctness for ALL cluster types"""
        errors = []
        
        if not isinstance(fsm_data, dict) or 'fsm_model' not in fsm_data:
            return errors
            
        fsm_model = fsm_data['fsm_model']
        cluster_name = fsm_model.get('cluster_name', '').lower()
        
        # Validate On/Off cluster semantics
        if 'on/off' in cluster_name or 'onoff' in cluster_name:
            errors.extend(FSMValidationAndCorrection._validate_onoff_semantics(fsm_model))
        
        # Validate Level Control cluster semantics  
        if 'level' in cluster_name and 'control' in cluster_name:
            errors.extend(FSMValidationAndCorrection._validate_level_control_semantics(fsm_model))
        
        # Validate Mode-based cluster semantics
        if 'mode' in cluster_name or 'operational' in cluster_name:
            errors.extend(FSMValidationAndCorrection._validate_mode_cluster_semantics(fsm_model))
        
        # Validate measurement cluster semantics
        if any(keyword in cluster_name for keyword in ['temperature', 'pressure', 'humidity', 'illuminance', 'measurement']):
            errors.extend(FSMValidationAndCorrection._validate_measurement_semantics(fsm_model))
        
        # Validate Door Lock cluster semantics
        if 'door' in cluster_name and 'lock' in cluster_name:
            errors.extend(FSMValidationAndCorrection._validate_door_lock_semantics(fsm_model))
        
        # Validate Thermostat cluster semantics
        if 'thermostat' in cluster_name:
            errors.extend(FSMValidationAndCorrection._validate_thermostat_semantics(fsm_model))
        
        # Validate Identify cluster semantics
        if 'identify' in cluster_name:
            errors.extend(FSMValidationAndCorrection._validate_identify_semantics(fsm_model))
        
        return errors
    
    @staticmethod
    def _validate_onoff_semantics(fsm_model: Dict[str, Any]) -> List[str]:
        """Validate On/Off cluster specific semantics"""
        errors = []
        
        # Check DelayedOff state semantics
        for state in fsm_model.get('states', []):
            if state.get('name') == 'DelayedOff':
                invariants = state.get('invariants', [])
                if any('OnOff == TRUE' in inv for inv in invariants):
                    errors.append("DelayedOff state should have OnOff == FALSE (device is off during countdown)")
        
        # Check for non-existent OFFONLY feature
        for transition in fsm_model.get('transitions', []):
            guard = transition.get('guard_condition', '')
            if 'OFFONLY' in guard:
                errors.append("OFFONLY feature does not exist in On/Off cluster (only LT and DF features)")
        
        return errors
    
    @staticmethod  
    def _validate_level_control_semantics(fsm_model: Dict[str, Any]) -> List[str]:
        """Validate Level Control cluster semantics"""
        errors = []
        
        # Check Off state should have CurrentLevel == null
        for state in fsm_model.get('states', []):
            if state.get('name') == 'Off':
                invariants = state.get('invariants', [])
                if not any('CurrentLevel == null' in inv for inv in invariants):
                    errors.append("Off state in Level Control should have CurrentLevel == null")
        
        return errors
    
    @staticmethod
    def _validate_mode_cluster_semantics(fsm_model: Dict[str, Any]) -> List[str]:
        """Validate Mode-based cluster semantics"""
        errors = []
        
        # Check that mode values are validated
        for transition in fsm_model.get('transitions', []):
            if 'ChangeToMode' in transition.get('trigger', ''):
                guard = transition.get('guard_condition', '')
                if 'supported_modes' not in guard and 'validate' not in guard:
                    errors.append("ChangeToMode should validate mode is supported")
        
        return errors
    
    @staticmethod
    def _validate_measurement_semantics(fsm_model: Dict[str, Any]) -> List[str]:
        """Validate measurement cluster semantics"""
        errors = []
        
        # Check Fault state semantics
        for state in fsm_model.get('states', []):
            if state.get('name') == 'Fault':
                invariants = state.get('invariants', [])
                if not any('measurement_valid == false' in inv for inv in invariants):
                    errors.append("Fault state should have measurement_valid == false")
        
        return errors
    
    @staticmethod
    def _validate_door_lock_semantics(fsm_model: Dict[str, Any]) -> List[str]:
        """Validate Door Lock cluster semantics"""
        errors = []
        
        # Check credential validation
        for transition in fsm_model.get('transitions', []):
            if 'Lock' in transition.get('trigger', '') or 'Unlock' in transition.get('trigger', ''):
                actions = transition.get('actions', [])
                if not any('credential' in action for action in actions):
                    errors.append("Lock/Unlock operations should validate credentials")
        
        return errors
    
    @staticmethod
    def _validate_thermostat_semantics(fsm_model: Dict[str, Any]) -> List[str]:
        """Validate Thermostat cluster semantics"""
        errors = []
        
        # Check that heating/cooling states validate capability
        for state in fsm_model.get('states', []):
            if state.get('name') == 'Heat':
                invariants = state.get('invariants', [])
                if not any('heating_available' in inv for inv in invariants):
                    errors.append("Heat state should check heating_available")
        
        return errors
    
    @staticmethod
    def _validate_identify_semantics(fsm_model: Dict[str, Any]) -> List[str]:
        """Validate Identify cluster semantics"""
        errors = []
        
        # Check IdentifyTime timer resolution (1 second, not 1/10 second)
        for transition in fsm_model.get('transitions', []):
            actions = transition.get('actions', [])
            for action in actions:
                if 'IdentifyTime' in action and '0.1' in action:
                    errors.append("IdentifyTime uses 1-second resolution, not 1/10 second")
        
        return errors
    
    @staticmethod
    def apply_validation_and_correction(fsm_data: Dict[str, Any]) -> tuple[Dict[str, Any], List[str]]:
        """Apply all validation and correction steps"""
        # First, correct common structural errors
        fsm_data = FSMValidationAndCorrection.correct_common_fsm_errors(fsm_data)
        
        # Then validate structure
        structural_errors = FSMValidationAndCorrection.validate_fsm_structure(fsm_data)
        
        # Finally validate Matter semantics
        semantic_errors = FSMValidationAndCorrection.validate_matter_semantics(fsm_data)
        
        all_errors = structural_errors + semantic_errors
        return fsm_data, all_errors

class ClusterFSMGenerator:
    """Generates FSM models for Matter clusters using Gemini AI"""
    
    def __init__(self, detailed_json_path: str, output_dir: str = "fsm_results"):
        """
        Initialize the FSM generator
        
        Args:
            detailed_json_path: Path to the matter_clusters_detailed.json file
            output_dir: Directory to save FSM results
        """
        self.detailed_json_path = detailed_json_path
        self.output_dir = output_dir
        self.clusters_data = None
        self.llm = None
        self.embeddings = None
        self.interruption_handler_set = False
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialize components
        self._load_clusters_data()
        self._init_llm()
        self._setup_interruption_handler()
    
    def _setup_interruption_handler(self):
        """Setup signal handlers for graceful interruption"""
        if not self.interruption_handler_set:
            def signal_handler(signum, frame):
                logger.warning(f"Received signal {signum}. Exiting gracefully...")
                sys.exit(0)
            
            signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
            signal.signal(signal.SIGTERM, signal_handler)  # Termination
            self.interruption_handler_set = True
            logger.info("Interruption handlers set up")
    
    def _init_llm(self):
        """Initialize the language model and embeddings"""
        try:
            self.llm = GoogleGenerativeAI(
                model=GEMINI_MODEL,
                google_api_key=GOOGLE_API_KEY,
                temperature=GEMINI_TEMPERATURE,
                max_output_tokens=GEMINI_MAX_OUTPUT_TOKENS
            )
            self.embeddings = GoogleGenerativeAIEmbeddings(
                model="models/embedding-001",
                google_api_key=GOOGLE_API_KEY
            )
            logger.info("Initialized Gemini LLM and embeddings")
        except Exception as e:
            logger.error(f"Error initializing LLM: {e}")
            raise
    
    def _load_clusters_data(self):
        """Load clusters data from detailed JSON file"""
        try:
            with open(self.detailed_json_path, 'r', encoding='utf-8') as f:
                self.clusters_data = json.load(f)
            cluster_count = len(self.clusters_data.get('clusters', []))
            logger.info(f"Loaded {cluster_count} detailed clusters")
        except Exception as e:
            logger.error(f"Error loading clusters data: {e}")
            raise
    
    def get_fsm_generation_prompt(self, cluster_info: Dict[str, Any]) -> str:
        """
        Generate FSM extraction prompt for a specific cluster
        
        Args:
            cluster_info: Detailed cluster information
            
        Returns:
            Formatted prompt string
        """
        # Convert cluster_info to a nicely formatted JSON string
        cluster_info_str = json.dumps(cluster_info, indent=2, ensure_ascii=False)
        
        # Use config template with full cluster information
        return FSM_GENERATION_PROMPT_TEMPLATE.format(
            cluster_info=cluster_info_str
        )
    
    def generate_cluster_fsm(self, cluster_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate FSM model for a single cluster
        
        Args:
            cluster_info: Detailed cluster information
            
        Returns:
            Generated FSM model as dictionary
        """
        cluster_data = cluster_info.get('cluster_info', {})
        cluster_name = cluster_data.get('cluster_name', 'Unknown')
        
        logger.info(f"Generating FSM for cluster: {cluster_name}")
        
        try:
            # Generate prompt
            prompt = self.get_fsm_generation_prompt(cluster_info)
            
            # Get LLM response
            response = self.llm.invoke(prompt)
            
            # Parse JSON response
            try:
                # Clean response by removing code block markers if present
                clean_response = response.strip()
                logger.debug(f"Original response length for {cluster_name}: {len(response)} characters")
                
                # Handle multiple code block formats
                if clean_response.startswith('```json'):
                    clean_response = clean_response[7:]  # Remove ```json
                    logger.debug(f"Removed ```json prefix")
                elif clean_response.startswith('```'):
                    clean_response = clean_response[3:]  # Remove ```
                    logger.debug(f"Removed ``` prefix")
                
                if clean_response.endswith('```'):
                    clean_response = clean_response[:-3]  # Remove ```
                    logger.debug(f"Removed ``` suffix")
                
                clean_response = clean_response.strip()
                logger.debug(f"Cleaned response length for {cluster_name}: {len(clean_response)} characters")
                
                # Log response length for debugging
                logger.debug(f"Final response length for {cluster_name}: {len(clean_response)} characters")
                
                # Additional validation - check if JSON starts correctly
                if not clean_response.startswith('{'):
                    logger.error(f"Response does not start with '{{' for {cluster_name}")
                    logger.error(f"First 200 chars: {repr(clean_response[:200])}")
                    logger.error(f"Original response first 200 chars: {repr(response[:200])}")
                    return self._create_fallback_fsm(cluster_info)
                
                # Try to find complete JSON if response was truncated
                if not clean_response.endswith('}'):
                    logger.warning(f"Response doesn't end with '}}' for {cluster_name}")
                    logger.debug(f"Last 200 chars: {repr(clean_response[-200:])}")
                    
                    # Look for the last complete JSON object
                    brace_count = 0
                    last_complete_pos = -1
                    
                    for i, char in enumerate(clean_response):
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                last_complete_pos = i
                    
                    if last_complete_pos > 0:
                        clean_response = clean_response[:last_complete_pos + 1]
                        logger.warning(f"Response was truncated, using partial JSON for {cluster_name}")
                        logger.debug(f"Truncated to position {last_complete_pos}, new length: {len(clean_response)}")
                    else:
                        logger.error(f"Could not find complete JSON for {cluster_name}")
                        logger.error(f"Brace analysis failed, last complete position: {last_complete_pos}")
                        return self._create_fallback_fsm(cluster_info)
                
                logger.debug(f"About to parse JSON for {cluster_name}, final length: {len(clean_response)}")
                fsm_model = json.loads(clean_response)
                
                # Apply behavioral pattern fixes to improve accuracy
                fsm_model = MatterBehavioralPatternRecognizer.apply_all_pattern_fixes(fsm_model)
                
                # Apply validation and error correction
                fsm_model, validation_errors = FSMValidationAndCorrection.apply_validation_and_correction(fsm_model)
                
                if validation_errors:
                    logger.warning(f"FSM validation errors for {cluster_name}: {validation_errors}")
                    # Add validation errors to metadata for debugging
                    if 'fsm_model' in fsm_model:
                        fsm_model['fsm_model']['validation_errors'] = validation_errors
                
                # Add generation metadata
                if 'fsm_model' in fsm_model:
                    fsm_model['fsm_model']['generation_timestamp'] = datetime.now().isoformat()
                    fsm_model['fsm_model']['source_metadata'] = {
                        'extraction_method': cluster_info.get('metadata', {}).get('extraction_method', 'Unknown'),
                        'source_pages': cluster_info.get('metadata', {}).get('source_pages', 'Unknown'),
                        'section_number': cluster_info.get('metadata', {}).get('section_number', 'Unknown')
                    }
                
                logger.info(f"Successfully generated FSM for {cluster_name}")
                return fsm_model
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error for {cluster_name}:")
                logger.error(f"  Error: {str(e)}")
                logger.error(f"  Error position: line {e.lineno}, column {e.colno}")
                logger.error(f"  Error msg: {e.msg}")
                logger.error(f"  Response length: {len(clean_response)} characters")
                logger.error(f"  First 500 chars: {clean_response[:500]}")
                logger.error(f"  Last 500 chars: {clean_response[-500:]}")
                
                # Try to find and extract the problematic area around the error
                try:
                    lines = clean_response.split('\n')
                    error_line = e.lineno - 1  # Convert to 0-based index
                    start_line = max(0, error_line - 3)
                    end_line = min(len(lines), error_line + 4)
                    
                    logger.error(f"  Context around error (lines {start_line + 1}-{end_line}):")
                    for i in range(start_line, end_line):
                        if i < len(lines):
                            marker = " --> " if i == error_line else "     "
                            logger.error(f"  {marker}Line {i + 1}: {repr(lines[i])}")
                except Exception as context_error:
                    logger.error(f"  Could not extract error context: {context_error}")
                
                # Try one more time with aggressive JSON repair
                try:
                    # Attempt to fix common JSON issues
                    repaired_response = self._attempt_json_repair(clean_response)
                    if repaired_response != clean_response:
                        logger.info(f"Attempting JSON repair for {cluster_name}")
                        fsm_model = json.loads(repaired_response)
                        logger.info(f"Successfully repaired and parsed JSON for {cluster_name}")
                        
                        # Apply behavioral pattern fixes to improve accuracy
                        fsm_model = MatterBehavioralPatternRecognizer.apply_all_pattern_fixes(fsm_model)
                        
                        # Apply validation and error correction
                        fsm_model, validation_errors = FSMValidationAndCorrection.apply_validation_and_correction(fsm_model)
                        
                        if validation_errors:
                            logger.warning(f"FSM validation errors for {cluster_name}: {validation_errors}")
                            # Add validation errors to metadata for debugging
                            if 'fsm_model' in fsm_model:
                                fsm_model['fsm_model']['validation_errors'] = validation_errors
                        
                        # Add generation metadata
                        if 'fsm_model' in fsm_model:
                            fsm_model['fsm_model']['generation_timestamp'] = datetime.now().isoformat()
                            fsm_model['fsm_model']['source_metadata'] = {
                                'extraction_method': cluster_info.get('metadata', {}).get('extraction_method', 'Unknown'),
                                'source_pages': cluster_info.get('metadata', {}).get('source_pages', 'Unknown'),
                                'section_number': cluster_info.get('metadata', {}).get('section_number', 'Unknown')
                            }
                            fsm_model['fsm_model']['json_repaired'] = True
                        
                        logger.info(f"Successfully generated FSM for {cluster_name} (with JSON repair)")
                        return fsm_model
                except Exception as repair_error:
                    logger.error(f"JSON repair also failed for {cluster_name}: {repair_error}")
                
                return self._create_fallback_fsm(cluster_info)
                
        except Exception as e:
            logger.error(f"Error generating FSM for {cluster_name}:")
            logger.error(f"  Exception type: {type(e).__name__}")
            logger.error(f"  Exception message: {str(e)}")
            logger.error(f"  Exception args: {e.args}")
            import traceback
            logger.error(f"  Full traceback: {traceback.format_exc()}")
            return self._create_fallback_fsm(cluster_info)
    
    def _create_fallback_fsm(self, cluster_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a basic fallback FSM when generation fails
        
        Args:
            cluster_info: Cluster information
            
        Returns:
            Basic FSM structure
        """
        cluster_data = cluster_info.get('cluster_info', {})
        cluster_name = cluster_data.get('cluster_name', 'Unknown')
        cluster_id = cluster_data.get('cluster_id', 'Unknown')
        category = cluster_info.get('metadata', {}).get('category', 'Unknown')
        
        return {
            "fsm_model": {
                "cluster_name": cluster_name,
                "cluster_id": cluster_id,
                "category": category,
                "generation_timestamp": datetime.now().isoformat(),
                "states": [
                    {
                        "name": "Uninitialized",
                        "description": "Initial state before cluster initialization",
                        "is_initial": True,
                        "is_final": False,
                        "attributes_monitored": [],
                        "invariants": []
                    },
                    {
                        "name": "Ready",
                        "description": "Cluster is ready for operation",
                        "is_initial": False,
                        "is_final": False,
                        "attributes_monitored": [],
                        "invariants": []
                    },
                    {
                        "name": "Error",
                        "description": "Error state - FSM generation failed",
                        "is_initial": False,
                        "is_final": True,
                        "attributes_monitored": [],
                        "invariants": []
                    }
                ],
                "transitions": [
                    {
                        "from_state": "Uninitialized",
                        "to_state": "Ready",
                        "trigger": "initialization",
                        "guard_condition": "true",
                        "actions": ["initialize_cluster"],
                        "response_command": None
                    }
                ],
                "initial_state": "Uninitialized",
                "final_states": ["Error"],
                "attributes_used": [],
                "commands_handled": [],
                "events_generated": [],
                "formal_properties": {
                    "safety_properties": ["No invalid state transitions"],
                    "liveness_properties": ["Eventually reaches Ready state"],
                    "invariants": ["State consistency"]
                },
                "verification_notes": {
                    "model_assumptions": ["Fallback model due to generation failure"],
                    "coverage_analysis": "Minimal coverage - generation failed",
                    "limitations": ["This is a fallback model", "Actual cluster behavior not modeled"]
                },
                "generation_error": "FSM generation failed - using fallback model"
            }
        }
    
    def _attempt_json_repair(self, json_string: str) -> str:
        """
        Attempt to repair common JSON syntax errors
        
        Args:
            json_string: Malformed JSON string
            
        Returns:
            Potentially repaired JSON string
        """
        repaired = json_string
        
        try:
            # Fix common issues
            # 1. Remove trailing commas before closing braces/brackets
            import re
            repaired = re.sub(r',(\s*[}\]])', r'\1', repaired)
            
            # 2. Fix missing quotes around keys (basic attempt)
            repaired = re.sub(r'(\w+)(\s*:)', r'"\1"\2', repaired)
            
            # 3. Fix single quotes to double quotes
            repaired = repaired.replace("'", '"')
            
            # 4. Fix common escape sequence issues
            repaired = repaired.replace('\\"', '"')
            repaired = re.sub(r'(?<!\\)"(?![\s,\]\}:])', r'\\"', repaired)
            
            # 5. Ensure proper string escaping
            repaired = re.sub(r'\\([^"\\bnfrt/])', r'\\\\\\1', repaired)
            
            # 6. Fix missing closing braces (basic attempt)
            open_braces = repaired.count('{')
            close_braces = repaired.count('}')
            if open_braces > close_braces:
                repaired += '}' * (open_braces - close_braces)
            
            # 7. Fix missing closing brackets
            open_brackets = repaired.count('[')
            close_brackets = repaired.count(']')
            if open_brackets > close_brackets:
                repaired += ']' * (open_brackets - close_brackets)
                
        except Exception as e:
            logger.debug(f"JSON repair error: {e}")
            return json_string  # Return original if repair fails
            
        return repaired
    
    def save_fsm_model(self, fsm_model: Dict[str, Any], cluster_name: str, section_number: str = None):
        """
        Save FSM model to JSON file and generate Promela model for SPIN verification
        
        Args:
            fsm_model: Generated FSM model
            cluster_name: Name of the cluster
            section_number: Section number for filename
        """
        try:
            # Clean cluster name for filename
            safe_name = "".join(c for c in cluster_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_name = safe_name.replace(' ', '_')
            
            # Create filename base
            if section_number:
                filename_base = f"{section_number}_{safe_name}"
            else:
                filename_base = f"{safe_name}"
            
            # Save JSON file (primary format)
            json_filepath = os.path.join(self.output_dir, f"{filename_base}_fsm.json")
            with open(json_filepath, 'w', encoding='utf-8') as f:
                json.dump(fsm_model, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved FSM JSON to: {json_filepath}")
            
            # Generate and save Promela model for SPIN verification
            promela_content = self._generate_promela_model(fsm_model, cluster_name)
            promela_filepath = os.path.join(self.output_dir, f"{filename_base}_model.pml")
            with open(promela_filepath, 'w', encoding='utf-8') as f:
                f.write(promela_content)
            logger.info(f"Saved Promela model to: {promela_filepath}")
            
        except Exception as e:
            logger.error(f"Error saving FSM model for {cluster_name}: {e}")
    
    def _generate_basic_promela_fallback(self, fsm_model: Dict[str, Any], cluster_name: str) -> str:
        """
        Generate basic Promela model as fallback when AI generation fails
        
        Args:
            fsm_model: FSM model dictionary
            cluster_name: Name of the cluster
            
        Returns:
            Basic Promela model as string
        """
        model = fsm_model.get("fsm_model", {})
        states = model.get("states", [])
        commands = model.get("commands_handled", [])
        
        # Extract state names
        state_names = [state.get("name", f"state{i}").lower().replace(" ", "_") 
                      for i, state in enumerate(states)]
        initial_state = model.get("initial_state", state_names[0] if state_names else "init").lower().replace(" ", "_")
        
        # Clean command names
        clean_commands = []
        for cmd in commands[:5]:  # Limit to 5 commands
            if cmd and str(cmd).strip():
                clean_cmd = str(cmd).lower().replace(" ", "_").replace("-", "_")
                clean_cmd = "".join(c for c in clean_cmd if c.isalnum() or c == "_")
                if clean_cmd and not clean_cmd[0].isdigit():
                    clean_commands.append(clean_cmd)
        
        if not clean_commands:
            clean_commands = ["nop"]
        
        return f'''/*
 * Basic Promela Model for {cluster_name}
 * Generated as fallback when AI generation failed
 */

#define MAX_COMMANDS 5

mtype = {{ {", ".join(state_names)} }};
mtype = {{ {", ".join(clean_commands)} }};

mtype current_state = {initial_state};
chan command_queue = [MAX_COMMANDS] of {{ mtype }};
bool processing = false;

active proctype {cluster_name.replace(" ", "")}FSM() {{
    do
    :: (current_state == {initial_state}) ->
        command_queue?_;
        current_state = {state_names[1] if len(state_names) > 1 else initial_state};
    :: else ->
        current_state = {initial_state};
    od
}}

ltl safety {{ [](current_state != {initial_state} -> !processing) }}
ltl progress {{ []<>(current_state == {initial_state}) }}
'''
    
    def _generate_promela_model(self, fsm_model: Dict[str, Any], cluster_name: str) -> str:
        """
        Generate Promela model for SPIN model checker using AI
        
        Args:
            fsm_model: FSM model dictionary
            cluster_name: Name of the cluster
            
        Returns:
            Promela model as string
        """
        try:
            # Prepare the prompt with FSM model and cluster name
            prompt = PROMELA_GENERATION_PROMPT_TEMPLATE.format(
                fsm_model=fsm_model,
                cluster_name=cluster_name
            )
            
            # Generate Promela model using AI
            logger.info(f"Generating Promela model for {cluster_name} using AI")
            
            # Use the same AI interface as FSM generation
            llm = GoogleGenerativeAI(
                model=GEMINI_MODEL,
                google_api_key=GOOGLE_API_KEY,
                temperature=GEMINI_TEMPERATURE,
                max_output_tokens=GEMINI_MAX_OUTPUT_TOKENS
            )
            
            response = llm.invoke(prompt)
            promela_content = response.strip()
            
            # Validate that we got Promela content
            if not promela_content or len(promela_content) < 100:
                raise ValueError("Generated Promela content is too short or empty")
            
            # Basic validation - check for Promela syntax elements
            required_elements = ["mtype", "proctype", "init"]
            missing_elements = [elem for elem in required_elements if elem not in promela_content]
            
            if missing_elements:
                logger.warning(f"Generated Promela missing elements: {missing_elements}")
                # Fall back to template-based generation
                return self._generate_fallback_promela_model(fsm_model, cluster_name)
            
            logger.info(f"Successfully generated AI-based Promela model for {cluster_name}")
            return promela_content
            
        except Exception as e:
            logger.error(f"Error generating AI-based Promela model for {cluster_name}: {e}")
            # Fall back to template-based generation
            return self._generate_fallback_promela_model(fsm_model, cluster_name)
    
    def _generate_fallback_promela_model(self, fsm_model: Dict[str, Any], cluster_name: str) -> str:
        """
        Generate fallback Promela model using templates (backup method)
        
        Args:
            fsm_model: FSM model dictionary
            cluster_name: Name of the cluster
            
        Returns:
            Promela model as string
        """
        logger.info(f"Using fallback template for Promela model: {cluster_name}")
        
        model = fsm_model.get("fsm_model", {})
        cluster_id = model.get("cluster_id", "unknown")
        states = model.get("states", [])
        transitions = model.get("transitions", [])
        commands = model.get("commands_handled", [])
        
        # Clean and prepare commands
        clean_commands = []
        for cmd in commands[:8]:  # Limit to first 8
            if isinstance(cmd, list):
                clean_commands.extend([str(c) for c in cmd[:3]])
            else:
                clean_commands.append(str(cmd))
        
        # Clean command names for Promela
        final_commands = []
        for cmd in clean_commands:
            if cmd and str(cmd).strip():
                clean_cmd = str(cmd).lower().replace(" ", "_").replace("-", "_")
                clean_cmd = "".join(c for c in clean_cmd if c.isalnum() or c == "_")
                if clean_cmd and not clean_cmd[0].isdigit():
                    final_commands.append(clean_cmd)
        
        if not final_commands:
            final_commands = ["nop"]
        
        # Clean state names
        state_names = []
        for i, state in enumerate(states):
            state_name = state.get("name", f"state{i}").lower().replace(" ", "_")
            state_name = "".join(c for c in state_name if c.isalnum() or c == "_")
            if state_name and not state_name[0].isdigit():
                state_names.append(state_name)
        
        if not state_names:
            state_names = ["init", "ready", "error"]
            
        initial_state = model.get("initial_state", state_names[0]).lower().replace(" ", "_")
        initial_state = "".join(c for c in initial_state if c.isalnum() or c == "_")
        if not initial_state or initial_state[0].isdigit():
            initial_state = state_names[0]

        promela_content = f'''/*
 * Promela Model for Matter {cluster_name} Cluster
 * Cluster ID: {cluster_id}
 * Generated: {model.get("generation_timestamp", "unknown")}
 * For verification with SPIN model checker
 */

#define MAX_USERS 3
#define MAX_COMMANDS 5

/* Command types */
mtype = {{ {", ".join(final_commands[:8])} }};

/* State enumeration */
mtype = {{ {", ".join(state_names[:8])} }};

/* Global variables */
mtype cluster_state = {initial_state};
byte active_users = 0;
bool error_condition = false;
chan user_commands = [MAX_COMMANDS] of {{ mtype, byte }};

/* Main cluster state machine */
active proctype ClusterStateMachine() {{
    mtype cmd;
    byte user_id;
    
    cluster_state = {initial_state};
    
    do
    :: user_commands?cmd, user_id ->
        atomic {{
            if'''

        # Add basic state transitions
        for i, transition in enumerate(transitions[:6]):  # Limit transitions
            from_state = transition.get("from_state", "unknown").lower().replace(" ", "_")
            to_state = transition.get("to_state", "unknown").lower().replace(" ", "_")
            
            # Clean state names
            from_state = "".join(c for c in from_state if c.isalnum() or c == "_")
            to_state = "".join(c for c in to_state if c.isalnum() or c == "_")
            
            if from_state and to_state and from_state in state_names and to_state in state_names:
                promela_content += f'''            :: (cluster_state == {from_state} && cmd == {final_commands[i % len(final_commands)]}) ->
                cluster_state = {to_state};
                printf("Transition: {from_state} -> {to_state}\\n");
'''

        promela_content += f'''            :: else ->
                printf("Invalid transition or command\\n");
            fi
        }}
    :: timeout ->
        if
        :: (cluster_state != {initial_state}) ->
            cluster_state = {initial_state};
            printf("Timeout: returning to initial state\\n");
        :: else ->
            skip;
        fi
    od
}}

/* User process */
proctype User(byte uid) {{
    do
    :: user_commands!{final_commands[0]}, uid;
    :: user_commands!{final_commands[1] if len(final_commands) > 1 else final_commands[0]}, uid;
    :: skip;
    od
}}

/* LTL properties */
ltl safety {{ [](cluster_state == {initial_state} || cluster_state == {state_names[1] if len(state_names) > 1 else initial_state}) }}
ltl liveness {{ []<>(cluster_state == {initial_state}) }}

init {{
    atomic {{
        run ClusterStateMachine();
        run User(0);
    }}
}}
'''
        return promela_content
    
    def generate_all_fsms(self, limit: Optional[int] = None, skip_existing: bool = True) -> Dict[str, Any]:
        """
        Generate FSM models for all clusters
        
        Args:
            limit: Optional limit on number of clusters to process
            skip_existing: Whether to skip clusters that already have FSM files
            
        Returns:
            Summary of generation results
        """
        if not self.clusters_data or 'clusters' not in self.clusters_data:
            logger.error("No clusters data found")
            return {"error": "No clusters data found"}
        
        clusters = self.clusters_data['clusters']
        total_clusters = len(clusters)
        
        if limit:
            clusters = clusters[:limit]
            logger.info(f"Processing {limit} out of {total_clusters} clusters")
        else:
            logger.info(f"Processing all {total_clusters} clusters")
        
        results = {
            "total_clusters": total_clusters,
            "processed": 0,
            "successful": 0,
            "failed": 0,
            "skipped": 0,
            "generation_summary": [],
            "start_time": datetime.now().isoformat()
        }
        
        for i, cluster_info in enumerate(clusters, 1):
            cluster_data = cluster_info.get('cluster_info', {})
            cluster_name = cluster_data.get('cluster_name', f'Cluster_{i}')
            section_number = cluster_info.get('metadata', {}).get('section_number', 'Unknown')
            
            logger.info(f"[{i}/{len(clusters)}] Processing: {cluster_name} (Section {section_number})")
            
            # Check if FSM already exists
            if skip_existing:
                safe_name = "".join(c for c in cluster_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
                safe_name = safe_name.replace(' ', '_')
                expected_file = os.path.join(self.output_dir, f"{section_number}_{safe_name}_fsm.json")
                
                if os.path.exists(expected_file):
                    logger.info(f"FSM already exists for {cluster_name}, skipping...")
                    results["skipped"] += 1
                    results["generation_summary"].append({
                        "cluster_name": cluster_name,
                        "section_number": section_number,
                        "status": "skipped",
                        "reason": "FSM file already exists"
                    })
                    continue
            
            try:
                # Generate FSM
                fsm_model = self.generate_cluster_fsm(cluster_info)
                
                # Save FSM
                self.save_fsm_model(fsm_model, cluster_name, section_number)
                
                results["successful"] += 1
                results["generation_summary"].append({
                    "cluster_name": cluster_name,
                    "section_number": section_number,
                    "status": "success",
                    "has_generation_error": "generation_error" in fsm_model.get("fsm_model", {})
                })
                
            except Exception as e:
                logger.error(f"Failed to process {cluster_name}: {e}")
                results["failed"] += 1
                results["generation_summary"].append({
                    "cluster_name": cluster_name,
                    "section_number": section_number,
                    "status": "failed",
                    "error": str(e)
                })
            
            results["processed"] += 1
        
        results["end_time"] = datetime.now().isoformat()
        
        # Save generation summary
        summary_file = os.path.join(self.output_dir, "generation_summary.json")
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Generation complete: {results['successful']} successful, {results['failed']} failed, {results['skipped']} skipped")
        logger.info(f"Summary saved to: {summary_file}")
        
        return results
    
    def get_existing_fsm_files(self) -> List[str]:
        """Get list of existing FSM files in output directory"""
        try:
            return [f for f in os.listdir(self.output_dir) if f.endswith('_fsm.json')]
        except Exception as e:
            logger.error(f"Error listing FSM files: {e}")
            return []
    
    def validate_fsm_model(self, fsm_model: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate the structure and consistency of an FSM model
        
        Args:
            fsm_model: FSM model to validate
            
        Returns:
            Validation results
        """
        validation_results = {
            "is_valid": True,
            "errors": [],
            "warnings": []
        }
        
        try:
            model = fsm_model.get("fsm_model", {})
            
            # Check required fields
            required_fields = ["cluster_name", "states", "transitions", "initial_state"]
            for field in required_fields:
                if field not in model:
                    validation_results["errors"].append(f"Missing required field: {field}")
                    validation_results["is_valid"] = False
            
            # Validate states
            states = model.get("states", [])
            if not states:
                validation_results["errors"].append("No states defined")
                validation_results["is_valid"] = False
            else:
                state_names = {state.get("name") for state in states}
                
                # Check initial state exists
                initial_state = model.get("initial_state")
                if initial_state and initial_state not in state_names:
                    validation_results["errors"].append(f"Initial state '{initial_state}' not found in states")
                    validation_results["is_valid"] = False
                
                # Check transitions reference valid states
                for transition in model.get("transitions", []):
                    from_state = transition.get("from_state")
                    to_state = transition.get("to_state")
                    
                    if from_state and from_state not in state_names:
                        validation_results["errors"].append(f"Transition references unknown from_state: {from_state}")
                        validation_results["is_valid"] = False
                    
                    if to_state and to_state not in state_names:
                        validation_results["errors"].append(f"Transition references unknown to_state: {to_state}")
                        validation_results["is_valid"] = False
            
            # Check for unreachable states (warning)
            if states and "transitions" in model:
                reachable_states = {model.get("initial_state")}
                for transition in model["transitions"]:
                    reachable_states.add(transition.get("to_state"))
                
                for state in states:
                    if state.get("name") not in reachable_states:
                        validation_results["warnings"].append(f"State '{state.get('name')}' may be unreachable")
        
        except Exception as e:
            validation_results["errors"].append(f"Validation error: {e}")
            validation_results["is_valid"] = False
        
        return validation_results


def main():
    """Main function"""
    # File paths
    detailed_json_path = "matter_clusters_detailed.json"
    output_dir = "fsm_results"
    
    # Check if input file exists
    if not os.path.exists(detailed_json_path):
        logger.error(f"Input file not found: {detailed_json_path}")
        logger.error("Please run cluster_detail_extractor.py first to generate the detailed clusters JSON")
        return
    
    try:
        # Initialize FSM generator
        logger.info("Initializing FSM generator...")
        generator = ClusterFSMGenerator(detailed_json_path, output_dir)
        
        # Show existing FSM files
        existing_files = generator.get_existing_fsm_files()
        if existing_files:
            logger.info(f"Found {len(existing_files)} existing FSM files")
        
        # Generate FSMs for all clusters
        logger.info("Starting FSM generation for all clusters...")
        results = generator.generate_all_fsms(
            limit=5,  # Process all clusters - change to number for testing specific amount
            skip_existing=True  # Skip clusters that already have FSM files
        )
        
        # Print summary
        print("\n" + "="*60)
        print("FSM GENERATION SUMMARY")
        print("="*60)
        print(f"Total clusters: {results['total_clusters']}")
        print(f"Processed: {results['processed']}")
        print(f"Successful: {results['successful']}")
        print(f"Failed: {results['failed']}")
        print(f"Skipped: {results['skipped']}")
        print(f"Output directory: {output_dir}")
        print("="*60)
        
        if results['failed'] > 0:
            print("\nFailed clusters:")
            for item in results['generation_summary']:
                if item['status'] == 'failed':
                    print(f"  - {item['cluster_name']} (Section {item['section_number']}): {item.get('error', 'Unknown error')}")
        
        print(f"\nFSM models saved to: {os.path.abspath(output_dir)}")
        
    except KeyboardInterrupt:
        logger.warning("Generation interrupted by user")
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        raise


if __name__ == "__main__":
    main()
