"""
CareFlow AI — Local Test Client

Tests all 4 MCP tools against the running server using the FastMCP client.
Run: python test_client.py

Prerequisites:
  1. Server running: python server.py
  2. ANTHROPIC_API_KEY set in .env (with credits)
"""

from __future__ import annotations

import asyncio
import json
import sys
import time

# Color output helpers
GREEN = "\033[92m"
RED = "\033[91m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
BOLD = "\033[1m"
RESET = "\033[0m"

# Known synthetic patients in HAPI FHIR sandbox
TEST_PATIENT_ID = "592012"
HAPI_FHIR = "https://hapi.fhir.org/baseR4"
SERVER_URL = "http://127.0.0.1:8000/mcp"


def banner(text: str) -> None:
    """Print a styled test banner."""
    print(f"\n{BOLD}{CYAN}{'═' * 60}{RESET}")
    print(f"{BOLD}{CYAN}  {text}{RESET}")
    print(f"{BOLD}{CYAN}{'═' * 60}{RESET}\n")


def extract_result(result) -> dict:
    """Extract parsed JSON from FastMCP CallToolResult."""
    text = result.content[0].text
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"raw_text": text}


async def run_tests():
    """Run all MCP tool tests using the FastMCP client."""
    from fastmcp import Client

    banner("CareFlow AI — Test Suite")
    print(f"  Server:  {SERVER_URL}")
    print(f"  Patient: {TEST_PATIENT_ID}")
    print(f"  FHIR:    {HAPI_FHIR}")

    results = {}

    async with Client(SERVER_URL) as client:
        # ── Test 0: Tool Discovery ────────────────────────────────────
        banner("TEST 0: tools/list — Tool Discovery")
        tools = await client.list_tools()
        tool_names = [t.name for t in tools]
        print(f"  Discovered {len(tools)} tools:")
        for t in tools:
            print(f"    • {GREEN}{t.name}{RESET}")
            desc = t.description or ""
            print(f"      {desc[:80]}...")

        expected = [
            "analyze_symptoms",
            "detect_care_gaps",
            "generate_handoff_note",
            "compute_readmission_risk",
        ]
        missing = [t for t in expected if t not in tool_names]
        if missing:
            print(f"\n  {RED}MISSING TOOLS: {missing}{RESET}")
            results["discovery"] = False
        else:
            print(f"\n  {GREEN}✅ All 4 tools discovered{RESET}")
            results["discovery"] = True

        # ── Test 1: Symptom Triage ────────────────────────────────────
        banner("TEST 1: analyze_symptoms — AI Triage")
        start = time.time()
        try:
            result = await client.call_tool(
                "analyze_symptoms",
                {
                    "symptoms": "chest pain radiating to left arm, shortness of breath, diaphoresis for 2 hours",
                    "patient_age": 62,
                    "fhir_server_url": HAPI_FHIR,
                    "patient_id": TEST_PATIENT_ID,
                },
            )
            elapsed = time.time() - start
            data = extract_result(result)
            print(json.dumps(data, indent=2))
            print(f"\n  ⏱️  Completed in {elapsed:.1f}s")

            if data.get("urgency_level"):
                print(f"  {GREEN}✅ Urgency: {data['urgency_level']} (score: {data.get('urgency_score')}){RESET}")
                results["triage"] = True
            else:
                print(f"  {RED}❌ Missing urgency_level{RESET}")
                results["triage"] = False
        except Exception as e:
            elapsed = time.time() - start
            print(f"  {RED}❌ Error: {e}{RESET}")
            print(f"  ⏱️  Failed in {elapsed:.1f}s")
            results["triage"] = False

        # ── Test 2: Care Gap Detection ────────────────────────────────
        banner("TEST 2: detect_care_gaps — Care Gap Analysis")
        start = time.time()
        try:
            result = await client.call_tool(
                "detect_care_gaps",
                {
                    "patient_id": TEST_PATIENT_ID,
                    "fhir_server_url": HAPI_FHIR,
                    "patient_age": 62,
                },
            )
            elapsed = time.time() - start
            data = extract_result(result)
            print(json.dumps(data, indent=2))
            print(f"\n  ⏱️  Completed in {elapsed:.1f}s")

            gaps = data.get("care_gaps", [])
            if isinstance(gaps, list):
                print(f"  {GREEN}✅ Found {len(gaps)} care gaps, {data.get('high_priority_count', 0)} high priority{RESET}")
                results["gaps"] = True
            else:
                print(f"  {RED}❌ Invalid care_gaps format{RESET}")
                results["gaps"] = False
        except Exception as e:
            elapsed = time.time() - start
            print(f"  {RED}❌ Error: {e}{RESET}")
            results["gaps"] = False

        # ── Test 3: Readmission Risk ──────────────────────────────────
        banner("TEST 3: compute_readmission_risk — 30-Day Risk Score")
        start = time.time()
        try:
            result = await client.call_tool(
                "compute_readmission_risk",
                {
                    "patient_id": TEST_PATIENT_ID,
                    "fhir_server_url": HAPI_FHIR,
                    "discharge_diagnosis": "Congestive Heart Failure",
                    "patient_age": 62,
                },
            )
            elapsed = time.time() - start
            data = extract_result(result)
            print(json.dumps(data, indent=2))
            print(f"\n  ⏱️  Completed in {elapsed:.1f}s")

            if data.get("risk_score") is not None:
                print(f"  {GREEN}✅ Risk: {data['risk_category']} ({data['risk_score']}/100){RESET}")
                results["risk"] = True
            else:
                print(f"  {RED}❌ Missing risk_score{RESET}")
                results["risk"] = False
        except Exception as e:
            elapsed = time.time() - start
            print(f"  {RED}❌ Error: {e}{RESET}")
            results["risk"] = False

        # ── Test 4: Handoff Note ──────────────────────────────────────
        banner("TEST 4: generate_handoff_note — SBAR Note")
        start = time.time()
        try:
            result = await client.call_tool(
                "generate_handoff_note",
                {
                    "symptoms": "chest pain, shortness of breath, diaphoresis",
                    "fhir_server_url": HAPI_FHIR,
                    "patient_id": TEST_PATIENT_ID,
                },
            )
            elapsed = time.time() - start
            data = extract_result(result)
            print(json.dumps(data, indent=2))
            print(f"\n  ⏱️  Completed in {elapsed:.1f}s")

            sbar = data.get("sbar_note", {})
            if sbar.get("situation"):
                print(f"  {GREEN}✅ SBAR note generated (acuity: {data.get('estimated_acuity_level')}){RESET}")
                results["handoff"] = True
            else:
                print(f"  {RED}❌ Missing SBAR content{RESET}")
                results["handoff"] = False
        except Exception as e:
            elapsed = time.time() - start
            print(f"  {RED}❌ Error: {e}{RESET}")
            results["handoff"] = False

    # ── Summary ───────────────────────────────────────────────────────
    banner("TEST SUMMARY")
    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        status = f"{GREEN}PASS{RESET}" if result else f"{RED}FAIL{RESET}"
        print(f"  {status}  {name}")

    print(f"\n  {BOLD}{passed}/{total} tests passed{RESET}")

    if passed == total:
        print(f"\n  {GREEN}{BOLD}🎉 All tests passed! CareFlow AI is ready for deployment.{RESET}")
    else:
        print(f"\n  {YELLOW}⚠️  Some tests failed. Check output above.{RESET}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(run_tests())
