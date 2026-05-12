# ── CAREFLOW AI DEMO SCRIPT ──────────────────────
# Run this ONCE first to get session ID
#!/bin/bash
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "    🏥 CareFlow AI — LIVE DEMO"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

SESSION=$(curl -s -D - https://careflow-ai-production-f474.up.railway.app/mcp \
  -X POST \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"demo","version":"1.0"}}}' \
  | grep -i "mcp-session-id" | awk '{print $2}' | tr -d '\r')
echo "✅ Connected to CareFlow AI MCP Server"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
sleep 2

echo ""
echo "🔍 TOOL 1: AI Symptom Triage"
echo "Patient: 62yr | Symptoms: chest pain, left arm radiation, diaphoresis"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
curl -s https://careflow-ai-production-f474.up.railway.app/mcp \
  -X POST \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"analyze_symptoms","arguments":{"symptoms":"chest pain radiating to left arm, shortness of breath, diaphoresis","patient_age":62}}}' \
  | python3 -c "
import sys,json
raw=sys.stdin.read()
for line in raw.split('\n'):
    if line.startswith('data:'):
        d=json.loads(line[5:])
        r=json.loads(d['result']['content'][0]['text'])
        print()
        print('  🚨 URGENCY LEVEL  :', r['urgency_level'])
        print('  📊 URGENCY SCORE  :', r['urgency_score'], '/ 10')
        print('  ⚠️  RED FLAGS      :', ', '.join(r['red_flags']))
        print('  🏥 GO TO          :', r['recommended_pathway'], '—', r['time_to_care'])
        print()
        print('  🤖 AI REASONING:')
        print('  ', r['ai_reasoning'][:300])
"
sleep 3

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 TOOL 2: Care Gap Detection (FHIR Data)"
echo "Fetching patient 592012 from HAPI FHIR sandbox..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
curl -s https://careflow-ai-production-f474.up.railway.app/mcp \
  -X POST \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"detect_care_gaps","arguments":{"patient_id":"592012","fhir_server_url":"https://hapi.fhir.org/baseR4","patient_age":62}}}' \
  | python3 -c "
import sys,json
raw=sys.stdin.read()
for line in raw.split('\n'):
    if line.startswith('data:'):
        d=json.loads(line[5:])
        r=json.loads(d['result']['content'][0]['text'])
        print()
        print('  📌 HIGH PRIORITY GAPS:', r.get('high_priority_count','?'))
        gaps=r.get('care_gaps',[])
        for g in gaps[:4]:
            print(f\"  ❗ [{g['priority']}] {g['description']}\")
        print()
        print('  📅 RECOMMENDED NEXT APPT:', r.get('recommended_next_appointment_type',''))
        print('  📝 SUMMARY:', r.get('summary','')[:200])
"
sleep 3

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 TOOL 3: 30-Day Readmission Risk Score"
echo "Diagnosis: Congestive Heart Failure | Age: 62"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
curl -s https://careflow-ai-production-f474.up.railway.app/mcp \
  -X POST \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION" \
  -d '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"compute_readmission_risk","arguments":{"patient_id":"592012","discharge_diagnosis":"Congestive Heart Failure","patient_age":62}}}' \
  | python3 -c "
import sys,json
raw=sys.stdin.read()
for line in raw.split('\n'):
    if line.startswith('data:'):
        d=json.loads(line[5:])
        r=json.loads(d['result']['content'][0]['text'])
        print()
        print('  🎯 RISK SCORE      :', r.get('risk_score','?'), '/ 100')
        print('  🔴 RISK CATEGORY   :', r.get('risk_category',''))
        print('  📉 PROBABILITY     :', r.get('estimated_readmission_probability',''))
        print()
        print('  ✅ INTERVENTIONS REQUIRED:')
        for i in r.get('recommended_interventions',[])[:3]:
            print(f\"    [{i['priority']}] {i['intervention']}\")
        print()
        print('  📅 FOLLOW-UP:', r.get('follow_up_timeline',''))
"
sleep 3

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📝 TOOL 4: SBAR Clinical Handoff Note"
echo "Generating physician handoff documentation..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
curl -s https://careflow-ai-production-f474.up.railway.app/mcp \
  -X POST \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION" \
  -d '{"jsonrpc":"2.0","id":5,"method":"tools/call","params":{"name":"generate_handoff_note","arguments":{"symptoms":"chest pain radiating to left arm, shortness of breath, diaphoresis"}}}' \
  | python3 -c "
import sys,json
raw=sys.stdin.read()
for line in raw.split('\n'):
    if line.startswith('data:'):
        d=json.loads(line[5:])
        r=json.loads(d['result']['content'][0]['text'])
        note=r.get('sbar_note',{})
        print()
        print('  S — SITUATION   :', note.get('situation','')[:120])
        print()
        print('  B — BACKGROUND  :', note.get('background','')[:120])
        print()
        print('  A — ASSESSMENT  :', note.get('assessment','')[:120])
        print()
        print('  R — RECOMMENDATION:', note.get('recommendation','')[:120])
        print()
        print('  🚨 URGENCY FLAG :', r.get('urgency_flag',''))
        print('  ⭐ ACUITY LEVEL :', r.get('estimated_acuity_level',''), '/ 5')
"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ CareFlow AI Demo Complete"
echo "🏥 4 Tools | FHIR R4 | SHARP-on-MCP | No PHI"
echo "🔗 https://app.promptopinion.ai/marketplace/mcp/019e1911-0570-749c-9b13-8e15396cbbd9"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"SESSION=$(curl -s -D - https://careflow-ai-production-f474.up.railway.app/mcp \
  -X POST \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"demo","version":"1.0"}}}' \
  | grep -i "mcp-session-id" | awk '{print $2}' | tr -d '\r')
echo "✅ Session: $SESSION"

# ── TOOL 1: Symptom Triage ───────────────────────
curl -s https://careflow-ai-production-f474.up.railway.app/mcp \
  -X POST \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"analyze_symptoms","arguments":{"symptoms":"chest pain radiating to left arm, shortness of breath, diaphoresis","patient_age":62}}}' \
  | python3 -c "
import sys,json
raw=sys.stdin.read()
for line in raw.split('\n'):
    if line.startswith('data:'):
        d=json.loads(line[5:])
        result=json.loads(d['result']['content'][0]['text'])
        print('\n🚨 URGENCY:', result['urgency_level'], '| SCORE:', result['urgency_score'],'/10')
        print('⚠️  RED FLAGS:', ', '.join(result['red_flags']))
        print('🏥 GO TO:', result['recommended_pathway'], '—', result['time_to_care'])
        print('🤖 AI REASONING:', result['ai_reasoning'][:200])
"

# ── TOOL 2: Care Gaps ────────────────────────────
curl -s https://careflow-ai-production-f474.up.railway.app/mcp \
  -X POST \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"detect_care_gaps","arguments":{"patient_id":"592012","fhir_server_url":"https://hapi.fhir.org/baseR4","patient_age":62}}}' \
  | python3 -c "
import sys,json
raw=sys.stdin.read()
for line in raw.split('\n'):
    if line.startswith('data:'):
        d=json.loads(line[5:])
        result=json.loads(d['result']['content'][0]['text'])
        print('\n📋 CARE GAPS FOUND:', result.get('high_priority_count','?'), 'HIGH PRIORITY')
        for g in result.get('care_gaps',[])[:3]:
            print(f\"  ❗ [{g['priority']}] {g['description']}\")
        print('📅 NEXT APPT:', result.get('recommended_next_appointment_type',''))
"

# ── TOOL 3: Readmission Risk ─────────────────────
curl -s https://careflow-ai-production-f474.up.railway.app/mcp \
  -X POST \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION" \
  -d '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"compute_readmission_risk","arguments":{"patient_id":"592012","discharge_diagnosis":"Congestive Heart Failure","patient_age":62}}}' \
  | python3 -c "
import sys,json
raw=sys.stdin.read()
for line in raw.split('\n'):
    if line.startswith('data:'):
        d=json.loads(line[5:])
        result=json.loads(d['result']['content'][0]['text'])
        print('\n📊 READMISSION RISK:', result.get('risk_score','?'), '% —', result.get('risk_category',''))
        print('📌 PROBABILITY:', result.get('estimated_readmission_probability',''))
        for i in result.get('recommended_interventions',[])[:3]:
            print(f\"  ✅ [{i['priority']}] {i['intervention']}\")
"

# ── TOOL 4: Handoff Note ─────────────────────────
curl -s https://careflow-ai-production-f474.up.railway.app/mcp \
  -X POST \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION" \
  -d '{"jsonrpc":"2.0","id":5,"method":"tools/call","params":{"name":"generate_handoff_note","arguments":{"symptoms":"chest pain radiating to left arm, shortness of breath, diaphoresis"}}}' \
  | python3 -c "
import sys,json
raw=sys.stdin.read()
for line in raw.split('\n'):
    if line.startswith('data:'):
        d=json.loads(line[5:])
        result=json.loads(d['result']['content'][0]['text'])
        note=result.get('sbar_note',{})
        print('\n📝 SBAR HANDOFF NOTE')
        print('S —', note.get('situation','')[:120])
        print('B —', note.get('background','')[:120])
        print('A —', note.get('assessment','')[:120])
        print('R —', note.get('recommendation','')[:120])
"
