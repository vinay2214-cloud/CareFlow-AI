# 🏥 CareFlow AI — Post-Discharge Care Intelligence

> **Agents Assemble Hackathon 2026** | Path A: MCP Server | Prompt Opinion Platform

[![Marketplace](https://img.shields.io/badge/Prompt%20Opinion-Live%20on%20Marketplace-teal)](https://app.promptopinion.ai/marketplace/mcp/019e1911-0570-749c-9b13-8e15396cbbd9)
[![FHIR R4](https://img.shields.io/badge/FHIR-R4%20Compatible-blue)](https://hapi.fhir.org)
[![SHARP](https://img.shields.io/badge/SHARP--on--MCP-Compliant-green)](https://sharponmcp.com)
[![Deploy](https://img.shields.io/badge/Deployed-Railway-purple)](https://railway.app)
[![No PHI](https://img.shields.io/badge/PHI-Zero%20%E2%80%94%20Synthetic%20Data%20Only-red)](https://hapi.fhir.org/baseR4)

## The Problem

**1 in 5 hospital patients is readmitted within 30 days. That's $26 billion annually in the US.**

The gap is not in medical guidelines; it is in connecting symptoms, vital signs,
FHIR history, medication safety, social barriers, and follow-up actions in real
time before discharge.

## What CareFlow AI Does

CareFlow AI is a SHARP-on-MCP compliant MCP server with **5 clinical AI tools**
available directly on the Prompt Opinion platform.

| Tool | What it does | Why AI wins here |
|------|-------------|-----------------|
| `analyze_symptoms` | Urgency triage with symptom + vital sign awareness | Identifies dangerous symptom **combinations** and physiologic patterns, not isolated rules |
| `detect_care_gaps` | Detects overdue screenings and monitoring from FHIR context | Cross-references conditions × medications × observations simultaneously |
| `compute_readmission_risk` | 30-day readmission risk with social determinants | Combines clinical burden with living situation, transportation, and recent readmissions |
| `generate_handoff_note` | Structured SBAR handoff for clinicians | Synthesizes fragmented context into physician-ready communication |
| `medication_reconciliation` | AI discharge medication safety review | Flags omissions, interactions, duplications, and high-alert medication risks |

## Architecture

```text
Prompt Opinion Platform (agent/client)
        │
        │ SHARP Headers:
        │ X-FHIR-Server-URL
        │ X-FHIR-Access-Token
        │ X-Patient-ID
        ▼
CareFlow AI MCP Server (FastMCP / Railway)
        ├── Google Gemini (clinical reasoning → structured JSON)
        └── HAPI FHIR R4 (Patient, Condition, MedicationRequest,
                          Observation, AllergyIntolerance, Encounter)
```

## Live Demo

- **Marketplace:** https://app.promptopinion.ai/marketplace/mcp/019e1911-0570-749c-9b13-8e15396cbbd9
- **MCP Endpoint:** https://careflow-ai-production-f474.up.railway.app/mcp
- **Health Check:** https://careflow-ai-production-f474.up.railway.app/

## Quick Start

```bash
git clone https://github.com/YOUR_USERNAME/careflow-ai
cd careflow-ai
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Add GOOGLE_API_KEY to .env
python server.py
# Server runs at http://localhost:8000/mcp
```

Environment variables:

```env
GOOGLE_API_KEY=your-gemini-api-key
AI_MODEL=gemini-3-flash-preview
FHIR_SANDBOX_URL=https://hapi.fhir.org/baseR4
PORT=8000
```

## Standards Compliance

| Standard | Status | Detail |
|----------|--------|--------|
| SHARP-on-MCP | ✅ Compliant | `X-FHIR-Server-URL`, `X-FHIR-Access-Token`, `X-Patient-ID` |
| FHIR R4 | ✅ Compatible | Epic, Cerner, MEDITECH, HAPI FHIR-compatible endpoints |
| MCP Protocol | ✅ Streamable HTTP | FastMCP with session-aware JSON-RPC |
| PHI | ✅ Zero | Public synthetic HAPI sandbox only |
| Open Access | ✅ Marketplace discoverable | Public MCP endpoint and tool metadata |

## Impact Hypothesis

| Metric | Data |
|--------|------|
| US 30-day readmission cost | $26B/year (CMS estimate) |
| Current readmission rate | ~20% within 30 days |
| Projected reduction with CareFlow AI | 15-20% via triage + risk stratification + med safety |
| Handoff documentation saved | 15-20 min per patient |
| Medication errors at discharge | ~20% of readmissions involve med-related issues |
| Estimated savings (500-bed hospital) | Multi-million annual penalty/risk reduction potential |

## Repository Structure

```text
careflow-ai/
├── server.py
├── requirements.txt
├── .env.example
├── Procfile
├── runtime.txt
├── test_client.py
├── models/
│   └── schemas.py
├── services/
│   ├── ai_provider.py
│   └── fhir_client.py
├── tools/
│   ├── symptom_triage.py
│   ├── care_gaps.py
│   ├── handoff_note.py
│   ├── readmission_risk.py
│   └── medication_reconciliation.py
├── prompts/
│   └── clinical.py
└── utils/
    └── json_helpers.py
```
