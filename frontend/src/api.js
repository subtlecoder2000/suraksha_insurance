/**
 * API utility functions
 */
const API_BASE = '/api';

async function request(url, options = {}) {
    const res = await fetch(`${API_BASE}${url}`, {
        headers: { 'Content-Type': 'application/json', ...options.headers },
        ...options,
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || 'Request failed');
    }
    return res.json();
}

// Journey
export const runJourney = (policyId) =>
    request('/v2/journey/run', { method: 'POST', body: JSON.stringify({ policy_id: policyId }) });

export const handleCustomerReply = (policyId, message) =>
    request('/journey/reply', { method: 'POST', body: JSON.stringify({ policy_id: policyId, message }) });

export const getPipeline = () => request('/pipeline');
export const getDashboardStats = () => request('/dashboard/stats');

// Traces
export const getTraces = (limit = 50) => request(`/traces?limit=${limit}`);
export const getTrace = (traceId) => request(`/traces/${traceId}`);
export const getTraceStats = () => request('/trace-stats');

// Prompts
export const getAllPrompts = () => request('/prompts');
export const getPrompt = (agentName) => request(`/prompts/${agentName}`);
export const updatePrompt = (agentName, systemPrompt, description) =>
    request('/prompts', { method: 'PUT', body: JSON.stringify({ agent_name: agentName, system_prompt: systemPrompt, description }) });
export const rollbackPrompt = (agentName, version) =>
    request('/prompts/rollback', { method: 'POST', body: JSON.stringify({ agent_name: agentName, target_version: version }) });

// Feedback & Improvement
export const submitFeedback = (data) =>
    request('/feedback', { method: 'POST', body: JSON.stringify(data) });
export const getPendingFeedback = (agentName) =>
    request(`/feedback/pending${agentName ? `?agent_name=${agentName}` : ''}`);
export const triggerImprovement = (agentName = null) =>
    request('/prompts/improve', { method: 'POST', body: JSON.stringify({ agent_name: agentName }) });
export const getPromptDashboard = () => request('/prompts/dashboard');

// Critique
export const getCritiqueSummary = () => request('/critique/summary');

// Observability
export const getAuditLog = () => request('/observability/audit_log');

// Human Queue
export const getHumanQueue = () => request('/human_queue');
