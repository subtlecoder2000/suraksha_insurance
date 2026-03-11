import { useState, useEffect } from 'react'
import { getPipeline, getHumanQueue } from '../api'

export default function PipelineView() {
  const [pipeline, setPipeline] = useState([])
  const [queue, setQueue] = useState({ items: [], stats: {} })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function loadData() {
      try {
        const [pipeData, queueData] = await Promise.all([
          getPipeline(),
          getHumanQueue()
        ])
        setPipeline(pipeData)
        setQueue(queueData)
      } catch (e) {
        console.error('Failed to load pipeline data')
      } finally {
        setLoading(false)
      }
    }
    
    loadData()
    const int = setInterval(loadData, 15000)
    return () => clearInterval(int)
  }, [])

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>📋 Policy Pipeline & Escalations</h2>
          <div className="subtitle">Track T-45 journey initiates, policy status, and manual intervention required.</div>
        </div>
      </div>

      <div className="card" style={{ marginBottom: '24px' }}>
        <div className="card-header">
          <div className="card-title">🚨 Human Escalation Queue</div>
          <span className="stream-status failed">Requires Attention: {queue.items?.filter(i => i.status === 'open').length || 0}</span>
        </div>
        
        {queue.items?.length === 0 ? (
          <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '20px' }}>
            No pending escalations. All AI conversions are operating autonomously.
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', textAlign: 'left', borderCollapse: 'collapse', fontSize: '13px' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border)' }}>
                  <th style={{ padding: '12px 16px', color: 'var(--text-muted)' }}>Case ID</th>
                  <th style={{ padding: '12px 16px', color: 'var(--text-muted)' }}>Policy</th>
                  <th style={{ padding: '12px 16px', color: 'var(--text-muted)' }}>Reason</th>
                  <th style={{ padding: '12px 16px', color: 'var(--text-muted)' }}>Escalated To</th>
                  <th style={{ padding: '12px 16px', color: 'var(--text-muted)' }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {queue.items?.map(item => (
                  <tr key={item.case_id} style={{ borderBottom: '1px solid var(--border)' }}>
                    <td style={{ padding: '12px 16px', color: 'var(--accent-indigo)' }}>{item.case_id}</td>
                    <td style={{ padding: '12px 16px' }}>{item.policy_id}</td>
                    <td style={{ padding: '12px 16px', color: 'var(--accent-rose)' }}>{item.reason}</td>
                    <td style={{ padding: '12px 16px', textTransform: 'capitalize' }}>{item.specialist_type}</td>
                    <td style={{ padding: '12px 16px' }}>
                      <span className={`stream-status ${item.status === 'open' ? 'failed' : 'completed'}`}>
                        {item.status.toUpperCase()}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="card">
        <div className="card-header">
          <div className="card-title">🔍 Active Policies Pipeline (T-45 Detection)</div>
        </div>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', textAlign: 'left', borderCollapse: 'collapse', fontSize: '13px' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border)' }}>
                <th style={{ padding: '12px 16px', color: 'var(--text-muted)' }}>Policy</th>
                <th style={{ padding: '12px 16px', color: 'var(--text-muted)' }}>Customer</th>
                <th style={{ padding: '12px 16px', color: 'var(--text-muted)' }}>Renewal Due</th>
                <th style={{ padding: '12px 16px', color: 'var(--text-muted)' }}>Status / Blockers</th>
                <th style={{ padding: '12px 16px', color: 'var(--text-muted)' }}>Risk Level</th>
              </tr>
            </thead>
            <tbody>
              {pipeline.map(policy => (
                <tr key={policy.policy_id} style={{ borderBottom: '1px solid var(--border)' }}>
                  <td style={{ padding: '12px 16px', color: 'var(--text-primary)', fontWeight: '600' }}>{policy.policy_id}</td>
                  <td style={{ padding: '12px 16px' }}>{policy.name}</td>
                  <td style={{ padding: '12px 16px' }}>{policy.renewal_due_date}</td>
                  <td style={{ padding: '12px 16px' }}>
                    {policy.distress ? (
                      <span className="stream-status failed">Stuck: Financial Distress</span>
                    ) : policy.last_payment_status === 'overdue' ? (
                      <span className="stream-status running">Overdue Payment</span>
                    ) : (
                      <span className="stream-status completed">On Track</span>
                    )}
                  </td>
                  <td style={{ padding: '12px 16px' }}>
                    {policy.lapse_risk === 'high' ? '🔴 High' : policy.lapse_risk === 'medium' ? '🟡 Medium' : '🟢 Low'}
                  </td>
                </tr>
              ))}
              {pipeline.length === 0 && !loading && (
                <tr>
                  <td colSpan="5" style={{ textAlign: 'center', padding: '24px', color: 'var(--text-muted)' }}>
                    No active policies in the pipeline.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
