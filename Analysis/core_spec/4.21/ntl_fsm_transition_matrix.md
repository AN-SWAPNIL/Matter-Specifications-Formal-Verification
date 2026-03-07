# NTL FSM Transition Matrix

**Visual representation of all possible state transitions**

Legend:
- ✅ = Transition EXISTS in FSM
- ❌ = Transition MISSING
- ➖ = Not applicable/impossible
- 🟡 = Partially covered (needs additional variant)

---

## Command Transition Matrix

### SELECT Command

| From State ↓ | To State → | Exists? | Error Code | Notes |
|--------------|------------|---------|------------|-------|
| IDLE | ERROR_NOT_IN_COMMISSIONING | ✅ | 0x6985 | When commissioning_mode==false |
| IDLE | IDLE | ✅ | (ignore) | Alternative when commissioning_mode==false |
| COMMISSIONING_MODE_READY | SELECTED | ✅ | 0x9000 | Valid SELECT with correct AID |
| COMMISSIONING_MODE_READY | ERROR_INVALID_AID | ✅ | 0x6A82 | Wrong AID |
| SELECTED | ❓ | ❌ | ??? | **UNDEFINED** - Re-selection scenario |
| TRANSPORT_ACTIVE | ❓ | ❌ | ??? | **UNDEFINED** - Re-selection during transport |
| CHAINING_IN_PROGRESS_RECEIVING | ❓ | ❌ | ??? | **UNDEFINED** - SELECT during fragment accumulation |
| RESPONSE_INCOMPLETE | ❓ | ❌ | ??? | **UNDEFINED** - SELECT during GET_RESPONSE sequence |
| ERROR_NOT_IN_COMMISSIONING | ❓ | ❌ | ??? | In error state |
| ERROR_MEMORY_EXCEEDED | ❓ | ❌ | ??? | In error state |
| ERROR_SEQUENCING | ❓ | ❌ | ??? | In error state |
| ERROR_INVALID_AID | ❓ | ❌ | ??? | In error state |
| ERROR_INVALID_STATE | ❓ | ❌ | ??? | In error state |
| SESSION_TIMEOUT | ❓ | ❌ | ??? | After timeout |

---

### TRANSPORT Command (Unchained: CLA=0x80)

| From State ↓ | To State → | Exists? | Response | Notes |
|--------------|------------|---------|----------|-------|
| IDLE | ERROR_INVALID_STATE | ✅ | 0x6985 | TRANSPORT before SELECT |
| COMMISSIONING_MODE_READY | ERROR_INVALID_STATE | ✅ | 0x6985 | TRANSPORT before SELECT |
| SELECTED | TRANSPORT_ACTIVE | ✅ | 0x9000 | Response fits in Le |
| SELECTED | RESPONSE_INCOMPLETE | ✅ | 0x61XX | Response exceeds Le |
| TRANSPORT_ACTIVE | TRANSPORT_ACTIVE | ✅ | 0x9000 | Response fits in Le (stay in state) |
| TRANSPORT_ACTIVE | RESPONSE_INCOMPLETE | ✅ | 0x61XX | Response exceeds Le |
| CHAINING_IN_PROGRESS_RECEIVING | TRANSPORT_ACTIVE | ✅ | 0x9000 | Last fragment, response fits |
| CHAINING_IN_PROGRESS_RECEIVING | RESPONSE_INCOMPLETE | ✅ | 0x61XX | Last fragment, response exceeds Le |
| RESPONSE_INCOMPLETE | ❓ | ❌ | ??? | **MISSING** - TRANSPORT during GET_RESPONSE |
| ERROR_* (all) | ❓ | ❌ | ??? | In error state |
| SESSION_TIMEOUT | ❓ | ❌ | ??? | After timeout |

---

### TRANSPORT Command (Chained Start: CLA=0x90, first fragment)

| From State ↓ | To State → | Exists? | Guard | Notes |
|--------------|------------|---------|-------|-------|
| IDLE | ERROR_INVALID_STATE | ✅ | session==IDLE | TRANSPORT before SELECT |
| COMMISSIONING_MODE_READY | ERROR_INVALID_STATE | ✅ | session==IDLE | TRANSPORT before SELECT |
| SELECTED | CHAINING_IN_PROGRESS_RECEIVING | ✅ | Lc <= max | First fragment valid |
| SELECTED | ERROR_MEMORY_EXCEEDED | ✅ | Lc > max | First fragment exceeds memory |
| TRANSPORT_ACTIVE | CHAINING_IN_PROGRESS_RECEIVING | ✅ | Lc <= max | Start new chain from TRANSPORT_ACTIVE |
| TRANSPORT_ACTIVE | ERROR_MEMORY_EXCEEDED | 🟡❌ | Lc > max | **MISSING explicit transition** |
| CHAINING_IN_PROGRESS_RECEIVING | ➖ | ➖ | N/A | Already in chaining (continuation, not start) |
| RESPONSE_INCOMPLETE | ❓ | ❌ | ??? | **MISSING** - Chained TRANSPORT during GET_RESPONSE |
| ERROR_* (all) | ❓ | ❌ | ??? | In error state |

---

### TRANSPORT Command (Chained Continuation: CLA=0x90, not first)

| From State ↓ | To State → | Exists? | Guard | Notes |
|--------------|------------|---------|-------|-------|
| CHAINING_IN_PROGRESS_RECEIVING | CHAINING_IN_PROGRESS_RECEIVING | ✅ | fragments+Lc < total && <= max | Continue accumulating |
| CHAINING_IN_PROGRESS_RECEIVING | ERROR_MEMORY_EXCEEDED | ✅ | fragments+Lc > max | Accumulated exceeds memory |
| CHAINING_IN_PROGRESS_RECEIVING | ERROR_SEQUENCING | ✅ | P1P2 != stored | P1/P2 inconsistency |
| (Other states) | ➖ | ➖ | N/A | Not in chaining mode |

---

### GET_RESPONSE Command

| From State ↓ | To State → | Exists? | Response | Notes |
|--------------|------------|---------|----------|-------|
| IDLE | ❓ | ❌ | ??? | **MISSING** - GET_RESPONSE before session |
| COMMISSIONING_MODE_READY | ❓ | ❌ | ??? | **MISSING** - GET_RESPONSE before SELECT |
| SELECTED | ERROR_SEQUENCING | ✅ | 0x6985 | No prior SW1=0x61 |
| TRANSPORT_ACTIVE | ERROR_SEQUENCING | ✅ | 0x6985 | No prior SW1=0x61 |
| CHAINING_IN_PROGRESS_RECEIVING | ERROR_SEQUENCING | ✅ | 0x6985 | Wrong command during chaining |
| RESPONSE_INCOMPLETE | RESPONSE_INCOMPLETE | ✅ | 0x61XX | More fragments (response_remaining > Le) |
| RESPONSE_INCOMPLETE | TRANSPORT_ACTIVE | ✅ | 0x9000 | Last fragment (response_remaining <= Le) |
| ERROR_* (all) | ❓ | ❌ | ??? | In error state |
| SESSION_TIMEOUT | ❓ | ❌ | ??? | After timeout |

---

### Timer Tick (Idle Timer Management)

| From State ↓ | To State → | Exists? | Condition | Notes |
|--------------|------------|---------|-----------|-------|
| IDLE | ➖ | ➖ | N/A | No active session timer |
| COMMISSIONING_MODE_READY | ➖ | ➖ | N/A | No session timer (only commissioning mode active) |
| SELECTED | SELECTED | ✅ | timer < 30000ms | Increment timer (stay) |
| SELECTED | SESSION_TIMEOUT | ✅ | timer >= 30000ms | Idle timeout |
| TRANSPORT_ACTIVE | TRANSPORT_ACTIVE | ✅ | timer < 30000ms | Increment timer (stay) |
| TRANSPORT_ACTIVE | SESSION_TIMEOUT | ✅ | timer >= 30000ms | Idle timeout |
| CHAINING_IN_PROGRESS_RECEIVING | CHAINING_IN_PROGRESS_RECEIVING | ✅ | timer < 30000ms | Increment timer (stay) |
| CHAINING_IN_PROGRESS_RECEIVING | SESSION_TIMEOUT | ✅ | timer >= 30000ms | Idle timeout (fragments cleared) |
| RESPONSE_INCOMPLETE | RESPONSE_INCOMPLETE | ✅ | timer < 30000ms | Increment timer (stay) |
| RESPONSE_INCOMPLETE | SESSION_TIMEOUT | ✅ | timer >= 30000ms | Idle timeout (response buffer cleared) |
| ERROR_* (all) | ❓ | ❌ | ??? | **MISSING** - Error state timeout |
| SESSION_TIMEOUT | ❓ | ❌ | ??? | **MISSING** - Cleanup to IDLE |

---

### Enable/Disable Commissioning Mode

| From State ↓ | To State → | Exists? | Trigger | Notes |
|--------------|------------|---------|---------|-------|
| IDLE | COMMISSIONING_MODE_READY | ✅ | enable_commissioning_mode | User action |
| COMMISSIONING_MODE_READY | IDLE | ✅ | disable_commissioning_mode | User action |
| SELECTED | ❓ | ⚠️ | disable_commissioning_mode | **Spec unclear** - disable during session? |
| TRANSPORT_ACTIVE | ❓ | ⚠️ | disable_commissioning_mode | **Spec unclear** - disable during transport? |

---

## State-by-State Command Coverage

### IDLE State

| Command | Transition | Status |
|---------|------------|--------|
| enable_commissioning_mode | → COMMISSIONING_MODE_READY | ✅ |
| SELECT | → ERROR_NOT_IN_COMMISSIONING or stay IDLE (ignore) | ✅ |
| TRANSPORT | → ERROR_INVALID_STATE | ✅ |
| GET_RESPONSE | → ??? | ❌ MISSING |

---

### COMMISSIONING_MODE_READY State

| Command | Transition | Status |
|---------|------------|--------|
| disable_commissioning_mode | → IDLE | ✅ |
| SELECT (valid AID) | → SELECTED | ✅ |
| SELECT (invalid AID) | → ERROR_INVALID_AID | ✅ |
| TRANSPORT | → ERROR_INVALID_STATE | ✅ |
| GET_RESPONSE | → ??? | ❌ MISSING |

---

### SELECTED State

| Command | Transition | Status |
|---------|------------|--------|
| SELECT | → ??? | ❌ MISSING (re-selection) |
| TRANSPORT (unchained, response fits) | → TRANSPORT_ACTIVE | ✅ |
| TRANSPORT (unchained, response exceeds Le) | → RESPONSE_INCOMPLETE | ✅ |
| TRANSPORT (chained, Lc <= max) | → CHAINING_IN_PROGRESS_RECEIVING | ✅ |
| TRANSPORT (chained, Lc > max) | → ERROR_MEMORY_EXCEEDED | ✅ |
| GET_RESPONSE | → ERROR_SEQUENCING | ✅ |
| timer_tick (timeout) | → SESSION_TIMEOUT | ✅ |
| timer_tick (no timeout) | → SELECTED (stay) | ✅ |

---

### TRANSPORT_ACTIVE State

| Command | Transition | Status |
|---------|------------|--------|
| SELECT | → ??? | ❌ MISSING (re-selection) |
| TRANSPORT (unchained, response fits) | → TRANSPORT_ACTIVE | ✅ |
| TRANSPORT (unchained, response exceeds Le) | → RESPONSE_INCOMPLETE | ✅ |
| TRANSPORT (chained, Lc <= max) | → CHAINING_IN_PROGRESS_RECEIVING | ✅ |
| TRANSPORT (chained, Lc > max) | → ERROR_MEMORY_EXCEEDED | 🟡 PARTIAL (missing explicit) |
| GET_RESPONSE | → ERROR_SEQUENCING | ✅ |
| timer_tick (timeout) | → SESSION_TIMEOUT | ✅ |
| timer_tick (no timeout) | → TRANSPORT_ACTIVE (stay) | ✅ |

---

### CHAINING_IN_PROGRESS_RECEIVING State

| Command | Transition | Status |
|---------|------------|--------|
| SELECT | → ??? | ❌ MISSING (SELECT during chaining) |
| TRANSPORT (chained continuation, valid) | → CHAINING_IN_PROGRESS_RECEIVING | ✅ |
| TRANSPORT (chained continuation, memory exceeded) | → ERROR_MEMORY_EXCEEDED | ✅ |
| TRANSPORT (chained continuation, P1P2 inconsistent) | → ERROR_SEQUENCING | ✅ |
| TRANSPORT (last fragment, response fits) | → TRANSPORT_ACTIVE | ✅ |
| TRANSPORT (last fragment, response exceeds Le) | → RESPONSE_INCOMPLETE | ✅ |
| GET_RESPONSE | → ERROR_SEQUENCING | ✅ |
| timer_tick (timeout) | → SESSION_TIMEOUT | ✅ |
| timer_tick (no timeout) | → CHAINING_IN_PROGRESS_RECEIVING (stay) | ✅ |

---

### RESPONSE_INCOMPLETE State

| Command | Transition | Status |
|---------|------------|--------|
| SELECT | → ??? | ❌ MISSING (SELECT during GET_RESPONSE) |
| TRANSPORT | → ??? | ❌ MISSING (TRANSPORT during GET_RESPONSE) |
| GET_RESPONSE (more fragments) | → RESPONSE_INCOMPLETE | ✅ |
| GET_RESPONSE (last fragment) | → TRANSPORT_ACTIVE | ✅ |
| timer_tick (timeout) | → SESSION_TIMEOUT | ✅ |
| timer_tick (no timeout) | → RESPONSE_INCOMPLETE (stay) | ✅ |

---

### ERROR States (all ERROR_* states)

| Command | Transition | Status |
|---------|------------|--------|
| SELECT | → ??? | ❌ MISSING (recovery or stay in error?) |
| TRANSPORT | → ??? | ❌ MISSING (repeat error or ignore?) |
| GET_RESPONSE | → ??? | ❌ MISSING (repeat error or ignore?) |
| timer_tick (error timeout) | → ??? | ❌ MISSING (cleanup to IDLE?) |

**Specific Error States:**
- ERROR_NOT_IN_COMMISSIONING
- ERROR_MEMORY_EXCEEDED
- ERROR_SEQUENCING
- ERROR_INVALID_AID
- ERROR_INVALID_STATE

**All have same gap:** No exit paths defined.

---

### SESSION_TIMEOUT State

| Command/Trigger | Transition | Status |
|-----------------|------------|--------|
| (any command) | → ??? | ❌ MISSING (state after timeout?) |
| (implicit) | → IDLE | ❌ MISSING (cleanup transition) |

---

## Summary Statistics

### Transitions by Status

| Status | Count | Percentage |
|--------|-------|------------|
| ✅ Fully Covered | 47 | ~73% |
| 🟡 Partially Covered | 2 | ~3% |
| ❌ Missing | 15 | ~23% |
| ➖ Not Applicable | 5 | (excluded) |

### Coverage by State

| State | Covered Transitions | Missing Transitions | Coverage % |
|-------|---------------------|---------------------|------------|
| IDLE | 3 | 1 | 75% |
| COMMISSIONING_MODE_READY | 4 | 1 | 80% |
| SELECTED | 7 | 1 | 88% |
| TRANSPORT_ACTIVE | 7 | 2 | 78% |
| CHAINING_IN_PROGRESS_RECEIVING | 8 | 1 | 89% |
| RESPONSE_INCOMPLETE | 4 | 2 | 67% |
| ERROR_* (all 5 states) | 0 | ~4 each | 0% |
| SESSION_TIMEOUT | 0 | 2 | 0% |

### Coverage by Command

| Command | Covered From States | Missing From States | Coverage % |
|---------|---------------------|---------------------|------------|
| SELECT | 4 states | 8 states | 33% |
| TRANSPORT (unchained) | 5 states | 3 states | 63% |
| TRANSPORT (chained) | 5 states | 2 states | 71% |
| GET_RESPONSE | 4 states | 3 states | 57% |
| timer_tick | 8 states | 6 states | 57% |

---

## Critical Missing Transitions (Priority 1)

1. **SELECT from SELECTED** → ERROR_SEQUENCING or session restart
2. **SELECT from TRANSPORT_ACTIVE** → ERROR_SEQUENCING
3. **SELECT from CHAINING_IN_PROGRESS_RECEIVING** → ERROR_SEQUENCING (+ clear fragments)
4. **SELECT from RESPONSE_INCOMPLETE** → ERROR_SEQUENCING (+ clear response buffer)
5. **TRANSPORT (chained) from TRANSPORT_ACTIVE with Lc > max** → ERROR_MEMORY_EXCEEDED
6. **TRANSPORT from RESPONSE_INCOMPLETE** → ERROR_SEQUENCING
7. **GET_RESPONSE from IDLE** → ERROR_INVALID_STATE
8. **GET_RESPONSE from COMMISSIONING_MODE_READY** → ERROR_INVALID_STATE
9. **timer_tick from ERROR_* states (timeout)** → IDLE (cleanup)
10. **SESSION_TIMEOUT exit** → IDLE

---

## Transition Guard Complexity

### Simple Guards (boolean checks)
- `commissioning_mode == true/false` - 4 transitions
- `session_state == ...` - 15 transitions
- `CLA == 0x80/0x90` - 12 transitions
- `aid == correct_value` - 2 transitions

### Complex Guards (arithmetic, comparisons)
- `(P1 << 8 | P2) == Lc` - 6 transitions (unchained)
- `(P1 << 8 | P2) > Lc` - 6 transitions (chained)
- `(P1 << 8 | P2) == P1P2_value` - 4 transitions (consistency)
- `fragments_received_length + Lc <= max_supported_size` - 3 transitions
- `response_size(...) <= Le` - 6 transitions
- `response_remaining > Le` - 2 transitions
- `paftp_idle_timer >= 30000` - 4 transitions

**All guards are deterministic and exclusive within trigger context** ✅

---

## Recommended Transition Additions

### Add These Transitions to FSM

```json
// 1. SELECT re-selection errors
{"from": "SELECTED", "to": "ERROR_SEQUENCING", "trigger": "SELECT_command", "guard": "session_state == SELECTED", "action": "send_error_response(0x69, 0x85)"},
{"from": "TRANSPORT_ACTIVE", "to": "ERROR_SEQUENCING", "trigger": "SELECT_command", "guard": "session_state == TRANSPORT_ACTIVE", "action": "send_error_response(0x69, 0x85)"},
{"from": "CHAINING_IN_PROGRESS_RECEIVING", "to": "ERROR_SEQUENCING", "trigger": "SELECT_command", "guard": "session_state == CHAINING_IN_PROGRESS", "action": ["send_error_response(0x69, 0x85)", "clear_fragment_buffer()", "chaining_active := false"]},
{"from": "RESPONSE_INCOMPLETE", "to": "ERROR_SEQUENCING", "trigger": "SELECT_command", "guard": "session_state == RESPONSE_INCOMPLETE", "action": ["send_error_response(0x69, 0x85)", "clear_response_buffer()"]},

// 2. Memory exceeded from TRANSPORT_ACTIVE
{"from": "TRANSPORT_ACTIVE", "to": "ERROR_MEMORY_EXCEEDED", "trigger": "TRANSPORT_command", "guard": "CLA == 0x90 && Lc > max_supported_size", "action": "send_error_response(0x6A, 0x84)"},

// 3. TRANSPORT in wrong state
{"from": "RESPONSE_INCOMPLETE", "to": "ERROR_SEQUENCING", "trigger": "TRANSPORT_command", "guard": "session_state == RESPONSE_INCOMPLETE", "action": ["send_error_response(0x69, 0x85)", "clear_response_buffer()"]},

// 4. GET_RESPONSE in wrong state
{"from": "IDLE", "to": "ERROR_INVALID_STATE", "trigger": "GET_RESPONSE_command", "guard": "session_state == IDLE", "action": "send_error_response(0x69, 0x85)"},
{"from": "COMMISSIONING_MODE_READY", "to": "ERROR_INVALID_STATE", "trigger": "GET_RESPONSE_command", "guard": "session_state == IDLE", "action": "send_error_response(0x69, 0x85)"},

// 5. Error state timeout cleanup
{"from": "ERROR_NOT_IN_COMMISSIONING", "to": "IDLE", "trigger": "timer_tick", "guard": "error_timer >= 5000", "action": "clear_error_state()"},
{"from": "ERROR_MEMORY_EXCEEDED", "to": "IDLE", "trigger": "timer_tick", "guard": "error_timer >= 5000", "action": "clear_error_state()"},
{"from": "ERROR_SEQUENCING", "to": "IDLE", "trigger": "timer_tick", "guard": "error_timer >= 5000", "action": "clear_error_state()"},
{"from": "ERROR_INVALID_AID", "to": "IDLE", "trigger": "timer_tick", "guard": "error_timer >= 5000", "action": "clear_error_state()"},
{"from": "ERROR_INVALID_STATE", "to": "IDLE", "trigger": "timer_tick", "guard": "error_timer >= 5000", "action": "clear_error_state()"},

// 6. Session timeout cleanup
{"from": "SESSION_TIMEOUT", "to": "IDLE", "trigger": "cleanup", "guard": "true", "action": "clear_session_state()"}
```

---

**Matrix Generated:** 2026-02-13  
**Total Transitions Analyzed:** 64  
**Existing Transitions:** 47  
**Missing Transitions:** 15  
**Partially Covered:** 2

