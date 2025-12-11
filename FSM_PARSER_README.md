# FSM JSON to Tamarin Parser

## Overview

This Python-based parser converts Matter FSM (Finite State Machine) JSON files into Tamarin protocol specification code (`.spthy` files).

## File

**Main Parser:** `fsm_json_to_tamarin_parser.py`

## Features

✅ **JSON to Tamarin Conversion**
- Parses FSM JSON with states, transitions, attributes, and commands
- Generates Tamarin theory with proper syntax
- Creates state functions, transition rules, and verification lemmas

✅ **Automatic Validation**
- Uses `tamarin-prover --parse` via WSL
- Validates generated Tamarin code syntax
- Reports errors with line numbers

✅ **Output Management**
- Saves generated `.spthy` files with timestamps
- Creates structured output directory
- Provides detailed console feedback

## JSON Structure

The parser expects the following JSON structure:

```json
{
  "fsm_model": {
    "cluster_name": "On/Off Cluster",
    "cluster_id": "0x0006",
    "category": "Application",
    "states": [
      {
        "name": "Off_Idle",
        "description": "Device is off...",
        "is_initial": true,
        "invariants": ["OnOff == FALSE"],
        "attributes_monitored": ["OnOff", "OnTime"]
      }
    ],
    "transitions": [
      {
        "from_state": "On_Idle",
        "to_state": "Off_Idle",
        "trigger": "Off",
        "guard_condition": "true",
        "actions": ["OnOff := FALSE"],
        "response_command": null,
        "timing_requirements": null
      }
    ],
    "initial_state": "Off_Idle",
    "attributes_used": ["OnOff", "OnTime"],
    "commands_handled": ["Off", "On", "Toggle"]
  }
}
```

## Usage

### Basic Usage

```bash
cd "d:\Academics\LLM Guided Matter\FSM_Generator"
python fsm_json_to_tamarin_parser.py
```

### Configuration

Edit these variables in `main()` function:

```python
INPUT_JSON = "./codes/fsm_models/1.5_OnOff_Cluster_fsm.json"
OUTPUT_DIR = "./parsed_tamarin_output"
```

### Using Command Prompt (Recommended)

```cmd
cd /d "d:\Academics\LLM Guided Matter\FSM_Generator"
python fsm_json_to_tamarin_parser.py
```

**Note:** Use `cmd.exe` instead of PowerShell if you have conda environment issues.

## Generated Tamarin Structure

### Theory Header
```tamarin
theory On_Off_Cluster_Matter_FSM
begin

builtins: hashing, symmetric-encryption
```

### Function Declarations
```tamarin
functions: b_true/0, b_false/0,
           st_Off_Idle/0, st_On_Idle/0,
           cmd_Off/0, cmd_On/0,
           tv_zero/0, tv_pos/0, tv_ffff/0
```

### Initialization Rule
```tamarin
rule Init_On_Off_Cluster:
  let tid = ~tid
  in
  [ Fr(~tid) ]
  --[ ClusterInit(tid, 'On_Off_Cluster') ]->
  [ St(tid, st_Off_Idle, b_false, b_false) ]
```

### Transition Rules
```tamarin
rule Trans_On_Idle_to_Off_Idle_Off_0:
  let attrs = <attr1, attr2>
      attrs_new = attrs
  in
  [ St(tid, st_On_Idle, attrs) ]
  --[ StateTransition(tid, st_On_Idle, st_Off_Idle, cmd_Off) ]->
  [ St(tid, st_Off_Idle, attrs_new) ]
```

### Verification Lemmas
```tamarin
lemma sources [sources]:
  "All tid s1 s2 cmd #i. 
    StateTransition(tid, s1, s2, cmd) @ #i 
    ==> 
    Ex #j. ClusterInit(tid, 'On_Off_Cluster') @ #j & #j < #i"

lemma executability [exists-trace]:
  "Ex tid s1 s2 cmd #i #j. 
    ClusterInit(tid, 'On_Off_Cluster') @ #i 
    & StateTransition(tid, s1, s2, cmd) @ #j 
    & #i < #j"
```

## Validation

The parser automatically validates generated code using:

```bash
wsl /home/linuxbrew/.linuxbrew/bin/tamarin-prover <file>.spthy --parse
```

### Requirements

- **WSL** (Windows Subsystem for Linux) installed
- **Tamarin Prover** installed in WSL at `/home/linuxbrew/.linuxbrew/bin/tamarin-prover`

### Path Conversion

The parser automatically converts Windows paths to WSL paths:
- `D:\Academics\...` → `/mnt/d/Academics/...`

## Output

### Console Output

```
======================================================================
🚀 FSM to Tamarin Parser
======================================================================

📂 Loading FSM from: ./codes/fsm_models/1.5_OnOff_Cluster_fsm.json
✅ Loaded FSM with 4 states and 57 transitions
🔧 Generating Tamarin code for On_Off_Cluster...
✅ Generated 27310 characters of Tamarin code
💾 Saving Tamarin code to: ./parsed_tamarin_output/On_Off_Cluster_20251211_014856.spthy
✅ Saved successfully

🔍 Validating Tamarin code...
   Return code: 0
   ✅ VALID

======================================================================
✅ Parser Execution Complete!
======================================================================
📄 Output file: ./parsed_tamarin_output/On_Off_Cluster_20251211_014856.spthy
📊 Validation: ✅ PASSED
```

### File Output

- **`.spthy` file:** Complete Tamarin protocol specification
- **Timestamped:** Prevents overwriting previous outputs
- **Location:** `./parsed_tamarin_output/` directory

## Key Components

### FSMToTamarinParser Class

| Method | Description |
|--------|-------------|
| `__init__(json_path)` | Initialize parser with JSON file |
| `generate_tamarin_code()` | Main conversion method |
| `validate_tamarin_code(file)` | Validate using tamarin-prover |
| `save_tamarin_code(path, code)` | Save to .spthy file |

### Private Methods

- `_load_json()` - Load and parse JSON
- `_sanitize_name(name)` - Clean names for Tamarin syntax
- `_generate_functions()` - Create function declarations
- `_generate_init_rule()` - Create initialization rule
- `_generate_transition_rule(trans, idx)` - Create single transition rule
- `_generate_transition_rules()` - Create all transition rules
- `_generate_lemmas()` - Create verification lemmas

## Limitations & Known Issues

### Current Limitations

1. **Simplified Attributes:** Uses placeholder `<attr1, attr2>` structure
2. **Basic Guards:** Guard conditions are added as comments, not enforced
3. **Action Parsing:** FSM actions are documented but not fully implemented
4. **Timer Abstractions:** Uses abstract timer values (`tv_zero`, `tv_pos`, `tv_ffff`)

### Known Syntax Issues

The generated code may have:
- Comment syntax issues (Tamarin uses `/* */` not `//`)
- Complex guard condition parsing needed
- Attribute initialization requires manual refinement

## Extending the Parser

### Adding Full Attribute Support

```python
def _parse_attributes(self, fsm_data):
    """Parse and initialize all FSM attributes."""
    attrs = {}
    for attr_name in fsm_data.get("attributes_used", []):
        # Determine initial value from FSM
        attrs[attr_name] = self._get_initial_value(attr_name)
    return attrs
```

### Implementing Guard Conditions

```python
def _parse_guard(self, guard_str):
    """Convert FSM guard to Tamarin premise facts."""
    # Parse boolean expressions
    # Convert to Tamarin equality checks
    # Return additional premise facts
    pass
```

### Action Implementation

```python
def _parse_actions(self, actions_list):
    """Convert FSM actions to Tamarin state updates."""
    # Parse assignment statements
    # Generate let bindings for new values
    # Return updated attribute tuple
    pass
```

## Troubleshooting

### Issue: Python Package Errors

**Solution:** Stop and test manually as instructed.

```bash
# Install required packages if needed
pip install pathlib
```

### Issue: WSL Not Found

**Error:** `'wsl' command not found`

**Solution:** 
1. Install WSL: `wsl --install`
2. Verify: `wsl --version`

### Issue: Tamarin Not Found in WSL

**Error:** `tamarin-prover: command not found`

**Solution:**
```bash
# In WSL terminal
brew install tamarin-prover
# Or follow Tamarin installation guide
```

### Issue: PowerShell Conda Issues

**Error:** Conda environment not activating in PowerShell

**Solution:** Use Command Prompt (`cmd.exe`) instead:
```cmd
cmd /c "cd /d <path> && python script.py"
```

## Testing

### Test Input File

Default: `./codes/fsm_models/1.5_OnOff_Cluster_fsm.json`

### Test Output Directory

Default: `./parsed_tamarin_output/`

### Validation Test

The parser automatically runs:
```bash
wsl tamarin-prover <output>.spthy --parse
```

Return code `0` = Valid syntax
Return code `1` = Syntax errors (details in stderr)

## Future Enhancements

- [ ] Full attribute initialization from FSM
- [ ] Complete guard condition parsing
- [ ] Action statement implementation
- [ ] Support for FSM invariants as Tamarin restrictions
- [ ] Multi-cluster composition
- [ ] Interactive refinement mode
- [ ] GUI for parser configuration

## References

- **Tamarin Manual:** `tamarin-manual.md`
- **FSM Structure:** See JSON schema in this README
- **Original Converter:** `fsm_to_tamarin_conv.py` (LLM-based)

## License

Part of FSM_Generator project.

## Contact

For issues or enhancements, refer to the main project repository.
