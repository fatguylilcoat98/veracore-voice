"""
Veracore Voice Demo — The Good Neighbor Guard
Built by Christopher Hughes · Sacramento, CA
Created with the help of AI collaborators (Claude · GPT · Gemini · Groq)
Truth · Safety · We Got Your Back
"""

from speaker.tts_output import speak

# ── Trigger phrases Chris says to deliver the next queued answer ──────────────
DELIVERY_TRIGGERS = [
    "go ahead",
    "veracore go",
    "answer that",
    "next question",
    "veracore answer"
]


def is_delivery_trigger(transcript: str) -> bool:
    """
    Returns True if the transcript is a host delivery command.
    These phrases tell Veracore to speak the next queued answer.
    """
    lower = transcript.lower().strip()
    return any(trigger in lower for trigger in DELIVERY_TRIGGERS)


def handoff(phrases: dict, reason: str = "out_of_scope") -> None:
    """
    Gracefully hand the question back to Chris.
    Speaks a natural handoff phrase so the audience
    sees the system showing judgment, not breaking.
    """
    if reason == "timeout":
        phrase = phrases.get("timeout_response",
                             "Still verifying. Chris, do you want to take that one?")
    elif reason == "declined":
        # Chris said no — stay silent, no spoken response needed
        print("[handoff] Chris declined. Returning to listening.")
        return
    else:
        phrase = phrases.get("handoff",
                             "Chris, that's a good question. I think it would be best for you to answer that one.")

    print(f"[handoff] Speaking handoff: '{phrase}'")
    speak(phrase)
