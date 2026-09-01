import { useState } from 'react'
import { Loading, Banner, fmtInt } from './ui.jsx'

const f3 = (v) => (v == null ? '—' : Number(v).toFixed(3))

// Research requirement #16: full pipeline vs single-shot baseline, measured.
export default function Evaluation({ onRun }) {
  const [report, setReport] = useState(null)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')

  const run = async () => {
    setBusy(true)
    setErr('')
    try {
      setReport(await onRun())
    } catch (e) {
      setErr(String(e))
    } finally {
      setBusy(false)
    }
  }

  const P = report?.proposed_metrics
  const B = report?.baseline_metrics

  return (
    <div>
      <p className="panel__sub">
        Ablation: the full multi-agent pipeline vs a single-shot LLM baseline. Running this makes
        one extra baseline LLM call; the baseline is cached afterwards.
      </p>

      {!report && !busy && (
        <button className="btn btn--primary" onClick={run}>Run evaluation</button>
      )}
      {err && <Banner kind="error">{err}</Banner>}
      {busy && <Loading label="Running single-shot baseline…" />}

      {report && P && B && (
        <>
          <table className="eval-table">
            <thead>
              <tr><th>Metric</th><th className="num col-prop">Proposed</th><th className="num col-base">Baseline</th></tr>
            </thead>
            <tbody>
              <tr><td>LLM calls</td><td className="num col-prop">{fmtInt(P.llm_calls)}</td><td className="num col-base">{fmtInt(B.llm_calls)}</td></tr>
              <tr><td>Total tokens</td><td className="num col-prop">{fmtInt(P.total_tokens)}</td><td className="num col-base">{fmtInt(B.total_tokens)}</td></tr>
              <tr><td>Latency (ms)</td><td className="num col-prop">{fmtInt(Math.round(P.latency_ms))}</td><td className="num col-base">{fmtInt(Math.round(B.latency_ms))}</td></tr>
              <tr><td>Debate rounds</td><td className="num col-prop">{fmtInt(P.debate_rounds)}</td><td className="num col-base">{fmtInt(B.debate_rounds)}</td></tr>
              <tr><td>Conflicts (detected / resolved)</td><td className="num col-prop">{report.conflicts_detected} / {report.conflicts_resolved}</td><td className="num col-base">0 / 0</td></tr>
              <tr><td>Final alignment</td><td className="num col-prop">{f3(report.proposed_alignment)}</td><td className="num col-base">{f3(report.baseline_alignment)}</td></tr>
            </tbody>
          </table>

          <ul className="notes">
            {(report.notes || []).map((n, i) => <li key={i}>{n}</li>)}
          </ul>
          <p className="muted" style={{ fontSize: 12, marginTop: 10 }}>
            All numbers are measured from actual runs — not fabricated. Re-run to refresh.
          </p>
          <div className="btn-row">
            <button className="btn btn--ghost btn--sm" onClick={run} disabled={busy}>↻ Re-run</button>
          </div>
        </>
      )}
    </div>
  )
}
