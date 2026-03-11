/*
static/script.js
Vanilla JS Frontend Logic — Suraksha Life Insurance PROJECT RenewAI v2.0
*/

let currentSection = 'dashboard';
let currentJourneyTab = 'A';

// ── Section Switching ─────────────────────────────────────────────────────────

function showSection(sectionId, element) {
    document.querySelectorAll('.page-section').forEach(s => s.classList.remove('active'));
    document.getElementById(sectionId).classList.add('active');
    
    document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
    element.classList.add('active');
    
    currentSection = sectionId;
    
    // Update header
    const titles = {
        'dashboard': ['Dashboard Overview', 'Suraksha Life Insurance — Policy Renewal Transformation'],
        'journeys': ['Run Journeys', 'Simulate AI Outbound Scenarios'],
        'pipeline': ['Policyholder Pipeline', 'Renewal Pool (CRM Demo)'],
        'scorecard': ['Success Metrics Scorecard', 'FY25 Baseline vs FY26 Target'],
        'critique': ['Critique Agent Quality', 'Layer 3.5 — 9-Point Quality Gate'],
        'human-queue': ['Human Queue Manager', 'Escalations and Specialist Handling'],
        'financial': ['Financial Summary', 'NPV, ROI, and OPEX Reductions'],
        'audit': ['Audit Log', 'IRDAI Compliance & Observability'],
    };
    
    document.getElementById('page-title').textContent = titles[sectionId][0];
    document.getElementById('page-subtitle').textContent = titles[sectionId][1];
    
    // Auto-fetch data for specific sections
    refreshData(sectionId);
}

function switchJourneyTab(tab, element) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    element.classList.add('active');
    currentJourneyTab = tab;
    
    // Clear chat simulation
    const chatBox = document.getElementById('chat-box');
    chatBox.innerHTML = '';
    document.getElementById('journey-simulation').style.display = 'none';
    document.getElementById('critique-details').innerHTML = '';
    
    // Description text
    const text = {
        'A': 'Rajesh Kumar (WhatsApp/EMI) — Term Policy. Premium ₹24,000. Evening available.',
        'B': 'Meenakshi Iyer (Bereavement) — Senior Citizen. Endowment. Critical Distress Scenario.',
        'C': 'Vikram Singh (ULIP/Email) — Tech-Savvy. Premium ₹85,000. Fund Performance Dashboard.',
    };
    document.getElementById('journey-subtitle').textContent = text[tab];
}

// ── Data Fetching ─────────────────────────────────────────────────────────────

async function refreshData(section) {
    if (section === 'dashboard') fetchDashboardStats();
    if (section === 'pipeline') fetchPipeline();
    if (section === 'scorecard') fetchScorecard();
    if (section === 'critique') fetchCritiqueSummary();
    if (section === 'human-queue') fetchHumanQueue();
    if (section === 'audit') fetchAuditLog();
}

async function fetchDashboardStats() {
    try {
        const res = await fetch('/api/dashboard/stats');
        const data = await res.json();
        
        const grid = document.getElementById('main-stats-grid');
        if (!grid) return;
        
        grid.innerHTML = `
            <div class="glass-card fade-in">
                <p class="stat-label">Main Persistency</p>
                <p class="stat-value">${(data.financial?.persistency_before || '71%')}</p>
                <p class="stat-delta delta-up">Target: ${data.financial?.persistency_target || '88%'}</p>
            </div>
            <div class="glass-card fade-in" style="animation-delay: 0.1s;">
                <p class="stat-label">Pending Policies</p>
                <p class="stat-value">${data.pipeline?.pending || '0'}</p>
                <p class="stat-label">Due 30 Days: ${data.pipeline?.due_30_days || '0'}</p>
            </div>
            <div class="glass-card fade-in" style="animation-delay: 0.2s;">
                <p class="stat-label">Human Queue</p>
                <p class="stat-value">${data.pipeline?.distressed || '0'}</p>
                <p class="stat-delta delta-down">Escalation Rate: 10%</p>
            </div>
            <div class="glass-card fade-in" style="animation-delay: 0.3s;">
                <p class="stat-label">3-Year NPV</p>
                <p class="stat-value">₹89.2 Cr</p>
                <p class="stat-delta delta-up">ROI: 8 Months</p>
            </div>
        `;
    } catch (err) {
        console.error("Failed to fetch dashboard stats:", err);
    }
}

async function fetchPipeline() {
    try {
        const res = await fetch('/api/pipeline');
        const data = await res.json();
        const body = document.getElementById('pipeline-body');
        if (!body || !Array.isArray(data)) return;
        body.innerHTML = '';
        data.forEach(ph => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${ph.name || ''}</td>
                <td>${ph.policy_number || ''}</td>
                <td>${ph.policy_type || ''}</td>
                <td>${(ph.premium || 0).toLocaleString('en-IN')}</td>
                <td>${ph.renewal_due_date || ''}</td>
                <td><span class="badge ${ph.lapse_risk === 'High' ? 'badge-red' : (ph.lapse_risk === 'Low' ? 'badge-green' : 'badge-gold')}">${ph.lapse_risk || 'Low'}</span></td>
                <td><span class="badge ${ph.last_payment_status === 'Paid' ? 'badge-green' : 'badge-blue'}">${ph.last_payment_status || 'Pending'}</span></td>
            `;
            body.appendChild(row);
        });
    } catch (err) {
        console.error("Failed to fetch pipeline:", err);
    }
}

async function fetchScorecard() {
    try {
        const res = await fetch('/api/dashboard/stats');
        const data = await res.json();
        const scorecard = data.scorecard;
        const container = document.getElementById('scorecard-container');
        if (!container || !Array.isArray(scorecard)) return;
        container.innerHTML = '<h3>Scorecard — FY25 Baseline vs FY26 Target</h3><br>';
        
        scorecard.forEach((s, idx) => {
            const row = document.createElement('div');
            row.className = 'score-row fade-in';
            row.style.animationDelay = (idx * 0.05) + 's';
            
            let val = s.current || '0%';
            let perc = parseInt(val.replace('%','')) || 0;
            if (s.metric && s.metric.includes('Cost')) perc = (45 / (parseInt(val.replace('₹','')) || 45)) * 100 || 10;
            
            row.innerHTML = `
                <div class="score-meta">
                    <span><b>${s.metric || ''}</b></span>
                    <span>Base: ${s.baseline || ''} | Target: ${s.target || ''} | <b>Current: ${s.current || ''}</b></span>
                </div>
                <div class="progress-track">
                    <div class="progress-bar ${s.status === '🟢' ? 'target-met' : ''}" style="width: ${perc}%"></div>
                </div>
            `;
            container.appendChild(row);
        });
    } catch (err) {
        console.error("Failed to fetch scorecard:", err);
    }
}

async function fetchCritiqueSummary() {
    try {
        const res = await fetch('/api/critique/summary');
        const data = await res.json();
        const grid = document.getElementById('critique-stats');
        if (!grid) return;
        grid.innerHTML = `
            <div class="glass-card fade-in">
                <p class="stat-label">Total Evaluated</p>
                <p class="stat-value">${data.total_evaluated || 0}</p>
            </div>
            <div class="glass-card fade-in">
                <p class="stat-label">Pass Rate</p>
                <p class="stat-value" style="color:var(--accent-green)">${data.pass_rate || '0%'}</p>
            </div>
            <div class="glass-card fade-in">
                <p class="stat-label">Block Rate</p>
                <p class="stat-value" style="color:var(--accent-red)">${data.block_rate || '0%'}</p>
            </div>
            <div class="glass-card fade-in">
                <p class="stat-label">Total Cost Saved</p>
                <p class="stat-value">₹14.2 Cr</p>
            </div>
        `;
    } catch (err) {
        console.error("Failed to fetch critique summary:", err);
    }
}

async function fetchHumanQueue() {
    try {
        const res = await fetch('/api/human_queue');
        const data = await res.json();
        const container = document.getElementById('queue-items-container');
        if (!container) return;
        container.innerHTML = '';
        
        if (!data.items || data.items.length === 0) {
            container.innerHTML = '<p class="stat-label">No escalated cases. Run Journey B to see an escalation.</p>';
            return;
        }
        
        data.items.forEach(item => {
            const card = document.createElement('div');
            card.className = 'glass-card fade-in';
            card.style.marginBottom = '1.5rem';
            card.innerHTML = `
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
                    <h4 style="color:var(--accent-red)">Case: ${item.case_id || 'N/A'} — ${item.customer_name || 'Anonymous'}</h4>
                    <span class="badge badge-red">${item.priority || 'Medium'}</span>
                </div>
                <p style="margin-bottom:10px;"><b>Reason:</b> ${item.escalation_reason || 'Manual escalation'}</p>
                <p style="margin-bottom:10px; font-size: 0.9rem;"><b>Specialist:</b> ${item.specialist_type || 'Agent'} | <b>SLA:</b> ${item.sla_hours || '24'}h</p>
                <div style="background:rgba(0,0,0,0.1); padding:10px; border-radius:8px; font-size:0.85rem; color:var(--text-secondary);">
                    ${item.recommended_approach || 'Review customer history and follow up.'}
                </div>
            `;
            container.appendChild(card);
        });
    } catch (err) {
        console.error("Failed to fetch human queue:", err);
    }
}

async function fetchAuditLog() {
    try {
        const res = await fetch('/api/observability/audit_log');
        const data = await res.json();
        const body = document.getElementById('audit-body');
        if (!body || !data.irdai || !Array.isArray(data.irdai)) return;
        body.innerHTML = '';
        data.irdai.forEach(log => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${(log.timestamp || '').slice(11, 19)}</td>
                <td>${log.policy_id || ''}</td>
                <td>${log.event_type || ''}</td>
                <td>${log.action || ''}</td>
                <td><span class="badge badge-green">COMPLIANT</span></td>
            `;
            body.appendChild(row);
        });
    } catch (err) {
        console.error("Failed to fetch audit log:", err);
    }
}

// ── JOURNEY TRIGGER ──────────────────────────────────────────────────────────

async function triggerJourney() {
    const policyMap = { 'A': 'POL-001', 'B': 'POL-002', 'C': 'POL-003' };
    const polId = policyMap[currentJourneyTab];
    
    document.getElementById('journey-simulation').style.display = 'block';
    const chatBox = document.getElementById('chat-box');
    chatBox.innerHTML = '<p class="stat-label">Orchestrating AI agents...</p>';
    
    // API Call
    const res = await fetch('/api/journey/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ policy_id: polId })
    });
    const data = await res.json();
    
    chatBox.innerHTML = '';
    
    // 1. Show AI Message
    addChatTurn('ai', `${data.decision.recommended_agent} — ${data.decision.channel}`, data.message);
    
    // 2. Critique Result
    const critiqueDiv = document.getElementById('critique-details');
    critiqueDiv.innerHTML = `
        <div class="glass-card" style="box-shadow:none; border-color: ${data.critique.verdict === 'PASS' ? 'var(--accent-green)' : 'var(--accent-red)'}">
            <h5 style="margin-bottom:10px;">Critique Agent Result: ${data.critique.verdict}</h5>
            <p style="font-size:0.85rem; color:var(--text-secondary);">Accuracy Score: ${(data.critique.overall_score * 100).toFixed(0)}% (Target: 87%)</p>
        </div>
    `;
    
    // 3. Simulate Customer Interaction
    if (currentJourneyTab === 'A') {
        // Expanded Simulation sequence for Rajesh
        setTimeout(async () => {
            // 1. HELP Request
            addChatTurn('user', 'Rajesh', "help");
            const resHelp = await fetch('/api/journey/reply', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ policy_id: polId, message: "help" })
            });
            const dataHelp = await resHelp.json();
            addChatTurn('ai', 'WhatsAppAgent', dataHelp.reply);

            // 2. POLICY DETAILS Request
            setTimeout(async () => {
                addChatTurn('user', 'Rajesh', "Show me my policy details");
                const resPol = await fetch('/api/journey/reply', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ policy_id: polId, message: "Show me my policy details" })
                });
                const dataPol = await resPol.json();
                addChatTurn('ai', 'WhatsAppAgent', dataPol.reply);

                // 3. CALL Slot Acknowledgment
                setTimeout(async () => {
                    addChatTurn('user', 'Rajesh', "I want a callback. Evening works.");
                    const resCall = await fetch('/api/journey/reply', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ policy_id: polId, message: "I want a callback. Evening works." })
                    });
                    const dataCall = await resCall.json();
                    addChatTurn('ai', 'WhatsAppAgent', dataCall.reply);
                }, 4000);
            }, 4000);
        }, 2000);
    } 
    else if (currentJourneyTab === 'B') {
        // Meenakshi bereavement
        const msg = "My husband passed away last month. I don't know what to do with this policy.";
        setTimeout(async () => {
            addChatTurn('user', 'Meenakshi', msg);
            const replyRes = await fetch('/api/journey/reply', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ policy_id: polId, message: msg })
            });
            const replyData = await replyRes.json();
            setTimeout(() => {
                addChatTurn('ai', 'WhatsAppAgent', replyData.reply);
                if (replyData.escalated) {
                    stMessage('blue', `🚨 EMERGENCY ESCALATION DETECTED: routing Case ${replyData.case_id} to Senior RM Priya Sharma. SLA: 2h.`);
                }
            }, 1000);
        }, 1500);
    }
}

function addChatTurn(role, label, text) {
    const chatBox = document.getElementById('chat-box');
    const div = document.createElement('div');
    div.className = `chat-bubble bubble-${role} fade-in`;
    div.innerHTML = `
        <p class="chat-label">${label}</p>
        <p>${text}</p>
    `;
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function stMessage(type, text) {
    const chatBox = document.getElementById('chat-box');
    const p = document.createElement('p');
    p.style.padding = '1rem';
    p.style.fontSize = '0.9rem';
    p.style.color = type === 'blue' ? 'var(--accent-blue)' : 'var(--accent-gold)';
    p.style.fontWeight = '700';
    p.textContent = text;
    chatBox.appendChild(p);
}

// Initial Load
document.addEventListener('DOMContentLoaded', () => {
    refreshData('dashboard');
});
