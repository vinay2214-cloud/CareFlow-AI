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


# ═══════════════════════════════════════════════════════════════════════════
# MCP Server Initialization
# ═══════════════════════════════════════════════════════════════════════════

mcp = FastMCP(
    name="CareFlow AI",
    version="1.0.0",
    instructions=(
        "Post-Discharge Care Intelligence: AI-powered symptom triage, "
        "care gap detection, readmission risk scoring, and clinical handoff "
        "notes using FHIR R4 patient data via SHARP context propagation. "
        "Built for the Prompt Opinion Healthcare AI Hackathon."
    ),
)


# ═══════════════════════════════════════════════════════════════════════════
# Tool Registration
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool(
    description=(
        "AI-powered symptom triage with FHIR context enrichment. "
        "Analyzes patient symptoms to determine urgency level, likely clinical "
        "categories, red flags, and recommended care pathway. Detects dangerous "
        "symptom combinations and medication interactions that rule-based systems miss. "
        "Enriched with FHIR patient context when SHARP headers are provided."
    )
)
async def analyze_symptoms(
    symptoms: str,
    patient_age: int = 0,
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
        "Computes a 30-day hospital readmission risk score using AI analysis "
        "of patient conditions, medications, recent encounters, and social "
        "determinants. Goes beyond traditional LACE/HOSPITAL scores by "
        "incorporating contextual factors from FHIR data."
    )
)
async def compute_readmission_risk(
    patient_id: str,
    fhir_server_url: str = "",
    fhir_access_token: str = "",
    discharge_diagnosis: str = "",
    patient_age: int = 0,
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
        "description": (
            "Post-Discharge Care Intelligence — AI-powered symptom triage, "
            "care gap detection, readmission risk scoring, and clinical "
            "handoff notes using FHIR R4 via SHARP context propagation."
        ),
        "mcp_endpoint": "/mcp",
        "tools": [
            "analyze_symptoms",
            "detect_care_gaps",
            "generate_handoff_note",
            "compute_readmission_risk",
        ],
        "fhir_sandbox": os.getenv(
            "FHIR_SANDBOX_URL", "https://hapi.fhir.org/baseR4"
        ),
        "documentation": "https://github.com/YOUR_USERNAME/careflow-ai",
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
    logger.info(f"  AI Model:     {os.getenv('AI_MODEL', 'claude-sonnet-4-6')}")
    logger.info("=" * 60)

    # Add health routes for mcp.run() path too
    mcp._additional_http_routes.extend(_health_routes)

    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=port,
    )

