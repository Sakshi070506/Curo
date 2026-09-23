import pytest
from services.dialogue_manager import DialogueManager, SessionState
from services.redflag_service import RedFlagDetector


def test_start_session_returns_chief_complaint_question():
    dm = DialogueManager()
    start = dm.start_session(language="en")
    assert "session_id" in start
    assert start["next_question"]["question_id"] == "chief_complaint"


def test_full_routine_interview_reaches_complete():
    dm = DialogueManager()
    start = dm.start_session(language="en", ayush_mode=False)
    sid = start["session_id"]

    # Answer chief complaint
    turn = dm.submit_answer(sid, "chief_complaint", "mild headache")
    assert turn["state"] == SessionState.HPI_LOOP.value
    assert turn["red_flag"]["triggered"] is False

    # Walk through the rest of the interview by always answering whatever
    # question comes back, until the session reports complete.
    guard = 0
    while not turn["complete"]:
        guard += 1
        assert guard < 100, "interview did not terminate - possible infinite loop"
        qid = turn["next_question"]["question_id"]
        turn = dm.submit_answer(sid, qid, "no significant issues")

    session = dm.get_session(sid)
    assert session.state == SessionState.COMPLETE
    assert session.chief_complaint == "mild headache"
    assert len(session.hpi) == 8  # all SOCRATES slots filled
    assert len(session.review_of_systems) == 6  # all ROS systems asked


def test_ayush_mode_adds_dashavidha_pariksha():
    dm = DialogueManager()
    start = dm.start_session(language="hi", ayush_mode=True)
    sid = start["session_id"]

    turn = dm.submit_answer(sid, "chief_complaint", "fatigue")
    guard = 0
    saw_dashavidha = False
    while not turn["complete"]:
        guard += 1
        assert guard < 100
        if turn["state"] == SessionState.DASHAVIDHA_PARIKSHA.value:
            saw_dashavidha = True
        qid = turn["next_question"]["question_id"]
        turn = dm.submit_answer(sid, qid, "answer")

    assert saw_dashavidha is True
    session = dm.get_session(sid)
    assert len(session.ayush) == 11  # all Dashavidha Pariksha slots filled


def test_non_ayush_session_skips_dashavidha():
    dm = DialogueManager()
    start = dm.start_session(language="en", ayush_mode=False)
    sid = start["session_id"]
    turn = dm.submit_answer(sid, "chief_complaint", "cough")
    states_seen = {turn["state"]}
    guard = 0
    while not turn["complete"]:
        guard += 1
        assert guard < 100
        qid = turn["next_question"]["question_id"]
        turn = dm.submit_answer(sid, qid, "answer")
        states_seen.add(turn["state"])
    assert SessionState.DASHAVIDHA_PARIKSHA.value not in states_seen


def test_redflag_triggers_mid_interview_and_is_recorded():
    dm = DialogueManager()
    start = dm.start_session(language="en")
    sid = start["session_id"]

    turn = dm.submit_answer(sid, "chief_complaint", "chest pain")
    assert turn["red_flag"]["triggered"] is False  # needs breathlessness too

    turn = dm.submit_answer(sid, turn["next_question"]["question_id"], "I also feel breathless")
    assert turn["red_flag"]["triggered"] is True
    assert turn["red_flag"]["severity"] == "critical"

    session = dm.get_session(sid)
    assert len(session.red_flags_triggered) >= 1
    assert any(r["id"] == "acute_coronary_syndrome" for r in session.red_flags_triggered)


def test_to_dict_matches_module_a_data_contract():
    dm = DialogueManager()
    start = dm.start_session(language="en")
    sid = start["session_id"]
    dm.submit_answer(sid, "chief_complaint", "fever")
    session = dm.get_session(sid)
    data = session.to_dict()
    for key in [
        "session_id", "language", "chief_complaint", "hpi",
        "past_medical_history", "drug_allergy_history", "family_history",
        "personal_history", "review_of_systems", "ayush", "red_flags_triggered", "state",
    ]:
        assert key in data


def test_unknown_session_id_raises():
    dm = DialogueManager()
    with pytest.raises(KeyError):
        dm.get_session("does-not-exist")


def test_cannot_submit_answer_after_completion():
    dm = DialogueManager()
    start = dm.start_session(language="en")
    sid = start["session_id"]
    turn = dm.submit_answer(sid, "chief_complaint", "cough")
    guard = 0
    while not turn["complete"]:
        guard += 1
        assert guard < 100
        turn = dm.submit_answer(sid, turn["next_question"]["question_id"], "fine")
    with pytest.raises(ValueError):
        dm.submit_answer(sid, "anything", "too late")


def test_dialogue_manager_uses_injected_redflag_detector():
    custom_detector = RedFlagDetector(rules=[])  # no rules -> never triggers
    dm = DialogueManager(redflag_detector=custom_detector)
    start = dm.start_session(language="en")
    sid = start["session_id"]
    turn = dm.submit_answer(sid, "chief_complaint", "chest pain and breathless")
    assert turn["red_flag"]["triggered"] is False