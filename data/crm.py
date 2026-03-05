"""
data/crm.py
CRM System — Layer 1 Data & Integration
Suraksha Life Insurance — PROJECT RenewAI

Policyholder profiles matching the business case personas:
- Rajesh (WhatsApp, Term, Budget Conscious) — Journey A
- Meenakshi (WhatsApp, Endowment, Distress/Bereavement) — Journey B
- Vikram (Email, ULIP, Tech-Savvy) — Journey C
Plus 7 additional representative policyholders.
"""
from __future__ import annotations
import random
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional


@dataclass
class Policyholder:
    policy_id: str
    policy_number: str          # e.g. SLI-2298741 (format from business case)
    name: str
    age: int
    phone: str
    email: str
    language: str
    segment: str                # Wealth Builder | Budget Conscious | Young Professional | Senior Citizen
    annual_premium: float       # INR
    sum_assured: float          # INR
    policy_type: str            # Term | Endowment | ULIP | Pension | Health
    policy_product_name: str    # e.g. "Suraksha Term Shield"
    renewal_due_date: date
    lapse_risk: str             # Low | Medium | High
    loyalty_tier: str           # Bronze | Silver | Gold | Platinum
    years_as_customer: int
    years_no_claim: int
    last_payment_status: str    # Paid | Pending | Failed | NA
    preferred_channel: str      # email | whatsapp | voice
    preferred_time_window: str  # morning | afternoon | evening | any
    payment_mode: str           # UPI | ECS | Manual | AutoPay
    state: str
    branch_code: str
    agent_code: str
    distress_flag: bool = False
    bereavement: bool = False
    claim_history: list[dict] = field(default_factory=list)
    interaction_history: list[dict] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


# ── Seeded Sample Policyholders (aligned to Business Case personas & profiles) ──

def _seed_data() -> list[Policyholder]:
    today = date.today()
    return [

        # ── Journey A: Rajesh — WhatsApp, Term, EMI request ──────────────────
        Policyholder(
            policy_id="POL-001",
            policy_number="SLI-2298741",
            name="Rajesh Kumar",
            age=42,
            phone="+919876543210",
            email="rajesh.kumar@example.com",
            language="Hindi",
            segment="Budget Conscious",
            annual_premium=24_000.0,
            sum_assured=10_000_000.0,     # ₹1 Crore
            policy_type="Term",
            policy_product_name="Suraksha Term Shield",
            renewal_due_date=date(today.year, today.month, 15) + timedelta(days=30),
            lapse_risk="Medium",
            loyalty_tier="Silver",
            years_as_customer=4,
            years_no_claim=4,
            last_payment_status="Pending",
            preferred_channel="whatsapp",
            preferred_time_window="evening",   # 9pm preferred
            payment_mode="UPI",
            state="Maharashtra",
            branch_code="MUM-042",
            agent_code="AGT-7721",
            tags=["whatsapp_first", "evening_available", "emi_likely"],
        ),

        # ── Journey B: Meenakshi — Bereavement/Distress ───────────────────────
        Policyholder(
            policy_id="POL-002",
            policy_number="SLI-4419832",
            name="Meenakshi Iyer",
            age=58,
            phone="+918765432109",
            email="meenakshi.iyer@example.com",
            language="Tamil",
            segment="Senior Citizen",
            annual_premium=18_000.0,
            sum_assured=1_000_000.0,
            policy_type="Endowment",
            policy_product_name="Suraksha Future Secure",
            renewal_due_date=today + timedelta(days=10),
            lapse_risk="High",
            loyalty_tier="Gold",
            years_as_customer=8,
            years_no_claim=0,
            last_payment_status="Pending",
            preferred_channel="whatsapp",
            preferred_time_window="morning",
            payment_mode="Manual",
            state="Tamil Nadu",
            branch_code="CHN-018",
            agent_code="AGT-3390",
            distress_flag=True,
            bereavement=True,
            tags=["bereavement", "distress", "human_queue_priority", "long_tenure"],
        ),

        # ── Journey C: Vikram — ULIP, Email, Tech-savvy ───────────────────────
        Policyholder(
            policy_id="POL-003",
            policy_number="SLI-7754210",
            name="Vikram Singh",
            age=35,
            phone="+917654321098",
            email="vikram.singh@example.com",
            language="English",
            segment="Wealth Builder",
            annual_premium=85_000.0,
            sum_assured=5_000_000.0,
            policy_type="ULIP",
            policy_product_name="Suraksha Wealth Builder Plus",
            renewal_due_date=today + timedelta(days=45),
            lapse_risk="Low",
            loyalty_tier="Gold",
            years_as_customer=6,
            years_no_claim=6,
            last_payment_status="Paid",
            preferred_channel="email",
            preferred_time_window="morning",
            payment_mode="AutoPay",
            state="Delhi",
            branch_code="DEL-005",
            agent_code="AGT-1102",
            tags=["tech_savvy", "high_value", "email_first", "no_claim_eligible"],
        ),

        # ── Additional representative policyholders ───────────────────────────

        Policyholder(
            policy_id="POL-004",
            policy_number="SLI-3301456",
            name="Priya Sharma",
            age=29,
            phone="+916543210987",
            email="priya.sharma@example.com",
            language="Hindi",
            segment="Young Professional",
            annual_premium=12_000.0,
            sum_assured=500_000.0,
            policy_type="Term",
            policy_product_name="Suraksha Term Shield",
            renewal_due_date=today + timedelta(days=8),
            lapse_risk="High",
            loyalty_tier="Bronze",
            years_as_customer=1,
            years_no_claim=1,
            last_payment_status="Failed",
            preferred_channel="whatsapp",
            preferred_time_window="evening",
            payment_mode="UPI",
            state="Uttar Pradesh",
            branch_code="LKO-011",
            agent_code="AGT-5543",
            tags=["new_customer", "at_risk", "payment_failed", "digital_native"],
        ),

        Policyholder(
            policy_id="POL-005",
            policy_number="SLI-9982001",
            name="Suresh Patel",
            age=50,
            phone="+915432109876",
            email="suresh.patel@example.com",
            language="Gujarati",
            segment="Budget Conscious",
            annual_premium=8_500.0,
            sum_assured=300_000.0,
            policy_type="Term",
            policy_product_name="Suraksha Term Shield",
            renewal_due_date=today - timedelta(days=12),    # Already lapsed
            lapse_risk="High",
            loyalty_tier="Bronze",
            years_as_customer=2,
            years_no_claim=2,
            last_payment_status="Failed",
            preferred_channel="voice",
            preferred_time_window="afternoon",
            payment_mode="Manual",
            state="Gujarat",
            branch_code="AMD-029",
            agent_code="AGT-8871",
            tags=["lapsed", "revival_candidate", "manual_payer"],
        ),

        Policyholder(
            policy_id="POL-006",
            policy_number="SLI-1123456",
            name="Kavitha Reddy",
            age=44,
            phone="+914321098765",
            email="kavitha.reddy@example.com",
            language="Telugu",
            segment="Wealth Builder",
            annual_premium=120_000.0,
            sum_assured=10_000_000.0,
            policy_type="ULIP",
            policy_product_name="Suraksha Wealth Builder Plus",
            renewal_due_date=today + timedelta(days=20),
            lapse_risk="Low",
            loyalty_tier="Platinum",
            years_as_customer=9,
            years_no_claim=5,
            last_payment_status="Paid",
            preferred_channel="email",
            preferred_time_window="morning",
            payment_mode="AutoPay",
            state="Andhra Pradesh",
            branch_code="HYD-007",
            agent_code="AGT-2215",
            tags=["high_value", "platinum", "no_claim_eligible", "long_tenure"],
        ),

        Policyholder(
            policy_id="POL-007",
            policy_number="SLI-6671234",
            name="Amit Banerjee",
            age=32,
            phone="+913210987654",
            email="amit.banerjee@example.com",
            language="Bengali",
            segment="Young Professional",
            annual_premium=18_000.0,
            sum_assured=750_000.0,
            policy_type="Term",
            policy_product_name="Suraksha Term Shield",
            renewal_due_date=today + timedelta(days=12),
            lapse_risk="Medium",
            loyalty_tier="Silver",
            years_as_customer=4,
            years_no_claim=4,
            last_payment_status="Paid",
            preferred_channel="whatsapp",
            preferred_time_window="evening",
            payment_mode="UPI",
            state="West Bengal",
            branch_code="KOL-014",
            agent_code="AGT-4432",
            tags=["digital_native", "no_claim_eligible"],
        ),

        Policyholder(
            policy_id="POL-008",
            policy_number="SLI-2234567",
            name="Lakshmi Devi",
            age=47,
            phone="+912109876543",
            email="lakshmi.devi@example.com",
            language="Marathi",
            segment="Budget Conscious",
            annual_premium=9_500.0,
            sum_assured=400_000.0,
            policy_type="Endowment",
            policy_product_name="Suraksha Future Secure",
            renewal_due_date=today + timedelta(days=3),
            lapse_risk="High",
            loyalty_tier="Bronze",
            years_as_customer=1,
            years_no_claim=1,
            last_payment_status="Pending",
            preferred_channel="voice",
            preferred_time_window="afternoon",
            payment_mode="Manual",
            state="Maharashtra",
            branch_code="PUN-022",
            agent_code="AGT-6601",
            tags=["at_risk", "urgent", "manual_payer"],
        ),

        Policyholder(
            policy_id="POL-009",
            policy_number="SLI-8890123",
            name="Ramesh Nair",
            age=62,
            phone="+911098765432",
            email="ramesh.nair@example.com",
            language="Malayalam",
            segment="Senior Citizen",
            annual_premium=60_000.0,
            sum_assured=3_000_000.0,
            policy_type="Health",
            policy_product_name="Suraksha Health Shield Plus",
            renewal_due_date=today + timedelta(days=25),
            lapse_risk="Low",
            loyalty_tier="Gold",
            years_as_customer=10,
            years_no_claim=3,
            last_payment_status="Paid",
            preferred_channel="voice",
            preferred_time_window="morning",
            payment_mode="ECS",
            state="Kerala",
            branch_code="KOC-003",
            agent_code="AGT-9987",
            tags=["senior", "long_tenure", "ecs_payer"],
        ),

        Policyholder(
            policy_id="POL-010",
            policy_number="SLI-5567890",
            name="Nisha Thomas",
            age=27,
            phone="+910987654321",
            email="nisha.thomas@example.com",
            language="English",
            segment="Young Professional",
            annual_premium=30_000.0,
            sum_assured=1_500_000.0,
            policy_type="ULIP",
            policy_product_name="Suraksha Wealth Builder Plus",
            renewal_due_date=today + timedelta(days=18),
            lapse_risk="Medium",
            loyalty_tier="Silver",
            years_as_customer=3,
            years_no_claim=3,
            last_payment_status="Paid",
            preferred_channel="email",
            preferred_time_window="any",
            payment_mode="AutoPay",
            state="Kerala",
            branch_code="TRV-009",
            agent_code="AGT-3344",
            tags=["digital_native", "no_claim_eligible", "autopay"],
        ),
    ]


_SAMPLE_POLICYHOLDERS: list[Policyholder] = _seed_data()


# ── Public CRM API ─────────────────────────────────────────────────────────────

def get_all_policyholders() -> list[Policyholder]:
    return _SAMPLE_POLICYHOLDERS


def get_policyholder(policy_id: str) -> Optional[Policyholder]:
    return next((p for p in _SAMPLE_POLICYHOLDERS if p.policy_id == policy_id), None)


def get_by_policy_number(policy_number: str) -> Optional[Policyholder]:
    return next((p for p in _SAMPLE_POLICYHOLDERS if p.policy_number == policy_number), None)


def get_by_risk(risk_level: str) -> list[Policyholder]:
    return [p for p in _SAMPLE_POLICYHOLDERS if p.lapse_risk == risk_level]


def get_by_channel(channel: str) -> list[Policyholder]:
    return [p for p in _SAMPLE_POLICYHOLDERS if p.preferred_channel == channel]


def get_lapsed() -> list[Policyholder]:
    return [p for p in _SAMPLE_POLICYHOLDERS if p.renewal_due_date < date.today()]


def get_due_within(days: int) -> list[Policyholder]:
    today = date.today()
    cutoff = today + timedelta(days=days)
    return [p for p in _SAMPLE_POLICYHOLDERS if today <= p.renewal_due_date <= cutoff]


def get_distressed() -> list[Policyholder]:
    return [p for p in _SAMPLE_POLICYHOLDERS if p.distress_flag or p.bereavement]


def get_high_value(min_premium: float = 100_000) -> list[Policyholder]:
    """High-value policies (₹1L+ premium) — routed to Senior RMs."""
    return [p for p in _SAMPLE_POLICYHOLDERS if p.annual_premium >= min_premium]


def update_interaction(policy_id: str, entry: dict) -> None:
    ph = get_policyholder(policy_id)
    if ph:
        ph.interaction_history.append(entry)


def update_payment_status(policy_id: str, status: str) -> None:
    ph = get_policyholder(policy_id)
    if ph:
        ph.last_payment_status = status


def flag_distress(policy_id: str, reason: str = "") -> None:
    ph = get_policyholder(policy_id)
    if ph:
        ph.distress_flag = True
        if reason:
            ph.tags.append(f"distress:{reason}")


# ── Business Case KPI Helpers ─────────────────────────────────────────────────

def get_persistency_rate() -> float:
    """Current mock persistency rate (paid / total due)."""
    total = len(_SAMPLE_POLICYHOLDERS)
    paid = len([p for p in _SAMPLE_POLICYHOLDERS if p.last_payment_status == "Paid"])
    return round(paid / total, 3) if total else 0.0


def get_pipeline_summary() -> dict:
    today = date.today()
    phs = _SAMPLE_POLICYHOLDERS
    return {
        "total":          len(phs),
        "paid":           len([p for p in phs if p.last_payment_status == "Paid"]),
        "pending":        len([p for p in phs if p.last_payment_status == "Pending"]),
        "failed":         len([p for p in phs if p.last_payment_status == "Failed"]),
        "lapsed":         len([p for p in phs if p.renewal_due_date < today]),
        "due_7_days":     len([p for p in phs if 0 <= (p.renewal_due_date - today).days <= 7]),
        "due_30_days":    len([p for p in phs if 0 <= (p.renewal_due_date - today).days <= 30]),
        "high_risk":      len([p for p in phs if p.lapse_risk == "High"]),
        "distressed":     len([p for p in phs if p.distress_flag]),
        "high_value":     len(get_high_value()),
    }


def reset_sample_data() -> None:
    """Test/helper utility to restore seeded CRM records."""
    global _SAMPLE_POLICYHOLDERS
    _SAMPLE_POLICYHOLDERS = _seed_data()
