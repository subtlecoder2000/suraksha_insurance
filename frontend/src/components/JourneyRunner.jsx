/**
 * JourneyRunner — Run renewal journeys with WebSocket streaming
 * Shows real-time streaming response of what each agent is performing
 */
import { useState, useRef, useEffect } from 'react'
import { useWebSocket } from '../hooks/useWebSocket'
import { getPipeline } from '../api'

const AGENT_CSS_MAP = {
    OrchestratorAgent: 'orchestrator',
    EmailAgent: 'email',
    WhatsAppAgent: 'whatsapp',
    VoiceAgent: 'voice',
    HumanQueueManager: 'human',
    ResponseAssembler: 'orchestrator',
}

function getAgentCss(name) {
    if (name?.startsWith('CritiqueAgent')) return 'critique'
    return AGENT_CSS_MAP[name] || 'orchestrator'
}

export default function JourneyRunner() {
    const [policyId, setPolicyId] = useState('POL-001')
    const [policies, setPolicies] = useState([])
    const [running, setRunning] = useState(false)
    const [result, setResult] = useState(null)
    const consoleRef = useRef(null)

    const wsUrl = `ws://${window.location.hostname}:8000/ws`
    const { isConnected, events, sendMessage, clearEvents } = useWebSocket(wsUrl)

    useEffect(() => {
        getPipeline()
            .then(data => setPolicies(data || []))
            .catch(() => { })
    }, [])

    useEffect(() => {
        if (consoleRef.current) {
            consoleRef.current.scrollTop = consoleRef.current.scrollHeight
        }
    }, [events])

    useEffect(() => {
        const last = events[events.length - 1]
        if (last?.type === 'journey_complete') {
            setRunning(false)
            setResult(last.result)
        }
    }, [events])

    function runJourney() {
        if (!isConnected || running) return
        clearEvents()
        setResult(null)
        setRunning(true)
        sendMessage({ action: 'run_journey', policy_id: policyId })
    }

    function formatTime(ts) {
        if (!ts) return ''
        const d = new Date(ts)
        return d.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })
    }

    return (
        <div>
            <div className="page-header">
                <div>
                    <h2>🚀 Run Renewal Journey</h2>
                    <div className="subtitle">
                        Execute Plan-Execute-Critique-Respond with live WebSocket streaming
                    </div>
                </div>
                <div className="header-actions">
                    <div className={`ws-status ${isConnected ? 'connected' : 'disconnected'}`}>
                        <div className="ws-dot"></div>
                        {isConnected ? 'WebSocket Connected' : 'Disconnected'}
                    </div>
                </div>
            </div>

            {/* Controls */}
            <div className="card" style={{ marginBottom: '24px' }}>
                <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
                    <div>
                        <label style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>
                            Policy ID
                        </label>
                        <select
                            className="select"
                            value={policyId}
                            onChange={e => setPolicyId(e.target.value)}
                            style={{ minWidth: '280px' }}
                        >
                            {policies.length > 0 ? (
                                policies.map(p => (
                                    <option key={p.policy_id} value={p.policy_id}>
                                        {p.policy_id} — {p.name} ({p.policy_type}, ₹{p.premium?.toLocaleString()})
                                    </option>
                                ))
                            ) : (
                                <>
                                    <option value="POL-001">POL-001 (Demo)</option>
                                    <option value="POL-002">POL-002 (Demo)</option>
                                    <option value="POL-003">POL-003 (Demo)</option>
                                </>
                            )}
                        </select>
                    </div>

                    <div style={{ marginTop: '20px' }}>
                        <button
                            className="btn btn-primary"
                            onClick={runJourney}
                            disabled={!isConnected || running}
                            style={{ opacity: (!isConnected || running) ? 0.5 : 1 }}
                        >
                            {running ? (
                                <>⏳ Running...</>
                            ) : (
                                <>▶ Run Journey</>
                            )}
                        </button>
                    </div>
                </div>
            </div>

            <div className="two-col">
                {/* Streaming Console */}
                <div style={{ gridColumn: '1 / -1' }}>
                    <div className="card-title" style={{ marginBottom: '12px', fontSize: '13px' }}>
                        📡 LIVE STREAMING CONSOLE
                    </div>
                    <div className="stream-console" ref={consoleRef}>
                        {events.length === 0 && (
                            <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '40px' }}>
                                {isConnected
                                    ? 'Ready. Click "Run Journey" to see live streaming events from each agent.'
                                    : 'Connecting to WebSocket server...'}
                            </div>
                        )}
                        {events.map((evt, i) => (
                            <div className="stream-event" key={i}>
                                <span className="stream-time">{formatTime(evt.timestamp || evt._receivedAt)}</span>
                                {evt.type === 'journey_start' && (
                                    <>
                                        <span className="stream-agent orchestrator">SYSTEM</span>
                                        <span className="stream-message">🚀 {evt.message}</span>
                                    </>
                                )}
                                {evt.type === 'agent_event' && (
                                    <>
                                        <span className={`stream-agent ${getAgentCss(evt.agent)}`}>
                                            {evt.agent}
                                        </span>
                                        <span className={`stream-status ${evt.status?.toLowerCase()}`}>
                                            {evt.status}
                                        </span>
                                        <span className="stream-message">{evt.message}</span>
                                    </>
                                )}
                                {evt.type === 'journey_complete' && (
                                    <>
                                        <span className="stream-agent orchestrator">SYSTEM</span>
                                        <span className="stream-message">
                                            ✅ Journey complete — Trace: {evt.result?.trace_id} | Channel: {evt.result?.channel_used}
                                            {evt.result?.critique?.verdict && ` | Critique: ${evt.result.critique.verdict}`}
                                        </span>
                                    </>
                                )}
                                {evt.type === 'pong' && null}
                                {!['journey_start', 'agent_event', 'journey_complete', 'pong', 'subscribed'].includes(evt.type) && (
                                    <>
                                        <span className="stream-agent orchestrator">INFO</span>
                                        <span className="stream-message">{JSON.stringify(evt)}</span>
                                    </>
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Result Card */}
            {result && (
                <div className="card" style={{ marginTop: '24px' }}>
                    <div className="card-header">
                        <div className="card-title">Journey Result</div>
                        <span className="stream-status completed">COMPLETED</span>
                    </div>
                    <div className="three-col" style={{ marginBottom: '16px' }}>
                        <div>
                            <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Trace ID</div>
                            <div style={{ fontFamily: 'monospace', color: 'var(--accent-indigo)', fontWeight: '600' }}>
                                {result.trace_id}
                            </div>
                        </div>
                        <div>
                            <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Channel</div>
                            <div style={{ fontWeight: '600', textTransform: 'capitalize' }}>
                                {result.channel_used}
                            </div>
                        </div>
                        <div>
                            <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Critique Verdict</div>
                            <div style={{
                                fontWeight: '700',
                                color: result.critique?.verdict === 'PASS' ? 'var(--accent-emerald)'
                                    : result.critique?.verdict === 'BLOCK' ? 'var(--accent-rose)'
                                        : 'var(--accent-amber)',
                            }}>
                                {result.critique?.verdict || 'N/A'}
                                {result.critique?.overall_score && ` (${Math.round(result.critique.overall_score * 100)}%)`}
                            </div>
                        </div>
                    </div>

                    {result.plan && (
                        <div className="evidence-panel">
                            <div className="evidence-title">Execution Plan</div>
                            <div className="evidence-content">{JSON.stringify(result.plan, null, 2)}</div>
                        </div>
                    )}
                </div>
            )}
        </div>
    )
}
