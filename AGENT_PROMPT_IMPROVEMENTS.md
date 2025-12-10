# Agent Prompt Improvements

## Summary of Changes

Transformed the comprehensive non-agentic prompt template into a concise, action-oriented agent system prompt that leverages the agent's ability to query the RAG database dynamically.

## Key Improvements

### 1. **Focused on Critical Errors**
Instead of listing all Tamarin syntax, the prompt now highlights the **most common parsing errors**:
- ❌ Using `not()` in rule premises (causes parsing errors)
- ❌ Multiple function blocks
- ❌ Reserved keywords (true/false)
- ❌ Underscore wildcards

### 2. **Actionable Instructions**
Changed from "here's everything about Tamarin" to "here's what to DO":
- Query the manual using tools
- Generate theory structure
- Validate immediately
- Fix specific error patterns
- Re-validate until it passes

### 3. **Dynamic Knowledge Retrieval**
The agent prompt now **instructs the agent to use tools** rather than embedding all knowledge:

**Before** (non-agentic):
```
[100+ lines of Tamarin syntax examples, all clusters, all features...]
```

**After** (agentic):
```
"Use db_query_tool('tamarin rule syntax', k=3) for syntax help"
```

### 4. **Critical "NOT EQUAL" Guard Handling**
Prominently featured the most problematic pattern with clear solution:

```
🚨 CRITICAL: FSM guards like `OnTime != 0xFFFF` CANNOT use `not()` in premises!

SOLUTION: Split into separate rules for each ALLOWED value
```

### 5. **Workflow-Oriented Structure**
Organized as a step-by-step workflow:
1. Query Manual
2. Generate Theory
3. Validate
4. Fix Errors
5. Re-validate
6. Save

### 6. **Error-to-Solution Mapping**
Added specific error message → solution mappings:
- "unexpected (" → you used not() in premises
- "Multiple function declarations" → merge into one block
- "facts must start with upper-case" → not() in premises

### 7. **Removed Redundancy**
Eliminated sections that the agent can query on-demand:
- ❌ Full cluster examples (OnOff, LevelControl, DoorLock)
- ❌ Feature combination generation code
- ❌ Cross-cluster dependencies
- ❌ Complete template with all sections

These are available in the RAG database and can be retrieved as needed.

## What Was Kept

### Essential Syntax Rules
- Single functions block
- State fact structure: `St(~tid, state_enum, attrs...)`
- Abstract timer values: `tv_zero/0, tv_pos/0, tv_ffff/0`
- Boolean values: `b_true/0, b_false/0`

### Critical Modeling Patterns
- Unified state fact approach
- Guard → Pattern mapping table
- Persistent config facts: `!Config(~tid, features...)`
- Required sources lemma

### Template Structure
Minimal template showing:
- Theory declaration
- Functions block
- Init rule with ClusterInit action
- Transition rules with StateTransition actions
- Sources lemma

## Benefits of Agentic Approach

1. **Adaptive**: Agent can query specific syntax as needed rather than processing entire reference
2. **Iterative**: Validate → Fix → Re-validate loop handles edge cases
3. **Context-Aware**: Agent focuses on actual FSM structure rather than all possible patterns
4. **Error Recovery**: Specific error patterns mapped to solutions
5. **Scalable**: Works for simple and complex FSMs without overwhelming the context

## Prompt Size Comparison

- **Non-agentic prompt**: ~400 lines, ~15,000 tokens
- **Agentic prompt**: ~150 lines, ~4,500 tokens
- **Reduction**: 70% smaller while maintaining effectiveness

## Key Instruction Additions

### For the User Request
Enhanced user request with:
- Explicit query suggestions
- Step-by-step conversion requirements
- Guard handling reminder
- Error pattern recognition guide
- Validation requirement

### For Tool Usage
Clear tool calling instructions:
- `db_query_tool("tamarin rule syntax", k=3)`
- `validate_tamarin_syntax(code, protocol_name)`
- `save_tamarin_protocol(code, name, metadata)`

## Result

The improved prompt:
- ✅ Maintains critical Tamarin knowledge
- ✅ Emphasizes common error patterns
- ✅ Guides agent through validation workflow
- ✅ Leverages RAG database for detailed syntax
- ✅ More concise and actionable
- ✅ Better error recovery instructions
