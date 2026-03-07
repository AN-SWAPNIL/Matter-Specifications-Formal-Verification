# Network Recovery FSM Analysis

## Section: 5.9 Network Recovery

### Key Behavioral Elements

#### Attributes/Variables
1. **operational_network_connected**: boolean - whether node has access to operational network
2. **recovery_identifier**: attribute from GeneralCommissioning cluster
3. **reconnection_timer**: duration timer (minimum 120 seconds)
4. **in_recovery_mode**: boolean - whether node is in network recovery mode
5. **announcement_active**: boolean - whether recovery announcement is active
6. **extended_announcement_timer**: timer for extended announcement duration
7. **fail_safe_timer**: 60 second timer for fail-safe
8. **case_session_established**: boolean - CASE session over recovery channel
9. **case_session_over_operational**: boolean - CASE session over operational network
10. **new_credentials_stored**: boolean - new network credentials received
11. **user_consent_granted**: boolean - administrator has user consent
12. **recovery_connection_type**: string - "BLE" or "WiFi"
13. **autonomous_reconnect_suspended**: boolean - reconnection attempts suspended
14. **operational_discovery_complete**: boolean - discovered on operational network
15. **current_credentials**: network credentials object
16. **new_credentials**: network credentials object
17. **reconnect_interval**: manufacturer-defined interval for reconnection attempts

#### Commands/Triggers
1. **network_credentials_changed** - operational network credentials changed
2. **reconnection_timer_expired** - 120 second timer expires
3. **extended_announcement_expired** - extended announcement period ends
4. **commissioning_mode_steps_performed** - CommissioningModeInitialStepsHint steps performed
5. **administrator_connects** - administrator establishes recovery connection
6. **establish_case** - CASE session establishment initiated
7. **ArmFailSafe** - command to arm fail-safe timer
8. **RemoveNetwork** - command to remove existing credentials
9. **AddOrUpdateWiFiNetwork** - command to add/update WiFi credentials
10. **AddOrUpdateThreadNetwork** - command to add/update Thread credentials
11. **ConnectNetwork** - command to connect to network with new credentials
12. **CommissioningComplete** - command to complete recovery
13. **connection_successful** - node successfully connected to operational network
14. **connection_failed** - connection attempt failed
15. **operational_discovery_success** - operational discovery succeeded
16. **fail_safe_timeout** - fail-safe timer reached zero

### States

#### State 1: NormalOperation
- **Description**: Node is connected and operational on the network
- **Is Initial**: true
- **Invariants**: 
  - operational_network_connected == true
  - in_recovery_mode == false
- **State Variables**:
  - current_credentials: network_credentials
  - recovery_identifier: attribute_value

#### State 2: ConnectivityLost
- **Description**: Node lost network connectivity, attempting reconnection with existing credentials
- **Is Initial**: false
- **Invariants**:
  - operational_network_connected == false
  - reconnection_timer > 0
  - in_recovery_mode == false
- **State Variables**:
  - reconnection_timer: integer (seconds)
  - current_credentials: network_credentials

#### State 3: RecoveryModeAnnouncing
- **Description**: Node is in recovery mode, advertising recovery payload
- **Is Initial**: false
- **Invariants**:
  - operational_network_connected == false
  - in_recovery_mode == true
  - announcement_active == true
- **State Variables**:
  - recovery_identifier: attribute_value
  - announcement_channels: list (BLE, WiFi)
  - extended_announcement_timer: integer

#### State 4: ExtendedAnnouncementActive
- **Description**: Node is in extended announcement period
- **Is Initial**: false
- **Invariants**:
  - operational_network_connected == false
  - in_recovery_mode == true
  - extended_announcement_timer > 0
- **State Variables**:
  - extended_announcement_timer: integer
  - autonomous_reconnect_active: boolean

#### State 5: PeriodicReconnectionAttempts
- **Description**: Extended announcement ended, making periodic reconnection attempts
- **Is Initial**: false
- **Invariants**:
  - operational_network_connected == false
  - in_recovery_mode == false
  - extended_announcement_timer == 0
- **State Variables**:
  - reconnect_interval: integer
  - current_credentials: network_credentials

#### State 6: RecoveryConnectionEstablished
- **Description**: Administrator established recovery connection (BLE or WiFi)
- **Is Initial**: false
- **Invariants**:
  - recovery_connection_active == true
  - user_consent_granted == true
  - case_session_established == false
- **State Variables**:
  - recovery_connection_type: string ("BLE" or "WiFi")
  - administrator_id: identifier

#### State 7: CASESessionActive
- **Description**: CASE session established over recovery channel, fail-safe auto-armed
- **Is Initial**: false
- **Invariants**:
  - case_session_established == true
  - case_session_over_operational == false
  - fail_safe_timer > 0
  - autonomous_reconnect_suspended == true
- **State Variables**:
  - fail_safe_timer: integer (60 seconds)
  - case_session_id: identifier

#### State 8: FailSafeArmed
- **Description**: Administrator explicitly armed fail-safe timer
- **Is Initial**: false
- **Invariants**:
  - fail_safe_timer > 0
  - case_session_established == true
  - administrator_armed_fail_safe == true
- **State Variables**:
  - fail_safe_timer: integer

#### State 9: NewCredentialsProvisioned
- **Description**: New network credentials received and stored
- **Is Initial**: false
- **Invariants**:
  - new_credentials_stored == true
  - fail_safe_timer > 0
- **State Variables**:
  - new_credentials: network_credentials
  - old_credentials_removed: boolean

#### State 10: ConnectingToNewNetwork
- **Description**: Attempting to connect to operational network with new credentials
- **Is Initial**: false
- **Invariants**:
  - new_credentials_stored == true
  - connection_attempt_in_progress == true
- **State Variables**:
  - new_credentials: network_credentials
  - connection_status: string

#### State 11: OperationalDiscovery
- **Description**: Connected to operational network, performing operational discovery
- **Is Initial**: false
- **Invariants**:
  - operational_network_connected == true
  - case_session_over_operational == false
  - operational_discovery_in_progress == true
- **State Variables**:
  - operational_network_connection: connection_object

#### State 12: RecoveryCompleteReady
- **Description**: Operational discovery complete, ready for CommissioningComplete
- **Is Initial**: false
- **Invariants**:
  - operational_network_connected == true
  - operational_discovery_complete == true
  - case_session_over_operational == true
- **State Variables**:
  - case_session_operational: session_object

#### State 13: RecoveryConnectionTerminated
- **Description**: Recovery connection terminated due to fail-safe timeout or error
- **Is Initial**: false
- **Invariants**:
  - recovery_connection_active == false
  - case_session_established == false
- **State Variables**:
  - termination_reason: string

#### State 14: RecoveryFlowAborted
- **Description**: Recovery flow aborted (no user consent or other failure)
- **Is Initial**: false
- **Invariants**:
  - in_recovery_mode == false
  - recovery_aborted == true
- **State Variables**:
  - abort_reason: string

#### State 15: ConnectionToNewNetworkFailed
- **Description**: Failed to connect to operational network with new credentials
- **Is Initial**: false
- **Invariants**:
  - connection_attempt_failed == true
  - fail_safe_timer > 0
- **State Variables**:
  - connection_error: string

### Transitions

#### T1: Normal to Connectivity Lost
- **From**: NormalOperation
- **To**: ConnectivityLost
- **Trigger**: network_credentials_changed
- **Guard**: operational_network_connected == false
- **Actions**:
  - reconnection_timer := 120
  - in_recovery_mode := false
  - attempt_network_connection(current_credentials)
- **Timing**: immediate

#### T2: Connectivity Lost - Stay (Reconnection Attempts)
- **From**: ConnectivityLost
- **To**: ConnectivityLost
- **Trigger**: reconnection_attempt_interval
- **Guard**: reconnection_timer > 0 && operational_network_connected == false
- **Actions**:
  - reconnection_timer := reconnection_timer - interval
  - attempt_network_connection(current_credentials)
- **Timing**: continuous for at least 120 seconds

#### T3: Connectivity Lost to Recovery Success
- **From**: ConnectivityLost
- **To**: NormalOperation
- **Trigger**: connection_successful
- **Guard**: operational_network_connected == true && reconnection_timer > 0
- **Actions**:
  - reconnection_timer := 0
  - in_recovery_mode := false
- **Timing**: within 120 seconds

#### T4: Connectivity Lost to Recovery Mode
- **From**: ConnectivityLost
- **To**: RecoveryModeAnnouncing
- **Trigger**: reconnection_timer_expired
- **Guard**: reconnection_timer >= 120 && operational_network_connected == false
- **Actions**:
  - in_recovery_mode := true
  - announcement_active := true
  - advertise_recovery_payload(recovery_identifier)
  - extended_announcement_timer := get_extended_announcement_duration()
- **Timing**: after 120 seconds minimum

#### T5: Recovery Mode to Extended Announcement
- **From**: RecoveryModeAnnouncing
- **To**: ExtendedAnnouncementActive
- **Trigger**: announcement_duration_reached
- **Guard**: announcement_active == true && extended_announcement_timer > 0
- **Actions**:
  - continue_extended_announcement()
  - attempt_network_connection(current_credentials)
- **Timing**: after initial announcement duration

#### T6: Extended Announcement to Periodic Reconnection
- **From**: ExtendedAnnouncementActive
- **To**: PeriodicReconnectionAttempts
- **Trigger**: extended_announcement_expired
- **Guard**: extended_announcement_timer == 0 && operational_network_connected == false
- **Actions**:
  - announcement_active := false
  - in_recovery_mode := false
  - set_manufacturer_reconnect_interval(reconnect_interval)
- **Timing**: after extended announcement duration ends

#### T7: Periodic Reconnection Stay
- **From**: PeriodicReconnectionAttempts
- **To**: PeriodicReconnectionAttempts
- **Trigger**: reconnect_interval_reached
- **Guard**: operational_network_connected == false
- **Actions**:
  - attempt_network_connection(current_credentials)
- **Timing**: at manufacturer-defined intervals

#### T8: Periodic Reconnection to Recovery Mode Restart
- **From**: PeriodicReconnectionAttempts
- **To**: RecoveryModeAnnouncing
- **Trigger**: commissioning_mode_steps_performed
- **Guard**: true
- **Actions**:
  - in_recovery_mode := true
  - announcement_active := true
  - advertise_recovery_payload(recovery_identifier)
  - extended_announcement_timer := get_extended_announcement_duration()
- **Timing**: when CommissioningModeInitialStepsHint steps performed

#### T9: Recovery Mode to Connection (No Consent)
- **From**: RecoveryModeAnnouncing
- **To**: RecoveryFlowAborted
- **Trigger**: administrator_connects
- **Guard**: user_consent_granted == false
- **Actions**:
  - abort_recovery_flow()
  - abort_reason := "no_user_consent"
  - announcement_active := false
- **Timing**: when administrator attempts connection

#### T10: Recovery Mode to Connection Established
- **From**: RecoveryModeAnnouncing
- **To**: RecoveryConnectionEstablished
- **Trigger**: administrator_connects
- **Guard**: user_consent_granted == true
- **Actions**:
  - recovery_connection_active := true
  - recovery_connection_type := get_connection_type()
  - announcement_active := false
- **Timing**: when administrator establishes connection

#### T11: Extended Announcement to Connection (No Consent)
- **From**: ExtendedAnnouncementActive
- **To**: RecoveryFlowAborted
- **Trigger**: administrator_connects
- **Guard**: user_consent_granted == false
- **Actions**:
  - abort_recovery_flow()
  - abort_reason := "no_user_consent"
  - announcement_active := false
- **Timing**: when administrator attempts connection

#### T12: Extended Announcement to Connection Established
- **From**: ExtendedAnnouncementActive
- **To**: RecoveryConnectionEstablished
- **Trigger**: administrator_connects
- **Guard**: user_consent_granted == true
- **Actions**:
  - recovery_connection_active := true
  - recovery_connection_type := get_connection_type()
  - announcement_active := false
  - extended_announcement_timer := 0
- **Timing**: when administrator establishes connection

#### T13: Connection Established to CASE Session
- **From**: RecoveryConnectionEstablished
- **To**: CASESessionActive
- **Trigger**: establish_case
- **Guard**: recovery_connection_active == true
- **Actions**:
  - case_session_id := establish_case_session(recovery_connection_type)
  - case_session_established := true
  - case_session_over_operational := false
  - autonomous_reconnect_suspended := true
  - fail_safe_timer := 60
  - auto_arm_fail_safe(60)
- **Timing**: after recovery connection established

#### T14: CASE Session to Fail-Safe Armed
- **From**: CASESessionActive
- **To**: FailSafeArmed
- **Trigger**: ArmFailSafe
- **Guard**: fail_safe_timer > 0 && case_session_established == true
- **Actions**:
  - administrator_armed_fail_safe := true
  - reset_fail_safe_timer(60)
- **Timing**: within 60 seconds of CASE establishment

#### T15: CASE Session to Terminated (Timeout)
- **From**: CASESessionActive
- **To**: RecoveryConnectionTerminated
- **Trigger**: fail_safe_timeout
- **Guard**: fail_safe_timer == 0 && administrator_armed_fail_safe == false
- **Actions**:
  - terminate_case_session(case_session_id)
  - case_session_established := false
  - recovery_connection_active := false
  - autonomous_reconnect_suspended := false
  - termination_reason := "fail_safe_timeout"
- **Timing**: 60 seconds after CASE establishment if ArmFailSafe not received

#### T16: Fail-Safe Armed to New Credentials (Optional Remove)
- **From**: FailSafeArmed
- **To**: FailSafeArmed
- **Trigger**: RemoveNetwork
- **Guard**: fail_safe_timer > 0
- **Actions**:
  - remove_network_credentials(network_id)
  - old_credentials_removed := true
- **Timing**: during fail-safe period

#### T17: Fail-Safe Armed to New Credentials Provisioned
- **From**: FailSafeArmed
- **To**: NewCredentialsProvisioned
- **Trigger**: AddOrUpdateWiFiNetwork OR AddOrUpdateThreadNetwork
- **Guard**: fail_safe_timer > 0
- **Actions**:
  - new_credentials := store_network_credentials(credentials)
  - new_credentials_stored := true
  - generate_event(network_config_response)
- **Timing**: during fail-safe period

#### T18: New Credentials to Connecting
- **From**: NewCredentialsProvisioned
- **To**: ConnectingToNewNetwork
- **Trigger**: ConnectNetwork
- **Guard**: new_credentials_stored == true && fail_safe_timer > 0
- **Actions**:
  - connection_attempt_in_progress := true
  - attempt_network_connection(new_credentials)
  - generate_event(connect_network_response)
- **Timing**: after new credentials provisioned

#### T19: Connecting to Operational Discovery (Success)
- **From**: ConnectingToNewNetwork
- **To**: OperationalDiscovery
- **Trigger**: connection_successful
- **Guard**: operational_network_connected == true
- **Actions**:
  - connection_attempt_in_progress := false
  - terminate_recovery_connection()
  - current_credentials := new_credentials
  - operational_discovery_in_progress := true
  - perform_operational_discovery()
- **Timing**: after connection attempt

#### T20: Connecting to Connection Failed
- **From**: ConnectingToNewNetwork
- **To**: ConnectionToNewNetworkFailed
- **Trigger**: connection_failed
- **Guard**: operational_network_connected == false && fail_safe_timer > 0
- **Actions**:
  - connection_attempt_in_progress := false
  - connection_error := get_connection_error()
  - generate_event(connection_failed_event)
- **Timing**: after connection attempt fails

#### T21: Connection Failed to Fail-Safe Armed
- **From**: ConnectionToNewNetworkFailed
- **To**: FailSafeArmed
- **Trigger**: retry_or_new_credentials
- **Guard**: fail_safe_timer > 0 && case_session_established == true
- **Actions**:
  - connection_error := null
- **Timing**: administrator can retry with different credentials

#### T22: Connection Failed to Terminated (Timeout)
- **From**: ConnectionToNewNetworkFailed
- **To**: RecoveryConnectionTerminated
- **Trigger**: fail_safe_timeout
- **Guard**: fail_safe_timer == 0
- **Actions**:
  - terminate_case_session(case_session_id)
  - case_session_established := false
  - recovery_connection_active := false
  - autonomous_reconnect_suspended := false
  - termination_reason := "fail_safe_timeout_after_connection_failure"
  - revert_to_old_credentials()
- **Timing**: when fail-safe expires

#### T23: Operational Discovery to Recovery Complete Ready
- **From**: OperationalDiscovery
- **To**: RecoveryCompleteReady
- **Trigger**: operational_discovery_success
- **Guard**: operational_discovery_complete == true
- **Actions**:
  - case_session_operational := establish_case_over_operational(administrator_id)
  - case_session_over_operational := true
  - operational_discovery_in_progress := false
- **Timing**: after operational discovery succeeds

#### T24: Recovery Complete Ready to Normal Operation
- **From**: RecoveryCompleteReady
- **To**: NormalOperation
- **Trigger**: CommissioningComplete
- **Guard**: verify_over_operational_network() == true && case_session_over_operational == true
- **Actions**:
  - send_commissioning_complete_response()
  - disarm_fail_safe()
  - fail_safe_timer := 0
  - in_recovery_mode := false
  - recovery_connection_active := false
  - case_session_established := false
  - operational_discovery_complete := false
  - generate_event(recovery_complete)
- **Timing**: when CommissioningComplete received over operational network

#### T25: Recovery Complete Ready Reject (Not Operational)
- **From**: RecoveryCompleteReady
- **To**: RecoveryCompleteReady
- **Trigger**: CommissioningComplete
- **Guard**: verify_over_operational_network() == false
- **Actions**:
  - reject_commissioning_complete("not_over_operational_network")
- **Timing**: when CommissioningComplete received over wrong channel

#### T26: Recovery Connection Terminated to Periodic Reconnection
- **From**: RecoveryConnectionTerminated
- **To**: PeriodicReconnectionAttempts
- **Trigger**: resume_autonomous_reconnect
- **Guard**: autonomous_reconnect_suspended == false
- **Actions**:
  - in_recovery_mode := false
  - set_manufacturer_reconnect_interval(reconnect_interval)
- **Timing**: after recovery connection terminated

#### T27: Recovery Aborted to Periodic Reconnection
- **From**: RecoveryFlowAborted
- **To**: PeriodicReconnectionAttempts
- **Trigger**: continue_attempts
- **Guard**: true
- **Actions**:
  - recovery_aborted := false
  - set_manufacturer_reconnect_interval(reconnect_interval)
- **Timing**: after administrator terminates without consent

### Function Definitions

#### F1: attempt_network_connection
- **Name**: attempt_network_connection
- **Parameters**: 
  - credentials: network_credentials_object (contains network name, password, type)
- **Returns**: connection_result (success/failure status)
- **Behavior**: Attempts to connect to the operational network using the provided credentials. Uses network-specific connection procedures (WiFi association, Thread attachment, etc.). Returns success if connection established, failure otherwise.
- **Algorithm Detail**: Network-layer specific. For WiFi: WPA2/WPA3 association with SSID and passphrase. For Thread: Thread network attachment using dataset credentials.
- **Usage in FSM**: Called in ConnectivityLost state (continuously), PeriodicReconnectionAttempts state (at intervals), and ConnectingToNewNetwork state (with new credentials).

#### F2: advertise_recovery_payload
- **Name**: advertise_recovery_payload
- **Parameters**:
  - recovery_identifier: attribute_value (from GeneralCommissioning.RecoveryIdentifier)
- **Returns**: void
- **Behavior**: Broadcasts network recovery advertisement over available commissioning channels (BLE and/or WiFi). Advertisement includes recovery identifier and error codes that led to need for recovery. Follows announcement duration requirements and extended announcement procedures.
- **Algorithm Detail**: 
  - BLE: Advertises using BLE Service Data payload format with OpCode indicating recovery mode
  - WiFi: Publishes recovery ID using WiFi Unsynchronized Service Discovery (Public Action Frame)
  - Advertisement distinguishes recovery from normal commissioning
- **Usage in FSM**: Called when entering RecoveryModeAnnouncing state to broadcast recovery availability.

#### F3: get_extended_announcement_duration
- **Name**: get_extended_announcement_duration
- **Parameters**: none
- **Returns**: integer (duration in seconds)
- **Behavior**: Returns the extended announcement duration as specified in Matter specification announcement duration requirements. This is the period during which the node continues to advertise its availability for recovery.
- **Algorithm Detail**: Returns specification-defined constant for extended announcement duration.
- **Usage in FSM**: Called when starting recovery announcement to determine how long to continue advertising.

#### F4: continue_extended_announcement
- **Name**: continue_extended_announcement
- **Parameters**: none
- **Returns**: void
- **Behavior**: Continues advertising recovery payload during extended announcement period while simultaneously attempting autonomous reconnection to existing operational network.
- **Algorithm Detail**: Maintains active advertisement over BLE/WiFi while parallel reconnection attempts occur.
- **Usage in FSM**: Called in ExtendedAnnouncementActive state to maintain advertisement.

#### F5: set_manufacturer_reconnect_interval
- **Name**: set_manufacturer_reconnect_interval
- **Parameters**:
  - interval: integer (seconds between reconnection attempts)
- **Returns**: void
- **Behavior**: Sets the manufacturer-defined interval at which the node will automatically attempt to reconnect to the operational network using existing credentials. Interval is implementation-specific.
- **Algorithm Detail**: Configures timer or scheduler for periodic reconnection attempts at manufacturer-chosen frequency.
- **Usage in FSM**: Called when entering PeriodicReconnectionAttempts state to schedule ongoing reconnection attempts.

#### F6: abort_recovery_flow
- **Name**: abort_recovery_flow
- **Parameters**: none
- **Returns**: void
- **Behavior**: Terminates the network recovery process. Stops all recovery advertisements, closes any recovery connections, and returns to autonomous reconnection attempt mode.
- **Algorithm Detail**: Clears recovery state, stops BLE/WiFi advertisements, closes connections.
- **Usage in FSM**: Called when administrator attempts connection without user consent (Step 7 of spec).

#### F7: get_connection_type
- **Name**: get_connection_type
- **Parameters**: none
- **Returns**: string ("BLE" or "WiFi")
- **Behavior**: Identifies which commissioning channel type (BLE or WiFi Public Action Frame) the administrator used to establish the recovery connection.
- **Algorithm Detail**: Queries the active recovery connection to determine its underlying transport type.
- **Usage in FSM**: Called when administrator establishes recovery connection to track connection type for CASE establishment.

#### F8: establish_case_session
- **Name**: establish_case_session
- **Parameters**:
  - connection_type: string ("BLE" or "WiFi")
- **Returns**: session_id (identifier for CASE session)
- **Behavior**: Establishes a Certificate Authenticated Session Establishment (CASE) secure session over the recovery connection channel. CASE performs mutual authentication using device certificates and derives session keys for encrypted communication. This is the same CASE protocol used for normal operational sessions but conducted over the commissioning channel.
- **Algorithm Detail**: 
  - CASE protocol as defined in Matter specification Section 4.13.2
  - Uses Device Attestation Certificate for node authentication
  - Uses Administrator's NOC (Node Operational Certificate) for administrator authentication
  - Derives session keys using CASE key derivation function
  - All subsequent messages encrypted with CASE-derived session keys
- **Cryptographic Detail**:
  - Algorithm: CASE (Certificate Authenticated Session Establishment)
  - Inputs: Device Attestation Certificate, Administrator NOC, random nonces
  - Outputs: Session ID, symmetric session encryption keys
  - Key Derivation: Uses HKDF with session ephemeral keys
  - Assumptions: Certificates are valid, private keys secure, CASE protocol is sound
- **Usage in FSM**: Called when transitioning from RecoveryConnectionEstablished to CASESessionActive.

#### F9: auto_arm_fail_safe
- **Name**: auto_arm_fail_safe
- **Parameters**:
  - duration: integer (60 seconds)
- **Returns**: void
- **Behavior**: Autonomously arms the fail-safe timer when CASE session is established. This is an automatic action by the Recovery Node (not commanded by administrator) to guard against administrator not proceeding with recovery in timely fashion. Timer is set to 60 seconds.
- **Algorithm Detail**: Starts 60-second countdown timer. If timer reaches zero before administrator sends ArmFailSafe command, session is terminated.
- **Usage in FSM**: Called automatically when CASE session established (Step 10 of spec).

#### F10: reset_fail_safe_timer
- **Name**: reset_fail_safe_timer
- **Parameters**:
  - duration: integer (60 seconds)
- **Returns**: void
- **Behavior**: Resets the fail-safe timer to specified duration. Called when administrator sends ArmFailSafe command to extend the fail-safe period and confirm intent to proceed with recovery.
- **Algorithm Detail**: Resets countdown timer to 60 seconds.
- **Usage in FSM**: Called when ArmFailSafe command received within initial 60-second window (Step 11 of spec).

#### F11: terminate_case_session
- **Name**: terminate_case_session
- **Parameters**:
  - session_id: identifier
- **Returns**: void
- **Behavior**: Terminates the CASE session, closes the recovery connection, destroys session keys, and resumes autonomous reconnection attempts. Called when fail-safe expires or recovery completes.
- **Algorithm Detail**: Securely destroys CASE session keys, closes transport connection, clears session state.
- **Cryptographic Detail**: Securely erases session encryption keys from memory.
- **Usage in FSM**: Called when fail-safe timer expires or recovery process terminates prematurely.

#### F12: remove_network_credentials
- **Name**: remove_network_credentials
- **Parameters**:
  - network_id: identifier (network index to remove)
- **Returns**: void
- **Behavior**: Removes stored network credentials for the specified network. Optional step that administrator may perform before provisioning new credentials. Deletes network configuration from persistent storage.
- **Algorithm Detail**: Deletes network configuration entry from non-volatile storage.
- **Usage in FSM**: Optional operation in Step 12, called via RemoveNetwork command.

#### F13: store_network_credentials
- **Name**: store_network_credentials
- **Parameters**:
  - credentials: network_credentials_object (network_id, type, SSID, passphrase, etc.)
- **Returns**: network_credentials_stored (confirms storage)
- **Behavior**: Stores new network credentials in persistent storage. Credentials include network type (WiFi/Thread), network identifier (SSID/PAN ID), security credentials (passphrase/dataset), and any other network-specific parameters.
- **Algorithm Detail**: Writes network configuration to secure non-volatile storage. May encrypt credentials before storage.
- **Cryptographic Detail**: Credentials may be encrypted at rest using device-specific encryption key.
- **Usage in FSM**: Called when AddOrUpdateWiFiNetwork or AddOrUpdateThreadNetwork command received (Step 12).

#### F14: get_connection_error
- **Name**: get_connection_error
- **Parameters**: none
- **Returns**: string (error description)
- **Behavior**: Returns description of why connection to operational network failed. Error codes may include authentication failure, network not found, timeout, etc.
- **Algorithm Detail**: Queries network stack for last connection failure reason.
- **Usage in FSM**: Called when connection attempt fails to populate error information.

#### F15: terminate_recovery_connection
- **Name**: terminate_recovery_connection
- **Parameters**: none
- **Returns**: void
- **Behavior**: Terminates the recovery connection (BLE or WiFi commissioning channel) after successfully connecting to operational network. Recovery connection is no longer needed once operational network connectivity is established.
- **Algorithm Detail**: Closes BLE connection or WiFi Public Action Frame session.
- **Usage in FSM**: Called in Step 14 when operational network connection succeeds and communication transitions to operational network.

#### F16: perform_operational_discovery
- **Name**: perform_operational_discovery
- **Parameters**: none
- **Returns**: void
- **Behavior**: Initiates operational discovery procedure to discover the administrator on the operational network. Uses mDNS-based service discovery as defined in Section 4.3.2 of Matter specification. Node advertises its operational identity and discovers administrator's operational address.
- **Algorithm Detail**: 
  - Uses DNS-SD (DNS Service Discovery) over mDNS
  - Advertises _matter._tcp service with operational identifiers
  - Discovers administrator's _matter._tcp service
  - Resolves IP address and port for operational communication
- **Usage in FSM**: Called when transitioning to OperationalDiscovery state (Step 15).

#### F17: establish_case_over_operational
- **Name**: establish_case_over_operational
- **Parameters**:
  - administrator_id: identifier (administrator's node ID)
- **Returns**: session_object (CASE session over operational network)
- **Behavior**: Establishes a new CASE session with the administrator over the operational network. This replaces the CASE session over the recovery channel. All remaining recovery messages must use this operational network CASE session.
- **Algorithm Detail**: Same CASE protocol as F8, but conducted over operational network transport (IP-based) instead of commissioning channel (BLE/WiFi).
- **Cryptographic Detail**: Same as F8, uses CASE protocol with NOCs over operational network transport.
- **Usage in FSM**: Called after operational discovery succeeds to establish operational CASE session (Step 15).

#### F18: verify_over_operational_network
- **Name**: verify_over_operational_network
- **Parameters**: none
- **Returns**: boolean (true if message received over operational network, false otherwise)
- **Behavior**: Verifies that a received message (specifically CommissioningComplete) was received over the operational network CASE session and not over the recovery channel CASE session. Recovery Node SHALL reject CommissioningComplete if not received over operational network.
- **Algorithm Detail**: Checks the session ID of incoming message against operational network session ID.
- **Usage in FSM**: Called when CommissioningComplete received to enforce Step 16 requirement.

#### F19: send_commissioning_complete_response
- **Name**: send_commissioning_complete_response
- **Parameters**: none
- **Returns**: void
- **Behavior**: Sends CommissioningCompleteResponse command to administrator over operational network CASE session, confirming successful completion of network recovery process.
- **Algorithm Detail**: Constructs and sends CommissioningCompleteResponse message encrypted with operational CASE session keys.
- **Usage in FSM**: Called when CommissioningComplete successfully received over operational network.

#### F20: disarm_fail_safe
- **Name**: disarm_fail_safe
- **Parameters**: none
- **Returns**: void
- **Behavior**: Disarms the fail-safe timer, committing all changes made during network recovery. New network credentials become permanent operational credentials.
- **Algorithm Detail**: Stops fail-safe timer, commits network configuration changes to persistent storage.
- **Usage in FSM**: Called when recovery successfully completes to finalize configuration changes.

#### F21: reject_commissioning_complete
- **Name**: reject_commissioning_complete
- **Parameters**:
  - reason: string (rejection reason)
- **Returns**: void
- **Behavior**: Rejects a CommissioningComplete command that was not received over the operational network. Sends error response to administrator indicating that command must be sent over operational network.
- **Algorithm Detail**: Sends error response with status code indicating protocol violation.
- **Usage in FSM**: Called when CommissioningComplete received over wrong channel (not operational network).

#### F22: revert_to_old_credentials
- **Name**: revert_to_old_credentials
- **Parameters**: none
- **Returns**: void
- **Behavior**: Reverts to old network credentials if fail-safe timer expires before recovery completes. Discards newly provisioned credentials and restores previous operational network credentials.
- **Algorithm Detail**: Restores previous network configuration from backup or discard uncommitted changes.
- **Usage in FSM**: Called when fail-safe expires to rollback incomplete recovery.

#### F23: read_recovery_identifier
- **Name**: read_recovery_identifier
- **Parameters**: none
- **Returns**: recovery_identifier (attribute value)
- **Behavior**: Reads the RecoveryIdentifier attribute from the GeneralCommissioning cluster. This identifier is used by administrator to identify specific node in recovery mode. Should be read and stored before operational network credentials change (Step 1).
- **Algorithm Detail**: Reads attribute value from GeneralCommissioning cluster (cluster 0x0030, attribute RecoveryIdentifier).
- **Usage in FSM**: Called by administrator before credentials change (preparatory step).

#### F24: get_ble_service_data_payload
- **Name**: get_ble_service_data_payload
- **Parameters**:
  - recovery_identifier: attribute_value
- **Returns**: ble_payload (byte array)
- **Behavior**: Constructs BLE Service Data payload for network recovery advertisement. Payload includes OpCode indicating recovery mode and recovery identifier value. Format defined in Matter specification for BLE commissioning.
- **Algorithm Detail**: Constructs BLE advertisement according to Matter BLE Service Data format with recovery-specific OpCode.
- **Usage in FSM**: Called when advertising recovery over BLE channel.

#### F25: get_wifi_discovery_payload
- **Name**: get_wifi_discovery_payload
- **Parameters**:
  - recovery_identifier: attribute_value
- **Returns**: wifi_payload (byte array)
- **Behavior**: Constructs WiFi Unsynchronized Service Discovery payload for network recovery advertisement. Uses WiFi Public Action Frame with OpCode indicating recovery mode and recovery identifier.
- **Algorithm Detail**: Constructs WiFi Public Action Frame according to Table 74 of specification with recovery-specific OpCode.
- **Usage in FSM**: Called when advertising recovery over WiFi channel.

#### F26: check_user_consent
- **Name**: check_user_consent
- **Parameters**:
  - recovery_node_id: identifier
- **Returns**: boolean (true if user granted consent, false otherwise)
- **Behavior**: Checks whether user has granted consent for administrator to provide new credentials to the specified recovery node. This is an administrator-side function that ensures user explicitly approves recovery for specific node, preventing inadvertent provisioning to imposter devices or during temporary outages.
- **Algorithm Detail**: Queries user via administrator application UI or other user interaction mechanism. User must explicitly approve recovery for identified node.
- **Usage in FSM**: Called by administrator before establishing recovery connection (Step 6-7).

#### F27: suspend_autonomous_reconnect
- **Name**: suspend_autonomous_reconnect
- **Parameters**: none
- **Returns**: void
- **Behavior**: Suspends autonomous reconnection attempts to existing operational network while recovery procedure is in progress. Network recovery SHALL preempt autonomous reconnect attempts once CASE session established.
- **Algorithm Detail**: Disables background reconnection timer/task.
- **Usage in FSM**: Called when CASE session established (Step 9).

#### F28: resume_autonomous_reconnect
- **Name**: resume_autonomous_reconnect
- **Parameters**: none
- **Returns**: void
- **Behavior**: Resumes autonomous reconnection attempts after recovery connection terminates. If recovery fails, node returns to attempting connection with previous credentials.
- **Algorithm Detail**: Re-enables background reconnection timer/task.
- **Usage in FSM**: Called when recovery connection terminates or recovery fails.

#### F29: generate_event
- **Name**: generate_event
- **Parameters**:
  - event_name: string (event identifier)
- **Returns**: void
- **Behavior**: Generates a Matter event to log significant state changes during network recovery process. Events include network_config_response, connect_network_response, connection_failed_event, recovery_complete, etc.
- **Algorithm Detail**: Creates event entry in event log with timestamp and event-specific data.
- **Usage in FSM**: Called at various transitions to record recovery process events.

### Cryptographic Operations Detail

#### CO1: CASE Session Establishment
- **Operation**: Certificate Authenticated Session Establishment
- **Algorithm**: CASE protocol (Matter Specification Section 4.13.2)
- **Inputs**: 
  - Device Attestation Certificate (or Node Operational Certificate)
  - Administrator's Node Operational Certificate
  - Random nonces from both parties
  - Ephemeral ECDH key pairs
- **Output**: 
  - Shared session encryption keys (128-bit AES-CCM keys)
  - Session ID
- **Assumptions**:
  - Certificates are valid and not revoked
  - Private keys are securely stored and not compromised
  - ECDH provides secure key exchange
  - HKDF provides secure key derivation
  - AES-CCM provides authenticated encryption
- **Usage**: Establishes secure channel for all recovery messages (over both recovery channel and operational network)

#### CO2: Message Encryption with CASE Keys
- **Operation**: Symmetric encryption of all recovery messages
- **Algorithm**: AES-128-CCM (Counter with CBC-MAC mode)
- **Inputs**:
  - Plaintext message
  - Session encryption key (from CASE)
  - Nonce/IV (message counter based)
  - Additional authenticated data (header fields)
- **Output**: Ciphertext + authentication tag
- **Assumptions**:
  - AES-CCM provides confidentiality and authenticity
  - Session keys are not leaked
  - Nonces are not reused
- **Usage**: All messages after CASE establishment encrypted with these keys

#### CO3: Operational Discovery Authentication
- **Operation**: Operational node identity verification
- **Algorithm**: 
  - mDNS-SD with operational identifiers
  - Operational identifiers derived from NOC
- **Inputs**:
  - Node Operational Certificate
  - Fabric ID
- **Output**: Operational node identifier for mDNS advertisement
- **Assumptions**:
  - Operational identifiers are unique within fabric
  - mDNS is not spoofed (local network trust)
- **Usage**: Discovering administrator on operational network (Step 15)

### Security Properties Detail

#### SP1: User Consent Enforcement
- **Property Name**: USER_CONSENT_REQUIRED
- **Type**: access_control
- **Description**: Administrator SHALL obtain user consent before providing new credentials to Recovery Node. Without consent, recovery flow SHALL be aborted.
- **FSM States Involved**: RecoveryModeAnnouncing, ExtendedAnnouncementActive, RecoveryFlowAborted
- **Critical Transitions**: 
  - T9: RecoveryModeAnnouncing → RecoveryFlowAborted (no consent)
  - T10: RecoveryModeAnnouncing → RecoveryConnectionEstablished (with consent)
  - T11: ExtendedAnnouncementActive → RecoveryFlowAborted (no consent)
  - T12: ExtendedAnnouncementActive → RecoveryConnectionEstablished (with consent)
- **Enforcement Mechanism**: Guard condition `user_consent_granted == true` on transitions establishing recovery connection
- **Security Rationale**: Prevents inadvertent credential provisioning to imposter devices, prevents recovery during temporary outages when user doesn't intend recovery

#### SP2: CASE Authentication for Recovery
- **Property Name**: CASE_AUTHENTICATED_RECOVERY
- **Type**: authenticity
- **Description**: All messages exchanged over recovery connection SHALL be encrypted using CASE-derived keys. Both Recovery Node and Administrator must mutually authenticate via certificates before any credentials are exchanged.
- **FSM States Involved**: RecoveryConnectionEstablished, CASESessionActive, FailSafeArmed, NewCredentialsProvisioned
- **Critical Transitions**: T13 (establish CASE), T17 (provision credentials)
- **Enforcement Mechanism**: CASE session establishment required before any credential provisioning commands accepted
- **Security Rationale**: Prevents man-in-the-middle attacks, prevents unauthorized credential changes, ensures mutual authentication

#### SP3: Operational Network Verification
- **Property Name**: OPERATIONAL_NETWORK_VERIFICATION
- **Type**: authenticity + consistency
- **Description**: Recovery Node SHALL reject CommissioningComplete command if not received over the operational network. This ensures recovery only completes after operational connectivity actually established.
- **FSM States Involved**: RecoveryCompleteReady
- **Critical Transitions**: 
  - T24: RecoveryCompleteReady → NormalOperation (success, over operational network)
  - T25: RecoveryCompleteReady → RecoveryCompleteReady (reject if not over operational)
- **Enforcement Mechanism**: Guard condition `verify_over_operational_network() == true` on transition to completion
- **Security Rationale**: Prevents premature recovery completion before actual network connectivity established, ensures recovery happens over correct network

#### SP4: Fail-Safe Protection
- **Property Name**: FAIL_SAFE_ROLLBACK
- **Type**: consistency + availability
- **Description**: 60 second fail-safe timer guards against incomplete recovery. If administrator does not complete recovery within fail-safe period, all changes are rolled back and node reverts to previous credentials.
- **FSM States Involved**: CASESessionActive, FailSafeArmed, NewCredentialsProvisioned, ConnectingToNewNetwork, ConnectionToNewNetworkFailed
- **Critical Transitions**: 
  - T15: CASESessionActive → RecoveryConnectionTerminated (timeout)
  - T22: ConnectionToNewNetworkFailed → RecoveryConnectionTerminated (timeout with rollback)
- **Enforcement Mechanism**: Guard condition `fail_safe_timer > 0` on all recovery operations; automatic termination when `fail_safe_timer == 0`
- **Security Rationale**: Prevents device being left in inconsistent state with invalid credentials, ensures device returns to functional state if recovery fails

#### SP5: Network Recovery Preemption
- **Property Name**: RECOVERY_PREEMPTS_RECONNECT
- **Type**: consistency
- **Description**: Once CASE session established during recovery, autonomous network reconnect attempts SHALL be suspended. This prevents interference between recovery procedure and background reconnection attempts.
- **FSM States Involved**: CASESessionActive, FailSafeArmed, NewCredentialsProvisioned
- **Critical Transitions**: T13 (CASE established suspends autonomous reconnect)
- **Enforcement Mechanism**: Action `autonomous_reconnect_suspended := true` when CASE established; resumed only when recovery connection terminates
- **Security Rationale**: Prevents race conditions between recovery and autonomous reconnection, ensures recovery procedure has exclusive control of network configuration

#### SP6: Recovery Identifier Binding
- **Property Name**: RECOVERY_IDENTIFIER_BINDING
- **Type**: authenticity
- **Description**: Recovery Node advertises its RecoveryIdentifier attribute during recovery mode. Administrator uses this identifier to identify specific node for recovery. Binding between identifier and node prevents targeting wrong device.
- **FSM States Involved**: RecoveryModeAnnouncing, ExtendedAnnouncementActive
- **Critical Transitions**: T4, T5, T10, T12 (recovery announcement includes identifier)
- **Enforcement Mechanism**: Recovery advertisement includes recovery_identifier; administrator matches before connecting
- **Security Rationale**: Prevents administrator from accidentally connecting to wrong device in recovery mode, enables specific device targeting in multi-device recovery scenarios

#### SP7: Delayed Recovery Mode Entry
- **Property Name**: DELAYED_RECOVERY_ENTRY
- **Type**: availability + timing
- **Description**: Recovery Node SHALL attempt to reconnect to operational network for at least 120 seconds before entering recovery mode. This prevents premature recovery mode entry during temporary network outages.
- **FSM States Involved**: ConnectivityLost, RecoveryModeAnnouncing
- **Critical Transitions**: T4 (connectivity lost → recovery mode with timer guard)
- **Enforcement Mechanism**: Guard condition `reconnection_timer >= 120` on transition to recovery mode
- **Security Rationale**: Reduces wireless spectrum pollution, limits attack opportunities, prevents unnecessary recovery procedures during transient outages

#### SP8: Recovery Channel Segregation
- **Property Name**: RECOVERY_CHANNEL_SEGREGATION
- **Type**: access_control
- **Description**: Recovery connection established over commissioning channel (BLE or WiFi), but final commissioning complete must be over operational network. This segregation ensures device has actually achieved operational connectivity before completing recovery.
- **FSM States Involved**: RecoveryConnectionEstablished, CASESessionActive, OperationalDiscovery, RecoveryCompleteReady
- **Critical Transitions**: T19 (switch from recovery to operational), T24 (complete only over operational)
- **Enforcement Mechanism**: Two separate CASE sessions - one over recovery channel, one over operational network; completion only accepted over operational CASE
- **Security Rationale**: Proves device has operational network access before completing, prevents fake completion over recovery channel

### Security Assumptions

#### A1: Certificate Validity
- **Assumption**: Device Attestation Certificates and Node Operational Certificates are valid, not expired, and not revoked
- **Type**: explicit (required by Matter certificate infrastructure)
- **If Violated**: CASE session establishment would fail or attacker could impersonate nodes
- **Mitigation**: Certificate validation checks, revocation checking

#### A2: Private Key Security
- **Assumption**: Private keys corresponding to certificates are securely stored and not compromised
- **Type**: explicit (fundamental cryptographic assumption)
- **If Violated**: Attacker could impersonate node or administrator
- **Mitigation**: Secure key storage (hardware security modules, secure enclaves)

#### A3: CASE Protocol Security
- **Assumption**: CASE protocol provides secure mutual authentication and key establishment
- **Type**: explicit (protocol design assumption)
- **If Violated**: Attacker could establish fake session and intercept/modify recovery messages
- **Mitigation**: Formal verification of CASE protocol, peer review

#### A4: Cryptographic Primitive Security
- **Assumption**: AES-CCM provides authenticated encryption, ECDH provides secure key exchange, HKDF provides secure key derivation
- **Type**: explicit (standard cryptographic assumptions)
- **If Violated**: Messages could be decrypted or forged
- **Mitigation**: Use of standardized, well-analyzed algorithms

#### A5: No Key Leakage
- **Assumption**: Session keys derived from CASE are not leaked to unauthorized parties
- **Type**: explicit (operational assumption)
- **If Violated**: Attacker could decrypt recovery messages or forge messages
- **Mitigation**: Secure memory handling, key zeroization after use

#### A6: Administrator Trustworthiness
- **Assumption**: Administrator with user consent is authorized to modify device network credentials
- **Type**: explicit (trust model assumption)
- **If Violated**: Malicious administrator could provision incorrect credentials or deny service
- **Mitigation**: User consent requirement, audit logging

#### A7: Recovery Identifier Uniqueness
- **Assumption**: RecoveryIdentifier is unique (or unique enough) within local environment to identify specific device
- **Type**: implicit (practical assumption)
- **If Violated**: Administrator might target wrong device for recovery
- **Mitigation**: Recovery identifier combined with other identifying information (device name, location)

#### A8: Local Network Trust
- **Assumption**: Local network used for operational discovery (mDNS) is not maliciously controlled
- **Type**: implicit (network trust assumption)
- **If Violated**: Operational discovery could be spoofed, connecting to wrong administrator
- **Mitigation**: Operational identifiers derived from certificates, CASE authentication after discovery

#### A9: User Consent Mechanism Integrity
- **Assumption**: User consent mechanism on administrator cannot be bypassed or faked
- **Type**: implicit (administrator implementation assumption)
- **If Violated**: Recovery could proceed without actual user consent
- **Mitigation**: Administrator implementation security, user interface design

#### A10: Time Source Availability
- **Assumption**: Device has access to time source for timer operations (120s reconnection, 60s fail-safe)
- **Type**: implicit (system capability assumption)
- **If Violated**: Timers might not operate correctly, affecting state transitions
- **Mitigation**: Internal clock with reasonable accuracy, timer relative to events

#### A11: Network Credential Validity
- **Assumption**: New network credentials provided by administrator are valid for the target operational network
- **Type**: implicit (administrator knowledge assumption)
- **If Violated**: Connection to new network would fail, recovery would not complete
- **Mitigation**: ConnectNetwork command tests credentials; fail-safe allows retry

#### A12: Announcement Channel Availability
- **Assumption**: BLE or WiFi commissioning channels remain available after operational network connectivity lost
- **Type**: implicit (physical layer assumption)
- **If Violated**: Recovery mode announcement not visible to administrator
- **Mitigation**: Support multiple announcement channels (BLE and WiFi)

### Timing Constraints Detail

#### TC1: Minimum Reconnection Attempt Duration
- **Duration**: 120 seconds minimum
- **Enforced By**: Guard condition on T4 transition
- **Specification Reference**: Step 3 - "SHALL continue to attempt to connect...for a duration of at least 120 seconds"
- **Purpose**: Prevent premature recovery mode entry during transient outages
- **Relaxation**: May continue longer than 120 seconds before entering recovery

#### TC2: Fail-Safe Auto-Arm Duration
- **Duration**: 60 seconds
- **Enforced By**: Automatic action in T13 transition
- **Specification Reference**: Step 10 - "SHALL autonomously arm the fail-safe timer for a timeout of 60 seconds"
- **Purpose**: Guard against administrator not proceeding with recovery timely
- **Reset**: Can be reset by administrator ArmFailSafe command

#### TC3: Administrator Fail-Safe Arm Window
- **Duration**: 60 seconds (before auto-armed fail-safe expires)
- **Enforced By**: Guard condition on T14 transition; timeout on T15 transition
- **Specification Reference**: Step 11 - "Within 60 seconds...Administrator SHALL arm the fail-safe timer"
- **Purpose**: Confirm administrator intent to proceed, extend fail-safe period
- **Failure Mode**: If not armed within 60 seconds, session terminates (T15)

#### TC4: Extended Announcement Duration
- **Duration**: Specification-defined (retrieved via get_extended_announcement_duration())
- **Enforced By**: extended_announcement_timer on T6 transition
- **Specification Reference**: Step 4 - "SHALL follow announcement duration requirements...SHALL take advantage of Extended Announcement"
- **Purpose**: Provide extended window for administrator to initiate recovery
- **Post-Expiry**: Transitions to periodic reconnection attempts

#### TC5: Manufacturer Reconnection Interval
- **Duration**: Manufacturer-defined
- **Enforced By**: reconnect_interval in PeriodicReconnectionAttempts state
- **Specification Reference**: Step 5 - "at a manufacturer-defined interval"
- **Purpose**: Balance between recovery responsiveness and resource consumption
- **Implementation Specific**: Interval chosen by manufacturer

### Additional Definitions

#### D1: RecoveryIdentifier Attribute
- **Term**: RecoveryIdentifier
- **Definition**: Attribute value from GeneralCommissioning cluster (cluster 0x0030) uniquely identifying node for recovery purposes. Read by administrator before credentials change to enable later identification during recovery.
- **Type**: Attribute (read-only)
- **Security Relevance**: Enables specific node targeting during recovery, prevents recovery of wrong device

#### D2: CommissioningModeInitialStepsHint
- **Term**: CommissioningModeInitialStepsHint
- **Definition**: Set of physical user actions (button presses, power cycles, etc.) that user performs to restart recovery mode after extended announcement expires. Manufacturer-specific actions.
- **Type**: Physical user interaction
- **Security Relevance**: Requires physical access to device to restart recovery, prevents remote unauthorized recovery restart

#### D3: OpCode
- **Term**: OpCode (Operation Code)
- **Definition**: Field in BLE Service Data or WiFi Public Action Frame indicating device operational mode. Distinct values for commissioning, recovery, etc.
- **Type**: Protocol field
- **Security Relevance**: Allows administrator to distinguish recovery advertisements from normal commissioning

#### D4: Announcement Duration
- **Term**: Announcement Duration
- **Definition**: Period during which device advertises its availability (for commissioning or recovery). Extended Announcement is longer duration for specific scenarios.
- **Type**: Timing parameter
- **Security Relevance**: Limits window during which device is discoverable, reducing exposure

#### D5: Operational Network
- **Term**: Operational Network
- **Definition**: Primary network (WiFi or Thread) on which device operates and communicates with other Matter nodes. Network Recovery goal is to restore connectivity to this network.
- **Type**: Network
- **Security Relevance**: Credentials for this network must be protected; recovery restores access

#### D6: Commissioning Channel
- **Term**: Commissioning Channel
- **Definition**: Communication channel (BLE or WiFi Unsynchronized Service Discovery) used for device commissioning and network recovery. Separate from operational network.
- **Type**: Communication channel
- **Security Relevance**: Used for recovery connection; must support CASE session establishment

#### D7: CASE Session
- **Term**: CASE Session (Certificate Authenticated Session Establishment)
- **Definition**: Mutually authenticated secure session between two nodes using their operational certificates. Provides encrypted and authenticated communication channel.
- **Type**: Security protocol
- **Security Relevance**: Fundamental security mechanism for all Matter operational communication; used for recovery authentication

#### D8: Fail-Safe Timer
- **Term**: Fail-Safe Timer
- **Definition**: Countdown timer during configuration operations that automatically rolls back changes if not disarmed before expiry. Prevents device being left in inconsistent state.
- **Type**: Safety mechanism
- **Security Relevance**: Ensures device returns to functional state if recovery incomplete, prevents denial-of-service

#### D9: Network Credentials
- **Term**: Network Credentials
- **Definition**: Parameters required to connect to operational network: SSID and passphrase for WiFi, dataset for Thread. Stored securely on device.
- **Type**: Configuration data
- **Security Relevance**: Compromise of credentials allows unauthorized network access; recovery securely updates these

#### D10: Operational Discovery
- **Term**: Operational Discovery
- **Definition**: DNS-SD based discovery mechanism allowing Matter nodes to discover each other on operational network using mDNS. Uses operational identifiers derived from certificates.
- **Type**: Discovery protocol
- **Security Relevance**: Required to reestablish communication on operational network; assumes local network trust

