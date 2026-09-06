// User-friendly "Theme & Problem Alignment" view. Shows an overall /100 score
// plus five sub-scores, a plain-language explanation, and improvement suggestions
// when alignment is low. Scores are computed deterministically on the backend
// (semantic embeddings + lexical overlap + feasibility) — no LLM, no cosine jargon.

const color = (v) => (v >= 75 ? 'var(--green)' : v >= 50 ? 'var(--amber)' : 'var(--red)')

function Ring({ value }) {
  const v = Math.max(0, Math.min(100, Number(value || 0)))
  const c = color(v)
  return (
    <div className="align-ring" style={{ background: `conic-gradient(${c} ${v * 3.6}deg, var(--line) 0deg)` }}>
      <div className="align-ring__hole">
        <div className="align-ring__num" style={{ color: c }}>{v}</div>
        <div className="align-ring__unit">/ 100</div>
      </div>
    </div>
  )
}

function Bar({ label, value, reason, fix }) {
  const v = Math.max(0, Math.min(100, Number(value || 0)))
  const c = color(v)
  return (
    <div className="align-bar">
      <div className="align-bar__head">
        <span>{label}</span>
        <b style={{ color: c }}>{v}</b>
      </div>
      <div className="align-bar__track">
        <div className="align-bar__fill" style={{ width: `${v}%`, background: c }} />
      </div>
      {reason && <p className="align-bar__why">{reason}</p>}
      {v < 75 && fix && <p className="align-bar__fix">↳ {fix}</p>}
    </div>
  )
}

export default function AlignmentGate({ report }) {
  if (!report) return <p className="muted">Alignment is computed once you select an idea.</p>

  // Match each category to its improvement suggestion (suggestions are prefixed
  // with the category name on the backend, e.g. "Theme (62/100): ...").
  const fixFor = (name) =>
    (report.improvements || []).find((s) => s.toLowerCase().startsWith(name.toLowerCase()))

  const subs = [
    ['Theme relevance', report.theme_relevance, report.theme_reason, fixFor('Theme')],
    ['Problem relevance', report.problem_relevance, report.problem_reason, fixFor('Problem')],
    ['User–problem fit', report.user_problem_fit, report.user_problem_reason, fixFor('User')],
    ['Solution relevance', report.solution_relevance, report.solution_reason, fixFor('Solution')],
    ['Feasibility', report.feasibility, report.feasibility_reason, fixFor('Feasibility')],
  ]

  return (
    <div>
      <div className="align-head">
        <Ring value={report.overall} />
        <div>
          <div className="align-label" style={{ color: color(report.overall) }}>{report.label || '—'}</div>
          {report.explanation && <p className="muted" style={{ marginTop: 6 }}>{report.explanation}</p>}
          {report.strengthened && (
            <p className="align-note">✓ The selected idea's description was strengthened once (same concept) to sharpen its theme, problem and user links before scoring.</p>
          )}
        </div>
      </div>

      <div className="align-bars">
        {subs.map(([label, v, reason, fix]) => (
          <Bar key={label} label={label} value={v} reason={reason} fix={fix} />
        ))}
      </div>

      {report.improvements?.length > 0 && (
        <div className="bp-section" style={{ marginTop: 18 }}>
          <h4>How to reach 75+ in every category</h4>
          <ul className="bp-list">{report.improvements.map((x, i) => <li key={i}>{x}</li>)}</ul>
        </div>
      )}
    </div>
  )
}
