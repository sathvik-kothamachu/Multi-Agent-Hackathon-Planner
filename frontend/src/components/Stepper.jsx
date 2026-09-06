// Pipeline progress indicator. Stages mirror the mandated workflow.
const STAGES = [
  { key: 'setup', label: 'Setup' },
  { key: 'ideas', label: 'Idea Generation' },
  { key: 'review', label: 'Human Review' },
  { key: 'debate', label: 'Multi-Agent Debate' },
  { key: 'alignment', label: 'Alignment Gate' },
  { key: 'persona', label: 'Persona Adaptation' },
  { key: 'blueprint', label: 'Final Blueprint' },
]

export default function Stepper({ current, reached, onJump }) {
  const curIdx = STAGES.findIndex((s) => s.key === current)
  return (
    <div className="stepper">
      {STAGES.map((s, i) => {
        const isReached = reached.has(s.key)
        const cls = [
          'step',
          s.key === current ? 'step--active' : '',
          i < curIdx && isReached ? 'step--done' : '',
          isReached && onJump ? 'clickable' : '',
        ].join(' ')
        return (
          <div
            key={s.key}
            className={cls}
            onClick={() => isReached && onJump && onJump(s.key)}
          >
            <div className="step__idx">{String(i + 1).padStart(2, '0')}</div>
            <div className="step__label">{s.label}</div>
          </div>
        )
      })}
    </div>
  )
}
