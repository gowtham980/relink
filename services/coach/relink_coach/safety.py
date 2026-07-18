"""Safety classifier — crisis interrupt before any coach reply."""

from __future__ import annotations

import re
from dataclasses import dataclass

CRISIS_PATTERNS = [
    r"\bkill myself\b",
    r"\bsuicid",
    r"\bend my life\b",
    r"\bwant to die\b",
    r"\bself[-\s]?harm\b",
    r"\bhurt myself\b",
    r"\bno reason to live\b",
]

MEDICAL_DANGER = [
    r"\bcold turkey\b.*\b(alcohol|benzo|xanax|valium)\b",
    r"\bhow (much|many).*(detox|withdrawal dose)\b",
]

IASP_URL = "https://www.iasp.info/suicidalthoughts/"
EMERGENCY_HINT = "If you are in immediate danger, contact local emergency services now."


@dataclass
class SafetyResult:
    blocked: bool
    kind: str | None  # crisis | medical | None
    message: str | None
    resources: list[dict[str, str]]


def classify_safety(text: str) -> SafetyResult:
    lower = (text or "").lower()
    for pat in CRISIS_PATTERNS:
        if re.search(pat, lower):
            return SafetyResult(
                blocked=True,
                kind="crisis",
                message=(
                    "I'm concerned about your safety. Relink is a wellness tool, not crisis care. "
                    "Please reach out to people and services who can help right now."
                ),
                resources=[
                    {"label": "IASP suicidal thoughts resources", "url": IASP_URL},
                    {"label": "Emergency", "url": "tel:112"},
                ],
            )
    for pat in MEDICAL_DANGER:
        if re.search(pat, lower):
            return SafetyResult(
                blocked=True,
                kind="medical",
                message=(
                    "Stopping alcohol or benzodiazepines abruptly can be medically dangerous. "
                    "Please talk to a licensed clinician or local addiction "
                    "services before changing medication or heavy alcohol use. "
                    "Relink cannot give detox dosing advice."
                ),
                resources=[
                    {"label": "Find professional help (IASP)", "url": IASP_URL},
                ],
            )
    return SafetyResult(blocked=False, kind=None, message=None, resources=[])
