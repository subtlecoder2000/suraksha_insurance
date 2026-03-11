"""
services/voice_engine.py
AI Voice Engine — Layer 2 AI Platform Services
Multi-language STT/TTS, real-time transcription, intent extraction, script adaptation.
Stub mode simulates call transcripts. Real mode uses Azure Cognitive Services.
"""
from __future__ import annotations
import random
from dataclasses import dataclass
from config.settings import VOICE_STUB
from config.languages import LANGUAGES, GREETING
from services.llm import classify_intent


@dataclass
class CallSession:
    call_id: str
    policy_id: str
    language: str
    transcript: list[dict]   # [{"role": "agent"|"customer", "text": str}]
    intent_detected: str
    sentiment: str
    outcome: str              # connected | voicemail | rejected | completed | escalated
    duration_seconds: int


@dataclass
class VoiceScript:
    language: str
    greeting: str
    intro: str
    renewal_ask: str
    objection_handler: str
    payment_offer: str
    closing: str


def get_script(language: str, context: dict) -> VoiceScript:
    """Generate a voice script adapted for the given language and context."""
    greeting = GREETING.get(language, "Hello")
    name = context.get("name", "Valued Customer")
    renewal_date = context.get("renewal_date", "soon")
    premium = context.get("premium", 0)
    offer_text = context.get("offer_text", "")

    if language == "Hindi":
        return VoiceScript(
            language=language,
            greeting=f"{greeting} {name} ji,",
            intro=f"Main Suraksha Insurance se Priya bol rahi hoon.",
            renewal_ask=(
                f"Aapki policy {renewal_date} ko renew hone wali hai. "
                f"Annual premium ₹{premium:,.0f} hai."
            ),
            objection_handler="Aapki baat sunna chahti hoon — kya koi concern hai?",
            payment_offer=f"{offer_text} Kya main abhi UPI payment link bhejoon?",
            closing="Dhanyavaad! Suraksha Insurance mein vishwas rakhne ke liye shukriya.",
        )
    # Default English
    return VoiceScript(
        language="English",
        greeting=f"{greeting} {name},",
        intro="This is Priya calling from Suraksha Insurance.",
        renewal_ask=(
            f"Your policy is due for renewal on {renewal_date}. "
            f"Your annual premium is ₹{premium:,.0f}."
        ),
        objection_handler="I'd love to understand your concerns — what's on your mind?",
        payment_offer=f"{offer_text} May I send you a UPI payment link right now?",
        closing="Thank you for being a valued Suraksha Insurance customer!",
    )


def simulate_call(policy_id: str, language: str, context: dict) -> CallSession:
    """
    Simulate an outbound AI voice call.
    In stub mode: generates synthetic transcript.
    In real mode: would trigger Azure telephony + STT/TTS.
    """
    import uuid
    call_id = f"CALL-{uuid.uuid4().hex[:8].upper()}"
    script = get_script(language, context)

    # Simulate customer responses
    customer_responses = [
        "Haan, kaun bol raha hai?" if language == "Hindi" else "Yes, who is this?",
        "Okay, samajh gaya." if language == "Hindi" else "Okay, I understand.",
        random.choice([
            "Premium thoda zyada lagta hai." if language == "Hindi" else "The premium seems a bit high.",
            "Theek hai, link bhejo." if language == "Hindi" else "Okay, send me the link.",
            "Sochna padega." if language == "Hindi" else "Let me think about it.",
        ]),
    ]

    transcript = [
        {"role": "agent",    "text": f"{script.greeting} {script.intro}"},
        {"role": "customer", "text": customer_responses[0]},
        {"role": "agent",    "text": script.renewal_ask},
        {"role": "customer", "text": customer_responses[1]},
        {"role": "agent",    "text": f"{script.payment_offer}"},
        {"role": "customer", "text": customer_responses[2]},
        {"role": "agent",    "text": script.closing},
    ]

    # Detect intent from last customer response
    last_response = customer_responses[-1]
    classification = classify_intent(last_response)

    outcome = "completed"
    if "payment_intent" in classification["intents"]:
        outcome = "payment_link_sent"
    elif classification["sentiment"] == "distressed":
        outcome = "escalated"

    return CallSession(
        call_id=call_id,
        policy_id=policy_id,
        language=language,
        transcript=transcript,
        intent_detected=", ".join(classification["intents"]),
        sentiment=classification["sentiment"],
        outcome=outcome,
        duration_seconds=random.randint(45, 180),
    )


def text_to_speech_stub(text: str, language: str) -> str:
    """Stub: returns a description of TTS output."""
    lang_info = LANGUAGES.get(language, LANGUAGES["English"])
    return f"[TTS: {lang_info['tts']} | '{text[:60]}...']"


def speech_to_text_stub(audio_path: str, language: str) -> str:
    """Stub: simulates STT transcription."""
    return f"[STT transcription of {audio_path} in {language}]"
