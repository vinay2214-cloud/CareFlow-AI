"""
CareFlow AI — Tool 3: Clinical Handoff Note Generation

Generates structured SBAR (Situation, Background, Assessment, Recommendation)
handoff notes for physician-to-physician communication.
"""

from __future__ import annotations

import json
import logging

from services.ai_provider import AIProvider
from services.fhir_client import FHIRClient
from models.schemas import PatientContext
from prompts.clinical import HANDOFF_SYSTEM, build_handoff_prompt

logger = logging.getLogger("careflow.tools.handoff")


async def generate_handoff_note(
    symptoms: str,
    triage_result: str = "",
    care_gaps_result: str = "",
    fhir_server_url: str = "",
    fhir_access_token: str = "",
    patient_id: str = "",
) -> dict:
    """
    Generates SBAR-format clinical handoff note combining AI triage,
    care gaps, and FHIR context.
    """
    ai = AIProvider()
    ctx = PatientContext()

    # Fetch FHIR context if available
    if fhir_server_url and patient_id:
        fhir = FHIRClient(fhir_server_url, fhir_access_token)
        ctx = await fhir.get_patient_context(patient_id)

    # Parse optional upstream results
    triage_data = None
    gaps_data = None
    try:
        if triage_result:
            triage_data = json.loads(triage_result)
    except json.JSONDecodeError:
        logger.debug("Could not parse triage_result JSON")
    try:
        if care_gaps_result:
            gaps_data = json.loads(care_gaps_result)
    except json.JSONDecodeError:
        logger.debug("Could not parse care_gaps_result JSON")

    user_prompt = build_handoff_prompt(symptoms, triage_data, gaps_data, ctx)

    try:
        result = await ai.analyze(HANDOFF_SYSTEM, user_prompt)
        result["note_generated_at"] = "synthetic_data_only_no_phi"
        return result

    except ValueError as e:
        logger.error(f"Handoff note generation failed: {e}")
        return {
            "sbar_note": {
                "situation": f"Patient presents with: {symptoms}",
                "background": f"Conditions: {', '.join(ctx.conditions or ['Unknown'])}",
                "assessment": "AI analysis incomplete — clinical evaluation required",
                "recommendation": "Escalate to attending physician for evaluation",
            },
            "urgency_flag": "URGENT",
            "key_action_items": ["Clinical evaluation required"],
            "estimated_acuity_level": 3,
            "note_generated_at": "synthetic_data_only_no_phi",
        }
