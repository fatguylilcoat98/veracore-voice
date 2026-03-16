"""
Veracore Voice Demo — The Good Neighbor Guard
Built by Christopher Hughes · Sacramento, CA
Created with the help of AI collaborators (Claude · GPT · Gemini · Groq)
Truth · Safety · We Got Your Back
"""

import os
import datetime


class CoPilotDashboard:
    """
    Hidden co-pilot dashboard for Chris only.
    Shows system status, last heard question,
    KB match, confidence, and answer/handoff counts.
    Renders in terminal — no browser needed.
    """

    def __init__(self):
        self.status = "Listening"
        self.last_heard = "—"
        self.last_match = "—"
        self.last_confidence = 0.0
        self.answers_given = 0
        self.handoffs = 0
        self.last_answer = "—"

    def update(self, **kwargs):
        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)

    def render(self):
        os.system('clear')
        now = datetime.datetime.now().strftime("%I:%M:%S %p")
        conf = f"{self.last_confidence:.2f}" if self.last_confidence else "—"

        print("╔══════════════════════════════════════════════╗")
        print("║     VERACORE DEMO  ●  CO-PILOT VIEW          ║")
        print(f"║     {now:<41}║")
        print("╠══════════════════════════════════════════════╣")
        print(f"║  HEARD:                                      ║")
        heard = self.last_heard[:44] if self.last_heard else "—"
        print(f"║  {heard:<44}║")
        print("╠══════════════════════════════════════════════╣")
        print(f"║  MATCH:       {str(self.last_match):<31}║")
        print(f"║  CONFIDENCE:  {conf:<31}║")
        print(f"║  STATUS:      {str(self.status):<31}║")
        print("╠══════════════════════════════════════════════╣")
        print("║  [ SPACE = APPROVE ]   [ ESC = DECLINE ]     ║")
        print("╠══════════════════════════════════════════════╣")
        print(f"║  ANSWERS GIVEN: {self.answers_given:<5}  HANDOFFS: {self.handoffs:<13}║")
        print("╚══════════════════════════════════════════════╝")
        print()
        print("  Press CTRL+C to stop the demo.")
