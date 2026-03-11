/**
 * TraceDashboard — LangSmith-style agent trace visualization
 * Shows agent-to-agent communication with click-to-expand span details
 */
import { useState, useEffect } from 'react'
import { getTraces, getTrace } from '../api'

const AGENT_COLORS = {
    OrchestratorAgent: 'var(--accent-indigo)',
    EmailAgent: 'var(--accent-cyan)',
    WhatsAppAgent: 'var(--accent-emerald)',
    VoiceAgent: 'var(--accent-violet)',
    HumanQueueManager: 'var(--accent-rose)',
    ResponseAssembler: 'var(--text-muted)',
}

function getCritiqueColor(name) {
    if (name?.includes('Email')) return 'var(--accent-cyan)'
    if (name?.includes('WhatsApp')) return 'var(--accent-emerald)'
    if (name?.includes('Voice')) return 'var(--accent-violet)'
    return 'var(--accent-amber)'
}

function getAgentColor(name) {
    if (name?.startsWith('CritiqueAgent')) return getCritiqueColor(name)
    return AGENT_COLORS[name] || 'var(--text-secondary)'
}

function SpanNode({ span, isExpanded, onToggle }) {
    const color = getAgentColor(span.agent_name)
    const statusColor = {
        COMPLETED: 'var(--accent-emerald)',
        RUNNING: 'var(--accent-amber)',
        FAILED: 'var(--accent-rose)',
        BLOCKED: 'var(--accent-rose)',
    }[span.status] || 'var(--text-muted)'

    return (
        <div className="span-node">
            <div
                className={`span-node-content ${isExpanded ? 'expanded' : ''}`}
                onClick={onToggle}
            >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div className="span-agent-name" style={{ color }}>
                        <span style={{
                            width: '8px', height: '8px', borderRadius: '50%',
                            background: statusColor, display: 'inline-block',
                            boxShadow: `0 0 6px ${statusColor}`,
                        }} />
                        {span.agent_name}
                    </div>
                    <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                        {span.duration_ms > 0 && (
                            <span className="span-duration">{Math.round(span.duration_ms)}ms</span>
                        )}
                        <span className={`stream-status ${span.status.toLowerCase()}`}>
                            {span.status}
                        </span>
                    </div>
                </div>
                <div className="span-action">
                    {span.action}
                    {span.span_id && (
                        <span style={{ marginLeft: '8px', color: 'var(--text-muted)', fontSize: '10px' }}>
                            {span.span_id}
                        </span>
                    )}
                </div>
            </div>

            {isExpanded && (
                <div className="span-detail">
                    {/* Input */}
                    {span.input_data && Object.keys(span.input_data).length > 0 && (
                        <div style={{ marginBottom: '12px' }}>
                            <div style={{ color: 'var(--accent-indigo)', fontWeight: '700', fontSize: '11px', marginBottom: '4px' }}>
                                INPUT
                            </div>
                            <pre>{JSON.stringify(span.input_data, null, 2)}</pre>
                        </div>
                    )}

                    {/* Output */}
                    {span.output_data && Object.keys(span.output_data).length > 0 && (
                        <div style={{ marginBottom: '12px' }}>
                            <div style={{ color: 'var(--accent-emerald)', fontWeight: '700', fontSize: '11px', marginBottom: '4px' }}>
                                OUTPUT
                            </div>
                            <pre>{JSON.stringify(span.output_data, null, 2)}</pre>
                        </div>
                    )}

                    {/* Evidence */}
                    {span.evidence && (
                        <div className="evidence-panel">
                            <div className="evidence-title">📋 Evidence (Text/JSON)</div>
                            <div className="evidence-content">{span.evidence}</div>
                        </div>
                    )}

                    {/* Error */}
                    {span.error && (
                        <div style={{ marginTop: '8px', color: 'var(--accent-rose)', fontSize: '12px' }}>
                            ❌ Error: {span.error}
                        </div>
                    )}
                </div>
            )}
        </div>
    )
}

export default function TraceDashboard() {
    const [traces, setTraces] = useState([])
    const [stats, setStats] = useState(null)
    const [selectedTrace, setSelectedTrace] = useState(null)
    const [expandedSpans, setExpandedSpans] = useState(new Set())
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        loadTraces()
        const interval = setInterval(loadTraces, 5000)
        return () => clearInterval(interval)
    }, [])

    async function loadTraces() {
        try {
            const data = await getTraces(30)
            setTraces(data.traces || [])
            setStats(data.stats)
        } catch {
            // API might not be running yet
        } finally {
            setLoading(false)
        }
    }

    async function selectTrace(traceId) {
        try {
            const detail = await getTrace(traceId)
            setSelectedTrace(detail)
            setExpandedSpans(new Set())
        } catch (e) {
            console.error('Failed to load trace:', e)
        }
    }

    function toggleSpan(spanId) {
        setExpandedSpans(prev => {
            const next = new Set(prev)
            if (next.has(spanId)) next.delete(spanId)
            else next.add(spanId)
            return next
        })
    }

    return (
        <div>
            <div className="page-header">
                <div>
                    <h2>🔍 Agent Traces</h2>
                    <div className="subtitle">
                        LangSmith-style execution tracing — click spans to see agent I/O and evidence
                    </div>
                </div>
                <div className="header-actions">
                    <button className="btn btn-secondary btn-sm" onClick={loadTraces}>
                        ↻ Refresh
                    </button>
                </div>
            </div>

            {/* Stats Bar */}
            {stats && (
                <div className="stat-grid" style={{ gridTemplateColumns: 'repeat(5, 1fr)', marginBottom: '24px' }}>
                    <div className="stat-card indigo">
                        <div className="stat-label">Total</div>
                        <div className="stat-value" style={{ fontSize: '22px' }}>{stats.total_traces}</div>
                    </div>
                    <div className="stat-card emerald">
                        <div className="stat-label">Completed</div>
                        <div className="stat-value" style={{ fontSize: '22px' }}>{stats.completed}</div>
                    </div>
                    <div className="stat-card amber">
                        <div className="stat-label">Running</div>
                        <div className="stat-value" style={{ fontSize: '22px' }}>{stats.running}</div>
                    </div>
                    <div className="stat-card rose">
                        <div className="stat-label">Failed</div>
                        <div className="stat-value" style={{ fontSize: '22px' }}>{stats.failed}</div>
                    </div>
                    <div className="stat-card cyan">
                        <div className="stat-label">Avg Duration</div>
                        <div className="stat-value" style={{ fontSize: '22px' }}>{Math.round(stats.avg_duration_ms || 0)}ms</div>
                    </div>
                </div>
            )}

            <div className="two-col">
                {/* Trace List */}
                <div>
                    <div className="card-title" style={{ marginBottom: '12px', fontSize: '13px' }}>
                        TRACE LIST ({traces.length})
                    </div>
                    <div className="trace-list">
                        {traces.length === 0 && !loading && (
                            <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
                                No traces yet. Run a journey to see traces appear here.
                            </div>
                        )}
                        {traces.map(trace => (
                            <div
                                key={trace.trace_id}
                                className={`trace-item ${selectedTrace?.trace_id === trace.trace_id ? 'active' : ''}`}
                                onClick={() => selectTrace(trace.trace_id)}
                            >
                                <div className={`trace-status ${trace.status.toLowerCase()}`} />
                                <div className="trace-info">
                                    <div className="trace-id">{trace.trace_id}</div>
                                    <div className="trace-meta">
                                        {trace.policy_id} • {trace.span_count} spans
                                    </div>
                                </div>
                                <div className="trace-duration">
                                    {trace.total_duration_ms > 0 ? `${Math.round(trace.total_duration_ms)}ms` : '—'}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Trace Detail — Agent-to-Agent Communication */}
                <div>
                    {selectedTrace ? (
                        <div className="card" style={{ padding: '0' }}>
                            <div style={{
                                padding: '16px 20px',
                                borderBottom: '1px solid var(--border)',
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'center',
                            }}>
                                <div>
                                    <div style={{ fontWeight: '700', fontSize: '15px' }}>
                                        Trace: {selectedTrace.trace_id}
                                    </div>
                                    <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px' }}>
                                        Policy: {selectedTrace.policy_id} • {selectedTrace.span_count} agent actions
                                        {selectedTrace.total_duration_ms > 0 &&
                                            ` • ${Math.round(selectedTrace.total_duration_ms)}ms total`
                                        }
                                    </div>
                                </div>
                                <span className={`stream-status ${selectedTrace.status.toLowerCase()}`}>
                                    {selectedTrace.status}
                                </span>
                            </div>

                            <div className="span-tree">
                                {(selectedTrace.spans || []).map(span => (
                                    <SpanNode
                                        key={span.span_id}
                                        span={span}
                                        isExpanded={expandedSpans.has(span.span_id)}
                                        onToggle={() => toggleSpan(span.span_id)}
                                    />
                                ))}
                            </div>
                        </div>
                    ) : (
                        <div className="card" style={{ textAlign: 'center', padding: '60px 40px' }}>
                            <div style={{ fontSize: '48px', marginBottom: '16px' }}>🔍</div>
                            <div style={{ fontSize: '16px', fontWeight: '600', marginBottom: '8px' }}>
                                Select a trace to inspect
                            </div>
                            <div style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
                                Click on a trace to see agent-to-agent communication,
                                execution response, and evidence for each step.
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}
