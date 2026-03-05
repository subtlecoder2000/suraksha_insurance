"""
demo/run_demo.py
End-to-End Demo — Suraksha Life Insurance PROJECT RenewAI v2.0

Runs all 3 business case customer journeys:
  Journey A: Rajesh Kumar — WhatsApp, Term, EMI
  Journey B: Meenakshi Iyer — Bereavement/Distress, Senior RM
  Journey C: Vikram Singh  — ULIP, Email, tech-savvy

Then runs full batch + prints scorecard.
"""
from __future__ import annotations
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.crm import get_policyholder
from agents.orchestrator import orchestrate, run_batch
from agents.email_agent import send_email
from agents.whatsapp_agent import send_whatsapp, handle_reply
from agents.voice_agent import make_call
from agents.human_queue_manager import escalate, get_queue_stats
from critique.critique_agent import evaluate, CritiqueVerdict
from critique.analytics import record as record_critique, get_summary as critique_summary
from monitoring.observability import log_event, EventType, get_system_stats
from monitoring.scorecard import get_scorecard, get_financial_summary, update_metric

DIVIDER = "─" * 70


def print_header():
    print("\n" + "═" * 70)
    print("  🛡  SURAKSHA LIFE INSURANCE — PROJECT RenewAI Demo")
    print("  Agentic AI Renewal System | June 2025 | CONFIDENTIAL")
    print("═" * 70)


def run_journey_a():
    """
    Journey A: Rajesh Kumar
    Dynamic channel by current journey step (email/WhatsApp), Term policy.
    Simulates conversion flow with minimal handoffs.
    """
    print(f"\n{DIVIDER}")
    print("📱 JOURNEY A — Rajesh Kumar | Dynamic Channel | Term Policy")
    print(DIVIDER)

    ph = get_policyholder("POL-001")
    decision = orchestrate(ph)

    print(f"  Journey Step   : {decision.journey_step}")
    print(f"  Channel        : {decision.channel}")
    print(f"  Tone           : {decision.tone}")
    print(f"  Lapse Risk     : {decision.lapse_risk}")
    print(f"  Days to Renewal: {decision.days_to_renewal}")
    print(f"  Agent          : {decision.recommended_agent}")

    # Dispatch by orchestrator recommendation.
    if decision.recommended_agent == "EmailAgent":
        email_result = send_email(
            "POL-001", ph.email, decision.context,
            tone=decision.tone, nudge_number=1,
            offer_ids=[o.offer_id for o in decision.offer_package.offers],
        )
        msg_body = email_result.body
        critique = evaluate(msg_body, decision.context, "POL-001", "EmailAgent", "email")
        log_event(EventType.AGENT_ACTION, "POL-001", "EmailAgent",
                  "sent_renewal_email", "email", "delivered")
        print("  Note           : Journey is currently in email-first step, so EMI WhatsApp simulation is skipped.")
        record_critique(critique)
        print(f"  Critique       : {critique.verdict.value} (score: {critique.overall_score:.0%})")
        return

    wa_msg = send_whatsapp("POL-001", ph.phone, decision.context, tone=decision.tone)

    # Critique quality gate
    critique = evaluate(wa_msg.body, decision.context, "POL-001", "WhatsAppAgent", "whatsapp")
    record_critique(critique)
    print(f"  Critique       : {critique.verdict.value} (score: {critique.overall_score:.0%})")

    if critique.verdict == CritiqueVerdict.BLOCK:
        print(f"  ⛔ BLOCKED — {critique.block_reason}")
        return

    # Simulate customer EMI query reply
    _emi_reply = handle_reply(
        "POL-001", ph.phone,
        "Can I pay in two installments?",
        decision.context,
    )

    log_event(EventType.AGENT_ACTION, "POL-001", "WhatsAppAgent",
              "sent_renewal_message", "whatsapp", "delivered")
    print(f"\n  ✅ Rajesh responded with EMI query — agent replied with EMI option.")
    print(f"  Target: Payment completed at 9:47pm. Journey complete. No human.")


def run_journey_b():
    """
    Journey B: Meenakshi Iyer
    Bereavement detected — instant human queue escalation.
    Business case: 'Priya calls Meenakshi within 90 minutes.'
    """
    print(f"\n{DIVIDER}")
    print("💙 JOURNEY B — Meenakshi Iyer | Bereavement/Distress | Senior RM")
    print(DIVIDER)

    ph = get_policyholder("POL-002")
    decision = orchestrate(ph)

    print(f"  Journey Step   : {decision.journey_step}")
    print(f"  Channel        : {decision.channel}  ← routed to HUMAN (bereavement)")
    print(f"  Tone           : {decision.tone}")
    print(f"  High Complexity: {decision.high_complexity}")
    for r in decision.complexity_reasons:
        print(f"    └── {r}")

    # For high-complexity cases, route directly to human queue.
    briefing = None
    if decision.recommended_agent == "HumanQueueManager":
        print(f"\n  💙 High-complexity case detected — escalating to Human Queue Manager...")
        briefing = escalate(
            "POL-002",
            "Auto-escalated by orchestrator: bereavement/distress complex case."
        )
    else:
        _wa_msg = send_whatsapp("POL-002", ph.phone, decision.context, tone="empathetic")
        distress_reply = handle_reply(
            "POL-002", ph.phone,
            "My husband passed away last month. I don't know what to do with this policy.",
            decision.context,
        )
        if distress_reply.escalate:
            print(f"\n  💙 Distress detected — escalating to Human Queue Manager...")
            briefing = escalate("POL-002", "Bereavement detected: spouse passed away. Immediate human empathy required.")

    if briefing is None:
        print("\n  ⚠️ No escalation was triggered for Journey B; review intent classifier thresholds.")
        return

    log_event(EventType.DISTRESS_FLAG, "POL-002", "WhatsAppAgent",
              "bereavement_detected", "whatsapp", "human_escalated", irdai_relevant=True)
    log_event(EventType.ESCALATION, "POL-002", "HumanQueueManager",
              "routed_to_senior_rm", "human", f"Case: {briefing.case_id}", irdai_relevant=True)

    print(f"\n  🔔 Case: {briefing.case_id} | Specialist: {briefing.specialist_type}")
    print(f"  Priority: {briefing.priority} | SLA: {briefing.sla_hours}h")
    print(f"  Approach: {briefing.recommended_approach[:150]}...")
    print(f"\n  Target: Senior RM calls within 90 min. Offers premium holiday + revival fee waiver.")


def run_journey_c():
    """
    Journey C: Vikram Singh
    ULIP, tech-savvy, email-first, fund dashboard, click-to-pay in 72h.
    Business case: 'Email open-to-pay conversion in 72 hours.'
    """
    print(f"\n{DIVIDER}")
    print("📧 JOURNEY C — Vikram Singh | ULIP | Email | Tech-Savvy")
    print(DIVIDER)

    ph = get_policyholder("POL-003")
    decision = orchestrate(ph)

    print(f"  Journey Step   : {decision.journey_step}")
    print(f"  Channel        : {decision.channel}")
    print(f"  Tone           : {decision.tone}")
    print(f"  Lapse Risk     : {decision.lapse_risk}")
    print(f"  Days to Renewal: {decision.days_to_renewal}")

    # T-45 personalised email with fund performance
    email_result = send_email(
        "POL-003", ph.email, decision.context,
        tone=decision.tone, nudge_number=1,
        offer_ids=[o.offer_id for o in decision.offer_package.offers],
    )

    # Critique
    critique = evaluate(email_result.body, decision.context, "POL-003", "EmailAgent", "email")
    record_critique(critique)
    print(f"  Critique       : {critique.verdict.value} (score: {critique.overall_score:.0%})")

    log_event(EventType.AGENT_ACTION, "POL-003", "EmailAgent",
              "sent_ulip_renewal_email", "email", "delivered")
    print(f"\n  ✅ Email sent with fund performance (ULIP +14% NAV) and 'Renew Now' button.")
    print(f"  Target: Vikram clicks and pays within 72h. Email → Payment in 1 touch.")


def run_scorecard():
    print(f"\n{DIVIDER}")
    print("📊 SUCCESS METRICS SCORECARD (FY25 Baseline → FY26 Target)")
    print(DIVIDER)
    rows = get_scorecard()
    print(f"  {'Metric':<40} {'Baseline':<12} {'Target':<10} {'Current':<10} Status")
    print(f"  {'-'*40} {'-'*12} {'-'*10} {'-'*10} ------")
    for r in rows:
        print(f"  {r['metric']:<40} {r['baseline']:<12} {r['target']:<10} {r['current']:<10} {r['status']}")


def run_financial_summary():
    f = get_financial_summary()
    print(f"\n{DIVIDER}")
    print("💰 FINANCIAL CASE SUMMARY")
    print(DIVIDER)
    print(f"  Annual OPEX: ₹{f['annual_opex_baseline_cr']} Cr → ₹{f['annual_opex_target_cr']} Cr (saving ₹{f['annual_saving_cr']} Cr/yr)")
    print(f"  Incremental Revenue: +₹{f['incremental_revenue_cr']} Cr (net)")
    print(f"  3-Year NPV: ₹{f['npv_3yr_cr']} Crore | Payback: {f['payback_months']} months")
    print(f"  Team: {f['team_before']} → {f['team_after']} | Persistency: {f['persistency_before']} → {f['persistency_target']}")
    print(f"  (Each 1% persistency lift = ₹{f['persistency_revenue_per_pct_cr']} Cr additional premium)"  )


def run_critique_summary():
    cs = critique_summary()
    print(f"\n{DIVIDER}")
    print("🔍 CRITIQUE AGENT QUALITY REPORT")
    print(DIVIDER)
    print(f"  Messages evaluated: {cs['total_evaluated']}")
    print(f"  Pass rate: {cs['pass_rate']} | Regenerate: {cs['regenerate_rate']} | Block: {cs['block_rate']}")
    print(f"  Meets ≥87% target: {'✅ YES' if cs['meets_target'] else '❌ NO'}")
    print(f"  Total cost: {cs['total_cost_inr']}")


def main():
    print_header()
    run_journey_a()
    run_journey_b()
    run_journey_c()

    # Quick batch run
    print(f"\n{DIVIDER}")
    print("🔄 BATCH RUN — All Policyholders in Renewal Pipeline")
    print(DIVIDER)
    decisions = run_batch(45)
    print(f"  Processed {len(decisions)} policyholders")
    human_q = [d for d in decisions if d.recommended_agent == "HumanQueueManager"]
    ai_handled = [d for d in decisions if d.recommended_agent != "HumanQueueManager"]
    escalation_rate = (len(human_q) / len(decisions)) if decisions else 0.0
    update_metric("escalation_rate", escalation_rate)
    print(f"  AI handled: {len(ai_handled)} | Human queue: {len(human_q)}")
    print(f"  Escalation rate: {escalation_rate:.0%} (target ≤10%)")

    queue_stats = get_queue_stats()
    print(f"  Human queue: {queue_stats['open']} open | {queue_stats['urgent']} urgent")

    run_scorecard()
    run_financial_summary()
    run_critique_summary()

    sys_stats = get_system_stats()
    print(f"\n{DIVIDER}")
    print("🔭 OBSERVABILITY — Audit Log")
    print(DIVIDER)
    print(f"  Total events: {sys_stats['total_events']}")
    print(f"  IRDAI-relevant: {sys_stats['irdai_relevant']}")
    print(f"  Distress events: {sys_stats['distress_events']}")
    print(f"  Escalations: {sys_stats['escalations']}")

    print(f"\n{'═'*70}")
    print("  ✅ Demo complete. Suraksha Life Insurance — PROJECT RenewAI v2.0")
    print("═" * 70 + "\n")


if __name__ == "__main__":
    main()
