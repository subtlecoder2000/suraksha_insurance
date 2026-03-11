"""
agents/email_agent.py
Email Agent — Layer 3 Agentic AI Layer
Personalized renewal emails, 3 nudges per segment, loyalty offers, escalation rules.

NOW WITH REAL SMTP EMAIL SENDING! 📧
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from services.llm import generate_message
from services.rag_retrieval import retrieve_policy_context
from services.email_service import get_email_service
from data.semantic_memory import add_turn, record_offer_shown
import logging

logger = logging.getLogger(__name__)


@dataclass
class EmailResult:
    policy_id: str
    recipient_name: str
    recipient_email: str
    subject: str
    body: str
    nudge_number: int        # 1 | 2 | 3
    offer_ids: list[str]
    sent_at: datetime
    escalate: bool = False
    escalation_reason: str = ""
    smtp_result: dict = None  # NEW: SMTP delivery status


def _build_subject(context: dict, nudge_number: int, tone: str) -> str:
    name = context.get("name", "Valued Customer")
    days_left = context.get("days_left", 0)
    discount = context.get("discount_pct", 0)
    if nudge_number == 1:
        if discount > 0:
            return f"🎁 You qualify for {discount}% discount — Renew your policy today, {name.split()[0]}"
        return f"Your policy renewal is coming up, {name.split()[0]} — Renew in 60 seconds"
    elif nudge_number == 2:
        return f"⏰ {days_left} days left — Don't let your coverage lapse, {name.split()[0]}"
    else:  # nudge 3
        return f"🚨 FINAL REMINDER: Policy expires soon — {name.split()[0]}, act now"


def _build_body(context: dict, nudge_number: int, tone: str, channel: str = "email") -> str:
    greeting = "Dear" if tone == "professional" else "Hello"
    name = context.get("name", "Customer")
    policy_id = context.get("policy_id", "")
    policy_type = context.get("policy_type", "")
    premium = context.get("premium", 0)
    sum_assured = context.get("sum_assured", 0)
    renewal_date = context.get("renewal_date", "")
    offer_text = context.get("offer_text", "")
    days_left = context.get("days_left", 0)

    segment = context.get("segment", "Standard")
    base = generate_message(channel, context)

    segment_bonus = ""
    if segment == "Wealth Builder":
        segment_bonus = "\nAs a Wealth Builder, securing your legacy is paramount. Our priority wealth management team is always available for you."
    elif segment == "Budget Conscious":
        segment_bonus = "\nWe know how important value is. Renew now to lock in these budget-friendly savings and maximum coverage."

    base += segment_bonus

    nudge_extras = {
        1: "\n\nRenew now and enjoy uninterrupted protection for you and your family.",
        2: (
            f"\n\n⚠️ Only {days_left} days remaining. After the grace period, "
            "your policy will lapse and a fresh medical check-up may be required for revival."
        ),
        3: (
            "\n\n🚨 This is your final reminder. Renewing today takes less than 2 minutes "
            "via UPI, NetBanking, or Credit Card. If you need assistance, reply to this email "
            "or call 1800-XXX-XXXX (toll free)."
        ),
    }
    return base + nudge_extras.get(nudge_number, "")


def send_email(
    policy_id: str,
    email: str,
    context: dict,
    tone: str = "friendly",
    nudge_number: int = 1,
    offer_ids: list[str] = None,
    deliver: bool = True,
) -> EmailResult:
    """
    Generate and optionally SEND a renewal email via SMTP.
    Set deliver=False to only generate (e.g. for critique gate).
    """
    subject = _build_subject(context, nudge_number, tone)
    body = _build_body(context, nudge_number, tone, "email")

    # Record in memory
    add_turn(policy_id, "assistant", f"[EMAIL] Subject: {subject}", channel="email",
             language=context.get("language", "English"))

    if context.get("offer_text"):
        record_offer_shown(policy_id, context["offer_text"][:50])

    # Tracking & Follow-up Escalation logic
    # Simulated email_metrics from system
    email_metrics = context.get("email_metrics", {"opens": 0, "link_errors": 0, "complaints": 0})
    
    escalate = False
    escalation_reason = ""
    
    if nudge_number >= 3 and email_metrics.get("opens", 0) == 0:
        escalate = True
        escalation_reason = "No open after 3 attempts"
    elif email_metrics.get("link_errors", 0) > 0:
        escalate = True
        escalation_reason = "payment link error"
    elif email_metrics.get("complaints", 0) > 0:
        escalate = True
        escalation_reason = "customer reply with complaint"
    elif nudge_number >= 3 and context.get("days_left", 30) <= 3:
        escalate = True
        escalation_reason = "Urgent pending lapse"
    
    # ═══════════════════════════════════════════════════════════════
    # NEW: ACTUALLY SEND EMAIL VIA SMTP! 🚀 (Only if deliver=True)
    # ═══════════════════════════════════════════════════════════════
    smtp_result = None
    if deliver:
        smtp_result = deliver_email_result(policy_id, email, context, nudge_number, offer_ids)
    # ═══════════════════════════════════════════════════════════════

    result = EmailResult(
        policy_id=policy_id,
        recipient_name=context.get("name", ""),
        recipient_email=email,
        subject=subject,
        body=body,
        nudge_number=nudge_number,
        offer_ids=offer_ids or [],
        sent_at=datetime.now(),
        escalate=escalate,
        escalation_reason=escalation_reason,
        smtp_result=smtp_result  # Include SMTP delivery status
    )
    
    return result


def deliver_email_result(
    policy_id: str,
    email: str,
    context: dict,
    nudge_number: int = 1,
    offer_ids: list[str] = None,
) -> dict:
    """Handle actual SMTP delivery of an already generated/critiqued email intent."""
    email_service = get_email_service()
    
    # Prepare offers list for template
    offers = []
    if context.get("discount_pct", 0) > 0:
        offers.append(f"{int(context['discount_pct'] * 100)}% No-Claim Discount")
    if context.get("autopay_cashback", 0) > 0:
        offers.append(f"₹{context['autopay_cashback']} AutoPay Cashback")
    if not offers:
        offers = ["Loyalty Bonus: 5% extra coverage", "24/7 Priority Support"]
    
    # Send via SMTP
    smtp_result = email_service.send_renewal_email(
        customer_name=context.get("name", "Customer"),
        customer_email=email,
        policy_number=policy_id,
        policy_type=context.get("policy_type", "Life Insurance Policy"),
        premium_amount=context.get("premium", 0),
        due_date=context.get("renewal_date", "Soon"),
        sum_assured=context.get("sum_assured", 0),
        offers=offers,
        payment_link=f"https://pay.suraksha.in/{policy_id}",
        language=context.get("language", "en")
    )
    
    if smtp_result.get('success'):
        logger.info(f"✅ Email DELIVERED to {email}")
        print(f"  [EmailAgent] ✉️  DELIVERED nudge #{nudge_number} to {email}")
    else:
        logger.error(f"❌ Email FAILED to {email}: {smtp_result.get('error')}")
    
    return smtp_result
