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
    deliver: bool = True,
) -> WhatsAppMessage:
    """
    Generate and optionally SEND a WhatsApp renewal message.
    Set deliver=False to only draft for critique.
    """
    body = _build_wa_message(context, tone)
    qr = None
    if include_qr:
        qr = generate_upi_qr(policy_id, context.get("premium", 0))

    buttons = ["✅ Pay Now", "📞 Call Me", "❓ More Info"]
    add_turn(policy_id, "assistant", body, channel="whatsapp",
             language=context.get("language", "English"))

    if deliver:
        print(f"  [WhatsAppAgent] 💬 Sent WA message to {phone} | {body[:80].strip()!r}")

    msg = WhatsAppMessage(
        policy_id=policy_id,
        to_number=phone,
        message_type="button",
        body=body,
        upi_qr=qr,
        buttons=buttons,
        sent_at=datetime.now(),
    )
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

    if any(k in text for k in ("emi", "installment", "instalment", "split payment", "part payment", "pay later")):
        part = context.get("emi_amount", round(context.get("premium", 0) / 3, 2))
        qr = generate_upi_qr(policy_id, part)
        response_body = (
            "Absolutely. You can choose a flexible payment plan:\n"
            f"• 3-part plan: ₹{part:,.0f} x 3 months\n"
            f"• Pay first part now: 👉 {qr['deeplink']}\n\n"
            "Reply *CALL* if you want an advisor to confirm installment setup."
        )
    elif "payment_intent" in intents or "PAY" in customer_text.upper() or "RECEIPT" in customer_text.upper():
        qr = generate_upi_qr(policy_id, context.get("premium", 0))
        response_body = (
            f"Great! 🎉 Here's your payment link:\n"
            f"👉 {qr['deeplink']}\n\n"
            f"Amount: ₹{context.get('premium', 0):,.0f} | Expires in 30 mins.\n"
            f"After payment, your policy renews instantly ✅. (If you have a receipt, simply upload it here for parsing)."
        )
    elif "help" in text or "faq" in text or "options" in text:
        response_body = (
            "I'm here to assist you! 😊 Here are a few things I can help with:\n\n"
            "• *POLICY* - View your policy summary and coverage\n"
            "• *PAY* - Get a quick payment link\n"
            "• *EMI* - View flexible installment plans\n"
            "• *CALL* - Request a callback from an expert\n"
            "• *OFFER* - Check your personalized loyalty benefits\n\n"
            "Just reply with any of the keywords above!"
        )
    elif any(k in text for k in ("policy", "details", "cover", "product", "sum assured", "summary")):
        response_body = (
            f"📄 *Policy Summary for {context.get('name')}*\n\n"
            f"• *Product:* {context.get('policy_product')}\n"
            f"• *Policy No:* {context.get('policy_number')}\n"
            f"• *Type:* {context.get('policy_type')}\n"
            f"• *Sum Assured:* ₹{context.get('sum_assured', 0):,.0f}\n"
            f"• *Renewal Due:* {context.get('renewal_date')}\n"
            f"• *Premium:* ₹{context.get('premium', 0):,.0f}\n\n"
            "Would you like to *PAY* now or view *EMI* options?"
        )
    elif any(k in text for k in ("morning", "afternoon", "evening")) and "call" not in text:
        # Acknowledge the slot
        slot = "Evening (5-8 PM)" if "evening" in text else ("Morning (9-12 AM)" if "morning" in text else "Afternoon (1-5 PM)")
        response_body = (
            f"✅ Confirmed! I've scheduled your callback for the *{slot}* slot.\n\n"
            "A renewal specialist will call you on this number. Is there anything else I can help with in the meantime?"
        )
    elif "price_objection" in intents or "delay_objection" in intents or "not renewing" in text:
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
    elif sentiment in ("distressed", "negative") or any(k in text for k in ("hardship", "illness", "hospital", "dispute", "complaint", "fraud")):
        escalate = True
        response_body = (
            "I'm really sorry to hear that. 💙 Let me connect you with a dedicated specialist "
            "who can personally assist you with this matter. You'll receive a call shortly."
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
