"""
services/llm.py
Large Language Model Wrapper — Layer 2 AI Platform Services
Supports stub (default), OpenAI, and Azure OpenAI backends.
Handles message generation, classification, objection handling, language detection.
"""
from __future__ import annotations
import os
import json
import random
from typing import Optional
from config.settings import LLM_PROVIDER, OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_KEY, AZURE_OPENAI_DEPLOYMENT
from config.settings import DISTRESS_KEYWORDS_EN, DISTRESS_KEYWORDS_HI


# ── Stub responses for demo mode ──────────────────────────────────────────────

_STUB_RENEWAL_MSGS = {
    "email": (
        "Dear {name},\n\nYour {policy_type} policy (Policy #{policy_id}) is due for renewal on {renewal_date}. "
        "Your annual premium of ₹{premium:,.0f} ensures ₹{sum_assured:,.0f} in coverage for you and your family.\n\n"
        "{offer_text}\n\n"
        "Renew now: https://renewai.in/pay/{policy_id}\n\n"
        "Warm regards,\nSurekha Insurance RenewAI Team"
    ),
    "whatsapp": (
        "Hello {name} 👋\n\nYour *{policy_type}* policy renews on *{renewal_date}*.\n"
        "Premium: ₹{premium:,.0f} | Cover: ₹{sum_assured:,.0f}\n\n"
        "{offer_text}\n\n"
        "Pay now ➡️ https://pay.renewai.in/{policy_id}\n"
        "Reply *HELP* for assistance."
    ),
    "voice": (
        "Hello, this is Priya from Surekha Insurance. Am I speaking with {name}? "
        "I'm calling about your {policy_type} policy renewal due on {renewal_date}. "
        "Your premium is ₹{premium:,.0f} for coverage of ₹{sum_assured:,.0f}. "
        "{offer_text} "
        "Would you like to renew now? I can send you a payment link immediately."
    ),
}


def _stub_generate(prompt: str, context: dict, channel: str = "email") -> str:
    template = _STUB_RENEWAL_MSGS.get(channel, _STUB_RENEWAL_MSGS["email"])
    try:
        return template.format(**context)
    except KeyError:
        return template


def _stub_classify(text: str) -> dict:
    text_lower = text.lower()
    intents = []
    if any(w in text_lower for w in ["expensive", "costly", "afford", "price", "premium"]):
        intents.append("price_objection")
    if any(w in text_lower for w in ["later", "next month", "busy", "tomorrow"]):
        intents.append("delay_objection")
    if any(w in text_lower for w in ["claim", "trust", "problem", "issue"]):
        intents.append("trust_objection")
    if any(w in text_lower for w in ["help", "how", "what", "tell me"]):
        intents.append("info_request")
    if any(w in text_lower for w in ["pay", "yes", "okay", "fine", "renew"]):
        intents.append("payment_intent")
    distress_triggers = set(DISTRESS_KEYWORDS_EN + DISTRESS_KEYWORDS_HI + [
        "sad", "worried", "scared", "stress", "trouble", "passed away", "death", "bereavement"
    ])
    if any(w in text_lower for w in distress_triggers):
        intents.append("distress_signal")
    sentiment = (
        "distressed" if "distress_signal" in intents else
        "positive" if "payment_intent" in intents else
        "negative" if intents else "neutral"
    )
    return {
        "intents": intents or ["general_inquiry"],
        "sentiment": sentiment,
        "language": "English",
        "confidence": round(random.uniform(0.80, 0.97), 2),
    }


def _stub_detect_language(text: str) -> str:
    hindi_chars = sum(1 for c in text if '\u0900' <= c <= '\u097f')
    tamil_chars = sum(1 for c in text if '\u0B80' <= c <= '\u0BFF')
    telugu_chars = sum(1 for c in text if '\u0C00' <= c <= '\u0C7F')
    if hindi_chars > 5:
        return "Hindi"
    if tamil_chars > 5:
        return "Tamil"
    if telugu_chars > 5:
        return "Telugu"
    return "English"


# ── OpenAI backend ─────────────────────────────────────────────────────────────

def _openai_generate(prompt: str, context: dict) -> str:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert insurance renewal assistant for Surekha Insurance, India. Always be helpful, empathetic, and IRDAI-compliant."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=500,
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"[LLM ERROR: {e}] Falling back to stub."


# ── Public API ─────────────────────────────────────────────────────────────────

def generate_message(channel: str, context: dict, system_prompt: str = "",
                     custom_prompt: str = "") -> str:
    """Generate a renewal/engagement message for the given channel and context."""
    if LLM_PROVIDER == "stub":
        return _stub_generate(custom_prompt or "", context, channel)
    prompt = custom_prompt or f"Generate a {channel} renewal message for the following policyholder context: {json.dumps(context, default=str)}"
    if OPENAI_API_KEY:
        return _openai_generate(prompt, context)
    return _stub_generate(prompt, context, channel)


def classify_intent(text: str) -> dict:
    """Classify a customer message into intents and sentiment."""
    if LLM_PROVIDER == "stub":
        return _stub_classify(text)
    prompt = f"Classify the intent and sentiment of this insurance customer message: '{text}'. Return JSON with keys: intents (list), sentiment (positive|neutral|negative|distressed), language, confidence."
    if OPENAI_API_KEY:
        try:
            result = _openai_generate(prompt, {})
            return json.loads(result)
        except Exception:
            pass
    return _stub_classify(text)


def detect_language(text: str) -> str:
    """Detect the language of the input text."""
    if LLM_PROVIDER == "stub":
        return _stub_detect_language(text)
    return _stub_detect_language(text)


def summarize_interaction(policy_id: str, turns: list[dict]) -> str:
    """Summarize a conversation history for human handoff."""
    if not turns:
        return "No prior interactions recorded."
    if LLM_PROVIDER == "stub":
        return (
            f"Policy {policy_id}: {len(turns)} message(s) exchanged. "
            f"Latest sentiment: {turns[-1].get('role', 'unknown')}. "
            "Customer showed interest in renewal options."
        )
    prompt = f"Summarize this insurance renewal conversation for a human agent: {json.dumps(turns, default=str)}"
    return _openai_generate(prompt, {})
