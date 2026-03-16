"""
Veracore Voice Demo — The Good Neighbor Guard
Built by Christopher Hughes · Sacramento, CA
Created with the help of AI collaborators (Claude · GPT · Gemini · Groq)
Truth · Safety · We Got Your Back
"""

import requests
import json
import config

# ── Mock responses for dry run mode ──────────────────────────────────────────
MOCK_RESPONSES = {
    "kb_001": "Every answer passes through multiple AI models that check each other. If they disagree, confidence drops and I say so. I don't guess. I verify.",
    "kb_002": "Most AI gives one answer from one model. I challenge my own answer before speaking. That's the difference between a response and a verified response.",
    "kb_003": "I use a confidence score. If models agree and evidence is strong, confidence is high. If they disagree, I flag the uncertainty.",
    "kb_004": "I have an adversarial layer — a model whose job is to find flaws in my answer before it reaches you. I argue with myself first.",
    "kb_005": "When models disagree, I don't pick a winner. Confidence drops, I flag the uncertainty, and I hand it back to Chris.",
    "default": "I've processed that question. The evidence is being weighed across multiple models before I give you a verified answer."
}


def call_veracore(question: str, kb_id: str = None) -> dict:
    """
    Send a question to the existing Veracore engine.
    Returns a dict with 'answer' and 'confidence'.
    Falls back to mock response in dry run mode.
    """
    if config.DRY_RUN:
        return _mock_response(kb_id)

    try:
        response = requests.post(
            f"{config.VERACORE_API_URL}/ask",
            json={"question": question},
            timeout=config.VERACORE_TIMEOUT_SECONDS
        )
        response.raise_for_status()
        data = response.json()

        return {
            "answer": data.get("answer", ""),
            "confidence": data.get("confidence", 0.0),
            "sources": data.get("sources", []),
            "success": True
        }

    except requests.Timeout:
        print("[veracore_caller] Timeout — Veracore did not respond in time.")
        return {"answer": "", "confidence": 0.0, "sources": [], "success": False, "reason": "timeout"}

    except requests.RequestException as e:
        print(f"[veracore_caller] Request error: {e}")
        return {"answer": "", "confidence": 0.0, "sources": [], "success": False, "reason": str(e)}


def _mock_response(kb_id: str = None) -> dict:
    """Return a prepared mock response for dry run testing."""
    answer = MOCK_RESPONSES.get(kb_id, MOCK_RESPONSES["default"])
    return {
        "answer": answer,
        "confidence": 0.82,
        "sources": ["mock"],
        "success": True
    }
