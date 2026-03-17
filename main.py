"""
Veracore Voice Demo — The Good Neighbor Guard
Built by Christopher Hughes · Sacramento, CA
Created with the help of AI collaborators (Claude · GPT · Gemini · Groq)
Truth · Safety · We Got Your Back

Usage:
  python main.py              # Live mode
  python main.py --dry-run    # Test mode (keyboard input, no live API calls)
"""

import sys
import json
import os
import time
import threading
from collections import deque

sys.path.insert(0, os.path.dirname(__file__))

import config
if "--dry-run" in sys.argv:
    config.DRY_RUN = True

from listener.voice_listener import listen_for_question, listen_continuous
from evaluator.question_evaluator import evaluate_question
from permission.permission_layer import request_permission
from handoff.handoff_layer import handoff, is_delivery_trigger
from engine.veracore_caller import call_veracore
from formatter.response_formatter import format_for_speech
from speaker.tts_output import speak, speak_with_confidence_floor
from copilot.dashboard import CoPilotDashboard


# ── Queue states ──────────────────────────────────────────────────────────────
DETECTED    = "DETECTED"
PROCESSING  = "PROCESSING"
READY       = "READY"
DELIVERED   = "DELIVERED"
FAILED      = "FAILED"

# ── Global question queue ─────────────────────────────────────────────────────
question_queue = deque(maxlen=5)
queue_lock = threading.Lock()


def load_knowledge_base() -> dict:
    with open(config.KNOWLEDGE_BASE_PATH, "r") as f:
        return json.load(f)


def _preprocess_question(entry: dict, kb: dict):
    """
    Background thread: evaluates and calls Veracore as soon as a question
    is detected. Answer sits READY in the queue before Chris approves.
    """
    question = entry["question"]
    entry["status"] = PROCESSING

    evaluation = evaluate_question(question, kb)
    entry["evaluation"] = evaluation

    if not evaluation["should_answer"]:
        entry["status"] = FAILED
        entry["reason"] = "no_match"
        print(f"[queue] #{entry['id']} no match — marked FAILED.")
        return

    match = evaluation["match"]
    result = call_veracore(question, kb_id=match["id"])

    if not result["success"]:
        entry["status"] = FAILED
        entry["reason"] = result.get("reason", "unknown")
        print(f"[queue] #{entry['id']} Veracore failed — marked FAILED.")
        return

    kb_answer = match.get("spoken_answer")
    spoken = format_for_speech(result["answer"], kb_answer=kb_answer)

    entry["result"]     = result
    entry["match"]      = match
    entry["spoken"]     = spoken
    entry["confidence"] = result["confidence"]
    entry["status"]     = READY
    print(f"[queue] #{entry['id']} READY. Confidence: {result['confidence']:.2f}")


def _add_to_queue(question: str, kb: dict) -> dict:
    """Add a question to the queue and fire background pre-processing."""
    with queue_lock:
        entry_id = f"q{int(time.time() * 1000) % 100000}"
        entry = {
            "id":         entry_id,
            "question":   question,
            "status":     DETECTED,
            "evaluation": None,
            "match":      None,
            "result":     None,
            "spoken":     None,
            "confidence": None,
            "reason":     None
        }
        question_queue.append(entry)

    # Fire preprocessing in background — don't block the listener
    t = threading.Thread(target=_preprocess_question, args=(entry, kb), daemon=True)
    t.start()

    print(f"[queue] Added #{entry_id}: {question[:60]}")
    return entry


def _deliver_next(phrases: dict, dashboard: "CoPilotDashboard", session_log: list):
    """Deliver the next READY item from the queue."""
    with queue_lock:
        ready = next((e for e in question_queue if e["status"] == READY), None)
        processing = next((e for e in question_queue if e["status"] == PROCESSING), None)

    if not ready:
        if processing:
            speak(phrases.get("still_verifying", "Still verifying — give me one more second."))
        else:
            speak(phrases.get("queue_empty", "No questions are queued right now."))
        return

    # Mark delivered
    ready["status"] = DELIVERED

    confidence = ready["confidence"] or 0.0
    spoken = ready["spoken"]

    dashboard.update(
        status="Speaking",
        last_answer=f"{ready['match']['id']} ({confidence:.2f})"
    )
    dashboard.render()

    # Confidence floor enforced in speak_with_confidence_floor
    speak_with_confidence_floor(spoken, confidence)

    dashboard.update(status="Listening", answers_given=dashboard.answers_given + 1)
    dashboard.render()

    session_log.append({
        "question":   ready["question"],
        "outcome":    "answered",
        "kb_id":      ready["match"]["id"],
        "confidence": confidence,
        "answer":     spoken
    })

    # Clean delivered items
    with queue_lock:
        delivered = [e for e in question_queue if e["status"] == DELIVERED]
        for e in delivered:
            question_queue.remove(e)


def run():
    kb = load_knowledge_base()
    phrases = kb["system_phrases"]
    dashboard = CoPilotDashboard()

    mode = "DRY RUN" if config.DRY_RUN else "LIVE"
    print(f"\n VERACORE VOICE DEMO — {mode}")
    print(" The Good Neighbor Guard · Truth · Safety · We Got Your Back")
    print(" ─────────────────────────────────────────────────────────")
    print(" Always listening. Say 'go ahead' to deliver next answer.")
    print(" CTRL+C to stop.\n")

    session_log = []

    # Pre-load birthday opener 
    birthday_question = "Can you help Chris convince everyone he is still in his 30s?"
    print("[main] Pre-loading birthday opener...")
    _add_to_queue(birthday_question, kb)

    try:
        while True:
            dashboard.update(status="Listening")
            dashboard.render()

            # Listen — now returns on silence detection automatically
            question = listen_for_question(timeout=30.0)

            if not question:
                continue

            print(f"[main] Heard: {question}")
            dashboard.update(last_heard=question, status="Detected — pre-processing")
            dashboard.render()

            # Check if this is a delivery trigger phrase
            if is_delivery_trigger(question):
                print("[main] Delivery trigger detected.")
                _deliver_next(phrases, dashboard, session_log)
                continue

            # Check for birthday opener trigger
            if any(t in question.lower() for t in ["30s", "still in your 30", "convince everyone"]):
                print("[main] Birthday opener triggered.")
                with queue_lock:
                    birthday = next(
                        (e for e in question_queue
                         if "30s" in e["question"] and e["status"] == READY),
                        None
                    )
                if birthday:
                    birthday["status"] = DELIVERED
                    speak_with_confidence_floor(birthday["spoken"], birthday["confidence"])
                else:
                    # Hardcoded fallback — birthday moment never fails
                    speak("Chris… I ran verification on that claim. Confidence score: extremely low.")
                continue

            # Add to queue — Veracore starts processing immediately in background
            _add_to_queue(question, kb)

            # Update dashboard with queue depth
            with queue_lock:
                q_count = len([e for e in question_queue if e["status"] in [DETECTED, PROCESSING, READY]])
            dashboard.update(status=f"Listening — {q_count} queued")
            dashboard.render()

    except KeyboardInterrupt:
        print("\n\n[main] Demo stopped.")
        _save_log(session_log)
        print(f"[main] Session log saved to {config.SESSION_LOG_PATH}")
        print(f"[main] Answers given: {dashboard.answers_given}  |  Handoffs: {dashboard.handoffs}")
        print("\n Good luck out there, Chris. Truth · Safety · We Got Your Back.\n")


def _save_log(log: list):
    import datetime
    os.makedirs("logs", exist_ok=True)
    entry = {
        "session_date": datetime.datetime.now().isoformat(),
        "events": log
    }
    try:
        with open(config.SESSION_LOG_PATH, "w") as f:
            json.dump(entry, f, indent=2)
    except Exception as e:
        print(f"[main] Could not save log: {e}")


if __name__ == "__main__":
    run()
