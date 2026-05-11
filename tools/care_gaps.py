"""
CareFlow AI — Tool 2: Care Gap Detection

Identifies overdue screenings, missed follow-ups, and medication
monitoring gaps by cross-referencing FHIR conditions, medications,
and observation history with AI clinical reasoning.
"""

from __future__ import annotations

import os
import logging

from services.ai_provider import AIProvider
from services.fhir_client import FHIRClient
from models.schemas import PatientContext
from prompts.clinical import CARE_GAPS_SYSTEM, build_care_gaps_prompt

logger = logging.getLogger("careflow.tools.care_gaps")

FHIR_SANDBOX = os.getenv("FHIR_SANDBOX_URL", "https://hapi.fhir.org/baseR4")


async def detect_care_gaps(
    patient_id: str,
    fhir_server_url: str = "",
    fhir_access_token: str = "",
    patient_age: int = 0,
) -> dict:
    """
    Identifies care gaps by analyzing FHIR data with AI clinical reasoning.

    Detects gaps a rules engine would miss — e.g., a diabetic patient on
    metformin whose last HbA1c was 14 months ago.
    """
    ai = AIProvider()

    # Use sandbox if no FHIR URL provided (for demo resilience)
    fhir_url = fhir_server_url or FHIR_SANDBOX
    fhir = FHIRClient(fhir_url, fhir_access_token)
    ctx = await fhir.get_patient_context(patient_id)

    user_prompt = build_care_gaps_prompt(patient_id, patient_age, ctx)

    try:
        result = await ai.analyze(CARE_GAPS_SYSTEM, user_prompt)
        result["patient_id"] = patient_id
        result["fhir_data_used"] = ctx.has_data and not bool(ctx.fhir_error)
        return result

    except ValueError as e:
        logger.error(f"Care gap detection failed: {e}")
        return {
            "care_gaps": [],
            "high_priority_count": 0,
            "summary": f"AI analysis incomplete. Error: {str(e)[:200]}",
            "recommended_next_appointment_type": "Primary Care",
            "patient_id": patient_id,
            "fhir_data_used": False,
        }
