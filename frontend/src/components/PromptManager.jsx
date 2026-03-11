/**
 * PromptManager — View, edit, and version system prompts for all agents
 * Includes weekly feedback improvement trigger
 */
import { useState, useEffect } from 'react'
import { getAllPrompts, updatePrompt, triggerImprovement, getPromptDashboard } from '../api'

const AGENT_ICONS = {
    OrchestratorAgent: '🧠',
    EmailAgent: '📧',
    WhatsAppAgent: '💬',
    VoiceAgent: '📞',
    CritiqueAgent_Email: '🔍',
    CritiqueAgent_WhatsApp: '🔍',
    CritiqueAgent_Voice: '🔍',
    PromptGeneratorAgent: '🤖',
}

export default function PromptManager() {
    const [prompts, setPrompts] = useState({})
    const [dashboard, setDashboard] = useState(null)
    const [expandedAgent, setExpandedAgent] = useState(null)
    const [editValues, setEditValues] = useState({})
    const [saving, setSaving] = useState(false)
    const [improving, setImproving] = useState(false)
    const [message, setMessage] = useState(null)

    useEffect(() => {
        loadData()
    }, [])

    async function loadData() {
        try {
            const [p, d] = await Promise.all([
                getAllPrompts().catch(() => ({})),
                getPromptDashboard().catch(() => null),
            ])
            setPrompts(p)
            setDashboard(d)
        } catch { }
    }

    function toggleAgent(name) {
        if (expandedAgent === name) {
            setExpandedAgent(null)
        } else {
            setExpandedAgent(name)
            if (!editValues[name]) {
                setEditValues(prev => ({ ...prev, [name]: prompts[name]?.system_prompt || '' }))
            }
        }
    }

    async function savePrompt(agentName) {
        setSaving(true)
        try {
            await updatePrompt(agentName, editValues[agentName], 'Updated from dashboard')
            setMessage({ type: 'success', text: `✅ ${agentName} prompt updated to new version` })
            await loadData()
        } catch (e) {
            setMessage({ type: 'error', text: `❌ Failed: ${e.message}` })
        } finally {
            setSaving(false)
            setTimeout(() => setMessage(null), 4000)
        }
    }

    async function runImprovement() {
        setImproving(true)
        try {
            const result = await triggerImprovement()
            const count = result.improvements?.length || 0
            setMessage({
                type: 'success',
                text: `🤖 PromptGeneratorAgent improved ${count} agent prompt(s)`,
            })
            await loadData()
        } catch (e) {
            setMessage({ type: 'error', text: `❌ Improvement failed: ${e.message}` })
        } finally {
            setImproving(false)
            setTimeout(() => setMessage(null), 4000)
        }
    }

    const promptEntries = Object.entries(prompts)

    return (
        <div>
            <div className="page-header">
                <div>
                    <h2>📝 Prompt Manager</h2>
                    <div className="subtitle">
                        View, edit, and version system prompts — Weekly auto-improvement from customer feedback
                    </div>
                </div>
                <div className="header-actions">
                    <button
                        className="btn btn-primary"
                        onClick={runImprovement}
                        disabled={improving}
                        style={{ opacity: improving ? 0.5 : 1 }}
                    >
                        {improving ? '⏳ Generating...' : '🤖 Run Weekly Improvement'}
                    </button>
                </div>
            </div>

            {/* Message Toast */}
            {message && (
                <div style={{
                    padding: '12px 20px',
                    borderRadius: 'var(--radius-sm)',
                    marginBottom: '16px',
                    background: message.type === 'success' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(244, 63, 94, 0.1)',
                    border: `1px solid ${message.type === 'success' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(244, 63, 94, 0.2)'}`,
                    color: message.type === 'success' ? 'var(--accent-emerald)' : 'var(--accent-rose)',
                    fontSize: '14px',
                    fontWeight: '600',
                }}>
                    {message.text}
                </div>
            )}

            {/* Stats */}
            {dashboard && (
                <div className="stat-grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)', marginBottom: '24px' }}>
                    <div className="stat-card indigo">
                        <div className="stat-label">Total Agents</div>
                        <div className="stat-value" style={{ fontSize: '22px' }}>{dashboard.agents?.length || 0}</div>
                    </div>
                    <div className="stat-card amber">
                        <div className="stat-label">Pending Feedback</div>
                        <div className="stat-value" style={{ fontSize: '22px' }}>{dashboard.total_pending_feedback || 0}</div>
                    </div>
                    <div className="stat-card emerald">
                        <div className="stat-label">Improvement Source</div>
                        <div className="stat-value" style={{ fontSize: '18px' }}>Customer + Critique</div>
                    </div>
                </div>
            )}

            {/* Prompt Cards */}
            {promptEntries.map(([agentName, data]) => (
                <div className="prompt-card" key={agentName}>
                    <div className="prompt-card-header" onClick={() => toggleAgent(agentName)}>
                        <div className="prompt-agent-name">
                            <span>{AGENT_ICONS[agentName] || '⚙️'}</span>
                            {agentName}
                            <span className="prompt-version-badge">v{data.active_version}</span>
                        </div>
                        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                                {data.total_versions} version(s) • {data.created_by}
                            </span>
                            <span style={{ fontSize: '14px', color: 'var(--text-muted)' }}>
                                {expandedAgent === agentName ? '▼' : '▶'}
                            </span>
                        </div>
                    </div>

                    <div className={`prompt-body ${expandedAgent === agentName ? 'open' : ''}`}>
                        <div style={{ marginBottom: '12px' }}>
                            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                                {data.description}
                            </span>
                        </div>

                        <textarea
                            className="prompt-textarea"
                            value={editValues[agentName] ?? data.system_prompt}
                            onChange={e => setEditValues(prev => ({ ...prev, [agentName]: e.target.value }))}
                            rows={10}
                        />

                        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '12px' }}>
                            <button
                                className="btn btn-secondary btn-sm"
                                onClick={() => setEditValues(prev => ({ ...prev, [agentName]: data.system_prompt }))}
                            >
                                ↩ Reset
                            </button>
                            <button
                                className="btn btn-primary btn-sm"
                                onClick={() => savePrompt(agentName)}
                                disabled={saving}
                            >
                                {saving ? 'Saving...' : '💾 Save New Version'}
                            </button>
                        </div>
                    </div>
                </div>
            ))}

            {promptEntries.length === 0 && (
                <div className="card" style={{ textAlign: 'center', padding: '60px' }}>
                    <div style={{ fontSize: '48px', marginBottom: '16px' }}>📝</div>
                    <div style={{ fontSize: '16px', fontWeight: '600' }}>
                        Loading prompts...
                    </div>
                    <div style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '8px' }}>
                        Start the backend server to see all agent system prompts here.
                    </div>
                </div>
            )}
        </div>
    )
}
