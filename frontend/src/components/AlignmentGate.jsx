// Signature view: semantic alignment meter (cosine similarity vs the original
// goal). Computed on the backend with Sentence Transformers — NO LLM.

const STATUS_LABEL = {
  aligned: 'ALIGNED',
  drift: 'GOAL DRIFT',
  max_rounds_exceeded: 'MAX ROUNDS — STOPPED',
}
const STATUS_COLOR = {
  aligned: 'var(--green)',
  drift: 'var(--amber)',
  max_rounds_exceeded: 'var(--red)',
}

const pct = (v) => `${Math.max(0, Math.min(1, v || 0)) * 100}%`
const fmt = (v) => (v == null ? '—' : Number(v).toFixed(3))

export default function AlignmentGate({ debate }) {
  if (!debate) return null
  const score = debate.alignment_score
  const threshold = debate.threshold ?? 0.75
  const status = debate.alignment_status || (score >= threshold ? 'aligned' : 'drift')
  const history = debate.alignment_history || []
  const color = STATUS_COLOR[status] || 'var(--cyan)'

  return (
    <div>
      <div className="gate__row">
        <div className="gate__scorebox">
          <div className="gate__score" style={{ color }}>{fmt(score)}</div>
          <div className="gate__scorelabel">cosine similarity</div>
        </div>

        <div className="meter">
          <div className="meter__track">
            <div className="meter__fill" style={{ width: pct(score), background: `${color}88`, boxShadow: `0 0 18px ${color}77` }} />
            <div className="meter__threshold" style={{ left: pct(threshold) }} data-label={`threshold ${threshold}`} />
          </div>
          <div className="meter__scale"><span>0.0</span><span>0.5</span><span>1.0</span></div>
          <div style={{ marginTop: 12 }}>
            <span className={`gate__status status--${status}`} style={{ color }}>
              ● {STATUS_LABEL[status] || status}
            </span>
            <span className="muted mono" style={{ marginLeft: 12, fontSize: 12 }}>
              round {debate.debate_round} / {debate.max_debate_rounds ?? 3}
            </span>
          </div>
        </div>
      </div>

      {status === 'drift' && (
        <p className="muted" style={{ marginTop: 14 }}>
          Below threshold → the solution drifted from the original goal, so another debate round is triggered.
        </p>
      )}
      {status === 'max_rounds_exceeded' && (
        <p className="muted" style={{ marginTop: 14 }}>
          Still below threshold at the round cap — the loop stops in a controlled way and returns the best result so far.
        </p>
      )}

      {history.length > 0 && (
        <div className="history">
          <div className="metric__label" style={{ marginBottom: 8 }}>Alignment per round</div>
          {history.map((h, i) => (
            <div className="history__row" key={i}>
              <span style={{ width: 64 }}>round {h.round}</span>
              <span style={{ width: 56 }}>{fmt(h.score)}</span>
              <span className="history__bar" style={{ width: `${Math.max(4, Math.min(1, h.score || 0) * 260)}px`, background: STATUS_COLOR[h.status] || 'var(--cyan)' }} />
              <span className="muted">{STATUS_LABEL[h.status] || h.status}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
