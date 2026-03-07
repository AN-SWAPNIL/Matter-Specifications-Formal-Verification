# FSM Analysis Working File - Section 14.2 Common Conventions

## Section Type
Conventions and Definitions for TLS usage in Matter

## Key Behavioral Aspects Identified

### 1. TLS Connection Lifecycle
- **Implicit States**: Not Connected → Connecting → Connected / Failed
- **Trigger**: Establish TLS connection to endpoint
- **Constraints**: 
  - TLS version >= 1.3 (SHALL NOT support earlier)
  - Must support Perfect Forward Security cipher suites
  - MAY use IPv4 or IPv6

### 2. Certificate Verification Process (Chain of Trust)
- **Implicit States**: Unverified → Verifying Chain → Verified / Failed
- **Process**: Client uses TLSRCAC to authenticate server (RFC 4158)
- **Operations**: 
  - SHA-256 fingerprint calculation (for comparison/verification)
  - Chain of trust verification per RFC 4158
  - DER encoding validation

### 3. Client Certificate Authentication
- **Implicit States**: No Client Cert → Client Cert Presented → Authenticated / Failed
- **Process**: Client presents certificate during handshake (RFC 8446)

### 4. Certificate Signing Request (CSR) Process
- **Implicit States**: No CSR → CSR Generated → Certificate Issued
- **Constraints**: SHALL follow PKCS #10 format

### 5. TLS Endpoint Management
- **States**: Endpoint not configured → Endpoint configured → Connection established
- **Attributes**: Hostname (domain/IP/mDNS), Port (default 443)

## State-Defining Attributes

1. **connection_state**: disconnected, connecting, connected, failed
2. **tls_version**: null, 1.3, >1.3
3. **server_cert_state**: unverified, verifying, verified, failed
4. **client_cert_state**: not_presented, presented, authenticated, failed
5. **endpoint_configured**: false, true
6. **hostname**: null, valid_hostname
7. **port**: null, port_number
8. **tls_role**: client, server (Node is presumed client)

## Cryptographic Operations

1. **SHA-256 Certificate Fingerprint**
   - Input: X.509 certificate (DER binary)
   - Output: 256-bit hash
   - Algorithm: SHA-256 (RFC 6234)

2. **Certificate Chain Verification**
   - Input: Server certificate, intermediate certs, TLSRCAC
   - Algorithm: Chain of Trust (RFC 4158)
   - Output: verified / failed

3. **TLS Handshake**
   - Protocol: TLS 1.3+ (RFC 8446)
   - Constraint: Perfect Forward Security cipher suites only
   - Client/Server authentication via certificates

4. **CSR Generation**
   - Format: PKCS #10
   - Input: Entity public key, entity information
   - Output: CSR

## Conditional Logic Extracted

1. **TLS Version Check**:
   - IF tls_version < 1.3 THEN reject_connection
   - IF tls_version >= 1.3 THEN allow_connection

2. **Port Number Default**:
   - IF port_number is omitted THEN port := 443

3. **Perfect Forward Security**:
   - IF cipher_suite without PFS THEN reject
   - IF cipher_suite with PFS THEN accept

4. **Certificate Encoding**:
   - SHALL be DER format (X.690)
   - SHALL be X.509v3 compliant (RFC 5280)

5. **Hostname Resolution**:
   - IF public DNS THEN resolve via DNS
   - IF .local name THEN resolve via mDNS
   - IF IP address THEN use directly

## Functions Required

1. `validate_tls_version(version)` - Check version >= 1.3
2. `verify_perfect_forward_security(cipher_suite)` - Check PFS support
3. `calculate_certificate_fingerprint(cert_der)` - SHA-256 hash
4. `verify_certificate_chain(cert, intermediates, root_ca)` - Chain of trust
5. `establish_tls_connection(hostname, port, version)` - TLS handshake
6. `present_client_certificate(cert)` - Client auth
7. `generate_csr(public_key, entity_info)` - PKCS #10 CSR
8. `encode_certificate_der(cert)` - DER encoding
9. `validate_x509v3(cert)` - X.509v3 compliance check
10. `resolve_hostname(hostname)` - DNS/mDNS/IP resolution
11. `set_default_port(port)` - Return 443 if null

## Security Properties

1. **TLS_VERSION_ENFORCEMENT**: Only TLS 1.3+ allowed
2. **PERFECT_FORWARD_SECURITY**: All cipher suites must provide PFS
3. **CERTIFICATE_AUTHENTICITY**: Server cert verified via TLSRCAC chain
4. **CLIENT_AUTHENTICATION**: Optional client cert authentication
5. **CERTIFICATE_INTEGRITY**: SHA-256 fingerprint for verification
6. **ENCODING_COMPLIANCE**: DER encoding required

## Assumptions

1. TLSRCAC is trusted and pre-provisioned
2. SHA-256 is collision-resistant
3. Certificate authorities are trustworthy
4. DNS/mDNS resolution is available
5. RFC 8446 (TLS 1.3) implementation is secure
6. Perfect Forward Security cipher suites are available
7. X.509v3 and DER encoding are correctly implemented
