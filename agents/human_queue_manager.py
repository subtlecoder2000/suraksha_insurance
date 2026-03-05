"""
agents/human_queue_manager.py
Human Queue Manager — Layer 3 Agentic AI Layer
Suraksha Life Insurance — PROJECT RenewAI

Routes escalated cases (~10%) to the right human specialist with full briefing.
Terminal human handoff node — no further AI action after this.

Routes to:
  - Senior Renewal RM       : high-value, HNI, emotionally complex cases
  - Revival Specialist       : lapsed policies, medical re-underwriting
  - Compliance Handler       : IRDAI complaints, mis-selling, ombudsman
  - AI Ops & Quality Manager : AI system issues
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from data.crm import get_policyholder, Policyholder
from data.semantic_memory import get_memory, get_context_window, get_current_sentiment
from services.llm import summarize_interaction
from config.settings import DISTRESS_ESCALATION_SLA_HRS


@dataclass
class HumanBriefing:
    """Briefing note prepared automatically for the human specialist."""
    case_id: str
    policy_id: str
    policy_number: str
    customer_name: str
    customer_age: int
    customer_language: str
    specialist_type: str        # SeniorRM | RevivalSpecialist | ComplianceHandler | AIOps
    priority: str               # URGENT | HIGH | NORMAL
    escalation_reason: str
    policy_summary: str
    prior_ai_interactions: list[dict]
    detected_sentiment: str
    recommended_approach: str
    offers_already_shown: list[str]
    objections_raised: list[str]
    sla_hours: int              # Target response within N hours
    timestamp: datetime = field(default_factory=datetime.now)
    status: str = "OPEN"        # OPEN | ASSIGNED | RESOLVED


_QUEUE: list[HumanBriefing] = []
_CASE_COUNTER = 1


def _determine_specialist(ph: Policyholder, escalation_reason: str) -> str:
    """Route to the right specialist per business case rules."""
    reason_lower = escalation_reason.lower()

    # Compliance & grievance handler
    if any(kw in reason_lower for kw in
           ["fraud", "legal", "complaint", "ombudsman", "mis-selling", "dispute", "irdai"]):
        return "ComplianceHandler"

    # Revival specialist
    if ph.renewal_due_date < datetime.now().date():
        return "RevivalSpecialist"

    # Senior RM for high-value / HNI / bereavement / complex
    if (ph.annual_premium >= 100_000
            or ph.loyalty_tier == "Platinum"
            or ph.bereavement
            or ph.distress_flag):
        return "SeniorRM"

    # Default: Senior RM
    return "SeniorRM"


def _determine_priority(ph: Policyholder, escalation_reason: str) -> str:
    reason_lower = escalation_reason.lower()
    if ph.bereavement or "bereavement" in reason_lower or "pass" in reason_lower:
        return "URGENT"
    if "distress" in reason_lower or ph.distress_flag:
        return "URGENT"
    if ph.annual_premium >= 100_000 or ph.loyalty_tier == "Platinum":
        return "HIGH"
    return "NORMAL"


def _recommended_approach(ph: Policyholder, specialist: str, sentiment: str) -> str:
    if ph.bereavement:
        return (
            "Customer has experienced bereavement. Lead with condolences and empathy. "
            "Do NOT discuss premiums immediately. Explain death benefit claim process first. "
            "Offer premium holiday (1–3 months) and revival fee waiver. "
            "Goal: retain customer for life through genuine human support."
        )
    if specialist == "RevivalSpecialist":
        return (
            f"Policy lapsed — eligible for penalty waiver revival within 90 days. "
            f"Calculate revival quotation. Explore EMI options (₹{ph.annual_premium / 3:,.0f} × 3). "
            "Check if medical re-underwriting required for health/ULIP policies."
        )
    if specialist == "ComplianceHandler":
        return (
            "Handle grievance per IRDAI Grievance Redressal guidelines. "
            "Log in grievance register. Target resolution within 15 days. "
            "If ombudsman case: prepare complete policy file."
        )
    # Senior RM
    discount_note = ""
    if ph.years_no_claim >= 3:
        discount_note = f" Offer No-Claim Discount ({10 if ph.years_no_claim >= 3 else 5}% off). "
    return (
        f"Approach as a trusted advisor. {discount_note}"
        f"Customer has been with Suraksha {ph.years_as_customer} years ({ph.loyalty_tier} tier). "
        "Acknowledge their loyalty. Authorise custom offer if needed (approval from Renewal Head)."
    )


def _build_policy_summary(ph: Policyholder) -> str:
    from data.policy_store import get_policy_summary
    product_map = {"Term": "TERM-BC", "Endowment": "ENDOW-YP",
                   "ULIP": "ULIP-WB", "Health": "HEALTH-SC", "Pension": "ENDOW-YP"}
    ps = get_policy_summary(product_map.get(ph.policy_type, "TERM-BC"))
    return (
        f"Policy: {ph.policy_product_name} ({ph.policy_number})\n"
        f"Type: {ph.policy_type} | Premium: ₹{ph.annual_premium:,.0f}/yr | "
        f"Sum Assured: ₹{ph.sum_assured:,.0f}\n"
        f"Renewal Due: {ph.renewal_due_date} | Tenure: {ph.years_as_customer} years\n"
        f"Loyalty Tier: {ph.loyalty_tier} | No-Claim Years: {ph.years_no_claim}\n"
        f"Last Payment: {ph.last_payment_status}\n"
        f"Product Details: {ps[:200]}..."
    )


# ── Main Escalation Entry Point ────────────────────────────────────────────────

def escalate(policy_id: str, escalation_reason: str) -> HumanBriefing:
    """
    Create a human briefing and add to queue.
    Automatically determines specialist type, priority, and SLA.
    """
    global _CASE_COUNTER
    ph = get_policyholder(policy_id)
    if not ph:
        raise ValueError(f"Policyholder {policy_id} not found.")

    memory = get_memory(policy_id)
    context_window = get_context_window(policy_id, last_n=10)
    sentiment = get_current_sentiment(policy_id)

    specialist = _determine_specialist(ph, escalation_reason)
    priority = _determine_priority(ph, escalation_reason)
    approach = _recommended_approach(ph, specialist, sentiment)
    policy_summary = _build_policy_summary(ph)

    # Distress SLA override
    sla = DISTRESS_ESCALATION_SLA_HRS if priority == "URGENT" else (
        4 if priority == "HIGH" else 24
    )

    # Summarize prior AI interactions
    turns = [{"role": t.role, "text": t.content, "channel": t.channel}
             for t in context_window]
    interaction_summary = summarize_interaction(policy_id, turns)

    case_id = f"HQ-{datetime.now().strftime('%Y%m%d')}-{_CASE_COUNTER:04d}"
    _CASE_COUNTER += 1

    briefing = HumanBriefing(
        case_id=case_id,
        policy_id=policy_id,
        policy_number=ph.policy_number,
        customer_name=ph.name,
        customer_age=ph.age,
        customer_language=ph.language,
        specialist_type=specialist,
        priority=priority,
        escalation_reason=escalation_reason,
        policy_summary=policy_summary,
        prior_ai_interactions=turns,
        detected_sentiment=sentiment,
        recommended_approach=approach,
        offers_already_shown=memory.offers_shown,
        objections_raised=memory.objections_raised,
        sla_hours=sla,
    )
    _QUEUE.append(briefing)

    print(
        f"  [HumanQueue] 🔔 Case {case_id} | {ph.name} → {specialist} | "
        f"Priority: {priority} | SLA: {sla}h | Reason: {escalation_reason[:60]}"
    )
    return briefing


# ── Queue Management API ──────────────────────────────────────────────────────

def get_queue() -> list[HumanBriefing]:
    return [b for b in _QUEUE if b.status == "OPEN"]


def get_urgent_cases() -> list[HumanBriefing]:
    return [b for b in _QUEUE if b.status == "OPEN" and b.priority == "URGENT"]


def resolve_case(case_id: str, resolution_note: str = "") -> Optional[HumanBriefing]:
    for b in _QUEUE:
        if b.case_id == case_id:
            b.status = "RESOLVED"
            if resolution_note:
                b.recommended_approach += f"\n\n[RESOLVED]: {resolution_note}"
            return b
    return None


def get_queue_stats() -> dict:
    all_cases = _QUEUE
    return {
        "total":      len(all_cases),
        "open":       len([b for b in all_cases if b.status == "OPEN"]),
        "urgent":     len([b for b in all_cases if b.priority == "URGENT" and b.status == "OPEN"]),
        "resolved":   len([b for b in all_cases if b.status == "RESOLVED"]),
        "by_specialist": {
            "SeniorRM":          len([b for b in all_cases if b.specialist_type == "SeniorRM"]),
            "RevivalSpecialist": len([b for b in all_cases if b.specialist_type == "RevivalSpecialist"]),
            "ComplianceHandler": len([b for b in all_cases if b.specialist_type == "ComplianceHandler"]),
        },
    }


def reset_queue() -> None:
    """Test/helper utility to clear queue and reset case numbering."""
    global _CASE_COUNTER
    _QUEUE.clear()
    _CASE_COUNTER = 1
