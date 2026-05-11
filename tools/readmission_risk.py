"""
CareFlow AI — Tool 4: 30-Day Readmission Risk Scoring

AI-enhanced readmission risk assessment that goes beyond LACE/HOSPITAL
scores by incorporating contextual factors from FHIR patient data.
"""

from __future__ import annotations

import os
import logging

from services.ai_provider import AIProvider
from services.fhir_client import FHIRClient
from models.schemas import PatientContext
from prompts.clinical import READMISSION_SYSTEM, build_readmission_prompt

logger = logging.getLogger("careflow.tools.readmission")

FHIR_SANDBOX = os.getenv("FHIR_SANDBOX_URL", "https://hapi.fhir.org/baseR4")


async def compute_readmission_risk(
    patient_id: str,
    fhir_server_url: str = "",
    fhir_access_token: str = "",
    discharge_diagnosis: str = "",
    patient_age: int = 0,
) -> dict:
    """
    AI-powered 30-day readmission risk assessment.

    Identifies high-risk patients who need intensive post-discharge
    follow-up to reduce costly readmissions.
    """
    ai = AIProvider()

    fhir_url = fhir_server_url or FHIR_SANDBOX
    fhir = FHIRClient(fhir_url, fhir_access_token)
    ctx = await fhir.get_patient_context(patient_id)

    user_prompt = build_readmission_prompt(
        patient_id, discharge_diagnosis, patient_age, ctx
    )

    try:
        result = await ai.analyze(READMISSION_SYSTEM, user_prompt)
        result["patient_id"] = patient_id
        result["data_source"] = "fhir_synthetic_data"
        return result

    except ValueError as e:
        logger.error(f"Readmission risk scoring failed: {e}")
        return {
            "risk_score": 50,
            "risk_category": "MODERATE",
            "risk_factors": [
                {
                    "factor": "Clinical evaluation needed",
                    "weight": "HIGH",
                    "detail": f"AI analysis incomplete: {str(e)[:200]}",
                }
            ],
            "protective_factors": [],
            "recommended_interventions": [
                {
                    "intervention": "Clinical review required",
                    "priority": "WITHIN_48H",
                }
            ],
            "follow_up_timeline": "Within 7 days",
            "estimated_readmission_probability": "Unknown",
            "ai_confidence": "LOW",
            "patient_id": patient_id,
            "data_source": "fhir_synthetic_data",
        }
