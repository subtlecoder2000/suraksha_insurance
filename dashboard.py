"""
dashboard.py
Streamlit Dashboard — Suraksha Life Insurance PROJECT RenewAI v2.0

Visualises:
 • Renewal Pipeline Overview (KPIs)
 • Success Metrics Scorecard (FY25 Baseline → FY26 Target)
 • Live Batch Simulation (run all 3 journeys)
 • Human Queue (distress escalations)
 • Critique Agent Results
 • Audit Log
 • Financial Business Case
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import pandas as pd
from datetime import date, timedelta

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Suraksha Life Insurance — PROJECT RenewAI",
    page_icon="🛡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Imports ───────────────────────────────────────────────────────────────────
from data.crm import (get_all_policyholders, get_pipeline_summary,
                      get_distressed, get_lapsed, get_due_within,
                      get_persistency_rate)
from agents.orchestrator import orchestrate, run_batch
from agents.email_agent import send_email
from agents.whatsapp_agent import send_whatsapp, handle_reply
from agents.voice_agent import make_call
from agents.human_queue_manager import escalate, get_queue, get_queue_stats
from critique.critique_agent import evaluate, CritiqueVerdict
from critique.analytics import record as record_critique, get_summary as critique_summary
from monitoring.scorecard import get_scorecard, get_financial_summary
from monitoring.observability import log_event, EventType, get_system_stats

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/color/96/shield.png", width=60)
    st.markdown("## 🛡 PROJECT RenewAI")
    st.markdown("**Suraksha Life Insurance**")
    st.caption("Est. 2003 | Mumbai | 4.8M Policyholders")
    st.divider()
    page = st.radio("Navigation", [
        "📊 Dashboard Overview",
        "🔄 Run Journeys (Demo)",
        "👥 Policyholder Pipeline",
        "📋 Success Metrics Scorecard",
        "🔍 Critique Agent",
        "🔔 Human Queue",
        "💰 Financial Business Case",
        "🔭 Audit Log",
    ])
    st.divider()
    st.caption(f"RenewAI v2.0 | June 2025 | CONFIDENTIAL")

# ── Helper: coloured metric ───────────────────────────────────────────────────
def metric_card(label, value, delta=None, help_txt=""):
    st.metric(label=label, value=value, delta=delta, help=help_txt)

# ═════════════════════════════════════════════════════════════════════════════
# PAGE: Dashboard Overview
# ═════════════════════════════════════════════════════════════════════════════
if page == "📊 Dashboard Overview":
    st.title("🛡 Suraksha Life Insurance — PROJECT RenewAI")
    st.markdown("**Transforming the Policy Renewal Function with Agentic AI** | 120→20 Agents | ₹89Cr 3-Year NPV")
    st.divider()

    pipeline = get_pipeline_summary()
    fin = get_financial_summary()

    # Row 1: Business case headline metrics
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Total Policyholders", "4.8M", help="As per FY25 data")
    col2.metric("Annual Renewal Pool", "14.4L", help="Policies due for renewal per year")
    col3.metric("Current Persistency", "71%", delta="+17pp target", delta_color="normal")
    col4.metric("Target Persistency", "88%", help="FY26 target")
    col5.metric("Team: Before → After", "120 → 20", help="Renewal ops headcount")
    col6.metric("3-Year NPV", "₹89 Cr", help="Business case projection")

    st.divider()
    st.subheader("🔄 Renewal Pipeline (Demo CRM — 10 Policyholders)")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total in Pipeline", pipeline["total"])
    col2.metric("✅ Paid", pipeline["paid"], delta="done")
    col3.metric("⏳ Pending", pipeline["pending"])
    col4.metric("❌ Failed/Lapsed", pipeline["lapsed"])
    col5.metric("🚨 High Risk", pipeline["high_risk"])

    st.divider()
    col1, col2, col3 = st.columns(3)
    col1.metric("Due in 7 Days", pipeline["due_7_days"])
    col2.metric("Due in 30 Days", pipeline["due_30_days"])
    col3.metric("💙 Distress Cases", pipeline["distressed"])

    st.divider()
    st.subheader("🏆 The Business Case at a Glance")
    biz_df = pd.DataFrame([
        {"Category": "Annual OPEX", "Before": "₹18.6 Cr", "After": "₹5.7 Cr", "Change": "▼ ₹12.9 Cr saved"},
        {"Category": "13th Month Persistency", "Before": "71%", "After": "88%", "Change": "+17pp"},
        {"Category": "Policies Renewed (annually)", "Before": "10.22L", "After": "12.67L", "Change": "+2.45L"},
        {"Category": "Incremental Premium Income (net)", "Before": "—", "After": "₹38.9 Cr/yr", "Change": "New revenue"},
        {"Category": "Cost per Renewal", "Before": "₹182", "After": "₹45", "Change": "▼ 75%"},
        {"Category": "Renewal Team Size", "Before": "120", "After": "20", "Change": "▼ 83%"},
        {"Category": "AI Availability", "Before": "8am–8pm", "After": "24×7×365", "Change": "Always on"},
    ])
    st.dataframe(biz_df, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("🗺 The Intelligent Renewal Journey (T-45 to Post-Lapse)")
    journey_df = pd.DataFrame([
        {"Trigger":        "T-45 Days",
         "Channel":        "📧 Email",
         "AI Action":      "Personalized renewal reminder with benefit recap, payment link",
         "Branch Logic":   "If opened within 48h → wait. If not → WhatsApp at T-30"},
        {"Trigger":        "T-30 Days",
         "Channel":        "💬 WhatsApp",
         "AI Action":      "'Hi Rajesh-ji! 🛡 Your Term Shield renews on 15 March. Tap to pay 👇'",
         "Branch Logic":   "If customer responds → WA Agent handles. If unread 24h → Voice T-20"},
        {"Trigger":        "T-20 Days",
         "Channel":        "📞 Voice",
         "AI Action":      "Outbound AI call at preferred time. Handles top-12 objections. Offers EMI.",
         "Branch Logic":   "If payment confirmed → end. 3 fails → T-10 escalation"},
        {"Trigger":        "T-10 Days",
         "Channel":        "💬 WhatsApp + 📧 Email",
         "AI Action":      "'Last chance' — ECS mandate link, UPI AutoPay, grace period info",
         "Branch Logic":   "Financial hardship → Human Queue. No response → T-5"},
        {"Trigger":        "T-5 Days",
         "Channel":        "📞 Voice + 💬 WhatsApp",
         "AI Action":      "Urgent dual-channel. 30-day grace period, premium holiday, partial payment",
         "Branch Logic":   "Human RRM if unresolved. Briefing auto-prepared."},
        {"Trigger":        "Post-Lapse",
         "Channel":        "🔁 Multi-channel",
         "AI Action":      "90-day revival campaign. Penalty waiver quotation. Medical re-u/w check.",
         "Branch Logic":   "Revival cases requiring u/w → Revival Specialist"},
    ])
    st.dataframe(journey_df, use_container_width=True, hide_index=True)

# ═════════════════════════════════════════════════════════════════════════════
# PAGE: Run Journeys (Demo)
# ═════════════════════════════════════════════════════════════════════════════
elif page == "🔄 Run Journeys (Demo)":
    st.title("🔄 Run Customer Journeys — Business Case Scenarios")
    st.markdown("Reproduce the 3 exact customer journeys from the business case document.")
    st.divider()

    from data.crm import get_policyholder

    tab_a, tab_b, tab_c, tab_batch = st.tabs([
        "📱 Journey A: Rajesh (WhatsApp / EMI)",
        "💙 Journey B: Meenakshi (Bereavement)",
        "📧 Journey C: Vikram (ULIP / Email)",
        "🔄 Full Batch Run",
    ])

    # ── JOURNEY A ──────────────────────────────────────────────────────────────
    with tab_a:
        st.subheader("📱 Journey A: Rajesh Kumar | WhatsApp | Term | EMI")
        st.info(
            "**Business case says:** Rajesh is a WhatsApp-first, evening-available customer. "
            "He asks 'Can I pay in two instalments?' — the WA Agent replies immediately. "
            "He pays at 9:47pm. Journey complete. **No human involved.**"
        )
        if st.button("▶ Run Journey A", key="btn_a"):
            ph = get_policyholder("POL-001")
            decision = orchestrate(ph)

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Journey Step", decision.journey_step)
            col2.metric("Channel", decision.channel.upper())
            col3.metric("Tone", decision.tone.capitalize())
            col4.metric("Lapse Risk", decision.lapse_risk)

            # WA Message
            wa_msg = send_whatsapp("POL-001", ph.phone, decision.context, tone=decision.tone)
            critique = evaluate(wa_msg.body, decision.context, "POL-001", "WhatsAppAgent", "whatsapp")
            record_critique(critique)

            st.markdown("#### 💬 WhatsApp Message Sent")
            st.code(wa_msg.body, language="")

            verdict_color = "🟢" if critique.verdict == CritiqueVerdict.PASS else "🔴"
            st.markdown(f"**Critique Agent:** {verdict_color} {critique.verdict.value} | Score: {critique.overall_score:.0%}")

            # Customer EMI reply
            st.markdown("#### 📥 Customer Reply: 'Can I pay in two instalments?'")
            reply = handle_reply("POL-001", ph.phone, "Can I pay in two installments?", decision.context)
            st.code(reply.body, language="")
            st.success("✅ EMI option offered. Rajesh pays at 9:47pm. Journey complete.")

    # ── JOURNEY B ──────────────────────────────────────────────────────────────
    with tab_b:
        st.subheader("💙 Journey B: Meenakshi Iyer | Bereavement | Senior RM")
        st.info(
            "**Business case says:** Meenakshi replies 'My husband passed away last month.' "
            "Content safety detects 'bereavement' in <1 second. Escalated to Senior RM. "
            "**Priya calls Meenakshi within 90 minutes. Offers premium holiday + revival fee waiver.**"
        )
        if st.button("▶ Run Journey B", key="btn_b"):
            ph = get_policyholder("POL-002")
            decision = orchestrate(ph)

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Journey Step", decision.journey_step)
            col2.metric("Channel", decision.channel.upper())
            col3.metric("Tone", decision.tone.capitalize())
            col4.metric("High Complexity", "✅ YES")

            st.markdown("#### 💜 Complexity Reasons Detected")
            for r in decision.complexity_reasons:
                st.warning(r)

            # First WA contact
            wa_msg = send_whatsapp("POL-002", ph.phone, decision.context, tone="empathetic")
            st.markdown("#### 💬 Initial WhatsApp")
            st.code(wa_msg.body[:400], language="")

            # Customer distress reply
            st.markdown("#### 📥 Customer Reply: Bereavement")
            reply = handle_reply(
                "POL-002", ph.phone,
                "My husband passed away last month. I don't know what to do with this policy.",
                decision.context,
            )
            st.code(reply.body, language="")

            # Escalate
            briefing = escalate("POL-002", "Bereavement: spouse deceased. Immediate human empathy.")
            log_event(EventType.DISTRESS_FLAG, "POL-002", "WhatsAppAgent",
                      "bereavement", "whatsapp", "escalated", irdai_relevant=True)

            st.error(f"🔔 **ESCALATED** → Case: {briefing.case_id} | Specialist: {briefing.specialist_type} | SLA: {briefing.sla_hours}h")
            st.markdown("#### 📋 Human Specialist Briefing Note")
            with st.expander("View Full Briefing"):
                st.text(briefing.policy_summary)
                st.markdown(f"**Recommended Approach:** {briefing.recommended_approach}")
            st.success("✅ Senior RM calls within 90 min. Premium holiday + fee waiver offered.")

    # ── JOURNEY C ──────────────────────────────────────────────────────────────
    with tab_c:
        st.subheader("📧 Journey C: Vikram Singh | ULIP | Email | Tech-Savvy")
        st.info(
            "**Business case says:** Vikram receives personalised email with fund performance dashboard, "
            "NAV, and 'Renew Now' button. He clicks, sees +14% portfolio, and pays in 3 minutes. "
            "**Email open-to-pay conversion in 72 hours.**"
        )
        if st.button("▶ Run Journey C", key="btn_c"):
            ph = get_policyholder("POL-003")
            decision = orchestrate(ph)

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Journey Step", decision.journey_step)
            col2.metric("Channel", decision.channel.upper())
            col3.metric("Tone", decision.tone.capitalize())
            col4.metric("No-Claim Years", ph.years_no_claim)

            email = send_email("POL-003", ph.email, decision.context, tone=decision.tone, nudge_number=1,
                               offer_ids=[o.offer_id for o in decision.offer_package.offers])
            critique = evaluate(email.body, decision.context, "POL-003", "EmailAgent", "email")
            record_critique(critique)

            st.markdown(f"#### 📧 Email Subject: *{email.subject}*")
            st.code(email.body, language="")
            verdict_color = "🟢" if critique.verdict == CritiqueVerdict.PASS else "🔴"
            st.markdown(f"**Critique Agent:** {verdict_color} {critique.verdict.value} | Score: {critique.overall_score:.0%}")
            st.success("✅ Vikram sees ULIP +14% NAV, clicks 'Renew Now', pays in 3 minutes.")

    # ── BATCH RUN ──────────────────────────────────────────────────────────────
    with tab_batch:
        st.subheader("🔄 Full Batch Orchestration — All Policyholders")
        if st.button("▶ Run Batch (All 10 PH)", key="btn_batch"):
            with st.spinner("Running orchestration..."):
                decisions = run_batch(45)

            data = []
            for d in decisions:
                data.append({
                    "Policy ID":     d.policy_id,
                    "Customer":      d.customer_name,
                    "Journey Step":  d.journey_step,
                    "Channel":       d.channel,
                    "Tone":          d.tone,
                    "Risk":          d.lapse_risk,
                    "Agent":         d.recommended_agent,
                    "Days to Renew": max(d.days_to_renewal, 0),
                })
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True, hide_index=True)

            total = len(decisions)
            human = len([d for d in decisions if d.recommended_agent == "HumanQueueManager"])
            st.metric("Total Policyholders Processed", total)
            col1, col2, col3 = st.columns(3)
            col1.metric("AI Handled", total - human)
            col2.metric("Human Queue", human)
            col3.metric("Escalation Rate", f"{human/total:.0%}")

# ═════════════════════════════════════════════════════════════════════════════
# PAGE: Policyholder Pipeline
# ═════════════════════════════════════════════════════════════════════════════
elif page == "👥 Policyholder Pipeline":
    st.title("👥 Policyholder Renewal Pipeline")
    phs = get_all_policyholders()
    today = date.today()

    data = []
    for ph in phs:
        days = (ph.renewal_due_date - today).days
        data.append({
            "Policy ID":   ph.policy_id,
            "Policy No":   ph.policy_number,
            "Name":        ph.name,
            "Age":         ph.age,
            "Type":        ph.policy_type,
            "Product":     ph.policy_product_name,
            "Premium (₹)": f"{ph.annual_premium:,.0f}",
            "Renewal Due": ph.renewal_due_date.strftime("%-d %b %Y"),
            "Days Left":   days,
            "Risk":        ph.lapse_risk,
            "Tier":        ph.loyalty_tier,
            "Channel":     ph.preferred_channel,
            "Language":    ph.language,
            "Payment":     ph.last_payment_status,
            "Distress":    "⚠️ YES" if (ph.distress_flag or ph.bereavement) else "—",
        })
    df = pd.DataFrame(data)

    # Filters
    col1, col2, col3 = st.columns(3)
    risk_filter = col1.multiselect("Risk Level", ["Low", "Medium", "High"],
                                    default=["Low", "Medium", "High"])
    ch_filter = col2.multiselect("Channel", ["email", "whatsapp", "voice"],
                                  default=["email", "whatsapp", "voice"])
    status_filter = col3.multiselect("Payment Status", ["Paid", "Pending", "Failed", "NA"],
                                      default=["Paid", "Pending", "Failed", "NA"])

    df_filtered = df[
        df["Risk"].isin(risk_filter) &
        df["Channel"].isin(ch_filter) &
        df["Payment"].isin(status_filter)
    ]
    st.dataframe(df_filtered, use_container_width=True, hide_index=True)
    st.caption(f"Showing {len(df_filtered)} of {len(df)} policyholders")

# ═════════════════════════════════════════════════════════════════════════════
# PAGE: Success Metrics Scorecard
# ═════════════════════════════════════════════════════════════════════════════
elif page == "📋 Success Metrics Scorecard":
    st.title("📋 Success Metrics Scorecard — Section 8")
    st.markdown("*Board Risk Committee review (monthly/quarterly). Based on business case Section 8.*")

    scorecard = get_scorecard()
    df = pd.DataFrame(scorecard)
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("📊 4-Agent Architecture")
    arch_df = pd.DataFrame([
        {
            "Agent": "Orchestrator Agent",
            "Responsibility": "Segments each renewal case — decides channel, timing, language, tone. Activates T-45.",
            "Escalates When": "Detects high-complexity flags",
        },
        {
            "Agent": "Email Agent",
            "Responsibility": "Personalized renewal emails in English, Hindi, regional. Tracks opens/clicks.",
            "Escalates When": "No open after 3 attempts; payment link error; complaint reply",
        },
        {
            "Agent": "WhatsApp Agent",
            "Responsibility": "Conversational WA flow. Payment QR, EMI, objection handling, memory across sessions.",
            "Escalates When": "Sentiment turns negative; hardship, illness, dispute mentioned",
        },
        {
            "Agent": "Voice Agent",
            "Responsibility": "AI outbound calls at preferred time. Handles top-12 objections. EMI, AutoPay. 9 languages.",
            "Escalates When": "Caller requests human; distress keywords; 3 objections unresolved",
        },
        {
            "Agent": "Human Queue Manager",
            "Responsibility": "Routes ~10% escalated cases. Auto-prepares briefing: policy, prior AI chats, sentiment, approach.",
            "Escalates When": "Terminal node — human handoff",
        },
    ])
    st.dataframe(arch_df, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("👩‍💼 The New Team of 20")
    team_df = pd.DataFrame([
        {"Role": "Senior Renewal Relationship Managers", "Count": 8, "CTC": "₹7.2L–₹10L",
         "Focus": "HNI, ₹1L+ premium, bereavement, emotionally complex"},
        {"Role": "Revival Specialists",                  "Count": 5, "CTC": "₹7.5L–₹9.5L",
         "Focus": "Lapsed policies, medical re-underwriting, penalty waivers"},
        {"Role": "Compliance & Grievance Handler",        "Count": 2, "CTC": "₹8L–₹11L",
         "Focus": "IRDAI complaints, mis-selling, ombudsman"},
        {"Role": "AI Operations & Quality Manager",       "Count": 3, "CTC": "₹10L–₹14L",
         "Focus": "Monitor AI performance, tune objection library, audit logs"},
        {"Role": "Renewal Head (Business Owner)",         "Count": 1, "CTC": "₹22L–₹28L",
         "Focus": "P&L ownership, IRDAI relationships, strategy"},
        {"Role": "AI Trainer / Prompt Engineer (external)", "Count": 1, "CTC": "₹6L retainer",
         "Focus": "Prompt tuning, objection library, model fine-tuning"},
    ])
    st.dataframe(team_df, use_container_width=True, hide_index=True)

# ═════════════════════════════════════════════════════════════════════════════
# PAGE: Critique Agent
# ═════════════════════════════════════════════════════════════════════════════
elif page == "🔍 Critique Agent":
    st.title("🔍 Critique Agent Quality Gate — Layer 3.5")
    st.markdown(
        "Every AI-generated message passes through a **9-point checklist** before delivery. "
        "Outcome: **PASS → deliver | REGENERATE → fix & retry | BLOCK → human queue**"
    )

    cs = critique_summary()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Messages Evaluated", cs["total_evaluated"])
    col2.metric("Pass Rate", cs["pass_rate"])
    col3.metric("Regenerate Rate", cs["regenerate_rate"])
    col4.metric("Block Rate", cs["block_rate"])

    meets = cs["meets_target"]
    if meets and cs["total_evaluated"] > 0:
        st.success("✅ Meets ≥87% AI accuracy target (business case Section 8)")
    elif cs["total_evaluated"] == 0:
        st.info("No messages evaluated yet — run journeys first.")
    else:
        st.warning("⚠️ Below 87% accuracy target — AI Ops review required")

    st.divider()
    st.subheader("🔟 The 9-Point Checklist")
    checklist_df = pd.DataFrame([
        {"#": 1, "Check": "Factual Accuracy",         "Severity": "CRITICAL",
         "Description": "Facts from RAG sources only — no AI hallucination on premium/sum assured"},
        {"#": 2, "Check": "Tone-Segment Alignment",   "Severity": "HIGH",
         "Description": "Wealth Builder = professional; Budget Conscious = affordability-focused"},
        {"#": 3, "Check": "Emotional Control",        "Severity": "CRITICAL",
         "Description": "No cheerful tone if customer expressed distress or bereavement"},
        {"#": 4, "Check": "Logical Coherence",        "Severity": "HIGH",
         "Description": "No contradiction with prior messages (e.g. different discount %)"},
        {"#": 5, "Check": "Regulatory Compliance",    "Severity": "CRITICAL",
         "Description": "No IRDAI violations — no guaranteed returns, no false promises"},
        {"#": 6, "Check": "Language Quality",         "Severity": "MEDIUM",
         "Description": "Grammar, cultural fit, correct language for customer preference (9 languages)"},
        {"#": 7, "Check": "Personalization Accuracy", "Severity": "HIGH",
         "Description": "Correct name, policy number, product name, premium amount"},
        {"#": 8, "Check": "Conversation Continuity",  "Severity": "MEDIUM",
         "Description": "Addresses previous objections, not a stale template"},
        {"#": 9, "Check": "Data Safety (DPDPA 2023)", "Severity": "CRITICAL",
         "Description": "No PII in message — Aadhaar, PAN, bank account, phone, email"},
    ])
    st.dataframe(checklist_df, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("🧪 Live Message Test")
    with st.expander("Test a message through the Critique Agent"):
        test_msg = st.text_area("Enter message to evaluate:",
                                 value="Dear Rajesh,\n\nYour Suraksha Term Shield policy renews on 15 March. Premium: ₹24,000. Cover: ₹1 Crore.\n\nPay now or choose 3 easy EMI instalments of ₹8,000 each.\n\nRenew now: pay.suraksha.in/pol-001")
        test_ctx = {"name": "Rajesh Kumar", "premium": 24000, "sum_assured": 10000000,
                    "renewal_date": "15 March 2026", "segment": "Budget Conscious",
                    "language": "English", "tone": "friendly", "policy_number": "SLI-2298741",
                    "policy_id": "POL-001", "distress_flag": False}
        if st.button("🔍 Evaluate with Critique Agent"):
            result = evaluate(test_msg, test_ctx, "POL-001", "ManualTest", "mixed")
            record_critique(result)
            verdict_color = {"PASS": "✅", "REGENERATE": "🔁", "BLOCK": "⛔"}
            st.markdown(f"### {verdict_color.get(result.verdict.value, '?')} Verdict: **{result.verdict.value}**")
            st.metric("Overall Score", f"{result.overall_score:.0%}", delta=f"Threshold: 87%")
            check_data = []
            for c in result.checks:
                check_data.append({
                    "Check": c.check_name,
                    "Result": "✅ PASS" if c.passed else "❌ FAIL",
                    "Severity": c.severity,
                    "Feedback": c.feedback,
                })
            st.dataframe(pd.DataFrame(check_data), use_container_width=True, hide_index=True)
            if result.regenerate_feedback:
                st.warning(result.regenerate_feedback)
            if result.block_reason:
                st.error(f"BLOCK REASON: {result.block_reason}")

# ═════════════════════════════════════════════════════════════════════════════
# PAGE: Human Queue
# ═════════════════════════════════════════════════════════════════════════════
elif page == "🔔 Human Queue":
    st.title("🔔 Human Specialist Queue")
    st.markdown("Cases automatically routed from AI → Human. **SLA: ≤2 hours for distress/bereavement.**")

    stats = get_queue_stats()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Cases", stats["total"])
    col2.metric("🔴 Open", stats["open"])
    col3.metric("🚨 URGENT", stats["urgent"])
    col4.metric("✅ Resolved", stats["resolved"])

    queue = get_queue()
    if not queue:
        st.info("No open cases. Run journeys to generate escalations.")
    else:
        for b in queue:
            urgency_icon = "🚨" if b.priority == "URGENT" else "🔴" if b.priority == "HIGH" else "🟡"
            with st.expander(f"{urgency_icon} {b.case_id} | {b.customer_name} → {b.specialist_type} | SLA: {b.sla_hours}h"):
                st.markdown(f"**Priority:** {b.priority} | **Status:** {b.status}")
                st.markdown(f"**Escalation Reason:** {b.escalation_reason}")
                st.markdown(f"**Policy Summary:**\n```\n{b.policy_summary}\n```")
                st.markdown(f"**Recommended Approach:** {b.recommended_approach}")
                if b.objections_raised:
                    st.markdown(f"**Objections Raised:** {' | '.join(b.objections_raised[:3])}")
                if b.offers_already_shown:
                    st.markdown(f"**Offers Shown:** {' | '.join(b.offers_already_shown[:3])}")

    st.divider()
    st.subheader("👩‍💼 Specialist Routing Logic")
    routing_df = pd.DataFrame([
        {"Specialist":    "Senior Renewal RM (8)",
         "Routes When":   "HNI (₹1L+ premium), Platinum tier, bereavement, emotional cases",
         "Target Cases":  "8–10% of pipeline escalations"},
        {"Specialist":    "Revival Specialist (5)",
         "Routes When":   "Policy already lapsed — revival + re-underwriting required",
         "Target Cases":  "Post-lapse cases (90-day window)"},
        {"Specialist":    "Compliance Handler (2)",
         "Routes When":   "IRDAI complaint, mis-selling dispute, fraud claim, ombudsman",
         "Target Cases":  "<1% of pipeline"},
        {"Specialist":    "AI Ops Manager (3)",
         "Routes When":   "AI system anomaly, model drift detected, audit discrepancy",
         "Target Cases":  "Internal only"},
    ])
    st.dataframe(routing_df, use_container_width=True, hide_index=True)

# ═════════════════════════════════════════════════════════════════════════════
# PAGE: Financial Business Case
# ═════════════════════════════════════════════════════════════════════════════
elif page == "💰 Financial Business Case":
    st.title("💰 Financial Business Case — Section 5")
    st.markdown("**Board Resolution: ₹2.39 Cr CapEx | 16-Week Implementation | Q4 FY26 Production**")

    fin = get_financial_summary()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("3-Year NPV", "₹89 Cr")
    col2.metric("Payback Period", "8 Months")
    col3.metric("Annual Saving", "₹12.9 Cr")
    col4.metric("Revenue Uplift", "+₹38.9 Cr/yr")

    st.divider()
    st.subheader("💸 5.1 Cost Savings")
    cost_df = pd.DataFrame([
        {"Cost Category": "Staff Cost (salary + PF + gratuity + bonus)",
         "Current (₹ Cr)": 12.8, "Post-RenewAI (₹ Cr)": 2.8},
        {"Cost Category": "Recruitment & Training (38% attrition)",
         "Current (₹ Cr)": 2.1, "Post-RenewAI (₹ Cr)": 0.2},
        {"Cost Category": "Office Space & Infrastructure",
         "Current (₹ Cr)": 1.8, "Post-RenewAI (₹ Cr)": 0.3},
        {"Cost Category": "Telephony & Communication (IVR, dialers, SMS)",
         "Current (₹ Cr)": 1.2, "Post-RenewAI (₹ Cr)": 0.4},
        {"Cost Category": "Quality & Compliance Auditing (manual)",
         "Current (₹ Cr)": 0.7, "Post-RenewAI (₹ Cr)": 0.1},
        {"Cost Category": "AI Platform (LLM + cloud + APIs)",
         "Current (₹ Cr)": 0.0, "Post-RenewAI (₹ Cr)": 1.4},
        {"Cost Category": "AI Operations & Maintenance",
         "Current (₹ Cr)": 0.0, "Post-RenewAI (₹ Cr)": 0.5},
        {"Cost Category": "TOTAL ANNUAL OPEX",
         "Current (₹ Cr)": 18.6, "Post-RenewAI (₹ Cr)": 5.7},
    ])
    st.dataframe(cost_df, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("📈 5.2 Revenue Uplift (Persistency 71% → 88%)")
    rev_df = pd.DataFrame([
        {"Metric": "Renewal Policies Due Annually",   "Current": "14,40,000",    "Post-RenewAI": "14,40,000"},
        {"Metric": "Persistency Rate (13th Month)",   "Current": "71%",           "Post-RenewAI": "88%"},
        {"Metric": "Policies Renewed",                "Current": "10,22,400",    "Post-RenewAI": "12,67,200"},
        {"Metric": "Additional Policies Retained",    "Current": "—",             "Post-RenewAI": "+2,44,800"},
        {"Metric": "Average Annual Premium",          "Current": "₹22,400",      "Post-RenewAI": "₹22,400"},
        {"Metric": "Incremental Premium (gross)",     "Current": "—",             "Post-RenewAI": "₹54.8 Cr/yr"},
        {"Metric": "After commission & admin deduct", "Current": "—",             "Post-RenewAI": "₹38.9 Cr net"},
    ])
    st.dataframe(rev_df, use_container_width=True, hide_index=True)
    st.info("💡 Every 1% improvement in persistency = ₹4.7 Cr additional premium income retained")

    st.divider()
    st.subheader("🗓 16-Week Implementation Roadmap (Section 6)")
    roadmap_df = pd.DataFrame([
        {"Phase": "Phase 1 (Wks 1-4)",   "Name": "Foundation",
         "Activities": "CRM integration, pilot data, IRDAI pre-engagement, AI platform setup, staff comms"},
        {"Phase": "Phase 2 (Wks 5-8)",   "Name": "Development",
         "Activities": "Build 4 agents, objection library, WhatsApp Business API, voice platform (9 languages)"},
        {"Phase": "Phase 3 (Wks 9-13)",  "Name": "Pilot",
         "Activities": "5% live pilot in shadow mode. Measure open/conversion/escalation. IRDAI pilot notification."},
        {"Phase": "Phase 4 (Wks 14-16)", "Name": "Transition",
         "Activities": "Phased staff exit (40+40+20). 20 specialists trained. Full go-live. 30-day hypercare."},
    ])
    st.dataframe(roadmap_df, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("⚠️ Risk Management (Section 7)")
    risk_df = pd.DataFrame([
        {"Risk": "AI misclassifies grievance as routine",
         "Likelihood": "Medium",
         "Mitigation": "Distress keyword dict (Hindi + 6 languages); all grievance cases reviewed by human within 2h"},
        {"Risk": "AI generates inaccurate policy information",
         "Likelihood": "Medium",
         "Mitigation": "All facts from verified RAG docs only — never generative on financial figures"},
        {"Risk": "Customer backlash to AI-only contact",
         "Likelihood": "Medium",
         "Mitigation": "AI identifies itself as 'Suraksha AI-powered renewal assistant'. Opt-out for human-only."},
        {"Risk": "Data privacy violation (PII via AI)",
         "Likelihood": "Low",
         "Mitigation": "India-hosted cloud. PII masking before every AI call. DPDPA 2023 compliant. Annual audit."},
        {"Risk": "IRDAI mandates human in loop for renewal decisions",
         "Likelihood": "High (regulatory certainty)",
         "Mitigation": "AI facilitates payment only — customer takes the action. HITL at all decision boundaries."},
        {"Risk": "Model drift reduces conversion over time",
         "Likelihood": "Low–Medium",
         "Mitigation": "Weekly 5% sample quality eval; monthly objection refresh; quarterly model review; A/B testing"},
    ])
    st.dataframe(risk_df, use_container_width=True, hide_index=True)

# ═════════════════════════════════════════════════════════════════════════════
# PAGE: Audit Log
# ═════════════════════════════════════════════════════════════════════════════
elif page == "🔭 Audit Log":
    st.title("🔭 AI Observability & IRDAI Audit Log")
    sys_stats = get_system_stats()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Events", sys_stats["total_events"])
    col2.metric("IRDAI-Relevant", sys_stats["irdai_relevant"])
    col3.metric("Distress Events", sys_stats["distress_events"])
    col4.metric("Escalations", sys_stats["escalations"])

    st.markdown(
        "**Full trace of every agent action, decision, and escalation. "
        "IRDAI Technology Framework 2024 & RBI FREE-AI Framework 2025 compliant.**"
    )
    st.info("Run journeys from '🔄 Run Journeys (Demo)' to generate audit events.")

    from monitoring.observability import get_irdai_audit_log, get_escalation_log
    irdai_log = get_irdai_audit_log()
    if irdai_log:
        st.subheader("📋 IRDAI-Relevant Events")
        st.dataframe(pd.DataFrame(irdai_log), use_container_width=True, hide_index=True)

    escalations = get_escalation_log()
    if escalations:
        st.subheader("🔔 Escalation Events")
        esc_data = [{"Event ID": e.event_id, "Policy": e.policy_id,
                     "Agent": e.agent, "Outcome": e.outcome,
                     "Time": e.timestamp.strftime("%H:%M:%S")} for e in escalations]
        st.dataframe(pd.DataFrame(esc_data), use_container_width=True, hide_index=True)

    st.subheader("🔒 Compliance Certifications")
    comp_df = pd.DataFrame([
        {"Requirement": "IRDAI Technology Framework for Insurers",    "Year": 2024, "Status": "✅ Designed as first principle"},
        {"Requirement": "RBI FREE-AI Framework",                       "Year": 2025, "Status": "✅ Explainability + HITL built-in"},
        {"Requirement": "DPDPA (Data Protection)",                     "Year": 2023, "Status": "✅ PII masking + India data residency"},
        {"Requirement": "ISO 27001",                                   "Year": "—",  "Status": "✅ Azure Central India (certified)"},
        {"Requirement": "SOC 2 Type II",                              "Year": "—",  "Status": "✅ Azure Central India (certified)"},
        {"Requirement": "Data Residency — India",                      "Year": "—",  "Status": "✅ No data leaves India"},
        {"Requirement": "Human-in-the-Loop at decision boundaries",    "Year": "—",  "Status": "✅ AI facilitates — human decides"},
        {"Requirement": "Grievance Redressal Mechanism",               "Year": "—",  "Status": "✅ Compliance Handler + 15-day SLA"},
    ])
    st.dataframe(comp_df, use_container_width=True, hide_index=True)
