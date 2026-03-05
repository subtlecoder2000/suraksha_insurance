"""
static/script.js
Vanilla JS Frontend Logic — Suraksha Life Insurance PROJECT RenewAI v2.0
"""

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
    const res = await fetch('/api/dashboard/stats');
    const data = await res.json();
    
    const grid = document.getElementById('main-stats-grid');
    grid.innerHTML = `
        <div class="glass-card fade-in">
            <p class="stat-label">Main Persistency</p>
            <p class="stat-value">${(data.financial.persistency_before)}</p>
            <p class="stat-delta delta-up">Target: ${data.financial.persistency_target}</p>
        </div>
        <div class="glass-card fade-in" style="animation-delay: 0.1s;">
            <p class="stat-label">Pending Policies</p>
            <p class="stat-value">${data.pipeline.pending}</p>
            <p class="stat-label">Due 30 Days: ${data.pipeline.due_30_days}</p>
        </div>
        <div class="glass-card fade-in" style="animation-delay: 0.2s;">
            <p class="stat-label">Human Queue</p>
            <p class="stat-value">${data.pipeline.distressed}</p>
            <p class="stat-delta delta-down">Escalation Rate: 10%</p>
        </div>
        <div class="glass-card fade-in" style="animation-delay: 0.3s;">
            <p class="stat-label">3-Year NPV</p>
            <p class="stat-value">₹89.2 Cr</p>
            <p class="stat-delta delta-up">ROI: 8 Months</p>
        </div>
    `;
}

async function fetchPipeline() {
    const res = await fetch('/api/pipeline');
    const data = await res.json();
    const body = document.getElementById('pipeline-body');
    body.innerHTML = '';
    data.forEach(ph => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${ph.name}</td>
            <td>${ph.policy_number}</td>
            <td>${ph.policy_type}</td>
            <td>${ph.premium.toLocaleString('en-IN')}</td>
            <td>${ph.renewal_due_date}</td>
            <td><span class="badge ${ph.lapse_risk === 'High' ? 'badge-red' : (ph.lapse_risk === 'Low' ? 'badge-green' : 'badge-gold')}">${ph.lapse_risk}</span></td>
            <td><span class="badge ${ph.last_payment_status === 'Paid' ? 'badge-green' : 'badge-blue'}">${ph.last_payment_status}</span></td>
        `;
        body.appendChild(row);
    });
}

async function fetchScorecard() {
    const res = await fetch('/api/dashboard/stats');
    const data = await res.json();
    const scorecard = data.scorecard;
    const container = document.getElementById('scorecard-container');
    container.innerHTML = '<h3>Scorecard — FY25 Baseline vs FY26 Target</h3><br>';
    
    scorecard.forEach((s, idx) => {
        const row = document.createElement('div');
        row.className = 'score-row fade-in';
        row.style.animationDelay = (idx * 0.05) + 's';
        
        let perc = parseInt(s.current.replace('%','')) || 0;
        if (s.metric.includes('Cost')) perc = (45 / parseInt(s.current.replace('₹',''))) * 100 || 10;
        
        row.innerHTML = `
            <div class="score-meta">
                <span><b>${s.metric}</b></span>
                <span>Base: ${s.baseline} | Target: ${s.target} | <b>Current: ${s.current}</b></span>
            </div>
            <div class="progress-track">
                <div class="progress-bar ${s.status === '🟢' ? 'target-met' : ''}" style="width: ${perc}%"></div>
            </div>
        `;
        container.appendChild(row);
    });
}

async function fetchCritiqueSummary() {
    const res = await fetch('/api/critique/summary');
    const data = await res.json();
    const grid = document.getElementById('critique-stats');
    grid.innerHTML = `
        <div class="glass-card fade-in">
            <p class="stat-label">Total Evaluated</p>
            <p class="stat-value">${data.total_evaluated}</p>
        </div>
        <div class="glass-card fade-in">
            <p class="stat-label">Pass Rate</p>
            <p class="stat-value" style="color:var(--accent-green)">${data.pass_rate}</p>
        </div>
        <div class="glass-card fade-in">
            <p class="stat-label">Block Rate</p>
            <p class="stat-value" style="color:var(--accent-red)">${data.block_rate}</p>
        </div>
        <div class="glass-card fade-in">
            <p class="stat-label">Total Cost Saved</p>
            <p class="stat-value">₹14.2 Cr</p>
        </div>
    `;
}

async function fetchHumanQueue() {
    const res = await fetch('/api/human_queue');
    const data = await res.json();
    const container = document.getElementById('queue-items-container');
    container.innerHTML = '';
    
    if (data.items.length === 0) {
        container.innerHTML = '<p class="stat-label">No escalated cases. Run Journey B to see an escalation.</p>';
        return;
    }
    
    data.items.forEach(item => {
        const card = document.createElement('div');
        card.className = 'glass-card fade-in';
        card.style.marginBottom = '1.5rem';
        card.innerHTML = `
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
                <h4 style="color:var(--accent-red)">Case: ${item.case_id} — ${item.customer_name}</h4>
                <span class="badge badge-red">${item.priority}</span>
            </div>
            <p style="margin-bottom:10px;"><b>Reason:</b> ${item.escalation_reason}</p>
            <p style="margin-bottom:10px; font-size: 0.9rem;"><b>Specialist:</b> ${item.specialist_type} | <b>SLA:</b> ${item.sla_hours}h</p>
            <div style="background:rgba(0,0,0,0.1); padding:10px; border-radius:8px; font-size:0.85rem; color:var(--text-secondary);">
                ${item.recommended_approach}
            </div>
        `;
        container.appendChild(card);
    });
}

async function fetchAuditLog() {
    const res = await fetch('/api/observability/audit_log');
    const data = await res.json();
    const body = document.getElementById('audit-body');
    body.innerHTML = '';
    data.irdai.forEach(log => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${log.timestamp.slice(11, 19)}</td>
            <td>${log.policy_id}</td>
            <td>${log.event_type}</td>
            <td>${log.action}</td>
            <td><span class="badge badge-green">COMPLIANT</span></td>
        `;
        body.appendChild(row);
    });
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
        // Rajesh asks about EMI
        setTimeout(async () => {
            addChatTurn('user', 'Rajesh', "Can I pay in two instalments?");
            const replyRes = await fetch('/api/journey/reply', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ policy_id: polId, message: "Can I pay in two instalments?" })
            });
            const replyData = await replyRes.json();
            setTimeout(() => addChatTurn('ai', 'WhatsAppAgent', replyData.reply), 1000);
        }, 1500);
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
