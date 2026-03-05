"""
agents/whatsapp_agent.py
WhatsApp Agent — Layer 3 Agentic AI Layer
Business API flows, UPI/QR payment, intent detection, loyalty messages, escalation rules.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from services.llm import generate_message, classify_intent
from data.semantic_memory import add_turn, record_intent, record_sentiment, record_objection
from data.payment_gateway import generate_upi_qr
from services.rag_retrieval import retrieve_objection_response


@dataclass
class WhatsAppMessage:
    policy_id: str
    to_number: str
    message_type: str       # text | template | list | button | media
    body: str
    upi_qr: dict = None
    buttons: list[str] = None
    sent_at: datetime = None
    delivery_status: str = "sent"   # sent | delivered | read | failed
    escalate: bool = False


def _build_wa_message(context: dict, tone: str) -> str:
    name = context.get("name", "").split()[0]
    premium = context.get("premium", 0)
    renewal_date = context.get("renewal_date", "")
    offer_text = context.get("offer_text", "")
    days_left = context.get("days_left", 0)
    policy_id = context.get("policy_id", "")

    urgency = "⚠️ " if days_left <= 7 else ""
    offer_line = f"\n🎁 *Special Offer:* {offer_text}" if offer_text else ""

    autopay_line = ""
    if context.get("offer_ecs_autopay"):
        autopay_line = (
            "\n⚡ Set up *AutoPay/ECS* today to avoid missing future renewals and get cashback benefits."
        )

    return (
        f"{urgency}Hello *{name}* 👋\n\n"
        f"Your *{context.get('policy_type')} policy* is due for renewal on *{renewal_date}*.\n"
        f"💰 Premium: *₹{premium:,.0f}* | 🛡️ Cover: *₹{context.get('sum_assured', 0):,.0f}*\n"
        f"{offer_line}\n\n"
        f"{autopay_line}\n"
        f"Pay instantly 👇\n"
        f"Reply *PAY* for UPI link | *EMI* for installment options | *CALL* for callback | *STOP* to opt out"
    )


def send_whatsapp(
    policy_id: str,
    phone: str,
    context: dict,
    tone: str = "friendly",
    include_qr: bool = True,
) -> WhatsAppMessage:
    """Send (stub) a WhatsApp renewal message with optional UPI QR."""
    body = _build_wa_message(context, tone)
    qr = None
    if include_qr:
        qr = generate_upi_qr(policy_id, context.get("premium", 0))

    buttons = ["✅ Pay Now", "📞 Call Me", "❓ More Info"]
    add_turn(policy_id, "assistant", body, channel="whatsapp",
             language=context.get("language", "English"))

    msg = WhatsAppMessage(
        policy_id=policy_id,
        to_number=phone,
        message_type="button",
        body=body,
        upi_qr=qr,
        buttons=buttons,
        sent_at=datetime.now(),
    )
    print(f"  [WhatsAppAgent] 💬 Sent WA message to {phone} | {body[:80].strip()!r}")
    return msg


def handle_reply(policy_id: str, phone: str, customer_text: str, context: dict) -> WhatsAppMessage:
    """Handle a customer reply on WhatsApp — classify intent and respond."""
    add_turn(policy_id, "user", customer_text, channel="whatsapp")
    classification = classify_intent(customer_text)
    intents = classification["intents"]
    sentiment = classification["sentiment"]

    record_intent(policy_id, intents[0] if intents else "general")
    record_sentiment(policy_id, sentiment)

    escalate = False
    response_body = ""
    qr = None
    text = customer_text.lower()

    if any(k in text for k in ("emi", "installment", "instalment", "split payment", "part payment")):
        part = context.get("emi_amount", round(context.get("premium", 0) / 3, 2))
        qr = generate_upi_qr(policy_id, part)
        response_body = (
            "Absolutely. You can choose a flexible payment plan:\n"
            f"• 3-part plan: ₹{part:,.0f} x 3 months\n"
            f"• Pay first part now: 👉 {qr['deeplink']}\n\n"
            "Reply *CALL* if you want an advisor to confirm installment setup."
        )
    elif "payment_intent" in intents or "PAY" in customer_text.upper():
        qr = generate_upi_qr(policy_id, context.get("premium", 0))
        response_body = (
            f"Great! 🎉 Here's your payment link:\n"
            f"👉 {qr['deeplink']}\n\n"
            f"Amount: ₹{context.get('premium', 0):,.0f} | Expires in 30 mins.\n"
            f"After payment, your policy renews instantly ✅"
        )
    elif "price_objection" in intents:
        objection_resp = retrieve_objection_response(
            customer_text, language=context.get("language", "English"),
            segment=context.get("segment"), context=context
        )
        record_objection(policy_id, customer_text[:80])
        response_body = f"I understand 😊\n\n{objection_resp}"
    elif any(k in text for k in ("call", "callback", "speak to", "talk to")):
        response_body = (
            "Sure, I can arrange a callback from our renewal specialist.\n"
            "Please share your preferred slot: *Morning (9-12)*, *Afternoon (1-5)*, or *Evening (5-8)*."
        )
    elif sentiment == "distressed":
        escalate = True
        response_body = (
            "I'm really sorry to hear that. 💙 Let me connect you with a dedicated specialist "
            "who can personally assist you. You'll receive a call within the next 2 hours."
        )
    else:
        response_body = (
            "Thanks for reaching out! 😊 Our team is here to help.\n\n"
            "Reply *PAY* to pay now, *CALL* to request a callback, or *HELP* for FAQs."
        )

    add_turn(policy_id, "assistant", response_body, channel="whatsapp")
    msg = WhatsAppMessage(
        policy_id=policy_id,
        to_number=phone,
        message_type="text",
        body=response_body,
        upi_qr=qr,
        sent_at=datetime.now(),
        escalate=escalate,
    )
    print(f"  [WhatsAppAgent] 💬 Reply sent | Escalate: {escalate}")
    return msg
