# Chapter 12 Analysis - FSM Extraction

## Overview
Chapter 12 covers THREE major protocol areas:
1. **Joint Fabric Creation** (Sections 12.2.1-12.2.5)
2. **Anchor Administrator Management** (Sections 12.2.6-12.2.7)
3. **Fabric Synchronization** (Section 12.6)

Each has distinct state machines that interact.

---

## FSM 1: Joint Commissioning Method (JCM)

### Key Entities
- Ecosystem A Administrator (Anchor)
- Ecosystem B Administrator (Joining)
- Device Conformance List (DCL)
- Root CA (Anchor CA)
- ICAC (Intermediate Certificate Authority)

### States Identified

1. **JCM_Idle**
   - Initial state
   - No commissioning in progress
   - Invariants: no_active_jcm_session

2. **JCM_Discovery**
   - Ecosystem B advertises via DNS-SD
   - Awaiting Ecosystem A to discover
   - Invariants: dns_sd_active, jf_txt_key_advertised

3. **JCM_ECM_BCM_InProgress**
   - Ecosystem A commissioning Ecosystem B Admin
   - PASE session active
   - Device attestation in progress
   - Invariants: pase_session_active, device_attestation_pending

4. **JCM_ECM_Complete_AwaitingCATVerification**
   - ECM/BCM completed
   - Must verify Anchor CAT in Eco A's NOC
   - Invariants: ecm_complete, anchor_cat_verification_pending

5. **JCM_UserConsent_Pending**
   - Waiting for user consent on Ecosystem B
   - Invariants: cat_verified, user_consent_pending

6. **JCM_RCAC_Validation_InProgress**
   - Validating Ecosystem A's RCAC via DCL
   - Vendor ID validation in progress
   - Invariants: user_consent_obtained, dcl_query_sent

7. **JCM_RCAC_Validated_AwaitingICACSR**
   - RCAC validation successful
   - Ready to request ICA cross-signing
   - Invariants: rcac_validated, icacsr_not_sent

8. **JCM_ICACSR_Sent_AwaitingEcoA_UserConsent**
   - ICA CSR sent to Ecosystem A
   - Waiting for Eco A user consent
   - Invariants: icacsr_sent, eco_a_user_consent_pending

9. **JCM_ICACSR_EcoA_Validating**
   - Ecosystem A validating ICA CSR
   - Checking format, signature, ICAC vendor ID
   - Invariants: eco_a_user_consent_obtained, csr_validation_in_progress

10. **JCM_ICACSR_CrossSigning_InProgress**
    - Ecosystem A Root CA signing the ICA CSR
    - Invariants: csr_validated, signing_in_progress

11. **JCM_CrossSigned_ICAC_Received**
    - Ecosystem B received cross-signed ICAC
    - Ready to update fabric
    - Invariants: cross_signed_icac_received, fabric_update_pending

12. **JCM_FabricUpdate_InProgress**
    - Updating all Fabric B nodes
    - Adding new RCAC, updating NOCs, removing old fabric
    - Invariants: cross_signed_icac_valid, nodes_updating

13. **JCM_Complete_JointFabric_Active**
    - All Fabric B nodes updated
    - Joint Fabric operational
    - Invariants: all_nodes_updated, joint_fabric_active

14. **JCM_Failed_CAT_Verification**
    - Error state: Anchor CAT not found in Eco A's NOC
    - Invariants: anchor_cat_missing, jcm_aborted

15. **JCM_Failed_UserConsent_Denied**
    - Error state: User denied consent
    - Invariants: user_consent_denied, jcm_aborted

16. **JCM_Failed_RCAC_Validation**
    - Error state: DCL validation failed or not RCAC
    - Invariants: rcac_validation_failed, jcm_aborted

17. **JCM_Failed_ICACSR_Format**
    - Error state: ICA CSR format invalid
    - Invariants: csr_format_invalid, jcm_aborted

18. **JCM_Failed_ICACSR_Signature**
    - Error state: ICA CSR signature invalid
    - Invariants: csr_signature_invalid, jcm_aborted

19. **JCM_Failed_DCL_VendorID_Validation**
    - Error state: ICAC vendor ID validation failed
    - Invariants: vendor_id_validation_failed, jcm_aborted

20. **JCM_Failed_CrossSigning**
    - Error state: Root CA failed to sign ICA
    - Invariants: cross_signing_failed, jcm_aborted

### Transitions for JCM

**T1: JCM_Idle → JCM_Discovery**
- Trigger: user_initiates_jcm
- Guard: ecosystem_b_supports_joint_fabric
- Actions:
  - advertise_dns_sd_with_jf_txt_key()
  - generate_qr_code()
  - generate_manual_pairing_code()

**T2: JCM_Discovery → JCM_ECM_BCM_InProgress**
- Trigger: ecosystem_a_initiates_commissioning
- Guard: dns_sd_discovered && pairing_code_entered
- Actions:
  - establish_pase_session()
  - begin_device_attestation()

**T3: JCM_ECM_BCM_InProgress → JCM_ECM_Complete_AwaitingCATVerification**
- Trigger: ecm_bcm_complete_event
- Guard: device_attestation_success && noc_received
- Actions:
  - store_eco_a_noc()
  - store_eco_a_rcac()
  - store_eco_a_icac()

**T4: JCM_ECM_Complete_AwaitingCATVerification → JCM_UserConsent_Pending**
- Trigger: verify_anchor_cat_command
- Guard: has_anchor_cat(eco_a_noc) || has_anchor_datastore_cat(eco_a_noc)
- Actions:
  - mark_anchor_cat_verified()
  - prompt_user_consent()

**T5: JCM_ECM_Complete_AwaitingCATVerification → JCM_Failed_CAT_Verification**
- Trigger: verify_anchor_cat_command
- Guard: !has_anchor_cat(eco_a_noc) && !has_anchor_datastore_cat(eco_a_noc)
- Actions:
  - abort_jcm()
  - generate_error_event(anchor_cat_missing)

**T6: JCM_UserConsent_Pending → JCM_RCAC_Validation_InProgress**
- Trigger: user_consent_obtained
- Guard: user_approved
- Actions:
  - extract_rcac_pubkey(eco_a_rcac)
  - dcl_vendor_id_validate_rcac(eco_a_rcac.pubkey, eco_a_rcac.algo, eco_a_rcac.curve, eco_a_vendor_id)

**T7: JCM_UserConsent_Pending → JCM_Failed_UserConsent_Denied**
- Trigger: user_consent_denied
- Guard: !user_approved
- Actions:
  - abort_jcm()
  - generate_error_event(user_consent_denied)

**T8: JCM_RCAC_Validation_InProgress → JCM_RCAC_Validated_AwaitingICACSR**
- Trigger: dcl_validation_result
- Guard: dcl_result == success && is_valid_rcac(returned_cert)
- Actions:
  - mark_rcac_validated()
  - prepare_ica_csr()

**T9: JCM_RCAC_Validation_InProgress → JCM_Failed_RCAC_Validation**
- Trigger: dcl_validation_result
- Guard: dcl_result == failure || !is_valid_rcac(returned_cert)
- Actions:
  - abort_jcm()
  - generate_error_event(rcac_validation_failed)

**T10: JCM_RCAC_Validated_AwaitingICACSR → JCM_ICACSR_Sent_AwaitingEcoA_UserConsent**
- Trigger: send_icacsr_request
- Guard: ica_csr_prepared
- Actions:
  - generate_ica_csr(eco_b_ica_private_key, anchor_fabric_id)
  - send_icacsr_request_command(ica_csr)

**T11: JCM_ICACSR_Sent_AwaitingEcoA_UserConsent → JCM_ICACSR_EcoA_Validating**
- Trigger: eco_a_user_consent_obtained
- Guard: eco_a_user_approved
- Actions:
  - validate_ica_csr_format()

**T12: JCM_ICACSR_Sent_AwaitingEcoA_UserConsent → JCM_Failed_UserConsent_Denied**
- Trigger: eco_a_user_consent_denied
- Guard: !eco_a_user_approved
- Actions:
  - send_icacsr_response(IcaCsrRequestNoUserConsent)
  - abort_jcm()

**T13: JCM_ICACSR_EcoA_Validating → JCM_Failed_ICACSR_Format**
- Trigger: csr_format_validation_complete
- Guard: !is_valid_pkcs10_format(ica_csr)
- Actions:
  - send_icacsr_response(InvalidIcaCsrFormat)
  - abort_jcm()

**T14: JCM_ICACSR_EcoA_Validating → JCM_Failed_ICACSR_Signature**
- Trigger: csr_signature_validation_complete
- Guard: is_valid_pkcs10_format(ica_csr) && !verify_signature(ica_csr.signature, ica_csr.pubkey)
- Actions:
  - send_icacsr_response(InvalidIcaCsrSignature)
  - abort_jcm()

**T15: JCM_ICACSR_EcoA_Validating → JCM_Failed_DCL_VendorID_Validation**
- Trigger: dcl_icac_validation_result
- Guard: is_valid_pkcs10_format(ica_csr) && verify_signature(ica_csr.signature, ica_csr.pubkey) && (dcl_icac_result == empty_list || !is_valid_icac(dcl_returned_cert))
- Actions:
  - send_icacsr_response(FailedDCLVendorIdValidation || NotAnIcac)
  - abort_jcm()

**T16: JCM_ICACSR_EcoA_Validating → JCM_ICACSR_CrossSigning_InProgress**
- Trigger: dcl_icac_validation_result
- Guard: is_valid_pkcs10_format(ica_csr) && verify_signature(ica_csr.signature, ica_csr.pubkey) && dcl_icac_result == valid && is_valid_icac(dcl_returned_cert)
- Actions:
  - request_root_ca_sign(ica_csr)

**T17: JCM_ICACSR_CrossSigning_InProgress → JCM_CrossSigned_ICAC_Received**
- Trigger: cross_signing_complete
- Guard: signing_success
- Actions:
  - send_icacsr_response(cross_signed_icac, pem_format)
  - store_cross_signed_icac()

**T18: JCM_ICACSR_CrossSigning_InProgress → JCM_Failed_CrossSigning**
- Trigger: cross_signing_failed
- Guard: !signing_success
- Actions:
  - send_icacsr_response(IcaCsrSigningFailed)
  - abort_jcm()

**T19: JCM_CrossSigned_ICAC_Received → JCM_FabricUpdate_InProgress**
- Trigger: begin_fabric_update
- Guard: cross_signed_icac_valid
- Actions:
  - foreach_node_in_fabric_b(add_trusted_root_certificate(anchor_rcac))
  - foreach_node_in_fabric_b(add_noc_with_anchor_fabric_id())

**T20: JCM_FabricUpdate_InProgress → JCM_Complete_JointFabric_Active**
- Trigger: all_nodes_updated
- Guard: all_nodes_added_rcac && all_nodes_updated_noc
- Actions:
  - foreach_node_in_fabric_b(remove_fabric(old_rcac))
  - mark_joint_fabric_active()
  - generate_event(jcm_complete)

---

## FSM 2: Anchor Administrator Transfer

### States Identified

1. **AnchorTransfer_Idle**
   - Initial state
   - No anchor transfer in progress
   - Invariants: no_transfer_active

2. **AnchorTransfer_Requested**
   - Admin B sent TransferAnchorRequest to Admin A
   - Awaiting Admin A processing
   - Invariants: transfer_request_sent, admin_b_user_consent_obtained

3. **AnchorTransfer_AdminA_CheckingConsent**
   - Admin A checking user consent
   - Invariants: request_received, consent_check_in_progress

4. **AnchorTransfer_AdminA_CheckingAdminCAT**
   - Admin A verifying Admin B has Administrator CAT
   - Invariants: user_consent_obtained, admin_cat_verification_in_progress

5. **AnchorTransfer_AdminA_CheckingDatastoreStatus**
   - Admin A checking datastore entries for Pending/DeletePending
   - Invariants: admin_cat_verified, datastore_status_check_in_progress

6. **AnchorTransfer_AdminA_SettingReadOnly**
   - Admin A setting datastore to read-only (DeletePending)
   - Stopping DNS-SD advertising
   - Invariants: datastore_not_busy, setting_readonly

7. **AnchorTransfer_AdminA_ReadOnly_AdminsStoppingCommissioning**
   - Datastore in read-only
   - All admins detecting and stopping commissioning
   - Invariants: datastore_status == DeletePending, dns_sd_stopped

8. **AnchorTransfer_AdminB_CopyingDatastore**
   - Admin B copying datastore from Admin A
   - Invariants: readonly_active, datastore_copy_in_progress

9. **AnchorTransfer_AdminB_UpdatingDatastore**
   - Admin B updating datastore (StatusEntry=Committed, AnchorNodeId=B)
   - Incrementing Administrator CAT version
   - Invariants: datastore_copied, updating_datastore

10. **AnchorTransfer_AdminB_UpdatingAdministrators**
    - Admin B updating NOCs of all other administrators
    - Using new Administrator CAT version
    - Invariants: datastore_committed, updating_admin_nocs

11. **AnchorTransfer_AdminB_IssuingSelfNOC**
    - Admin B issuing itself new NOC with Anchor/Datastore CAT
    - Invariants: admins_updated, self_noc_pending

12. **AnchorTransfer_AdminB_AdvertisingAsAnchor**
    - Admin B advertising as Anchor/Datastore via DNS-SD
    - Invariants: self_noc_issued, dns_sd_starting

13. **AnchorTransfer_AdminB_NotifyingCompletion**
    - Admin B sending TransferAnchorComplete to Admin A
    - Invariants: dns_sd_active, completion_notification_sending

14. **AnchorTransfer_OtherAdmins_Discovering**
    - Other admins discovering new Anchor via DNS-SD
    - Subscribing to new datastore
    - Invariants: transfer_complete_received, admins_discovering

15. **AnchorTransfer_OtherAdmins_VerifyingNewAnchor**
    - Admins verifying new Anchor has Anchor/Datastore CAT
    - Checking NOC chains to Anchor ICAC
    - Invariants: new_datastore_discovered, anchor_verification_in_progress

16. **AnchorTransfer_OtherAdmins_RequestingICACSR**
    - Admins requesting ICA Cross Signing from new Anchor
    - Invariants: new_anchor_verified, icacsr_request_sending

17. **AnchorTransfer_OtherAdmins_RemovingOldFabric**
    - Admins removing old fabric via RemoveFabric
    - Invariants: new_icac_received, old_fabric_removal_in_progress

18. **AnchorTransfer_Complete_NewAnchor_Active**
    - Transfer complete
    - New Anchor operational
    - All admins using new ICAC
    - Invariants: old_fabric_removed, new_anchor_active

19. **AnchorTransfer_Failed_NoUserConsent**
    - Error: Admin A user consent not obtained
    - Invariants: user_consent_denied

20. **AnchorTransfer_Failed_NoAdminCAT**
    - Error: Admin B doesn't have Administrator CAT
    - Invariants: admin_cat_missing

21. **AnchorTransfer_Failed_DatastoreBusy**
    - Error: Datastore has Pending/DeletePending entries
    - Invariants: datastore_busy

### Transitions for Anchor Transfer

**T1: AnchorTransfer_Idle → AnchorTransfer_Requested**
- Trigger: user_initiates_anchor_transfer
- Guard: admin_b_user_consent_obtained
- Actions:
  - send_transfer_anchor_request(admin_a)

**T2: AnchorTransfer_Requested → AnchorTransfer_AdminA_CheckingConsent**
- Trigger: transfer_anchor_request_received
- Guard: true
- Actions:
  - check_user_consent()

**T3: AnchorTransfer_AdminA_CheckingConsent → AnchorTransfer_AdminA_CheckingAdminCAT**
- Trigger: consent_check_complete
- Guard: user_consent_obtained
- Actions:
  - verify_admin_b_has_admin_cat()

**T4: AnchorTransfer_AdminA_CheckingConsent → AnchorTransfer_Failed_NoUserConsent**
- Trigger: consent_check_complete
- Guard: !user_consent_obtained
- Actions:
  - send_transfer_anchor_response(TransferAnchorStatusNoUserConsent)
  - abort_transfer()

**T5: AnchorTransfer_AdminA_CheckingAdminCAT → AnchorTransfer_AdminA_CheckingDatastoreStatus**
- Trigger: admin_cat_verification_complete
- Guard: has_administrator_cat(admin_b_noc)
- Actions:
  - check_datastore_entries_status()

**T6: AnchorTransfer_AdminA_CheckingAdminCAT → AnchorTransfer_Failed_NoAdminCAT**
- Trigger: admin_cat_verification_complete
- Guard: !has_administrator_cat(admin_b_noc)
- Actions:
  - send_transfer_anchor_response(AdminCATMissing)
  - abort_transfer()

**T7: AnchorTransfer_AdminA_CheckingDatastoreStatus → AnchorTransfer_AdminA_SettingReadOnly**
- Trigger: datastore_status_check_complete
- Guard: all_entries_not_pending()
- Actions:
  - set_datastore_status_entry(DeletePending)

**T8: AnchorTransfer_AdminA_CheckingDatastoreStatus → AnchorTransfer_Failed_DatastoreBusy**
- Trigger: datastore_status_check_complete
- Guard: any_entry_pending_or_delete_pending()
- Actions:
  - send_transfer_anchor_response(TransferAnchorStatusDatastoreBusy)
  - abort_transfer()

**T9: AnchorTransfer_AdminA_SettingReadOnly → AnchorTransfer_AdminA_ReadOnly_AdminsStoppingCommissioning**
- Trigger: readonly_set_complete
- Guard: datastore_status == DeletePending
- Actions:
  - stop_dns_sd_advertising(Administrator, Anchor, Datastore)
  - set_busy_anchor_transfer_error_for_icacsr()

**T10: AnchorTransfer_AdminA_ReadOnly_AdminsStoppingCommissioning → AnchorTransfer_AdminB_CopyingDatastore**
- Trigger: all_admins_stopped_commissioning
- Guard: dns_sd_stopped
- Actions:
  - admin_b_copy_datastore_from_admin_a()

**T11: AnchorTransfer_AdminB_CopyingDatastore → AnchorTransfer_AdminB_UpdatingDatastore**
- Trigger: datastore_copy_complete
- Guard: datastore_copy_success
- Actions:
  - set_datastore_status_entry(Committed)
  - set_datastore_anchor_node_id(admin_b_node_id)
  - increment_administrator_cat_version()

**T12: AnchorTransfer_AdminB_UpdatingDatastore → AnchorTransfer_AdminB_UpdatingAdministrators**
- Trigger: datastore_update_complete
- Guard: datastore_committed
- Actions:
  - foreach_admin_except_admin_a(add_trusted_root_certificate(new_rcac))
  - foreach_admin_except_admin_a(add_noc_with_new_admin_cat_version())

**T13: AnchorTransfer_AdminB_UpdatingAdministrators → AnchorTransfer_AdminB_IssuingSelfNOC**
- Trigger: all_admins_updated
- Guard: all_nocs_updated
- Actions:
  - issue_self_noc_with_anchor_datastore_cat()

**T14: AnchorTransfer_AdminB_IssuingSelfNOC → AnchorTransfer_AdminB_AdvertisingAsAnchor**
- Trigger: self_noc_issued
- Guard: has_anchor_datastore_cat(self_noc)
- Actions:
  - advertise_dns_sd(Administrator, Anchor, Datastore)

**T15: AnchorTransfer_AdminB_AdvertisingAsAnchor → AnchorTransfer_AdminB_NotifyingCompletion**
- Trigger: dns_sd_active
- Guard: advertising_capabilities
- Actions:
  - send_transfer_anchor_complete(admin_a)

**T16: AnchorTransfer_AdminB_NotifyingCompletion → AnchorTransfer_OtherAdmins_Discovering**
- Trigger: transfer_anchor_complete_sent
- Guard: true
- Actions:
  - other_admins_discover_new_datastore()

**T17: AnchorTransfer_OtherAdmins_Discovering → AnchorTransfer_OtherAdmins_VerifyingNewAnchor**
- Trigger: new_datastore_discovered
- Guard: discovered_via_jf_txt_key
- Actions:
  - verify_anchor_datastore_cat_in_noc()
  - verify_noc_chains_to_anchor_icac()

**T18: AnchorTransfer_OtherAdmins_VerifyingNewAnchor → AnchorTransfer_OtherAdmins_RequestingICACSR**
- Trigger: anchor_verification_complete
- Guard: anchor_cat_verified && chain_verified
- Actions:
  - request_ica_cross_signing(new_anchor)

**T19: AnchorTransfer_OtherAdmins_RequestingICACSR → AnchorTransfer_OtherAdmins_RemovingOldFabric**
- Trigger: new_icac_received
- Guard: cross_signed_icac_valid
- Actions:
  - remove_fabric(old_anchor_ca)

**T20: AnchorTransfer_OtherAdmins_RemovingOldFabric → AnchorTransfer_Complete_NewAnchor_Active**
- Trigger: old_fabric_removed
- Guard: all_devices_removed_from_old_fabric
- Actions:
  - start_commissioning_with_new_icac()
  - generate_event(anchor_transfer_complete)

---

## FSM 3: Administrator Removal

### States Identified

1. **AdminRemoval_Idle**
   - No removal in progress
   - Invariants: no_removal_active

2. **AdminRemoval_Requested**
   - Anchor admin initiating removal
   - User consent obtained
   - Invariants: user_consent_obtained, target_admin_identified

3. **AdminRemoval_SendingRemoveFabric**
   - Sending RemoveFabric command to target admin
   - Invariants: removal_initiated

4. **AdminRemoval_TargetRemoving**
   - Target admin removing fabric and deleting fabric-scoped data
   - Invariants: remove_fabric_command_received

5. **AdminRemoval_AnchorUpdatingDatastore**
   - Anchor removing target from Joint Fabric Datastore
   - Invariants: target_removed_fabric, datastore_update_in_progress

6. **AdminRemoval_AnchorIncrementingCAT**
   - Anchor incrementing Administrator CAT version
   - Invariants: datastore_updated

7. **AdminRemoval_AnchorIssuingSelfNOC**
   - Anchor issuing itself new NOC with new CAT version
   - Invariants: cat_version_incremented

8. **AdminRemoval_AnchorUpdatingOtherAdmins**
   - Anchor updating NOCs of all remaining admins
   - Invariants: anchor_noc_updated

9. **AdminRemoval_Complete**
   - Administrator successfully removed
   - Invariants: all_admins_updated, target_removed

10. **AdminRemoval_Recommended_AnchorTransition**
    - Optional: Transitioning to new Anchor to ensure cryptographic revocation
    - Invariants: removal_complete, anchor_transition_recommended

### Transitions for Administrator Removal

**T1: AdminRemoval_Idle → AdminRemoval_Requested**
- Trigger: user_requests_admin_removal
- Guard: user_consent_obtained
- Actions:
  - identify_target_admin()

**T2: AdminRemoval_Requested → AdminRemoval_SendingRemoveFabric**
- Trigger: begin_removal
- Guard: target_admin_valid
- Actions:
  - send_remove_fabric_command(target_admin)

**T3: AdminRemoval_SendingRemoveFabric → AdminRemoval_TargetRemoving**
- Trigger: remove_fabric_command_sent
- Guard: true
- Actions:
  - await_target_removal()

**T4: AdminRemoval_TargetRemoving → AdminRemoval_AnchorUpdatingDatastore**
- Trigger: target_fabric_removed
- Guard: target_deleted_fabric_scoped_data
- Actions:
  - remove_target_from_datastore()

**T5: AdminRemoval_AnchorUpdatingDatastore → AdminRemoval_AnchorIncrementingCAT**
- Trigger: datastore_updated
- Guard: target_removed_from_datastore
- Actions:
  - increment_administrator_cat_version()

**T6: AdminRemoval_AnchorIncrementingCAT → AdminRemoval_AnchorIssuingSelfNOC**
- Trigger: cat_version_incremented
- Guard: new_cat_version > old_cat_version
- Actions:
  - issue_self_noc_with_new_cat()

**T7: AdminRemoval_AnchorIssuingSelfNOC → AdminRemoval_AnchorUpdatingOtherAdmins**
- Trigger: anchor_noc_issued
- Guard: has_new_cat_version(anchor_noc)
- Actions:
  - foreach_remaining_admin(set_noc_with_new_cat())

**T8: AdminRemoval_AnchorUpdatingOtherAdmins → AdminRemoval_Complete**
- Trigger: all_admins_updated
- Guard: all_nocs_have_new_cat_version
- Actions:
  - generate_event(admin_removal_complete)

**T9: AdminRemoval_Complete → AdminRemoval_Recommended_AnchorTransition**
- Trigger: security_consideration_check
- Guard: cryptographic_revocation_desired
- Actions:
  - initiate_anchor_transition_to_new_rcac()

---

## FSM 4: Fabric Synchronization Setup

### States Identified

1. **FabricSync_Idle**
   - No synchronization setup in progress
   - Invariants: no_sync_active

2. **FabricSync_Commissionee_AdvertisingDNS_SD**
   - Commissionee advertising presence
   - Providing QR/Manual code
   - Invariants: dns_sd_active, pairing_codes_available

3. **FabricSync_Commissioner_Discovering**
   - Commissioner discovering commissionee
   - Invariants: discovery_in_progress

4. **FabricSync_ForwardCommissioning_InProgress**
   - Commissioner commissioning commissionee
   - Concurrent connection commissioning flow
   - Invariants: commissioning_active

5. **FabricSync_ForwardCommissioning_Complete_AggregatorAccessible**
   - Commissionee's Aggregator now accessible on commissioner's fabric
   - Invariants: commissioning_complete, aggregator_accessible

6. **FabricSync_Commissioner_RequestingApproval**
   - Commissioner requesting commissioning approval via Commissioner Control Cluster
   - Invariants: aggregator_accessible, approval_request_sent

7. **FabricSync_Commissionee_UserConsent_Pending**
   - Commissionee asking user for consent
   - Invariants: approval_request_received, user_consent_pending

8. **FabricSync_ReverseCommissioning_InProgress**
   - Commissionee commissioning commissioner (reverse flow)
   - Invariants: user_consent_obtained, reverse_commissioning_active

9. **FabricSync_ReverseCommissioning_Complete_BidirectionalSetup**
   - Both ecosystems commissioned each other
   - Mutual authentication complete
   - Invariants: bidirectional_commissioning_complete, mutual_attestation_verified

10. **FabricSync_Configuration_Pending**
    - Both ecosystems asking users for sync configuration
    - Invariants: bidirectional_setup_complete, config_pending

11. **FabricSync_DeviceSynchronization_InProgress**
    - Ecosystems commissioning synchronized devices
    - Invariants: config_obtained, device_sync_active

12. **FabricSync_Complete_Active**
    - Fabric synchronization operational
    - Invariants: devices_synchronized, sync_active

13. **FabricSync_Failed_ConsentDenied**
    - Error: User denied consent
    - Invariants: consent_denied

14. **FabricSync_Failed_ReverseRequired**
    - Error: Reverse commissioning required but not completed
    - Invariants: reverse_required, reverse_not_complete

### Transitions for Fabric Synchronization

**T1: FabricSync_Idle → FabricSync_Commissionee_AdvertisingDNS_SD**
- Trigger: user_initiates_fabric_sync
- Guard: supports_fabric_synchronization
- Actions:
  - advertise_dns_sd()
  - generate_qr_code()
  - generate_manual_pairing_code()

**T2: FabricSync_Commissionee_AdvertisingDNS_SD → FabricSync_Commissioner_Discovering**
- Trigger: commissioner_scans_qr_or_enters_code
- Guard: dns_sd_discoverable
- Actions:
  - discover_commissionee()

**T3: FabricSync_Commissioner_Discovering → FabricSync_ForwardCommissioning_InProgress**
- Trigger: commissionee_discovered
- Guard: true
- Actions:
  - initiate_concurrent_connection_commissioning()

**T4: FabricSync_ForwardCommissioning_InProgress → FabricSync_ForwardCommissioning_Complete_AggregatorAccessible**
- Trigger: commissioning_complete_event
- Guard: commissioning_success
- Actions:
  - verify_aggregator_accessible()

**T5: FabricSync_ForwardCommissioning_Complete_AggregatorAccessible → FabricSync_Commissioner_RequestingApproval**
- Trigger: aggregator_accessible_verified
- Guard: aggregator_accessible_on_commissioner_fabric
- Actions:
  - send_request_commissioning_approval(commissioner_control_cluster)

**T6: FabricSync_Commissioner_RequestingApproval → FabricSync_Commissionee_UserConsent_Pending**
- Trigger: approval_request_received
- Guard: true
- Actions:
  - prompt_user_consent()

**T7: FabricSync_Commissionee_UserConsent_Pending → FabricSync_ReverseCommissioning_InProgress**
- Trigger: user_consent_obtained
- Guard: user_approved
- Actions:
  - send_commissioning_request_result(SUCCESS)
  - send_commission_node_command()
  - open_commissioning_window_for_commissioner()

**T8: FabricSync_Commissionee_UserConsent_Pending → FabricSync_Failed_ConsentDenied**
- Trigger: user_consent_denied
- Guard: !user_approved
- Actions:
  - send_commissioning_request_result(CONSENT_DENIED)
  - abort_sync()

**T9: FabricSync_ReverseCommissioning_InProgress → FabricSync_ReverseCommissioning_Complete_BidirectionalSetup**
- Trigger: reverse_commissioning_complete_event
- Guard: commissioning_success
- Actions:
  - verify_mutual_attestation()

**T10: FabricSync_ReverseCommissioning_Complete_BidirectionalSetup → FabricSync_Configuration_Pending**
- Trigger: mutual_attestation_verified
- Guard: attestation_valid
- Actions:
  - prompt_both_users_for_config()

**T11: FabricSync_Configuration_Pending → FabricSync_DeviceSynchronization_InProgress**
- Trigger: config_obtained_from_both_users
- Guard: sync_config_valid
- Actions:
  - discover_synchronized_devices_via_partslist()

**T12: FabricSync_DeviceSynchronization_InProgress → FabricSync_Complete_Active**
- Trigger: all_devices_commissioned
- Guard: all_sync_devices_accessible
- Actions:
  - generate_event(fabric_sync_complete)

**T13: FabricSync_ReverseCommissioning_Complete_BidirectionalSetup → FabricSync_Failed_ReverseRequired**
- Trigger: commissionee_requires_reverse
- Guard: reverse_commissioning_not_complete && requires_reverse_commissioning
- Actions:
  - abort_sync()
  - generate_error_event(reverse_required)

---

## FSM 5: Synchronized Device Commissioning

### States Identified

1. **SyncDevice_Idle**
   - Device not being commissioned
   - Invariants: no_commissioning_active

2. **SyncDevice_Discovered_CheckingUniqueID**
   - Device discovered in PartsList
   - Checking UniqueID to prevent duplication
   - Invariants: discovered, uniqueid_check_in_progress

3. **SyncDevice_UniqueID_Verified_CheckingICD**
   - UniqueID check passed (not duplicate)
   - Checking if device supports BridgedICDSupport
   - Invariants: not_duplicate, icd_check_in_progress

4. **SyncDevice_ICD_EnsureActive**
   - Device is ICD, ensuring it's active before commissioning
   - Invariants: is_icd, activating_device

5. **SyncDevice_OpeningCommissioningWindow**
   - Sending OpenCommissioningWindow to Administrator Commissioning Cluster
   - Invariants: device_active, window_opening

6. **SyncDevice_CommissioningWindow_Open_ECM_InProgress**
   - Window open, performing Enhanced Commissioning Method
   - Invariants: window_open, ecm_in_progress

7. **SyncDevice_Commissioned_PersistingUniqueID**
   - Device commissioned successfully
   - Persisting UniqueID mapping
   - Invariants: commissioned, uniqueid_persisting

8. **SyncDevice_Complete**
   - Device synchronized and accessible
   - Invariants: commissioned, uniqueid_persisted

9. **SyncDevice_Duplicate_Detected_Abort**
   - Error: Device already on intended fabric
   - Invariants: duplicate_detected

10. **SyncDevice_Missing_UniqueID_Generating**
    - Device lacks UniqueID in Basic Info
    - Generating and persisting new UniqueID
    - Invariants: no_original_uniqueid, generating_uniqueid

11. **SyncDevice_UniqueID_Conflict_CacheCheck**
    - UniqueID conflict detected
    - Checking cache for prior known UniqueIDs
    - Invariants: uniqueid_conflict, cache_checking

12. **SyncDevice_UniqueID_Loop_Detected_TiebreakerApplied**
    - Loop detected (cached UniqueID matches but differs from current)
    - Applying lexicographic tiebreaker
    - Invariants: loop_detected, tiebreaker_applied

### Transitions for Synchronized Device Commissioning

**T1: SyncDevice_Idle → SyncDevice_Discovered_CheckingUniqueID**
- Trigger: discover_synchronized_device
- Guard: device_in_partslist
- Actions:
  - read_bridged_device_basic_info()
  - check_uniqueid_vendorid_productid()

**T2: SyncDevice_Discovered_CheckingUniqueID → SyncDevice_UniqueID_Verified_CheckingICD**
- Trigger: uniqueid_check_complete
- Guard: !is_duplicate_device()
- Actions:
  - check_bridged_icd_support_feature()

**T3: SyncDevice_Discovered_CheckingUniqueID → SyncDevice_Duplicate_Detected_Abort**
- Trigger: uniqueid_check_complete
- Guard: is_duplicate_device()
- Actions:
  - abort_commissioning()
  - generate_event(duplicate_device_detected)

**T4: SyncDevice_Discovered_CheckingUniqueID → SyncDevice_Missing_UniqueID_Generating**
- Trigger: uniqueid_check_complete
- Guard: !has_uniqueid()
- Actions:
  - generate_unique_id()

**T5: SyncDevice_Missing_UniqueID_Generating → SyncDevice_UniqueID_Verified_CheckingICD**
- Trigger: uniqueid_generated
- Guard: uniqueid_valid
- Actions:
  - persist_generated_uniqueid()
  - check_bridged_icd_support_feature()

**T6: SyncDevice_UniqueID_Verified_CheckingICD → SyncDevice_ICD_EnsureActive**
- Trigger: icd_check_complete
- Guard: has_bridged_icd_support
- Actions:
  - use_bridged_icd_support_to_ensure_active()

**T7: SyncDevice_UniqueID_Verified_CheckingICD → SyncDevice_OpeningCommissioningWindow**
- Trigger: icd_check_complete
- Guard: !has_bridged_icd_support
- Actions:
  - send_open_commissioning_window(admin_commissioning_cluster)

**T8: SyncDevice_ICD_EnsureActive → SyncDevice_OpeningCommissioningWindow**
- Trigger: device_active_verified
- Guard: device_is_active
- Actions:
  - send_open_commissioning_window(admin_commissioning_cluster)

**T9: SyncDevice_OpeningCommissioningWindow → SyncDevice_CommissioningWindow_Open_ECM_InProgress**
- Trigger: commissioning_window_opened
- Guard: window_open
- Actions:
  - initiate_enhanced_commissioning_method()

**T10: SyncDevice_CommissioningWindow_Open_ECM_InProgress → SyncDevice_Commissioned_PersistingUniqueID**
- Trigger: ecm_complete
- Guard: commissioning_success
- Actions:
  - persist_uniqueid_association(device_node_id, uniqueid)

**T11: SyncDevice_Commissioned_PersistingUniqueID → SyncDevice_Complete**
- Trigger: uniqueid_persisted
- Guard: mapping_stored
- Actions:
  - generate_event(device_synchronized)

**T12: SyncDevice_UniqueID_Verified_CheckingICD → SyncDevice_UniqueID_Conflict_CacheCheck**
- Trigger: uniqueid_conflict_detected
- Guard: uniqueid_in_cache_but_differs
- Actions:
  - check_cache_for_loop()

**T13: SyncDevice_UniqueID_Conflict_CacheCheck → SyncDevice_UniqueID_Loop_Detected_TiebreakerApplied**
- Trigger: cache_check_complete
- Guard: loop_detected()
- Actions:
  - set_uniqueid_to_lexicographically_smallest()

**T14: SyncDevice_UniqueID_Loop_Detected_TiebreakerApplied → SyncDevice_UniqueID_Verified_CheckingICD**
- Trigger: tiebreaker_applied
- Guard: uniqueid_resolved
- Actions:
  - check_bridged_icd_support_feature()

---

## Functions to Define

### JCM Functions
1. advertise_dns_sd_with_jf_txt_key()
2. generate_qr_code()
3. generate_manual_pairing_code()
4. establish_pase_session()
5. begin_device_attestation()
6. has_anchor_cat(noc)
7. has_anchor_datastore_cat(noc)
8. extract_rcac_pubkey(rcac)
9. dcl_vendor_id_validate_rcac(pubkey, algo, curve, vendor_id)
10. is_valid_rcac(cert)
11. prepare_ica_csr()
12. generate_ica_csr(private_key, fabric_id)
13. validate_ica_csr_format(csr)
14. is_valid_pkcs10_format(csr)
15. verify_signature(signature, pubkey)
16. dcl_vendor_id_validate_icac(pubkey, algo, curve, vendor_id)
17. is_valid_icac(cert)
18. request_root_ca_sign(csr)
19. foreach_node_in_fabric_b(action)

### Anchor Transfer Functions
20. has_administrator_cat(noc)
21. check_datastore_entries_status()
22. all_entries_not_pending()
23. any_entry_pending_or_delete_pending()
24. set_datastore_status_entry(status)
25. stop_dns_sd_advertising(capabilities)
26. set_busy_anchor_transfer_error_for_icacsr()
27. admin_b_copy_datastore_from_admin_a()
28. set_datastore_anchor_node_id(node_id)
29. increment_administrator_cat_version()
30. issue_self_noc_with_anchor_datastore_cat()
31. advertise_dns_sd(capabilities)
32. verify_anchor_datastore_cat_in_noc()
33. verify_noc_chains_to_anchor_icac()

### Administrator Removal Functions
34. remove_target_from_datastore()
35. issue_self_noc_with_new_cat()
36. foreach_remaining_admin(action)

### Fabric Sync Functions
37. supports_fabric_synchronization()
38. discover_commissionee()
39. initiate_concurrent_connection_commissioning()
40. verify_aggregator_accessible()
41. send_request_commissioning_approval(cluster)
42. open_commissioning_window_for_commissioner()
43. verify_mutual_attestation()
44. discover_synchronized_devices_via_partslist()

### Sync Device Functions
45. read_bridged_device_basic_info()
46. check_uniqueid_vendorid_productid()
47. is_duplicate_device()
48. has_uniqueid()
49. generate_unique_id()
50. persist_generated_uniqueid()
51. check_bridged_icd_support_feature()
52. has_bridged_icd_support()
53. use_bridged_icd_support_to_ensure_active()
54. persist_uniqueid_association(node_id, uniqueid)
55. check_cache_for_loop()
56. loop_detected()
57. set_uniqueid_to_lexicographically_smallest()

### Cryptographic Functions
58. ecdsa_sign(data, private_key)
59. ecdsa_verify(data, signature, public_key)
60. hkdf_sha256(input_key, salt, info, output_length)
61. x509_extract_subject_dn(cert)
62. x509_verify_chain(cert, root_ca)
63. pkcs10_generate_csr(private_key, subject_dn)
64. pkcs10_verify_csr(csr, public_key)

---

## Security Properties Mapped to FSM

From security_properties.json, map properties to states/transitions:

- PROP_001 (Node_ID_Uniqueness): Checked in all states where Node IDs assigned
- PROP_002 (Anchor_ICAC_Reserved_Attribute): Verified in JCM states
- PROP_003 (Administrator_CAT_ACL_Requirement): Enforced in all admin operations
- PROP_004 (Administrator_CAT_CASE_Verification): JCM_ECM_Complete_AwaitingCATVerification state
- PROP_005 (Administrator_CAT_Version_Revocation): AdminRemoval_AnchorIncrementingCAT state
- PROP_006 (Anchor_CAT_Issuance_Restriction): Verified during ICA cross-signing
- PROP_010 (JCM_Anchor_CAT_Verification_During_Commissioning): T4 transition guard
- PROP_011 (JCM_User_Consent_Requirement): JCM_UserConsent_Pending state
- PROP_012 (RCAC_Vendor_ID_Validation): JCM_RCAC_Validation_InProgress state
- PROP_013 (ICA_CSR_Signature_Validation): T14 transition guard
- PROP_017 (Anchor_Transfer_Mutual_User_Consent): T3 and T1 transition guards
- PROP_018 (Anchor_Transfer_Datastore_Busy_Check): T7/T8 transition logic
- PROP_019 (Anchor_Transfer_Datastore_Read_Only): T9 actions
- PROP_025 (Fabric_Table_Duplication_Prevention): SyncDevice_Discovered_CheckingUniqueID
- PROP_033 (Fabric_Synchronization_User_Consent): FabricSync_Commissionee_UserConsent_Pending

---

## Cryptographic Operations Detail

### ECDSA Signature Generation
- Algorithm: ECDSA with SHA-256
- Input: data (bitstring), private_key (ECC private key, P-256)
- Output: signature (bitstring, DER-encoded)
- Used in: ICA CSR generation, certificate signing

### ECDSA Signature Verification
- Algorithm: ECDSA with SHA-256
- Input: data (bitstring), signature (bitstring), public_key (ECC public key, P-256)
- Output: boolean (true if valid)
- Used in: ICA CSR validation, NOC verification, CASE handshake

### HKDF-SHA256 Key Derivation
- Algorithm: HMAC-based Key Derivation Function with SHA-256
- Input: input_key (bitstring), salt (bitstring), info (string), output_length (integer)
- Output: derived_key (bitstring of output_length)
- Used in: (Not explicitly in Chapter 12, but referenced for key derivation)

### X.509 Certificate Operations
- Extract Subject DN: Read subject distinguished name from certificate
- Verify Chain: Validate certificate chains to trusted root CA
- Check Basic Constraints: Verify cA field for CA/ICAC distinction

### PKCS#10 CSR Operations
- Generate CSR: Create certificate signing request with subject DN and public key
- Sign CSR: Generate signature over CSR using private key
- Verify CSR: Validate CSR signature using public key from CSR

---

## Timing Requirements

1. **Commissioning Window Duration**: Prescribed time for window to remain open
2. **Datastore Copy Timeout**: Maximum time for datastore transfer during anchor transfer
3. **DNS-SD Advertisement Interval**: Periodic advertisement frequency
4. **User Consent Timeout**: Maximum time to wait for user input
5. **Network Operation Timeout**: General timeout for network commands

---

## Key Insights for FSM Completeness

1. **Multiple Parallel FSMs**: Chapter 12 contains at least 5 distinct FSMs that interact
2. **State Explosion**: Combining all states would create 1000+ combined states
3. **Hierarchical Structure**: Best modeled as hierarchical FSMs with inter-FSM events
4. **Error Recovery**: Most error states are terminal (abort) with no recovery path
5. **Asynchronous Operations**: Many operations involve multiple nodes acting independently
6. **Security Critical Paths**: CAT verification, user consent, and vendor validation are critical decision points

---

## Validation Checklist

- [ ] All SHALL/MUST requirements mapped to states/transitions
- [ ] All conditional logic (if/then) separated into distinct transitions with guards
- [ ] All functions used in actions are defined
- [ ] Cryptographic operations fully detailed
- [ ] Error states included for all failure modes
- [ ] Security properties cross-referenced to FSM elements
- [ ] Timing requirements documented
- [ ] No control flow in actions (all atomic operations)
- [ ] Guard conditions are boolean expressions
- [ ] All triggers identified (commands, events, timers)
