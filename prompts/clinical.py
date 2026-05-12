"""
CareFlow AI — Clinical Prompt Templates

Production-grade prompts for healthcare AI reasoning.
All prompts enforce strict JSON output and clinical safety.
"""

from __future__ import annotations

import json
from models.schemas import PatientContext


# ═══════════════════════════════════════════════════════════════════════════
# Symptom Triage
# ═══════════════════════════════════════════════════════════════════════════

TRIAGE_SYSTEM = """You are a clinical triage AI assistant for post-discharge patient monitoring.
Analyze the patient's symptoms and return a structured triage assessment.
You MUST identify patterns that rule-based systems miss:
- Dangerous symptom combinations (e.g., chest pain + diaphoresis + arm radiation = STEMI pattern)
- Medication-symptom interactions
- Post-discharge complication patterns

SAFETY: Never provide a definitive diagnosis. Always recommend clinical evaluation.
PRIVACY: Never include patient names or identifiers in your reasoning.

Return ONLY valid JSON with this EXACT structure:
{
  "urgency_level": "EMERGENT|URGENT|SEMI-URGENT|NON-URGENT",
  "urgency_score": <1-10 integer>,
  "primary_concerns": ["concern1", "concern2"],
  "red_flags": ["flag1", "flag2"],
  "likely_conditions": ["condition1", "condition2"],
  "recommended_pathway": "ER|Urgent Care|Primary Care|Telehealth|Self-Care",
  "time_to_care": "Immediate|Within 2 hours|Within 24 hours|Within 72 hours|Routine",
  "ai_reasoning": "detailed clinical reasoning string"
}"""


def build_triage_prompt(
    symptoms: str,
    patient_age: int = 0,
    vital_signs: str = "",
    ctx: PatientContext | None = None,
) -> str:
    """Build enriched triage user prompt."""
    info = f"Age: {patient_age if patient_age else 'unknown'}"
    if vital_signs:
        info += f"\nVital Signs: {vital_signs}"
    if ctx and ctx.conditions:
        info += f"\nActive Conditions: {', '.join(ctx.conditions)}"
    if ctx and ctx.medications:
        info += f"\nCurrent Medications: {', '.join(ctx.medications)}"
    if ctx and ctx.allergies:
        info += f"\nAllergies: {', '.join(ctx.allergies)}"
    if ctx and ctx.observations:
        recent = [
            f"{o.name}: {o.value} {o.unit} ({o.date})"
            for o in ctx.observations[:5] if o.name
        ]
        if recent:
            info += f"\nRecent Labs/Vitals: {'; '.join(recent)}"

    return f"""Patient symptoms: {symptoms}

Patient context:
{info}

Perform a clinical triage assessment. Flag any dangerous symptom combinations
or potential medication-symptom interactions. Use vital signs when provided.
Consider post-discharge complications."""


# ═══════════════════════════════════════════════════════════════════════════
# Care Gap Detection
# ═══════════════════════════════════════════════════════════════════════════

CARE_GAPS_SYSTEM = """You are a preventive care specialist AI. Analyze the patient's
FHIR data and identify care gaps — overdue screenings, missing follow-ups,
medication monitoring needs.

Think BEYOND simple age/sex rules:
- Cross-reference conditions with required monitoring protocols
- Identify drug-condition monitoring needs (e.g., metformin → renal function)
- Flag high-priority items that could lead to readmission
- Consider post-discharge follow-up gaps

Return ONLY valid JSON:
{
  "care_gaps": [
    {
      "gap_type": "Screening|Monitoring|Follow-up|Immunization|Medication Review",
      "description": "specific description",
      "priority": "HIGH|MEDIUM|LOW",
      "overdue_by": "estimated time or Unknown",
      "clinical_rationale": "why this matters clinically"
    }
  ],
  "high_priority_count": <integer>,
  "summary": "overall summary string",
  "recommended_next_appointment_type": "specialist type or Primary Care"
}"""


def build_care_gaps_prompt(
    patient_id: str,
    patient_age: int = 0,
    ctx: PatientContext | None = None,
) -> str:
    """Build care gap analysis user prompt."""
    obs_data = []
    if ctx and ctx.observations:
        obs_data = [o.model_dump() for o in ctx.observations[:5]]

    return f"""Patient FHIR Data:
- Patient ID: {patient_id}
- Age: {patient_age or (ctx.birth_date if ctx else 'unknown')}
- Gender: {ctx.gender if ctx else 'unknown'}
- Active Conditions: {json.dumps(ctx.conditions if ctx else [])}
- Current Medications: {json.dumps(ctx.medications if ctx else [])}
- Recent Labs/Observations: {json.dumps(obs_data)}
- Allergies: {json.dumps(ctx.allergies if ctx else [])}

Identify ALL care gaps. Pay special attention to:
1. Condition-specific monitoring (diabetics → HbA1c q3mo, CHF → BNP, weight)
2. Medication monitoring (metformin → renal, warfarin → INR, statins → LFTs)
3. Age/sex-appropriate screenings
4. Missing post-discharge follow-ups"""


# ═══════════════════════════════════════════════════════════════════════════
# Handoff Note (SBAR)
# ═══════════════════════════════════════════════════════════════════════════

HANDOFF_SYSTEM = """You are a clinical documentation specialist generating
professional SBAR handoff notes. Notes must be:
- Concise but complete
- Use standard medical terminology
- Suitable for physician-to-physician handoff
- Free of any PHI — use "the patient" or patient ID only

Return ONLY valid JSON:
{
  "sbar_note": {
    "situation": "current clinical situation",
    "background": "relevant history and context",
    "assessment": "clinical assessment",
    "recommendation": "specific next steps"
  },
  "urgency_flag": "EMERGENT|URGENT|ROUTINE",
  "key_action_items": ["action1", "action2"],
  "estimated_acuity_level": <1-5 integer>,
  "note_generated_at": "timestamp"
}"""


def build_handoff_prompt(
    symptoms: str,
    triage_data: dict | None = None,
    gaps_data: dict | None = None,
    ctx: PatientContext | None = None,
) -> str:
    """Build handoff note user prompt."""
    conditions = ctx.conditions if ctx else ["Unknown"]
    medications = ctx.medications if ctx else ["Unknown"]
    allergies = ctx.allergies if ctx else ["NKDA"]

    triage_str = json.dumps(triage_data) if triage_data else "Not yet performed"
    gaps_list = gaps_data.get("care_gaps", [])[:3] if gaps_data else []
    gaps_str = json.dumps(gaps_list) if gaps_list else "Not yet assessed"

    return f"""Generate a clinical handoff note for:

Presenting Symptoms: {symptoms}
Triage Assessment: {triage_str}
Care Gaps Identified: {gaps_str}

Patient Background:
- Conditions: {', '.join(conditions)}
- Medications: {', '.join(medications)}
- Allergies: {', '.join(allergies)}

Create a complete SBAR note capturing the full clinical picture."""


# ═══════════════════════════════════════════════════════════════════════════
# Readmission Risk
# ═══════════════════════════════════════════════════════════════════════════

READMISSION_SYSTEM = """You are a hospital readmission risk specialist. Calculate
30-day readmission risk using LACE+ index factors PLUS AI-enhanced factors:
- Length of stay, Acuity, Comorbidity burden, ER visits (LACE)
- Medication complexity and polypharmacy
- Condition burden and disease interactions
- Care gap severity
- Social determinants indicators

Return ONLY valid JSON:
{
  "risk_score": <0-100 integer>,
  "risk_category": "LOW|MODERATE|HIGH|VERY_HIGH",
  "risk_factors": [
    {"factor": "name", "weight": "HIGH|MEDIUM|LOW", "detail": "explanation"}
  ],
  "protective_factors": ["factor1", "factor2"],
  "recommended_interventions": [
    {"intervention": "specific action", "priority": "IMMEDIATE|WITHIN_48H|WITHIN_WEEK"}
  ],
  "follow_up_timeline": "specific timeline",
  "estimated_readmission_probability": "X%",
  "ai_confidence": "HIGH|MEDIUM|LOW"
}"""


def build_readmission_prompt(
    patient_id: str,
    discharge_diagnosis: str = "",
    patient_age: int = 0,
    lives_alone: bool = False,
    has_transportation: bool = True,
    prior_readmissions_90d: int = 0,
    ctx: PatientContext | None = None,
) -> str:
    """Build readmission risk user prompt."""
    obs_data = []
    if ctx and ctx.observations:
        obs_data = [o.model_dump() for o in ctx.observations[:5]]

    return f"""Patient Readmission Risk Assessment:
- Patient ID: {patient_id}
- Age: {patient_age or 'unknown'}
- Discharge Diagnosis: {discharge_diagnosis or 'Not specified'}
- Active Conditions ({len(ctx.conditions if ctx else [])} total): {', '.join((ctx.conditions if ctx else [])[:8])}
- Medications ({len(ctx.medications if ctx else [])} active): {', '.join((ctx.medications if ctx else [])[:8])}
- Recent Labs: {json.dumps(obs_data)}
- Allergies: {', '.join(ctx.allergies if ctx else [])}

Social Determinants of Health:
- Lives alone: {lives_alone}
- Has transportation to follow-up: {has_transportation}
- Prior readmissions in last 90 days: {prior_readmissions_90d}

Compute 30-day readmission risk. Consider polypharmacy, comorbidity burden,
recent acute events, and evidence-based readmission predictors."""


# ═══════════════════════════════════════════════════════════════════════════
# Medication Reconciliation
# ═══════════════════════════════════════════════════════════════════════════

MED_RECON_SYSTEM = """You are a clinical pharmacist AI performing medication
reconciliation at hospital discharge. Analyze the discharge medication list
against the patient's FHIR medication history and identify ALL clinically
significant discrepancies.

Pay special attention to:
1. HIGH-ALERT medications: anticoagulants (warfarin, heparin), insulin,
   opioids, digoxin, lithium, methotrexate, chemotherapy
2. Drug-drug interactions in the new discharge combination
3. Medications for known conditions that are MISSING from discharge list
4. Therapeutic duplications (same drug class prescribed twice)
5. Medications that were held during admission needing clear restart instructions
6. Renal/hepatic dose adjustments needed for known organ dysfunction

Return ONLY valid JSON:
{
  "overall_risk": "HIGH|MODERATE|LOW",
  "safe_to_discharge": true|false,
  "requires_pharmacist_review": true|false,
  "discrepancies": [
    {
      "type": "OMISSION|DUPLICATION|INTERACTION|DOSAGE_CHANGE|HIGH_ALERT|RESTART_NEEDED",
      "medication": "...",
      "severity": "CRITICAL|HIGH|MODERATE|LOW",
      "description": "...",
      "recommended_action": "...",
      "rationale": "..."
    }
  ],
  "high_alert_medications_on_list": ["..."],
  "drug_interactions_detected": ["..."],
  "missing_medications_for_conditions": ["..."],
  "pharmacist_counseling_points": ["..."],
  "monitoring_required": ["..."],
  "reconciliation_summary": "..."
}"""


def build_medication_reconciliation_prompt(
    discharge_medications: str,
    patient_id: str = "",
    ctx: PatientContext | None = None,
) -> str:
    """Build medication reconciliation user prompt."""
    observations = []
    if ctx and ctx.observations:
        observations = [o.model_dump() for o in ctx.observations[:5]]

    return f"""DISCHARGE MEDICATION LIST:
{discharge_medications}

PATIENT FHIR DATA:
- Patient ID: {patient_id or 'not provided'}
- Pre-admission medications ({len(ctx.medications if ctx else [])} total):
  {', '.join(ctx.medications if ctx and ctx.medications else ['None on file'])}
- Active conditions: {', '.join(ctx.conditions if ctx and ctx.conditions else ['Unknown'])}
- Allergies: {', '.join(ctx.allergies if ctx and ctx.allergies else ['NKDA'])}
- Recent labs: {json.dumps(observations)}

Perform complete medication reconciliation. Identify every discrepancy
that could cause post-discharge harm or readmission. Be specific about
which medications are concerning and exactly what action is needed."""
