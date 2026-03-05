"""
agents/voice_agent.py
Voice Agent — Layer 3 Agentic AI Layer
Suraksha Life Insurance — PROJECT RenewAI

Outbound AI voice calls in 9 Indian languages.
- Reads live payment status before calling (does NOT call if already paid)
- Dynamic objection library (top 12 objections)
- Offers EMI, grace period, AutoPay setup
- ESCALATES: distress keywords, 3 unresolved objections, caller requests human
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from services.voice_engine import simulate_call, get_script, CallSession
from services.llm import classify_intent
from services.rag_retrieval import retrieve_objection_response
from data.semantic_memory import add_turn, record_intent, record_sentiment, record_objection, is_distressed
from data.payment_gateway import generate_upi_qr
from data.crm import get_policyholder, flag_distress


@dataclass
class VoiceCallResult:
    policy_id: str
    policy_number: str
    call_session: CallSession
    objections_handled: list[str]
    payment_link_offered: bool
    emi_offered: bool
    autopay_offered: bool
    grace_period_mentioned: bool
    escalated: bool
    escalation_reason: str
    outcome: str   # payment_link_sent | emi_agreed | callback_requested | escalated | voicemail | completed


def make_call(
    policy_id: str,
    context: dict,
    journey_step: str = "T20",
) -> VoiceCallResult:
    """
    Main voice agent entry point.
    1. Check payment status — skip call if already paid.
    2. Simulate AI outbound call.
    3. Handle objections from transcript.
    4. Detect distress and escalate.
    5. Offer payment link / EMI / AutoPay.
    """
    ph = get_policyholder(policy_id)
    if not ph:
        raise ValueError(f"Policyholder {policy_id} not found")

    # ── Rule: Do NOT call if payment already made ─────────────────────────────
    if ph.last_payment_status == "Paid":
        print(f"  [VoiceAgent] ✅ Skipping call for {ph.name} — payment already received.")
        return VoiceCallResult(
            policy_id=policy_id,
            policy_number=ph.policy_number,
            call_session=CallSession(
                call_id="SKIP",
                policy_id=policy_id,
                language=ph.language,
                transcript=[],
                intent_detected="payment_already_made",
                sentiment="positive",
                outcome="skipped_already_paid",
                duration_seconds=0,
            ),
            objections_handled=[],
            payment_link_offered=False,
            emi_offered=False,
            autopay_offered=False,
            grace_period_mentioned=False,
            escalated=False,
            escalation_reason="",
            outcome="skipped_already_paid",
        )

    # ── Build context enriched for voice script ───────────────────────────────
    voice_context = dict(context)
    voice_context["offer_text"] = context.get("offer_text", "")

    # T5/T10 urgency additions
    if journey_step in ("T5",):
        voice_context["grace_period_info"] = (
            f"Your policy has a {context.get('grace_period', 30)}-day grace period. "
            "Renewing within grace period keeps all benefits active."
        )
    if journey_step in ("T10", "T5"):
        voice_context["autopay_prompt"] = (
            "You can also set up AutoPay right now — just say 'AutoPay' and I'll guide you."
        )

    # ── Simulate call ─────────────────────────────────────────────────────────
    session = simulate_call(policy_id, ph.language, voice_context)
    add_turn(policy_id, "system", f"[VOICE CALL {session.call_id}] {session.outcome}",
             channel="voice", language=ph.language)

    # ── Analyse transcript for distress, objections, intents ─────────────────
    objections_handled = []
    escalated = False
    escalation_reason = ""
    payment_link_offered = False
    emi_offered = False
    autopay_offered = False
    grace_mentioned = journey_step in ("T5",)

    for turn in session.transcript:
        if turn["role"] == "customer":
            classification = classify_intent(turn["text"])
            intents = classification.get("intents", [])
            sentiment = classification.get("sentiment", "neutral")
            record_sentiment(policy_id, sentiment)

            if sentiment == "distressed" or is_distressed(policy_id):
                flag_distress(policy_id, "voice_call_distress")
                escalated = True
                escalation_reason = "Distress keywords detected during voice call"
                break

            if "price_objection" in intents or "delay_objection" in intents:
                objection_text = turn["text"]
                record_objection(policy_id, objection_text[:80])
                objections_handled.append(objection_text[:80])
                # After 3 unresolved objections → escalate
                if len(objections_handled) >= 3:
                    escalated = True
                    escalation_reason = "3 objections unresolved — human agent required"
                    break

            if "payment_intent" in intents:
                payment_link_offered = True
                emi_offered = "emi" in " ".join(intents).lower() or "instalment" in turn["text"].lower()

    if "human" in session.outcome.lower():
        escalated = True
        escalation_reason = "Customer requested human agent"

    # Determine final outcome
    if escalated:
        final_outcome = "escalated"
    elif payment_link_offered:
        final_outcome = "payment_link_sent"
    elif emi_offered:
        final_outcome = "emi_agreed"
    elif session.outcome == "voicemail":
        final_outcome = "voicemail"
    else:
        final_outcome = "completed"

    print(
        f"  [VoiceAgent] 📞 Call {session.call_id} | {ph.name} | "
        f"Lang: {ph.language} | Outcome: {final_outcome} | "
        f"Escalate: {escalated}"
    )

    return VoiceCallResult(
        policy_id=policy_id,
        policy_number=ph.policy_number,
        call_session=session,
        objections_handled=objections_handled,
        payment_link_offered=payment_link_offered,
        emi_offered=emi_offered,
        autopay_offered=autopay_offered,
        grace_period_mentioned=grace_mentioned,
        escalated=escalated,
        escalation_reason=escalation_reason,
        outcome=final_outcome,
    )
