// Renders the three specialist analyses + team allocation + detected conflicts.
// This is "debate" as detect → critique → resolve, not parallel generation.

function List({ items, ordered }) {
  if (!items || items.length === 0) return <span className="muted">—</span>
  const Tag = ordered ? 'ol' : 'ul'
  return <Tag className="mini-list">{items.map((x, i) => <li key={i}>{x}</li>)}</Tag>
}

function Chips({ items }) {
  if (!items || items.length === 0) return null
  return <div className="chips">{items.map((x, i) => <span className="chip" key={i}>{x}</span>)}</div>
}

function Score({ value }) {
  const v = Math.max(0, Math.min(100, Number(value || 0)))
  const color = v >= 75 ? 'var(--green)' : v >= 50 ? 'var(--amber)' : 'var(--red)'
  return (
    <div className="score-badge" style={{ borderColor: color, color }}>
      <b>{v}</b><span>/100</span>
    </div>
  )
}

function AgentColumn({ kind, title, right, children, flags }) {
  return (
    <div className="agent-col">
      <div className="agent-col__head">
        <span className={kind}>{title}</span>
        {right}
        {flags && flags.length > 0 && <span className="sev sev--medium">{flags.length} flag(s)</span>}
      </div>
      <div className="agent-col__body">{children}</div>
    </div>
  )
}

function StackTable({ items }) {
  if (!items || items.length === 0) return <span className="muted">—</span>
  return (
    <table className="mini-table">
      <thead><tr><th>Technology</th><th>Purpose</th></tr></thead>
      <tbody>{items.map((s, i) => <tr key={i}><td>{s.name}</td><td>{s.purpose || '—'}</td></tr>)}</tbody>
    </table>
  )
}

function ScheduleTable({ items }) {
  if (!items || items.length === 0) return <span className="muted">—</span>
  return (
    <table className="mini-table">
      <thead><tr><th>Task</th><th>Tech</th><th>Duration</th><th>Depends on</th><th>Expected output</th></tr></thead>
      <tbody>
        {items.map((s, i) => (
          <tr key={i}>
            <td>{s.task}</td><td>{s.technology || '—'}</td><td>{s.duration || '—'}</td>
            <td>{s.dependency || '—'}</td><td>{s.expected_output || '—'}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

export default function DebatePanel({ debate }) {
  if (!debate) return null
  const tech = debate.tech_analysis || {}
  const time = debate.timeline_analysis || {}
  const allocation = debate.team_allocation || []
  const conflicts = debate.conflicts || []
  const directives = debate.revision_directives || []

  const stack = tech.stack_details?.length
    ? tech.stack_details
    : (tech.recommended_stack || []).map((n) => ({ name: n, purpose: '' }))

  return (
    <div>
      <div className="debate-grid debate-grid--2">
        <AgentColumn kind="tech" title="Tech Stack Architect" right={<Score value={tech.feasibility_score} />} flags={tech.cross_domain_flags}>
          <div className="kv"><span className="k">Complexity</span>{tech.complexity || '—'}</div>
          <div className="kv"><span className="k">Recommended stack</span><StackTable items={stack} /></div>
          <div className="kv"><span className="k">Architecture</span><List items={tech.architecture} /></div>
          <div className="kv"><span className="k">Technical risks</span><List items={tech.technical_risks} /></div>
          <div className="kv"><span className="k">Critique</span><List items={tech.critique} /></div>
        </AgentColumn>

        <AgentColumn kind="time" title="Timeline Scheduler" flags={time.cross_domain_flags}>
          <div className="kv"><span className="k">Fits time limit?</span>{time.feasible ? 'Yes' : 'At risk'}</div>
          <div className="kv"><span className="k">Estimated vs available</span>
            {(time.estimated_hours || 0)}h estimated / {(time.available_hours || 0)}h available</div>
          {time.time_risk && <div className="kv"><span className="k">Time risk</span>{time.time_risk}</div>}
          <div className="kv"><span className="k">Build schedule</span><ScheduleTable items={time.schedule} /></div>
          <div className="kv"><span className="k">Critical dependencies</span><List items={time.critical_dependencies} /></div>
          <div className="kv"><span className="k">Critique</span><List items={time.critique} /></div>
        </AgentColumn>
      </div>

      <hr className="divider" />
      <h3 className="panel__title" style={{ fontSize: 14 }}>Team task allocation</h3>
      {allocation.length === 0 ? (
        <p className="muted">No allocation yet.</p>
      ) : (
        <table className="mini-table">
          <thead><tr><th>Member</th><th>Skills</th><th>Responsibilities</th><th>Technologies</th><th>Time</th></tr></thead>
          <tbody>
            {allocation.map((a, i) => (
              <tr key={i}>
                <td><b>{a.name}</b>{a.role ? <div className="muted" style={{ fontSize: 12 }}>{a.role}</div> : null}</td>
                <td><Chips items={a.skills} /></td>
                <td><List items={a.responsibilities} /></td>
                <td><Chips items={a.technologies} /></td>
                <td>{a.time_allocation || '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <hr className="divider" />
      <h3 className="panel__title" style={{ fontSize: 14 }}>
        Conflicts detected <span className="idx">{conflicts.length}</span>
      </h3>
      {conflicts.length === 0 ? (
        <p className="muted">No cross-domain conflicts detected this round — the specialists converged.</p>
      ) : (
        <div className="conflicts">
          {conflicts.map((c, i) => (
            <div className={`conflict ${c.resolved ? 'conflict--resolved' : ''}`} key={i}>
              <div className="conflict__top">
                <span className="conflict__type">{c.type || 'conflict'}</span>
                <span className={`sev sev--${c.severity || 'medium'}`}>{c.severity || 'medium'}</span>
                {c.resolved && <span className="sev" style={{ color: 'var(--green)' }}>resolved</span>}
              </div>
              <div className="conflict__desc">{c.description}</div>
              {c.resolution && <div className="conflict__res">→ {c.resolution}</div>}
            </div>
          ))}
        </div>
      )}

      {directives.length > 0 && (
        <>
          <hr className="divider" />
          <div className="kv"><span className="k">Latest revision directives</span></div>
          <div className="conflicts">
            {directives.map((d, i) => (
              <div className="conflict conflict--resolved" key={i}>
                <div className="conflict__top"><span className="conflict__type">{d.agent}</span></div>
                <div className="conflict__desc">{d.change}</div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
