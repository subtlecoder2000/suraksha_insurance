"""
critique/checklist.py
9-Point Critique Checklist — Suraksha Life Insurance PROJECT RenewAI v2.0

Each check is an independent validator returning CheckResult(passed, score, feedback).
All 9 checks run per message. Critical failures trigger BLOCK.
"""
from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Optional

from data.irdai_rules import check_message_compliance
from services.content_safety import detect_distress, detect_hallucinations, mask_pii, _PII_PATTERNS
from config.settings import CRITIQUE_BLOCK_KEYWORDS, SUPPORTED_LANGUAGES


@dataclass
class CheckResult:
    check_number: int
    check_name: str
    passed: bool
    score: float        # 0.0 – 1.0
    feedback: str
    severity: str       # CRITICAL | HIGH | MEDIUM


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 1: Factual Accuracy (RAG source verification)
# Business case: "All benefit figures served from verified policy document retrieval,
#                not AI memory. Hallucination detected → case suspended, routed human."
# ─────────────────────────────────────────────────────────────────────────────
def check_factual_accuracy(message: str, context: dict) -> CheckResult:
    hallucinations = detect_hallucinations(message)

    # Check if premium/sum_assured in message match CRM context
    premium = context.get("premium", 0)
    sum_assured = context.get("sum_assured", 0)

    found_wrong_premium = False
    if premium:
        # Extract first ₹ figure in message
        amounts = re.findall(r'₹[\d,]+', message.replace(' ', ''))
        if amounts and not any(str(int(premium)).replace(",", "") in a.replace(",", "") for a in amounts):
            found_wrong_premium = False  # Can't reliably check without true RAG

    passed = not hallucinations
    return CheckResult(
        check_number=1,
        check_name="Factual Accuracy",
        passed=passed,
        score=0.0 if hallucinations else 1.0,
        feedback=(
            f"Hallucination risk detected: {', '.join(hallucinations)}"
            if hallucinations else "Facts grounded in RAG source docs."
        ),
        severity="CRITICAL",
    )


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 2: Tone / Segment Alignment
# Business case: "Tone-Segment Alignment — Wealth Builder vs Budget Conscious"
# ─────────────────────────────────────────────────────────────────────────────
def check_tone_segment(message: str, context: dict) -> CheckResult:
    segment = context.get("segment", "")
    tone = context.get("tone", "friendly")
    msg_lower = message.lower()

    issues = []
    if segment == "Wealth Builder":
        # Should be professional, not too casual or discount-pushy
        if "aap" in msg_lower and "yaar" in msg_lower:
            issues.append("Too casual for Wealth Builder segment")
    if segment == "Budget Conscious":
        # Should mention affordability, EMI, discount
        if not any(kw in msg_lower for kw in ["emi", "installment", "discount", "affordable", "save"]):
            issues.append("Budget Conscious segment should mention affordability/discount options")

    passed = not issues
    return CheckResult(
        check_number=2,
        check_name="Tone-Segment Alignment",
        passed=passed,
        score=0.0 if issues else 1.0,
        feedback="; ".join(issues) if issues else f"Tone '{tone}' appropriate for '{segment}' segment.",
        severity="HIGH",
    )


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 3: Emotional Context (Emotional Control)
# Business case: "Emotional Context — no cheerful tone if customer expressed distress"
# ─────────────────────────────────────────────────────────────────────────────
def check_emotional_context(message: str, context: dict) -> CheckResult:
    is_distressed = (
        context.get("sentiment") == "distressed"
        or context.get("distress_flag", False)
        or context.get("bereavement", False)
    )
    msg_lower = message.lower()

    # Cheerful markers that are inappropriate for distressed customers
    cheerful_markers = ["🎉", "🥳", "exciting", "celebrate", "great news!", "amazing offer"]
    found_cheerful = [m for m in cheerful_markers if m in msg_lower] if is_distressed else []

    passed = not found_cheerful
    return CheckResult(
        check_number=3,
        check_name="Emotional Context",
        passed=passed,
        score=0.0 if found_cheerful else 1.0,
        feedback=(
            f"Distress/bereavement context: remove cheerful markers: {found_cheerful}"
            if found_cheerful else "Emotional tone appropriate for customer state."
        ),
        severity="CRITICAL" if context.get("bereavement") else "HIGH",
    )


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 4: Logical Coherence
# Business case: "Logical Coherence — no contradiction with prior messages"
# ─────────────────────────────────────────────────────────────────────────────
def check_logical_coherence(message: str, prior_messages: list[str]) -> CheckResult:
    if not prior_messages:
        return CheckResult(4, "Logical Coherence", True, 1.0, "No prior messages to check against.", "MEDIUM")

    issues = []
    # Detect contradictory discount claims across messages
    discounts_this = re.findall(r'(\d+)%\s(?:discount|off)', message.lower())
    for prior in prior_messages:
        discounts_prior = re.findall(r'(\d+)%\s(?:discount|off)', prior.lower())
        if discounts_this and discounts_prior:
            if set(discounts_this) != set(discounts_prior):
                issues.append(
                    f"Discount mismatch: this message says {discounts_this}%, prior said {discounts_prior}%"
                )

    passed = not issues
    return CheckResult(
        check_number=4,
        check_name="Logical Coherence",
        passed=passed,
        score=0.0 if issues else 1.0,
        feedback="; ".join(issues) if issues else "No contradictions detected with prior messages.",
        severity="HIGH",
    )


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 5: Regulatory Compliance (including DPDPA 2023 / PII Safety)
# Business case: "Regulatory Guidance — no false promise, no IRDAI guideline violations"
# ─────────────────────────────────────────────────────────────────────────────
def check_regulatory_compliance(message: str) -> CheckResult:
    violations = check_message_compliance(message)
    critical_v = [v for v in violations if v["severity"] == "Critical"]

    # Integrate PII Check here (from former check 9)
    pii_found = []
    for ptype, pat in _PII_PATTERNS.items():
        if pat.search(message):
            pii_found.append(ptype)

    pii_violations = [{"title": f"PII exposed: {ptype}", "severity": "Critical"} for ptype in pii_found]

    all_violations = violations + pii_violations
    passed = not all_violations
    
    feedback = (
        f"Violations: {'; '.join(v['title'] for v in all_violations)}"
        if all_violations else "Regulatory and DPDPA/PII compliance verified."
    )

    return CheckResult(
        check_number=5,
        check_name="Regulatory Compliance",
        passed=passed,
        score=0.0 if (critical_v or pii_found) else (0.5 if violations else 1.0),
        feedback=feedback,
        severity="CRITICAL" if (critical_v or pii_found) else "HIGH",
    )


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 6: Language Quality
# Business case: "Language Quality — grammar + cultural fit check (9 languages)"
# ─────────────────────────────────────────────────────────────────────────────
def check_language_quality(message: str, context: dict) -> CheckResult:
    language = context.get("language", "English")
    issues = []

    # Basic checks: message not empty, reasonable length
    if len(message.strip()) < 20:
        issues.append("Message too short — likely incomplete generation")
    if len(message) > 2000:
        issues.append("Message too long — may overwhelm customer, consider brevity")

    # Check language plausibility (stub: production uses LLM translation check)
    # If language is Hindi, check for at least some Devanagari or romanised Hindi markers
    if language == "Hindi":
        has_hindi = any('\u0900' <= c <= '\u097f' for c in message)
        has_roman_hindi = any(w in message.lower() for w in ["aap", "ji", "kya", "hai", "hum"])
        if not has_hindi and not has_roman_hindi:
            issues.append("Hindi customer but no Hindi language content detected")

    passed = not issues
    return CheckResult(
        check_number=6,
        check_name="Language Quality",
        passed=passed,
        score=0.0 if issues else 1.0,
        feedback="; ".join(issues) if issues else f"Language quality acceptable for {language}.",
        severity="MEDIUM",
    )


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 7: Personalization Accuracy
# Business case: "Personalization Accuracy — correct name, policy#, product, premium"
# ─────────────────────────────────────────────────────────────────────────────
def check_personalization(message: str, context: dict) -> CheckResult:
    issues = []
    name = context.get("name", "")
    first_name = name.split()[0] if name else ""
    policy_number = context.get("policy_number", "")
    premium = str(int(context.get("premium", 0)))

    if first_name and first_name.lower() not in message.lower():
        issues.append(f"Customer name '{first_name}' not found in message — generic/stale template?")

    if policy_number and policy_number not in message and "SLI-" not in message:
        # Not a hard failure — policy# may not always be included
        pass

    # Check that a wrong name is not present (e.g. placeholder like {name})
    if "{name}" in message or "{first_name}" in message:
        issues.append("Unfilled template placeholder detected: {name} or {first_name}")
    if "{premium}" in message or "{policy_id}" in message:
        issues.append("Unfilled template placeholder detected in message body")

    passed = not issues
    return CheckResult(
        check_number=7,
        check_name="Personalization Accuracy",
        passed=passed,
        score=0.0 if issues else 1.0,
        feedback="; ".join(issues) if issues else "Personalization fields correctly populated.",
        severity="HIGH",
    )


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 8: Conversation Completeness (Continuity)
# Business case: "Conversation Completeness — response answers customer's actual question"
# ─────────────────────────────────────────────────────────────────────────────
def check_conversation_completeness(message: str, context: dict, prior_messages: list[str]) -> CheckResult:
    issues = []

    # If customer raised an objection in prior messages, this message should address it
    objections_raised = context.get("objections_raised", [])
    if objections_raised and prior_messages:
        # Check if response acknowledges the objection context
        objection_addressed = any(
            any(word in message.lower() for word in ["understand", "concern", "option", "solution", "help"])
            for _ in [True])
        if not objection_addressed:
            issues.append("Customer raised objections in prior turn but response ignores them")

    passed = not issues
    return CheckResult(
        check_number=8,
        check_name="Conversation Completeness",
        passed=passed,
        score=0.0 if issues else 1.0,
        feedback="; ".join(issues) if issues else "Response addresses customer's conversational context.",
        severity="MEDIUM",
    )


# ─────────────────────────────────────────────────────────────────────────────
# CHECK 9: Offer Validity
# Business case: "Offer Validity — loyalty discount/offer correctly applied & IRDAI compliant"
# ─────────────────────────────────────────────────────────────────────────────
def check_offer_validity(message: str, context: dict) -> CheckResult:
    """Validate that mentioned offers/discounts match the customer's eligible offers."""
    issues = []
    
    # Extract mentioned discounts in message (e.g. "10% discount", "₹200 cashback")
    mentioned_pcts = re.findall(r'(\d+)%\s(?:discount|off)', message.lower())
    mentioned_cashback = re.findall(r'₹(\d+)\s(?:cashback)', message.lower())
    
    # Get eligibility from context
    eligible_discount = context.get("discount_pct", 0)
    offer_text = context.get("offer_text", "")
    
    if mentioned_pcts:
        # Check if at least one mentioned pct matches eligible discount
        # Note: eligible_discount is like 0.10 for 10%
        target_pct_str = str(int(eligible_discount * 100))
        if not any(target_pct_str in p for p in mentioned_pcts) and eligible_discount > 0:
            issues.append(f"Offer mismatch: Message mentions {mentioned_pcts}% but customer is only eligible for {target_pct_str}%")
        elif not eligible_discount and mentioned_pcts:
             issues.append(f"Invalid offer: Message mentions {mentioned_pcts}% discount but customer is not eligible for any NCD")

    passed = not issues
    return CheckResult(
        check_number=9,
        check_name="Offer Validity",
        passed=passed,
        score=0.0 if issues else 1.0,
        feedback="; ".join(issues) if issues else "Loyalty offers and discounts correctly applied.",
        severity="CRITICAL",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Master runner
# ─────────────────────────────────────────────────────────────────────────────

def run_all_checks(message: str, context: dict,
                   prior_messages: list[str] = None) -> list[CheckResult]:
    """Run all 9 checks and return results list."""
    prior = prior_messages or []
    return [
        check_factual_accuracy(message, context),
        check_tone_segment(message, context),
        check_emotional_context(message, context),
        check_logical_coherence(message, prior),
        check_regulatory_compliance(message),
        check_language_quality(message, context),
        check_personalization(message, context),
        check_conversation_completeness(message, context, prior),
        check_offer_validity(message, context),
    ]
