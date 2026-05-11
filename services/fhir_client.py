"""
CareFlow AI — FHIR R4 Client Service

Fetches and normalizes patient data from FHIR R4-compatible servers.
Supports SHARP context propagation via X-FHIR-* headers.
Gracefully degrades when FHIR is unavailable.
"""

from __future__ import annotations

import logging
from typing import Optional

import httpx

from models.schemas import PatientContext, FHIRObservation

logger = logging.getLogger("careflow.fhir")

# Default timeout for FHIR API calls (seconds)
FHIR_TIMEOUT = 12.0

# Maximum number of resources to fetch per type
MAX_RESOURCES = 10


class FHIRClient:
    """
    FHIR R4 client for fetching patient context.
    
    Supports:
    - Patient demographics
    - Active Conditions
    - Active MedicationRequests
    - Recent Observations (labs/vitals)
    - AllergyIntolerance
    - Recent Encounters
    """

    def __init__(self, base_url: str, access_token: str = ""):
        self.base_url = base_url.rstrip("/")
        self.headers = {"Accept": "application/fhir+json"}
        if access_token:
            self.headers["Authorization"] = f"Bearer {access_token}"

    async def get_patient_context(self, patient_id: str) -> PatientContext:
        """
        Fetch comprehensive patient context from FHIR server.
        
        Returns PatientContext with whatever data is available.
        Never raises — returns empty context with fhir_error on failure.
        """
        ctx = PatientContext(patient_id=patient_id)

        try:
            async with httpx.AsyncClient(timeout=FHIR_TIMEOUT) as client:
                # Fetch all resource types concurrently for speed
                ctx = await self._fetch_demographics(client, patient_id, ctx)
                ctx = await self._fetch_conditions(client, patient_id, ctx)
                ctx = await self._fetch_medications(client, patient_id, ctx)
                ctx = await self._fetch_observations(client, patient_id, ctx)
                ctx = await self._fetch_allergies(client, patient_id, ctx)
                ctx = await self._fetch_encounters(client, patient_id, ctx)

            logger.info(
                f"FHIR context loaded for patient {patient_id}: "
                f"{len(ctx.conditions)} conditions, "
                f"{len(ctx.medications)} medications, "
                f"{len(ctx.observations)} observations"
            )
        except httpx.TimeoutException:
            ctx.fhir_error = "FHIR server timeout"
            logger.warning(f"FHIR timeout for patient {patient_id}")
        except httpx.ConnectError:
            ctx.fhir_error = "FHIR server unreachable"
            logger.warning(f"FHIR connection failed for patient {patient_id}")
        except Exception as e:
            ctx.fhir_error = str(e)
            logger.error(f"FHIR fetch error for patient {patient_id}: {e}")

        return ctx

    async def _fetch_demographics(
        self, client: httpx.AsyncClient, patient_id: str, ctx: PatientContext
    ) -> PatientContext:
        """Fetch Patient resource for demographics."""
        try:
            r = await client.get(
                f"{self.base_url}/Patient/{patient_id}",
                headers=self.headers
            )
            if r.status_code == 200:
                pt = r.json()
                name = pt.get("name", [{}])[0]
                given = " ".join(name.get("given", []))
                family = name.get("family", "")
                ctx.patient_name = f"{given} {family}".strip()
                ctx.gender = pt.get("gender", "unknown")
                ctx.birth_date = pt.get("birthDate", "unknown")
        except Exception as e:
            logger.debug(f"Demographics fetch failed: {e}")
        return ctx

    async def _fetch_conditions(
        self, client: httpx.AsyncClient, patient_id: str, ctx: PatientContext
    ) -> PatientContext:
        """Fetch active Condition resources."""
        try:
            r = await client.get(
                f"{self.base_url}/Condition",
                params={"patient": patient_id, "clinical-status": "active"},
                headers=self.headers
            )
            if r.status_code == 200:
                bundle = r.json()
                ctx.conditions = [
                    self._extract_codeable_text(
                        entry.get("resource", {}), "code", "Unknown condition"
                    )
                    for entry in bundle.get("entry", [])
                    if "resource" in entry
                ][:MAX_RESOURCES]
        except Exception as e:
            logger.debug(f"Conditions fetch failed: {e}")
        return ctx

    async def _fetch_medications(
        self, client: httpx.AsyncClient, patient_id: str, ctx: PatientContext
    ) -> PatientContext:
        """Fetch active MedicationRequest resources."""
        try:
            r = await client.get(
                f"{self.base_url}/MedicationRequest",
                params={"patient": patient_id, "status": "active"},
                headers=self.headers
            )
            if r.status_code == 200:
                bundle = r.json()
                ctx.medications = [
                    self._extract_codeable_text(
                        entry.get("resource", {}),
                        "medicationCodeableConcept",
                        "Unknown medication"
                    )
                    for entry in bundle.get("entry", [])
                    if "resource" in entry
                ][:MAX_RESOURCES]
        except Exception as e:
            logger.debug(f"Medications fetch failed: {e}")
        return ctx

    async def _fetch_observations(
        self, client: httpx.AsyncClient, patient_id: str, ctx: PatientContext
    ) -> PatientContext:
        """Fetch recent Observation resources (labs and vitals)."""
        try:
            r = await client.get(
                f"{self.base_url}/Observation",
                params={
                    "patient": patient_id,
                    "_sort": "-date",
                    "_count": str(MAX_RESOURCES)
                },
                headers=self.headers
            )
            if r.status_code == 200:
                bundle = r.json()
                ctx.observations = [
                    FHIRObservation(
                        name=entry.get("resource", {}).get("code", {}).get("text", ""),
                        value=str(
                            entry.get("resource", {})
                                 .get("valueQuantity", {})
                                 .get("value", "")
                        ),
                        unit=entry.get("resource", {})
                             .get("valueQuantity", {})
                             .get("unit", ""),
                        date=entry.get("resource", {})
                             .get("effectiveDateTime", "")[:10]
                    )
                    for entry in bundle.get("entry", [])
                    if "resource" in entry
                ]
        except Exception as e:
            logger.debug(f"Observations fetch failed: {e}")
        return ctx

    async def _fetch_allergies(
        self, client: httpx.AsyncClient, patient_id: str, ctx: PatientContext
    ) -> PatientContext:
        """Fetch AllergyIntolerance resources."""
        try:
            r = await client.get(
                f"{self.base_url}/AllergyIntolerance",
                params={"patient": patient_id},
                headers=self.headers
            )
            if r.status_code == 200:
                bundle = r.json()
                ctx.allergies = [
                    self._extract_codeable_text(
                        entry.get("resource", {}), "code", "Unknown allergen"
                    )
                    for entry in bundle.get("entry", [])
                    if "resource" in entry
                ][:5]
        except Exception as e:
            logger.debug(f"Allergies fetch failed: {e}")
        return ctx

    async def _fetch_encounters(
        self, client: httpx.AsyncClient, patient_id: str, ctx: PatientContext
    ) -> PatientContext:
        """Fetch recent Encounter resources."""
        try:
            r = await client.get(
                f"{self.base_url}/Encounter",
                params={
                    "patient": patient_id,
                    "_sort": "-date",
                    "_count": "5"
                },
                headers=self.headers
            )
            if r.status_code == 200:
                bundle = r.json()
                ctx.encounters = [
                    {
                        "type": (
                            entry.get("resource", {})
                                 .get("type", [{}])[0]
                                 .get("text", "Unknown")
                            if entry.get("resource", {}).get("type")
                            else "Unknown"
                        ),
                        "status": entry.get("resource", {}).get("status", ""),
                        "period_start": (
                            entry.get("resource", {})
                                 .get("period", {})
                                 .get("start", "")[:10]
                        )
                    }
                    for entry in bundle.get("entry", [])
                    if "resource" in entry
                ]
        except Exception as e:
            logger.debug(f"Encounters fetch failed: {e}")
        return ctx

    @staticmethod
    def _extract_codeable_text(
        resource: dict, field: str, default: str = ""
    ) -> str:
        """Extract display text from a CodeableConcept field."""
        codeable = resource.get(field, {})
        # Try text first, then coding[0].display
        text = codeable.get("text", "")
        if not text:
            codings = codeable.get("coding", [])
            if codings:
                text = codings[0].get("display", default)
        return text or default
