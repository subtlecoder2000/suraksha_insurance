"""
monitoring/scorecard.py
Success Metrics Scorecard — Layer 6 Monitoring & Governance
Suraksha Life Insurance — PROJECT RenewAI v2.0

Business case Section 8: "Success Metrics — How We Know It's Working"
Tracks all KPIs against FY25 baseline and FY26 targets.
"""
from __future__ import annotations
from config.settings import (
    CURRENT_PERSISTENCY_13M, TARGET_PERSISTENCY_13M,
    COST_PER_RENEWAL_BASELINE, COST_PER_RENEWAL_TARGET,
    EMAIL_OPEN_RATE_TARGET, WA_RESPONSE_RATE_TARGET,
    VOICE_CONVERSION_TARGET, NPS_BASELINE, NPS_TARGET,
    AI_ACCURACY_TARGET, HUMAN_ESCALATION_RATE_TARGET,
    DISTRESS_ESCALATION_SLA_HRS,
)

# ── KPI Definitions from Business Case Section 8 ─────────────────────────────

KPI_DEFINITIONS = [
    {
        "metric":      "13th Month Persistency Rate",
        "baseline":    "71%",
        "target":      "88%",
        "measurement": "Monthly IRDAI persistency report",
    },
    {
        "metric":      "Cost per Renewal (₹)",
        "baseline":    "₹182",
        "target":      "₹45",
        "measurement": "Opex / policies renewed",
    },
    {
        "metric":      "Email Open Rate",
        "baseline":    "18%",
        "target":      "42%",
        "measurement": "Email platform analytics dashboard",
    },
    {
        "metric":      "WhatsApp Response Rate",
        "baseline":    "N/A (manual)",
        "target":      "58%",
        "measurement": "WhatsApp Business API read receipts",
    },
    {
        "metric":      "AI Voice Call Conversion Rate",
        "baseline":    "N/A (manual calls)",
        "target":      "31%",
        "measurement": "Calls resulting in payment within 48h",
    },
    {
        "metric":      "Human Escalation Rate",
        "baseline":    "100% (all manual)",
        "target":      "≤10%",
        "measurement": "AI system escalation trigger logs",
    },
    {
        "metric":      "Customer NPS (Renewal Experience)",
        "baseline":    "34",
        "target":      "≥55",
        "measurement": "Post-interaction IVR/WhatsApp survey",
    },
    {
        "metric":      "IRDAI Grievance Violations",
        "baseline":    "12/year (FY24)",
        "target":      "0",
        "measurement": "IRDAI regulatory filings; grievance register",
    },
    {
        "metric":      "AI Response Accuracy Score",
        "baseline":    "N/A",
        "target":      "≥87%",
        "measurement": "Weekly automated quality evaluation on 5% random sample",
    },
    {
        "metric":      "AI-detected Distress Cases Escalated ≤2h",
        "baseline":    "N/A (manual)",
        "target":      "100%",
        "measurement": "AI monitoring system + human case queue timestamp delta",
    },
]

# ── Live scorecard (mock current values for demo) ─────────────────────────────

_DEFAULT_LIVE_METRICS: dict[str, float] = {
    "persistency_rate":      0.71,   # Will update as renewals complete
    "cost_per_renewal":      182,
    "email_open_rate":       0.18,
    "wa_response_rate":      0.0,    # New channel, starts at 0
    "voice_conversion":      0.0,
    "escalation_rate":       1.0,    # Starts at 100% (all manual)
    "nps":                   34,
    "grievance_violations":  12,
    "ai_accuracy":           0.0,    # Starts at N/A
    "distress_escalation_100pct": False,
}
_LIVE_METRICS: dict[str, float] = dict(_DEFAULT_LIVE_METRICS)


def update_metric(metric: str, value: float) -> None:
    if metric in _LIVE_METRICS:
        _LIVE_METRICS[metric] = value


def refresh_operational_metrics() -> None:
    """Refresh scorecard metrics derived from operational event logs."""
    from monitoring.observability import get_distress_sla_stats
    distress = get_distress_sla_stats(DISTRESS_ESCALATION_SLA_HRS)
    ratio = distress["adherence_ratio"]
    # Mark true only when measured events exist and all closed cases met SLA.
    _LIVE_METRICS["distress_escalation_100pct"] = (
        ratio is not None and ratio >= 1.0 and distress["pending"] == 0
    )


def reset_metrics() -> None:
    """Test/helper utility to restore default scorecard values."""
    _LIVE_METRICS.clear()
    _LIVE_METRICS.update(_DEFAULT_LIVE_METRICS)


def get_scorecard() -> list[dict]:
    """Return the full scorecard with baseline, target, current, and status."""
    refresh_operational_metrics()
    live = _LIVE_METRICS
    return [
        {
            "metric":    "13th Month Persistency Rate",
            "baseline":  "71%",
            "target":    "88%",
            "current":   f"{live['persistency_rate']:.0%}",
            "status":    "🟢" if live["persistency_rate"] >= TARGET_PERSISTENCY_13M else "🔴",
        },
        {
            "metric":    "Cost per Renewal (₹)",
            "baseline":  "₹182",
            "target":    "₹45",
            "current":   f"₹{live['cost_per_renewal']:.0f}",
            "status":    "🟢" if live["cost_per_renewal"] <= COST_PER_RENEWAL_TARGET else "🔴",
        },
        {
            "metric":    "Email Open Rate",
            "baseline":  "18%",
            "target":    "42%",
            "current":   f"{live['email_open_rate']:.0%}",
            "status":    "🟢" if live["email_open_rate"] >= EMAIL_OPEN_RATE_TARGET else "🔴",
        },
        {
            "metric":    "WhatsApp Response Rate",
            "baseline":  "N/A",
            "target":    "58%",
            "current":   f"{live['wa_response_rate']:.0%}",
            "status":    "🟢" if live["wa_response_rate"] >= WA_RESPONSE_RATE_TARGET else "🔴",
        },
        {
            "metric":    "AI Voice Conversion Rate",
            "baseline":  "N/A",
            "target":    "31%",
            "current":   f"{live['voice_conversion']:.0%}",
            "status":    "🟢" if live["voice_conversion"] >= VOICE_CONVERSION_TARGET else "🔴",
        },
        {
            "metric":    "Human Escalation Rate",
            "baseline":  "100%",
            "target":    "≤10%",
            "current":   f"{live['escalation_rate']:.0%}",
            "status":    "🟢" if live["escalation_rate"] <= HUMAN_ESCALATION_RATE_TARGET else "🔴",
        },
        {
            "metric":    "Customer NPS",
            "baseline":  "34",
            "target":    "≥55",
            "current":   str(int(live["nps"])),
            "status":    "🟢" if live["nps"] >= NPS_TARGET else "🔴",
        },
        {
            "metric":    "IRDAI Grievance Violations",
            "baseline":  "12/yr",
            "target":    "0",
            "current":   str(int(live["grievance_violations"])),
            "status":    "🟢" if live["grievance_violations"] == 0 else "🔴",
        },
        {
            "metric":    "AI Response Accuracy",
            "baseline":  "N/A",
            "target":    "≥87%",
            "current":   f"{live['ai_accuracy']:.0%}" if live["ai_accuracy"] > 0 else "N/A",
            "status":    "🟢" if live["ai_accuracy"] >= AI_ACCURACY_TARGET else "🔴",
        },
        {
            "metric":    "Distress Escalation ≤2h (100%)",
            "baseline":  "N/A",
            "target":    "100%",
            "current":   "100%" if live["distress_escalation_100pct"] else "Pending",
            "status":    "🟢" if live["distress_escalation_100pct"] else "🔴",
        },
    ]


def get_financial_summary() -> dict:
    """Business case Section 5 financial summary."""
    return {
        "annual_opex_baseline_cr": 18.6,
        "annual_opex_target_cr":    5.7,
        "annual_saving_cr":         12.9,
        "incremental_revenue_cr":   38.9,
        "npv_3yr_cr":               89,
        "payback_months":           8,
        "team_before":              120,
        "team_after":               20,
        "persistency_before":       "71%",
        "persistency_target":       "88%",
        "persistency_revenue_per_pct_cr": 4.7,
    }
