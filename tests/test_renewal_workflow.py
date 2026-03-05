import pytest

from agents.orchestrator import orchestrate, run_batch
from agents.whatsapp_agent import handle_reply
from api.main import JourneyRequest, run_batch_endpoint, run_journey_endpoint
from data.crm import get_policyholder
from monitoring.observability import EventType, log_event
from monitoring.scorecard import get_scorecard


def _scorecard_entry(metric_name: str) -> dict:
    return next(row for row in get_scorecard() if row["metric"] == metric_name)


def test_orchestrator_routes_distress_case_to_human_queue():
    ph = get_policyholder("POL-002")
    decision = orchestrate(ph)

    assert decision.high_complexity is True
    assert decision.recommended_agent == "HumanQueueManager"
    assert decision.channel == "human"
    assert decision.channel_sequence == ["human"]


def test_whatsapp_handles_emi_flow_with_partial_payment_link():
    ph = get_policyholder("POL-001")
    decision = orchestrate(ph)

    reply = handle_reply(
        ph.policy_id,
        ph.phone,
        "Can I pay in EMI installments?",
        decision.context,
    )

    assert reply.escalate is False
    assert reply.upi_qr is not None
    assert "3-part plan" in reply.body


@pytest.mark.asyncio
async def test_api_journey_run_dispatches_email_and_human_paths():
    email_out = await run_journey_endpoint(JourneyRequest(policy_id="POL-003"))
    assert email_out["routed_to_human"] is False
    assert email_out["channel_used"] == "email"
    assert "subject" in email_out

    human_out = await run_journey_endpoint(JourneyRequest(policy_id="POL-002"))
    assert human_out["routed_to_human"] is True
    assert human_out["specialist"] == "SeniorRM"


@pytest.mark.asyncio
async def test_batch_endpoint_updates_live_escalation_metric_from_decisions():
    decisions = run_batch(45)
    expected = len([d for d in decisions if d.recommended_agent == "HumanQueueManager"]) / len(decisions)

    await run_batch_endpoint()
    row = _scorecard_entry("Human Escalation Rate")
    assert row["current"] == f"{expected:.0%}"


def test_distress_sla_metric_turns_green_when_distress_is_escalated_within_sla():
    log_event(
        EventType.DISTRESS_FLAG,
        policy_id="POL-999",
        agent="WhatsAppAgent",
        action="detected_distress",
        channel="whatsapp",
        outcome="flagged",
        irdai_relevant=True,
    )
    log_event(
        EventType.ESCALATION,
        policy_id="POL-999",
        agent="HumanQueueManager",
        action="human_handoff",
        channel="human",
        outcome="queued",
        irdai_relevant=True,
    )

    row = _scorecard_entry("Distress Escalation ≤2h (100%)")
    assert row["current"] == "100%"
    assert row["status"] == "🟢"
