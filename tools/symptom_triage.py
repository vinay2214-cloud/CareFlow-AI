"""
CareFlow AI — Tool 1: Symptom Triage & Risk Analysis

AI-powered symptom analysis with FHIR context enrichment.
Detects dangerous symptom combinations and medication interactions
that rule-based triage systems miss.
"""

from __future__ import annotations

import logging

from services.ai_provider import AIProvider
from services.fhir_client import FHIRClient
from models.schemas import PatientContext
from prompts.clinical import TRIAGE_SYSTEM, build_triage_prompt

logger = logging.getLogger("careflow.tools.triage")


async def analyze_symptoms(
    symptoms: str,
    patient_age: int = 0,
    fhir_server_url: str = "",
    fhir_access_token: str = "",
    patient_id: str = "",
) -> dict:
    """
    AI-powered symptom triage with FHIR context enrichment.

    Returns urgency level, clinical categories, red flags,
    and recommended care pathway.
    """
    ai = AIProvider()
    ctx = PatientContext()

    # Fetch FHIR context if SHARP headers provided
    if fhir_server_url and patient_id:
        logger.info(f"Fetching FHIR context for patient {patient_id}")
        fhir = FHIRClient(fhir_server_url, fhir_access_token)
        ctx = await fhir.get_patient_context(patient_id)

    # Build prompt with enriched context
    user_prompt = build_triage_prompt(symptoms, patient_age, ctx)

    try:
        result = await ai.analyze(TRIAGE_SYSTEM, user_prompt)

        # Attach metadata
        result["fhir_context_used"] = ctx.has_data
        result["patient_context"] = {
            "conditions_count": len(ctx.conditions),
            "medications_count": len(ctx.medications),
            "observations_count": len(ctx.observations),
        }
        return result

    except ValueError as e:
        logger.error(f"Triage analysis failed: {e}")
        return {
            "urgency_level": "URGENT",
            "urgency_score": 7,
            "primary_concerns": [symptoms],
            "red_flags": ["AI analysis incomplete — clinical evaluation required"],
            "likely_conditions": ["Requires clinical evaluation"],
            "recommended_pathway": "Primary Care",
            "time_to_care": "Within 24 hours",
            "ai_reasoning": f"AI analysis encountered an error. Raw symptoms: {symptoms}. Please escalate to clinical evaluation.",
            "fhir_context_used": ctx.has_data,
            "patient_context": {
                "conditions_count": len(ctx.conditions),
                "medications_count": len(ctx.medications),
                "observations_count": len(ctx.observations),
            },
        }
