"""
data/irdai_rules.py
IRDAI Regulatory Rules — Layer 1 Data & Integration
Stores IRDAI Tech Framework 2024, DPDPA 2023, RBI FRE 2025 compliance rules.
Used by Content Safety Layer and Critique Agent for regulatory validation.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class IrdaiRule:
    rule_id: str
    category: str      # Disclosure | Advertisement | Claims | DataPrivacy | DistanceSelling
    title: str
    description: str
    violation_keywords: list[str]
    severity: str      # Critical | High | Medium


IRDAI_RULES: list[IrdaiRule] = [
    IrdaiRule(
        rule_id="IRDAI-ADV-001",
        category="Advertisement",
        title="No False Promise of Guaranteed Returns",
        description="Insurance products (except guaranteed products) must not promise fixed/guaranteed returns.",
        violation_keywords=["guaranteed returns", "assured profit", "100% safe returns",
                            "guaranteed income", "fixed market returns"],
        severity="Critical",
    ),
    IrdaiRule(
        rule_id="IRDAI-ADV-002",
        category="Advertisement",
        title="No Misleading Comparisons",
        description="Must not compare insurance products with FD/MF using misleading statements.",
        violation_keywords=["better than FD", "beats mutual fund guaranteed",
                            "risk-free investment", "no risk policy"],
        severity="High",
    ),
    IrdaiRule(
        rule_id="IRDAI-ADV-003",
        category="Advertisement",
        title="Regulatory Approval Claim",
        description="Must not claim product is approved by SEBI or government unless explicitly true.",
        violation_keywords=["SEBI approved", "government backed insurance",
                            "RBI guaranteed", "SEBI regulated insurance"],
        severity="Critical",
    ),
    IrdaiRule(
        rule_id="IRDAI-DISC-001",
        category="Disclosure",
        title="Premium & Benefit Disclosure",
        description="All communications must state actual premium, actual benefit, and key exclusions clearly.",
        violation_keywords=[],   # checked programmatically
        severity="High",
    ),
    IrdaiRule(
        rule_id="IRDAI-DISC-002",
        category="Disclosure",
        title="Grace Period Disclosure",
        description="Customer must be informed of grace period before lapse.",
        violation_keywords=[],
        severity="Medium",
    ),
    IrdaiRule(
        rule_id="IRDAI-CLAIM-001",
        category="Claims",
        title="Claim Settlement Timeline",
        description="Claims must be settled within 30 days of receiving complete documents.",
        violation_keywords=["will not pay claim", "claim will be rejected", "no claim allowed"],
        severity="Critical",
    ),
    IrdaiRule(
        rule_id="DPDPA-001",
        category="DataPrivacy",
        title="Personal Data Protection (DPDPA 2023)",
        description="Customer PII (Aadhaar, PAN, bank details) must never be shared or exposed in communications.",
        violation_keywords=[],   # checked programmatically via PII masker
        severity="Critical",
    ),
    IrdaiRule(
        rule_id="DPDPA-002",
        category="DataPrivacy",
        title="Consent for Data Processing",
        description="Customer consent required before using their data for cross-sell/upsell.",
        violation_keywords=[],
        severity="High",
    ),
    IrdaiRule(
        rule_id="RBI-FRE-001",
        category="DistanceSelling",
        title="RBI Fair Practices Code — Distance Selling",
        description="Phone/digital insurance sales must include a free-look period disclosure.",
        violation_keywords=[],
        severity="High",
    ),
    IrdaiRule(
        rule_id="IRDAI-TECH-001",
        category="Technology",
        title="IRDAI Tech Framework 2024 — AI Use",
        description="AI-generated messages must be traceable, auditable, and pass human review for critical decisions.",
        violation_keywords=[],
        severity="High",
    ),
]


# ── Public API ─────────────────────────────────────────────────────────────────

def check_message_compliance(message: str) -> list[dict]:
    """
    Scan a message for IRDAI rule violations.
    Returns list of violations found (empty = compliant).
    """
    message_lower = message.lower()
    violations = []
    for rule in IRDAI_RULES:
        for kw in rule.violation_keywords:
            if kw.lower() in message_lower:
                violations.append({
                    "rule_id": rule.rule_id,
                    "category": rule.category,
                    "title": rule.title,
                    "severity": rule.severity,
                    "triggered_by": kw,
                })
    return violations


def get_rules_by_category(category: str) -> list[IrdaiRule]:
    return [r for r in IRDAI_RULES if r.category == category]


def get_critical_rules() -> list[IrdaiRule]:
    return [r for r in IRDAI_RULES if r.severity == "Critical"]


COMPLIANCE_SUMMARY = {
    "framework": "IRDAI Tech Framework 2024",
    "data_protection": "DPDPA 2023",
    "fair_practices": "RBI FRE 2025",
    "data_residency": "India Only",
    "audit_ready": True,
    "last_review": "2026-03-01",
}
