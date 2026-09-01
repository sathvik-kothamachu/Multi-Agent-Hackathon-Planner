import { useState } from 'react'

const SKILLS = ['beginner', 'intermediate', 'advanced']
const EXAMPLE =
  'Help small clinics reduce no-show appointments without adding staff workload.'

export default function SetupForm({ onSubmit, busy }) {
  const [problem, setProblem] = useState('')
  const [theme, setTheme] = useState('general')
  const [hours, setHours] = useState(24)
  const [prefs, setPrefs] = useState('')
  const [members, setMembers] = useState([{ role: 'Full-stack developer', skill_level: 'intermediate' }])

  const setMember = (i, key, val) =>
    setMembers((m) => m.map((x, idx) => (idx === i ? { ...x, [key]: val } : x)))
  const addMember = () => setMembers((m) => [...m, { role: '', skill_level: 'intermediate' }])
  const removeMember = (i) => setMembers((m) => m.filter((_, idx) => idx !== i))

  const submit = (e) => {
    e.preventDefault()
    if (!problem.trim()) return
    onSubmit({
      problem_statement: problem.trim(),
      hackathon_theme: theme.trim() || 'general',
      time_limit_hours: Number(hours) || 24,
      preferences: prefs.trim(),
      team_members: members.filter((m) => m.role.trim()),
    })
  }

  return (
    <form onSubmit={submit}>
      <div className="field">
        <label>Problem statement *</label>
        <textarea
          value={problem}
          onChange={(e) => setProblem(e.target.value)}
          placeholder={EXAMPLE}
          required
        />
        {!problem && (
          <button type="button" className="btn btn--ghost btn--sm" style={{ marginTop: 8 }} onClick={() => setProblem(EXAMPLE)}>
            Use example
          </button>
        )}
      </div>

      <div className="grid2">
        <div className="field">
          <label>Hackathon theme</label>
          <input value={theme} onChange={(e) => setTheme(e.target.value)} placeholder="e.g. AI for healthcare" />
        </div>
        <div className="field">
          <label>Time limit (hours)</label>
          <input type="number" min="1" max="168" value={hours} onChange={(e) => setHours(e.target.value)} />
        </div>
      </div>

      <div className="field">
        <label>Preferences / constraints (optional)</label>
        <input value={prefs} onChange={(e) => setPrefs(e.target.value)} placeholder="e.g. must use Python; no paid APIs" />
      </div>

      <div className="field">
        <label>Team profile — drives persona adaptation</label>
        {members.map((m, i) => (
          <div className="team-row" key={i}>
            <input
              placeholder="Role (e.g. Frontend developer)"
              value={m.role}
              onChange={(e) => setMember(i, 'role', e.target.value)}
            />
            <select value={m.skill_level} onChange={(e) => setMember(i, 'skill_level', e.target.value)}>
              {SKILLS.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
            <button type="button" className="btn btn--sm btn--danger-soft" onClick={() => removeMember(i)} disabled={members.length === 1}>
              Remove
            </button>
          </div>
        ))}
        <button type="button" className="btn btn--ghost btn--sm" onClick={addMember}>+ Add teammate</button>
      </div>

      <div className="btn-row">
        <button type="submit" className="btn btn--primary" disabled={busy || !problem.trim()}>
          {busy ? 'Generating ideas…' : 'Generate ideas →'}
        </button>
      </div>
    </form>
  )
}
