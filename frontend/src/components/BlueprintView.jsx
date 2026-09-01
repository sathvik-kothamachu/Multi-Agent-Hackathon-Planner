function Chips({ items }) {
  if (!items || items.length === 0) return <span className="muted">—</span>
  return <div className="chips">{items.map((x, i) => <span className="chip" key={i}>{x}</span>)}</div>
}
function List({ items, ordered }) {
  if (!items || items.length === 0) return <span className="muted">—</span>
  const Tag = ordered ? 'ol' : 'ul'
  return <Tag className="bp-list">{items.map((x, i) => <li key={i}>{x}</li>)}</Tag>
}

export default function BlueprintView({ blueprint: b }) {
  if (!b) return null
  return (
    <div>
      <div className="bp-section">
        <h4>Selected idea</h4>
        <div className="idea-title">{b.selected_idea?.title || '—'}</div>
        {b.selected_idea?.solution && <p className="muted" style={{ marginTop: 6 }}>{b.selected_idea.solution}</p>}
      </div>

      <div className="grid2">
        <div className="bp-section"><h4>Recommended stack</h4><Chips items={b.recommended_stack} /></div>
        <div className="bp-section"><h4>Target users</h4><p>{b.target_users || '—'}</p></div>
      </div>

      <div className="bp-section"><h4>Architecture</h4><List items={b.architecture} /></div>

      <div className="bp-section">
        <h4>Timeline</h4>
        {(b.timeline || []).length === 0 ? <span className="muted">—</span> : (b.timeline || []).map((m, i) => (
          <div className="milestone" key={i}>
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10 }}>
              <span className="milestone__name">{m.name}</span>
              {m.duration && <span className="milestone__dur">{m.duration}</span>}
            </div>
            {m.deliverables?.length > 0 && <List items={m.deliverables} />}
          </div>
        ))}
      </div>

      <div className="grid2">
        <div className="bp-section"><h4>Dependencies</h4><List items={b.dependencies} /></div>
        <div className="bp-section"><h4>Technical risks</h4><List items={b.technical_risks} /></div>
      </div>

      <div className="bp-section"><h4>Value proposition</h4><p>{b.value_proposition || '—'}</p></div>

      <div className="grid2">
        <div className="bp-section"><h4>Differentiation</h4><List items={b.differentiation} /></div>
        <div className="bp-section"><h4>Pitch structure</h4><List items={b.pitch_structure} ordered /></div>
      </div>

      <hr className="divider" />
      <div className="kv mono" style={{ fontSize: 13 }}>
        <span className="k">Convergence</span>
        Alignment {b.alignment_score != null ? Number(b.alignment_score).toFixed(3) : '—'} · {b.alignment_status || '—'} · {b.debate_summary || ''}
      </div>
    </div>
  )
}
