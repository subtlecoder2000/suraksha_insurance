import { useState } from 'react'
import './index.css'
import TraceDashboard from './components/TraceDashboard'
import PromptManager from './components/PromptManager'
import JourneyRunner from './components/JourneyRunner'
import Overview from './components/Overview'
import ChatWidget from './components/ChatWidget'
import PipelineView from './components/PipelineView'
import AuditLogView from './components/AuditLogView'

const NAV_ITEMS = [
    { id: 'overview', label: 'Overview', icon: '📊', section: 'Dashboard' },
    { id: 'pipeline', label: 'Policy Pipeline', icon: '📋', section: 'Dashboard' },
    { id: 'traces', label: 'Agent Traces', icon: '🔍', section: 'Dashboard' },
    { id: 'journey', label: 'Run Journey', icon: '🚀', section: 'Actions' },
    { id: 'prompts', label: 'Prompt Manager', icon: '📝', section: 'Management' },
    { id: 'audit', label: 'Audit Logs', icon: '🛡️', section: 'Management' },
]

function App() {
    const [activePage, setActivePage] = useState('overview')

    const sections = {}
    NAV_ITEMS.forEach(item => {
        if (!sections[item.section]) sections[item.section] = []
        sections[item.section].push(item)
    })

    return (
        <div className="app-container">
            {/* Sidebar */}
            <nav className="sidebar">
                <div className="sidebar-logo">
                    <div className="logo-icon">🛡️</div>
                    <div>
                        <h1>RenewAI</h1>
                        <span>Suraksha Insurance v2.0</span>
                    </div>
                </div>

                {Object.entries(sections).map(([section, items]) => (
                    <div className="nav-section" key={section}>
                        <div className="nav-section-title">{section}</div>
                        {items.map(item => (
                            <div
                                key={item.id}
                                className={`nav-item ${activePage === item.id ? 'active' : ''}`}
                                onClick={() => setActivePage(item.id)}
                            >
                                <span className="nav-icon">{item.icon}</span>
                                <span>{item.label}</span>
                            </div>
                        ))}
                    </div>
                ))}

                <div style={{ marginTop: 'auto', padding: '12px', borderTop: '1px solid var(--border)' }}>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                        WebSocket Streaming
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--accent-emerald)', marginTop: '4px' }}>
                        ● Real-time enabled
                    </div>
                </div>
            </nav>

            {/* Main Content */}
            <main className="main-content">
                {activePage === 'overview' && <Overview />}
                {activePage === 'pipeline' && <PipelineView />}
                {activePage === 'traces' && <TraceDashboard />}
                {activePage === 'journey' && <JourneyRunner />}
                {activePage === 'prompts' && <PromptManager />}
                {activePage === 'audit' && <AuditLogView />}
            </main>
            
            {/* Global floating components */}
            <ChatWidget />
        </div>
    )
}

export default App
