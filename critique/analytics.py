"""
critique/analytics.py
Critique Agent Analytics — Suraksha Life Insurance PROJECT RenewAI v2.0

Tracks: pass rate, block rate, regeneration rate, top failure categories,
agent-wise quality scores. Feeds into Layer 6 Quality Evaluation dashboard.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from collections import defaultdict
from datetime import datetime
from critique.critique_agent import CritiqueResult, CritiqueVerdict


@dataclass
class CritiqueStats:
    total_evaluated: int = 0
    total_pass: int = 0
    total_regenerate: int = 0
    total_block: int = 0
    check_failure_counts: dict = field(default_factory=lambda: defaultdict(int))
    agent_pass_counts: dict = field(default_factory=lambda: defaultdict(int))
    agent_total_counts: dict = field(default_factory=lambda: defaultdict(int))
    total_cost_inr: float = 0.0
    history: list[dict] = field(default_factory=list)


_STATS = CritiqueStats()


def record(result: CritiqueResult) -> None:
    """Record a critique result into analytics."""
    _STATS.total_evaluated += 1
    _STATS.total_cost_inr += result.cost_inr

    if result.verdict == CritiqueVerdict.PASS:
        _STATS.total_pass += 1
    elif result.verdict == CritiqueVerdict.REGENERATE:
        _STATS.total_regenerate += 1
    else:
        _STATS.total_block += 1

    for chk in result.failed_checks:
        _STATS.check_failure_counts[chk] += 1

    if result.agent_name:
        _STATS.agent_total_counts[result.agent_name] += 1
        if result.verdict == CritiqueVerdict.PASS:
            _STATS.agent_pass_counts[result.agent_name] += 1

    _STATS.history.append({
        "timestamp": result.timestamp.isoformat(),
        "policy_id": result.policy_id,
        "agent": result.agent_name,
        "channel": result.channel,
        "verdict": result.verdict.value,
        "score": result.overall_score,
        "failed_checks": result.failed_checks,
    })


def get_summary() -> dict:
    s = _STATS
    total = s.total_evaluated or 1
    top_failures = sorted(s.check_failure_counts.items(), key=lambda x: x[1], reverse=True)

    # Agent-wise quality
    agent_quality = {}
    for agent in s.agent_total_counts:
        t = s.agent_total_counts[agent]
        p = s.agent_pass_counts.get(agent, 0)
        agent_quality[agent] = {
            "total": t,
            "pass_rate": f"{p/t:.1%}" if t else "N/A",
        }

    return {
        "total_evaluated":    s.total_evaluated,
        "pass_rate":          f"{s.total_pass / total:.1%}",
        "regenerate_rate":    f"{s.total_regenerate / total:.1%}",
        "block_rate":         f"{s.total_block / total:.1%}",
        "total_cost_inr":     f"₹{s.total_cost_inr:.2f}",
        "top_failure_checks": [{"check": k, "failures": v} for k, v in top_failures[:5]],
        "agent_quality":      agent_quality,
        "target_pass_rate":   "87%",
        "meets_target":       s.total_pass / total >= 0.87,
    }


def get_recent_history(n: int = 20) -> list[dict]:
    return _STATS.history[-n:]


def reset_stats() -> None:
    """Test/helper utility to reset critique analytics state."""
    global _STATS
    _STATS = CritiqueStats()
