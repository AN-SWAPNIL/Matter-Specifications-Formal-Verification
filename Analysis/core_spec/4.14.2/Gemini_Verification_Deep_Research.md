# **Formal Verification and Security Analysis of the Matter Certificate Authenticated Session Establishment (CASE) Protocol**

## **1\. Introduction**

The Internet of Things (IoT) landscape has historically been fragmented, characterized by a disparate array of proprietary protocols, incompatible ecosystems, and inconsistent security standards. This fragmentation has posed significant barriers to adoption, creating a chaotic user experience and, more critically, a fractured security landscape where vulnerabilities in one device could compromise an entire network. The Matter protocol, spearheaded by the Connectivity Standards Alliance (CSA), emerged as a unifying solution designed to ensure interoperability, reliability, and security across smart home devices.1

At the heart of Matter's security architecture lies the Certificate Authenticated Session Establishment (CASE) protocol. CASE is the cryptographic handshake used to establish secure, mutually authenticated sessions between operational nodes within a Matter fabric. It is the gatekeeper of the smart home; it determines whether a controller (such as a smartphone or hub) is authorized to issue commands to a device (such as a lock or thermostat). Given its critical role, the security of the CASE protocol is non-negotiable. A failure in CASE could allow unauthorized entities to seize control of physical devices, eavesdrop on sensitive sensor data, or launch denial-of-service attacks that render the smart home non-functional.

This report presents a rigorous, deep-dive analysis of the formal verification claims regarding the CASE protocol, as defined in the Matter Core Specification Version 1.4. The objective is to validate the assertions of cryptographic soundness provided in the verification artifacts while conducting an independent, exhaustive search for vulnerabilities that may have evaded the formal model. This analysis integrates findings from the provided Finite State Machine (FSM) models, security property definitions, and external vulnerability reports (including CVE-2024-3297) to provide a holistic "final decision" on the protocol's security posture.

The analysis proceeds by first deconstructing the architectural underpinnings of the protocol, moving to a state-by-state evaluation of the formal model, and culminating in a detailed vulnerability assessment that contrasts theoretical security guarantees with implementation realities. Special attention is paid to the "Specification Gaps" identified in the formal verification—specifically regarding certificate revocation and key rotation—and how the recent Matter 1.4 specification updates mitigate these risks through mechanisms like Certificate Revocation Lists (CRLs).

## **2\. Theoretical Framework and Architectural Deconstruction**

To evaluate the formal verification claims, one must first establish a comprehensive understanding of the CASE protocol's design philosophy, cryptographic primitives, and operational mechanics. CASE is not a novel invention in isolation; it is a specialized adaptation of the SIGMA-I protocol, a well-studied "Sign-and-MAC" key exchange method designed to provide mutual authentication and identity protection.3

### **2.1 The Cryptographic Foundation**

Matter's security is built upon a restricted but robust suite of cryptographic primitives, ensuring that all implementations adhere to a high baseline of security. The protocol mandates the use of Elliptic Curve Cryptography (ECC) on the NIST P-256 curve (secp256r1) for public key operations, including digital signatures (ECDSA) and key exchange (ECDH).4 This choice balances security strength (roughly equivalent to 3072-bit RSA) with the performance constraints of low-power IoT microcontrollers.

For symmetric operations, the protocol utilizes the Advanced Encryption Standard (AES) in Counter with CBC-MAC (CCM) mode. AES-CCM is an Authenticated Encryption with Associated Data (AEAD) algorithm, which provides both confidentiality (encryption) and integrity (authentication) in a single operation.4 This prevents a class of attacks where an adversary might modify the ciphertext to manipulate the plaintext upon decryption.

Hashing operations are standardized on SHA-256. This is used extensively in the Key Derivation Function (KDF), specifically HKDF (HMAC-based Key Derivation Function), to derive session keys from the shared secrets established during the handshake. The integration of these primitives is not merely a recommendation but a normative requirement; any deviation results in a non-compliant and likely insecure implementation.4

### **2.2 The Public Key Infrastructure (PKI) Trust Model**

The trust model of Matter is hierarchical and rooted in a Public Key Infrastructure (PKI). Unlike web PKI, which relies on hundreds of public root authorities, a Matter fabric typically operates with a much smaller, controlled set of trust anchors.

* **Node Operational Certificate (NOC):** Every operational device on the network possesses a unique NOC. This certificate authenticates the node's identity within the fabric and is bound to a specific Node ID and Fabric ID. The verification report emphasizes that proof of possession of the private key associated with the NOC is a critical security property.4  
* **Intermediate CA Certificate (ICAC):** Optionally, fabrics may employ Intermediate CAs to issue NOCs. The formal model accounts for this by including validation steps for the ICAC in the Sigma2 and Sigma3 phases.4  
* **Root CA Certificate (RCAC):** The root of trust. All certificate chains must validate back to a Trusted RCAC installed on the device during the commissioning process. The strict enforcement of this chain validation is the primary defense against unauthorized devices joining the fabric.4

### **2.3 The CASE Handshake Protocol Flow**

The CASE protocol executes a three-message exchange (Sigma1, Sigma2, Sigma3) to establish a secure session. This "Sigma" structure is designed to protect the identities of the participants from active attackers and passive eavesdroppers.

#### **2.3.1 Sigma1: The Initiation and Context Binding**

The handshake begins with the **Initiator** sending the Sigma1 message. This message sets the stage for the cryptographic exchange but does not yet transmit sensitive identity information.

* **Randomness and Freshness:** The Initiator generates a 32-byte InitiatorRandom value using a Cryptographically Secure Deterministic Random Bit Generator (CS-DRBG).4 This value serves as a nonce to ensure the liveness of the session and to prevent replay attacks where old messages are re-sent to force the derivation of old keys.  
* **Ephemeral Key Exchange:** The Initiator generates an ephemeral ECDH key pair (InitiatorEphPubKey). This key is used *only* for this specific session negotiation. By combining this with the Responder's ephemeral key later in the protocol, both parties derive a SharedSecret. The use of ephemeral keys is the mathematical guarantor of **Perfect Forward Secrecy (PFS)**; even if the long-term private keys of the devices are compromised years later, the traffic captured today cannot be decrypted because the ephemeral private keys were discarded immediately after use.4  
* **Destination Identifier:** A unique feature of Matter is the privacy-preserving DestinationIdentifier. Instead of sending the target Node ID or Fabric ID in plaintext (which would allow an observer to map the network structure), the Initiator computes a keyed hash (HMAC) of its random value, the Root Public Key, the Fabric ID, and the Node ID, using the **Identity Protection Key (IPK)**.4 Only a Responder that possesses the corresponding IPK (and is thus a member of the same fabric) can validate this identifier. This property is critical for preventing privacy leakage in multi-tenant environments (e.g., apartment complexes).

#### **2.3.2 Sigma2: Responder Authentication and Challenge**

The **Responder** receives Sigma1, validates the Destination Identifier, and replies with Sigma2. This message is the first to carry encrypted identity information.

* **S2K Key Derivation:** The Responder generates its own random value (ResponderRandom) and ephemeral key pair. It computes the ECDH SharedSecret and then derives a specific encryption key, S2K, using the IPK, the random values, and the public keys exchanged so far.4  
* **Encrypted Credentials:** The Responder encrypts its NOC (and ICAC, if present) using S2K. This encryption ensures that the Responder's identity is never exposed to an unauthenticated party. Only the Initiator, who can also derive S2K (having generated the initial randoms and ephemeral keys), can decrypt and view the certificate.4  
* **Proof of Possession:** The Responder signs the handshake transcript (a hash of the messages exchanged so far) using its long-term NOC private key. This signature is included in the encrypted payload (TBEData2). This proves that the Responder is not just replaying a captured certificate but actively controls the private key associated with it.

#### **2.3.3 Sigma3: Initiator Authentication and Completion**

The Initiator processes Sigma2, verifies the Responder's credentials, and sends Sigma3 to complete the mutual authentication.

* **S3K Key Derivation:** A new encryption key, S3K, is derived for this message.  
* **Encrypted Credentials:** The Initiator encrypts its own NOC and a signature over the updated transcript using S3K.  
* **Session Key Derivation:** Upon successful validation of Sigma3 by the Responder, both parties possess all the necessary ingredients—shared secret, transcript hash, and identity proofs—to derive the final session keys: I2RKey (Initiator-to-Responder) and R2IKey (Responder-to-Initiator). The use of distinct keys for each direction prevents reflection attacks.4

## **3\. Detailed Formal Verification Analysis**

The core of the user's query pertains to the validation of claims made in the formal verification report. The provided artifacts include a Finite State Machine (FSM) model (case\_protocol\_fsm.json) and a set of Security Properties (case\_security\_properties.json). This section analyzes the logical soundness of these models against the protocol architecture.

### **3.1 Mutual Authentication Verification (CASE\_PROP\_001)**

**Claim:** The protocol guarantees mutual authentication. **Model Analysis:** The FSM explicitly models the transition from Sigma2\_Received to Session\_Keys\_Established as being contingent on responder\_noc\_validated \== true. Similarly, the Responder's transition to Session\_Keys\_Established requires initiator\_noc\_validated \== true.4 The validation logic is rigorous; it requires not just the presence of a certificate, but the cryptographic verification of the signature (tbs\_data2\_signature\_verified) covering the session unique random values. **Insight:** The formal model accurately captures the dependency between the cryptographic primitives and the authentication state. An attacker playing Man-in-the-Middle (MitM) might be able to intercept messages, but without the private keys, they cannot generate the valid signatures required to satisfy the signature\_verified invariants. Thus, the claim holds: mutual authentication is structurally enforced.

### **3.2 Forward Secrecy Verification (CASE\_PROP\_005)**

**Claim:** The protocol ensures forward secrecy via ephemeral key exchange. **Model Analysis:** The FSM enforces that initiator\_eph\_keypair and responder\_eph\_keypair are generated anew in the Sigma1\_Generated and Sigma2\_Generated states, respectively.4 The SharedSecret is derived from these ephemeral inputs. **Insight:** The formal verification confirms that the session keys are *not* derived from the static long-term keys (NOC keys). The long-term keys are used solely for *signing* (authentication), not for *encryption* (confidentiality) of the session secret. This separation of concerns is the textbook definition of Forward Secrecy. The verification correctly identifies this as a holding property.

### **3.3 Identity Protection and Privacy (CASE\_PROP\_007)**

**Claim:** Node identities are protected from passive observation. **Model Analysis:** The property Sigma1\_Destination\_ID\_Privacy asserts that an observer cannot derive the Fabric ID from the Destination ID without the IPK.4 The FSM correctly models the Destination ID as a function of the IPK and random inputs. Furthermore, the Encrypted\_Certificate\_Exchange property ensures that NOCs are encrypted in the tbe\_data structures.4 **Insight:** The verification validates that at no point in the handshake is the Subject Name (Node ID/Fabric ID) of the certificate transmitted in cleartext. This is a significant improvement over legacy protocols and is crucial for the privacy requirements of smart home devices.

### **3.4 Validated Specification Gaps**

The formal analysis identified specific "Specification Gaps." These are not failures of the verification process, but accurate identifications of potential weaknesses in the protocol specification itself.

#### **3.4.1 SPEC\_GAP\_001: Revocation Latency**

The report correctly identifies that the core CASE specification (prior to 1.4.2) relies on Access Control List (ACL) updates for revocation rather than an online check (OCSP) or a Certificate Revocation List (CRL).4 This means that if a device is compromised, it remains trusted by other nodes until the administrator manually removes its Node ID from the ACLs of every other device in the fabric.

* **Implication:** There is a window of vulnerability between the detection of a compromise and the propagation of the ACL update. In a mesh network with sleepy devices, this propagation is not instantaneous.  
* **Verdict:** This is a valid design trade-off for low-latency, offline-capable IoT networks. However, as discussed in Section 5, Matter 1.4.2 introduces CRLs to mitigate this.5

#### **3.4.2 SPEC\_GAP\_002: IPK Epoch Key Transition**

The report highlights a theoretical timing attack related to the rotation of the Identity Protection Key (IPK). The IPK is managed via "Epoch Keys," and during a rotation, devices may accept Destination Identifiers generated with either the old or the new key to ensure continuity.4

* **Implication:** This creates a transition window where the "exclusivity" of the key usage is slightly blurred. An attacker might exploit this to replay Sigma1 messages captured from a previous epoch, potentially confusing the responder or extending the window of validity for a captured session attempt.  
* **Verdict:** While theoretically valid, the practical exploitability is low due to the requirement of the specific InitiatorRandom in the hash. The verification report's classification of this as a "Minor Concern" rather than a "Critical Vulnerability" is appropriate.

## **4\. The Critical Blind Spot: Availability and CVE-2024-3297**

While the formal verification successfully validated the **safety** properties (Authentication, Secrecy), it failed to identify a critical **liveness** and **availability** vulnerability present in earlier versions of the specification and SDK. This oversight highlights a common limitation in formal methods: models often assume infinite resources or idealized state transitions unless explicitly constrained.

### **4.1 Vulnerability Analysis: CVE-2024-3297 (DeeDoS)**

**CVE-2024-3297** describes a "Session establishment lock-up" or "Delayed Denial of Service" (DeeDoS) vulnerability.6

* **The Mechanism:** The attack exploits the Sigma1 processing logic. When a Responder receives a Sigma1 message, it must allocate memory and state to track the "pending" session (waiting for Sigma3).  
* **The Flaw:** In affected versions (pre-Matter 1.1), the implementation did not adequately verify the freshness or uniqueness of the Sigma1 message *before* allocating this state. Crucially, the MessageCounter in the unencrypted header of Sigma1 is not cryptographically protected (as no session keys exist yet).  
* **The Exploit:** An attacker captures a legitimate Sigma1 message. They then replay this message repeatedly, perhaps modifying the unencrypted message counter to bypass simple deduplication checks. The victim device, following the protocol, allocates a session context for each "new" request.  
* **The Consequence:** The device has a finite number of session slots. The attacker floods the device, filling all available slots with half-open sessions. Since the attacker never sends the subsequent messages to complete the handshake, these sessions sit idle until a timeout occurs. If the attack is sustained, legitimate controllers cannot establish a new CASE session. The device becomes unresponsive to the smart home network, requiring a physical power cycle to recover.3

### **4.2 Why the Formal Model Missed It**

The provided FSM model focuses on the logical progression of a *single* session. It tracks transitions from Idle to Sigma1\_Received to Sigma2\_Generated.4

* **Missing Constraint:** The model does not include a session\_count variable or a MAX\_SESSIONS constraint. It implicitly assumes that if the inputs are valid (cryptographically), the transition *can* occur.  
* **Missing Liveness Property:** There is no property in case\_security\_properties.json that asserts "A legitimate initiator can always establish a session within time T." The properties focus on "If a session is established, it is secure," not "A session *can* be established."  
* **Validation Scope:** The verification checked for *cryptographic* replay protection (using the Transcript Hash in Sigma2/3) but missed the *resource* replay vulnerability in the unauthenticated Sigma1 phase.

### **4.3 Mitigation in Matter 1.4**

The Matter 1.4 specification and updated SDKs address this by implementing stricter pre-allocation checks.

* **Stateless Processing:** Implementations are encouraged to process Sigma1 statelessly or with minimal state (using cookies) until the initiator proves return routability or identity in Sigma3.  
* **Rate Limiting:** Strict rate limiting on Sigma1 messages from the same IP or Node ID prevents the rapid exhaustion of slots.  
* **Counter Validation:** Enhanced checks on the MessageCounter window, even for unencrypted messages, help discard obvious replays before resource allocation.6

## **5\. Security Property Verification Status Table**

The following table summarizes the verification status of the key properties, integrating the findings from the formal report and the independent vulnerability analysis.

| Property ID | Property Name | Formal Verdict | Independent Analysis Verdict | Key Justification |
| :---- | :---- | :---- | :---- | :---- |
| **CASE\_PROP\_001** | Mutual Authentication | **HOLDS** | **VALID** | Protocol logic requires NOC validation and signature verification on both sides before session activation. |
| **CASE\_PROP\_002** | Chain Validation | **HOLDS** | **VALID** | Trust anchor verification is structurally enforced in the FSM logic. |
| **CASE\_PROP\_003** | Fabric ID Match | **HOLDS** | **VALID** | Cross-fabric isolation is verified; Fabric ID in NOC matches the session context. |
| **CASE\_PROP\_005** | Ephemeral Key Exchange | **HOLDS** | **VALID** | Fresh ephemeral keys for every session ensure Perfect Forward Secrecy. |
| **CASE\_PROP\_007** | Destination ID Privacy | **HOLDS** | **VALID** | Hashed Destination ID prevents passive observers from identifying the target fabric. |
| **CASE\_PROP\_008** | IPK Exclusive Use | **PARTIAL** | **CONDITIONAL** | Specification intent holds, but implementation (Epoch rotation) creates a theoretical timing window (SPEC\_GAP\_002). |
| **CASE\_PROP\_011** | Encrypted Cert Exchange | **HOLDS** | **VALID** | Certificates are encrypted (AEAD) in Sigma2/3, protecting node identity from observers. |
| **CASE\_PROP\_016** | Message Counter Init | **HOLDS** | **VALID** | Counters are initialized to zero, protecting post-handshake traffic from replay. |
| **N/A** | **Resource Availability** | **NOT CHECKED** | **FAILED** | (Pre-1.1/Unpatched) Vulnerable to CVE-2024-3297 Sigma1 Replay DoS. Formal model lacked resource constraints. |
| **N/A** | **Revocation Check** | **PARTIAL** | **IMPROVED** | Core spec relied on ACLs (Gap 001). Matter 1.4.2 introduces CRLs, significantly strengthening this area. |

## **6\. Matter 1.4: Evolution and Enhanced Security Measures**

The release of Matter 1.4 and the subsequent 1.4.2 update introduce significant enhancements that address the identified gaps and strengthen the overall security posture.

### **6.1 Certificate Revocation Lists (CRLs)**

As identified in **SPEC\_GAP\_001**, the reliance on ACLs for revocation was a latency risk. Matter 1.4.2 introduces a standardized mechanism for **Certificate Revocation Lists (CRLs)**. Ecosystems and commissioners can now publish CRLs to the Distributed Compliance Ledger (DCL). Devices can fetch these lists (or receive them from controllers) to perform real-time validity checks on NOCs and DACs during the handshake.2 This effectively closes the revocation gap, ensuring that compromised credentials can be blacklisted globally and near-instantaneously.

### **6.2 Home Routers and Access Points (HRAP)**

Matter 1.4 introduces the **Home Router and Access Point (HRAP)** device type. This is a strategic move to secure the underlying network infrastructure. HRAPs combine a Wi-Fi access point and a Thread Border Router into a single, Matter-certified device.8

* **Secure Credential Storage:** HRAPs feature a "secure directory" for storing Thread network credentials. This centralizes trust and reduces the fragmentation of network keys, which previously had to be managed by individual border routers or mobile apps.  
* **Infrastructure-Level Control:** By certifying the network equipment itself, Matter extends its security model down to the transport layer, ensuring that the devices facilitating the CASE protocol traffic are themselves hardened against attacks.

### **6.3 Enhanced Multi-Admin and Quieter Reporting**

The **Enhanced Multi-Admin** feature simplifies the sharing of devices across fabrics (e.g., controlling a light via both Apple Home and Alexa). From a security perspective, this requires rigorous enforcement of **Fabric Isolation** to ensure that granting access to a second ecosystem does not leak credentials from the first.9 The "Quieter Reporting" feature optimizes network traffic by reducing the frequency of attribute updates.10 While primarily a performance feature, it indirectly enhances security by reducing the "noise" on the network, making traffic analysis slightly more difficult for attackers trying to infer device activity patterns.

## **7\. Conclusions and Final Decision**

The formal verification of the Matter CASE protocol yields a nuanced but generally positive verdict. The protocol's cryptographic core is robust, leveraging industry-standard primitives (SIGMA-I, ECDH-P256, AES-CCM) to achieve strong properties of **Mutual Authentication**, **Forward Secrecy**, and **Identity Privacy**. The formal model accurately confirms that, assuming infinite resources and correct implementation, the protocol logic prevents unauthorized access and data leakage.

However, the "final decision" regarding the protocol's vulnerability status must account for the critical distinction between *protocol logic* and *system implementation*.

1. **Cryptographic Soundness:** The analysis confirms that the claims of authentication and secrecy are **Valid**. The protocol design is secure against standard cryptographic attacks (MitM, Replay of Session Data, Identity Correlation).  
2. **Operational Vulnerability:** The independent review identified a critical blind spot in the formal verification regarding **Availability**. The protocol (specifically in versions prior to 1.1) is vulnerable to **CVE-2024-3297**, a resource exhaustion attack via Sigma1 replay. The formal model failed to detect this because it did not model finite resource constraints (session slots).  
3. **Specification Gaps:** The identified gaps regarding revocation and key rotation are valid. However, the introduction of **CRLs in Matter 1.4.2** effectively mitigates the revocation latency risk, transforming a "Gap" into a "Managed Feature."

**Final Decision:**

The Matter CASE protocol is **Cryptographically Sound** and secure for its intended purpose of authenticated session establishment. The claims in the formal verification report regarding safety properties are **Verified**. However, the claim of *total* security assurance is **Incomplete** due to the historical susceptibility to Resource Exhaustion (DoS).

**Recommendation:**

To "find vulnerabilities for sure," the formal verification model must be expanded to include **Liveness Properties** and **Resource Constraints**. Specifically, the model should introduce a MAX\_SESSIONS state variable and verify that a legitimate Initiator can successfully complete a handshake even when an adversary is flooding the Responder with Sigma1 messages. Without this expansion, the formal verification remains blind to Denial-of-Service vectors.

For deployment, it is strictly recommended to utilize **Matter SDK version 1.4.2 or later**, which contains the necessary mitigations for CVE-2024-3297 and implements the new CRL-based revocation checks, ensuring both the safety and availability of the smart home network.

#### **Works cited**

1. Introduction to Matter: Why, What and How \- Silicon Labs, accessed February 3, 2026, [https://www.silabs.com/documents/login/presentations/mat101-introduction-to-the-matter-specification.pdf](https://www.silabs.com/documents/login/presentations/mat101-introduction-to-the-matter-specification.pdf)  
2. Matter 1.4.2 | Enhancing Security and Scalability for Smart Homes \- CSA-IOT, accessed February 3, 2026, [https://csa-iot.org/newsroom/matter-1-4-2-enhancing-security-and-scalability-for-smart-homes/](https://csa-iot.org/newsroom/matter-1-4-2-enhancing-security-and-scalability-for-smart-homes/)  
3. Breaking Matter: vulnerabilities in the Matter protocol \- Black Hat, accessed February 3, 2026, [http://i.blackhat.com/EU-24/Presentations/EU-24-Genge-BreakingMatterVulnerabiltiesInTheMatterProtocol-wp.pdf](http://i.blackhat.com/EU-24/Presentations/EU-24-Genge-BreakingMatterVulnerabiltiesInTheMatterProtocol-wp.pdf)  
4. case\_security\_properties.json  
5. Matter and Certificate Revocation \- Espressif Developer Portal, accessed February 3, 2026, [https://developer.espressif.com/blog/matter-and-certificate-revocation/](https://developer.espressif.com/blog/matter-and-certificate-revocation/)  
6. CVE-2024-3297 Detail \- NVD, accessed February 3, 2026, [https://nvd.nist.gov/vuln/detail/CVE-2024-3297](https://nvd.nist.gov/vuln/detail/CVE-2024-3297)  
7. CVE-2024-3297 Connectivity Standards Alliance Matter resource consumption \- VulDB, accessed February 3, 2026, [https://vuldb.com/?id.272358](https://vuldb.com/?id.272358)  
8. CSA Unveils Matter 1.4: New Horizons for Smart Home Interoperability & Energy Management \- Granite River Labs, accessed February 3, 2026, [https://www.graniteriverlabs.com/en-us/technical-blog/csa-matter-1.4-released](https://www.graniteriverlabs.com/en-us/technical-blog/csa-matter-1.4-released)  
9. Matter 1.4 Enables More Capable Smart Homes \- CSA-IOT, accessed February 3, 2026, [https://csa-iot.org/newsroom/matter-1-4-enables-more-capable-smart-homes/](https://csa-iot.org/newsroom/matter-1-4-enables-more-capable-smart-homes/)  
10. Matter 1.4.2 brings Wi-Fi only setup and enhanced base experience, accessed February 3, 2026, [https://www.matteralpha.com/industry-news/matter-1-4-2-brings-wi-fi-only-setup-and-enhanced-base-experience](https://www.matteralpha.com/industry-news/matter-1-4-2-brings-wi-fi-only-setup-and-enhanced-base-experience)