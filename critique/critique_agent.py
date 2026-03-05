"""
critique/critique_agent.py
Critique Agent — Layer 3.5 Quality Gate
Suraksha Life Insurance — PROJECT RenewAI v2.0

Every AI-generated message passes through this 9-point checklist
BEFORE being delivered to the customer.

Outcomes:
  PASS       → Message delivered (cost: ~₹0.035/msg addon)
  REGENERATE → Loop back to source agent with specific feedback
  BLOCK      → Route to Human Queue (hard fail)

From business case:
  "Critique Agent reviews EVERY message before delivery"
  "Accuracy: 87% → 95%+ | Cost: +₹35–50/yr additional LLM"
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

from critique.checklist import run_all_checks, CheckResult
from config.settings import CRITIQUE_PASS_THRESHOLD, CRITIQUE_COST_PER_MSG_INR


class CritiqueVerdict(str, Enum):
    PASS       = "PASS"
    REGENERATE = "REGENERATE"
    BLOCK      = "BLOCK"


@dataclass
class CritiqueResult:
    verdict: CritiqueVerdict
    overall_score: float            # 0.0 – 1.0
    checks: list[CheckResult]
    passed_checks: list[str]
    failed_checks: list[str]
    block_reason: Optional[str]
    regenerate_feedback: str        # Specific feedback sent back to source agent
    cost_inr: float                 # ₹0.035 per evaluation
    timestamp: datetime = field(default_factory=datetime.now)
    policy_id: str = ""
    agent_name: str = ""
    channel: str = ""


def evaluate(
    message: str,
    context: dict,
    policy_id: str = "",
    agent_name: str = "",
    channel: str = "",
    prior_messages: list[str] = None,
) -> CritiqueResult:
    """
    Run the 9-point Critique Agent checklist on a proposed AI message.

    Returns PASS / REGENERATE / BLOCK with detailed feedback.
    """
    checks = run_all_checks(message, context, prior_messages or [])

    passed = [c for c in checks if c.passed]
    failed = [c for c in checks if not c.passed]

    # Hard BLOCK criteria (any single critical failure → BLOCK)
    block_checks = [c for c in failed if c.severity == "CRITICAL"]
    if block_checks:
        block_reason = "; ".join(c.feedback for c in block_checks)
        return CritiqueResult(
            verdict=CritiqueVerdict.BLOCK,
            overall_score=round(len(passed) / len(checks), 3),
            checks=checks,
            passed_checks=[c.check_name for c in passed],
            failed_checks=[c.check_name for c in failed],
            block_reason=block_reason,
            regenerate_feedback="",
            cost_inr=CRITIQUE_COST_PER_MSG_INR,
            policy_id=policy_id,
            agent_name=agent_name,
            channel=channel,
        )

    overall_score = round(len(passed) / len(checks), 3)

    # PASS
    if overall_score >= CRITIQUE_PASS_THRESHOLD:
        return CritiqueResult(
            verdict=CritiqueVerdict.PASS,
            overall_score=overall_score,
            checks=checks,
            passed_checks=[c.check_name for c in passed],
            failed_checks=[c.check_name for c in failed],
            block_reason=None,
            regenerate_feedback="",
            cost_inr=CRITIQUE_COST_PER_MSG_INR,
            policy_id=policy_id,
            agent_name=agent_name,
            channel=channel,
        )

    # REGENERATE — build specific feedback for source agent
    feedback_lines = [f"• [{c.check_name}] {c.feedback}" for c in failed]
    regenerate_feedback = (
        f"Message quality score: {overall_score:.0%} (threshold: {CRITIQUE_PASS_THRESHOLD:.0%}). "
        f"Please address the following before resending:\n" + "\n".join(feedback_lines)
    )

    return CritiqueResult(
        verdict=CritiqueVerdict.REGENERATE,
        overall_score=overall_score,
        checks=checks,
        passed_checks=[c.check_name for c in passed],
        failed_checks=[c.check_name for c in failed],
        block_reason=None,
        regenerate_feedback=regenerate_feedback,
        cost_inr=CRITIQUE_COST_PER_MSG_INR,
        policy_id=policy_id,
        agent_name=agent_name,
        channel=channel,
    )
