"""
CareFlow AI — Pydantic Data Models

Structured schemas for all tool inputs/outputs and FHIR data.
Ensures type safety and validation across the entire pipeline.
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════════════════
# FHIR Patient Context
# ═══════════════════════════════════════════════════════════════════════════

class FHIRObservation(BaseModel):
    """Normalized FHIR Observation (lab result or vital sign)."""
    name: str = ""
    value: str = ""
    unit: str = ""
    date: str = ""


class PatientContext(BaseModel):
    """Aggregated FHIR patient data fetched via SHARP context."""
    patient_id: str = ""
    patient_name: str = ""
    gender: str = "unknown"
    birth_date: str = "unknown"
    conditions: list[str] = Field(default_factory=list)
    medications: list[str] = Field(default_factory=list)
    observations: list[FHIRObservation] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)
    encounters: list[dict] = Field(default_factory=list)
    fhir_error: Optional[str] = None

    @property
    def has_data(self) -> bool:
        """True if any meaningful FHIR data was retrieved."""
        return bool(self.conditions or self.medications or self.observations)


# ═══════════════════════════════════════════════════════════════════════════
# Tool Output Models
# ═══════════════════════════════════════════════════════════════════════════

class TriageResult(BaseModel):
    """Output schema for analyze_symptoms tool."""
    urgency_level: str = "URGENT"
    urgency_score: int = 5
    primary_concerns: list[str] = Field(default_factory=list)
    red_flags: list[str] = Field(default_factory=list)
    likely_conditions: list[str] = Field(default_factory=list)
    recommended_pathway: str = "Primary Care"
    time_to_care: str = "Within 24 hours"
    ai_reasoning: str = ""
    fhir_context_used: bool = False
    patient_context: dict = Field(default_factory=dict)


class CareGap(BaseModel):
    """Individual care gap entry."""
    gap_type: str = "Screening"
    description: str = ""
    priority: str = "MEDIUM"
    overdue_by: str = "Unknown"
    clinical_rationale: str = ""


class CareGapsResult(BaseModel):
    """Output schema for detect_care_gaps tool."""
    care_gaps: list[CareGap] = Field(default_factory=list)
    high_priority_count: int = 0
    summary: str = ""
    recommended_next_appointment_type: str = ""
    patient_id: str = ""
    fhir_data_used: bool = False


class SBARNote(BaseModel):
    """Structured SBAR clinical handoff note."""
    situation: str = ""
    background: str = ""
    assessment: str = ""
    recommendation: str = ""


class HandoffResult(BaseModel):
    """Output schema for generate_handoff_note tool."""
    sbar_note: SBARNote = Field(default_factory=SBARNote)
    urgency_flag: str = "ROUTINE"
    key_action_items: list[str] = Field(default_factory=list)
    estimated_acuity_level: int = 3
    note_generated_at: str = "synthetic_data_only_no_phi"


class RiskFactor(BaseModel):
    """Individual readmission risk factor."""
    factor: str = ""
    weight: str = "MEDIUM"
    detail: str = ""


class Intervention(BaseModel):
    """Recommended intervention for readmission prevention."""
    intervention: str = ""
    priority: str = "WITHIN_48H"


class ReadmissionRiskResult(BaseModel):
    """Output schema for compute_readmission_risk tool."""
    risk_score: int = 50
    risk_category: str = "MODERATE"
    risk_factors: list[RiskFactor] = Field(default_factory=list)
    protective_factors: list[str] = Field(default_factory=list)
    recommended_interventions: list[Intervention] = Field(default_factory=list)
    follow_up_timeline: str = ""
    estimated_readmission_probability: str = "Unknown"
    ai_confidence: str = "MEDIUM"
    patient_id: str = ""
    data_source: str = "fhir_synthetic_data"
