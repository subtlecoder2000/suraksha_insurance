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

    base = generate_message(channel, context)

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
) -> EmailResult:
    """
    Generate and ACTUALLY SEND a renewal email via SMTP
    
    This now sends REAL emails using the configured SMTP service!
    """
    subject = _build_subject(context, nudge_number, tone)
    body = _build_body(context, nudge_number, tone, "email")

    # Record in memory
    add_turn(policy_id, "assistant", f"[EMAIL] Subject: {subject}", channel="email",
             language=context.get("language", "English"))

    if context.get("offer_text"):
        record_offer_shown(policy_id, context["offer_text"][:50])

    escalate = nudge_number >= 3 and context.get("days_left", 30) <= 3
    
    # ═══════════════════════════════════════════════════════════════
    # NEW: ACTUALLY SEND EMAIL VIA SMTP! 🚀
    # ═══════════════════════════════════════════════════════════════
    email_service = get_email_service()
    
    # Prepare offers list for template
    offers = []
    if context.get("discount_pct", 0) > 0:
        offers.append(f"{context['discount_pct']}% No-Claim Discount")
    if context.get("autopay_cashback", 0) > 0:
        offers.append(f"₹{context['autopay_cashback']} AutoPay Cashback")
    if not offers:
        offers = ["Loyalty Bonus: 5% extra coverage", "24/7 Priority Support"]
    
    # Send via SMTP using beautiful HTML template
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
    
    # Log result
    if smtp_result.get('success'):
        logger.info(f"✅ Email DELIVERED to {email} via {smtp_result.get('provider', 'SMTP')}")
        print(f"  [EmailAgent] ✉️  SENT nudge #{nudge_number} to {email} | Subject: {subject[:60]}")
        print(f"  [EmailAgent] 🎯 Message ID: {smtp_result.get('message_id')}")
    else:
        logger.error(f"❌ Email FAILED to {email}: {smtp_result.get('error')}")
        print(f"  [EmailAgent] ❌ FAILED to {email}: {smtp_result.get('message')}")
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
        smtp_result=smtp_result  # Include SMTP delivery status
    )
    
    return result
