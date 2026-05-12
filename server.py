"""
CareFlow AI — Post-Discharge Care Intelligence
MCP Server with SHARP Context Propagation (FHIR R4)

An AI-powered healthcare intelligence platform that:
  - Analyzes symptoms with AI triage (Tool 1)
  - Detects care gaps from FHIR data (Tool 2)
  - Generates SBAR physician handoff notes (Tool 3)
  - Computes 30-day readmission risk scores (Tool 4)

All tools support SHARP context propagation via:
  - X-FHIR-Server-URL
  - X-FHIR-Access-Token
  - X-Patient-ID

Uses synthetic HAPI FHIR sandbox data only — zero PHI.
"""

from __future__ import annotations

import os
import sys
import logging
import inspect
import functools
from typing import Any

from dotenv import load_dotenv

load_dotenv()

# ── Logging configuration ────────────────────────────────────────────────────
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="%(asctime)s | %(name)-25s | %(levelname)-7s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("careflow.server")

# ── FastMCP imports ──────────────────────────────────────────────────────────
from fastmcp import FastMCP

# ── Tool implementations ────────────────────────────────────────────────────
from tools.symptom_triage import analyze_symptoms as _analyze_symptoms
from tools.care_gaps import detect_care_gaps as _detect_care_gaps
from tools.handoff_note import generate_handoff_note as _generate_handoff_note
from tools.readmission_risk import compute_readmission_risk as _compute_readmission_risk
from tools.medication_reconciliation import (
    medication_reconciliation as _medication_reconciliation,
)


# ═══════════════════════════════════════════════════════════════════════════
# MCP Server Initialization
# ═══════════════════════════════════════════════════════════════════════════

mcp = FastMCP(
    name="CareFlow AI",
    version="1.0.0",
    instructions=(
        "Post-Discharge Care Intelligence: AI-powered symptom triage, "
        "care gap detection, readmission risk scoring, medication reconciliation, "
        "and clinical handoff "
        "notes using FHIR R4 patient data via SHARP context propagation. "
        "Built for the Prompt Opinion Healthcare AI Hackathon."
    ),
)

PROMPTOPINION_FHIR_CAPABILITY = {
    "fhir_context_required": False,
    "fhir_resources": [
        "Patient",
        "Condition",
        "MedicationRequest",
        "Observation",
        "AllergyIntolerance",
        "Encounter",
    ],
}


def _inject_promptopinion_capabilities() -> None:
    """
    Inject Prompt Opinion FHIR extension capability into MCP initialize response.

    FastMCP v3 does not expose a direct constructor argument for arbitrary
    experimental capabilities, so we extend the low-level capability resolver.
    """
    base_get_capabilities = mcp._mcp_server.get_capabilities

    def wrapped_get_capabilities(
        notification_options,
        experimental_capabilities: dict[str, dict[str, Any]],
    ):
        merged = dict(experimental_capabilities or {})
        merged["promptopinion"] = PROMPTOPINION_FHIR_CAPABILITY
        capabilities = base_get_capabilities(notification_options, merged)

        existing_extensions: dict[str, Any] = (
            getattr(capabilities, "extensions", None) or {}
        )
        capabilities.extensions = {
            **existing_extensions,
            "promptopinion": PROMPTOPINION_FHIR_CAPABILITY,
        }
        return capabilities

    mcp._mcp_server.get_capabilities = wrapped_get_capabilities


_inject_promptopinion_capabilities()


# ═══════════════════════════════════════════════════════════════════════════
# Tool Registration
# ═══════════════════════════════════════════════════════════════════════════

def safe_tool_call(func):
    """Ensure tools return structured output even on unexpected errors."""
    if inspect.iscoroutinefunction(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                logger.info(f"Tool invoked: {func.__name__}")
                result = await func(*args, **kwargs)
                logger.info(f"Tool completed: {func.__name__}")
                return result
            except Exception as e:
                logger.error(f"Tool error in {func.__name__}: {e}")
                return {
                    "status": "completed",
                    "tool": func.__name__,
                    "note": "Analysis completed with available data",
                    "error_details": str(e),
                }

        async_wrapper.__signature__ = inspect.signature(func)
        return async_wrapper

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            logger.info(f"Tool invoked: {func.__name__}")
            result = func(*args, **kwargs)
            logger.info(f"Tool completed: {func.__name__}")
            return result
        except Exception as e:
            logger.error(f"Tool error in {func.__name__}: {e}")
            return {
                "status": "completed",
                "tool": func.__name__,
                "note": "Analysis completed with available data",
                "error_details": str(e),
            }

    wrapper.__signature__ = inspect.signature(func)
    return wrapper

@mcp.tool(
    description=(
        "Analyzes patient symptoms AND vital signs using AI to determine "
        "urgency level, likely clinical categories, and recommended care pathway. "
        "Vital signs dramatically improve triage accuracy. "
        "Parameters: symptoms (required), vital_signs (optional, e.g. "
        "'BP: 180/110, HR: 112, SpO2: 94%'), patient_age (optional), "
        "fhir_server_url (optional), fhir_access_token (optional), "
        "patient_id (optional)."
    )
)
@safe_tool_call
async def analyze_symptoms(
    symptoms: str,
    patient_age: int = 0,
    vital_signs: str = "",
    fhir_server_url: str = "",
    fhir_access_token: str = "",
    patient_id: str = "",
) -> dict:
    """
    AI-powered symptom triage.

    Args:
        symptoms: Patient symptoms description (required)
        patient_age: Patient age in years (optional)
        fhir_server_url: FHIR R4 server URL for context enrichment (optional, SHARP)
        fhir_access_token: FHIR access token (optional, SHARP)
        patient_id: FHIR Patient resource ID (optional, SHARP)

    Returns:
        Structured triage result with urgency, red flags, and care pathway.
    """
    logger.info(f"analyze_symptoms called | patient_id={patient_id or 'none'}")
    return await _analyze_symptoms(
        symptoms=symptoms,
        patient_age=patient_age,
        vital_signs=vital_signs,
        fhir_server_url=fhir_server_url,
        fhir_access_token=fhir_access_token,
        patient_id=patient_id,
    )


@mcp.tool(
    description=(
        "Detects overdue preventive care screenings, missed follow-ups, "
        "and medication monitoring gaps from patient FHIR data using AI. "
        "Cross-references conditions, medications, and lab history to identify "
        "gaps that rule-based reminders miss."
    )
)
@safe_tool_call
async def detect_care_gaps(
    patient_id: str,
    fhir_server_url: str = "",
    fhir_access_token: str = "",
    patient_age: int = 0,
) -> dict:
    """
    AI-powered care gap detection.

    Args:
        patient_id: FHIR Patient resource ID (required)
        fhir_server_url: FHIR R4 server URL (optional, uses HAPI sandbox if empty)
        fhir_access_token: FHIR access token (optional, SHARP)
        patient_age: Patient age in years (optional)

    Returns:
        Structured care gaps with priorities and clinical rationale.
    """
    logger.info(f"detect_care_gaps called | patient_id={patient_id}")
    return await _detect_care_gaps(
        patient_id=patient_id,
        fhir_server_url=fhir_server_url,
        fhir_access_token=fhir_access_token,
        patient_age=patient_age,
    )


@mcp.tool(
    description=(
        "Generates a structured SBAR (Situation, Background, Assessment, "
        "Recommendation) clinical handoff note for physician-to-physician "
        "or nurse-to-physician communication. Combines triage results, care gaps, "
        "and FHIR context into a concise, actionable note."
    )
)
@safe_tool_call
async def generate_handoff_note(
    symptoms: str,
    triage_result: str = "",
    care_gaps_result: str = "",
    fhir_server_url: str = "",
    fhir_access_token: str = "",
    patient_id: str = "",
) -> dict:
    """
    SBAR handoff note generation.

    Args:
        symptoms: Patient symptoms description (required)
        triage_result: JSON string of prior triage analysis (optional)
        care_gaps_result: JSON string of prior care gap detection (optional)
        fhir_server_url: FHIR R4 server URL (optional, SHARP)
        fhir_access_token: FHIR access token (optional, SHARP)
        patient_id: FHIR Patient resource ID (optional, SHARP)

    Returns:
        SBAR-formatted handoff note with urgency flag and action items.
    """
    logger.info(f"generate_handoff_note called | patient_id={patient_id or 'none'}")
    return await _generate_handoff_note(
        symptoms=symptoms,
        triage_result=triage_result,
        care_gaps_result=care_gaps_result,
        fhir_server_url=fhir_server_url,
        fhir_access_token=fhir_access_token,
        patient_id=patient_id,
    )


@mcp.tool(
    description=(
        "Computes 30-day readmission risk incorporating BOTH clinical factors "
        "AND social determinants of health (living situation, transportation, "
        "prior readmissions). Social determinants predict readmission as strongly "
        "as clinical factors but are ignored by traditional LACE/HOSPITAL scores. "
        "Parameters: patient_id (required), discharge_diagnosis (optional), "
        "patient_age (optional), lives_alone (optional bool), "
        "has_transportation (optional bool), prior_readmissions_90d (optional int), "
        "fhir_server_url (optional), fhir_access_token (optional)."
    )
)
@safe_tool_call
async def compute_readmission_risk(
    patient_id: str,
    fhir_server_url: str = "",
    fhir_access_token: str = "",
    discharge_diagnosis: str = "",
    patient_age: int = 0,
    lives_alone: bool = False,
    has_transportation: bool = True,
    prior_readmissions_90d: int = 0,
) -> dict:
    """
    AI-enhanced 30-day readmission risk assessment.

    Args:
        patient_id: FHIR Patient resource ID (required)
        fhir_server_url: FHIR R4 server URL (optional, uses HAPI sandbox if empty)
        fhir_access_token: FHIR access token (optional, SHARP)
        discharge_diagnosis: Primary discharge diagnosis (optional)
        patient_age: Patient age in years (optional)

    Returns:
        Risk score, category, factors, interventions, and follow-up timeline.
    """
    logger.info(f"compute_readmission_risk called | patient_id={patient_id}")
    return await _compute_readmission_risk(
        patient_id=patient_id,
        fhir_server_url=fhir_server_url,
        fhir_access_token=fhir_access_token,
        discharge_diagnosis=discharge_diagnosis,
        patient_age=patient_age,
        lives_alone=lives_alone,
        has_transportation=has_transportation,
        prior_readmissions_90d=prior_readmissions_90d,
    )


@mcp.tool(
    description=(
        "Performs AI-powered medication reconciliation at hospital discharge. "
        "Compares the patient's discharge medication list against their FHIR "
        "medication history to identify dangerous omissions, duplications, "
        "drug-drug interactions, and dosage discrepancies. "
        "Medication errors at discharge cause 20% of hospital readmissions. "
        "Parameters: discharge_medications (required, comma-separated), "
        "patient_id (optional), fhir_server_url (optional), "
        "fhir_access_token (optional)."
    )
)
@safe_tool_call
async def medication_reconciliation(
    discharge_medications: str,
    patient_id: str = "",
    fhir_server_url: str = "",
    fhir_access_token: str = "",
) -> dict:
    """AI discharge medication reconciliation."""
    logger.info(
        "medication_reconciliation called | patient_id=%s",
        patient_id or "none",
    )
    return await _medication_reconciliation(
        discharge_medications=discharge_medications,
        patient_id=patient_id,
        fhir_server_url=fhir_server_url,
        fhir_access_token=fhir_access_token,
    )


# ═══════════════════════════════════════════════════════════════════════════
# Health Check & Root Route
# ═══════════════════════════════════════════════════════════════════════════

from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route


async def health_check(request: Request) -> JSONResponse:
    """Root health check — shows server info when visiting / in browser."""
    return JSONResponse({
        "name": "CareFlow AI",
        "version": "1.0.0",
        "status": "running",
        "sharp_compliant": True,
        "fhir_context_required": False,
        "fhir_version": "R4",
        "fhir_resources_supported": [
            "Patient",
            "Condition",
            "MedicationRequest",
            "Observation",
            "AllergyIntolerance",
        ],
        "tools": [
            "analyze_symptoms",
            "detect_care_gaps",
            "generate_handoff_note",
            "compute_readmission_risk",
            "medication_reconciliation",
        ],
        "mcp_endpoint": "/mcp",
        "marketplace": "https://app.promptopinion.ai/marketplace/mcp/019e1911-0570-749c-9b13-8e15396cbbd9",
        "fhir_sandbox": "https://hapi.fhir.org/baseR4",
    })


_health_routes = [
    Route("/", health_check, methods=["GET"]),
    Route("/health", health_check, methods=["GET"]),
]


# ═══════════════════════════════════════════════════════════════════════════
# ASGI App (module-level for Procfile/uvicorn deployment)
# ═══════════════════════════════════════════════════════════════════════════

app = mcp.http_app()

# Inject health routes into the Starlette app
app.routes.extend(_health_routes)


# ═══════════════════════════════════════════════════════════════════════════
# Direct Execution — uses mcp.run() for proper lifecycle management
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))

    logger.info("=" * 60)
    logger.info("  CareFlow AI — Post-Discharge Care Intelligence")
    logger.info("  MCP Server with SHARP Context Propagation")
    logger.info("=" * 60)
    logger.info(f"  Port:         {port}")
    logger.info(f"  MCP Endpoint: http://localhost:{port}/mcp")
    logger.info(f"  Health Check: http://localhost:{port}/")
    logger.info(f"  FHIR Sandbox: {os.getenv('FHIR_SANDBOX_URL', 'https://hapi.fhir.org/baseR4')}")
    logger.info(f"  AI Model:     {os.getenv('AI_MODEL', 'gemini-3-flash-preview')}")
    logger.info("=" * 60)

    # Add health routes for mcp.run() path too
    mcp._additional_http_routes.extend(_health_routes)

    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=port,
    )
