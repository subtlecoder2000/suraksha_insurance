/**
 * ChatSimulator — Interactive chat interface to test WhatsApp/SMS conversations
 * Connects to the /api/journey/reply endpoint.
 */
import { useState, useRef, useEffect } from 'react'
import { getPipeline, handleCustomerReply } from '../api'

export default function ChatSimulator() {
  const [policies, setPolicies] = useState([])
  const [policyId, setPolicyId] = useState('POL-001')
  const [messages, setMessages] = useState([
    { role: 'system', text: 'Select a policyholder and send a message to start testing the conversational agent.' }
  ])
  const [inputValue, setInputValue] = useState('')
  const [sending, setSending] = useState(false)
  const messagesEndRef = useRef(null)

  useEffect(() => {
    getPipeline()
      .then(data => setPolicies(data || []))
      .catch(() => {})
  }, [])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  async function sendMessage(e) {
    if (e) e.preventDefault()
    if (!inputValue.trim() || sending) return

    const userMessage = inputValue.trim()
    setInputValue('')
    setMessages(prev => [...prev, { role: 'user', text: userMessage }])
    setSending(true)

    try {
      const response = await handleCustomerReply(policyId, userMessage)
      
      setMessages(prev => [...prev, { 
        role: 'agent', 
        text: response.reply,
        escalated: response.escalated,
        caseId: response.case_id
      }])
    } catch (error) {
      setMessages(prev => [...prev, { 
        role: 'system', 
        text: `Error interacting with agent: ${error.message}` 
      }])
    } finally {
      setSending(false)
    }
  }

  function clearChat() {
    setMessages([{ role: 'system', text: 'Chat cleared. Start a new conversation.' }])
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>💬 Chat Simulator</h2>
          <div className="subtitle">
            Impersonate a customer to test dynamic RAG responses, objection handling, and human escalation.
          </div>
        </div>
        <div className="header-actions">
          <button className="btn btn-secondary btn-sm" onClick={clearChat}>
            🗑️ Clear Chat
          </button>
        </div>
      </div>

      <div className="two-col" style={{ gridTemplateColumns: 'minmax(300px, 380px) 1fr' }}>
        {/* Controls Panel */}
        <div>
          <div className="card" style={{ marginBottom: '24px' }}>
            <div className="card-header">
              <div className="card-title">Test Configuration</div>
            </div>
            
            <div style={{ marginBottom: '16px' }}>
              <label style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>
                Impersonating Policyholder
              </label>
              <select
                className="select"
                value={policyId}
                onChange={e => {
                  setPolicyId(e.target.value);
                  clearChat();
                }}
                style={{ width: '100%' }}
              >
                {policies.length > 0 ? (
                  policies.map(p => (
                    <option key={p.policy_id} value={p.policy_id}>
                      {p.policy_id} — {p.name} ({p.policy_type})
                    </option>
                  ))
                ) : (
                  <>
                    <option value="POL-001">POL-001 (Demo)</option>
                    <option value="POL-002">POL-002 (Demo)</option>
                  </>
                )}
              </select>
            </div>

            <div className="evidence-panel">
              <div className="evidence-title">Simulator Instructions</div>
              <div className="evidence-content" style={{ fontSize: '12px', lineHeight: '1.5' }}>
                <p style={{ marginBottom: '8px' }}>Test various scenarios:</p>
                <ul style={{ paddingLeft: '16px', color: 'var(--text-muted)' }}>
                  <li style={{ marginBottom: '4px' }}><strong>Objections:</strong> "Why did my premium increase?" or "I found a cheaper policy."</li>
                  <li style={{ marginBottom: '4px' }}><strong>Payment intents:</strong> "How do I setup autopay?" or "Can I pay in EMIs?"</li>
                  <li><strong>Distress (Escalation):</strong> "I lost my job and cannot pay this." or "I am having financial difficulties."</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        {/* Chat Interface */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 160px)', padding: '0', overflow: 'hidden' }}>
          {/* Header */}
          <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: '12px', background: 'var(--bg-card-hover)' }}>
            <div style={{ width: '36px', height: '36px', borderRadius: '50%', background: 'var(--gradient-success)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '18px' }}>
              🤖
            </div>
            <div>
              <div style={{ fontWeight: '600', fontSize: '15px', color: 'var(--text-primary)' }}>RenewAI Agent</div>
              <div style={{ fontSize: '12px', color: 'var(--accent-emerald)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <span className="ws-dot" style={{ width: '6px', height: '6px' }}></span> Online
              </div>
            </div>
          </div>

          {/* Messages */}
          <div className="chat-messages" style={{ flex: 1, overflowY: 'auto', padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {messages.map((msg, idx) => (
              <div key={idx} className={`chat-bubble-wrapper ${msg.role}`}>
                {msg.role === 'system' ? (
                  <div className="chat-system-msg">{msg.text}</div>
                ) : (
                  <div className={`chat-bubble ${msg.role}`}>
                    <div style={{ whiteSpace: 'pre-wrap' }}>{msg.text}</div>
                    {msg.escalated && (
                      <div className="chat-escalation-alert">
                        ⚠️ Escalated to Human Queue (Case: {msg.caseId})
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
            {sending && (
              <div className="chat-bubble-wrapper agent">
                <div className="chat-bubble agent typing-indicator">
                  <span></span><span></span><span></span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div style={{ padding: '16px 20px', borderTop: '1px solid var(--border)', background: 'var(--bg-card-hover)' }}>
            <form onSubmit={sendMessage} style={{ display: 'flex', gap: '12px' }}>
              <input 
                type="text" 
                value={inputValue}
                onChange={e => setInputValue(e.target.value)}
                placeholder="Type a message to the agent..."
                disabled={sending}
                style={{
                  flex: 1,
                  background: 'var(--bg-card)',
                  border: '1px solid var(--border)',
                  color: 'var(--text-primary)',
                  padding: '12px 16px',
                  borderRadius: 'var(--radius-xl)',
                  fontSize: '14px',
                  outline: 'none',
                }}
              />
              <button 
                type="submit" 
                disabled={!inputValue.trim() || sending}
                className="btn btn-primary"
                style={{ borderRadius: '50%', width: '44px', height: '44px', padding: '0', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
              >
                ➤
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  )
}
