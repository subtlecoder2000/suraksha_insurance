"""
api/main.py
FastAPI Backend — Suraksha Life Insurance PROJECT RenewAI v2.0
UPGRADED: WebSocket streaming, LangGraph, Prompt Management, Model Tracing

New features:
  - /ws — WebSocket endpoint for streaming agent execution
  - /api/v2/journey/run — LangGraph-based Plan-Execute-Critique-Respond
  - /api/prompts/* — Prompt management dashboard API
  - /api/traces/* — Model tracing (LangSmith-style)
  - /api/feedback — Customer feedback collection
"""
import sys
import os
import json
import asyncio
from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
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
from agents.langgraph_orchestrator import run_renewal_journey
from agents.email_agent import send_email
from agents.whatsapp_agent import send_whatsapp, handle_reply
from agents.voice_agent import make_call
from agents.human_queue_manager import get_queue, resolve_case, get_queue_stats, escalate
from agents.prompt_generator_agent import (
    collect_feedback, run_weekly_improvement, get_improvement_dashboard,
    generate_improved_prompt, get_pending_feedback,
)
from critique.critique_agent import evaluate, CritiqueVerdict
from critique.analytics import record as record_critique, get_summary as critique_summary
from monitoring.observability import get_irdai_audit_log, get_all_audit_logs, log_event, EventType, get_system_stats
from monitoring.scorecard import get_scorecard, get_financial_summary, update_metric
from monitoring.tracer import (
    get_trace, get_all_traces, get_traces_by_policy,
    get_span_detail, get_trace_stats,
    add_ws_subscriber, remove_ws_subscriber,
)
from services.prompt_manager import (
    get_all_prompts, get_active_prompt, get_prompt_versions,
    update_prompt, rollback_prompt, incorporate_feedback,
)

app = FastAPI(title="Suraksha Life Insurance — PROJECT RenewAI API v2.0")

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# ── Data Models ───────────────────────────────────────────────────────────────

class JourneyRequest(BaseModel):
    policy_id: str

class ReplyRequest(BaseModel):
    policy_id: str
    message: str

class PromptUpdateRequest(BaseModel):
    agent_name: str
    system_prompt: str
    description: str = ""

class PromptRollbackRequest(BaseModel):
    agent_name: str
    target_version: int

class FeedbackRequest(BaseModel):
    policy_id: str
    agent_name: str
    feedback_type: str
    feedback_text: str
    rating: int = 0

class WeeklyImprovementRequest(BaseModel):
    agent_name: Optional[str] = None

# ── Root ──────────────────────────────────────────────────────────────────────

@app.get("/")
async def read_root():
    index_path = os.path.join(static_dir, "index.html") if os.path.exists(static_dir) else None
    if index_path and os.path.exists(index_path):
        with open(index_path, "r") as f:
            return HTMLResponse(content=f.read())
    return {"message": "RenewAI v2.0 API", "docs": "/docs"}


# ══════════════════════════════════════════════════════════════════════════════
# WEBSOCKET — Streaming agent execution
# ══════════════════════════════════════════════════════════════════════════════

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        add_ws_subscriber(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        remove_ws_subscriber(websocket)

    async def broadcast(self, message: dict):
        dead = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                dead.append(connection)
        for conn in dead:
            self.disconnect(conn)

manager = ConnectionManager()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for streaming agent execution.
    Clients receive real-time updates about what each agent is performing.
    """
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                request = json.loads(data)
                action = request.get("action")

                if action == "run_journey":
                    policy_id = request.get("policy_id")
                    if not policy_id:
                        await websocket.send_json({"error": "policy_id required"})
                        continue

                    # Send start event
                    await websocket.send_json({
                        "type": "journey_start",
                        "policy_id": policy_id,
                        "timestamp": datetime.now().isoformat(),
                        "message": f"Starting renewal journey for {policy_id}..."
                    })

                    # Run the LangGraph journey
                    result = run_renewal_journey(policy_id)

                    # Stream each event
                    for event in result.get("stream_events", []):
                        await websocket.send_json({
                            "type": "agent_event",
                            **event
                        })
                        await asyncio.sleep(0.1)  # Small delay for visual effect

                    # Send completion
                    await websocket.send_json({
                        "type": "journey_complete",
                        "policy_id": policy_id,
                        "result": {
                            "trace_id": result.get("trace_id"),
                            "channel_used": result.get("channel_used"),
                            "critique": result.get("critique", {}),
                            "message_preview": result.get("message", "")[:200],
                            "plan": result.get("plan", {}),
                        },
                        "timestamp": datetime.now().isoformat(),
                    })

                elif action == "subscribe_traces":
                    await websocket.send_json({
                        "type": "subscribed",
                        "message": "Now receiving live trace updates"
                    })

                elif action == "ping":
                    await websocket.send_json({"type": "pong"})

                else:
                    await websocket.send_json({"error": f"Unknown action: {action}"})

            except json.JSONDecodeError:
                await websocket.send_json({"error": "Invalid JSON"})

    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ══════════════════════════════════════════════════════════════════════════════
# v2 API — LangGraph Journey
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/api/v2/journey/run")
async def run_journey_v2(req: JourneyRequest):
    """
    Run renewal journey using LangGraph Plan-Execute-Critique-Respond.
    Returns full trace with agent-to-agent communication.
    """
    ph = get_policyholder(req.policy_id)
    if not ph:
        raise HTTPException(status_code=404, detail="Policyholder not found")

    result = run_renewal_journey(req.policy_id)

    # Broadcast to WebSocket clients
    await manager.broadcast({
        "type": "journey_complete",
        "policy_id": req.policy_id,
        "trace_id": result.get("trace_id"),
        "channel_used": result.get("channel_used"),
    })

    return result


# ══════════════════════════════════════════════════════════════════════════════
# PROMPT MANAGEMENT API
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/api/prompts")
async def list_all_prompts():
    """Get all agent prompts — viewable on dashboard."""
    return get_all_prompts()


@app.get("/api/prompts/{agent_name}")
async def get_prompt(agent_name: str):
    """Get active prompt for a specific agent."""
    prompt = get_active_prompt(agent_name)
    if not prompt:
        raise HTTPException(status_code=404, detail=f"No prompt found for {agent_name}")
    return {
        "agent_name": agent_name,
        "system_prompt": prompt,
        "versions": get_prompt_versions(agent_name),
    }


@app.put("/api/prompts")
async def update_agent_prompt(req: PromptUpdateRequest):
    """Update/create a new version of an agent's system prompt."""
    version = update_prompt(req.agent_name, req.system_prompt, req.description, "dashboard_user")
    return {
        "agent_name": req.agent_name,
        "new_version": version.version,
        "description": version.description,
    }


@app.post("/api/prompts/rollback")
async def rollback_agent_prompt(req: PromptRollbackRequest):
    """Rollback to a previous prompt version."""
    version = rollback_prompt(req.agent_name, req.target_version)
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    return {
        "agent_name": req.agent_name,
        "rolled_back_to": version.version,
    }


# ══════════════════════════════════════════════════════════════════════════════
# MODEL TRACING API (LangSmith-style)
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/api/traces")
async def list_traces(limit: int = 50):
    """Get all traces — main dashboard view."""
    return {
        "traces": get_all_traces(limit),
        "stats": get_trace_stats(),
    }


@app.get("/api/traces/{trace_id}")
async def get_trace_detail(trace_id: str):
    """Get full trace detail with all spans."""
    trace = get_trace(trace_id)
    if not trace:
        raise HTTPException(status_code=404, detail="Trace not found")
    return trace


@app.get("/api/traces/{trace_id}/spans/{span_id}")
async def get_span(trace_id: str, span_id: str):
    """Get span detail — click on agent in dashboard to see execution."""
    span = get_span_detail(trace_id, span_id)
    if not span:
        raise HTTPException(status_code=404, detail="Span not found")
    return span


@app.get("/api/traces/policy/{policy_id}")
async def get_policy_traces(policy_id: str):
    """Get all traces for a specific policy."""
    return get_traces_by_policy(policy_id)


@app.get("/api/trace-stats")
async def trace_statistics():
    """Get aggregate tracing statistics."""
    return get_trace_stats()


# ══════════════════════════════════════════════════════════════════════════════
# FEEDBACK & PROMPT IMPROVEMENT API
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/api/feedback")
async def submit_feedback(req: FeedbackRequest):
    """Submit customer/system feedback for prompt improvement."""
    collect_feedback(req.policy_id, req.agent_name, req.feedback_type,
                     req.feedback_text, req.rating)
    return {"status": "recorded", "message": "Feedback will be incorporated in next improvement cycle"}


@app.get("/api/feedback/pending")
async def list_pending_feedback(agent_name: str = None):
    """Get pending feedback items."""
    return get_pending_feedback(agent_name)


@app.post("/api/prompts/improve")
async def trigger_improvement(req: WeeklyImprovementRequest):
    """
    Trigger the Prompt Generator Agent to create improved prompts.
    Can target a specific agent or run for all agents.
    """
    if req.agent_name:
        improvement = generate_improved_prompt(req.agent_name)
        if not improvement:
            raise HTTPException(status_code=404, detail="Agent not found")
        return {
            "improvements": [{
                "agent_name": improvement.agent_name,
                "new_version": improvement.new_version,
                "changes_summary": improvement.changes_summary,
                "improvement_areas": improvement.improvement_areas,
            }]
        }
    else:
        improvements = run_weekly_improvement()
        return {
            "improvements": [{
                "agent_name": imp.agent_name,
                "new_version": imp.new_version,
                "changes_summary": imp.changes_summary,
            } for imp in improvements]
        }


@app.get("/api/prompts/dashboard")
async def prompt_improvement_dashboard():
    """Dashboard data for prompt management and improvement."""
    return get_improvement_dashboard()


# ══════════════════════════════════════════════════════════════════════════════
# LEGACY API (v1) — Kept for backward compatibility
# ══════════════════════════════════════════════════════════════════════════════

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
    """Legacy v1 endpoint — now wraps LangGraph v2."""
    return run_renewal_journey(req.policy_id)

@app.post("/api/journey/reply")
async def handle_customer_reply(req: ReplyRequest):
    ph = get_policyholder(req.policy_id)
    if not ph:
        raise HTTPException(status_code=404, detail="Policyholder not found")

    decision = orchestrate(ph)
    reply = handle_reply(ph.policy_id, ph.phone, req.message, decision.context)

    if reply.escalate:
        briefing = escalate(ph.policy_id, f"Distress detected in reply: {req.message}")
        log_event(EventType.DISTRESS_FLAG, ph.policy_id, "WhatsAppAgent",
                  "message_reply", "whatsapp", "escalated", irdai_relevant=True)
        return {"reply": reply.body, "escalated": True, "case_id": briefing.case_id}

    return {"reply": reply.body, "escalated": False}

@app.get("/api/human_queue")
async def get_human_queue():
    return {"items": get_queue(), "stats": get_queue_stats()}

@app.get("/api/critique/summary")
async def get_critique_summary():
    return critique_summary()

@app.get("/api/observability/audit_log")
async def get_audit_log():
    return {"irdai": get_all_audit_logs(), "stats": get_system_stats()}

@app.post("/api/batch/run")
async def run_batch_endpoint():
    decisions = run_batch(45)
    if decisions:
        escalated = len([d for d in decisions if d.recommended_agent == "HumanQueueManager"])
        update_metric("escalation_rate", escalated / len(decisions))
    return {"processed": len(decisions)}


# ── Customer Journey Tracking (kept from v1) ─────────────────────────────────

@app.get("/api/journey/tracker")
async def get_journey_tracker(db: Session = Depends(get_db)):
    customers = CustomerRepository.get_all(db)
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
                for c in stage_customers[:10]
            ]
        }

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
    customer = CustomerRepository.get_by_id(db, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    conversations = ConversationRepository.get_by_customer(db, customer_id)
    from database.models import EscalationCase
    escalations = db.query(EscalationCase).filter(EscalationCase.customer_id == customer_id).all()

    journey_order = ["T-45", "T-30", "T-20", "T-10", "T-5", "POST_LAPSE", "RENEWED"]
    current_stage_index = journey_order.index(customer.current_journey_stage) if customer.current_journey_stage in journey_order else 0
    progress_percentage = (current_stage_index / (len(journey_order) - 1)) * 100

    timeline = []
    for conv in conversations:
        timeline.append({
            "timestamp": conv.timestamp.isoformat(),
            "type": "conversation", "channel": conv.channel,
            "message": conv.message[:100] + "..." if len(conv.message) > 100 else conv.message,
            "sentiment": conv.sentiment, "outcome": conv.outcome,
            "journey_stage": conv.journey_stage
        })

    return {
        "customer": {
            "customer_id": customer.customer_id, "name": customer.name,
            "policy_number": customer.policy_number, "policy_type": customer.policy_type,
            "annual_premium": customer.annual_premium, "sum_assured": customer.sum_assured,
            "due_date": customer.due_date.isoformat() if customer.due_date else None,
            "renewal_status": customer.renewal_status,
            "preferred_channel": customer.preferred_channel,
            "preferred_language": customer.preferred_language,
            "mobile": customer.mobile, "email": customer.email
        },
        "journey": {
            "current_stage": customer.current_journey_stage,
            "progress_percentage": progress_percentage,
            "last_contact_date": customer.last_contact_date.isoformat() if customer.last_contact_date else None,
        },
        "risk_assessment": {
            "propensity_to_lapse": customer.propensity_to_lapse,
            "persistency_score": customer.persistency_score,
            "risk_level": "High" if customer.propensity_to_lapse >= 0.3 else ("Medium" if customer.propensity_to_lapse >= 0.15 else "Low")
        },
        "timeline": sorted(timeline, key=lambda x: x["timestamp"], reverse=True),
        "conversation_count": len(conversations),
        "escalation_count": len(escalations),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
