"""
Module   : Dialogue Manager
Owner    : Conversation AI Engineer
Purpose  : Drives the adaptive clinical interview (voice/touch), branching on
           chief complaint (SOCRATES) and running a red-flag check every turn.

State machine (docs/module-A-conversation-engine.md):
START -> LANGUAGE_SELECTED -> CONSENT_GRANTED -> CHIEF_COMPLAINT
      -> HPI_LOOP (SOCRATES) -> PAST_HISTORY -> DRUG_ALLERGY_HISTORY
      -> FAMILY_HISTORY -> PERSONAL_HISTORY -> ROS
      -> (AYUSH_MODE ? DASHAVIDHA_PARIKSHA : skip) -> COMPLETE

Note on imports: uses a relative-then-flat fallback so this file works both as
part of the `services` package (backend/services/dialogue_manager.py, imported
via `from .redflag_service import ...`) and as a standalone script sitting next
to redflag_service.py on sys.path (imported via `from redflag_service import ...`).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

try:
    from .redflag_service import RedFlagDetector, RedFlagResult
except ImportError:  # running as a flat script / standalone module
    from redflag_service import RedFlagDetector, RedFlagResult  # type: ignore


class SessionState(str, Enum):
    START = "START"
    LANGUAGE_SELECTED = "LANGUAGE_SELECTED"
    CONSENT_GRANTED = "CONSENT_GRANTED"
    CHIEF_COMPLAINT = "CHIEF_COMPLAINT"
    HPI_LOOP = "HPI_LOOP"
    PAST_HISTORY = "PAST_HISTORY"
    DRUG_ALLERGY_HISTORY = "DRUG_ALLERGY_HISTORY"
    FAMILY_HISTORY = "FAMILY_HISTORY"
    PERSONAL_HISTORY = "PERSONAL_HISTORY"
    ROS = "ROS"
    DASHAVIDHA_PARIKSHA = "DASHAVIDHA_PARIKSHA"
    COMPLETE = "COMPLETE"


SOCRATES_QUESTIONS = [
    ("site", "Where exactly do you feel it?"),
    ("onset", "When did it start, and did it come on suddenly or gradually?"),
    ("character", "How would you describe it (sharp, dull, burning, cramping)?"),
    ("radiation", "Does it spread anywhere else?"),
    ("associated_symptoms", "Are you having any other symptoms along with this?"),
    ("timing", "Is it constant, or does it come and go?"),
    ("exacerbating_relieving", "Does anything make it better or worse?"),
    ("severity", "On a scale of 1 to 10, how severe is it?"),
]

DASHAVIDHA_PARIKSHA_QUESTIONS = [
    ("prakriti", "What is your natural body constitution — do you tend to run hot, cold, light, or heavy?"),
    ("vikriti", "How would you describe your current imbalance compared to your usual self?"),
    ("sara", "How would you describe the quality of your tissues/strength overall?"),
    ("samhanana", "How would you describe your body's compactness/build?"),
    ("pramana", "Any comments on your body proportions/measurements?"),
    ("satmya", "What foods/climates suit you best?"),
    ("sattva", "How would you describe your mental strength/resilience?"),
    ("ahara_shakti", "How is your digestive capacity/appetite?"),
    ("vyayama_shakti", "How much physical exertion can you comfortably tolerate?"),
    ("vaya", "What is your age group/life-stage?"),
    ("ahara_vihara", "Tell me about your typical diet and daily routine."),
]

ROS_SYSTEMS = ["cardiovascular", "respiratory", "gastrointestinal", "neurological", "musculoskeletal", "genitourinary"]

PAST_HISTORY_PROMPT = "Have you had any major illnesses, surgeries, or hospital admissions in the past?"
DRUG_ALLERGY_PROMPT = "Are you currently taking any medications, and do you have any known allergies?"
FAMILY_HISTORY_PROMPT = "Does anyone in your immediate family have any major medical conditions?"
PERSONAL_HISTORY_PROMPT = "Could you tell me about your lifestyle — smoking, alcohol, diet, occupation?"


@dataclass
class Question:
    question_id: str
    prompt: str
    state: SessionState


@dataclass
class HistorySession:
    session_id: str
    language: str
    ayush_mode: bool = False
    state: SessionState = SessionState.START
    chief_complaint: str = ""
    hpi: Dict[str, str] = field(default_factory=dict)
    past_medical_history: List[str] = field(default_factory=list)
    drug_allergy_history: List[str] = field(default_factory=list)
    family_history: List[str] = field(default_factory=list)
    personal_history: Dict[str, str] = field(default_factory=dict)
    review_of_systems: Dict[str, str] = field(default_factory=dict)
    ayush: Dict[str, str] = field(default_factory=dict)
    red_flags_triggered: List[Dict] = field(default_factory=list)
    _socrates_idx: int = 0
    _ros_idx: int = 0
    _dashavidha_idx: int = 0
    _raw_answers: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Data contract consumed by Module C (Summary Generator) — see
        docs/module-A-conversation-engine.md."""
        return {
            "session_id": self.session_id,
            "language": self.language,
            "chief_complaint": self.chief_complaint,
            "hpi": self.hpi,
            "past_medical_history": self.past_medical_history,
            "drug_allergy_history": self.drug_allergy_history,
            "family_history": self.family_history,
            "personal_history": self.personal_history,
            "review_of_systems": self.review_of_systems,
            "ayush": self.ayush if self.ayush_mode else {},
            "red_flags_triggered": self.red_flags_triggered,
            "state": self.state.value,
        }


class DialogueManager:
    """In-memory session store for local dev/tests. In the full backend this
    would persist via backend/database/models.py (a HistorySession table) instead
    of a plain dict, so a patient can resume after stepping away (e.g. to scan
    documents in Module B) — swap `self.sessions` for a DB-backed repository."""

    def __init__(self, redflag_detector: Optional[RedFlagDetector] = None):
        self.sessions: Dict[str, HistorySession] = {}
        self.redflag_detector = redflag_detector or RedFlagDetector()

    # ---- session lifecycle -------------------------------------------------
    def start_session(self, language: str, ayush_mode: bool = False) -> Dict:
        session_id = str(uuid.uuid4())
        session = HistorySession(
            session_id=session_id,
            language=language,
            ayush_mode=ayush_mode,
            state=SessionState.CHIEF_COMPLAINT,
        )
        self.sessions[session_id] = session
        question = Question("chief_complaint", "What brings you in today?", SessionState.CHIEF_COMPLAINT)
        return {"session_id": session_id, "next_question": question.__dict__}

    def get_session(self, session_id: str) -> HistorySession:
        if session_id not in self.sessions:
            raise KeyError(f"Unknown session_id: {session_id}")
        return self.sessions[session_id]

    # ---- core turn handler ---------------------------------------------------
    def submit_answer(self, session_id: str, question_id: str, answer_text: str) -> Dict:
        session = self.get_session(session_id)
        if session.state == SessionState.COMPLETE:
            raise ValueError(f"Session {session_id} is already complete")

        session._raw_answers.append(answer_text)

        redflag_result: RedFlagResult = self.redflag_detector.check_session_answers(session._raw_answers)
        if redflag_result.triggered:
            for rule in redflag_result.matched_rules:
                if rule not in session.red_flags_triggered:
                    session.red_flags_triggered.append(rule)

        self._record_answer(session, question_id, answer_text)
        next_question = self._advance(session)

        return {
            "session_id": session_id,
            "state": session.state.value,
            "red_flag": {
                "triggered": redflag_result.triggered,
                "severity": redflag_result.highest_severity,
                "matched_rules": redflag_result.matched_rules,
            },
            "next_question": next_question.__dict__ if next_question else None,
            "complete": session.state == SessionState.COMPLETE,
        }

    # ---- internal state machine ----------------------------------------------
    def _record_answer(self, session: HistorySession, question_id: str, answer_text: str) -> None:
        if session.state == SessionState.CHIEF_COMPLAINT:
            session.chief_complaint = answer_text
        elif session.state == SessionState.HPI_LOOP:
            session.hpi[question_id] = answer_text
        elif session.state == SessionState.PAST_HISTORY:
            session.past_medical_history.append(answer_text)
        elif session.state == SessionState.DRUG_ALLERGY_HISTORY:
            session.drug_allergy_history.append(answer_text)
        elif session.state == SessionState.FAMILY_HISTORY:
            session.family_history.append(answer_text)
        elif session.state == SessionState.PERSONAL_HISTORY:
            session.personal_history[question_id] = answer_text
        elif session.state == SessionState.ROS:
            session.review_of_systems[question_id] = answer_text
        elif session.state == SessionState.DASHAVIDHA_PARIKSHA:
            session.ayush[question_id] = answer_text

    def _advance(self, session: HistorySession) -> Optional[Question]:
        if session.state == SessionState.CHIEF_COMPLAINT:
            session.state = SessionState.HPI_LOOP
            session._socrates_idx = 0
            return self._next_socrates_question(session)

        if session.state == SessionState.HPI_LOOP:
            question = self._next_socrates_question(session)
            if question:
                return question
            session.state = SessionState.PAST_HISTORY
            return Question("past_history", PAST_HISTORY_PROMPT, session.state)

        if session.state == SessionState.PAST_HISTORY:
            session.state = SessionState.DRUG_ALLERGY_HISTORY
            return Question("drug_allergy_history", DRUG_ALLERGY_PROMPT, session.state)

        if session.state == SessionState.DRUG_ALLERGY_HISTORY:
            session.state = SessionState.FAMILY_HISTORY
            return Question("family_history", FAMILY_HISTORY_PROMPT, session.state)

        if session.state == SessionState.FAMILY_HISTORY:
            session.state = SessionState.PERSONAL_HISTORY
            return Question("personal_history", PERSONAL_HISTORY_PROMPT, session.state)

        if session.state == SessionState.PERSONAL_HISTORY:
            session.state = SessionState.ROS
            session._ros_idx = 0
            return self._next_ros_question(session)

        if session.state == SessionState.ROS:
            question = self._next_ros_question(session)
            if question:
                return question
            if session.ayush_mode:
                session.state = SessionState.DASHAVIDHA_PARIKSHA
                session._dashavidha_idx = 0
                return self._next_dashavidha_question(session)
            session.state = SessionState.COMPLETE
            return None

        if session.state == SessionState.DASHAVIDHA_PARIKSHA:
            question = self._next_dashavidha_question(session)
            if question:
                return question
            session.state = SessionState.COMPLETE
            return None

        return None

    def _next_socrates_question(self, session: HistorySession) -> Optional[Question]:
        if session._socrates_idx >= len(SOCRATES_QUESTIONS):
            return None
        qid, prompt = SOCRATES_QUESTIONS[session._socrates_idx]
        session._socrates_idx += 1
        return Question(qid, prompt, SessionState.HPI_LOOP)

    def _next_ros_question(self, session: HistorySession) -> Optional[Question]:
        if session._ros_idx >= len(ROS_SYSTEMS):
            return None
        system = ROS_SYSTEMS[session._ros_idx]
        session._ros_idx += 1
        return Question(system, f"Any issues with your {system} system (relevant symptoms)?", SessionState.ROS)

    def _next_dashavidha_question(self, session: HistorySession) -> Optional[Question]:
        if session._dashavidha_idx >= len(DASHAVIDHA_PARIKSHA_QUESTIONS):
            return None
        qid, prompt = DASHAVIDHA_PARIKSHA_QUESTIONS[session._dashavidha_idx]
        session._dashavidha_idx += 1
        return Question(qid, prompt, SessionState.DASHAVIDHA_PARIKSHA)


if __name__ == "__main__":
    dm = DialogueManager()
    start = dm.start_session(language="en", ayush_mode=False)
    print("START:", start)
    sid = start["session_id"]
    turn = dm.submit_answer(sid, "chief_complaint", "chest pain and I'm breathless")
    print("TURN 1 red_flag:", turn["red_flag"])
    print("TURN 1 next_question:", turn["next_question"])
