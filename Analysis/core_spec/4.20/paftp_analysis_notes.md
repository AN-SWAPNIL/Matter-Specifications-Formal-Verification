# PAFTP FSM Extraction - Intermediate Analysis

## Constants
- PAFTP_CONN_RSP_TIMEOUT = 5 seconds
- PAFTP_ACK_TIMEOUT = 15 seconds
- PAFTP_CONN_IDLE_TIMEOUT = 30 seconds
- send_ack_timer_duration < PAFTP_ACK_TIMEOUT / 2 (< 7.5 seconds)
- Max window size = 255
- Max SDU size = 64KB (16-bit Message Length field)
- Default Supported Max Service Specific Info Length = 350 (if unknown)
- Handshake Control Flags = 0x65, Management Opcode = 0x6C
- Version values: 0=unused, 4=PAFTP v1.5

## Control Flags Layout (Table 38)
bit 7: reserved (-)
bit 6: H (Handshake)
bit 5: M (Management Message)
bit 4: reserved (-)  
bit 3: A (Acknowledgement)
bit 2: E (Ending Segment)
bit 1: C (Continuing Segment)
bit 0: B (Beginning Segment)

0x65 = 01100101 → H=1, M=1, E=1, B=1, A=0, C=0

## Timers
1. conn_rsp_timer: Started by Commissioner on sending handshake request. Duration = PAFTP_CONN_RSP_TIMEOUT (5s). Expiry → close session.
2. ack_received_timer (ack-rx): Per peer. Started on sending any packet (if not running). Duration = PAFTP_ACK_TIMEOUT (15s). Restart on valid ack for non-most-recent. Stop on ack for most recent. Expiry → close session. Device starts on sending handshake response.
3. send_ack_timer (ack-tx): Per peer. Started on receiving any packet (if not running). Duration < 7.5s. On expiry with pending ack → immediately send ack. Restart on pending ack sent for non-largest received. Stop on pending ack sent for largest received. Client starts on receiving handshake response (pending_ack = 0).
4. idle_timeout: PAFTP_CONN_IDLE_TIMEOUT (30s). Commissioner must close if no unique data sent for this duration.

## SHALL Requirements Enumerated

### Overview (4.20)
S01: MATTERoPAF Interface SHALL implement PAFTP.
S02: MATTERoPAF Interface SHALL only transport Matter messages as PAFTP SDU.

### Frame Format (4.20.2)
S03: Unused fields SHALL be set to '0'.
S04: All segments of a message SHALL set M bit to same value.

### Session Establishment (4.20.3.3)
S05: Commissioner SHALL first establish WFA-USD connection before PAFTP session.
S06: Commissioner SHALL send handshake request to initiate.
S07: Request SHALL include: supported versions, supported max SSI length, max window size.
S08: Version list SHALL be sorted descending.
S09: Device SHALL send handshake response after receiving request.
S10: Response SHALL contain: window size, max selected packet size, protocol version.
S11: Device SHALL select window_size = min(device_max, commissioner_max).
S12: Device SHALL select max_packet_size = min(device_supported_ssi, commissioner_supported_ssi).
S13: Device SHALL select newest common version (numerically largest).
S14: Version in response SHALL determine protocol version for session duration.
S15: If no common version → Device SHALL close WFA-USD connection.
S16: Commissioner SHALL start conn_rsp_timer on sending request.
S17: If conn_rsp_timer expires → Commissioner SHALL close PAFTP session and report error.
S18: If PAFTP not aware of Supported Max SSI Length → SHALL be set to 350 (handshake request).
S19: If PAFTP not aware of Supported Max SSI Length → SHALL be set to 350 (handshake response).
S20: Reserved field in handshake response must be set to 0.

### Data Transmission (4.20.3.4)
S21: All packets SHALL adhere to PAFTP Packet PDU format.
S22: All packets SHALL include header flags byte and 8-bit sequence number.
S23: Concurrent sessions SHALL maintain separate/independent timers, seq nums, windows.

### Message Segmentation (4.20.3.5)
S24: SDU SHALL be split into ordered, non-overlapping segments.
S25: Each segment SHALL be prepended with PAFTP packet header.
S26: Segments SHALL be sent in order of position (head first).
S27: Segments of two SDUs SHALL NOT overlap (one SDU per direction at a time).
S28: New SDU during transmission SHALL be appended to FIFO queue.
S29: Next SDU SHALL be dequeued when current completes (all segments transmitted and acked).
S30: First segment SHALL have B (Beginning) flag set.
S31: B flag SHALL indicate Message Length field presence.
S32: Last segment SHALL have E (Ending) flag set.
S33: Single-segment SDU SHALL have both B and E flags set.
S34: Non-ending segment payload length SHALL equal max_packet_size - header_size.
S35: Ending segment payload length SHALL equal SDU_size - sum(previous_segments).
S36: Peer SHALL reassemble in ascending sequence number order.
S37: SHALL verify reassembled length matches Message Length.
S38: If match → SHALL pass reassembled SDU to next higher layer.
S39: If mismatch → SHALL close session and report error.
S40: If segment payload exceeds max packet size → SHALL close session and report error.
S41: If Ending received without previous Beginning → SHALL close session and report error.
S42: If Beginning received during in-progress SDU → SHALL close session and report error.

### Sequence Numbers (4.20.3.6)
S43: All packets SHALL have sequence numbers (including standalone acks).
S44: Sequence number SHALL be uint8, monotonically incrementing by 1.
S45: Sequence past 255 SHALL wrap to 0.
S46: Sequences SHALL be separate for each direction.
S47: Commissioner first packet after handshake SHALL be seq 0.
S48: Device first data packet after handshake SHALL be seq 1 (handshake response = implicit seq 0).
S49: Peers SHALL check proper seq increment by 1.
S50: If seq check fails → SHALL close session and report error.

### Receive Windows (4.20.3.7)
S51: Both peers SHALL define receive window.
S52: Max window size SHALL be established in handshake.
S53: Both SHALL maintain counter of remote peer's window.
S54: SHALL decrement counter on send.
S55: SHALL increment counter on ack received.
S56: If counter = 0 → window closed, SHALL NOT send until reopens.
S57: On reopen → SHALL immediately resume pending transmission.
S58: SHALL NOT send if remote window = 1 AND no pending ack (deadlock prevention).
S59: Device SHALL init Commissioner window counter = negotiated_max - 1.
S60: Commissioner SHALL init Device window counter = negotiated_max.
S61: Both SHALL keep counter of own receive window size.

### Acknowledgements (4.20.3.8)
S62: Ack SHALL be uint8 in header.
S63: Ack value SHALL indicate seq number of acknowledged packet.
S64: Standalone acks SHALL be acknowledged by remote peer.
S65: SHALL maintain ack-received timer.
S66: SHALL start ack-rx timer on sending any packet (if not running).
S67: Timer duration SHALL = PAFTP_ACK_TIMEOUT.
S68: SHALL restart ack-rx timer on valid ack for non-most-recent.
S69: SHALL stop ack-rx timer on ack for most recently sent unacknowledged packet.
S70: If ack-rx timer expires → SHALL close session and report error.
S71: If invalid ack received → SHALL close session and report error.
S72: Device SHALL start ack-rx timer when sending handshake response.
S73: SHALL maintain send-ack timer.
S74: On receiving packet → SHALL record seq as pending ack value, start send-ack timer (if not running).
S75: Send-ack timer duration SHALL < PAFTP_ACK_TIMEOUT / 2.
S76: SHALL restart send-ack timer on pending ack sent for non-largest received.
S77: SHALL stop send-ack timer on pending ack sent for largest received.
S78: On send-ack timer expiry with pending ack → SHALL immediately send ack.
S79: Ack number SHALL be contiguous (seq of which all previous contiguous seqs received).
S80: If sending before send-ack expiry → SHALL piggyback any pending ack.
S81: Piggybacked ack number SHALL be contiguous.
S82: Commissioner SHALL set pending_ack = 0 and start send-ack timer on receiving handshake response.
S83: If own receive window ≤ 2 free slots → SHALL immediately send pending ack.
S84: That ack number SHALL be contiguous.

## State Machines from Spec Diagrams

### Figure 33: Commissioner Lifecycle
States: Disconnected, WFA-USD connection formed, Capabilities request sent, wait on capabilities response, Connected
Transitions:
- [*] → Disconnected
- Disconnected → WFA-USD connection formed: WFA-USD discovery issued
- WFA-USD connection formed → Capabilities request sent: Send PAFTP capabilities request
- Capabilities request sent → wait on capabilities response: PAFTP capabilities response wait initiated
- wait on capabilities response → Connected: PAFTP capabilities response received
- wait on capabilities response → Disconnected: PAFTP connection response timed out  
- Connected → Disconnected: Close WFA-USD connection

### Figure 34: Device Lifecycle
States: Disconnected advertising, WFA-USD connection formed, Wait on capabilities request, Prepared capabilities response, Connected
Transitions:
- [*] → Disconnected advertising
- Disconnected advertising → WFA-USD connection formed: WFA-USD discovery issued
- WFA-USD connection formed → Wait on capabilities request: PAFTP capabilities request wait initiated
- Wait on capabilities request → Prepared capabilities response: PAFTP capabilities request received
- Prepared capabilities response → Connected: PAFTP capabilities response sent
- Prepared capabilities response → Disconnected advertising: PAFTP connection response timed out
- Connected → Disconnected advertising: Close WFA-USD connection

### Figure 35: Post-Establishment Session
States: CommissionerState (ack-rx stopped, ack-tx ticking), DeviceState (ack-rx ticking, ack-tx stopped), BothTicking (both ticking), Closing
Transitions:
- [*] → CommissionerState (Commissioner entry)
- [*] → DeviceState (Device entry)
- CommissionerState → CommissionerState: Any packet received
- CommissionerState → DeviceState: standalone ack-tx OR piggyback ack-tx on msg segment
- DeviceState → CommissionerState: standalone ack-rx OR piggyback ack-rx for most recent segment
- DeviceState → DeviceState: standalone ack-tx OR piggyback ack-tx on msg segment
- DeviceState → BothTicking: packet-rx without ack
- BothTicking → DeviceState: standalone ack-rx OR piggyback ack-rx for most recent segment
- BothTicking → BothTicking: Any packet without ack either tx or rx
- CommissionerState → BothTicking: standalone ack-rx OR piggyback ack-rx for most recent segment [NOTE: ambiguous per spec text]
- BothTicking → Closing: ack-rx timer fires
- DeviceState → Closing: standalone ack-tx OR piggyback ack-tx on msg segment [NOTE: spec has same trigger for self-loop and closing—implicit guard]
- DeviceState → Closing: ack-rx timer fires OR app closes PAFTP connection
- Closing → [*]: PAFTP connection closed

## Implicit States from Behavioral Descriptions

### TX States (per-peer, per-direction)
- TX_Idle: No SDU transmission in progress
- TX_Sending_SDU: SDU being segmented and transmitted (sub: beginning sent, middle, ending)
- TX_SDU_Queued: Additional SDUs queued in FIFO

### RX States (per-peer, per-direction)  
- RX_Idle: No SDU reception in progress
- RX_Reassembling: Beginning segment received, accumulating segments
- RX_Verification: All segments received, verifying length match
- RX_Error: Reassembly error detected → close session

## Notes on Figure 35 Ambiguity

DeviceState has BOTH:
- Self-loop: "standalone ack-tx OR piggyback ack-tx on msg segment"  
- Transition to Closing: "standalone ack-tx OR piggyback ack-tx on msg segment"

These have identical trigger labels. This implies an implicit guard condition differentiating them.
Interpretation: The self-loop is the normal case; the Closing transition may represent an error condition detected during the ack send (e.g., invalid state, protocol error). Will model with guard conditions noting this spec ambiguity.
