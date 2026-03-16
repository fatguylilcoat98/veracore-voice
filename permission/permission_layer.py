# FILE: permission/permission_layer.py
"""
Veracore Voice Demo — The Good Neighbor Guard
Built by Christopher Hughes · Sacramento, CA
Created with the help of AI collaborators (Claude · GPT · Gemini · Groq)
Truth · Safety · We Got Your Back
"""

import sys
import threading
import config
from speaker.tts_output import speak

APPROVE_WORDS = {"yes", "yeah", "yep", "sure", "go ahead", "go", "okay", "ok", "do it", "answer"}
DECLINE_WORDS = {"no", "nope", "stop", "skip", "pass", "decline"}


def request_permission(phrases: dict) -> bool:
    """
    Speak the permission request then listen for:
    - Voice approval (yes / sure / go ahead etc.)
    - Voice decline (no / stop / skip etc.)
    - Spacebar = approve (silent backup)
    - ESC = decline (silent backup)
    - Timeout = auto decline
    """
    permission_text = phrases.get("permission_request", "Chris, may I answer that?")
    print(f"\n[permission] Asking: '{permission_text}'")
    speak(permission_text)
    print(f"[permission] Listening for approval... (say yes/no, or SPACE=yes, ESC=no, timeout={config.APPROVAL_TIMEOUT_SECONDS}s)")

    result = [None]
    stop_event = threading.Event()

    # Thread 1: Listen for voice response
    def voice_listener():
        try:
            import sounddevice as sd
            import numpy as np
            from groq import Groq
            import io
            import wave

            client = Groq(api_key=config.GROQ_API_KEY)
            sample_rate = 16000
            duration = config.APPROVAL_TIMEOUT_SECONDS
            chunk_samples = int(sample_rate * duration)

            recording = sd.rec(chunk_samples, samplerate=sample_rate,
                               channels=1, dtype='int16')
            sd.wait()

            if stop_event.is_set():
                return

            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes(recording.tobytes())
            wav_buffer.seek(0)
            wav_buffer.name = "approval.wav"

            transcription = client.audio.transcriptions.create(
                model="whisper-large-v3",
                file=wav_buffer,
                language="en"
            )

            heard = transcription.text.strip().lower()
            print(f"[permission] Heard response: '{heard}'")

            if stop_event.is_set():
                return

            if any(word in heard for word in APPROVE_WORDS):
                result[0] = True
                stop_event.set()
            elif any(word in heard for word in DECLINE_WORDS):
                result[0] = False
                stop_event.set()

        except Exception as e:
            print(f"[permission] Voice listener error: {e}")

    # Thread 2: Listen for keypress backup
    def key_listener():
        try:
            import tty
            import termios
            fd = sys.stdin.fileno()
            old = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                while not stop_event.is_set():
                    import select
                    r, _, _ = select.select([sys.stdin], [], [], 0.1)
                    if r:
                        ch = sys.stdin.read(1)
                        if ch == ' ':
                            result[0] = True
                            stop_event.set()
                            break
                        elif ch in ('\x1b', 'n', 'N'):
                            result[0] = False
                            stop_event.set()
                            break
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old)
        except Exception as e:
            print(f"[permission] Key listener error: {e}")

    # Start both threads
    if config.DRY_RUN:
        # In dry run just use keyboard
        try:
            response = input("Approve? (y/n): ").strip().lower()
            return response in ('y', 'yes', 'sure', 'go ahead', '')
        except Exception:
            return False

    vt = threading.Thread(target=voice_listener, daemon=True)
    kt = threading.Thread(target=key_listener, daemon=True)
    vt.start()
    kt.start()

    stop_event.wait(timeout=config.APPROVAL_TIMEOUT_SECONDS)
    stop_event.set()

    if result[0] is None:
        print("[permission] Timeout — no response from Chris.")
        return False

    approved = result[0]
    print(f"[permission] {'Approved ✓' if approved else 'Declined ✗'}")
    return approved
