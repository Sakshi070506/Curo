from services.redflag_service import RedFlagDetector, build_triage_alert_payload
from services.notification_service import NotificationService, InMemoryDashboardChannel


# ---------------------------------------------------------------------------
# Red-flag detection
# ---------------------------------------------------------------------------
def test_redflag_detects_acute_coronary_syndrome():
    detector = RedFlagDetector()
    result = detector.check("I have chest pain and I'm breathless since this morning")
    assert result.triggered is True
    assert result.highest_severity == "critical"
    ids = [r["id"] for r in result.matched_rules]
    assert "acute_coronary_syndrome" in ids


def test_redflag_no_trigger_on_routine_complaint():
    detector = RedFlagDetector()
    result = detector.check("mild headache for two days, otherwise feeling fine")
    assert result.triggered is False
    assert result.highest_severity == "none"


def test_redflag_empty_text_is_safe():
    detector = RedFlagDetector()
    result = detector.check("")
    assert result.triggered is False


def test_redflag_spans_multiple_turns():
    detector = RedFlagDetector()
    # "chest pain" in turn 1, breathlessness only shows up in turn 2 -- the
    # combined-answers check should still catch it even though neither single
    # turn triggers the rule alone.
    turn1 = detector.check("chest pain")
    turn2 = detector.check("breathless")
    assert turn1.triggered is False
    assert turn2.triggered is False

    combined = detector.check_session_answers(["chest pain", "breathless"])
    assert combined.triggered is True
    assert combined.highest_severity == "critical"


def test_redflag_stroke_fast_rule():
    detector = RedFlagDetector()
    result = detector.check("sudden weakness on one side of my body")
    assert result.triggered is True
    assert any(r["id"] == "stroke_fast" for r in result.matched_rules)


def test_redflag_multiple_rules_take_highest_severity():
    detector = RedFlagDetector()
    text = "chest pain, breathless, and also high fever with confusion"
    result = detector.check(text)
    assert result.triggered is True
    assert result.highest_severity == "critical"
    assert len(result.matched_rules) >= 2


def test_build_triage_alert_payload_shape():
    detector = RedFlagDetector()
    result = detector.check("chest pain and breathless")
    payload = build_triage_alert_payload("p1", "s1", result)
    assert payload["patient_id"] == "p1"
    assert payload["session_id"] == "s1"
    assert payload["severity"] == "critical"
    assert payload["requires_immediate_attention"] is True


# ---------------------------------------------------------------------------
# Notification service
# ---------------------------------------------------------------------------
def test_notification_push_and_queue():
    svc = NotificationService()
    alert = svc.push_triage_alert("p1", "s1", "high", [{"id": "x", "description": "y", "severity": "high"}])
    queue = svc.get_queue()
    assert len(queue) == 1
    assert queue[0].id == alert.id
    assert queue[0].acknowledged is False


def test_notification_acknowledge_removes_from_pending():
    svc = NotificationService()
    alert = svc.push_triage_alert("p1", "s1", "high", [])
    assert svc.acknowledge(alert.id) is True
    assert svc.get_queue() == []


def test_notification_critical_alert_triggers_sms_escalation():
    svc = NotificationService(sms_escalation_numbers=["+91-9999999999"])
    svc.push_triage_alert(
        "p1", "s1", "critical",
        [{"id": "acute_coronary_syndrome", "description": "Chest pain with breathlessness", "severity": "critical"}],
    )
    assert len(svc.sms_provider.sent_log) == 1
    assert svc.sms_provider.sent_log[0]["to"] == "+91-9999999999"
    assert "p1" in svc.sms_provider.sent_log[0]["message"]


def test_notification_high_severity_does_not_trigger_sms():
    svc = NotificationService(sms_escalation_numbers=["+91-9999999999"])
    svc.push_triage_alert("p1", "s1", "high", [])
    assert len(svc.sms_provider.sent_log) == 0


def test_notification_subscriber_receives_alert():
    received = []
    channel = InMemoryDashboardChannel()
    channel.subscribe(lambda alert: received.append(alert))
    svc = NotificationService(dashboard_channel=channel)
    svc.push_triage_alert("p1", "s1", "high", [])
    assert len(received) == 1