# AD applicability report: DEMO-003

Aircraft: {'id': 'DEMO-003', 'model': 'A320-214', 'msn': 5678, 'engine': 'CFM56-5B4'}
Question: Which ADs apply and what is due?

## Verdicts (rule-based)
| AD | Verdict | Reason |
|---|---|---|
| 2023-10-07 | DOES_NOT_APPLY | Model A320-214 is not in the AD's list: 737-600, 737-700, 737-800. |
| 2023-13-12 | DOES_NOT_APPLY | Model A320-214 is not in the AD's list: 737-100, 737-200, 737-200C, 737-300, 737-400, 737-500, 737-600, 737-700, 737-700C, 737-800, 737-900, 737-900ER, 757-200, 757-200PF, 757-200CB, 757-300, 767-200, 767-300, 767-300F, 767-400ER. |
| 2023-13-05 | DOES_NOT_APPLY | Model A320-214 is not in the AD's list: 737-600, 737-700, 737-700C, 737-800, 737-900, 737-900ER. |
| 2024-01-06 | DOES_NOT_APPLY | Model A320-214 is not in the AD's list: 737-600, 737-700, 737-800. |
| 2024-13-06 | DOES_NOT_APPLY | Model A320-214 is not in the AD's list: 737-300, 737-400, 737-800. |
| 2024-21-09 | DOES_NOT_APPLY | Model A320-214 is not in the AD's list: 737-800. |
| 2024-19-01 | DOES_NOT_APPLY | Model A320-214 is not in the AD's list: 747-100, 747-100B, 747-100B SUD, 747-200B, 747-200C, 747-200F, 747-300, 747-400, 747-400D, 747-400F, 747SP, 747SR. |
| 2025-05-16 | DOES_NOT_APPLY | Model A320-214 is not in the AD's list: 737-800. |
| 2025-09-11 | DOES_NOT_APPLY | Model A320-214 is not in the AD's list: 737-700, 737-800, 737-900, 737-900ER, 737-8, 737-9. |
| 2025-0025 | DOES_NOT_APPLY | Model A320-214 is not in the AD's list: AS 350B2, AS 350B3, AS355N, AS355NP, EC 130 B4. |
| 2025-0158R2 | CANNOT_DETERMINE | Model matches, but affected aircraft are defined in 'Airbus Alert Operators Transmission (AOT) A32N033-24 Revision 02 or Revision 03; Triumph Service Bulletin 114122-32-108', which this system cannot see. |
| 2025-0237R1 | APPLIES | Model, serial number and engine all match the AD's applicability. |
| 2025-0274R1 | APPLIES | Model, serial number and engine all match the AD's applicability. |
| 2026-0037R1 | CANNOT_DETERMINE | Model matches, but affected aircraft are defined in 'Safran Aerosystems Evacuation Vendor Service Bulletin A320 004-25-130', which this system cannot see. |
| 2026-0120 | DOES_NOT_APPLY | Model A320-214 is not in the AD's list: A319-151N, A319-153N, A319-171N, A319-173N, A320-251N, A320-252N, A320-253N, A320-271N, A320-272N, A320-273N, A321-251N, A321-251NX, A321-252N, A321-252NX, A321-253N, A321-253NX, A321-271N, A321-271NX, A321-272N, A321-272NX. |
| 2026-0130 | DOES_NOT_APPLY | Superseded by AD 2026-0176; check that AD instead. |
| 2026-0133 | APPLIES | Model, serial number and engine all match the AD's applicability. |
| 2026-0134 | APPLIES | Model, serial number and engine all match the AD's applicability. |
| 2026-0136 | APPLIES | Model, serial number and engine all match the AD's applicability. |
| 2026-0142 | CANNOT_DETERMINE | Model matches, but affected aircraft are defined in 'Airbus Alert Operators Transmission (AOT) A57N028-26', which this system cannot see. |
| 2026-0144R1 | DOES_NOT_APPLY | Model A320-214 is not in the AD's list: A320-251N, A320-252N, A321-252NX, A320-271N. |
| 2026-0176 | APPLIES | Model, serial number and engine all match the AD's applicability. |

## Analysis
# Applicability and compliance summary: DEMO-003 (A320-214, MSN 5678)

The rules decided each verdict below. Group numbers and several compliance details depend on documents or AD paragraphs that are not in the retrieved text. I flag these as "not stated in the retrieved text".

## AD 2025-0158R2: CANNOT_DETERMINE
- **Addresses:** Main landing gear (MLG) door actuators, P/N 114122015, with a serial number listed in Appendix 1 List A of the AOT. [AD 2025-0158R2 p.1] This revision adds X-ray inspection instructions as terminating action for the repetitive inspections. [AD 2025-0158R2 p.3]
- **Required action (Group 1):** Inspect each affected MLG door 1 in accordance with the AOT. [AD 2025-0158R2 p.3] Replacement of affected parts is required by paragraph (3), (4) or (5) and terminates the repetitive inspections. [AD 2025-0158R2 p.4] The text of paragraphs (3), (4) and (5) is not stated in the retrieved text.
- **Compliance time (Group 1):** The inspection is due within 8 days or 5 FC, whichever occurs later, from the last inspection in accordance with the AOT at any revision. Alternatively, it is due before next flight after 04 August 2025, whichever occurs later. It then repeats at intervals not to exceed 8 days or 5 FC, whichever occurs later. [AD 2025-0158R2 p.3] The compliance times for the replacement paragraphs and for Group 2 are not stated in the retrieved text.
- **Parts installation:** For Group 1 and Group 2 aeroplanes, do not install any affected part from 04 August 2025. [AD 2025-0158R2 p.4]
- **What to check:** Confirm affected status against Airbus AOT A32N033-24 Revision 02 or 03 and Triumph SB 114122-32-108. [AD 2025-0158R2 p.4] Also confirm which Group the aircraft falls in. The Group definitions are not stated in the retrieved text.

## AD 2025-0237R1: APPLIES
- **Addresses:** This revision updates the repair instruction reference in Table 1 for Group 5 aeroplanes and corrects the compliance time date in paragraphs (4) and (5). [AD 2025-0237R1 p.4] The unsafe condition is not stated in the retrieved text.
- **Required action:** Accomplish a Special Detailed Inspection (SDI) of each zone in accordance with the SB. [AD 2025-0237R1 p.4] If any discrepancy is found, accomplish the corrective actions in accordance with the SB

## Unresolved review flags
- Uncited claim: The inspection is due within 8 days or 5 FC, whichever occurs later, from the last inspection in accordance with the AOT at any revision.
- Uncited claim: Alternatively, it is due before next flight after 04 August 2025, whichever occurs later.
- Uncited claim: If any discrepancy is found, accomplish the corrective actions in accordance with the SB

## Engineer sign-off
APPROVED by Shiney F. Note: Verdicts checked. 3 uncited claims in analysis; verify 2026-0142 timings against the AOT before acting.

_Decision-support only. Not an airworthiness determination._
