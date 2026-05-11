"""
CareFlow AI — AI Provider Abstraction

Clean abstraction over Google Gemini API with retry logic, timeout handling,
and structured JSON output enforcement.
"""

from __future__ import annotations

import os
import logging
import asyncio

from google import genai

from utils.json_helpers import extract_json

logger = logging.getLogger("careflow.ai")

MAX_RETRIES = 2
RETRY_DELAY = 1.0


class AIProvider:
    """
    Abstracted AI provider for clinical reasoning.
    Uses Google Gemini 2.0 Flash (free tier).
    """

    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY", "")
        if not api_key:
            logger.warning("GOOGLE_API_KEY not set — AI calls will fail")
        self.client = genai.Client(api_key=api_key)
        self.model = os.getenv("AI_MODEL", "gemini-3-flash-preview")

    async def analyze(
        self,
        system_prompt: str,
        user_content: str,
        max_tokens: int = 8192,
    ) -> dict:
        """
        Send prompt to Gemini, parse JSON response with retries.

        Raises ValueError if all retries exhausted.
        """
        last_error = None
        raw_text = ""

        for attempt in range(MAX_RETRIES + 1):
            try:
                response = await asyncio.to_thread(
                    self._call_gemini, system_prompt, user_content, max_tokens,
                )
                raw_text = response.text or ""
                result = extract_json(raw_text)
                logger.info(f"AI analysis successful (attempt {attempt + 1})")
                return result

            except Exception as e:
                last_error = e
                error_msg = str(e).lower()

                if "quota" in error_msg or "rate" in error_msg:
                    logger.warning(f"Rate limited (attempt {attempt + 1})")
                    await asyncio.sleep(RETRY_DELAY * (attempt + 1))
                elif "timeout" in error_msg:
                    logger.warning(f"API timeout (attempt {attempt + 1})")
                    await asyncio.sleep(RETRY_DELAY)
                elif isinstance(e, ValueError):
                    logger.warning(f"JSON parse failed (attempt {attempt + 1})")
                    if attempt < MAX_RETRIES:
                        await asyncio.sleep(RETRY_DELAY)
                else:
                    logger.error(f"API error (attempt {attempt + 1}): {e}")
                    if attempt < MAX_RETRIES:
                        await asyncio.sleep(RETRY_DELAY)

        logger.error(f"AI failed after {MAX_RETRIES + 1} attempts: {last_error}")
        raise ValueError(f"AI analysis failed: {last_error}. Raw: {raw_text[:300]}")

    def _call_gemini(self, system_prompt: str, user_content: str, max_tokens: int):
        """Synchronous Gemini API call (run via asyncio.to_thread)."""
        return self.client.models.generate_content(
            model=self.model,
            contents=f"{system_prompt}\n\n{user_content}",
            config={
                "max_output_tokens": max_tokens,
                "temperature": 0.3,
                "response_mime_type": "application/json",
            },
        )
