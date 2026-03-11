import { useState, useRef, useEffect } from 'react'
import { getPipeline, handleCustomerReply } from '../api'

export default function ChatWidget() {
  const [isOpen, setIsOpen] = useState(false)
  const [policies, setPolicies] = useState([])
  const [policyId, setPolicyId] = useState('POL-001')
  const [messages, setMessages] = useState([
    { role: 'system', text: 'Select a policyholder and send a message to start testing the agent.' }
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
    if (isOpen) {
      scrollToBottom()
    }
  }, [messages, isOpen])

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
        text: `Error interacting: ${error.message}` 
      }])
    } finally {
      setSending(false)
    }
  }

  function clearChat() {
    setMessages([{ role: 'system', text: 'Chat cleared. Start a new conversation.' }])
  }

  return (
    <>
      <div 
        className={`chat-widget-button ${isOpen ? 'open' : ''}`} 
        onClick={() => setIsOpen(!isOpen)}
      >
        💬
      </div>

      <div className={`chat-widget-window ${isOpen ? 'open' : ''}`}>
        {/* Header */}
        <div className="chat-widget-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ width: '28px', height: '28px', borderRadius: '50%', background: 'var(--gradient-success)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '14px' }}>
              🤖
            </div>
            <div>
              <div style={{ fontWeight: '600', fontSize: '14px', color: 'var(--text-primary)' }}>RenewAI Agent</div>
              <div style={{ fontSize: '11px', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <span className="ws-dot" style={{ width: '6px', height: '6px' }}></span> Online
              </div>
            </div>
          </div>
          <button className="chat-widget-close" onClick={() => setIsOpen(false)}>×</button>
        </div>

        {/* Configuration (Only show briefly or collapsible) */}
        <div className="chat-widget-config">
          <select
            className="select"
            value={policyId}
            onChange={e => {
              setPolicyId(e.target.value);
              clearChat();
            }}
            style={{ width: '100%', fontSize: '12px', padding: '6px 10px' }}
          >
            {policies.length > 0 ? (
              policies.map(p => (
                <option key={p.policy_id} value={p.policy_id}>
                  {p.policy_id} — {p.name}
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

        {/* Messages */}
        <div className="chat-widget-messages">
          {messages.map((msg, idx) => (
            <div key={idx} className={`chat-bubble-wrapper ${msg.role}`}>
              {msg.role === 'system' ? (
                <div className="chat-system-msg">{msg.text}</div>
              ) : (
                <div className={`chat-bubble ${msg.role}`}>
                  <div style={{ whiteSpace: 'pre-wrap' }}>{msg.text}</div>
                  {msg.escalated && (
                    <div className="chat-escalation-alert">
                      ⚠️ Escalated to Human (Case: {msg.caseId})
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
        <div className="chat-widget-input-area">
          <form onSubmit={sendMessage} style={{ display: 'flex', gap: '8px' }}>
            <input 
              type="text" 
              value={inputValue}
              onChange={e => setInputValue(e.target.value)}
              placeholder="Message..."
              disabled={sending}
              style={{
                flex: 1,
                background: 'var(--bg-card)',
                border: '1px solid var(--border)',
                color: 'var(--text-primary)',
                padding: '8px 12px',
                borderRadius: 'var(--radius-xl)',
                fontSize: '13px',
                outline: 'none',
              }}
            />
            <button 
              type="submit" 
              disabled={!inputValue.trim() || sending}
              className="btn btn-primary"
              style={{ borderRadius: '50%', width: '36px', height: '36px', padding: '0', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
            >
              ➤
            </button>
          </form>
        </div>
      </div>
    </>
  )
}
