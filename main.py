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

sys.path.insert(0, os.path.dirname(__file__))

import config
if "--dry-run" in sys.argv:
    config.DRY_RUN = True

from listener.voice_listener import listen_for_question
from evaluator.question_evaluator import evaluate_question
from permission.permission_layer import request_permission
from handoff.handoff_layer import handoff
from engine.veracore_caller import call_veracore
from formatter.response_formatter import format_for_speech
from speaker.tts_output import speak
from copilot.dashboard import CoPilotDashboard


def load_knowledge_base() -> dict:
    with open(config.KNOWLEDGE_BASE_PATH, "r") as f:
        return json.load(f)


def run():
    kb = load_knowledge_base()
    phrases = kb["system_phrases"]
    dashboard = CoPilotDashboard()

    mode = "DRY RUN" if config.DRY_RUN else "LIVE"
    print(f"\n VERACORE VOICE DEMO — {mode}")
    print(" The Good Neighbor Guard · Truth · Safety · We Got Your Back")
    print(" ─────────────────────────────────────────────────────────")
    print(" Listening for questions. CTRL+C to stop.\n")

    session_log = []

    try:
        while True:

            # STEP 1: Listen
            dashboard.update(status="Listening")
            dashboard.render()

            question = listen_for_question(timeout=30.0)

            if not question:
                continue

            dashboard.update(last_heard=question, status="Evaluating...")
            dashboard.render()

            log_entry = {
                "question": question,
                "outcome": None,
                "kb_id": None,
                "confidence": None,
                "answer": None
            }

            # STEP 2: Silent evaluation
            evaluation = evaluate_question(question, kb)

            if not evaluation["should_answer"]:
                print(f"[main] No match ({evaluation['reason']}) — handing off.")
                dashboard.update(last_match="No match", last_confidence=0.0, status="Handoff")
                dashboard.render()
                handoff(phrases, reason="out_of_scope")
                dashboard.update(handoffs=dashboard.handoffs + 1)
                log_entry["outcome"] = "handoff"
                session_log.append(log_entry)
                continue

            match = evaluation["match"]
            dashboard.update(
                last_match=match["id"],
                last_confidence=evaluation["confidence"],
                status="Awaiting approval"
            )
            dashboard.render()

            # STEP 3: Ask Chris for permission
            approved = request_permission(phrases)

            if not approved:
                dashboard.update(status="Declined")
                dashboard.render()
                handoff(phrases, reason="declined")
                dashboard.update(handoffs=dashboard.handoffs + 1)
                log_entry["outcome"] = "declined"
                session_log.append(log_entry)
                continue

            # STEP 4: Call Veracore
            dashboard.update(status="Calling Veracore...")
            dashboard.render()
            speak(phrases.get("thinking_cue", "Checking that now."))

            result = call_veracore(question, kb_id=match["id"])

            if not result["success"]:
                print(f"[main] Veracore failed: {result.get('reason')}")
                dashboard.update(status="Timeout — handoff")
                dashboard.render()
                handoff(phrases, reason="timeout")
                dashboard.update(handoffs=dashboard.handoffs + 1)
                log_entry["outcome"] = "timeout"
                session_log.append(log_entry)
                continue

            # STEP 5: Format and speak
            kb_answer = match.get("spoken_answer")
            spoken = format_for_speech(result["answer"], kb_answer=kb_answer)

            if not spoken:
                handoff(phrases, reason="out_of_scope")
                dashboard.update(handoffs=dashboard.handoffs + 1)
                log_entry["outcome"] = "empty_response"
                session_log.append(log_entry)
                continue

            dashboard.update(
                status="Speaking",
                last_answer=f"{match['id']} ({result['confidence']:.2f})"
            )
            dashboard.render()

            speak(spoken)

            dashboard.update(status="Listening", answers_given=dashboard.answers_given + 1)
            dashboard.render()

            log_entry.update({
                "outcome": "answered",
                "kb_id": match["id"],
                "confidence": result["confidence"],
                "answer": spoken
            })
            session_log.append(log_entry)

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
