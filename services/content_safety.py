"""
services/content_safety.py
Content Safety Layer — Layer 2 AI Platform Services
Distress keyword detection, PII masking, hallucination checks, regulatory violation prevention.
Runs BEFORE every AI message is sent to Critique Agent.
"""
from __future__ import annotations
import re
from dataclasses import dataclass
from data.irdai_rules import check_message_compliance


# ── Distress Keywords ──────────────────────────────────────────────────────────
_DISTRESS_KEYWORDS = [
    # Financial stress
    "bankrupt", "can't pay", "debt trap", "loan defaulted", "lost job",
    "no money", "paisa nahi", "koi rasta nahi",
    # Emotional distress
    "suicidal", "want to die", "end my life", "no reason to live",
    "depressed", "hopeless", "give up", "bahut pareshan",
    # Medical emergency
    "hospital", "critical condition", "icu", "serious illness",
    # Anger / abuse
    "fraud", "cheat", "scam", "worst company", "consumer forum",
    "legal action", "police complaint",
]

# ── PII Patterns ──────────────────────────────────────────────────────────────
_PII_PATTERNS = {
    "aadhaar":   re.compile(r'\b\d{4}\s?\d{4}\s?\d{4}\b'),
    "pan":       re.compile(r'\b[A-Z]{5}[0-9]{4}[A-Z]\b'),
    "phone":     re.compile(r'(\+91[-\s]?)?[6-9]\d{9}'),
    "email":     re.compile(r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Z|a-z]{2,}\b'),
    "bank_acc":  re.compile(r'\b\d{9,18}\b'),
    "ifsc":      re.compile(r'\b[A-Z]{4}0[A-Z0-9]{6}\b'),
}

# ── Hallucination Triggers ────────────────────────────────────────────────────
_HALLUCINATION_TRIGGERS = [
    "we guarantee", "100% returns", "no risk whatsoever",
    "approved by government", "as per supreme court",
    "your claim is automatically approved",
    "premium will never increase", "policy covers everything",
]


@dataclass
class SafetyCheckResult:
    passed: bool
    distress_detected: bool
    pii_found: list[str]
    regulatory_violations: list[dict]
    hallucinations_found: list[str]
    masked_message: str
    flags: list[str]


def mask_pii(text: str) -> str:
    """Replace PII with masked placeholders."""
    masked = text
    masked = _PII_PATTERNS["aadhaar"].sub("[AADHAAR-MASKED]", masked)
    masked = _PII_PATTERNS["pan"].sub("[PAN-MASKED]", masked)
    masked = _PII_PATTERNS["bank_acc"].sub("[BANK-MASKED]", masked)
    masked = _PII_PATTERNS["ifsc"].sub("[IFSC-MASKED]", masked)
    # Phone: Keep first 5 digits, mask rest
    masked = _PII_PATTERNS["phone"].sub(
        lambda m: m.group()[:5] + "XXXXX", masked
    )
    # Email: mask domain
    masked = _PII_PATTERNS["email"].sub(
        lambda m: m.group().split("@")[0][:3] + "***@***.***", masked
    )
    return masked


def detect_distress(text: str) -> bool:
    text_lower = text.lower()
    return any(kw in text_lower for kw in _DISTRESS_KEYWORDS)


def detect_hallucinations(text: str) -> list[str]:
    text_lower = text.lower()
    return [kw for kw in _HALLUCINATION_TRIGGERS if kw in text_lower]


def check_safety(message: str, customer_input: str = "") -> SafetyCheckResult:
    """
    Run full safety check on an AI-generated message and customer context.
    Returns a SafetyCheckResult with masked message and all flags.
    """
    flags = []

    # 1. Distress detection (from customer input)
    distress = detect_distress(customer_input) or detect_distress(message)
    if distress:
        flags.append("DISTRESS_DETECTED")

    # 2. PII in message
    pii_found = [ptype for ptype, pat in _PII_PATTERNS.items() if pat.search(message)]
    if pii_found:
        flags.extend([f"PII_{p.upper()}" for p in pii_found])

    # 3. Regulatory violations
    violations = check_message_compliance(message)
    if violations:
        critical = [v for v in violations if v["severity"] == "Critical"]
        if critical:
            flags.append("REGULATORY_CRITICAL")
        else:
            flags.append("REGULATORY_WARNING")

    # 4. Hallucinations
    hallucinations = detect_hallucinations(message)
    if hallucinations:
        flags.append("HALLUCINATION_RISK")

    # 5. Mask PII in message before delivery
    masked = mask_pii(message)

    passed = not bool(flags)
    return SafetyCheckResult(
        passed=passed,
        distress_detected=distress,
        pii_found=pii_found,
        regulatory_violations=violations,
        hallucinations_found=hallucinations,
        masked_message=masked,
        flags=flags,
    )
