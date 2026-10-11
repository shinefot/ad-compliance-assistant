# Evaluation results

Prompt: extractor_v3 | Extraction model: claude-haiku-4-5-20251001 | Cases: 10

| Metric | Count | Rate |
|---|---|---|
| FALSE NEGATIVE | 0 | 0% |
| false positive | 0 | 0% |
| escalated (safe) | 0 | 0% |
| other mismatch | 0 | 0% |
| correct | 10 | 100% |

## Case details
| Aircraft | AD | Expected | System | Outcome | System reason |
|---|---|---|---|---|---|
| DEMO-001 | NPRM-FAA-2024-2315 | DOES_NOT_APPLY | DOES_NOT_APPLY | correct | This is a PROPOSED rule (NPRM), not an AD in force. It creates no legal requirement yet. |
| DEMO-002 | NPRM-FAA-2024-2315 | DOES_NOT_APPLY | DOES_NOT_APPLY | correct | This is a PROPOSED rule (NPRM), not an AD in force. It creates no legal requirement yet. |
| DEMO-003 | 2025-0274R1 | APPLIES | APPLIES | correct | Model, serial number and engine all match the AD's applicability. |
| DEMO-004 | 2025-0274R1 | APPLIES | APPLIES | correct | Model, serial number and engine all match the AD's applicability. |
| DEMO-005 | 2025-0274R1 | APPLIES | APPLIES | correct | Model, serial number and engine all match the AD's applicability. |
| DEMO-001 | 2025-05-16 | CANNOT_DETERMINE | CANNOT_DETERMINE | correct | Model matches, but affected aircraft are defined in 'Boeing 737-800BCF Airworthiness Limitations, D140A006, Revision L, dated April 1, 2021 (Section 5.2.1 identifies Group A airplanes affected)', which this system cannot see. |
| DEMO-002 | NPRM-FAA-2023-1041 | DOES_NOT_APPLY | DOES_NOT_APPLY | correct | This is a PROPOSED rule (NPRM), not an AD in force. It creates no legal requirement yet. |
| DEMO-003 | 2026-0037R1 | APPLIES | APPLIES | correct | Model, serial number and engine all match the AD's applicability. |
| DEMO-004 | 2025-0237R1 | APPLIES | APPLIES | correct | Model, serial number and engine all match the AD's applicability. |
| DEMO-005 | 2026-0130 | DOES_NOT_APPLY | DOES_NOT_APPLY | correct | Superseded by AD 2026-0176; check that AD instead. |
