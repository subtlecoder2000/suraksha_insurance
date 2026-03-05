"""
services/workflow_engine.py
AI Workflow Engine — Layer 2 AI Platform Services
State machine per policyholder: NTI interrupt nodes, branching logic, auto-retry, escalation timers.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Callable


class WorkflowState(str, Enum):
    IDLE            = "idle"
    ASSESSMENT      = "assessment"          # Propensity scored, channel decided
    FIRST_CONTACT   = "first_contact"       # First outbound message sent
    AWAITING_RESPONSE = "awaiting_response"
    OBJECTION_HANDLING = "objection_handling"
    PAYMENT_INITIATED = "payment_initiated"
    PAYMENT_SUCCESS = "payment_success"
    ESCALATED       = "escalated"           # Routed to human
    LAPSED          = "lapsed"
    REVIVAL_ATTEMPT = "revival_attempt"
    REVIVAL_SUCCESS = "revival_success"
    CLOSED          = "closed"


@dataclass
class WorkflowNode:
    state: WorkflowState
    action: str
    channel: str
    scheduled_at: datetime
    completed_at: Optional[datetime] = None
    outcome: Optional[str] = None
    retry_count: int = 0


@dataclass
class PolicyWorkflow:
    policy_id: str
    current_state: WorkflowState = WorkflowState.IDLE
    nodes: list[WorkflowNode] = field(default_factory=list)
    max_retries: int = 3
    escalate_after_days: int = 3
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: dict = field(default_factory=dict)


_WORKFLOWS: dict[str, PolicyWorkflow] = {}


# ── Workflow Factory ──────────────────────────────────────────────────────────

def create_workflow(policy_id: str, preferred_channel: str, lapse_risk: str) -> PolicyWorkflow:
    """Initialize a renewal workflow for a policyholder based on risk level."""
    now = datetime.now()

    # Define touch sequence based on risk level
    if lapse_risk == "High":
        nodes = [
            WorkflowNode(WorkflowState.FIRST_CONTACT, "send_whatsapp", "whatsapp", now),
            WorkflowNode(WorkflowState.FIRST_CONTACT, "send_email", "email", now + timedelta(hours=2)),
            WorkflowNode(WorkflowState.FIRST_CONTACT, "voice_call", "voice", now + timedelta(days=1)),
            WorkflowNode(WorkflowState.ESCALATED, "human_queue", "human", now + timedelta(days=2)),
        ]
    elif lapse_risk == "Medium":
        nodes = [
            WorkflowNode(WorkflowState.FIRST_CONTACT, f"send_{preferred_channel}", preferred_channel, now),
            WorkflowNode(WorkflowState.FIRST_CONTACT, "send_whatsapp", "whatsapp", now + timedelta(days=2)),
            WorkflowNode(WorkflowState.FIRST_CONTACT, "voice_call", "voice", now + timedelta(days=5)),
        ]
    else:  # Low risk
        nodes = [
            WorkflowNode(WorkflowState.FIRST_CONTACT, f"send_{preferred_channel}", preferred_channel, now),
            WorkflowNode(WorkflowState.FIRST_CONTACT, "send_email", "email", now + timedelta(days=7)),
        ]

    wf = PolicyWorkflow(
        policy_id=policy_id,
        current_state=WorkflowState.ASSESSMENT,
        nodes=nodes,
        metadata={"lapse_risk": lapse_risk, "preferred_channel": preferred_channel},
    )
    _WORKFLOWS[policy_id] = wf
    return wf


def get_workflow(policy_id: str) -> Optional[PolicyWorkflow]:
    return _WORKFLOWS.get(policy_id)


def advance_state(policy_id: str, new_state: WorkflowState, outcome: str = None) -> PolicyWorkflow:
    """Move workflow to a new state."""
    wf = _WORKFLOWS.get(policy_id)
    if not wf:
        raise ValueError(f"No workflow found for {policy_id}")
    wf.current_state = new_state
    wf.updated_at = datetime.now()
    if wf.nodes:
        current_node = wf.nodes[0]
        current_node.completed_at = datetime.now()
        current_node.outcome = outcome
    return wf


def get_pending_actions(policy_id: str) -> list[WorkflowNode]:
    """Return nodes that are due to run but not yet completed."""
    wf = _WORKFLOWS.get(policy_id)
    if not wf:
        return []
    now = datetime.now()
    return [n for n in wf.nodes if n.completed_at is None and n.scheduled_at <= now]


def mark_payment_success(policy_id: str) -> None:
    advance_state(policy_id, WorkflowState.PAYMENT_SUCCESS, "payment_received")


def mark_escalated(policy_id: str) -> None:
    advance_state(policy_id, WorkflowState.ESCALATED, "human_handoff")


def should_escalate(policy_id: str) -> bool:
    """Check if the workflow has exceeded retry/time thresholds."""
    wf = _WORKFLOWS.get(policy_id)
    if not wf:
        return False
    completed = [n for n in wf.nodes if n.completed_at is not None]
    if len(completed) >= wf.max_retries:
        return True
    age = (datetime.now() - wf.created_at).days
    return age >= wf.escalate_after_days


def get_all_workflows() -> dict[str, PolicyWorkflow]:
    return _WORKFLOWS


def reset_workflows() -> None:
    """Test/helper utility to clear in-memory workflow state."""
    _WORKFLOWS.clear()
