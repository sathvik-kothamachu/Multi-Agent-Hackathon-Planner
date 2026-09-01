// Renders the three specialist analyses side-by-side + detected conflicts.
// This is "debate" as detect → critique → resolve, not parallel generation.

function List({ items }) {
  if (!items || items.length === 0) return <span className="muted">—</span>
  return (
    <ul className="mini-list">
      {items.map((x, i) => <li key={i}>{x}</li>)}
    </ul>
  )
}

function Chips({ items }) {
  if (!items || items.length === 0) return null
  return <div className="chips">{items.map((x, i) => <span className="chip" key={i}>{x}</span>)}</div>
}

function AgentColumn({ kind, title, children, flags }) {
  return (
    <div className="agent-col">
      <div className="agent-col__head">
        <span className={kind}>{title}</span>
        {flags && flags.length > 0 && <span className="sev sev--medium">{flags.length} flag(s)</span>}
      </div>
      <div className="agent-col__body">{children}</div>
    </div>
  )
}

export default function DebatePanel({ debate }) {
  if (!debate) return null
  const tech = debate.tech_analysis || {}
  const time = debate.timeline_analysis || {}
  const pitch = debate.pitch_analysis || {}
  const conflicts = debate.conflicts || []
  const directives = debate.revision_directives || []

  return (
    <div>
      <div className="debate-grid">
        <AgentColumn kind="tech" title="Tech Stack Architect" flags={tech.cross_domain_flags}>
          <div className="kv"><span className="k">Feasibility / Complexity</span>{tech.feasibility || '—'} / {tech.complexity || '—'}</div>
          <div className="kv"><span className="k">Recommended stack</span><Chips items={tech.recommended_stack} /></div>
          <div className="kv"><span className="k">Technical risks</span><List items={tech.technical_risks} /></div>
          <div className="kv"><span className="k">Critique</span><List items={tech.critique} /></div>
        </AgentColumn>

        <AgentColumn kind="time" title="Timeline Scheduler" flags={time.cross_domain_flags}>
          <div className="kv"><span className="k">Fits time limit?</span>{time.feasible ? 'Yes' : 'At risk'}</div>
          <div className="kv"><span className="k">Milestones</span>
            <Chips items={(time.milestones || []).map((m) => (typeof m === 'string' ? m : m.name))} /></div>
          <div className="kv"><span className="k">Critical dependencies</span><List items={time.critical_dependencies} /></div>
          <div className="kv"><span className="k">Critique</span><List items={time.critique} /></div>
        </AgentColumn>

        <AgentColumn kind="pitch" title="Pitch Specialist" flags={pitch.cross_domain_flags}>
          <div className="kv"><span className="k">Value proposition</span>{pitch.value_proposition || '—'}</div>
          <div className="kv"><span className="k">Differentiation</span><List items={pitch.differentiation} /></div>
          <div className="kv"><span className="k">Impact</span>{pitch.impact || '—'}</div>
          <div className="kv"><span className="k">Critique</span><List items={pitch.critique} /></div>
        </AgentColumn>
      </div>

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
