"""
Module   : Notification Service
Owner    : Backend Engineer
Purpose  : Pushes triage alerts to staff (dashboard/SMS/email).

Design notes
------------
- InMemoryDashboardChannel stands in for a websocket/polling broadcast channel
  during local dev and tests. Swap it for a real websocket broadcaster in
  production without touching NotificationService's public API.
- SMS/email are optional escalation channels for CRITICAL alerts only, behind a
  provider interface so they're safe no-ops in dev (NoOpSMSProvider just logs).
"""

from __future__ import annotations

import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol


@dataclass
class TriageAlert:
    id: str
    patient_id: str
    session_id: str
    severity: str
    matched_rules: list[dict]
    created_at: float
    acknowledged: bool = False
    requires_immediate_attention: bool = False
    symptom: str = ""
    timestamp: str = ""


class DashboardChannel(Protocol):
    def publish(self, alert: TriageAlert) -> None: ...
    def subscribe(self, callback: Callable[[TriageAlert], None]) -> None: ...


class InMemoryDashboardChannel:
    """Backing store for both GET /api/triage/queue (polling) and a future
    websocket handler (via subscribe callbacks) — same underlying queue."""

    def __init__(self):
        self._queue: list[TriageAlert] = []
        self._subscribers: list[Callable[[TriageAlert], None]] = []

    def publish(self, alert: TriageAlert) -> None:
        self._queue.append(alert)
        for callback in self._subscribers:
            callback(alert)

    def subscribe(self, callback: Callable[[TriageAlert], None]) -> None:
        self._subscribers.append(callback)

    def pending(self) -> list[TriageAlert]:
        return [a for a in self._queue if not a.acknowledged]

    def acknowledge(self, alert_id: str) -> bool:
        for alert in self._queue:
            if alert.id == alert_id:
                alert.acknowledged = True
                return True
        return False


class SMSProvider(Protocol):
    def send(self, to: str, message: str) -> bool: ...


class NoOpSMSProvider:
    """Default provider for local dev — logs instead of sending a real SMS, so
    tests can assert on `sent_log` without any telecom API integration."""

    def __init__(self):
        self.sent_log: list[dict[str, str]] = []

    def send(self, to: str, message: str) -> bool:
        self.sent_log.append({"to": to, "message": message})
        return True


class NotificationService:
    def __init__(
        self,
        dashboard_channel: DashboardChannel | None = None,
        sms_provider: SMSProvider | None = None,
        sms_escalation_numbers: list[str] | None = None,
    ):
        self.dashboard_channel = dashboard_channel or InMemoryDashboardChannel()
        self.sms_provider = sms_provider or NoOpSMSProvider()
        self.sms_escalation_numbers = sms_escalation_numbers or []

    def push_triage_alert(
        self,
        patient_id: str,
        session_id: str,
        severity: str,
        matched_rules: list[dict],
        requires_immediate_attention: bool | None = None,
        symptom: str = "",
        timestamp: str = "",
    ) -> TriageAlert:
        if requires_immediate_attention is None:
            requires_immediate_attention = severity == "critical"
        alert = TriageAlert(
            id=str(uuid.uuid4()),
            patient_id=patient_id,
            session_id=session_id,
            severity=severity,
            matched_rules=matched_rules,
            created_at=time.time(),
            requires_immediate_attention=requires_immediate_attention,
            symptom=symptom,
            timestamp=timestamp,
        )
        self.dashboard_channel.publish(alert)

        if requires_immediate_attention:
            self._escalate_sms(alert)

        return alert

    def _escalate_sms(self, alert: TriageAlert) -> None:
        message = (
            f"CRITICAL triage alert for patient {alert.patient_id} "
            f"(session {alert.session_id}): "
            f"{', '.join(r['description'] for r in alert.matched_rules)}"
        )
        for number in self.sms_escalation_numbers:
            self.sms_provider.send(number, message)

    def get_queue(self) -> list[TriageAlert]:
        if hasattr(self.dashboard_channel, "pending"):
            return self.dashboard_channel.pending()
        return []

    def acknowledge(self, alert_id: str) -> bool:
        if hasattr(self.dashboard_channel, "acknowledge"):
            return self.dashboard_channel.acknowledge(alert_id)
        return False


if __name__ == "__main__":
    svc = NotificationService(sms_escalation_numbers=["+91-9999999999"])
    alert = svc.push_triage_alert(
        "p123", "s456", "critical",
        [{"id": "acute_coronary_syndrome", "description": "Chest pain with breathlessness", "severity": "critical"}],
        requires_immediate_attention=True,
        symptom="Chest pain with breathlessness — possible cardiac event",
        timestamp="2026-01-01T00:00:00Z",
    )
    print("Queued:", svc.get_queue())
    print("SMS log:", svc.sms_provider.sent_log)
