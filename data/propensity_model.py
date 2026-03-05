"""
data/propensity_model.py
Propensity-to-Lapse Model — Layer 1 Data & Integration
Scores policyholders on lapse likelihood: Low / Medium / High
Based on: payment history, policy tenure, segment, premium amount, engagement signals
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from data.crm import Policyholder


@dataclass
class PropensityScore:
    policy_id: str
    risk_level: str          # Low | Medium | High
    score: float             # 0.0 (low risk) — 1.0 (certain lapse)
    contributing_factors: list[str]
    recommended_action: str
    budget_persona: str      # Wealth Builder | Budget Conscious


def score_policyholder(ph: "Policyholder") -> PropensityScore:
    """
    Rule-based propensity scoring (production: replace with trained ML model).
    Score 0.0 = very likely to renew, 1.0 = very likely to lapse.
    """
    score = 0.0
    factors = []

    # Payment history
    if ph.last_payment_status == "Failed":
        score += 0.35
        factors.append("Last payment failed")
    elif ph.last_payment_status == "Pending":
        score += 0.20
        factors.append("Payment still pending")

    # Premium amount relative to segment
    if ph.segment == "Budget Conscious" and ph.annual_premium > 20000:
        score += 0.15
        factors.append("High premium for budget segment")

    # Payment mode — manual is highest risk
    if ph.payment_mode == "Manual":
        score += 0.15
        factors.append("Manual payment mode (no automation)")
    elif ph.payment_mode == "UPI":
        score += 0.05

    # Tenure — new customers are higher risk
    if ph.years_as_customer < 2:
        score += 0.15
        factors.append("New customer (< 2 years)")
    elif ph.years_as_customer > 7:
        score -= 0.10
        factors.append("Long-tenure customer (7+ years)")

    # Days until renewal
    from datetime import date
    days_to_renewal = (ph.renewal_due_date - date.today()).days
    if days_to_renewal < 0:
        score += 0.30
        factors.append("Policy already lapsed")
    elif days_to_renewal <= 7:
        score += 0.15
        factors.append("Renewal due within 7 days")
    elif days_to_renewal <= 14:
        score += 0.08
        factors.append("Renewal due within 14 days")

    # Loyalty tier — higher tier, lower lapse risk
    tier_penalty = {"Platinum": -0.10, "Gold": -0.05, "Silver": 0.0, "Bronze": 0.05}
    score += tier_penalty.get(ph.loyalty_tier, 0)

    # Segment persona
    if ph.segment in ("Wealth Builder",):
        score -= 0.05
    elif ph.segment == "Budget Conscious":
        score += 0.05

    # Clamp score
    score = min(max(score, 0.0), 1.0)

    # Assign risk level
    if score < 0.30:
        risk_level = "Low"
        action = "Send standard renewal reminder with loyalty offer"
    elif score < 0.60:
        risk_level = "Medium"
        action = "Send personalised discount offer + UPI payment link; follow up in 48h"
    else:
        risk_level = "High"
        action = "Trigger Voice Agent + Human Queue escalation if no response in 24h"

    # Budget persona
    persona = "Budget Conscious" if ph.annual_premium / ph.sum_assured < 0.02 else "Wealth Builder"

    return PropensityScore(
        policy_id=ph.policy_id,
        risk_level=risk_level,
        score=round(score, 3),
        contributing_factors=factors,
        recommended_action=action,
        budget_persona=persona,
    )


def score_all(policyholders: list) -> list[PropensityScore]:
    return [score_policyholder(ph) for ph in policyholders]


def get_high_risk(policyholders: list) -> list[tuple]:
    """Returns (policyholder, score) tuples for High risk only."""
    results = []
    for ph in policyholders:
        s = score_policyholder(ph)
        if s.risk_level == "High":
            results.append((ph, s))
    return results
