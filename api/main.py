"""
api/main.py
FastAPI Backend — Suraksha Life Insurance PROJECT RenewAI v2.0
"""
import sys, os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from typing import List, Optional
from pydantic import BaseModel
from datetime import date, datetime

# Add root directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.crm import (get_all_policyholders, get_pipeline_summary, 
                      get_policyholder, update_payment_status)
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
