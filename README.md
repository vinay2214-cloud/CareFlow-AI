# CareFlow AI: Post-Discharge Care Intelligence

<div align="center">
  <img src="https://img.shields.io/badge/Status-Hackathon_Ready-success" alt="Status" />
  <img src="https://img.shields.io/badge/Protocol-MCP_v1.0-blue" alt="MCP" />
  <img src="https://img.shields.io/badge/AI-Google_Gemini-orange" alt="Gemini" />
  <img src="https://img.shields.io/badge/Data-FHIR_R4-purple" alt="FHIR" />
</div>

CareFlow AI is an MCP-native clinical intelligence server that helps reduce avoidable 30-day readmissions by turning discharge follow-up into a structured, risk-prioritized workflow.

It combines Google Gemini reasoning with FHIR R4 patient context to deliver:
- symptom triage with urgency scoring,
- care gap detection,
- readmission risk analysis,
- and physician-ready SBAR handoff notes.

---

## Executive Summary

Post-discharge transitions are one of the highest-risk moments in care delivery. Teams often miss early warning signals because triage, preventive follow-up, and handoff communication are disconnected across systems.

CareFlow AI addresses this gap with interoperable MCP tools that plug into any compatible assistant or client. Each tool produces structured, action-oriented output that can be consumed by care coordinators, clinicians, or downstream automation.

---

## Why This Matters for Hackathon Judging

| Judging Dimension | CareFlow AI Value |
|---|---|
| **Impact** | Addresses a major healthcare cost center: preventable readmissions and delayed follow-up. |
| **AI Quality** | Uses Gemini to reason over symptom combinations and patient context rather than static rule checks. |
| **Interoperability** | Built with MCP + FHIR R4 + SHARP-compatible context headers. |
| **Execution Feasibility** | Runs locally in minutes and deploys directly to Railway or Render. |

---

## Core MCP Tools

| Tool | What It Does | Primary Output |
|---|---|---|
| `analyze_symptoms` | Triages symptoms with optional FHIR context enrichment | Urgency level/score, red flags, care pathway |
| `detect_care_gaps` | Identifies preventive or monitoring gaps from patient context | Prioritized gap list and recommended follow-up |
| `compute_readmission_risk` | Estimates 30-day readmission risk and key drivers | Risk score/category, factors, interventions |
| `generate_handoff_note` | Produces structured SBAR handoff content | Situation, Background, Assessment, Recommendation |

---

## Technical Architecture

- **Application Layer:** FastMCP server exposing HTTP MCP tools
- **AI Layer:** Google Gemini via `google-genai` (`AI_MODEL` configurable)
- **Clinical Data Layer:** Async FHIR R4 access via `httpx`
- **Contract Layer:** Pydantic schemas for predictable I/O
- **Reliability:** Retry logic, timeout handling, and robust JSON extraction/repair

### SHARP Context Headers

| Header | Purpose |
|---|---|
| `X-FHIR-Server-URL` | FHIR base URL |
| `X-FHIR-Access-Token` | Bearer token for FHIR auth |
| `X-Patient-ID` | Patient resource ID |

When headers are provided, tools run with live patient context. Without headers, tools run in AI-only mode.

---

## Quick Start

### Requirements
- Python 3.10+
- Google Gemini API key ([Google AI Studio](https://aistudio.google.com/apikey))

### 1. Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
```

Set the key variables:

```env
GOOGLE_API_KEY=your-gemini-api-key
AI_MODEL=gemini-3-flash-preview
FHIR_SANDBOX_URL=https://hapi.fhir.org/baseR4
PORT=8000
```

### 3. Run

```bash
python server.py
```

Endpoints:
- MCP endpoint: `http://localhost:8000/mcp`
- Health check: `http://localhost:8000/`

### 4. Run Integration Client

```bash
python test_client.py
```

### 5. Verify Tool Discovery

```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
```

---

## Deployment

### Railway

1. Push this repository to GitHub
2. Create a Railway project from the repo
3. Configure environment variables:
   - `GOOGLE_API_KEY`
   - `AI_MODEL` (for example, `gemini-3-flash-preview`)
   - `FHIR_SANDBOX_URL` (optional)
4. Deploy (the included `Procfile` is already configured)

### Render

1. Create a new Web Service from this repository
2. Build command: `pip install -r requirements.txt`
3. Start command: `fastmcp run server.py:mcp --transport http --host 0.0.0.0 --port $PORT`
4. Add the same environment variables as above

---

## Suggested Demo Flow (Jury-Friendly)

1. Invoke `analyze_symptoms` with a high-risk symptom cluster (for example, chest pain + dyspnea + diaphoresis)
2. Invoke `detect_care_gaps` for the same patient ID
3. Invoke `compute_readmission_risk` with discharge context
4. Invoke `generate_handoff_note` to produce physician-ready SBAR output

This sequence demonstrates triage, prevention, risk stratification, and clinical communication in one continuous workflow.

---

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
│   └── readmission_risk.py
├── prompts/
│   └── clinical.py
└── utils/
    └── json_helpers.py
```

---

## Safety and Scope

- Designed for **clinical decision support**, not diagnostic replacement
- Demonstrated with synthetic/public FHIR sandbox data
- Produces structured outputs suitable for audit and downstream integration
- Includes graceful degradation when upstream AI/FHIR dependencies are unavailable

---

## Expected Operational Benefit

| Metric | Traditional Workflow | With CareFlow AI |
|---|---|---|
| Post-discharge risk visibility | Fragmented and manual | Real-time and structured |
| Care gap detection speed | Days to weeks | Seconds |
| Handoff consistency | Variable quality | Standardized SBAR output |
| Follow-up prioritization | Broad outreach | Risk-prioritized actions |

---

Built with Google Gemini, FastMCP, FHIR R4, and SHARP-compatible context propagation.
