# Evaluation results

Prompt: extractor_v2 | Extraction model: claude-haiku-4-5-20251001 | Cases: 10

| Metric | Count | Rate |
|---|---|---|
| FALSE NEGATIVE | 2 | 20% |
| false positive | 0 | 0% |
| escalated (safe) | 1 | 10% |
| other mismatch | 3 | 30% |
| correct | 4 | 40% |

## Case details
| Aircraft | AD | Expected | System | Outcome | System reason |
|---|---|---|---|---|---|
| DEMO-001 | 2024-21-09 | DOES_NOT_APPLY | CANNOT_DETERMINE | other mismatch | Model matches, but affected aircraft are defined in 'Boeing 737–800BCF Airworthiness Limitations, D140A006, Revision L, dated April 1, 2021', which this system cannot see. |
| DEMO-002 | 2024-21-09 | DOES_NOT_APPLY | CANNOT_DETERMINE | other mismatch | Model matches, but affected aircraft are defined in 'Boeing 737–800BCF Airworthiness Limitations, D140A006, Revision L, dated April 1, 2021', which this system cannot see. |
| DEMO-003 | 2025-0274R1 | APPLIES | APPLIES | correct | Model, serial number and engine all match the AD's applicability. |
| DEMO-004 | 2025-0274R1 | APPLIES | DOES_NOT_APPLY | FALSE NEGATIVE | MSN 12680 is outside the AD's serial ranges (253-2627, 108-1344, 1677-9419, 112-189, 250-632). |
| DEMO-005 | 2025-0274R1 | APPLIES | DOES_NOT_APPLY | FALSE NEGATIVE | MSN 12681 is outside the AD's serial ranges (253-2627, 108-1344, 1677-9419, 112-189, 250-632). |
| DEMO-001 | 2025-05-16 | CANNOT_DETERMINE | CANNOT_DETERMINE | correct | Model matches, but affected aircraft are defined in 'Boeing 737-800BCF Airworthiness Limitations, D140A006, Revision L, dated April 1, 2021 (Section 5.2.1 identifies Group A airplanes)', which this system cannot see. |
| DEMO-002 | 2023-10-07 | DOES_NOT_APPLY | CANNOT_DETERMINE | other mismatch | Model matches, but affected aircraft are defined in 'Boeing Alert Service Bulletin 737–53A1217, Revision 1, dated September 8, 2022', which this system cannot see. |
| DEMO-003 | 2026-0037R1 | APPLIES | CANNOT_DETERMINE | escalated (safe) | Model matches, but affected aircraft are defined in 'Safran Aerosystems Evacuation Vendor Service Bulletin A320 004-25-130', which this system cannot see. |
| DEMO-004 | 2025-0237R1 | APPLIES | APPLIES | correct | Model, serial number and engine all match the AD's applicability. |
| DEMO-005 | 2026-0130 | DOES_NOT_APPLY | DOES_NOT_APPLY | correct | Superseded by AD 2026-0176; check that AD instead. |
