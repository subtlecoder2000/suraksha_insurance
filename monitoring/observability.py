"""
monitoring/observability.py
AI Observability Platform — Layer 6 Monitoring & Governance
Suraksha Life Insurance — PROJECT RenewAI v2.0

Full trace of every agent action, decision, and escalation.
IRDAI audit-ready logs.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
from typing import Optional


class EventType(str, Enum):
    AGENT_ACTION   = "AGENT_ACTION"
    CRITIQUE_EVAL  = "CRITIQUE_EVAL"
    ESCALATION     = "ESCALATION"
    PAYMENT_EVENT  = "PAYMENT_EVENT"
    DISTRESS_FLAG  = "DISTRESS_FLAG"
    RENEWAL_CLOSED = "RENEWAL_CLOSED"
    SYSTEM_ERROR   = "SYSTEM_ERROR"


@dataclass
class AuditEvent:
    event_id: str
    event_type: EventType
    policy_id: str
    agent: str
    action: str
    channel: str
    outcome: str
    metadata: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    irdai_relevant: bool = False


_AUDIT_LOG: list[AuditEvent] = []
_EVENT_COUNTER = 1


def log_event(
    event_type: EventType,
    policy_id: str,
    agent: str,
    action: str,
    channel: str = "",
    outcome: str = "",
    metadata: dict = None,
    irdai_relevant: bool = False,
) -> AuditEvent:
    global _EVENT_COUNTER
    event = AuditEvent(
        event_id=f"EVT-{_EVENT_COUNTER:06d}",
        event_type=event_type,
        policy_id=policy_id,
        agent=agent,
        action=action,
        channel=channel,
        outcome=outcome,
        metadata=metadata or {},
        irdai_relevant=irdai_relevant,
    )
    _AUDIT_LOG.append(event)
    _EVENT_COUNTER += 1
    return event


def get_policy_trace(policy_id: str) -> list[AuditEvent]:
    """Full trace for a single policyholder (IRDAI audit ready)."""
    return [e for e in _AUDIT_LOG if e.policy_id == policy_id]


def get_irdai_audit_log() -> list[dict]:
    """Export all IRDAI-relevant events in structured format."""
    return [
        {
            "event_id": e.event_id,
            "timestamp": e.timestamp.isoformat(),
            "policy_id": e.policy_id,
            "event_type": e.event_type.value,
            "agent": e.agent,
            "action": e.action,
            "channel": e.channel,
            "outcome": e.outcome,
        }
        for e in _AUDIT_LOG if e.irdai_relevant
    ]

def get_all_audit_logs() -> list[dict]:
    return [
        {
            "id": e.event_id,
            "timestamp": e.timestamp.isoformat(),
            "policy_id": e.policy_id,
            "type": e.event_type.value,
            "agent": e.agent,
            "action": e.action,
            "channel": e.channel,
            "outcome": e.outcome,
            "irdai_relevant": e.irdai_relevant,
        }
        for e in _AUDIT_LOG
    ]



def get_escalation_log() -> list[AuditEvent]:
    return [e for e in _AUDIT_LOG if e.event_type == EventType.ESCALATION]


def get_distress_log() -> list[AuditEvent]:
    return [e for e in _AUDIT_LOG if e.event_type == EventType.DISTRESS_FLAG]


def get_system_stats() -> dict:
    total = len(_AUDIT_LOG)
    by_type = {}
    for e in _AUDIT_LOG:
        by_type[e.event_type.value] = by_type.get(e.event_type.value, 0) + 1
    return {
        "total_events": total,
        "by_type": by_type,
        "irdai_relevant": len([e for e in _AUDIT_LOG if e.irdai_relevant]),
        "distress_events": len(get_distress_log()),
        "escalations": len(get_escalation_log()),
    }


def get_distress_sla_stats(sla_hours: int) -> dict:
    """
    Compute distress-to-escalation SLA adherence from audit logs.
    A distress event is considered within SLA when the first subsequent
    escalation for the same policy occurs within `sla_hours`.
    """
    distress_events = sorted(get_distress_log(), key=lambda e: e.timestamp)
    escalation_by_policy: dict[str, list[AuditEvent]] = {}
    for evt in sorted(get_escalation_log(), key=lambda e: e.timestamp):
        escalation_by_policy.setdefault(evt.policy_id, []).append(evt)

    measured = 0
    within_sla = 0
    breached = 0
    pending = 0

    for distress in distress_events:
        measured += 1
        policy_escalations = escalation_by_policy.get(distress.policy_id, [])
        matched: Optional[AuditEvent] = next(
            (e for e in policy_escalations if e.timestamp >= distress.timestamp),
            None
        )
        if not matched:
            pending += 1
            continue

        delta_hours = (matched.timestamp - distress.timestamp).total_seconds() / 3600
        if delta_hours <= sla_hours:
            within_sla += 1
        else:
            breached += 1

    measured_closed = within_sla + breached
    adherence = (within_sla / measured_closed) if measured_closed else None
    return {
        "total_distress_events": measured,
        "within_sla": within_sla,
        "breached": breached,
        "pending": pending,
        "adherence_ratio": adherence,  # None when no closed distress events exist
    }


def reset_audit_log() -> None:
    """Test/helper utility to clear in-memory audit state."""
    global _EVENT_COUNTER
    _AUDIT_LOG.clear()
    _EVENT_COUNTER = 1
