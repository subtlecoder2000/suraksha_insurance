import { useState, useEffect } from 'react'
import { getAuditLog } from '../api'

export default function AuditLogView() {
  const [logs, setLogs] = useState([])
  const [stats, setStats] = useState(null)
  const [filter, setFilter] = useState('all') // all, IRDAI, specific policy
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function loadData() {
      try {
        const data = await getAuditLog()
        setLogs(data.irdai || []) // or fetch a wider list if backend provides it
        setStats(data.stats)
      } catch (e) {
        console.error('Failed to load audit logs')
      } finally {
        setLoading(false)
      }
    }
    
    loadData()
  }, [])

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>🛡️ System Audit Logs</h2>
          <div className="subtitle">Track IRDAI compliance events, SLA breaches, and historical actions across all policies.</div>
        </div>
        <div className="header-actions">
          <select className="select" value={filter} onChange={e => setFilter(e.target.value)}>
            <option value="all">All Events</option>
            <option value="irdai">IRDAI Relevant Only</option>
          </select>
        </div>
      </div>

      {stats && (
        <div className="stat-grid" style={{ gridTemplateColumns: 'repeat(4, 1fr)', marginBottom: '24px' }}>
          <div className="stat-card indigo">
            <div className="stat-label">Total Events</div>
            <div className="stat-value">{stats.total_events || 0}</div>
          </div>
          <div className="stat-card rose">
            <div className="stat-label">Critical IRDAI flags</div>
            <div className="stat-value">{stats.irdai_relevant_count || 0}</div>
          </div>
        </div>
      )}

      <div className="card">
        <div className="card-header">
          <div className="card-title">Event Log</div>
        </div>
        
        {logs.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
            No audit events recorded yet.
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', textAlign: 'left', borderCollapse: 'collapse', fontSize: '12px' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border)' }}>
                  <th style={{ padding: '12px 16px', color: 'var(--text-muted)' }}>Timestamp</th>
                  <th style={{ padding: '12px 16px', color: 'var(--text-muted)' }}>Event ID</th>
                  <th style={{ padding: '12px 16px', color: 'var(--text-muted)' }}>Type</th>
                  <th style={{ padding: '12px 16px', color: 'var(--text-muted)' }}>Policy ID</th>
                  <th style={{ padding: '12px 16px', color: 'var(--text-muted)' }}>Agent</th>
                  <th style={{ padding: '12px 16px', color: 'var(--text-muted)' }}>Action</th>
                  <th style={{ padding: '12px 16px', color: 'var(--text-muted)' }}>Outcome</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log, index) => (
                  <tr key={log.id || index} style={{ borderBottom: '1px solid var(--border)' }}>
                    <td style={{ padding: '12px 16px', color: 'var(--text-muted)' }}>{log.timestamp}</td>
                    <td style={{ padding: '12px 16px', color: 'var(--accent-indigo)' }}>{log.id?.substring(0, 8)}</td>
                    <td style={{ padding: '12px 16px' }}>
                      <span className={`stream-status ${log.irdai_relevant ? 'failed' : 'completed'}`}>
                        {log.type}
                      </span>
                    </td>
                    <td style={{ padding: '12px 16px', fontWeight: 'bold' }}>{log.policy_id}</td>
                    <td style={{ padding: '12px 16px' }}>{log.agent}</td>
                    <td style={{ padding: '12px 16px' }}>{log.action}</td>
                    <td style={{ padding: '12px 16px', color: 'var(--text-muted)' }}>{log.outcome}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
