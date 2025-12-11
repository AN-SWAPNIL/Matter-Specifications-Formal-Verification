# FSM to Tamarin Parser - Quick Reference

## 🚀 Quick Start

```bash
cd "d:\Academics\LLM Guided Matter\FSM_Generator"
python fsm_json_to_tamarin_parser.py
```

## 📁 Files Created

| File | Purpose |
|------|---------|
| `fsm_json_to_tamarin_parser.py` | Main parser (400+ lines) |
| `FSM_PARSER_README.md` | Full documentation |
| `FSM_PARSER_SUMMARY.md` | Implementation summary |
| `QUICK_REFERENCE.md` | This file |

## 📊 JSON Schema Quick Reference

```
fsm_model/
├── cluster_name (string)
├── cluster_id (string)
├── category (string)
├── initial_state (string)
├── attributes_used (array)
├── commands_handled (array)
├── states (array)
│   ├── name (string)
│   ├── description (string)
│   ├── is_initial (boolean)
│   ├── invariants (array)
│   └── attributes_monitored (array)
├── transitions (array)
│   ├── from_state (string)
│   ├── to_state (string)
│   ├── trigger (string)
│   ├── guard_condition (string)
│   ├── actions (array)
│   ├── response_command (string|null)
│   └── timing_requirements (string|null)
└── metadata
    ├── generation_timestamp (string)
    ├── generation_attempts (integer)
    ├── judge_approved (boolean)
    ├── source_pages (string)
    └── section_number (string)
```

## 🔧 Configuration

Edit in `main()` function:

```python
INPUT_JSON = "./codes/fsm_models/1.5_OnOff_Cluster_fsm.json"
OUTPUT_DIR = "./parsed_tamarin_output"
```

## ✅ What Works

- ✅ JSON loading and parsing
- ✅ Tamarin code generation
- ✅ File output with timestamps
- ✅ WSL path conversion
- ✅ Tamarin syntax validation
- ✅ Error reporting with line numbers

## ⚠️ Known Limitations

- ⚠️ Placeholder attributes (`<attr1, attr2>`)
- ⚠️ Guards as comments (not enforced)
- ⚠️ Actions documented but not implemented
- ⚠️ Comment syntax may need manual fix (`//` → `/* */`)

## 🔍 Validation Command

```bash
wsl /home/linuxbrew/.linuxbrew/bin/tamarin-prover <file>.spthy --parse
```

## 📤 Expected Output

```
======================================================================
🚀 FSM to Tamarin Parser
======================================================================

📂 Loading FSM from: ./codes/fsm_models/1.5_OnOff_Cluster_fsm.json
✅ Loaded FSM with 4 states and 57 transitions
🔧 Generating Tamarin code...
✅ Generated 27,310 characters
💾 Saving to: ./parsed_tamarin_output/On_Off_Cluster_<timestamp>.spthy
✅ Saved successfully

🔍 Validating Tamarin code...
   Return code: 0 or 1
   ✅ VALID or ❌ INVALID

======================================================================
✅ Parser Execution Complete!
======================================================================
```

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Python package error | Stop and test manually (as instructed) |
| WSL not found | Install: `wsl --install` |
| Tamarin not found | Install in WSL: `brew install tamarin-prover` |
| PowerShell conda issues | Use cmd.exe instead |

## 💻 Use cmd.exe (Recommended)

```cmd
cmd /c "cd /d d:\Academics\LLM Guided Matter\FSM_Generator && python fsm_json_to_tamarin_parser.py"
```

## 📝 Generated Tamarin Structure

```tamarin
theory <ClusterName>_Matter_FSM
begin

builtins: hashing, symmetric-encryption

functions: b_true/0, b_false/0,
           st_<State1>/0, st_<State2>/0,
           cmd_<Cmd1>/0, cmd_<Cmd2>/0,
           tv_zero/0, tv_pos/0, tv_ffff/0

rule Init_<ClusterName>:
  [Fr(~tid)]
  --[ClusterInit(tid, '<ClusterName>')]->
  [St(tid, st_<InitialState>, <attrs>)]

rule Trans_<From>_to_<To>_<Cmd>_<Idx>:
  [St(tid, st_<From>, attrs)]
  --[StateTransition(tid, st_<From>, st_<To>, cmd_<Cmd>)]->
  [St(tid, st_<To>, attrs_new)]

lemma sources [sources]:
  "All tid s1 s2 cmd #i. 
    StateTransition(tid, s1, s2, cmd) @ #i 
    ==> Ex #j. ClusterInit(tid, '<ClusterName>') @ #j & #j < #i"

lemma executability [exists-trace]:
  "Ex tid s1 s2 cmd #i #j. 
    ClusterInit(tid, '<ClusterName>') @ #i 
    & StateTransition(tid, s1, s2, cmd) @ #j 
    & #i < #j"

end
```

## 🎯 Key Class Methods

```python
parser = FSMToTamarinParser(json_path)
tamarin_code = parser.generate_tamarin_code()
parser.save_tamarin_code(output_path, tamarin_code)
is_valid, output = parser.validate_tamarin_code(tamarin_file)
```

## 🔄 vs. LLM-Based Converter

| Parser | LLM Converter |
|--------|---------------|
| Fast | Slow (15 iterations) |
| Free | API costs |
| Consistent | Variable quality |
| Simplified | Potentially complete |
| No dependencies | Requires OpenAI + VectorDB |

## 📚 Documentation Files

- **`FSM_PARSER_README.md`** - Full user guide
- **`FSM_PARSER_SUMMARY.md`** - Implementation details
- **`QUICK_REFERENCE.md`** - This quick reference

## 🎓 Next Steps

1. Run parser and check output
2. Review generated `.spthy` file
3. Note validation errors (expected)
4. Manually refine if needed
5. Consider implementing full features (guards, actions, attributes)

## ✨ No Files Modified

As requested, **zero existing files were changed**. All new functionality.

---

**For full details:** See `FSM_PARSER_README.md`

**For implementation notes:** See `FSM_PARSER_SUMMARY.md`
