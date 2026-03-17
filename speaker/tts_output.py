"""
Veracore Voice Demo — The Good Neighbor Guard
Built by Christopher Hughes · Sacramento, CA
Created with the help of AI collaborators (Claude · GPT · Gemini · Groq)
Truth · Safety · We Got Your Back
"""

import os
import tempfile
import config

# ── Confidence floor thresholds (council spec) ────────────────────────────────
CONFIDENCE_HIGH     = 0.65   # speak normally
CONFIDENCE_MID_LOW  = 0.40   # speak with hedge
# below 0.40 → do not speak answer, hand to visual only

VISUAL_ANCHOR = "I've shown the full verification on screen."


def speak_with_confidence_floor(text: str, confidence: float,
                                 instruction_allowed: bool = True) -> bool:
    """
    Speak with confidence floor enforcement.
    Called by main.py queue delivery — replaces direct speak() for answers.

    Rules:
      confidence >= 0.65  → speak normally + visual anchor
      0.40 - 0.64         → hedge prefix + speak + visual anchor
      < 0.40              → do NOT speak answer — say "check the screen"
      instruction_allowed = False → completely silent
    """
    # Safety flag — Veracore said no
    if not instruction_allowed:
        print("[tts_output] instruction_allowed=False — staying silent.")
        return False

    if not text or not text.strip():
        print("[tts_output] No answer text — skipping.")
        return False

    if confidence < CONFIDENCE_MID_LOW:
        print(f"[tts_output] Confidence {confidence:.2f} below floor — visual only.")
        return speak("I want to show you this one. Check the verification on screen.")

    if confidence < CONFIDENCE_HIGH:
        print(f"[tts_output] Confidence {confidence:.2f} — hedged response.")
        hedged = f"I'm not fully certain, but — {text} {VISUAL_ANCHOR}"
        return speak(hedged)

    # Full confidence
    print(f"[tts_output] Confidence {confidence:.2f} — full response.")
    full = f"{text} {VISUAL_ANCHOR}"
    return speak(full)


# ── Original speak() — unchanged, used throughout the system ─────────────────

def speak(text: str) -> bool:
    if not text or not text.strip():
        print("[tts_output] No text to speak.")
        return False

    print(f"[tts_output] Speaking: {text}")

    if config.TTS_PROVIDER == "elevenlabs":
        return _speak_elevenlabs(text)
    elif config.TTS_PROVIDER == "openai":
        return _speak_openai(text)
    else:
        print(f"[tts_output] Unknown TTS provider: {config.TTS_PROVIDER}")
        return False


def _speak_openai(text: str) -> bool:
    try:
        from openai import OpenAI
        import pygame

        client = OpenAI(api_key=config.OPENAI_API_KEY)
        response = client.audio.speech.create(
            model="tts-1",
            voice="onyx",
            input=text
        )

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            tmp_path = f.name
            response.stream_to_file(tmp_path)

        pygame.mixer.init()
        pygame.mixer.music.load(tmp_path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        os.unlink(tmp_path)
        return True

    except Exception as e:
        print(f"[tts_output] OpenAI TTS error: {e}")
        return False


def _speak_elevenlabs(text: str) -> bool:
    try:
        import requests
        import pygame

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{config.ELEVENLABS_VOICE_ID}"
        headers = {
            "xi-api-key": config.ELEVENLABS_API_KEY,
            "Content-Type": "application/json"
        }
        payload = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {"stability": 0.6, "similarity_boost": 0.8}
        }

        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            tmp_path = f.name
            f.write(response.content)

        pygame.mixer.init()
        pygame.mixer.music.load(tmp_path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        os.unlink(tmp_path)
        return True

    except Exception as e:
        print(f"[tts_output] ElevenLabs TTS error: {e}")
        return False
