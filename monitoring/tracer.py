"""
monitoring/tracer.py
Model Tracing System — LangSmith-style execution tracing

Features:
  - Unique trace ID per journey execution
  - Tracks agent-to-agent communication
  - Records input/output/duration for each agent step
  - Provides streaming updates via WebSocket
  - Evidence stored as simple text/JSON per conversation
"""
from __future__ import annotations
import uuid
import time
import json
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional, Any
from enum import Enum


class SpanStatus(str, Enum):
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"


@dataclass
class TraceSpan:
    """A single agent execution span within a trace."""
    span_id: str
    trace_id: str
    agent_name: str
    action: str
    status: SpanStatus = SpanStatus.RUNNING
    input_data: dict = field(default_factory=dict)
    output_data: dict = field(default_factory=dict)
    evidence: str = ""  # Simple text/JSON evidence for the conversation
    start_time: str = field(default_factory=lambda: datetime.now().isoformat())
    end_time: Optional[str] = None
    duration_ms: float = 0
    parent_span_id: Optional[str] = None
    children: list[str] = field(default_factory=list)
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "span_id": self.span_id,
            "trace_id": self.trace_id,
            "agent_name": self.agent_name,
            "action": self.action,
            "status": self.status.value,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "evidence": self.evidence,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "parent_span_id": self.parent_span_id,
            "children": self.children,
            "error": self.error,
            "metadata": self.metadata,
        }


@dataclass
class Trace:
    """A complete execution trace for one renewal journey."""
    trace_id: str
    policy_id: str
    status: SpanStatus = SpanStatus.RUNNING
    spans: list[TraceSpan] = field(default_factory=list)
    start_time: str = field(default_factory=lambda: datetime.now().isoformat())
    end_time: Optional[str] = None
    total_duration_ms: float = 0
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "trace_id": self.trace_id,
            "policy_id": self.policy_id,
            "status": self.status.value,
            "spans": [s.to_dict() for s in self.spans],
            "start_time": self.start_time,
            "end_time": self.end_time,
            "total_duration_ms": self.total_duration_ms,
            "span_count": len(self.spans),
            "metadata": self.metadata,
        }


# ── Global Trace Store ────────────────────────────────────────────────────────
_TRACES: dict[str, Trace] = {}
_ACTIVE_TRACE: Optional[str] = None


# ── WebSocket subscribers for live streaming ──────────────────────────────────
_WS_SUBSCRIBERS: list = []


def add_ws_subscriber(ws):
    _WS_SUBSCRIBERS.append(ws)


def remove_ws_subscriber(ws):
    if ws in _WS_SUBSCRIBERS:
        _WS_SUBSCRIBERS.remove(ws)


async def _broadcast_event(event: dict):
    """Broadcast trace event to all WebSocket subscribers."""
    message = json.dumps(event, default=str)
    dead = []
    for ws in _WS_SUBSCRIBERS:
        try:
            await ws.send_text(message)
        except Exception:
            dead.append(ws)
    for ws in dead:
        remove_ws_subscriber(ws)


# ── Trace Lifecycle ───────────────────────────────────────────────────────────

def start_trace(policy_id: str, metadata: dict = None) -> Trace:
    """Start a new execution trace for a policy renewal journey."""
    global _ACTIVE_TRACE
    trace_id = f"trace-{uuid.uuid4().hex[:12]}"
    trace = Trace(
        trace_id=trace_id,
        policy_id=policy_id,
        metadata=metadata or {},
    )
    _TRACES[trace_id] = trace
    _ACTIVE_TRACE = trace_id
    return trace


def end_trace(trace_id: str, status: SpanStatus = SpanStatus.COMPLETED) -> Trace:
    """End an execution trace."""
    global _ACTIVE_TRACE
    trace = _TRACES.get(trace_id)
    if trace:
        trace.status = status
        trace.end_time = datetime.now().isoformat()
        start = datetime.fromisoformat(trace.start_time)
        end = datetime.fromisoformat(trace.end_time)
        trace.total_duration_ms = (end - start).total_seconds() * 1000
    if _ACTIVE_TRACE == trace_id:
        _ACTIVE_TRACE = None
    return trace


def start_span(
    trace_id: str,
    agent_name: str,
    action: str,
    input_data: dict = None,
    parent_span_id: str = None,
    metadata: dict = None,
) -> TraceSpan:
    """Start a new span within a trace."""
    trace = _TRACES.get(trace_id)
    if not trace:
        raise ValueError(f"Trace {trace_id} not found")

    span = TraceSpan(
        span_id=f"span-{uuid.uuid4().hex[:8]}",
        trace_id=trace_id,
        agent_name=agent_name,
        action=action,
        input_data=input_data or {},
        parent_span_id=parent_span_id,
        metadata=metadata or {},
    )
    trace.spans.append(span)

    # Link parent → child
    if parent_span_id:
        parent = next((s for s in trace.spans if s.span_id == parent_span_id), None)
        if parent:
            parent.children.append(span.span_id)

    return span


def end_span(
    trace_id: str,
    span_id: str,
    output_data: dict = None,
    evidence: str = "",
    status: SpanStatus = SpanStatus.COMPLETED,
    error: str = None,
) -> TraceSpan:
    """End a span with output data and evidence."""
    trace = _TRACES.get(trace_id)
    if not trace:
        return None
    span = next((s for s in trace.spans if s.span_id == span_id), None)
    if not span:
        return None

    span.status = status
    span.output_data = output_data or {}
    span.evidence = evidence
    span.end_time = datetime.now().isoformat()
    span.error = error

    start = datetime.fromisoformat(span.start_time)
    end = datetime.fromisoformat(span.end_time)
    span.duration_ms = (end - start).total_seconds() * 1000

    return span


# ── Query API ─────────────────────────────────────────────────────────────────

def get_trace(trace_id: str) -> Optional[dict]:
    """Get a complete trace by ID."""
    trace = _TRACES.get(trace_id)
    return trace.to_dict() if trace else None


def get_all_traces(limit: int = 50) -> list[dict]:
    """Get all traces, most recent first."""
    traces = sorted(
        _TRACES.values(),
        key=lambda t: t.start_time,
        reverse=True,
    )[:limit]
    return [t.to_dict() for t in traces]


def get_traces_by_policy(policy_id: str) -> list[dict]:
    """Get all traces for a specific policy."""
    return [
        t.to_dict() for t in _TRACES.values()
        if t.policy_id == policy_id
    ]


def get_span_detail(trace_id: str, span_id: str) -> Optional[dict]:
    """Get detailed info for a specific span (click-to-expand in dashboard)."""
    trace = _TRACES.get(trace_id)
    if not trace:
        return None
    span = next((s for s in trace.spans if s.span_id == span_id), None)
    return span.to_dict() if span else None


def get_trace_stats() -> dict:
    """Get aggregate tracing statistics."""
    total = len(_TRACES)
    completed = len([t for t in _TRACES.values() if t.status == SpanStatus.COMPLETED])
    failed = len([t for t in _TRACES.values() if t.status == SpanStatus.FAILED])
    total_spans = sum(len(t.spans) for t in _TRACES.values())
    avg_duration = (
        sum(t.total_duration_ms for t in _TRACES.values() if t.total_duration_ms > 0)
        / max(completed, 1)
    )

    # Agent distribution
    agent_counts = {}
    for trace in _TRACES.values():
        for span in trace.spans:
            agent_counts[span.agent_name] = agent_counts.get(span.agent_name, 0) + 1

    return {
        "total_traces": total,
        "completed": completed,
        "failed": failed,
        "running": total - completed - failed,
        "total_spans": total_spans,
        "avg_duration_ms": round(avg_duration, 1),
        "agent_distribution": agent_counts,
    }
