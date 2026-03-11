"""
agents/langgraph_orchestrator.py
Plan-and-Execute Agent Framework using LangGraph

Replaces the procedural orchestrator with a LangGraph-based
stateful graph that implements Plan → Execute → Critique → Respond.

Features:
  - Plan-and-Execute action framework
  - Per-agent critique (one critique agent per channel agent)
  - Model tracing with trace IDs for every step
  - Streaming responses about what each agent is performing
  - Evidence stored as simple text/JSON
"""
from __future__ import annotations
import json
import uuid
from datetime import date, datetime
from typing import TypedDict, Annotated, Optional
from dataclasses import asdict

from langgraph.graph import StateGraph, END

from agents.orchestrator import (
    orchestrate as legacy_orchestrate,
    OrchestratorDecision,
    _get_journey_step,
)
from agents.email_agent import send_email
from agents.whatsapp_agent import send_whatsapp, handle_reply
from agents.voice_agent import make_call
from agents.human_queue_manager import escalate, get_queue_stats
from critique.critique_agent import evaluate, CritiqueVerdict
from critique.analytics import record as record_critique
from monitoring.tracer import (
    start_trace, end_trace, start_span, end_span,
    SpanStatus,
)
from monitoring.observability import log_event, EventType
from services.prompt_manager import get_active_prompt
from data.crm import get_policyholder


# ── State Definition ──────────────────────────────────────────────────────────

class RenewalState(TypedDict):
    """State passed between nodes in the LangGraph."""
    policy_id: str
    trace_id: str
    # Plan
    plan: dict
    decision: Optional[dict]
    # Execute
    agent_output: dict
    channel_used: str
    message: str
    # Critique
    critique_result: dict
    critique_verdict: str
    regeneration_count: int
    # Response
    final_response: dict
    # Streaming
    stream_events: list[dict]
    error: Optional[str]


# ── Graph Nodes ───────────────────────────────────────────────────────────────

def plan_node(state: RenewalState) -> RenewalState:
    """
    PLAN: Orchestrator analyzes the policyholder context and creates an
    execution plan (channel, tone, timing, offers).
    """
    policy_id = state["policy_id"]
    trace_id = state["trace_id"]

    span = start_span(trace_id, "OrchestratorAgent", "plan",
                      input_data={"policy_id": policy_id})

    ph = get_policyholder(policy_id)
    if not ph:
        end_span(trace_id, span.span_id,
                 output_data={"error": "Policyholder not found"},
                 status=SpanStatus.FAILED, error="Policyholder not found")
        state["error"] = "Policyholder not found"
        state["stream_events"].append({
            "agent": "OrchestratorAgent", "action": "plan",
            "status": "FAILED", "message": "Policyholder not found",
            "timestamp": datetime.now().isoformat()
        })
        return state

    decision = legacy_orchestrate(ph)

    plan = {
        "journey_step": decision.journey_step,
        "channel": decision.channel,
        "channel_sequence": decision.channel_sequence,
        "recommended_agent": decision.recommended_agent,
        "tone": decision.tone,
        "timing": decision.timing,
        "lapse_risk": decision.lapse_risk,
        "priority_score": decision.priority_score,
        "high_complexity": decision.high_complexity,
        "complexity_reasons": decision.complexity_reasons,
        "offer_package": {
            "total_savings": sum(o.savings_inr for o in decision.offer_package.offers) if decision.offer_package else 0,
            "offer_count": len(decision.offer_package.offers) if decision.offer_package else 0,
        },
    }

    evidence = json.dumps({
        "plan": plan,
        "context_keys": list(decision.context.keys()),
        "system_prompt_used": get_active_prompt("OrchestratorAgent")[:100] + "...",
    }, indent=2)

    end_span(trace_id, span.span_id,
             output_data=plan, evidence=evidence)

    state["plan"] = plan
    state["decision"] = {
        "context": decision.context,
        "recommended_agent": decision.recommended_agent,
        "tone": decision.tone,
        "journey_step": decision.journey_step,
        "offer_ids": [o.offer_id for o in decision.offer_package.offers] if decision.offer_package else [],
    }
    state["stream_events"].append({
        "agent": "OrchestratorAgent", "action": "plan",
        "status": "COMPLETED",
        "message": f"Plan created: {decision.recommended_agent} via {decision.channel} "
                   f"(risk: {decision.lapse_risk}, priority: {decision.priority_score})",
        "timestamp": datetime.now().isoformat()
    })
    return state


def execute_node(state: RenewalState) -> RenewalState:
    """
    EXECUTE (Draft): Generate the proposed message but do NOT deliver yet.
    """
    trace_id = state["trace_id"]
    decision = state["decision"]
    policy_id = state["policy_id"]

    if not decision:
        state["error"] = "No decision from planner"
        return state

    agent_name = decision["recommended_agent"]
    context = decision["context"]

    # Human Queue routing (Terminal, no critique gate needed for human briefing)
    if agent_name == "HumanQueueManager":
        span = start_span(trace_id, "HumanQueueManager", "escalate",
                          input_data={"policy_id": policy_id, "reasons": state["plan"].get("complexity_reasons", [])})
        briefing = escalate(
            policy_id,
            f"Auto-escalated by planner: {'; '.join(state['plan'].get('complexity_reasons', []))}"
        )
        evidence = json.dumps({
            "case_id": briefing.case_id,
            "specialist_type": briefing.specialist_type,
            "priority": briefing.priority,
        }, indent=2)
        end_span(trace_id, span.span_id,
                 output_data={"case_id": briefing.case_id, "specialist": briefing.specialist_type},
                 evidence=evidence)
        log_event(EventType.ESCALATION, policy_id, "HumanQueueManager",
                  "auto_handoff", "human", f"Case: {briefing.case_id}", irdai_relevant=True)

        state["agent_output"] = {"routed_to_human": True, "case_id": briefing.case_id}
        state["channel_used"] = "human"
        state["message"] = f"Escalated to {briefing.specialist_type} (Case: {briefing.case_id})"
        state["critique_verdict"] = "SKIP"
        state["stream_events"].append({
            "agent": "HumanQueueManager", "action": "escalate",
            "status": "COMPLETED",
            "message": f"Case escalated to {briefing.specialist_type}",
            "timestamp": datetime.now().isoformat()
        })
        return state

    span = start_span(trace_id, agent_name, "draft_message",
                      input_data={"policy_id": policy_id, "channel": decision.get("tone", "")})

    try:
        if agent_name == "EmailAgent":
            # Call with deliver=False for pre-critique draft
            mail = send_email(
                policy_id, context.get("email", "customer@example.com"),
                context, tone=decision.get("tone", "friendly"),
                nudge_number=1,
                offer_ids=decision.get("offer_ids", []),
                deliver=False
            )
            state["message"] = mail.body
            state["channel_used"] = "email"
            state["agent_output"] = {"subject": mail.subject, "body": mail.body}

        elif agent_name == "VoiceAgent":
            # For voice, we critique the script/transcript simulation draft
            call = make_call(policy_id, context, journey_step=decision.get("journey_step", "T20"))
            voice_excerpt = next(
                (t.get("text", "") for t in call.call_session.transcript if t.get("role") == "assistant"),
                f"Voice call outcome: {call.outcome}",
            )
            state["message"] = voice_excerpt
            state["channel_used"] = "voice"
            state["agent_output"] = {
                "voice_outcome": call.outcome,
                "escalated": call.escalated,
                "objections": call.objections_handled,
                "call_session": asdict(call.call_session)
            }

        else:  # WhatsAppAgent
            wa_msg = send_whatsapp(
                policy_id, context.get("phone", "+910000000000"),
                context, tone=decision.get("tone", "friendly"),
            )
            state["message"] = wa_msg.body
            state["channel_used"] = "whatsapp"
            state["agent_output"] = {"body": wa_msg.body}

        evidence = json.dumps({
            "agent": agent_name,
            "channel": state["channel_used"],
            "message_preview": state["message"][:200],
            "is_draft": True
        }, indent=2)

        end_span(trace_id, span.span_id,
                 output_data=state["agent_output"], evidence=evidence)

        state["stream_events"].append({
            "agent": agent_name, "action": "draft_message",
            "status": "COMPLETED",
            "message": f"Draft generated for {state['channel_used']}. Ready for Critique Agent review.",
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        end_span(trace_id, span.span_id,
                 status=SpanStatus.FAILED, error=str(e))
        state["error"] = str(e)
        state["stream_events"].append({
            "agent": agent_name, "action": "draft_message",
            "status": "FAILED", "message": str(e),
            "timestamp": datetime.now().isoformat()
        })

    return state


def critique_node(state: RenewalState) -> RenewalState:
    """
    CRITIQUE: Per-agent critique validation.
    Uses the channel-specific critique agent (CritiqueAgent_Email, etc.)
    """
    trace_id = state["trace_id"]
    policy_id = state["policy_id"]
    channel = state.get("channel_used", "email")
    message = state.get("message", "")

    if state.get("critique_verdict") == "SKIP":
        return state

    if not message:
        state["critique_verdict"] = "SKIP"
        return state

    # Use per-agent critique
    critique_agent_name = f"CritiqueAgent_{channel.capitalize()}"
    span = start_span(trace_id, critique_agent_name, "evaluate",
                      input_data={"message_preview": message[:100], "channel": channel})

    agent_name = state["decision"]["recommended_agent"] if state.get("decision") else "Unknown"
    context = state["decision"]["context"] if state.get("decision") else {}

    critique = evaluate(message, context, policy_id, agent_name, channel)
    record_critique(critique)

    critique_dict = {
        "verdict": critique.verdict.value,
        "overall_score": critique.overall_score,
        "passed_checks": critique.passed_checks,
        "failed_checks": critique.failed_checks,
        "block_reason": critique.block_reason,
        "regenerate_feedback": critique.regenerate_feedback,
        "cost_inr": critique.cost_inr,
    }

    evidence = json.dumps({
        "critique_agent": critique_agent_name,
        "system_prompt": get_active_prompt(critique_agent_name)[:100] + "..." if get_active_prompt(critique_agent_name) else "N/A",
        "verdict": critique.verdict.value,
        "score": critique.overall_score,
        "passed": critique.passed_checks,
        "failed": critique.failed_checks,
    }, indent=2)

    end_span(trace_id, span.span_id,
             output_data=critique_dict, evidence=evidence)

    state["critique_result"] = critique_dict
    state["critique_verdict"] = critique.verdict.value

    state["stream_events"].append({
        "agent": critique_agent_name, "action": "evaluate",
        "status": "COMPLETED",
        "message": f"Critique: {critique.verdict.value} (score: {critique.overall_score:.0%})",
        "timestamp": datetime.now().isoformat()
    })

    if critique.verdict == CritiqueVerdict.REGENERATE:
        state["regeneration_count"] = state.get("regeneration_count", 0) + 1
    elif critique.verdict == CritiqueVerdict.BLOCK:
        log_event(EventType.ESCALATION, policy_id, critique_agent_name,
                  "critique_block", channel, critique.block_reason or "blocked", irdai_relevant=True)
        # Escalation rule from XML: Blocked -> Urgent Manual Queue
        from agents.human_queue_manager import escalate
        escalate(policy_id, f"Critique Agent BLOCKED: {critique.block_reason}")

    return state


def deliver_node(state: RenewalState) -> RenewalState:
    """
    DELIVER: Final step to actually send the message/call now that it has passed critique.
    """
    trace_id = state["trace_id"]
    policy_id = state["policy_id"]
    channel = state.get("channel_used", "")
    decision = state.get("decision", {})
    context = decision.get("context", {})

    span = start_span(trace_id, "DeliveryAgent", "deliver",
                      input_data={"channel": channel, "policy_id": policy_id})

    try:
        if channel == "email":
            from agents.email_agent import deliver_email_result
            deliver_email_result(
                policy_id, context.get("email", "customer@example.com"),
                context, nudge_number=1
            )
            log_event(EventType.AGENT_ACTION, policy_id, "EmailAgent",
                      "sent_renewal_email", "email", "delivered")

        elif channel == "whatsapp":
            # For WA, currently it's a print-driven stub in send_whatsapp
            # In a real system, the actual API call would move here.
            log_event(EventType.AGENT_ACTION, policy_id, "WhatsAppAgent",
                      "sent_renewal_message", "whatsapp", "delivered")

        elif channel == "voice":
            # Voice call execution was already 'simulated' in execute_node to get a transcript for critique
            # In real mode, the actual outbound trigger would happen here.
            log_event(EventType.AGENT_ACTION, policy_id, "VoiceAgent",
                      "placed_outbound_call", "voice", state["agent_output"].get("voice_outcome"))

        state["stream_events"].append({
            "agent": "DeliveryAgent", "action": "deliver",
            "status": "COMPLETED",
            "message": f"Message successfully delivered via {channel}.",
            "timestamp": datetime.now().isoformat()
        })
        end_span(trace_id, span.span_id, output_data={"status": "delivered"})

    except Exception as e:
        end_span(trace_id, span.span_id, status=SpanStatus.FAILED, error=str(e))
        state["error"] = f"Delivery failed: {str(e)}"

    return state


def respond_node(state: RenewalState) -> RenewalState:
    """
    RESPOND: Assemble the final response with all trace information.
    """
    trace_id = state["trace_id"]
    span = start_span(trace_id, "ResponseAssembler", "assemble",
                      input_data={"verdict": state.get("critique_verdict", "N/A")})

    response = {
        "trace_id": trace_id,
        "policy_id": state["policy_id"],
        "plan": state.get("plan", {}),
        "channel_used": state.get("channel_used", ""),
        "message": state.get("message", ""),
        "critique": state.get("critique_result", {}),
        "agent_output": state.get("agent_output", {}),
        "routed_to_human": state.get("channel_used") == "human",
        "stream_events": state.get("stream_events", []),
        "error": state.get("error"),
    }

    end_span(trace_id, span.span_id,
             output_data={"status": "assembled"},
             evidence=json.dumps({"response_keys": list(response.keys())}))

    end_trace(trace_id, SpanStatus.COMPLETED if not state.get("error") else SpanStatus.FAILED)

    state["final_response"] = response
    return state


# ── Routing Logic ─────────────────────────────────────────────────────────────

def should_proceed(state: RenewalState) -> str:
    """Route after critique: regenerate, block (human), or deliver."""
    verdict = state.get("critique_verdict", "PASS")
    regen_count = state.get("regeneration_count", 0)

    if verdict == "REGENERATE" and regen_count < 2:
        return "execute"
    elif verdict == "BLOCK":
        return "respond"   # Blocked messages are not delivered, final response shows block reason
    elif verdict == "PASS" or verdict == "SKIP":
        return "deliver"
    return "respond"


# ── Build the LangGraph ──────────────────────────────────────────────────────

def build_renewal_graph() -> StateGraph:
    """Build the Plan-Execute-Critique-Deliver-Respond LangGraph."""
    graph = StateGraph(RenewalState)

    graph.add_node("plan", plan_node)
    graph.add_node("execute", execute_node)
    graph.add_node("critique", critique_node)
    graph.add_node("deliver", deliver_node)
    graph.add_node("respond", respond_node)

    graph.set_entry_point("plan")
    graph.add_edge("plan", "execute")
    graph.add_edge("execute", "critique")
    graph.add_conditional_edges("critique", should_proceed, {
        "execute": "execute",
        "deliver": "deliver",
        "respond": "respond",
    })
    graph.add_edge("deliver", "respond")
    graph.add_edge("respond", END)

    return graph


# ── Public API ────────────────────────────────────────────────────────────────

_GRAPH = None

def get_graph():
    global _GRAPH
    if _GRAPH is None:
        _GRAPH = build_renewal_graph().compile()
    return _GRAPH


def run_renewal_journey(policy_id: str) -> dict:
    """
    Execute a complete renewal journey for a policyholder
    using the Plan-Execute-Critique-Respond LangGraph.

    Returns the full response with trace information.
    """
    trace = start_trace(policy_id, metadata={"source": "langgraph_orchestrator"})

    initial_state: RenewalState = {
        "policy_id": policy_id,
        "trace_id": trace.trace_id,
        "plan": {},
        "decision": None,
        "agent_output": {},
        "channel_used": "",
        "message": "",
        "critique_result": {},
        "critique_verdict": "",
        "regeneration_count": 0,
        "final_response": {},
        "stream_events": [],
        "error": None,
    }

    graph = get_graph()
    result = graph.invoke(initial_state)

    return result.get("final_response", result)
