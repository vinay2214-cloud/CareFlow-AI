"""
CareFlow AI — Tool 5: Medication Reconciliation

Performs AI-powered discharge medication reconciliation using optional
FHIR medication history and clinical context.
"""

from __future__ import annotations

import os
import logging

from services.ai_provider import AIProvider
from services.fhir_client import FHIRClient
from models.schemas import PatientContext
from prompts.clinical import (
    MED_RECON_SYSTEM,
    build_medication_reconciliation_prompt,
)

logger = logging.getLogger("careflow.tools.med_recon")

FHIR_SANDBOX = os.getenv("FHIR_SANDBOX_URL", "https://hapi.fhir.org/baseR4")


async def medication_reconciliation(
    discharge_medications: str,
    patient_id: str = "",
    fhir_server_url: str = "",
    fhir_access_token: str = "",
) -> dict:
    """
    AI medication reconciliation at discharge.

    Identifies high-risk discrepancies such as omissions, duplications,
    interactions, and high-alert medication issues.
    """
    ai = AIProvider()
    ctx = PatientContext(patient_id=patient_id)

    if patient_id:
        fhir_url = fhir_server_url or FHIR_SANDBOX
        fhir = FHIRClient(fhir_url, fhir_access_token)
        ctx = await fhir.get_patient_context(patient_id)

    user_prompt = build_medication_reconciliation_prompt(
        discharge_medications=discharge_medications,
        patient_id=patient_id,
        ctx=ctx,
    )

    try:
        result = await ai.analyze(MED_RECON_SYSTEM, user_prompt)
        result["patient_id"] = patient_id
        result["discharge_medications_reviewed"] = discharge_medications
        result["fhir_history_used"] = bool(ctx.medications)
        result["data_source"] = "synthetic_data_no_phi"
        return result
    except ValueError as e:
        logger.error(f"Medication reconciliation failed: {e}")
        return {
            "overall_risk": "HIGH",
            "safe_to_discharge": False,
            "requires_pharmacist_review": True,
            "discrepancies": [],
            "high_alert_medications_on_list": [],
            "drug_interactions_detected": [],
            "missing_medications_for_conditions": [],
            "pharmacist_counseling_points": ["Manual pharmacist review required"],
            "monitoring_required": ["Clinical review required before discharge"],
            "reconciliation_summary": f"AI analysis incomplete: {str(e)[:300]}",
            "patient_id": patient_id,
            "discharge_medications_reviewed": discharge_medications,
            "fhir_history_used": bool(ctx.medications),
            "data_source": "synthetic_data_no_phi",
        }
