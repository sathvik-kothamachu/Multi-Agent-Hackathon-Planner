import { api } from '../api.js'

function Chips({ items }) {
  if (!items || items.length === 0) return <span className="muted">—</span>
  return <div className="chips">{items.map((x, i) => <span className="chip" key={i}>{x}</span>)}</div>
}
function List({ items, ordered }) {
  if (!items || items.length === 0) return <span className="muted">—</span>
  const Tag = ordered ? 'ol' : 'ul'
  return <Tag className="bp-list">{items.map((x, i) => <li key={i}>{x}</li>)}</Tag>
}
function Text({ value }) {
  return <p className="bp-text">{value || '—'}</p>
}
function Section({ title, children }) {
  return <div className="bp-section"><h4>{title}</h4>{children}</div>
}

function StackTable({ details, fallback }) {
  const rows = details?.length ? details : (fallback || []).map((n) => ({ name: n, purpose: '' }))
  if (rows.length === 0) return <span className="muted">—</span>
  return (
    <table className="mini-table">
      <thead><tr><th>Technology</th><th>Purpose</th></tr></thead>
      <tbody>{rows.map((s, i) => <tr key={i}><td>{s.name}</td><td>{s.purpose || '—'}</td></tr>)}</tbody>
    </table>
  )
}

function TeamTable({ items }) {
  if (!items || items.length === 0) return <span className="muted">—</span>
  return (
    <table className="mini-table">
      <thead><tr><th>Member</th><th>Skills</th><th>Responsibilities</th><th>Technologies</th><th>Time</th></tr></thead>
      <tbody>
        {items.map((a, i) => (
          <tr key={i}>
            <td><b>{a.name}</b>{a.role ? <div className="muted" style={{ fontSize: 12 }}>{a.role}</div> : null}</td>
            <td>{(a.skills || []).join(', ') || '—'}</td>
            <td><List items={a.responsibilities} /></td>
            <td>{(a.technologies || []).join(', ') || '—'}</td>
            <td>{a.time_allocation || '—'}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

function ScheduleTable({ items }) {
  if (!items || items.length === 0) return <span className="muted">—</span>
  return (
    <table className="mini-table">
      <thead><tr><th>Task</th><th>Tech</th><th>Duration</th><th>Depends on</th><th>Expected output</th></tr></thead>
      <tbody>
        {items.map((s, i) => (
          <tr key={i}>
            <td>{s.task}</td><td>{s.technology || '—'}</td><td>{s.duration || '—'}</td>
            <td>{s.dependency || '—'}</td><td>{s.expected_output || '—'}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

export default function BlueprintView({ blueprint: b, projectId }) {
  if (!b) return null
  const idea = b.selected_idea || {}
  const rep = b.alignment_report

  return (
    <div>
      <div className="btn-row" style={{ marginTop: 0, marginBottom: 16 }}>
        {projectId && (
          <>
            <a className="btn btn--primary btn--sm" href={api.exportPdfUrl(projectId)} target="_blank" rel="noreferrer">⬇ Download PDF</a>
            <a className="btn btn--ghost btn--sm" href={api.exportDocxUrl(projectId)} target="_blank" rel="noreferrer">⬇ Download editable DOCX</a>
          </>
        )}
      </div>

      <Section title="Project name"><Text value={b.project_name || idea.title} /></Section>
      <Section title="Problem statement"><Text value={b.problem_statement} /></Section>
      <Section title="Hackathon theme"><Text value={b.hackathon_theme} /></Section>
      <Section title="Aim"><Text value={b.aim} /></Section>
      <Section title="Objectives"><List items={b.objectives} ordered /></Section>
      <Section title="Selected idea">
        <div className="idea-title">{idea.title || '—'}</div>
        {idea.solution && <p className="bp-text" style={{ marginTop: 6 }}>{idea.solution}</p>}
      </Section>
      <Section title="Core features"><List items={b.core_features} /></Section>

      <div className="grid2">
        <Section title="Target users"><Text value={b.target_users} /></Section>
        <Section title="Expected impact"><Text value={b.expected_impact} /></Section>
      </div>

      <Section title="Technical architecture"><List items={b.architecture} /></Section>
      <Section title="Technology stack"><StackTable details={b.stack_details} fallback={b.recommended_stack} /></Section>
      <Section title="Team & responsibilities"><TeamTable items={b.team_allocation} /></Section>
      <Section title="Development timeline"><ScheduleTable items={b.schedule} /></Section>
      <Section title="Implementation procedure"><List items={b.implementation_procedure} ordered /></Section>

      <div className="grid2">
        <Section title="Dependencies"><List items={b.dependencies} /></Section>
        <Section title="Technical risks"><List items={b.technical_risks} /></Section>
      </div>
      <div className="grid2">
        <Section title="Risk mitigation"><List items={b.risk_mitigation} /></Section>
        <Section title="Testing plan"><List items={b.testing_plan} /></Section>
      </div>

      <Section title="Demo flow (2-minute)"><List items={b.demo_flow} ordered /></Section>
      <Section title="Value proposition"><Text value={b.value_proposition} /></Section>

      <div className="grid2">
        <Section title="Differentiation"><List items={b.differentiation} /></Section>
        <Section title="Pitch structure"><List items={b.pitch_structure} ordered /></Section>
      </div>

      <Section title="Future scope"><List items={b.future_scope} /></Section>
      <div className="grid2">
        <Section title="MVP features"><List items={b.mvp_features} /></Section>
        <Section title="Nice-to-have features"><List items={b.nice_to_have_features} /></Section>
      </div>

      {rep && (
        <>
          <hr className="divider" />
          <Section title="Theme & problem alignment">
            <p className="bp-text">
              <b style={{ color: rep.overall >= 75 ? 'var(--green)' : rep.overall >= 50 ? 'var(--amber)' : 'var(--red)' }}>
                {rep.overall}/100
              </b> — {rep.label}
            </p>
            {rep.explanation && <p className="muted">{rep.explanation}</p>}
          </Section>
        </>
      )}
    </div>
  )
}
