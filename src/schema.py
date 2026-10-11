"""
schema.py — the shapes of our data.

Pydantic models are like strict forms. When the AI extracts information from an
AD, it must fill in this form exactly. If it puts text where a number belongs,
Pydantic raises an error instead of letting bad data slip through silently.
"""
from datetime import date
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field


class SerialRange(BaseModel):
    """An inclusive range of manufacturer serial numbers (MSN), e.g. 28001-33000."""
    start: int
    end: int


class ADExtraction(BaseModel):
    """What the LLM must return for each AD. (We add source_file ourselves.)"""
    ad_number: str = Field(description="AD number exactly as printed, e.g. '2025-14-07' or '2025-0123'")
    issuing_authority: Literal["FAA", "EASA", "GCAA"]
    effective_date: Optional[date] = Field(None, description="Effective date, if stated")
    supersedes: list[str] = Field(default_factory=list, description="AD numbers this AD replaces")
    applicable_models: list[str] = Field(
        description="Every aircraft model listed, written in full, e.g. ['737-800', '737-900ER'] "
                    "or ['A320-214', 'A320-216']. Never abbreviate as '-800'."
    )
    serial_ranges: list[SerialRange] = Field(
        default_factory=list,
        description="Serial number ranges if applicability is limited by serial number. "
                    "Empty list means all serial numbers.",
    )
    engine_models: list[str] = Field(
        default_factory=list,
        description="Engine models if applicability is limited by engine. Empty means any engine.",
    )
    applicability_by_reference: Optional[str] = Field(
        None,
        description="If the affected aircraft are defined by another document (e.g. 'as identified in "
                    "Boeing Alert Service Bulletin 737-53A1234'), name that document here. Otherwise null.",
    )
    compliance_time: str = Field(description="When action must be done, in plain words")
    required_action: str = Field(description="One or two sentence summary of the required action")
    source_pages: list[int] = Field(description="Page numbers where applicability and actions are stated")
    extraction_notes: Optional[str] = Field(
        None, description="Anything ambiguous or uncertain about this extraction"
    )


class ADRecord(ADExtraction):
    """A stored AD = the extraction plus which file it came from."""
    source_file: str


class Verdict(str, Enum):
    APPLIES = "APPLIES"
    DOES_NOT_APPLY = "DOES_NOT_APPLY"
    CANNOT_DETERMINE = "CANNOT_DETERMINE"


class ApplicabilityResult(BaseModel):
    ad_number: str
    verdict: Verdict
    reason: str


class Aircraft(BaseModel):
    id: str
    model: str
    msn: int
    engine: str


class ReviewResult(BaseModel):
    """What the Safety Reviewer LLM must return."""
    uncited_claims: list[str] = Field(
        default_factory=list,
        description="Factual statements in the analysis that have no [AD ... p.N] citation",
    )
    unsafe_statements: list[str] = Field(
        default_factory=list,
        description="Statements that tell the reader an action is unnecessary, give a definitive "
                    "airworthiness sign-off, or go beyond what the cited text supports",
    )
