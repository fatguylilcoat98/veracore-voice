"""
Veracore Voice Demo — The Good Neighbor Guard
Built by Christopher Hughes · Sacramento, CA
Created with the help of AI collaborators (Claude · GPT · Gemini · Groq)
Truth · Safety · We Got Your Back
"""

import os

# ── Mode Flags ────────────────────────────────────────────────────────────────
DRY_RUN = False          # True = mock Veracore responses, no live API calls
DEMO_MODE = True         # True = restrict to prepared Q&A scope only
LOG_SESSION = True       # True = write session_log.json after each run

# ── API Keys (set in environment) ─────────────────────────────────────────────
VERACORE_API_URL    = os.getenv("VERACORE_API_URL", "https://veracore.onrender.com")
ELEVENLABS_API_KEY  = os.getenv("ELEVENLABS_API_KEY", "")
OPENAI_API_KEY      = os.getenv("OPENAI_API_KEY", "")
GROQ_API_KEY        = os.getenv("GROQ_API_KEY", "")

# ── TTS Provider: "elevenlabs" | "openai" ─────────────────────────────────────
TTS_PROVIDER        = "openai"
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "")

# ── Timing ────────────────────────────────────────────────────────────────────
APPROVAL_TIMEOUT_SECONDS  = 8     # How long to wait for Chris to approve
VERACORE_TIMEOUT_SECONDS  = 12    # How long to wait for Veracore response
STT_SILENCE_THRESHOLD     = 1.5   # Seconds of silence before question is complete

# ── Evaluation Thresholds ─────────────────────────────────────────────────────
CONFIDENCE_THRESHOLD      = 0.70  # Minimum confidence to offer an answer
KEYWORD_MATCH_MINIMUM     = 2     # Minimum keyword matches to consider a question in-scope

# ── Response Formatting ───────────────────────────────────────────────────────
MAX_SPOKEN_SENTENCES      = 3     # Strip answers to this many sentences

# ── Paths ─────────────────────────────────────────────────────────────────────
KNOWLEDGE_BASE_PATH = "knowledge_base.json"
SESSION_LOG_PATH    = "logs/session_log.json"
