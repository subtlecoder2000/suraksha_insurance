"""
services/ab_testing.py
A/B Testing Engine — Layer 2 AI Platform Services
Message variant testing, offer effectiveness tracking, weekly quality audit.
"""
from __future__ import annotations
import random
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Variant:
    variant_id: str
    experiment_id: str
    name: str           # e.g. "Control" | "Treatment-A" | "Treatment-B"
    message_template: str
    sends: int = 0
    opens: int = 0
    clicks: int = 0
    payments: int = 0
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def open_rate(self) -> float:
        return round(self.opens / self.sends, 4) if self.sends else 0

    @property
    def conversion_rate(self) -> float:
        return round(self.payments / self.sends, 4) if self.sends else 0


@dataclass
class Experiment:
    experiment_id: str
    name: str
    description: str
    variants: list[Variant]
    is_active: bool = True
    winner: str = None
    started_at: datetime = field(default_factory=datetime.now)


_EXPERIMENTS: dict[str, Experiment] = {}


# ── Seed default experiments ──────────────────────────────────────────────────

def _seed_experiments() -> None:
    exp = Experiment(
        experiment_id="EXP-001",
        name="Email Subject Line Test",
        description="Testing urgency vs benefit framing in renewal emails",
        variants=[
            Variant("V-001-A", "EXP-001", "Control",
                    "Your insurance policy is expiring soon. Renew now.",
                    sends=15000, opens=3200, clicks=900, payments=320),
            Variant("V-001-B", "EXP-001", "Treatment-A",
                    "Your family's protection expires in {days_left} days — renew in 60 seconds.",
                    sends=15000, opens=4500, clicks=1400, payments=530),
            Variant("V-001-C", "EXP-001", "Treatment-B",
                    "You qualify for {discount_pct}% discount — renew today!",
                    sends=15000, opens=5100, clicks=1700, payments=620),
        ],
    )
    _EXPERIMENTS["EXP-001"] = exp

    exp2 = Experiment(
        experiment_id="EXP-002",
        name="WhatsApp Offer Message Test",
        description="Testing emoji/visual vs text-only WhatsApp messages",
        variants=[
            Variant("V-002-A", "EXP-002", "Text-Only",
                    "Your policy renewal is due. Premium: ₹{premium}. Pay now.",
                    sends=8000, opens=3100, clicks=700, payments=210),
            Variant("V-002-B", "EXP-002", "Emoji-Rich",
                    "🔔 Policy renewing soon!\n💰 Premium: ₹{premium}\n🎁 {offer_text}\n✅ Pay now →",
                    sends=8000, opens=5200, clicks=1800, payments=490),
        ],
    )
    _EXPERIMENTS["EXP-002"] = exp2


_seed_experiments()


# ── Public API ─────────────────────────────────────────────────────────────────

def assign_variant(policy_id: str, experiment_id: str) -> Variant:
    """Assign a policy to a variant deterministically (hash-based)."""
    exp = _EXPERIMENTS.get(experiment_id)
    if not exp or not exp.variants:
        raise ValueError(f"Experiment {experiment_id} not found.")
    idx = hash(policy_id) % len(exp.variants)
    variant = exp.variants[idx]
    variant.sends += 1
    return variant


def record_open(experiment_id: str, variant_id: str) -> None:
    exp = _EXPERIMENTS.get(experiment_id)
    if exp:
        v = next((v for v in exp.variants if v.variant_id == variant_id), None)
        if v:
            v.opens += 1


def record_payment(experiment_id: str, variant_id: str) -> None:
    exp = _EXPERIMENTS.get(experiment_id)
    if exp:
        v = next((v for v in exp.variants if v.variant_id == variant_id), None)
        if v:
            v.payments += 1


def get_winner(experiment_id: str) -> dict:
    """Return the best-performing variant by conversion rate."""
    exp = _EXPERIMENTS.get(experiment_id)
    if not exp:
        return {}
    best = max(exp.variants, key=lambda v: v.conversion_rate)
    return {
        "experiment": exp.name,
        "winner": best.name,
        "variant_id": best.variant_id,
        "conversion_rate": f"{best.conversion_rate:.2%}",
        "sends": best.sends,
        "payments": best.payments,
    }


def get_all_experiments() -> list[Experiment]:
    return list(_EXPERIMENTS.values())


def get_experiment_report(experiment_id: str) -> dict:
    exp = _EXPERIMENTS.get(experiment_id)
    if not exp:
        return {}
    return {
        "experiment_id": exp.experiment_id,
        "name": exp.name,
        "variants": [
            {
                "name": v.name,
                "sends": v.sends,
                "open_rate": f"{v.open_rate:.2%}",
                "conversion_rate": f"{v.conversion_rate:.2%}",
            }
            for v in exp.variants
        ],
        "winner": get_winner(experiment_id),
    }
