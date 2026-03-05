"""
agents/orchestrator.py
Orchestrator Agent — Layer 3 Agentic AI Layer
Suraksha Life Insurance — PROJECT RenewAI

Master Planner: Activates at T-45 days.
Follows the Intelligent Renewal Journey from the business case:
  T-45 → Email personalised reminder
  T-30 → WhatsApp if no payment/email response
  T-20 → Voice call if WhatsApp unread
  T-10 → WhatsApp + Email (last chance, ECS/AutoPay)
  T-5  → Voice + WhatsApp (urgent, grace period)
  POST_LAPSE → 90-day revival campaign

Routes high-complexity cases to Human Queue Manager.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional

from data.crm import Policyholder, get_all_policyholders, get_due_within, get_lapsed, get_distressed
from data.propensity_model import score_policyholder, PropensityScore
from data.loyalty_offers_engine import build_offer_package, CustomerOfferPackage
from data.semantic_memory import get_memory, is_distressed
from services.workflow_engine import create_workflow, get_workflow, should_escalate
from config.settings import (
    RENEWAL_JOURNEY, HUMAN_ESCALATION_RATE_TARGET,
    DISTRESS_ESCALATION_SLA_HRS, GRACE_PERIOD_DAYS
)


@dataclass
class OrchestratorDecision:
    policy_id: str
    policy_number: str
    customer_name: str
    # ── Journey step ──────────────────────────────────────────────────────────
    journey_step: str           # T45 | T30 | T20 | T10 | T5 | POST_LAPSE
    days_to_renewal: int
    # ── Routing ───────────────────────────────────────────────────────────────
    channel: str                # email | whatsapp | voice | human
    channel_sequence: list[str] # Ordered channel plan (primary + fallback)
    language: str
    tone: str                   # empathetic | professional | urgent | friendly | informative
    timing: str                 # immediate | morning | evening | business_hours
    # ── Risk & Offers ─────────────────────────────────────────────────────────
    lapse_risk: str
    propensity_score: float
    priority_score: int
    offer_package: Optional[CustomerOfferPackage]
    # ── Complexity & Agent routing ────────────────────────────────────────────
    high_complexity: bool
    complexity_reasons: list[str]
    recommended_agent: str      # EmailAgent | WhatsAppAgent | VoiceAgent | HumanQueueManager
    # ── LLM context dict (passed to agent) ───────────────────────────────────
    context: dict


# ── Journey Step Calculation ──────────────────────────────────────────────────

def _get_journey_step(days_to_renewal: int) -> str:
    """
    Map days-to-renewal to the business case T-trigger.
    T-45: First touch (email)
    T-30: WhatsApp follow-up
    T-20: Voice call
    T-10: Last chance dual channel
    T-5:  Urgent dual channel + grace period
    POST_LAPSE: Already lapsed
    """
    if days_to_renewal < 0:
        return "POST_LAPSE"
    elif days_to_renewal <= 5:
        return "T5"
    elif days_to_renewal <= 10:
        return "T10"
    elif days_to_renewal <= 20:
        return "T20"
    elif days_to_renewal <= 30:
        return "T30"
    else:
        return "T45"


def _journey_channel(step: str, preferred_channel: str) -> str:
    """
    Business case channel logic per journey step:
    T45  → email (always)
    T30  → whatsapp (always — conversational)
    T20  → voice (outbound AI call)
    T10  → whatsapp (with ECS/AutoPay options)
    T5   → voice (primary) + whatsapp (simultaneous)
    POST → multi-channel revival
    """
    step_channel = {
        "T45":       "email",
        "T30":       "whatsapp",
        "T20":       "voice",
        "T10":       "whatsapp",
        "T5":        "voice",
        "POST_LAPSE": "whatsapp",    # Start revival via WhatsApp
    }
    return step_channel.get(step, preferred_channel)


def _journey_channel_sequence(step: str, preferred_channel: str) -> list[str]:
    """
    Ordered channel execution plan.
    Keeps single-channel for early journey steps, and enables intentional
    dual/multi-channel touchpoints near due date and post-lapse.
    """
    if step == "T10":
        return ["whatsapp", "email"]
    if step == "T5":
        return ["voice", "whatsapp"]
    if step == "POST_LAPSE":
        return ["whatsapp", "voice", "email"]
    return [_journey_channel(step, preferred_channel)]


# ── Tone Decision ─────────────────────────────────────────────────────────────

def _decide_tone(ph: Policyholder, step: str, distressed: bool) -> str:
    if distressed or ph.bereavement:
        return "empathetic"
    if step in ("T5", "POST_LAPSE"):
        return "urgent"
    if ph.segment == "Wealth Builder" or ph.loyalty_tier in ("Gold", "Platinum"):
        return "professional"
    if step == "T10":
        return "urgent"
    return "friendly"


# ── Timing Decision ───────────────────────────────────────────────────────────

def _decide_timing(ph: Policyholder, channel: str) -> str:
    if channel == "voice":
        # Honor customer preferred time window (business case: 41% prefer evening/weekend)
        if ph.preferred_time_window == "evening":
            return "17:00–20:00 IST"
        elif ph.preferred_time_window == "morning":
            return "09:00–12:00 IST"
        elif ph.preferred_time_window == "afternoon":
            return "13:00–17:00 IST"
        return "10:00–20:00 IST"
    return "immediate"


# ── High-Complexity Detector ──────────────────────────────────────────────────

def _detect_complexity(ph: Policyholder, score: PropensityScore,
                       memory) -> tuple[bool, list[str]]:
    """
    Route to Human Queue Manager when:
    1. Distress / bereavement keywords detected
    2. 3 objections unresolved (per business case Voice Agent escalation rule)
    3. Fraud/legal complaint raised
    4. Platinum customer at non-Low risk
    5. High-value policy (₹1L+ premium) at Medium/High risk
    6. Workflow retry threshold exceeded
    7. Financial hardship mentioned
    """
    reasons = []

    if ph.distress_flag or ph.bereavement:
        reasons.append("Distress or bereavement detected — immediate human empathy required")

    if len(memory.objections_raised) >= 3:
        reasons.append(f"{len(memory.objections_raised)} objections unresolved — escalate per policy")

    if any("fraud" in obj.lower() or "legal" in obj.lower() or "ombudsman" in obj.lower()
           for obj in memory.objections_raised):
        reasons.append("Legal/fraud/ombudsman complaint — Compliance Handler required")

    if ph.loyalty_tier == "Platinum" and ph.lapse_risk != "Low":
        reasons.append("Platinum customer at lapse risk — Senior RM required")

    if ph.annual_premium >= 100_000 and ph.lapse_risk in ("Medium", "High"):
        reasons.append(f"High-value policy ₹{ph.annual_premium:,.0f} at {ph.lapse_risk} lapse risk")

    if should_escalate(ph.policy_id):
        reasons.append("All automated channels exhausted without resolution")

    return bool(reasons), reasons


def _priority_score(ph: Policyholder, score: PropensityScore, days_to_renewal: int, memory) -> int:
    """
    Priority used to process urgent cases first in batch mode.
    Higher score = higher execution priority.
    """
    urgency = 0
    # Base risk signal
    risk_points = {"Low": 10, "Medium": 25, "High": 45}
    urgency += risk_points.get(score.risk_level, 10)

    # Renewal proximity
    if days_to_renewal < 0:
        urgency += 35
    elif days_to_renewal <= 5:
        urgency += 30
    elif days_to_renewal <= 10:
        urgency += 22
    elif days_to_renewal <= 20:
        urgency += 12

    # Distress and payment friction
    if ph.distress_flag or ph.bereavement:
        urgency += 40
    if ph.last_payment_status in ("Failed", "Pending"):
        urgency += 12
    if ph.payment_mode == "Manual":
        urgency += 8

    # Conversation friction and high value retention
    urgency += min(len(memory.objections_raised) * 5, 20)
    if ph.annual_premium >= 100_000:
        urgency += 8

    return int(min(100, urgency))


def _map_to_agent(channel: str, high_complexity: bool) -> str:
    if high_complexity:
        return "HumanQueueManager"
    return {
        "email":     "EmailAgent",
        "whatsapp":  "WhatsAppAgent",
        "voice":     "VoiceAgent",
    }.get(channel, "EmailAgent")


# ── Core Orchestration Logic ──────────────────────────────────────────────────

def orchestrate(ph: Policyholder) -> OrchestratorDecision:
    """
    Main orchestration for a single policyholder.
    Follows the T-45/30/20/10/5 Intelligent Renewal Journey from the business case.
    """
    score = score_policyholder(ph)
    memory = get_memory(ph.policy_id)
    offer_package = build_offer_package(ph)

    days_to_renewal = (ph.renewal_due_date - date.today()).days
    journey_step = _get_journey_step(days_to_renewal)

    # Complexity check
    high_complexity, complexity_reasons = _detect_complexity(ph, score, memory)
    priority_score = _priority_score(ph, score, days_to_renewal, memory)

    # Channel: override with human queue if complex
    if high_complexity:
        channel = "human"
        channel_sequence = ["human"]
    else:
        channel_sequence = _journey_channel_sequence(journey_step, ph.preferred_channel)
        channel = channel_sequence[0]

    # Tone & timing
    distressed = is_distressed(ph.policy_id) or ph.distress_flag
    tone = _decide_tone(ph, journey_step, distressed)
    timing = _decide_timing(ph, channel)

    # Build full context dict for LLM / agent
    product_map = {"Term": "TERM-BC", "Endowment": "ENDOW-YP",
                   "ULIP": "ULIP-WB", "Health": "HEALTH-SC", "Pension": "ENDOW-YP"}
    product_code = product_map.get(ph.policy_type, "TERM-BC")

    offer_text = ""
    if offer_package.offers:
        best_offer = max(offer_package.offers, key=lambda o: o.savings_inr)
        offer_text = best_offer.description

    context = {
        "name":             ph.name,
        "first_name":       ph.name.split()[0],
        "policy_id":        ph.policy_id,
        "policy_number":    ph.policy_number,
        "policy_type":      ph.policy_type,
        "policy_product":   ph.policy_product_name,
        "premium":          ph.annual_premium,
        "sum_assured":      ph.sum_assured,
        "renewal_date":     ph.renewal_due_date.strftime("%-d %B %Y"),
        "days_left":        max(days_to_renewal, 0),
        "daily_cost":       round(ph.annual_premium / 365, 2),
        "partial_amount":   round(ph.annual_premium * 0.40, 2),
        "emi_amount":       round(ph.annual_premium / 3, 2),
        "pending_premium":  ph.annual_premium,
        "discount_pct":     max(
                                (int(o.discount_pct * 100) for o in offer_package.offers if o.discount_pct > 0),
                                default=0
                            ),
        "savings":          max((o.savings_inr for o in offer_package.offers), default=0),
        "years_no_claim":   ph.years_no_claim,
        "years_as_customer": ph.years_as_customer,
        "loyalty_tier":     ph.loyalty_tier,
        "segment":          ph.segment,
        "language":         ph.language,
        "offer_text":       offer_text,
        "payment_mode":     ph.payment_mode,
        "phone":            ph.phone,
        "grace_period":     GRACE_PERIOD_DAYS,
        "product_code":     product_code,
        "journey_step":     journey_step,
        "tone":             tone,
        "company":          "Suraksha Life Insurance",
        "protection_years": max(30 - ph.years_as_customer, 10),
        "penalty_waiver":   journey_step == "POST_LAPSE",
        "offer_ecs_autopay": journey_step in ("T10", "T5"),
        "channel_sequence": channel_sequence,
        "priority_score": priority_score,
    }

    # Create workflow (idempotent)
    if not get_workflow(ph.policy_id):
        create_workflow(ph.policy_id, ph.preferred_channel, score.risk_level)

    return OrchestratorDecision(
        policy_id=ph.policy_id,
        policy_number=ph.policy_number,
        customer_name=ph.name,
        journey_step=journey_step,
        days_to_renewal=days_to_renewal,
        channel=channel,
        channel_sequence=channel_sequence,
        language=ph.language,
        tone=tone,
        timing=timing,
        lapse_risk=score.risk_level,
        propensity_score=score.score,
        priority_score=priority_score,
        offer_package=offer_package,
        high_complexity=high_complexity,
        complexity_reasons=complexity_reasons,
        recommended_agent=_map_to_agent(channel, high_complexity),
        context=context,
    )


def run_batch(days_ahead: int = 45) -> list[OrchestratorDecision]:
    """Run orchestration for all policyholders in the renewal pipeline."""
    due = get_due_within(days_ahead)
    lapsed = get_lapsed()
    distressed = get_distressed()
    # Deduplicate
    all_phs = list({ph.policy_id: ph for ph in due + lapsed + distressed}.values())
    # Process highest-value/urgent opportunities first for faster conversion impact.
    prioritized = sorted(
        all_phs,
        key=lambda ph: (
            ph.distress_flag or ph.bereavement,
            ph.renewal_due_date < date.today(),
            ph.lapse_risk == "High",
            -((ph.renewal_due_date - date.today()).days),
        ),
        reverse=True,
    )

    decisions = []
    for ph in prioritized:
        try:
            decisions.append(orchestrate(ph))
        except Exception as e:
            print(f"  [Orchestrator] ⚠️  Error on {ph.policy_id}: {e}")
    return sorted(decisions, key=lambda d: d.priority_score, reverse=True)
