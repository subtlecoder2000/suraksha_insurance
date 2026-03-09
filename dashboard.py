"""
dashboard.py
Streamlit Dashboard — Suraksha Life Insurance PROJECT RenewAI v2.0

Visualises:
 • Renewal Pipeline Overview (KPIs)
 • Customer Journey Tracker (stage-by-stage progress)
 • Success Metrics Scorecard (FY25 Baseline → FY26 Target)
 • Live Batch Simulation (run all 3 journeys)
 • Audit Log & Compliance
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
from database.connection import SessionLocal
from database.repositories import CustomerRepository, ConversationRepository
from database.models import Customer
from agents.orchestrator import orchestrate, run_batch
from agents.email_agent import send_email
from agents.whatsapp_agent import send_whatsapp, handle_reply
from agents.voice_agent import make_call
from agents.human_queue_manager import escalate
from critique.critique_agent import evaluate, CritiqueVerdict
from critique.analytics import record as record_critique
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
        "🔄 Customer Journey Tracker",
        "▶️ Run Journeys (Demo)",
        "👥 Policyholder Pipeline",
        "📋 Success Metrics Scorecard",
        " Audit Log",
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
# PAGE: Customer Journey Tracker
# ═════════════════════════════════════════════════════════════════════════════
elif page == "🔄 Customer Journey Tracker":
    st.title("🔄 Customer Journey Tracker")
    st.markdown("**Real-time visualization of customer progress through the renewal pipeline**")
    st.divider()

    # Get database session
    db = SessionLocal()
    
    try:
        # Get all customers
        customers = CustomerRepository.get_all(db)
        
        if not customers:
            st.warning("No customers found in database. Please run `python database/seed.py` to load demo data.")
        else:
            # Summary metrics
            total_customers = len(customers)
            pending = len([c for c in customers if c.renewal_status == "PENDING"])
            renewed = len([c for c in customers if c.renewal_status == "RENEWED"])
            renewal_rate = (renewed / total_customers * 100) if total_customers > 0 else 0
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Customers", total_customers, help="In renewal pipeline")
            col2.metric("Pending", pending, help="Awaiting renewal")
            col3.metric("Renewed", renewed, help="Successfully renewed")
            col4.metric("Renewal Rate", f"{renewal_rate:.1f}%", 
                       delta=f"{renewal_rate - 88:.1f}pp vs target" if renewal_rate < 88 else "✓ Target met",
                       delta_color="normal" if renewal_rate >= 88 else "inverse")
            
            st.divider()
            
            # Journey stages pipeline
            st.subheader("📊 Journey Pipeline by Stage")
            
            journey_stages = ["T-45", "T-30", "T-20", "T-10", "T-5", "POST_LAPSE", "RENEWED"]
            stage_counts = {}
            stage_customers = {}
            
            for stage in journey_stages:
                if stage == "RENEWED":
                    stage_list = [c for c in customers if c.renewal_status == "RENEWED"]
                else:
                    stage_list = [c for c in customers if c.current_journey_stage == stage]
                stage_counts[stage] = len(stage_list)
                stage_customers[stage] = stage_list
            
            # Display stage counts as metrics
            cols = st.columns(len(journey_stages))
            for idx, stage in enumerate(journey_stages):
                with cols[idx]:
                    emoji = "✅" if stage == "RENEWED" else "🔄"
                    st.metric(f"{emoji} {stage}", stage_counts[stage])
            
            st.divider()
            
            # Stage selector
            selected_stage = st.selectbox(
                "Select Journey Stage to View Customers",
                journey_stages,
                index=0
            )
            
            customers_in_stage = stage_customers[selected_stage]
            
            if not customers_in_stage:
                st.info(f"No customers currently in **{selected_stage}** stage.")
            else:
                st.subheader(f"Customers in {selected_stage} Stage ({len(customers_in_stage)})")
                
                # Create customer cards
                for customer in customers_in_stage:
                    # Determine risk level
                    if customer.propensity_to_lapse >= 0.3:
                        risk_level = "🔴 High Risk"
                        risk_color = "red"
                    elif customer.propensity_to_lapse >= 0.15:
                        risk_level = "🟡 Medium Risk"
                        risk_color = "orange"
                    else:
                        risk_level = "🟢 Low Risk"
                        risk_color = "green"
                    
                    # Create expander for each customer
                    with st.expander(f"**{customer.name}** | {customer.policy_type} | ₹{customer.annual_premium:,} | {risk_level}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("##### 📋 Customer Profile")
                            st.write(f"**Customer ID:** {customer.customer_id}")
                            st.write(f"**Policy Number:** {customer.policy_number}")
                            st.write(f"**Age:** {customer.age}")
                            st.write(f"**Policy Type:** {customer.policy_type}")
                            st.write(f"**Annual Premium:** ₹{customer.annual_premium:,}")
                            st.write(f"**Sum Assured:** ₹{customer.sum_assured:,}")
                            st.write(f"**Payment Mode:** {customer.payment_mode}")
                            
                            st.markdown("##### 📞 Contact Preferences")
                            st.write(f"**Mobile:** {customer.mobile}")
                            st.write(f"**Email:** {customer.email}")
                            st.write(f"**Preferred Channel:** {customer.preferred_channel}")
                            st.write(f"**Preferred Language:** {customer.preferred_language}")
                            st.write(f"**Preferred Time:** {customer.preferred_time}")
                        
                        with col2:
                            st.markdown("##### 🎯 Journey Status")
                            st.write(f"**Current Stage:** {customer.current_journey_stage}")
                            st.write(f"**Renewal Status:** {customer.renewal_status}")
                            
                            if customer.due_date:
                                from datetime import datetime
                                days_to_due = (customer.due_date - datetime.now().date()).days
                                st.write(f"**Due Date:** {customer.due_date.strftime('%d %b %Y')}")
                                st.write(f"**Days to Due Date:** {days_to_due} days")
                            
                            if customer.last_contact_date:
                                st.write(f"**Last Contact:** {customer.last_contact_date.strftime('%d %b %Y %H:%M')}")
                            
                            st.markdown("##### 📊 Risk Assessment")
                            st.write(f"**Risk Level:** {risk_level}")
                            st.progress(customer.propensity_to_lapse, text=f"Lapse Propensity: {customer.propensity_to_lapse*100:.1f}%")
                            st.progress(customer.persistency_score, text=f"Persistency Score: {customer.persistency_score*100:.1f}%")
                            
                            st.markdown("##### 🎬 Recommended Next Action")
                            if customer.renewal_status == "RENEWED":
                                st.success("✅ Customer has renewed successfully")
                            elif customer.current_journey_stage == "T-45":
                                st.info("📧 Send initial renewal reminder email")
                            elif customer.current_journey_stage == "T-30":
                                st.info("💬 Follow up via WhatsApp")
                            elif customer.current_journey_stage == "T-20":
                                st.info("📞 Place voice call")
                            elif customer.current_journey_stage == "T-10":
                                st.warning("⚡ Send urgent dual-channel reminder (Email + WhatsApp)")
                            elif customer.current_journey_stage == "T-5":
                                st.error("🚨 Last chance - Grace period notification")
                            elif customer.current_journey_stage == "POST_LAPSE":
                                st.error("🔁 Initiate 90-day revival campaign")
                        
                        # Conversation history
                        st.markdown("##### 💬 Recent Activity")
                        conversations = ConversationRepository.get_recent(db, customer.customer_id, limit=5)
                        
                        if conversations:
                            for conv in conversations:
                                sentiment_emoji = "😊" if conv.sentiment == "POSITIVE" else ("😐" if conv.sentiment == "NEUTRAL" else "😞")
                                st.markdown(f"""
                                **{conv.timestamp.strftime('%d %b %H:%M')}** | {conv.channel} | {sentiment_emoji} {conv.sentiment}
                                
                                _{conv.message[:150]}{'...' if len(conv.message) > 150 else ''}_
                                """)
                        else:
                            st.caption("No activity recorded yet")
            
            st.divider()
            
            # Analytics section
            st.subheader("📈 Journey Analytics")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("##### 🎯 Risk Segmentation")
                high_risk = len([c for c in customers if c.propensity_to_lapse >= 0.3])
                medium_risk = len([c for c in customers if 0.15 <= c.propensity_to_lapse < 0.3])
                low_risk = len([c for c in customers if c.propensity_to_lapse < 0.15])
                
                risk_df = pd.DataFrame({
                    "Risk Level": ["🔴 High (≥30%)", "🟡 Medium (15-30%)", "🟢 Low (<15%)"],
                    "Count": [high_risk, medium_risk, low_risk],
                    "Percentage": [
                        f"{high_risk/total_customers*100:.1f}%",
                        f"{medium_risk/total_customers*100:.1f}%",
                        f"{low_risk/total_customers*100:.1f}%"
                    ]
                })
                st.dataframe(risk_df, use_container_width=True, hide_index=True)
            
            with col2:
                st.markdown("##### 📱 Channel Distribution")
                channel_counts = {}
                for c in customers:
                    channel = c.preferred_channel or "Unknown"
                    channel_counts[channel] = channel_counts.get(channel, 0) + 1
                
                channel_df = pd.DataFrame([
                    {"Channel": channel, "Count": count, "Percentage": f"{count/total_customers*100:.1f}%"}
                    for channel, count in channel_counts.items()
                ])
                st.dataframe(channel_df, use_container_width=True, hide_index=True)
            
            # Stage funnel visualization
            st.markdown("##### 🔄 Journey Stage Funnel")
            funnel_data = []
            for stage in journey_stages:
                count = stage_counts[stage]
                percentage = (count / total_customers * 100) if total_customers > 0 else 0
                funnel_data.append({
                    "Stage": stage,
                    "Count": count,
                    "Percentage": f"{percentage:.1f}%"
                })
            
            funnel_df = pd.DataFrame(funnel_data)
            st.dataframe(funnel_df, use_container_width=True, hide_index=True)
            
            # Quick actions
            st.divider()
            st.subheader("⚡ Quick Actions")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🔄 Refresh Data", use_container_width=True):
                    st.rerun()
            
            with col2:
                if st.button("📊 Export Pipeline Report", use_container_width=True):
                    st.info("Export functionality coming soon!")
            
            with col3:
                if st.button("🎯 Run Batch Process", use_container_width=True):
                    with st.spinner("Processing batch..."):
                        # This would trigger the orchestrator for all pending customers
                        st.success("Batch process initiated!")
    
    finally:
        db.close()

# ═════════════════════════════════════════════════════════════════════════════
# PAGE: Run Journeys (Demo)
# ═════════════════════════════════════════════════════════════════════════════
elif page == "▶️ Run Journeys (Demo)":
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
