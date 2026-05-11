# 🏥 CareFlow AI — Post-Discharge Care Intelligence

> **AI-powered MCP server for clinical triage, care gap detection, readmission risk scoring, and physician handoff notes using FHIR R4 patient data via SHARP context propagation.**

[![MCP Protocol](https://img.shields.io/badge/MCP-Protocol-blue?style=for-the-badge)](https://modelcontextprotocol.io)
[![FHIR R4](https://img.shields.io/badge/FHIR-R4-green?style=for-the-badge)](https://hl7.org/fhir/R4/)
[![SHARP](https://img.shields.io/badge/SHARP-Context-orange?style=for-the-badge)](https://www.healthit.gov/topic/standards-technology/standards/sharp)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-yellow?style=for-the-badge)](https://python.org)
[![Claude AI](https://img.shields.io/badge/Claude-Sonnet_4-purple?style=for-the-badge)](https://anthropic.com)

---

## 🎯 Problem Statement

**20% of patients are readmitted to hospital within 30 days.** This costs the US healthcare system **$26 billion annually** (CMS data). The root causes:

- **Missed care gaps** — overdue screenings, medication monitoring not flagged
- **Poor handoffs** — critical information lost between discharge and follow-up
- **No risk stratification** — high-risk patients don't receive intensive follow-up
- **Rule-based triage** — misses dangerous symptom *combinations*

## 💡 Solution

CareFlow AI is an **MCP-powered clinical intelligence server** that:

1. **Detects dangerous symptom combinations** that rule-based triage misses (e.g., chest pain + diaphoresis + arm radiation = STEMI pattern)
2. **Cross-references FHIR data** to find care gaps (e.g., diabetic on metformin with no HbA1c in 14 months)
3. **Scores readmission risk** beyond LACE/HOSPITAL scores using AI contextual analysis
4. **Generates SBAR handoff notes** in seconds for physician-to-physician communication

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Prompt Opinion Platform                │
│                  (MCP Client / Marketplace)              │
└──────────────────────┬──────────────────────────────────┘
                       │  JSON-RPC / MCP Protocol
                       ▼
┌─────────────────────────────────────────────────────────┐
│               CareFlow AI MCP Server                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │ Symptom  │  │  Care    │  │ Handoff  │  │Readmit │ │
│  │ Triage   │  │  Gaps    │  │  Note    │  │ Risk   │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └───┬────┘ │
│       │              │              │             │      │
│  ┌────▼──────────────▼──────────────▼─────────────▼───┐ │
│  │              AI Provider (Claude Sonnet 4)         │ │
│  │        Clinical Prompt Templates + JSON Parse      │ │
│  └────────────────────┬───────────────────────────────┘ │
│                       │                                  │
│  ┌────────────────────▼───────────────────────────────┐ │
│  │           FHIR R4 Client (SHARP Context)           │ │
│  │    Patient | Condition | MedicationRequest |       │ │
│  │    Observation | AllergyIntolerance | Encounter    │ │
│  └────────────────────┬───────────────────────────────┘ │
└───────────────────────┼─────────────────────────────────┘
                        │  FHIR R4 API
                        ▼
               ┌──────────────────┐
               │  HAPI FHIR R4    │
               │  Public Sandbox  │
               │  (Synthetic Data)│
               └──────────────────┘
```

### SHARP Context Propagation

CareFlow AI supports SHARP-on-MCP context headers:

| Header | Purpose |
|---|---|
| `X-FHIR-Server-URL` | FHIR R4 server base URL |
| `X-FHIR-Access-Token` | Bearer token for FHIR auth |
| `X-Patient-ID` | Patient resource ID |

When provided, all tools automatically enrich their analysis with live FHIR patient data. When absent, tools gracefully degrade to AI-only mode.

---

## 🛠 MCP Tools

### Tool 1: `analyze_symptoms`
**AI-powered symptom triage with FHIR context enrichment**

Detects dangerous symptom combinations and medication interactions that rule-based triage systems miss.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `symptoms` | string | ✅ | Patient symptoms |
| `patient_age` | int | ❌ | Age in years |
| `fhir_server_url` | string | ❌ | FHIR R4 server URL |
| `fhir_access_token` | string | ❌ | FHIR auth token |
| `patient_id` | string | ❌ | FHIR Patient ID |

**Returns:** urgency_level, urgency_score, red_flags, likely_conditions, care_pathway, ai_reasoning

### Tool 2: `detect_care_gaps`
**Cross-references conditions/medications/labs to find overdue screenings**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `patient_id` | string | ✅ | FHIR Patient ID |
| `fhir_server_url` | string | ❌ | FHIR R4 server URL |
| `fhir_access_token` | string | ❌ | FHIR auth token |
| `patient_age` | int | ❌ | Age in years |

**Returns:** care_gaps[], high_priority_count, summary, recommended_appointment_type

### Tool 3: `generate_handoff_note`
**SBAR-format physician handoff note generation**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `symptoms` | string | ✅ | Patient symptoms |
| `triage_result` | string | ❌ | JSON from Tool 1 |
| `care_gaps_result` | string | ❌ | JSON from Tool 2 |
| `fhir_server_url` | string | ❌ | FHIR R4 server URL |
| `fhir_access_token` | string | ❌ | FHIR auth token |
| `patient_id` | string | ❌ | FHIR Patient ID |

**Returns:** sbar_note{situation, background, assessment, recommendation}, urgency_flag, key_action_items

### Tool 4: `compute_readmission_risk`
**AI-enhanced 30-day readmission probability with interventions**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `patient_id` | string | ✅ | FHIR Patient ID |
| `fhir_server_url` | string | ❌ | FHIR R4 server URL |
| `fhir_access_token` | string | ❌ | FHIR auth token |
| `discharge_diagnosis` | string | ❌ | Primary diagnosis |
| `patient_age` | int | ❌ | Age in years |

**Returns:** risk_score (0-100), risk_category, risk_factors[], interventions[], follow_up_timeline

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Anthropic API key ([get one here](https://console.anthropic.com))

### Local Setup

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/careflow-ai.git
cd careflow-ai

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Start the server
python server.py
```

The MCP endpoint will be available at: `http://localhost:8000/mcp`

### Run Tests

```bash
# In a separate terminal (server must be running)
python test_client.py
```

### Verify Tool Discovery

```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
```

---

## ☁️ Deployment

### Railway (Recommended)

1. Push to GitHub
2. Go to [railway.app](https://railway.app) → **New Project → Deploy from GitHub**
3. Add environment variables:
   - `ANTHROPIC_API_KEY` = your key
   - `FHIR_SANDBOX_URL` = `https://hapi.fhir.org/baseR4`
4. Railway auto-detects the `Procfile` and deploys

Your production MCP endpoint: `https://your-app.up.railway.app/mcp`

### Render

1. Push to GitHub
2. Go to [render.com](https://render.com) → **New Web Service**
3. Connect your repo
4. Build command: `pip install -r requirements.txt`
5. Start command: `uvicorn server:app --host 0.0.0.0 --port $PORT`
6. Add environment variables

---

## 🏪 Prompt Opinion Marketplace

### Publishing

1. Go to [app.promptopinion.ai](https://app.promptopinion.ai)
2. Navigate to **Marketplace → Publish New Tool**
3. Fill in:
   - **Name:** CareFlow AI — Post-Discharge Care Intelligence
   - **MCP Server URL:** `https://your-app.up.railway.app/mcp`
   - **Auth Type:** Anonymous
   - **Category:** Clinical Decision Support
   - **Tags:** triage, care-gaps, readmission, FHIR, SHARP

### Demo Workflow

```
1. Search "CareFlow AI" in the Prompt Opinion marketplace
2. Select and invoke `analyze_symptoms`:
   - symptoms: "chest pain radiating to left arm, SOB, diaphoresis"
   - patient_age: 62
   - fhir_server_url: "https://hapi.fhir.org/baseR4"
   - patient_id: "592012"
3. See EMERGENT classification with red flags
4. Invoke `detect_care_gaps` with same patient
5. Invoke `compute_readmission_risk` with discharge diagnosis
6. Invoke `generate_handoff_note` combining all results
```

---

## 📁 Project Structure

```
careflow-ai/
├── server.py              # Main FastMCP server — tool registration & ASGI app
├── requirements.txt       # Python dependencies
├── .env.example           # Environment variable template
├── Procfile               # Railway/Render deployment
├── runtime.txt            # Python version pin
├── test_client.py         # Local test suite
├── models/
│   ├── __init__.py
│   └── schemas.py         # Pydantic data models for all I/O
├── services/
│   ├── __init__.py
│   ├── ai_provider.py     # Claude AI abstraction with retry logic
│   └── fhir_client.py     # Async FHIR R4 client
├── tools/
│   ├── __init__.py
│   ├── symptom_triage.py  # Tool 1: AI symptom analysis
│   ├── care_gaps.py       # Tool 2: Care gap detection
│   ├── handoff_note.py    # Tool 3: SBAR note generation
│   └── readmission_risk.py# Tool 4: 30-day risk scoring
├── prompts/
│   ├── __init__.py
│   └── clinical.py        # Prompt templates & builders
├── utils/
│   ├── __init__.py
│   └── json_helpers.py    # JSON extraction & repair
└── docs/
    └── .gitkeep
```

---

## 🔒 Compliance & Safety

- **No PHI**: All patient data comes from HAPI FHIR public sandbox (synthetic only)
- **No Diagnosis**: AI never provides definitive diagnoses — always recommends clinical evaluation
- **No Medical Advice**: System is for clinical decision *support*, not replacement
- **Data Sanitization**: All outputs are sanitized to prevent PHI leakage
- **Audit Trail**: Structured logging for all tool invocations
- **Graceful Degradation**: Tools never crash — return safe fallback results when AI/FHIR unavailable

---

## 🔧 Troubleshooting

| Issue | Solution |
|---|---|
| FastMCP version errors | `pip install "fastmcp>=2.0.0" --upgrade` |
| HAPI FHIR slow/timeout | Tools gracefully degrade to AI-only mode |
| Patient ID not found | Try: `592012`, `1277693`, `1855030` |
| Claude API errors | Verify `ANTHROPIC_API_KEY` in .env or Railway Variables |
| Railway deploy fails | Add `runtime.txt` with `python-3.11.0` |
| `tools/list` empty | Ensure `server.py` imports run without errors |

---

## 🗺 Roadmap

- [ ] **Stage 2**: Real-time FHIR webhook subscriptions
- [ ] **Stage 2**: Multi-patient batch analysis
- [ ] **Stage 2**: CDS Hooks integration for Epic/Cerner
- [ ] **Stage 3**: Longitudinal outcome tracking
- [ ] **Stage 3**: Custom clinical protocol engine
- [ ] **Stage 3**: HL7v2 ADT message integration

---

## 📊 Impact Hypothesis

| Metric | Current State | With CareFlow AI |
|---|---|---|
| 30-day readmission rate | 20% | Estimated 15-16% (-20% reduction) |
| Care gap detection time | Days to weeks | Seconds (real-time) |
| Handoff note quality | Inconsistent | Standardized SBAR |
| Annual savings potential | — | ~$3.9B at scale |

---

## 🏆 Hackathon Scoring

| Criteria | How CareFlow Delivers |
|---|---|
| **AI Factor** | Claude identifies symptom *combinations* and medication interactions that rule-based systems miss. Cross-references conditions with monitoring protocols. |
| **Potential Impact** | $26B readmission problem. 20% readmission rate reducible by 15-20%. Plugs into any Epic/Cerner via FHIR. |
| **Feasibility** | FHIR R4 standard (Epic/Cerner compatible). SHARP context headers. Synthetic data only. Deployable today. |

---

*Built with Claude Sonnet 4 + FastMCP + FHIR R4 + SHARP-on-MCP Context Propagation*

*Submission for the Prompt Opinion Healthcare AI Hackathon — Agents Assemble*
