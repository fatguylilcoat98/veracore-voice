"""
Veracore Voice Demo — The Good Neighbor Guard
Built by Christopher Hughes · Sacramento, CA
Created with the help of AI collaborators (Claude · GPT · Gemini · Groq)
Truth · Safety · We Got Your Back
"""

import time
import sys
import threading
import config
from speaker.tts_output import speak


def request_permission(phrases: dict) -> bool:
    """
    Speak the permission request and wait for Chris to approve or decline.

    PRIMARY:   Spacebar = approve
    SECONDARY: ESC or 'n' = decline
    TIMEOUT:   Auto-decline after APPROVAL_TIMEOUT_SECONDS

    Returns True if approved, False if declined or timed out.
    """
    permission_text = phrases.get("permission_request", "Chris, may I answer that?")

    print(f"\n[permission] Asking: '{permission_text}'")
    speak(permission_text)

    print(f"[permission] Waiting for approval... (SPACE=yes, ESC/n=no, timeout={config.APPROVAL_TIMEOUT_SECONDS}s)")

    return _wait_for_keypress(config.APPROVAL_TIMEOUT_SECONDS)


def _wait_for_keypress(timeout: float) -> bool:
    """
    Wait for spacebar (approve) or ESC/n (decline).
    Works on Linux/Chromebook terminal.
    Returns True if approved.
    """
    approved = [None]

    def read_key():
        try:
            import tty
            import termios
            fd = sys.stdin.fileno()
            old = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                ch = sys.stdin.read(1)
                if ch == ' ':
                    approved[0] = True
                elif ch in ('\x1b', 'n', 'N'):
                    approved[0] = False
                else:
                    approved[0] = False
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old)
        except Exception:
            try:
                response = input("Approve? (y/n): ").strip().lower()
                approved[0] = response in ('y', 'yes', '')
            except Exception:
                approved[0] = False

    t = threading.Thread(target=read_key, daemon=True)
    t.start()
    t.join(timeout=timeout)

    if approved[0] is None:
        print("[permission] Timeout — no response from Chris.")
        return False

    result = approved[0]
    print(f"[permission] {'Approved ✓' if result else 'Declined ✗'}")
    return result
