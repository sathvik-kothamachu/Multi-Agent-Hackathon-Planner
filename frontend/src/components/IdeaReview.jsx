import { useState } from 'react'

// Human-in-the-loop gate: select / modify / regenerate. Never auto-selects.

// Split a multi-paragraph solution into paragraphs for readable rendering.
const paras = (s) => String(s || '').split(/\n\s*\n|\n/).map((p) => p.trim()).filter(Boolean)

function ObjectiveList({ items }) {
  if (!items || items.length === 0) return null
  return (
    <div className="idea-block">
      <span className="idea-block__label">Objectives</span>
      <ol className="idea-objectives">{items.map((x, i) => <li key={i}>{x}</li>)}</ol>
    </div>
  )
}

function FeatureChips({ items }) {
  if (!items || items.length === 0) return null
  return (
    <div className="idea-block">
      <span className="idea-block__label">Core features</span>
      <div className="chips">{items.map((x, i) => <span className="chip" key={i}>{x}</span>)}</div>
    </div>
  )
}

function EditForm({ idea, onSave, onCancel }) {
  const [d, setD] = useState({
    ...idea,
    objectives: (idea.objectives && idea.objectives.length ? idea.objectives : ['', '', '', '']).slice(0, 4),
  })
  const set = (k, v) => setD((x) => ({ ...x, [k]: v }))
  const setObj = (i, v) => setD((x) => {
    const objectives = [...(x.objectives || [])]
    objectives[i] = v
    return { ...x, objectives }
  })
  const save = () => {
    const cleaned = { ...d, objectives: (d.objectives || []).map((o) => o.trim()).filter(Boolean) }
    onSave(cleaned)
  }
  return (
    <div className="idea-card idea-card--selected">
      <div className="field"><label>Title</label>
        <input value={d.title || ''} onChange={(e) => set('title', e.target.value)} /></div>
      <div className="field"><label>Problem</label>
        <textarea value={d.problem || ''} onChange={(e) => set('problem', e.target.value)} /></div>
      <div className="field"><label>Solution (2–3 paragraphs)</label>
        <textarea rows={6} value={d.solution || ''} onChange={(e) => set('solution', e.target.value)} /></div>
      <div className="field"><label>Objectives (4)</label>
        {[0, 1, 2, 3].map((i) => (
          <input key={i} style={{ marginBottom: 6 }} placeholder={`Objective ${i + 1}`}
            value={d.objectives?.[i] || ''} onChange={(e) => setObj(i, e.target.value)} />
        ))}
      </div>
      <div className="field"><label>Target users</label>
        <input value={d.target_users || ''} onChange={(e) => set('target_users', e.target.value)} /></div>
      <div className="field"><label>Expected impact</label>
        <textarea value={d.expected_impact || ''} onChange={(e) => set('expected_impact', e.target.value)} /></div>
      <div className="idea-actions">
        <button className="btn btn--primary btn--sm" onClick={save}>Save &amp; continue →</button>
        <button className="btn btn--ghost btn--sm" onClick={onCancel}>Cancel</button>
      </div>
    </div>
  )
}

// The 8 evaluation criteria, in display order, with short labels.
const CRITERIA = [
  ['theme_alignment', 'Theme'],
  ['problem_relevance', 'Problem'],
  ['innovation', 'Innovation'],
  ['technical_feasibility', 'Tech feasibility'],
  ['time_feasibility', 'Time feasibility'],
  ['team_skill_fit', 'Team fit'],
  ['impact', 'Impact'],
  ['demo_potential', 'Demo'],
]

const scoreColor = (v) =>
  v >= 75 ? 'var(--green)' : v >= 50 ? 'var(--amber)' : 'var(--red)'

// Compact scored view of one idea's evaluation (advisory; never auto-selects).
function EvaluationBlock({ ev }) {
  if (!ev) return null
  return (
    <div className="idea-block">
      <span className="idea-block__label">
        Evaluation
        <span className="score-badge" style={{ marginLeft: 8, borderColor: scoreColor(ev.overall), color: scoreColor(ev.overall) }}>
          <b>{ev.overall}</b><span>/100</span>
        </span>
      </span>
      <table className="mini-table eval-criteria">
        <tbody>
          {CRITERIA.map(([key, label]) => {
            const c = ev[key] || {}
            return (
              <tr key={key}>
                <td style={{ whiteSpace: 'nowrap' }}>{label}</td>
                <td style={{ fontFamily: 'var(--mono)', color: scoreColor(c.score), width: 44 }}>{c.score ?? 0}</td>
                <td className="muted">{c.reason || '—'}</td>
              </tr>
            )
          })}
        </tbody>
      </table>
      <div className="phase-card__meta" style={{ marginTop: 8 }}>
        {ev.strongest_point && <span><b>Strongest:</b> {ev.strongest_point}</span>}
        {ev.biggest_weakness && <span><b>Weakness:</b> {ev.biggest_weakness}</span>}
        {ev.biggest_risk && <span><b>Risk:</b> {ev.biggest_risk}</span>}
        {ev.why_fits && <span><b>Why it fits:</b> {ev.why_fits}</span>}
      </div>
    </div>
  )
}

function IdeaCard({ idea, evaluation, onSelect, onModify, busy }) {
  const [open, setOpen] = useState(false)
  const p = paras(idea.solution)
  const preview = p.slice(0, 1)
  const rest = p.slice(1)
  return (
    <div className="idea-card">
      <div className="idea-title">
        {idea.title || 'Untitled idea'}
        {evaluation && (
          <span className="score-badge" style={{ marginLeft: 8, borderColor: scoreColor(evaluation.overall), color: scoreColor(evaluation.overall) }}>
            <b>{evaluation.overall}</b><span>/100</span>
          </span>
        )}
      </div>

      {idea.core_concept && <p className="idea-text muted" style={{ marginTop: -2 }}>{idea.core_concept}</p>}

      {idea.problem && (
        <div className="idea-block">
          <span className="idea-block__label">Problem</span>
          <p className="idea-text">{idea.problem}</p>
        </div>
      )}

      <div className="idea-block">
        <span className="idea-block__label">Solution</span>
        {preview.map((x, i) => <p className="idea-text" key={i}>{x}</p>)}
        {open && rest.map((x, i) => <p className="idea-text" key={`r${i}`}>{x}</p>)}
        {open && (
          <>
            {idea.how_it_works && (
              <div className="idea-block"><span className="idea-block__label">How it works</span>
                <p className="idea-text">{idea.how_it_works}</p></div>
            )}
            <ObjectiveList items={idea.objectives} />
            <FeatureChips items={idea.core_features} />
            {idea.implementation_approach?.length > 0 && (
              <div className="idea-block">
                <span className="idea-block__label">Implementation approach</span>
                <ol className="idea-objectives">{idea.implementation_approach.map((x, i) => <li key={i}>{x}</li>)}</ol>
              </div>
            )}
            {idea.target_users && (
              <div className="idea-block"><span className="idea-block__label">Target users</span>
                <p className="idea-text">{idea.target_users}</p></div>
            )}
            {idea.expected_impact && (
              <div className="idea-block"><span className="idea-block__label">Expected impact</span>
                <p className="idea-text">{idea.expected_impact}</p></div>
            )}
            {idea.innovation && (
              <div className="idea-block"><span className="idea-block__label">Innovation</span>
                <p className="idea-text">{idea.innovation}</p></div>
            )}
            {idea.feasibility && (
              <div className="idea-block"><span className="idea-block__label">Feasibility</span>
                <p className="idea-text">{idea.feasibility}</p></div>
            )}
            {idea.tech_approach && (
              <div className="idea-block"><span className="idea-block__label">Technology / AI approach</span>
                <p className="idea-text">{idea.tech_approach}</p></div>
            )}
            {idea.theme_relevance && (
              <div className="idea-block"><span className="idea-block__label">Theme relevance</span>
                <p className="idea-text">{idea.theme_relevance}</p></div>
            )}
            <EvaluationBlock ev={evaluation} />
          </>
        )}
      </div>

      <div className="idea-actions">
        <button className="btn btn--primary btn--sm" disabled={busy} onClick={() => onSelect(idea.id)}>Select</button>
        <button className="btn btn--ghost btn--sm" disabled={busy} onClick={() => onModify(idea.id)}>Modify</button>
        {(rest.length > 0 || idea.objectives?.length || idea.core_features?.length ||
          idea.how_it_works || idea.innovation || idea.feasibility || evaluation) && (
          <button className="btn btn--link btn--sm" onClick={() => setOpen((v) => !v)}>
            {open ? 'Read less ▲' : 'Read more ▼'}
          </button>
        )}
      </div>
    </div>
  )
}

// Advisory side-by-side comparison (title / scores / objectives / impact). Non-binding.
function CompareTable({ ideas, evalById }) {
  const hasScores = Object.keys(evalById).length > 0
  return (
    <div className="compare-wrap">
      <table className="compare">
        <thead>
          <tr>
            <th></th>
            {ideas.map((i) => <th key={i.id}>{i.title || 'Idea'}</th>)}
          </tr>
        </thead>
        <tbody>
          {hasScores && (
            <tr>
              <td className="compare__row">Overall score</td>
              {ideas.map((i) => {
                const ev = evalById[i.id]
                return (
                  <td key={i.id} style={{ fontFamily: 'var(--mono)', color: ev ? scoreColor(ev.overall) : 'inherit' }}>
                    {ev ? `${ev.overall}/100` : '—'}
                  </td>
                )
              })}
            </tr>
          )}
          <tr>
            <td className="compare__row">Objectives</td>
            {ideas.map((i) => (
              <td key={i.id}>
                <ol className="compare__list">{(i.objectives || []).map((o, k) => <li key={k}>{o}</li>)}</ol>
              </td>
            ))}
          </tr>
          <tr>
            <td className="compare__row">Target users</td>
            {ideas.map((i) => <td key={i.id}>{i.target_users || '—'}</td>)}
          </tr>
          <tr>
            <td className="compare__row">Expected impact</td>
            {ideas.map((i) => <td key={i.id}>{i.expected_impact || '—'}</td>)}
          </tr>
          <tr>
            <td className="compare__row">Theme relevance</td>
            {ideas.map((i) => <td key={i.id}>{i.theme_relevance || '—'}</td>)}
          </tr>
        </tbody>
      </table>
    </div>
  )
}

export default function IdeaReview({ ideas, evaluations, onSelect, onModify, onRegenerate, busy }) {
  const [editing, setEditing] = useState(null)
  const [compare, setCompare] = useState(false)
  if (!ideas || ideas.length === 0) return <p className="muted">No ideas yet.</p>

  const evalById = {}
  for (const e of evaluations || []) if (e && e.idea_id) evalById[e.idea_id] = e

  return (
    <div>
      <div className="btn-row" style={{ marginTop: 0, marginBottom: 14 }}>
        <button className="btn btn--ghost btn--sm" disabled={busy} onClick={onRegenerate}>↻ Regenerate ideas</button>
        {ideas.length > 1 && (
          <button className="btn btn--ghost btn--sm" onClick={() => setCompare((v) => !v)}>
            {compare ? 'Hide comparison' : '⇄ Compare ideas'}
          </button>
        )}
      </div>

      {Object.keys(evalById).length > 0 && (
        <p className="muted" style={{ marginTop: 0, fontSize: 12.5 }}>
          Scores are advisory — they help you compare, but the choice is yours. Expand an idea (Read more) to see the full breakdown.
        </p>
      )}

      {compare && <CompareTable ideas={ideas} evalById={evalById} />}

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
            <IdeaCard
              key={idea.id}
              idea={idea}
              evaluation={evalById[idea.id]}
              busy={busy}
              onSelect={onSelect}
              onModify={(id) => setEditing(id)}
            />
          )
        )}
      </div>
    </div>
  )
}
