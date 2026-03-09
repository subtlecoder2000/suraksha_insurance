"""
api/main.py
FastAPI Backend — Suraksha Life Insurance PROJECT RenewAI v2.0
"""
import sys, os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from typing import List, Optional
from pydantic import BaseModel
from datetime import date, datetime
from sqlalchemy.orm import Session

# Add root directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.crm import (get_all_policyholders, get_pipeline_summary, 
                      get_policyholder, update_payment_status)
from database.connection import get_db
from database.repositories import CustomerRepository, ConversationRepository, EscalationRepository
from agents.orchestrator import orchestrate, run_batch
from agents.email_agent import send_email
from agents.whatsapp_agent import send_whatsapp, handle_reply
from agents.voice_agent import make_call
from agents.human_queue_manager import get_queue, resolve_case, get_queue_stats, escalate
from critique.critique_agent import evaluate, CritiqueVerdict
from critique.analytics import record as record_critique, get_summary as critique_summary
from monitoring.observability import get_irdai_audit_log, log_event, EventType, get_system_stats
from monitoring.scorecard import get_scorecard, get_financial_summary, update_metric

app = FastAPI(title="Suraksha Life Insurance — PROJECT RenewAI API")

# Mount static files (will hold our frontend)
app.mount("/static", StaticFiles(directory="static"), name="static")

# ── Data Models ───────────────────────────────────────────────────────────────

class JourneyRequest(BaseModel):
    policy_id: str

class ReplyRequest(BaseModel):
    policy_id: str
    message: str

# ── API Endpoints ─────────────────────────────────────────────────────────────

@app.get("/")
async def read_root():
    with open("static/index.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    pipeline = get_pipeline_summary()
    fin = get_financial_summary()
    return {
        "pipeline": pipeline,
        "financial": fin,
        "scorecard": get_scorecard()
    }

@app.get("/api/pipeline")
async def get_pipeline():
    phs = get_all_policyholders()
    data = []
    for ph in phs:
        data.append({
            "policy_id": ph.policy_id,
            "policy_number": ph.policy_number,
            "name": ph.name,
            "policy_type": ph.policy_type,
            "premium": ph.annual_premium,
            "renewal_due_date": ph.renewal_due_date,
            "lapse_risk": ph.lapse_risk,
            "last_payment_status": ph.last_payment_status,
            "distress": ph.distress_flag or ph.bereavement
        })
    return data

@app.post("/api/journey/run")
async def run_journey_endpoint(req: JourneyRequest):
    ph = get_policyholder(req.policy_id)
    if not ph:
        raise HTTPException(status_code=404, detail="Policyholder not found")
    
    decision = orchestrate(ph)

    # Human-first routing for complex journeys.
    if decision.recommended_agent == "HumanQueueManager":
        briefing = escalate(
            ph.policy_id,
            f"Auto-escalated by orchestrator: {'; '.join(decision.complexity_reasons) or 'high complexity case'}"
        )
        log_event(
            EventType.ESCALATION, ph.policy_id, "HumanQueueManager",
            "auto_handoff", "human", f"Case: {briefing.case_id}", irdai_relevant=True
        )
        return {
            "decision": decision,
            "routed_to_human": True,
            "case_id": briefing.case_id,
            "specialist": briefing.specialist_type,
            "priority": briefing.priority,
        }

    payload = {"decision": decision, "routed_to_human": False}
    critique = None

    if decision.recommended_agent == "EmailAgent":
        mail = send_email(
            ph.policy_id,
            ph.email,
            decision.context,
            tone=decision.tone,
            nudge_number=1,
            offer_ids=[o.offer_id for o in decision.offer_package.offers],
        )
        critique = evaluate(mail.body, decision.context, ph.policy_id, "EmailAgent", "email")
        record_critique(critique)
        log_event(EventType.AGENT_ACTION, ph.policy_id, "EmailAgent",
                  "sent_renewal_email", "email", "delivered")
        payload.update({"message": mail.body, "subject": mail.subject, "channel_used": "email"})
    elif decision.recommended_agent == "VoiceAgent":
        call = make_call(ph.policy_id, decision.context, journey_step=decision.journey_step)
        voice_excerpt = next(
            (t.get("text", "") for t in call.call_session.transcript if t.get("role") == "assistant"),
            f"Voice call outcome: {call.outcome}",
        )
        critique = evaluate(voice_excerpt, decision.context, ph.policy_id, "VoiceAgent", "voice")
        record_critique(critique)
        log_event(EventType.AGENT_ACTION, ph.policy_id, "VoiceAgent",
                  "placed_outbound_call", "voice", call.outcome)
        payload.update({
            "message": voice_excerpt,
            "voice_outcome": call.outcome,
            "channel_used": "voice",
            "escalated": call.escalated,
        })
    else:
        wa_msg = send_whatsapp(ph.policy_id, ph.phone, decision.context, tone=decision.tone)
        critique = evaluate(wa_msg.body, decision.context, ph.policy_id, "WhatsAppAgent", "whatsapp")
        record_critique(critique)
        log_event(EventType.AGENT_ACTION, ph.policy_id, "WhatsAppAgent",
                  "sent_renewal_message", "whatsapp", "delivered")
        payload.update({"message": wa_msg.body, "channel_used": "whatsapp"})

        # Keep demo simulation hook for Journey A.
        if req.policy_id == "POL-001":
            payload["simulated_reply"] = "Can I pay in two instalments?"

    payload["critique"] = critique
    return payload

@app.post("/api/journey/reply")
async def handle_customer_reply(req: ReplyRequest):
    ph = get_policyholder(req.policy_id)
    if not ph:
        raise HTTPException(status_code=404, detail="Policyholder not found")
    
    decision = orchestrate(ph) # need current context
    reply = handle_reply(ph.policy_id, ph.phone, req.message, decision.context)
    
    # Check if a distress was flagged and escalated
    if reply.escalate:
        briefing = escalate(ph.policy_id, f"Distress detected in reply: {req.message}")
        log_event(EventType.DISTRESS_FLAG, ph.policy_id, "WhatsAppAgent", 
                  "message_reply", "whatsapp", "escalated", irdai_relevant=True)
        return {"reply": reply.body, "escalated": True, "case_id": briefing.case_id}
        
    return {"reply": reply.body, "escalated": False}

@app.get("/api/human_queue")
async def get_human_queue():
    queue = get_queue()
    return {
        "items": queue,
        "stats": get_queue_stats()
    }

@app.get("/api/critique/summary")
async def get_critique_summary():
    return critique_summary()

@app.get("/api/observability/audit_log")
async def get_audit_log():
    return {
        "irdai": get_irdai_audit_log(),
        "stats": get_system_stats()
    }

@app.post("/api/batch/run")
async def run_batch_endpoint():
    decisions = run_batch(45)
    if decisions:
        escalated = len([d for d in decisions if d.recommended_agent == "HumanQueueManager"])
        update_metric("escalation_rate", escalated / len(decisions))
    return {"processed": len(decisions)}


# ── Customer Journey Tracking Endpoints ──────────────────────────────────────

@app.get("/api/journey/tracker")
async def get_journey_tracker(db: Session = Depends(get_db)):
    """
    Get comprehensive journey tracking data for all customers
    Returns: Pipeline view with stage distribution, progress metrics, and individual customer journeys
    """
    customers = CustomerRepository.get_all(db)
    
    # Stage distribution
    stage_distribution = {}
    journey_stages = ["T-45", "T-30", "T-20", "T-10", "T-5", "POST_LAPSE", "RENEWED"]
    
    for stage in journey_stages:
        stage_customers = [c for c in customers if c.current_journey_stage == stage or (stage == "RENEWED" and c.renewal_status == "RENEWED")]
        stage_distribution[stage] = {
            "count": len(stage_customers),
            "customers": [
                {
                    "customer_id": c.customer_id,
                    "name": c.name,
                    "policy_type": c.policy_type,
                    "premium": c.annual_premium,
                    "lapse_risk": "High" if c.propensity_to_lapse >= 0.3 else ("Medium" if c.propensity_to_lapse >= 0.15 else "Low"),
                    "preferred_channel": c.preferred_channel,
                    "last_contact": c.last_contact_date.isoformat() if c.last_contact_date else None,
                    "due_date": c.due_date.isoformat() if c.due_date else None
                }
                for c in stage_customers[:10]  # Limit to 10 per stage for performance
            ]
        }
    
    # Overall metrics
    total_customers = len(customers)
    pending_customers = len([c for c in customers if c.renewal_status == "PENDING"])
    renewed_customers = len([c for c in customers if c.renewal_status == "RENEWED"])
    
    return {
        "summary": {
            "total_customers": total_customers,
            "pending": pending_customers,
            "renewed": renewed_customers,
            "renewal_rate": (renewed_customers / total_customers * 100) if total_customers > 0 else 0
        },
        "stage_distribution": stage_distribution,
        "journey_stages": journey_stages
    }


@app.get("/api/journey/customer/{customer_id}")
async def get_customer_journey(customer_id: str, db: Session = Depends(get_db)):
    """
    Get detailed journey tracking for a specific customer
    Returns: Full journey history, conversations, escalations, and next actions
    """
    customer = CustomerRepository.get_by_id(db, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Get conversation history
    conversations = ConversationRepository.get_by_customer(db, customer_id)
    
    # Get escalations
    from database.models import EscalationCase
    escalations = db.query(EscalationCase).filter(EscalationCase.customer_id == customer_id).all()
    
    # Calculate journey progress
    journey_order = ["T-45", "T-30", "T-20", "T-10", "T-5", "POST_LAPSE", "RENEWED"]
    current_stage_index = journey_order.index(customer.current_journey_stage) if customer.current_journey_stage in journey_order else 0
    progress_percentage = (current_stage_index / (len(journey_order) - 1)) * 100
    
    # Build timeline
    timeline = []
    for conv in conversations:
        timeline.append({
            "timestamp": conv.timestamp.isoformat(),
            "type": "conversation",
            "channel": conv.channel,
            "message": conv.message[:100] + "..." if len(conv.message) > 100 else conv.message,
            "sentiment": conv.sentiment,
            "outcome": conv.outcome,
            "journey_stage": conv.journey_stage
        })
    
    return {
        "customer": {
            "customer_id": customer.customer_id,
            "name": customer.name,
            "policy_number": customer.policy_number,
            "policy_type": customer.policy_type,
            "annual_premium": customer.annual_premium,
            "sum_assured": customer.sum_assured,
            "due_date": customer.due_date.isoformat() if customer.due_date else None,
            "grace_period_end": customer.grace_period_end.isoformat() if customer.grace_period_end else None,
            "renewal_status": customer.renewal_status,
            "preferred_channel": customer.preferred_channel,
            "preferred_language": customer.preferred_language,
            "mobile": customer.mobile,
            "email": customer.email
        },
        "journey": {
            "current_stage": customer.current_journey_stage,
            "progress_percentage": progress_percentage,
            "last_contact_date": customer.last_contact_date.isoformat() if customer.last_contact_date else None,
            "days_to_due_date": (customer.due_date - datetime.now().date()).days if customer.due_date else None,
        },
        "risk_assessment": {
            "propensity_to_lapse": customer.propensity_to_lapse,
            "persistency_score": customer.persistency_score,
            "risk_level": "High" if customer.propensity_to_lapse >= 0.3 else ("Medium" if customer.propensity_to_lapse >= 0.15 else "Low")
        },
        "timeline": sorted(timeline, key=lambda x: x["timestamp"], reverse=True),
        "conversation_count": len(conversations),
        "escalation_count": len(escalations),
        "next_action": _determine_next_action(customer)
    }


def _determine_next_action(customer):
    """Determine the recommended next action for a customer"""
    if customer.renewal_status == "RENEWED":
        return {"action": "none", "message": "Customer has renewed successfully"}
    
    if customer.current_journey_stage == "T-45":
        return {"action": "send_email", "message": "Send initial renewal reminder email", "channel": "email"}
    elif customer.current_journey_stage == "T-30":
        return {"action": "send_whatsapp", "message": "Follow up via WhatsApp", "channel": "whatsapp"}
    elif customer.current_journey_stage == "T-20":
        return {"action": "make_call", "message": "Place voice call", "channel": "voice"}
    elif customer.current_journey_stage == "T-10":
        return {"action": "dual_channel", "message": "Send urgent dual-channel reminder", "channel": "email+whatsapp"}
    elif customer.current_journey_stage == "T-5":
        return {"action": "urgent_dual", "message": "Last chance - Grace period notification", "channel": "email+whatsapp"}
    elif customer.current_journey_stage == "POST_LAPSE":
        return {"action": "revival_campaign", "message": "Initiate 90-day revival campaign", "channel": "all"}
    else:
        return {"action": "evaluate", "message": "Evaluate customer status and route", "channel": "system"}


@app.get("/api/journey/analytics")
async def get_journey_analytics(db: Session = Depends(get_db)):
    """
    Get journey analytics and conversion metrics
    """
    customers = CustomerRepository.get_all(db)
    
    # Calculate stage-wise conversion rates
    journey_funnel = {
        "T-45": len([c for c in customers if c.current_journey_stage == "T-45"]),
        "T-30": len([c for c in customers if c.current_journey_stage == "T-30"]),
        "T-20": len([c for c in customers if c.current_journey_stage == "T-20"]),
        "T-10": len([c for c in customers if c.current_journey_stage == "T-10"]),
        "T-5": len([c for c in customers if c.current_journey_stage == "T-5"]),
        "POST_LAPSE": len([c for c in customers if c.current_journey_stage == "POST_LAPSE"]),
        "RENEWED": len([c for c in customers if c.renewal_status == "RENEWED"])
    }
    
    # Channel preference distribution
    channel_distribution = {}
    for c in customers:
        channel = c.preferred_channel or "Unknown"
        channel_distribution[channel] = channel_distribution.get(channel, 0) + 1
    
    # Risk segmentation
    high_risk = len([c for c in customers if c.propensity_to_lapse >= 0.3])
    medium_risk = len([c for c in customers if 0.15 <= c.propensity_to_lapse < 0.3])
    low_risk = len([c for c in customers if c.propensity_to_lapse < 0.15])
    
    return {
        "funnel": journey_funnel,
        "channel_distribution": channel_distribution,
        "risk_segmentation": {
            "high": high_risk,
            "medium": medium_risk,
            "low": low_risk
        },
        "total_customers": len(customers)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
