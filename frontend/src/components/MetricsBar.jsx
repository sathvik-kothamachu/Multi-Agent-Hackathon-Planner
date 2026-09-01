import { fmtInt } from './ui.jsx'

// Always-visible efficiency instrumentation (research requirement #7).
export default function MetricsBar({ metrics }) {
  if (!metrics) return null
  const items = [
    ['LLM calls', fmtInt(metrics.llm_calls)],
    ['Total tokens', fmtInt(metrics.total_tokens)],
    ['Input tok', fmtInt(metrics.input_tokens)],
    ['Output tok', fmtInt(metrics.output_tokens)],
    ['Latency', <>{fmtInt(Math.round(metrics.latency_ms))} <small>ms</small></>],
    ['Debate rounds', <>{fmtInt(metrics.debate_rounds)} <small>/ 3</small></>],
  ]
  return (
    <div className="metrics">
      {items.map(([label, value]) => (
        <div className="metric" key={label}>
          <div className="metric__label">{label}</div>
          <div className="metric__value">{value}</div>
        </div>
      ))}
    </div>
  )
}
