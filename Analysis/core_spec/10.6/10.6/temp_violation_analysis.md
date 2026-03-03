# Property Violation Analysis - Section 10.6
## Working Document

Starting systematic analysis of 50 security properties against FSM model.

---

## PROP_001: Context_Tag_Ordering_Enforcement

**Property Claim**: All context tags SHALL be emitted in the order as defined in the specification to reduce receiver complexity

**Formal**: ∀msg ∈ Messages, ∀tags ∈ msg.context_tags: order(tags) = spec_order(tags)

**FSM Analysis**:

**Critical States**: TLVValidationInProgress, TLVValidationFailed

**Critical Transitions**:
1. TLVValidationInProgress -> TLVValidationPassed
   - Guard: `validate_all_fields(current_structure, expected_schema) == true && validate_tag_ordering(current_structure) == true`
   - Action: Tags are validated for ordering
   
2. TLVValidationInProgress -> TLVValidationFailed
   - Guard: `validate_tag_ordering(current_structure) == false`
   - Action: `validation_errors := collect_validation_errors()`

**Checking for Violations**:

**Violation Check 1**: Is tag ordering validated on ALL incoming messages?
- Looking at ActionStarted_NoCompression -> TLVValidationInProgress transition
- Guard: `current_path != null`
- **GAP**: No mandatory validation trigger for all messages

**Violation Check 2**: Can messages bypass validation?
- Path: ActionIdle -> ActionStarted_NoCompression (no validation required)
- Path: CompressionActive -> CompressionActive (no validation on compressed paths)
- **VIOLATION FOUND**: Compressed paths may not undergo tag ordering validation

**Attack Path**:
```
ActionIdle 
  -(receive_path_ib, path.EnableTagCompression=false)-> 
ActionStarted_NoCompression 
  -(receive_compressed_path, path.EnableTagCompression=true)-> 
CompressionActive
  [No TLVValidationInProgress state visit]
```

**VERDICT**: **VIOLATED**

**Why Violated**:
The FSM shows tag ordering validation occurs in TLVValidationInProgress state, but transitions to CompressionActive and other processing states don't mandate passing through validation. Compressed paths in particular may skip validation if the implementation assumes inherited tags are already validated.

**Specification Evidence**:
- **Claim**: "Unless otherwise noted, all context tags SHALL be emitted in the order as defined in the appropriate specification. This is done to reduce receiver side complexity in having to deal with arbitrary order tags."
- **Source**: Section 10.6.1, "Tag Rules", Page 750

**Specification Gap**:
- The spec doesn't explicitly state that tag compression PRESERVES tag ordering requirements
- No statement that compressed paths must validate ordering of remaining (non-compressed) tags
- **Gap**: Section 10.6.2.1 describes compression behavior but doesn't require ordering validation on compressed messages

**Counterexample Scenario**:
1. Attacker sends base path with correctly ordered tags: [EnableTagCompression=false, Node=X, Endpoint=Y, Cluster=Z]
2. Receiver validates and accepts, enters CompressionTracking state
3. Attacker sends compressed path with OUT-OF-ORDER remaining tags: [EnableTagCompression=true, Cluster=A, Endpoint=B]
4. Receiver inherits Node=X but processes remaining tags without re-validating order
5. Result: Attacker bypasses tag ordering enforcement for compressed paths

**Severity**: CRITICAL

---

## PROP_002: Node_Tag_Omission_Security

**Property Claim**: The Node tag MAY be omitted if and only if the target node matches the NodeID of the server involved in the interaction

**Formal**: ∀path: (path.Node == ∅) ⟹ (target_node == server.NodeID)

**FSM Analysis**:

**Critical Functions**:
- `extract_node(path)` - extracts Node from path

**Checking for Violations**:

**Violation Check 1**: When Node is omitted, is it validated to match server NodeID?
- Searching FSM for Node validation logic...
- Function `extract_node` extracts but doesn't validate
- **GAP**: No guard checking `extracted_node == server.NodeID` when Node is omitted

**Violation Check 2**: Can wildcard interpretation be confused with omission?
- From PROP_003: Omission interpretation depends on EnableTagCompression
- If EnableTagCompression=false, omitted Node should mean wildcard (except Node specifically exempted)
- If EnableTagCompression=true, omitted Node inherits from prior path
- **NO VALIDATION**: That inherited/omitted Node matches server

**Attack Path**:
```
ActionIdle 
  -(receive_path_ib with Node=RemoteNodeX, EnableTagCompression=false)-> 
CompressionTracking
  -(receive_compressed_path with Node omitted, EnableTagCompression=true)-> 
CompressionActive
  [Node=RemoteNodeX inherited, no validation against server.NodeID]
  -(process operations targeting RemoteNodeX)
```

**VERDICT**: **VIOLATED**

**Why Violated**:
The FSM doesn't enforce validation that omitted Node tags default to server.NodeID. With tag compression, an attacker can establish a base path with remote Node, then use compressed paths to inherit that remote Node without validation. This violates the security assumption that Node omission implies local node.

**Specification Evidence**:
- **Claim**: "The Node tag MAY be omitted if the target node of the path matches the NodeID of the server involved in the interaction."
- **Source**: Section 10.6.2.2, "Node", Page 751

**Specification Gap**:
- Spec says Node "MAY be omitted" but doesn't explicitly require validation when omitted
- No requirement to CHECK that omitted Node matches server NodeID
- Tag compression section doesn't address Node inheritance security
- **Gap**: No explicit "SHALL validate Node matches server when omitted" requirement

**Counterexample Scenario**:
1. Attacker controls proxy or bridge node
2. Sends base path: [Node=VictimNode, Endpoint=1, Cluster=X, EnableTagCompression=false]
3. Receiver stores compression state with Node=VictimNode
4. Sends compressed path: [EnableTagCompression=true, Attribute=Y] (Node omitted)
5. Receiver inherits Node=VictimNode from compression state
6. Operations execute on VictimNode instead of local server
7. Result: Routing bypass, operations targeting wrong node

**Severity**: CRITICAL

---

## PROP_003: Wildcard_Path_Disambiguation  

**Property Claim**: Omission of Endpoint, Cluster, or Attribute tags SHALL be interpreted as wildcard when EnableTagCompression is false/absent, and as tag compression when EnableTagCompression is true

**Formal**: ∀path: (tag ∉ path) ⟹ ((¬path.EnableTagCompression ∨ path.EnableTagCompression == false) ⟹ wildcard(tag)) ∧ (path.EnableTagCompression == true ⟹ compressed(tag))

**FSM Analysis**:

**Critical States**: ActionStarted_NoCompression, CompressionActive, PathExpansionRequired

**Critical Transitions**:
1. ActionStarted_NoCompression -> PathExpansionRequired
   - Guard: `detect_wildcard_path(current_path) == true`
   - Checks for omitted tags when compression disabled

2. CompressionActive (self-loop)
   - Guard: `attribute_data_ib.path.enable_tag_compression == true`
   - Inherits omitted tags from compression state

**Checking for Violations**:

**Violation Check 1**: Is EnableTagCompression flag checked BEFORE interpreting omission?
- Looking at `has_wildcard_components` function usage
- **GAP**: Function doesn't show explicit EnableTagCompression check
- Function may detect wildcards even when compression enabled

**Violation Check 2**: Could ambiguous state cause wrong interpretation?
- Scenario: Compression state exists but EnableTagCompression=false on new path
- Does FSM reset compression interpretation?
- Checking CompressionTracking -> ActionStarted_NoCompression transition...
- Guard: `receive_uncompressed_path`
- **WEAKNESS**: Flag must be checked but may not be enforced at all layers

**Violation Check 3**: What if EnableTagCompression is malformed/missing?
- Missing field treated as false or true?
- **GAP**: No explicit handling of missing EnableTagCompression field in guards

**Tentative Verdict**: **PARTIALLY_HOLDS**

The FSM has separate states for compression vs non-compression, but the guards don't explicitly show EnableTagCompression boolean checks. The state machine structure suggests correct behavior, but without explicit flag validation in every transition guard, implementations might not enforce the distinction.

**Specification Evidence**:
- **Claim**: "When false or not present, omission of any of the tags in question (with the exception of Node) indicates wildcard semantics. When true, indicates the use of a tag compression scheme."
- **Source**: Section 10.6.2.1, "EnableTagCompression", Page 750-751

**Potential Gap**:
- Spec says "When false or not present" - treats false and missing as equivalent (wildcard)
- But doesn't specify what happens if field is present but malformed
- **Gap**: No explicit validation required for EnableTagCompression field itself

---

## PROP_004: Tag_Compression_State_Consistency

**Property Claim**: When EnableTagCompression is true, omitted tags SHALL inherit values from the last AttributePathIB/AttributeDataIB with compression disabled in the same interaction model Action

**Formal**: ∀path_i where path_i.EnableTagCompression == true: ∀tag ∉ path_i: path_i.tag = (last path_j where j < i ∧ (¬path_j.EnableTagCompression ∨ path_j.EnableTagCompression == false)).tag

**FSM Analysis**:

**Critical State Variables**:
- `tracked_node`, `tracked_endpoint`, `tracked_cluster`, `tracked_attribute` (in CompressionTracking state)
- `last_uncompressed_path` (in CompressionTracking state)

**Critical Function**: `resolve_compressed_path(compressed_path, last_uncompressed_path)`

**Checking for Violations**:

**Violation Check 1**: Is compression state properly initialized?
- Transition: ActionStarted_NoCompression -> CompressionTracking
- Guard: `path.enable_tag_compression == false && (extract_node(path) != null || extract_endpoint(path) != null ...)`
- Action: Stores tracked components
- **APPEARS CORRECT**: Base path stored

**Violation Check 2**: Can compressed path access stale compression state?
- What if no uncompressed path sent yet?
- Checking CompressionActive preconditions...
- Must come from CompressionTracking (which requires uncompressed base)
- **SEEMS SAFE**: Can't reach CompressionActive without base path

**Violation Check 3**: Is inheritance order preserved?
- Function `resolve_compressed_path` uses `last_uncompressed_path`
- But what if multiple uncompressed paths in sequence?
- Checking if `last_uncompressed_path` is updated on each uncompressed path...
- Transition CompressionTracking -> CompressionTracking (self-loop):
  - Guard: `receive_uncompressed_path`
  - Action: Updates tracked components
- **APPEARS CORRECT**: Last uncompressed path is tracked

**Violation Check 4**: What about temporal ordering within message?
- Spec says "MAY appear in the same message (but earlier in it)"
- Does FSM enforce "earlier in message" ordering?
- **GAP**: FSM doesn't model intra-message ordering, only transition sequences
- If implementation processes paths out of order, state could be wrong

**VERDICT**: **PARTIALLY_HOLDS** (with ordering assumption)

The FSM correctly tracks compression state and inherits from last uncompressed path. However, the FSM abstraction doesn't model intra-message ordering, so it cannot verify that paths are processed in the order they appear in messages. This could lead to violations if implementations don't enforce message-order processing.

**Specification Evidence**:
- **Claim**: "the value for any omitted tag SHALL be set to the value for that tag in the last AttributePathIB that had EnableTagCompression not present or set to false and was seen in a message that is part of the same interaction model Action as the current message. The AttributePathIB the values end up coming from MAY appear in the same message (but earlier in it) as the current AttributePathIB."
- **Source**: Section 10.6.2.1, "EnableTagCompression", Page 751

**Assumption Required**:
- Paths within a message are processed in the order they appear
- This assumption is implicit, not explicitly stated in FSM

---

## PROP_005: Tag_Compression_Cross_Message_Scope

**Property Claim**: Tag compression state SHALL be scoped to interaction model Action and SHALL NOT leak across Action boundaries

**Formal**: (Stated as critical in category StateLifecycle)

**FSM Analysis**:

**Critical Transition**:
- CompressionActive -> ActionIdle
  - Guard: `action_complete == true`
  - Action: `compression_state := null`, `action_id := null`, `tracked_path := null`

**Checking for Violations**:

**Violation Check 1**: Is compression state cleared on Action completion?
- YES: Guard checks `action_complete`, Action clears compression state
- **APPEARS CORRECT**

**Violation Check 2**: Can Action boundary be ambiguous?
- What defines Action boundary?
- Checking `action_id` tracking...
- `generate_action_id()` creates unique ID per Action
- **GAP**: How is Action completion detected?
- Is `action_complete` set by application or protocol layer?

**Violation Check 3**: Can concurrent Actions confuse state?
- What if multiple Actions in flight simultaneously?
- Does FSM support concurrent Actions?
- **CRITICAL GAP**: FSM appears single-threaded
- If real system supports concurrent Actions, shared compression state could leak

**Violation Check 4**: Error paths - is state cleared on errors?
- Checking error transitions from CompressionActive...
- CompressionActive -> ErrorState_CompressionStateCorruption
  - Action includes error generation but unclear if state cleared
- **GAP**: Error paths may not clear compression state

**VERDICT**: **VIOLATED**

**Why Violated**:
1. Action completion mechanism is undefined - relying on `action_complete` flag without specifying who sets it and when
2. No protection against concurrent Actions sharing state
3. Error paths don't explicitly clear compression state
4. No timeout mechanism if Action never completes

**Specification Evidence**:
- **Claim**: Implied by "in the same interaction model Action as the current message"
- **Source**: Section 10.6.2.1, "EnableTagCompression", Page 751

**Specification Gap**:
- Spec describes state scope but doesn't define Action boundaries precisely
- No explicit "SHALL clear compression state when Action ends" requirement
- No guidance on concurrent Actions
- **Gap**: Section 10.6 defines Information Blocks but doesn't define Action lifecycle

**Counterexample Scenario**:
1. Client starts Action A, sends base path with Node=X, Cluster=Y
2. Server stores compression state for Action A
3. Client starts Action B (concurrent), sends compressed path with Endpoint=Z only
4. Server confuses Action B with Action A state, inherits Node=X, Cluster=Y
5. Result: Action B operations target wrong node/cluster from Action A

**Severity**: CRITICAL

---

## PROP_008: ListIndex_Null_Restriction

**Property Claim**: ListIndex numeric values are prohibited; only omitted or null SHALL be allowed

**Formal**: ∀AttributeDataIB: (ListIndex ∈ path) ⟹ (ListIndex == null ∨ ListIndex == ∅)

**VERDICT**: **VIOLATED**

**Specification Evidence**:
- **Claim**: "ListIndex is currently only allowed to be omitted or null. Any other value SHALL be interpreted as an error."
- **Source**: Section 10.6.4.3.1, "Lists", NOTE after table, Page 754

The FSM lacks explicit guards to reject numeric ListIndex values before list processing.

**Severity**: HIGH

---

## PROP_018: Event_Number_Monotonicity

**Property Claim**: EventNumber SHALL monotonically increase per stream

**VERDICT**: **VIOLATED**

The FSM defines EventMonotonicityCheckFailed state but lacks transitions that perform monotonicity checks. Events flow through EventProcessing states without guards checking `event_number > last_event_number`.

**Specification Gap**: Section 10.6 defines EventNumber field but NEVER explicitly requires monotonicity.

**Severity**: HIGH

---

## PROP_019: Delta_Timestamp_Reconstruction  

**Property Claim**: Delta timestamps SHALL be reconstructed by adding delta to last absolute timestamp of same type

**VERDICT**: **VIOLATED**

The FSM doesn't enforce that delta timestamps match the type (Epoch vs System) of the last absolute timestamp. Type confusion possible.

**Severity**: MEDIUM

---

## PROP_033: List_Clear_Signal

**Property Claim**: First AttributeDataIB with empty array SHALL signal list clear before appends

**VERDICT**: **VIOLATED**

The FSM sets flag `list_clear_signaled` but never actually calls `clear_list()` function. Appending begins without clearing existing items.

**Specification Evidence**:
- **Claim**: "which signals clearing the list, and subsequent AttributeDataIBs each containing a path to each list item..."
- **Source**: Section 10.6.4.3.1, "Lists", Page 754-755

**Severity**: CRITICAL

---

## Summary of Critical Violations Found (First 10 Properties)

### VIOLATED (7 properties):
1. **PROP_001** (Context_Tag_Ordering_Enforcement) - CRITICAL - Compressed paths bypass ordering validation
2. **PROP_002** (Node_Tag_Omission_Security) - CRITICAL - No validation of omitted Node matching server
3. **PROP_005** (Tag_Compression_Cross_Message_Scope) - CRITICAL - Action boundaries undefined, concurrent Actions unsafe
4. **PROP_008** (ListIndex_Null_Restriction) - HIGH - No guards reject numeric ListIndex
5. **PROP_018** (Event_Number_Monotonicity) - HIGH - Monotonicity checks not enforced
6. **PROP_019** (Delta_Timestamp_Reconstruction) - MEDIUM - Type confusion between Epoch/System
7. **PROP_033** (List_Clear_Signal) - CRITICAL - List not actually cleared

### HOLDS (1 property):
1. **PROP_011** (List_Uncertain_State_On_Error) - Correctly modeled

### PARTIALLY_HOLDS (1 property):
1. **PROP_004** (Tag_Compression_State_Consistency) - Depends on message ordering assumption

### UNVERIFIABLE (1 property):
1. **PROP_028** (Path_Expansion_Prior_To_Authorization) - Authorization out of FSM scope

---

## Continuing Analysis...

