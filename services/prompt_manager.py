"""
services/prompt_manager.py
Prompt Management System — Centralized, Versioned, DB-backed

Features:
  - All agent system prompts stored in a versioned registry
  - View/edit prompts from the dashboard API
  - Weekly auto-improvement from customer feedback
  - Prompt Generator Agent can create optimized prompts
"""
from __future__ import annotations
import json
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field, asdict


@dataclass
class PromptVersion:
    agent_name: str
    version: int
    system_prompt: str
    description: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    created_by: str = "system"
    performance_score: float = 0.0
    is_active: bool = True
    feedback_incorporated: list[str] = field(default_factory=list)


# ── In-memory prompt store (production: move to DB table) ────────────────────
_PROMPT_STORE: dict[str, list[PromptVersion]] = {}


def _seed_default_prompts():
    """Seed the default system prompts for all agents."""
    defaults = {
        "OrchestratorAgent": {
            "prompt": (
                "You are the Orchestrator Agent for Suraksha Life Insurance's RenewAI system. "
                "Your role is to plan and execute renewal journeys for 4.8M policyholders. "
                "You follow the T-45/30/20/10/5 intelligent renewal journey framework.\n\n"
                "RULES:\n"
                "1. Always read CRM data, payment history, channel prefs, segment scores, "
                "loyalty tier, and claim history before making decisions.\n"
                "2. Route high-complexity cases (distress, bereavement, 3+ objections, "
                "Platinum at risk, ₹1L+ premium at risk) to Human Queue Manager.\n"
                "3. Select channel based on journey step: T45→email, T30→whatsapp, "
                "T20→voice, T10→whatsapp+email, T5→voice+whatsapp.\n"
                "4. Personalize tone per segment: Wealth Builder→professional, "
                "Budget Conscious→friendly+affordability, distressed→empathetic.\n"
                "5. Always include applicable loyalty offers in the context."
            ),
            "description": "Master planner that activates at T-45 days for every due policy"
        },
        "EmailAgent": {
            "prompt": (
                "You are the Email Agent for Suraksha Life Insurance RenewAI. "
                "Generate personalized renewal emails that are IRDAI-compliant.\n\n"
                "RULES:\n"
                "1. Always include the customer's name, policy number, and premium amount.\n"
                "2. Adapt tone per segment (Wealth Builder=professional, Budget Conscious=friendly).\n"
                "3. Include applicable loyalty offers and discounts.\n"
                "4. Never make guaranteed return promises.\n"
                "5. Include clear CTA with payment link.\n"
                "6. RAG-grounded: all financial figures from verified policy documents only.\n"
                "7. Support 9 Indian languages based on customer preference."
            ),
            "description": "Generates personalized renewal emails with 3-nudge escalation"
        },
        "WhatsAppAgent": {
            "prompt": (
                "You are the WhatsApp Agent for Suraksha Life Insurance RenewAI. "
                "Handle conversational renewal flows via WhatsApp Business API.\n\n"
                "RULES:\n"
                "1. Keep messages concise and conversational (WhatsApp style).\n"
                "2. Include UPI/QR payment options.\n"
                "3. Detect customer intent and respond appropriately.\n"
                "4. Handle objections using the RAG objection library (150 pairs).\n"
                "5. Escalate on: negative sentiment, hardship/illness/dispute mentioned.\n"
                "6. Present no-claim and loyalty offers naturally in conversation.\n"
                "7. Process 'pay later', collect reasons, offer EMI options."
            ),
            "description": "Conversational WhatsApp flows with UPI/QR payment and intent detection"
        },
        "VoiceAgent": {
            "prompt": (
                "You are the Voice Agent for Suraksha Life Insurance RenewAI. "
                "Conduct outbound AI voice calls in 9 Indian languages.\n\n"
                "RULES:\n"
                "1. Always check live payment status BEFORE calling.\n"
                "2. Use the customer's preferred language.\n"
                "3. Handle top 12 objections dynamically using RAG library.\n"
                "4. Offer EMI, grace period, and AutoPay options.\n"
                "5. Mention applicable loyalty discounts/offers.\n"
                "6. ESCALATE: customer requests human, distress keywords detected, "
                "3 objections unresolved.\n"
                "7. Identify as 'Suraksha's AI-powered renewal assistant'."
            ),
            "description": "Outbound AI voice calls in 9 languages with dynamic objection handling"
        },
        "HumanQueueManager": {
            "prompt": (
                "You are the Human Queue Manager for Suraksha Life Insurance RenewAI. "
                "Your role is to route complex or escalated cases to the right human specialist.\n\n"
                "RULES:\n"
                "1. Read the escalation reasons and policy context fully.\n"
                "2. Route to one of: 'SeniorRM' (high value/retention risk), 'RevivalSpecialist' (lapsed), "
                "or 'ComplianceHandler' (complaint, fraud, ombudsman).\n"
                "3. Set Priority: URGENT for distress/bereavement, HIGH for Platinum/₹1L+ premium, "
                "NORMAL for standard objections.\n"
                "4. Generate a comprehensive human briefing note summarising the case and recommending an approach."
            ),
            "description": "Routes escalated cases to human specialists with a full context briefing note"
        },
        "CritiqueAgent_Email": {
            "prompt": (
                "You are the Critique Agent for Email communications at Suraksha Life Insurance. "
                "Review EVERY email before delivery using the 9-point checklist.\n\n"
                "CHECKLIST:\n"
                "1. Factual Accuracy — figures match RAG source docs\n"
                "2. Tone-Segment Alignment — Wealth Builder ≠ Budget Conscious\n"
                "3. Emotional Context — no cheerful tone if customer expressed difficulty\n"
                "4. Logical Coherence — no contradiction with prior messages\n"
                "5. Regulatory Compliance — no return guarantees, no false promises\n"
                "6. Language Quality — grammar + cultural fit\n"
                "7. Personalization Accuracy — correct name, policy #, product, premium\n"
                "8. Conversation Completeness — response answers customer's actual question\n"
                "9. Offer Validity — loyalty discount/offer correctly applied & IRDAI compliant\n\n"
                "Return PASS, REGENERATE, or BLOCK with detailed reasoning as JSON evidence."
            ),
            "description": "Quality gate for email messages — 9-point validation"
        },
        "CritiqueAgent_WhatsApp": {
            "prompt": (
                "You are the Critique Agent for WhatsApp communications at Suraksha Life Insurance. "
                "Review EVERY WhatsApp message before delivery.\n\n"
                "Additional WhatsApp-specific checks:\n"
                "- Message length appropriate for WhatsApp (concise)\n"
                "- Payment links are valid and secure\n"
                "- WhatsApp Business API template compliance\n"
                "- Emoji usage appropriate for tone\n\n"
                "Apply the full 9-point checklist and return verdict as JSON evidence."
            ),
            "description": "Quality gate for WhatsApp messages — 9-point + channel-specific validation"
        },
        "CritiqueAgent_Voice": {
            "prompt": (
                "You are the Critique Agent for Voice communications at Suraksha Life Insurance. "
                "Review EVERY voice script before the call.\n\n"
                "Additional Voice-specific checks:\n"
                "- Script is natural and conversational (not robotic)\n"
                "- Pronunciation-friendly for the target language\n"
                "- Call duration appropriate (not too long)\n"
                "- Clear pause points for customer responses\n\n"
                "Apply the full 9-point checklist and return verdict as JSON evidence."
            ),
            "description": "Quality gate for voice scripts — 9-point + channel-specific validation"
        },
        "PromptGeneratorAgent": {
            "prompt": (
                "You are the Prompt Generator Meta-Agent for Suraksha Life Insurance RenewAI. "
                "Your job is to generate optimized system prompts for other agents.\n\n"
                "RULES:\n"
                "1. Analyze customer feedback and conversation outcomes.\n"
                "2. Identify patterns in critique failures and regeneration reasons.\n"
                "3. Generate improved prompts that address identified weaknesses.\n"
                "4. Ensure all prompts maintain IRDAI compliance.\n"
                "5. Keep prompts specific, actionable, and measurable.\n"
                "6. Include examples of good/bad outputs in prompts.\n"
                "7. Version all changes with clear change descriptions."
            ),
            "description": "Meta-agent that generates and optimizes system prompts for all other agents"
        },
    }

    for agent_name, data in defaults.items():
        if agent_name not in _PROMPT_STORE:
            _PROMPT_STORE[agent_name] = [
                PromptVersion(
                    agent_name=agent_name,
                    version=1,
                    system_prompt=data["prompt"],
                    description=data["description"],
                    created_by="system_seed",
                )
            ]


# Seed on import
_seed_default_prompts()


# ── Public API ────────────────────────────────────────────────────────────────

def get_active_prompt(agent_name: str) -> Optional[str]:
    """Get the currently active system prompt for an agent."""
    versions = _PROMPT_STORE.get(agent_name, [])
    active = [v for v in versions if v.is_active]
    if not active:
        return None
    return max(active, key=lambda v: v.version).system_prompt


def get_prompt_versions(agent_name: str) -> list[dict]:
    """Get all prompt versions for an agent."""
    versions = _PROMPT_STORE.get(agent_name, [])
    return [asdict(v) for v in versions]


def get_all_prompts() -> dict:
    """Get all agents and their active prompts."""
    result = {}
    for agent_name, versions in _PROMPT_STORE.items():
        active = [v for v in versions if v.is_active]
        if active:
            latest = max(active, key=lambda v: v.version)
            result[agent_name] = {
                "agent_name": agent_name,
                "active_version": latest.version,
                "system_prompt": latest.system_prompt,
                "description": latest.description,
                "total_versions": len(versions),
                "performance_score": latest.performance_score,
                "created_at": latest.created_at,
                "created_by": latest.created_by,
            }
    return result


def update_prompt(agent_name: str, new_prompt: str, description: str = "",
                  created_by: str = "manual", feedback: list[str] = None) -> PromptVersion:
    """Create a new version of a prompt for an agent."""
    versions = _PROMPT_STORE.setdefault(agent_name, [])
    # Deactivate all existing
    for v in versions:
        v.is_active = False
    new_version = PromptVersion(
        agent_name=agent_name,
        version=len(versions) + 1,
        system_prompt=new_prompt,
        description=description or f"Updated by {created_by}",
        created_by=created_by,
        feedback_incorporated=feedback or [],
    )
    versions.append(new_version)
    return new_version


def rollback_prompt(agent_name: str, target_version: int) -> Optional[PromptVersion]:
    """Rollback to a specific prompt version."""
    versions = _PROMPT_STORE.get(agent_name, [])
    target = next((v for v in versions if v.version == target_version), None)
    if not target:
        return None
    for v in versions:
        v.is_active = False
    target.is_active = True
    return target


def incorporate_feedback(agent_name: str, feedback_items: list[str]) -> PromptVersion:
    """
    Weekly feedback incorporation:
    Analyze feedback and create an improved prompt version.
    """
    current_prompt = get_active_prompt(agent_name)
    if not current_prompt:
        return None

    feedback_summary = "\n".join(f"- {f}" for f in feedback_items[:10])

    improved_prompt = (
        f"{current_prompt}\n\n"
        f"IMPROVEMENTS BASED ON RECENT FEEDBACK ({datetime.now().strftime('%Y-W%W')}):\n"
        f"{feedback_summary}"
    )

    return update_prompt(
        agent_name,
        improved_prompt,
        description=f"Weekly feedback update - {len(feedback_items)} items incorporated",
        created_by="feedback_loop",
        feedback=feedback_items,
    )
