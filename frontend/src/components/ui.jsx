// Small shared presentational helpers.
export function Panel({ idx, title, sub, right, children }) {
  return (
    <section className="panel">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12 }}>
        <div>
          <h2 className="panel__title">
            {idx != null && <span className="idx">{idx}</span>}
            {title}
          </h2>
          {sub && <p className="panel__sub">{sub}</p>}
        </div>
        {right}
      </div>
      {children}
    </section>
  )
}

export function Banner({ kind = 'info', children }) {
  return <div className={`banner banner--${kind}`}>{children}</div>
}

export function Loading({ label = 'Working…' }) {
  return (
    <div className="loading">
      <span className="spinner" />
      {label}
    </div>
  )
}

export const fmtInt = (n) => (n == null ? '—' : Number(n).toLocaleString('en-US'))
