"""
data/policy_store.py
Policy Document Store — Layer 1 Data & Integration
Premium tables, T&C summaries, Fund NAV, ULIP details for RAG retrieval.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PolicyProduct:
    product_code: str
    name: str
    policy_type: str      # ULIP | Term | Endowment | Health
    min_sum_assured: float
    max_sum_assured: float
    premium_table: dict   # {sum_assured: annual_premium}
    features: list[str]
    exclusions: list[str]
    grace_period_days: int
    surrender_value_after_years: int
    irdai_product_id: str


@dataclass
class FundNAV:
    fund_code: str
    fund_name: str
    nav: float
    date: str
    category: str         # Equity | Debt | Balanced


# ── Product Catalogue ──────────────────────────────────────────────────────────
PRODUCTS: dict[str, PolicyProduct] = {
    "ULIP-WB": PolicyProduct(
        product_code="ULIP-WB",
        name="Wealth Builder ULIP",
        policy_type="ULIP",
        min_sum_assured=500000,
        max_sum_assured=50000000,
        premium_table={500000: 25000, 1000000: 48000, 5000000: 120000, 10000000: 200000},
        features=[
            "Market-linked returns with life cover",
            "Switch between equity/debt funds",
            "Partial withdrawal after 5 years",
            "Tax benefit under 80C and 10(10D)",
            "Loyalty additions from year 11",
        ],
        exclusions=["Suicide within first year", "War and nuclear risks"],
        grace_period_days=30,
        surrender_value_after_years=5,
        irdai_product_id="IRDAI/ULIP/2022/001",
    ),
    "TERM-BC": PolicyProduct(
        product_code="TERM-BC",
        name="Budget Secure Term Plan",
        policy_type="Term",
        min_sum_assured=300000,
        max_sum_assured=10000000,
        premium_table={300000: 5500, 500000: 8500, 750000: 12000, 1000000: 15000},
        features=[
            "Pure life protection, low cost",
            "Return of premium option",
            "Critical illness rider available",
            "Tax benefit under 80C",
        ],
        exclusions=["Pre-existing diseases (2yr wait)", "Suicide within first year"],
        grace_period_days=30,
        surrender_value_after_years=0,
        irdai_product_id="IRDAI/TERM/2021/005",
    ),
    "ENDOW-YP": PolicyProduct(
        product_code="ENDOW-YP",
        name="Future Secure Endowment",
        policy_type="Endowment",
        min_sum_assured=250000,
        max_sum_assured=5000000,
        premium_table={250000: 9000, 500000: 18000, 1000000: 35000, 2500000: 80000},
        features=[
            "Guaranteed maturity benefit",
            "Bonus accumulation",
            "Life cover during policy term",
            "Tax benefit under 80C and 10(10D)",
        ],
        exclusions=["Suicide within first year", "Self-inflicted injuries"],
        grace_period_days=30,
        surrender_value_after_years=3,
        irdai_product_id="IRDAI/ENDOW/2020/003",
    ),
    "HEALTH-SC": PolicyProduct(
        product_code="HEALTH-SC",
        name="SeniorCare Health Shield",
        policy_type="Health",
        min_sum_assured=300000,
        max_sum_assured=10000000,
        premium_table={300000: 20000, 500000: 35000, 1000000: 60000, 3000000: 140000},
        features=[
            "Cashless hospitalisation at 8000+ hospitals",
            "Day care procedures covered",
            "Annual health check-up",
            "No-claim bonus 5% per year up to 50%",
            "AYUSH treatment covered",
        ],
        exclusions=["Cosmetic surgery", "Infertility treatment", "Pre-existing (4yr wait)"],
        grace_period_days=30,
        surrender_value_after_years=0,
        irdai_product_id="IRDAI/HEALTH/2023/007",
    ),
}

# ── Fund NAV Store ──────────────────────────────────────────────────────────────
FUND_NAVS: list[FundNAV] = [
    FundNAV("EF-01", "Equity Growth Fund",       nav=42.35, date="2026-03-01", category="Equity"),
    FundNAV("DF-01", "Debt Secure Fund",          nav=18.72, date="2026-03-01", category="Debt"),
    FundNAV("BF-01", "Balanced Advantage Fund",   nav=31.14, date="2026-03-01", category="Balanced"),
    FundNAV("EF-02", "Large Cap Equity Fund",     nav=55.89, date="2026-03-01", category="Equity"),
    FundNAV("DF-02", "Government Securities Fund",nav=22.41, date="2026-03-01", category="Debt"),
]

# ── Public API ─────────────────────────────────────────────────────────────────

def get_product(product_code: str) -> Optional[PolicyProduct]:
    return PRODUCTS.get(product_code)


def get_product_by_type(policy_type: str) -> list[PolicyProduct]:
    return [p for p in PRODUCTS.values() if p.policy_type == policy_type]


def get_premium(product_code: str, sum_assured: float) -> Optional[float]:
    product = get_product(product_code)
    if not product:
        return None
    table = product.premium_table
    closest = min(table.keys(), key=lambda x: abs(x - sum_assured))
    return table[closest]


def get_all_navs() -> list[FundNAV]:
    return FUND_NAVS


def get_nav(fund_code: str) -> Optional[FundNAV]:
    return next((f for f in FUND_NAVS if f.fund_code == fund_code), None)


def get_policy_summary(product_code: str) -> str:
    """Return a short text summary suitable for RAG injection."""
    p = get_product(product_code)
    if not p:
        return "Product not found."
    features = "; ".join(p.features)
    exclusions = "; ".join(p.exclusions)
    return (
        f"Product: {p.name} ({p.product_code}) | Type: {p.policy_type} | "
        f"Grace Period: {p.grace_period_days} days | IRDAI ID: {p.irdai_product_id}\n"
        f"Features: {features}\nExclusions: {exclusions}"
    )
