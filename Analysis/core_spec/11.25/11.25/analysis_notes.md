# FSM Analysis Notes for Section 11.25: Joint Fabric Administrator Cluster

## Overview
- Cluster ID: 0x0753
- Purpose: Joint Fabric Administrator functionality for nodes acting as Anchor CA
- Role: Utility cluster at Node scope
- Conformance: Provisional (P)

## Data Types Extracted

### ICACResponseStatusEnum (enum8)
- 0: OK - No error
- 1: InvalidPublicKey - Public Key in ICAC is invalid
- 2: InvalidICAC - ICAC chain validation failed / DN Encoding rules verification failed

### TransferAnchorResponseStatusEnum (enum8)
- 0: OK - No error
- 1: TransferAnchorStatusDatastoreBusy - Transfer not started due to ongoing Datastore operations
- 2: TransferAnchorStatusNoUserConsent - User has not consented for Anchor Transfer

## Status Codes (StatusCodeEnum)
- 0x02: Busy - Another commissioning in progress
- 0x03: PAKEParameterError - PAKE parameters invalid
- 0x04: WindowNotOpen - No commissioning window open
- 0x05: VIDNotVerified - VID Verification not executed
- 0x06: InvalidAdministratorFabricIndex - AdministratorFabricIndex is null

## Attributes
- AdministratorFabricIndex (fabric-idx, 1-254 or null)
  - Indicates FabricIndex from Endpoint 0's Operational Cluster Fabrics attribute
  - null if no fabric associated with JointFabric

## Commands Analysis

### 1. ICACCSRRequest (0x00)
**Trigger**: Client invokes command
**Preconditions**:
- MUST be over CASE session
- MUST have armed fail-safe context
- Fabric Table VID Verification MUST be executed
- NO prior successful AddICAC within fail-safe period

**Effects**:
- Generates ICACCSRResponse with ICACCSR

**Failure Conditions**:
- Not CASE session → INVALID_COMMAND
- No fail-safe → FAILSAFE_REQUIRED
- VID not verified → JfVidNotVerified
- Prior AddICAC success → CONSTRAINT_ERROR

### 2. ICACCSRResponse (0x01)
**Response to**: ICACCSRRequest
**Data**: ICACCSR (DER-encoded PKCS#10 CSR, max 600 bytes)

### 3. AddICAC (0x02)
**Trigger**: Client invokes with ICACValue
**Preconditions**:
- MUST be over CASE session
- MUST have armed fail-safe context
- NO prior successful AddICAC within fail-safe period

**Validation Steps**:
1. Verify ICAC using Crypto_VerifyChain([ICACValue, RootCACertificate])
   - Failure → InvalidICAC
2. Public key matches last ICACCSRResponse
   - Failure → InvalidPublicKey
3. DN Encoding Rules validation
   - Failure → InvalidICAC

**Effects on Success**:
- ICACValue used in Joint Commissioning Method

**Failure Conditions**:
- Not CASE session → INVALID_COMMAND
- No fail-safe → FAILSAFE_REQUIRED
- Prior AddICAC success → CONSTRAINT_ERROR
- Validation fails → ICACResponse with error

### 4. ICACResponse (0x03)
**Response to**: AddICAC
**Data**: StatusCode (ICACResponseStatusEnum)

### 5. OpenJointCommissioningWindow (0x04)
**Precondition**:
- AdministratorFabricIndex MUST NOT be null
  - Failure → InvalidAdministratorFabricIndex

**Parameters**:
- CommissioningTimeout (uint16)
- PAKEPasscodeVerifier (octstr, 97 bytes)
- Discriminator (uint16, max 4095)
- Iterations (uint32, 1000-100000)
- Salt (octstr, 16-32 bytes)

**Note**: Alias to OpenCommissioningWindow in Joint Fabric Administrator Cluster

### 6. TransferAnchorRequest (0x05)
**Trigger**: Candidate Anchor sends to current Anchor
**Purpose**: Request transfer of Anchor Fabric

### 7. TransferAnchorResponse (0x06)
**Response to**: TransferAnchorRequest
**Data**: StatusCode (TransferAnchorResponseStatusEnum)

### 8. TransferAnchorComplete (0x07)
**Trigger**: After transfer completes
**Purpose**: Indicate completion of Anchor Fabric transfer

### 9. AnnounceJointFabricAdministrator (0x08)
**Purpose**: Communicate endpoint holding Joint Fabric Administrator Cluster
**Data**: EndpointID (endpoint-no)

## State Variables Identified
1. **fail_safe_armed**: boolean - Whether fail-safe context is active
2. **case_session_active**: boolean - Whether command received over CASE
3. **vid_verified**: boolean - Whether VID verification executed
4. **icac_added_in_failsafe**: boolean - Whether AddICAC succeeded in current fail-safe period
5. **last_icaccsr**: octstr - Last ICACCSR generated in this session
6. **administrator_fabric_index**: fabric-idx or null - Current fabric association
7. **commissioning_window_open**: boolean - Whether commissioning window is open
8. **anchor_transfer_in_progress**: boolean - Whether anchor transfer ongoing
9. **datastore_busy**: boolean - Whether datastore operations ongoing
10. **user_consent_given**: boolean - Whether user consented to transfer

## Cryptographic Operations Identified
1. **ICACCSR Generation**: PKCS#10 CSR generation (DER-encoded)
2. **Crypto_VerifyChain**: Certificate chain verification
   - Inputs: [ICACValue, RootCACertificate]
   - Returns: success/failure
3. **Public Key Matching**: Compare public keys from ICAC and CSR
4. **DN Encoding Rules Validation**: Validate Distinguished Name encoding

## Security Properties
1. **Access Control**: Commands require CASE session
2. **Fail-Safe Protection**: Commands require armed fail-safe
3. **Certificate Validation**: Multi-step ICAC validation
4. **Idempotency Protection**: Prevent duplicate AddICAC in fail-safe period
5. **VID Verification**: Required before ICAC operations
6. **User Consent**: Required for anchor transfer
