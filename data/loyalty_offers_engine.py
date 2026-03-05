"""
data/loyalty_offers_engine.py
Loyalty & Retention Offers Engine — Layer 1 Data & Integration (NEW in v2.0)
Calculates No-Claim Discount, Repeat Customer Priority, and Dynamic Offers.
All offers are IRDAI-compliant.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from data.crm import Policyholder

from config.settings import NO_CLAIM_DISCOUNT_TIERS, AUTOPAY_CASHBACK_INR


@dataclass
class LoyaltyOffer:
    offer_id: str
    offer_type: str        # NoClaimDiscount | RepeatCustomer | Dynamic
    title: str
    description: str
    discount_pct: float
    savings_inr: float
    conditions: list[str]
    irdai_compliant: bool = True
    applicable: bool = True


@dataclass
class CustomerOfferPackage:
    policy_id: str
    customer_name: str
    tier: str
    offers: list[LoyaltyOffer]
    total_savings_inr: float
    priority_service: bool
    summary: str


# ── No-Claim Discount ─────────────────────────────────────────────────────────

def _calc_no_claim_discount(ph: "Policyholder") -> Optional[LoyaltyOffer]:
    if ph.years_no_claim <= 0:
        return None
    # Pick highest applicable tier
    pct = 0.0
    for min_years, discount in sorted(NO_CLAIM_DISCOUNT_TIERS.items()):
        if ph.years_no_claim >= min_years:
            pct = discount
    if pct == 0:
        return None
    savings = round(ph.annual_premium * pct, 2)
    return LoyaltyOffer(
        offer_id=f"NCD-{ph.policy_id}",
        offer_type="NoClaimDiscount",
        title=f"{int(pct * 100)}% No-Claim Discount",
        description=(
            f"You've had {ph.years_no_claim} claim-free years! Enjoy {int(pct*100)}% off "
            f"your renewal premium — saving ₹{savings:,.0f}."
        ),
        discount_pct=pct,
        savings_inr=savings,
        conditions=[
            f"Minimum {ph.years_no_claim} consecutive claim-free years",
            "Applicable on base premium only",
            "Valid for this renewal cycle only",
        ],
    )


# ── Repeat Customer Priority ───────────────────────────────────────────────────

def _calc_repeat_customer(ph: "Policyholder") -> Optional[LoyaltyOffer]:
    if ph.years_as_customer < 3:
        return None
    perks = []
    if ph.years_as_customer >= 3:
        perks.append("Priority service tier (dedicated RM)")
    if ph.years_as_customer >= 5:
        perks.append("Faster claim settlement SLA (24h vs 72h standard)")
    if ph.years_as_customer >= 7:
        perks.append("Early renewal reminder T-60 days")
        perks.append("Birthday & anniversary personalised greeting")
    return LoyaltyOffer(
        offer_id=f"RCP-{ph.policy_id}",
        offer_type="RepeatCustomer",
        title="Loyal Customer Priority Benefits",
        description=(
            f"As a {ph.years_as_customer}-year valued customer ({ph.loyalty_tier} tier), "
            f"you receive exclusive priority benefits."
        ),
        discount_pct=0.0,
        savings_inr=0.0,
        conditions=[f"{ph.years_as_customer}+ years as Surekha Insurance customer"],
    )


# ── Dynamic Offers ─────────────────────────────────────────────────────────────

def _calc_dynamic_offers(ph: "Policyholder") -> list[LoyaltyOffer]:
    offers = []

    # AutoPay cashback
    if ph.payment_mode not in ("AutoPay", "ECS"):
        offers.append(LoyaltyOffer(
            offer_id=f"APY-{ph.policy_id}",
            offer_type="Dynamic",
            title=f"AutoPay Cashback ₹{AUTOPAY_CASHBACK_INR}",
            description=f"Switch to AutoPay and get ₹{AUTOPAY_CASHBACK_INR} cashback on your next renewal.",
            discount_pct=0.0,
            savings_inr=AUTOPAY_CASHBACK_INR,
            conditions=["Enroll in AutoPay via UPI/ECS", "Cashback credited within 7 working days"],
        ))

    # Premium holiday (1 month free) for high-value policyholders
    if ph.annual_premium >= 50000 and ph.loyalty_tier in ("Gold", "Platinum"):
        monthly_equiv = round(ph.annual_premium / 12, 2)
        offers.append(LoyaltyOffer(
            offer_id=f"PHD-{ph.policy_id}",
            offer_type="Dynamic",
            title="1-Month Premium Holiday",
            description=f"As a {ph.loyalty_tier} member, enjoy 1 month free — save ₹{monthly_equiv:,.0f}.",
            discount_pct=round(1/12, 4),
            savings_inr=monthly_equiv,
            conditions=["Gold or Platinum loyalty tier", "Available once per policy year"],
        ))

    # Free rider add-on for Budget Conscious
    if ph.segment == "Budget Conscious" and ph.policy_type == "Term":
        offers.append(LoyaltyOffer(
            offer_id=f"RDR-{ph.policy_id}",
            offer_type="Dynamic",
            title="Free Critical Illness Rider (1 Year)",
            description="Add critical illness cover worth ₹5 Lakh FREE for 1 year.",
            discount_pct=0.0,
            savings_inr=3500.0,   # estimated rider premium saved
            conditions=["Budget Conscious Term policyholders", "Valid for renewal term only"],
        ))

    # Cross-sell bundle discount
    if ph.years_as_customer >= 5 and ph.policy_type != "Health":
        offers.append(LoyaltyOffer(
            offer_id=f"CSB-{ph.policy_id}",
            offer_type="Dynamic",
            title="Cross-Sell Bundle: 10% off Health Add-On",
            description="Add a Health Shield policy and get 10% off the first year's premium.",
            discount_pct=0.10,
            savings_inr=round(20000 * 0.10, 2),
            conditions=["Existing policyholder 5+ years", "Bundle must be purchased together"],
        ))

    return offers


# ── Main Package Builder ──────────────────────────────────────────────────────

def build_offer_package(ph: "Policyholder") -> CustomerOfferPackage:
    offers = []

    ncd = _calc_no_claim_discount(ph)
    if ncd:
        offers.append(ncd)

    rcp = _calc_repeat_customer(ph)
    if rcp:
        offers.append(rcp)

    offers.extend(_calc_dynamic_offers(ph))

    total_savings = sum(o.savings_inr for o in offers)
    priority = ph.loyalty_tier in ("Gold", "Platinum") or ph.years_as_customer >= 5

    titles = [o.title for o in offers]
    summary = (
        f"{ph.name} qualifies for {len(offers)} offer(s): {', '.join(titles)}. "
        f"Total savings: ₹{total_savings:,.0f}."
    ) if offers else f"{ph.name} has no current special offers."

    return CustomerOfferPackage(
        policy_id=ph.policy_id,
        customer_name=ph.name,
        tier=ph.loyalty_tier,
        offers=offers,
        total_savings_inr=total_savings,
        priority_service=priority,
        summary=summary,
    )
