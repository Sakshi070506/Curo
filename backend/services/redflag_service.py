"""
Module   : Red-Flag Detector
Owner    : Conversation AI Engineer / ML Engineer
Purpose  : Classifies emergency symptoms mid-interview and produces the payload
           used to trigger a priority triage alert.

Design notes
------------
- Rule-based (AND-of-OR keyword groups) rather than a trained classifier, so it's
  auditable and fast to extend during the hackathon: a clinical advisor can add or
  edit a RedFlagRule without touching any ML pipeline.
- check_session_answers() checks the *concatenation* of all answers so far, so a
  rule can span two separate interview turns (e.g. "chest pain" in turn 1, "can't
  breathe" in turn 3).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, List


@dataclass
class RedFlagRule:
    id: str
    description: str
    # List of keyword groups. ALL groups must match (AND-of-groups); a group
    # matches if ANY of its keywords is present (OR-within-group).
    required_any: List[List[str]]
    severity: str  # "critical" | "high"

    def matches(self, text: str) -> bool:
        text_lower = text.lower()
        for group in self.required_any:
            if not any(re.search(rf"\b{re.escape(kw)}\b", text_lower) for kw in group):
                return False
        return True


RED_FLAG_RULES: List[RedFlagRule] = [
    RedFlagRule(
        id="acute_coronary_syndrome",
        description="Chest pain with breathlessness — possible cardiac event",
        required_any=[
            ["chest pain", "chest tightness", "chest pressure"],
            ["breathless", "dyspnoea", "dyspnea", "shortness of breath", "difficulty breathing", "can't breathe", "cant breathe"],
        ],
        severity="critical",
    ),
    RedFlagRule(
        id="stroke_fast",
        description="Sudden weakness/speech difficulty — possible stroke (FAST criteria)",
        required_any=[
            ["weakness", "numbness", "slurred speech", "facial droop", "one-sided", "one sided"],
        ],
        severity="critical",
    ),
    RedFlagRule(
        id="severe_headache",
        description="Sudden severe headache — possible intracranial event",
        required_any=[
            ["worst headache", "sudden severe headache", "thunderclap headache"],
        ],
        severity="critical",
    ),
    RedFlagRule(
        id="anaphylaxis",
        description="Allergic reaction with breathing/swelling — possible anaphylaxis",
        required_any=[
            ["allergic reaction", "throat swelling", "swelling of throat", "hives"],
            ["breathless", "difficulty breathing", "wheeze", "wheezing"],
        ],
        severity="critical",
    ),
    RedFlagRule(
        id="severe_bleeding",
        description="Uncontrolled or heavy bleeding",
        required_any=[
            ["heavy bleeding", "uncontrolled bleeding", "vomiting blood", "coughing blood", "blood in stool", "blood in vomit"],
        ],
        severity="critical",
    ),
    RedFlagRule(
        id="sepsis_meningitis_signs",
        description="High fever with confusion/lethargy — possible sepsis/meningitis",
        required_any=[
            ["high fever", "very high fever"],
            ["confusion", "lethargy", "unresponsive", "drowsy", "stiff neck"],
        ],
        severity="high",
    ),
    RedFlagRule(
        id="acute_abdomen",
        description="Sudden severe abdominal pain — possible surgical emergency",
        required_any=[
            ["severe abdominal pain", "worst stomach pain", "rigid abdomen"],
        ],
        severity="high",
    ),
]


_SEVERITY_ORDER = {"none": 0, "high": 1, "critical": 2}


@dataclass
class RedFlagResult:
    triggered: bool
    matched_rules: List[Dict[str, str]] = field(default_factory=list)
    highest_severity: str = "none"


class RedFlagDetector:
    def __init__(self, rules: Iterable[RedFlagRule] = RED_FLAG_RULES):
        self.rules = list(rules)

    def check(self, text: str) -> RedFlagResult:
        if not text or not text.strip():
            return RedFlagResult(triggered=False)

        matched: List[Dict[str, str]] = []
        highest = "none"
        for rule in self.rules:
            if rule.matches(text):
                matched.append({"id": rule.id, "description": rule.description, "severity": rule.severity})
                if _SEVERITY_ORDER[rule.severity] > _SEVERITY_ORDER[highest]:
                    highest = rule.severity

        return RedFlagResult(triggered=bool(matched), matched_rules=matched, highest_severity=highest)

    def check_session_answers(self, answers: List[str]) -> RedFlagResult:
        """Check the running interview transcript so a rule can span multiple turns."""
        combined = " . ".join(a for a in answers if a)
        return self.check(combined)


def build_triage_alert_payload(patient_id: str, session_id: str, red_flag: RedFlagResult) -> Dict:
    """Payload shape agreed in AGENTS.md §3 ('Red-flag event payload' contract,
    Conversation AI Engineer <-> Backend Engineer). Feed this straight into
    NotificationService.push_triage_alert(**payload) or POST /api/triage/alert."""
    return {
        "patient_id": patient_id,
        "session_id": session_id,
        "severity": red_flag.highest_severity,
        "matched_rules": red_flag.matched_rules,
        "requires_immediate_attention": red_flag.highest_severity == "critical",
    }


if __name__ == "__main__":
    detector = RedFlagDetector()
    result = detector.check("I have chest pain and I'm breathless since this morning")
    print(result)
    print(build_triage_alert_payload("p123", "s456", result))
