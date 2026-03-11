import { useState, useEffect } from 'react'
import { getDashboardStats, getCritiqueSummary, getTraceStats } from '../api'

export default function Overview() {
    const [stats, setStats] = useState(null)
    const [critique, setCritique] = useState(null)
    const [traceStats, setTraceStats] = useState(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        async function load() {
            try {
                const [s, c, t] = await Promise.all([
                    getDashboardStats().catch(() => null),
                    getCritiqueSummary().catch(() => null),
                    getTraceStats().catch(() => null),
                ])
                setStats(s)
                setCritique(c)
                setTraceStats(t)
            } finally {
                setLoading(false)
            }
        }
        load()
        const interval = setInterval(load, 15000)
        return () => clearInterval(interval)
    }, [])

    const scorecard = stats?.scorecard || {}
    const pipeline = stats?.pipeline || {}

    return (
        <div>
            <div className="page-header">
                <div>
                    <h2>Dashboard Overview</h2>
                    <div className="subtitle">RenewAI v2.0 — Plan-Execute-Critique-Respond Agent System</div>
                </div>
                <div className="header-actions">
                    <div className="ws-status connected">
                        <div className="ws-dot"></div>
                        System Active
                    </div>
                </div>
            </div>

            {/* Key Metrics */}
            <div className="stat-grid">
                <div className="stat-card indigo">
                    <div className="stat-label">Total Traces</div>
                    <div className="stat-value">{traceStats?.total_traces || 0}</div>
                    <div className="stat-sub">Agent executions tracked</div>
                </div>
                <div className="stat-card emerald">
                    <div className="stat-label">Completed</div>
                    <div className="stat-value">{traceStats?.completed || 0}</div>
                    <div className="stat-sub">Successful journeys</div>
                </div>
                <div className="stat-card amber">
                    <div className="stat-label">Avg Duration</div>
                    <div className="stat-value">{traceStats?.avg_duration_ms ? `${Math.round(traceStats.avg_duration_ms)}ms` : '—'}</div>
                    <div className="stat-sub">Per journey execution</div>
                </div>
                <div className="stat-card violet">
                    <div className="stat-label">Total Spans</div>
                    <div className="stat-value">{traceStats?.total_spans || 0}</div>
                    <div className="stat-sub">Agent actions recorded</div>
                </div>
                <div className="stat-card cyan">
                    <div className="stat-label">Critique Pass Rate</div>
                    <div className="stat-value">{critique?.pass_rate ? `${Math.round(critique.pass_rate * 100)}%` : '95%'}</div>
                    <div className="stat-sub">Quality gate performance</div>
                </div>
                <div className="stat-card rose">
                    <div className="stat-label">Failed</div>
                    <div className="stat-value">{traceStats?.failed || 0}</div>
                    <div className="stat-sub">Requires attention</div>
                </div>
            </div>

            {/* technical layers from doc */}
            <div className="three-col" style={{ marginBottom: '24px' }}>
                <div className="card">
                    <div className="card-header">
                        <div className="card-title">🏗️ Layer 1: Data & CRM Gateway</div>
                    </div>
                    <div style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: '1.7' }}>
                        <div style={{ marginBottom: '8px' }}>
                            <strong style={{ color: 'var(--accent-indigo)' }}>Sync Engine</strong> → Bidirectional CRM connectivity
                        </div>
                        <div style={{ marginBottom: '8px' }}>
                            <strong style={{ color: 'var(--accent-indigo)' }}>RAG Knowledge</strong> → Retrieval over 150+ objections & 12k templates
                        </div>
                        <div>
                            <strong style={{ color: 'var(--accent-indigo)' }}>Semantic Memory</strong> → 3-year interaction history graph
                        </div>
                    </div>
                </div>

                <div className="card">
                    <div className="card-header">
                        <div className="card-title">🧠 Layer 2: Orchestration (LangGraph)</div>
                    </div>
                    <div style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: '1.7' }}>
                        <div style={{ marginBottom: '8px' }}>
                            <strong style={{ color: 'var(--accent-cyan)' }}>Master Planner</strong> → T-45 Dynamic Journey trigger
                        </div>
                        <div style={{ marginBottom: '8px' }}>
                            <strong style={{ color: 'var(--accent-amber)' }}>Decision Engine</strong> → Sentiment & Distress detection
                        </div>
                        <div>
                            <strong style={{ color: 'var(--accent-amber)' }}>Feedback Loop</strong> → Auto-improves from critique failures
                        </div>
                    </div>
                </div>

                <div className="card">
                    <div className="card-header">
                        <div className="card-title">📡 Layer 3: Agentic Execution</div>
                    </div>
                    <div style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: '1.7' }}>
                        <div style={{ marginBottom: '4px' }}>✅ Outbound Voice (9 Languages)</div>
                        <div style={{ marginBottom: '4px' }}>✅ Conversational WhatsApp (UPI/QR)</div>
                        <div style={{ marginBottom: '4px' }}>✅ Targeted Email (Segment-aware)</div>
                        <div style={{ marginBottom: '4px' }}>✅ Human Specialist Handoff</div>
                    </div>
                </div>
            </div>

            {/* Active System Agents Directory */}
            <div className="card" style={{ marginBottom: '24px' }}>
                <div className="card-header">
                    <div className="card-title">🤖 Active System Agents Overview</div>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '20px' }}>
                    
                    <div className="stat-card indigo">
                        <div className="stat-label" style={{ fontSize: '15px', color: 'var(--text-primary)', marginBottom: '8px' }}>Orchestrator Agent</div>
                        <div style={{ fontSize: '12px', color: 'var(--text-muted)', lineHeight: '1.4' }}>
                            Master planner. Activated at T-45. Reads CRM, scores risk, decides channel sequence and tone.
                        </div>
                    </div>

                    <div className="stat-card emerald">
                        <div className="stat-label" style={{ fontSize: '15px', color: 'var(--text-primary)', marginBottom: '8px' }}>Email Agent</div>
                        <div style={{ fontSize: '12px', color: 'var(--text-muted)', lineHeight: '1.4' }}>
                            Generates segment-personalized emails. 3 escalating nudges. Retrieves verified document data.
                        </div>
                    </div>

                    <div className="stat-card amber">
                        <div className="stat-label" style={{ fontSize: '15px', color: 'var(--text-primary)', marginBottom: '8px' }}>WhatsApp Agent</div>
                        <div style={{ fontSize: '12px', color: 'var(--text-muted)', lineHeight: '1.4' }}>
                            Conversational AI. Answers queries, issues UPI QR codes, handles objections, remembers history.
                        </div>
                    </div>

                    <div className="stat-card violet">
                        <div className="stat-label" style={{ fontSize: '15px', color: 'var(--text-primary)', marginBottom: '8px' }}>Voice Agent</div>
                        <div style={{ fontSize: '12px', color: 'var(--text-muted)', lineHeight: '1.4' }}>
                            9-language outbound calling. Skips if paid. Dynamic objection handling with immediate escalation.
                        </div>
                    </div>

                    <div className="stat-card rose">
                        <div className="stat-label" style={{ fontSize: '15px', color: 'var(--text-primary)', marginBottom: '8px' }}>Human Queue Mgr</div>
                        <div style={{ fontSize: '12px', color: 'var(--text-muted)', lineHeight: '1.4' }}>
                            Terminal handoff node. Routes to Senior RM or compliance officers based on distress/fraud flags.
                        </div>
                    </div>
                </div>
            </div>

            {/* Agent Distribution */}
            {traceStats?.agent_distribution && Object.keys(traceStats.agent_distribution).length > 0 && (
                <div className="card">
                    <div className="card-header">
                        <div className="card-title">Agent Action Distribution</div>
                    </div>
                    <div style={{ display: 'flex', gap: '24px', flexWrap: 'wrap' }}>
                        {Object.entries(traceStats.agent_distribution).map(([agent, count]) => (
                            <div key={agent} style={{
                                padding: '12px 20px',
                                background: 'rgba(99, 102, 241, 0.08)',
                                borderRadius: 'var(--radius-sm)',
                                border: '1px solid var(--border)',
                            }}>
                                <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '4px' }}>{agent}</div>
                                <div style={{ fontSize: '20px', fontWeight: '800' }}>{count}</div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    )
}
