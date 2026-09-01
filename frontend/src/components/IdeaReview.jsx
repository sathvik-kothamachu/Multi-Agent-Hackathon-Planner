import { useState } from 'react'

// Human-in-the-loop gate: select / modify / regenerate. Never auto-selects.
function EditForm({ idea, onSave, onCancel }) {
  const [d, setD] = useState({ ...idea })
  const set = (k, v) => setD((x) => ({ ...x, [k]: v }))
  return (
    <div className="idea-card idea-card--selected">
      <div className="field"><label>Title</label>
        <input value={d.title || ''} onChange={(e) => set('title', e.target.value)} /></div>
      <div className="field"><label>Problem</label>
        <textarea value={d.problem || ''} onChange={(e) => set('problem', e.target.value)} /></div>
      <div className="field"><label>Solution</label>
        <textarea value={d.solution || ''} onChange={(e) => set('solution', e.target.value)} /></div>
      <div className="field"><label>Target users</label>
        <input value={d.target_users || ''} onChange={(e) => set('target_users', e.target.value)} /></div>
      <div className="idea-actions">
        <button className="btn btn--primary btn--sm" onClick={() => onSave(d)}>Save &amp; continue →</button>
        <button className="btn btn--ghost btn--sm" onClick={onCancel}>Cancel</button>
      </div>
    </div>
  )
}

export default function IdeaReview({ ideas, onSelect, onModify, onRegenerate, busy }) {
  const [editing, setEditing] = useState(null)
  if (!ideas || ideas.length === 0) return <p className="muted">No ideas yet.</p>

  return (
    <div>
      <div className="ideas">
        {ideas.map((idea) =>
          editing === idea.id ? (
            <EditForm
              key={idea.id}
              idea={idea}
              onSave={(d) => { setEditing(null); onModify(d) }}
              onCancel={() => setEditing(null)}
            />
          ) : (
            <div className="idea-card" key={idea.id}>
              <div className="idea-title">{idea.title || 'Untitled idea'}</div>
              {idea.problem && <div className="idea-field"><b>Problem:</b> {idea.problem}</div>}
              {idea.solution && <div className="idea-field"><b>Solution:</b> {idea.solution}</div>}
              {idea.target_users && <div className="idea-field"><b>Users:</b> {idea.target_users}</div>}
              {idea.rationale && <div className="idea-field muted">{idea.rationale}</div>}
              <div className="idea-actions">
                <button className="btn btn--primary btn--sm" disabled={busy} onClick={() => onSelect(idea.id)}>Select</button>
                <button className="btn btn--ghost btn--sm" disabled={busy} onClick={() => setEditing(idea.id)}>Modify</button>
              </div>
            </div>
          )
        )}
      </div>
      <div className="btn-row">
        <button className="btn btn--ghost" disabled={busy} onClick={onRegenerate}>↻ Regenerate ideas</button>
      </div>
    </div>
  )
}
