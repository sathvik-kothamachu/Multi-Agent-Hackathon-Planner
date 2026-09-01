import { useState } from 'react'
import { Loading, Banner } from './ui.jsx'

const PERSONAS = ['beginner', 'intermediate', 'advanced']

// Research objective #3: the SAME plan re-explained per skill level (on demand).
export default function PersonaCompare({ defaultPlan, onAdapt }) {
  const seed = defaultPlan?.persona || 'intermediate'
  const [plans, setPlans] = useState(defaultPlan ? { [seed]: defaultPlan } : {})
  const [active, setActive] = useState(seed)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')

  const pick = async (p) => {
    setActive(p)
    setErr('')
    if (plans[p]) return
    setBusy(true)
    try {
      const plan = await onAdapt(p)
      setPlans((m) => ({ ...m, [p]: plan }))
    } catch (e) {
      setErr(String(e))
    } finally {
      setBusy(false)
    }
  }

  const plan = plans[active]
  return (
    <div>
      <p className="panel__sub">
        Same blueprint, re-explained for each skill level. The underlying solution never changes —
        only depth, terminology, and hand-holding.
      </p>
      <div className="persona__tabs">
        {PERSONAS.map((p) => (
          <button
            key={p}
            className={`persona-tab ${p === active ? 'persona-tab--active' : ''}`}
            onClick={() => pick(p)}
          >
            {p}{p === seed ? ' (team)' : ''}
          </button>
        ))}
      </div>

      {err && <Banner kind="error">{err}</Banner>}
      {busy && <Loading label={`Adapting for ${active}…`} />}

      {!busy && plan && (
        <div>
          {plan.summary && <p style={{ marginTop: 0 }}>{plan.summary}</p>}
          <div className="guidance">
            <div className="guidance__block"><h4>Tech guidance</h4><p>{plan.tech_guidance || '—'}</p></div>
            <div className="guidance__block"><h4>Timeline guidance</h4><p>{plan.timeline_guidance || '—'}</p></div>
            <div className="guidance__block"><h4>Pitch guidance</h4><p>{plan.pitch_guidance || '—'}</p></div>
            <div className="guidance__block">
              <h4>Watch out for</h4>
              {plan.pitfalls?.length ? (
                <ul className="bp-list">{plan.pitfalls.map((x, i) => <li key={i}>{x}</li>)}</ul>
              ) : <p className="muted">—</p>}
            </div>
          </div>
          {plan.next_steps?.length > 0 && (
            <div className="bp-section" style={{ marginTop: 14 }}>
              <h4>First steps</h4>
              <ol className="bp-list">{plan.next_steps.map((x, i) => <li key={i}>{x}</li>)}</ol>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
