"""
agents/prompt_generator_agent.py
Prompt Generator Meta-Agent

Generates optimized system prompts for all agents based on:
  - Customer feedback and conversation outcomes
  - Critique failure patterns
  - Performance metrics
  - Weekly improvement cycles
"""
from __future__ import annotations
import json
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field

from services.prompt_manager import (
    get_active_prompt, get_all_prompts, update_prompt, incorporate_feedback,
)
from critique.analytics import get_summary as critique_summary
from monitoring.tracer import get_trace_stats


@dataclass
class PromptImprovement:
    agent_name: str
    current_version: int
    new_version: int
    changes_summary: str
    feedback_items: list[str]
    improvement_areas: list[str]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


# ── Feedback Collection ───────────────────────────────────────────────────────

_FEEDBACK_STORE: list[dict] = []


def collect_feedback(policy_id: str, agent_name: str, feedback_type: str,
                     feedback_text: str, rating: int = 0):
    """Collect customer/system feedback for prompt improvement."""
    _FEEDBACK_STORE.append({
        "policy_id": policy_id,
        "agent_name": agent_name,
        "feedback_type": feedback_type,  # customer, critique_failure, system
        "feedback_text": feedback_text,
        "rating": rating,
        "timestamp": datetime.now().isoformat(),
        "incorporated": False,
    })


def get_pending_feedback(agent_name: str = None) -> list[dict]:
    """Get all pending (not yet incorporated) feedback."""
    items = [f for f in _FEEDBACK_STORE if not f["incorporated"]]
    if agent_name:
        items = [f for f in items if f["agent_name"] == agent_name]
    return items


# ── Prompt Analysis ───────────────────────────────────────────────────────────

def analyze_critique_patterns() -> dict:
    """Analyze critique failure patterns to identify prompt improvement areas."""
    summary = critique_summary()
    patterns = {
        "total_evaluations": summary.get("total", 0),
        "pass_rate": summary.get("pass_rate", 0),
        "common_failures": [],
        "improvement_suggestions": [],
    }

    # Identify most common failure categories
    by_check = summary.get("by_check", {})
    for check_name, stats in by_check.items() if isinstance(by_check, dict) else []:
        if stats.get("fail_rate", 0) > 0.1:
            patterns["common_failures"].append({
                "check": check_name,
                "fail_rate": stats["fail_rate"],
            })
            patterns["improvement_suggestions"].append(
                f"Improve {check_name}: {stats.get('fail_rate', 0):.0%} failure rate"
            )

    return patterns


def generate_improved_prompt(agent_name: str, feedback_items: list[str] = None) -> PromptImprovement:
    """
    Generate an improved system prompt for the specified agent.

    This is the core Prompt Generator Agent logic:
    1. Analyze current prompt
    2. Review feedback and critique patterns
    3. Generate improved prompt with specific enhancements
    4. Version and store the new prompt
    """
    current_prompt = get_active_prompt(agent_name)
    if not current_prompt:
        return None

    # Gather feedback
    if feedback_items is None:
        pending = get_pending_feedback(agent_name)
        feedback_items = [f["feedback_text"] for f in pending]

    # Analyze critique patterns
    patterns = analyze_critique_patterns()

    # Build improvement areas
    improvement_areas = []
    if patterns.get("common_failures"):
        for failure in patterns["common_failures"]:
            improvement_areas.append(f"Address {failure['check']} failures ({failure['fail_rate']:.0%} fail rate)")

    for fb in feedback_items[:5]:
        improvement_areas.append(f"Customer feedback: {fb[:100]}")

    # Generate improved prompt (in production this would call an LLM)
    # For now, we append structured improvements
    improvements_text = "\n".join(f"  - {area}" for area in improvement_areas)

    improved_prompt = (
        f"{current_prompt}\n\n"
        f"--- WEEKLY IMPROVEMENT ({datetime.now().strftime('%Y-%m-%d')}) ---\n"
        f"Based on {len(feedback_items)} feedback items and critique analysis:\n"
        f"{improvements_text}\n\n"
        f"ADDITIONAL GUIDELINES:\n"
    )

    # Add specific guidelines based on feedback patterns
    if any("tone" in f.lower() for f in feedback_items):
        improved_prompt += "- Pay extra attention to tone matching customer's emotional state.\n"
    if any("offer" in f.lower() or "discount" in f.lower() for f in feedback_items):
        improved_prompt += "- Ensure all offer values are accurately calculated and clearly presented.\n"
    if any("language" in f.lower() for f in feedback_items):
        improved_prompt += "- Double-check language appropriateness for the customer's preferred language.\n"

    improved_prompt += "- Always validate all financial figures against policy documents before including.\n"

    # Get current version number
    all_prompts = get_all_prompts()
    current_version = all_prompts.get(agent_name, {}).get("active_version", 1)

    # Store the new prompt
    new_version = update_prompt(
        agent_name,
        improved_prompt,
        description=f"Auto-generated improvement - {len(feedback_items)} feedback items, {len(improvement_areas)} areas",
        created_by="PromptGeneratorAgent",
        feedback=feedback_items,
    )

    # Mark feedback as incorporated
    for fb in _FEEDBACK_STORE:
        if fb["agent_name"] == agent_name and not fb["incorporated"]:
            fb["incorporated"] = True

    return PromptImprovement(
        agent_name=agent_name,
        current_version=current_version,
        new_version=new_version.version,
        changes_summary=f"Improved {len(improvement_areas)} areas based on {len(feedback_items)} feedback items",
        feedback_items=feedback_items,
        improvement_areas=improvement_areas,
    )


def run_weekly_improvement() -> list[PromptImprovement]:
    """
    Run the weekly prompt improvement cycle for ALL agents.
    Called by a scheduler or manually from the dashboard.
    """
    all_prompts = get_all_prompts()
    improvements = []

    for agent_name in all_prompts.keys():
        pending = get_pending_feedback(agent_name)
        if pending:
            improvement = generate_improved_prompt(
                agent_name,
                [f["feedback_text"] for f in pending]
            )
            if improvement:
                improvements.append(improvement)

    return improvements


def get_improvement_dashboard() -> dict:
    """Get dashboard data for the prompt improvement system."""
    all_prompts = get_all_prompts()
    pending_feedback = get_pending_feedback()

    agents_data = []
    for name, data in all_prompts.items():
        agent_feedback = [f for f in pending_feedback if f["agent_name"] == name]
        agents_data.append({
            "agent_name": name,
            "active_version": data["active_version"],
            "total_versions": data["total_versions"],
            "performance_score": data["performance_score"],
            "pending_feedback_count": len(agent_feedback),
            "prompt_preview": data["system_prompt"][:200] + "...",
        })

    return {
        "agents": agents_data,
        "total_pending_feedback": len(pending_feedback),
        "last_improvement_run": datetime.now().isoformat(),
        "critique_patterns": analyze_critique_patterns(),
    }
