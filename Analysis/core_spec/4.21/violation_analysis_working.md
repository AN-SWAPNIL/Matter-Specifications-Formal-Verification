# Property Violation Analysis - Working Document

**Analysis Date:** 2026-02-13  
**Specification:** Matter Core Specification v1.4, Section 4.21  
**FSM Model:** ntl_fsm_model.json (Updated with 52 transitions)  
**Properties File:** ntl_security_properties.json (42 properties)

---

## Analysis Progress

**Status:** IN PROGRESS  
**Properties Analyzed:** 0/42  
**Violations Found:** TBD

---

## Property Checklist

### CRITICAL Properties (17 total)
- [ ] PROP_001: Commissioning_Mode_Access_Control
- [ ] PROP_002: AID_Authentication
- [ ] PROP_003: Role_Asymmetry_Enforcement
- [ ] PROP_004: State_Transition_Ordering
- [ ] PROP_005: Protocol_Version_Binding
- [ ] PROP_008: Chaining_Parameter_Consistency
- [ ] PROP_009: Fragment_Reassembly_Atomicity
- [ ] PROP_010: Memory_Bounds_Enforcement
- [ ] PROP_011: Lc_Data_Length_Consistency
- [ ] PROP_012: Le_Response_Length_Consistency
- [ ] PROP_015: Response_Chaining_Integrity
- [ ] PROP_016: GET_RESPONSE_Sequencing
- [ ] PROP_019: Session_Timeout_Enforcement
- [ ] PROP_020: Idle_Timer_Reset
- [ ] PROP_021: Message_Size_Limit
- [ ] PROP_029: Fragment_Order_Preservation
- [ ] PROP_032: Short_Field_Coding_Mandatory

### HIGH Properties (19 total)
- [ ] PROP_006: Version_Value_Constraint
- [ ] PROP_007: Vendor_Product_ID_Consistency
- [ ] PROP_013: P1P2_Message_Length_Encoding
- [ ] PROP_014: Data_Fragment_Content
- [ ] PROP_017: GET_RESPONSE_Le_Encoding
- [ ] PROP_018: Status_Code_Correctness
- [ ] PROP_022: Select_Response_Format
- [ ] PROP_023: Commissioning_Mode_Rejection
- [ ] PROP_024: Transport_After_Select
- [ ] PROP_025: APDU_Structure_Validation
- [ ] PROP_026: Chaining_CLA_Consistency
- [ ] PROP_027: Fragment_Buffer_Isolation
- [ ] PROP_028: Response_Buffer_Isolation
- [ ] PROP_030: SW2_Remaining_Bytes_Accuracy
- [ ] PROP_031: Response_Complete_SW1_SW2
- [ ] PROP_033: Matter_Message_Opacity
- [ ] PROP_034: Higher_Layer_Crypto_Assumption
- [ ] PROP_035: ISO_DEP_Reliability_Assumption
- [ ] PROP_036: NFC_Forum_Compliance

### MEDIUM Properties (6 total)
- [ ] PROP_037: VID_PID_Privacy_Respect
- [ ] PROP_038: Extended_Data_Optional
- [ ] PROP_039: Lc_FSC_Optimization
- [ ] PROP_040: Le_FSD_Optimization
- [ ] PROP_041: Commissioner_Role_Compliance
- [ ] PROP_042: Commissionee_Role_Compliance

---

## Violations Found

(To be populated as analysis progresses)

