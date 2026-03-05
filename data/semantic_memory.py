"""
data/semantic_memory.py
Semantic Memory Store — Layer 1 Data & Integration
Stores customer intent history, conversation context, and channel engagement signals.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class ConversationTurn:
    role: str           # user | assistant | system
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    channel: str = "unknown"
    language: str = "English"


@dataclass
class CustomerMemory:
    policy_id: str
    intents_detected: list[str] = field(default_factory=list)    # objection | payment_intent | info_request | distress
    sentiment_history: list[str] = field(default_factory=list)   # positive | neutral | negative | distressed
    conversation_turns: list[ConversationTurn] = field(default_factory=list)
    engagement_signals: dict = field(default_factory=dict)        # {channel: {opens, clicks, replies}}
    last_contact_channel: Optional[str] = None
    last_contact_time: Optional[datetime] = None
    objections_raised: list[str] = field(default_factory=list)
    offers_shown: list[str] = field(default_factory=list)


_MEMORY_STORE: dict[str, CustomerMemory] = {}


# ── Public API ─────────────────────────────────────────────────────────────────

def get_memory(policy_id: str) -> CustomerMemory:
    if policy_id not in _MEMORY_STORE:
        _MEMORY_STORE[policy_id] = CustomerMemory(policy_id=policy_id)
    return _MEMORY_STORE[policy_id]


def add_turn(policy_id: str, role: str, content: str,
             channel: str = "unknown", language: str = "English") -> None:
    mem = get_memory(policy_id)
    mem.conversation_turns.append(
        ConversationTurn(role=role, content=content, channel=channel, language=language)
    )
    mem.last_contact_channel = channel
    mem.last_contact_time = datetime.now()


def record_intent(policy_id: str, intent: str) -> None:
    mem = get_memory(policy_id)
    if intent not in mem.intents_detected:
        mem.intents_detected.append(intent)


def record_sentiment(policy_id: str, sentiment: str) -> None:
    get_memory(policy_id).sentiment_history.append(sentiment)


def record_objection(policy_id: str, objection: str) -> None:
    mem = get_memory(policy_id)
    if objection not in mem.objections_raised:
        mem.objections_raised.append(objection)


def record_offer_shown(policy_id: str, offer: str) -> None:
    mem = get_memory(policy_id)
    if offer not in mem.offers_shown:
        mem.offers_shown.append(offer)


def get_context_window(policy_id: str, last_n: int = 5) -> list[ConversationTurn]:
    return get_memory(policy_id).conversation_turns[-last_n:]


def get_current_sentiment(policy_id: str) -> str:
    history = get_memory(policy_id).sentiment_history
    return history[-1] if history else "neutral"


def is_distressed(policy_id: str) -> bool:
    return get_current_sentiment(policy_id) == "distressed"


def reset_memory_store() -> None:
    """Test/helper utility to clear all in-memory customer memory."""
    _MEMORY_STORE.clear()
