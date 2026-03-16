"""
Veracore Voice Demo — The Good Neighbor Guard
Built by Christopher Hughes · Sacramento, CA
Created with the help of AI collaborators (Claude · GPT · Gemini · Groq)
Truth · Safety · We Got Your Back
"""

import config


def evaluate_question(question: str, kb: dict) -> dict:
    if not question or not question.strip():
        return _no_answer("empty question")

    q_lower = question.lower().strip()

    if len(q_lower.split()) < 3:
        return _no_answer("too short")

    match = _find_kb_match(q_lower, kb)

    if match:
        return {
            "should_answer": True,
            "match": match,
            "confidence": match["confidence_floor"],
            "reason": f"kb_match:{match['id']}"
        }

    return _no_answer("no kb match")


def _find_kb_match(q_lower: str, kb: dict) -> dict | None:
    best_match = None
    best_score = 0

    for entry in kb["entries"]:
        score = sum(1 for kw in entry["keywords"] if kw.lower() in q_lower)
        if score >= config.KEYWORD_MATCH_MINIMUM and score > best_score:
            best_score = score
            best_match = entry

    return best_match


def _no_answer(reason: str) -> dict:
    return {
        "should_answer": False,
        "match": None,
        "confidence": 0.0,
        "reason": reason
    }
