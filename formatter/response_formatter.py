# FILE: formatter/response_formatter.py
"""
Veracore Voice Demo — The Good Neighbor Guard
Built by Christopher Hughes · Sacramento, CA
Created with the help of AI collaborators (Claude · GPT · Gemini · Groq)
Truth · Safety · We Got Your Back
"""

import re
import config


def format_for_speech(text: str, kb_answer: str = None) -> str:
    """
    Prepare a Veracore answer for spoken delivery.

    Priority order:
    1. If a prepared KB answer exists, use it — it's already speech-optimized.
    2. Otherwise strip the live Veracore response to MAX_SPOKEN_SENTENCES.

    Returns a clean string ready for TTS.
    """
    if kb_answer and kb_answer.strip():
        return kb_answer.strip()

    if not text or not text.strip():
        return ""

    sentences = _split_sentences(text)
    trimmed = sentences[:config.MAX_SPOKEN_SENTENCES]
    result = " ".join(trimmed).strip()
    result = _clean_for_speech(result)
    return result


def _split_sentences(text: str) -> list:
    """Split text into sentences."""
    raw = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in raw if s.strip()]


def _clean_for_speech(text: str) -> str:
    """
    Remove markdown, symbols, and anything that sounds
    wrong when read aloud by a TTS engine.
    """
    text = re.sub(r'\*+', '', text)
    text = re.sub(r'#+\s*', '', text)
    text = re.sub(r'\[.*?\]\(.*?\)', '', text)
    text = re.sub(r'`+', '', text)
    text = re.sub(r'\s{2,}', ' ', text)
    return text.strip()
