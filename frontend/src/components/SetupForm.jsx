import { useState } from 'react'

const SKILLS = ['beginner', 'intermediate', 'advanced']
const EXAMPLE =
  'Help small clinics reduce no-show appointments without adding staff workload.'

const emptyMember = () => ({ name: '', role: '', skills: [], skill_level: 'intermediate' })

// One team member row: name, role, multiple skill chips, skill level.
function MemberRow({ member, index, onChange, onRemove, canRemove }) {
  const [skillInput, setSkillInput] = useState('')
  const set = (k, v) => onChange(index, { ...member, [k]: v })

  const addSkill = () => {
    const s = skillInput.trim()
    if (!s) return
    if (!member.skills.some((x) => x.toLowerCase() === s.toLowerCase())) {
      set('skills', [...member.skills, s])
    }
    setSkillInput('')
  }
  const removeSkill = (s) => set('skills', member.skills.filter((x) => x !== s))
  const onSkillKey = (e) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault()
      addSkill()
    }
  }

  return (
    <div className="member-card">
      <div className="member-card__grid">
        <div className="field">
          <label>Name *</label>
          <input value={member.name} placeholder="e.g. Ana" onChange={(e) => set('name', e.target.value)} />
        </div>
        <div className="field">
          <label>Role</label>
          <input value={member.role} placeholder="e.g. Frontend developer" onChange={(e) => set('role', e.target.value)} />
        </div>
        <div className="field">
          <label>Skill level</label>
          <select value={member.skill_level} onChange={(e) => set('skill_level', e.target.value)}>
            {SKILLS.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
      </div>

      <div className="field">
        <label>Skills * (Enter or comma to add)</label>
        <div className="chip-input">
          {member.skills.map((s) => (
            <span className="chip chip--removable" key={s}>
              {s}
              <button type="button" className="chip__x" onClick={() => removeSkill(s)} aria-label={`Remove ${s}`}>×</button>
            </span>
          ))}
          <input
            className="chip-input__field"
            value={skillInput}
            placeholder={member.skills.length ? '' : 'e.g. React, Python, Figma'}
            onChange={(e) => setSkillInput(e.target.value)}
            onKeyDown={onSkillKey}
            onBlur={addSkill}
          />
        </div>
      </div>

      {canRemove && (
        <button type="button" className="btn btn--sm btn--danger-soft" onClick={() => onRemove(index)}>
          Remove teammate
        </button>
      )}
    </div>
  )
}

export default function SetupForm({ onSubmit, busy }) {
  const [problem, setProblem] = useState('')
  const [theme, setTheme] = useState('general')
  const [hours, setHours] = useState(24)
  const [prefs, setPrefs] = useState('')
  const [usingAi, setUsingAi] = useState(true)
  const [members, setMembers] = useState([{ name: '', role: 'Full-stack developer', skills: [], skill_level: 'intermediate' }])
  const [err, setErr] = useState('')

  const changeMember = (i, next) => setMembers((m) => m.map((x, idx) => (idx === i ? next : x)))
  const addMember = () => setMembers((m) => [...m, emptyMember()])
  const removeMember = (i) => setMembers((m) => m.filter((_, idx) => idx !== i))

  const submit = (e) => {
    e.preventDefault()
    setErr('')
    if (!problem.trim()) return setErr('Problem statement is required.')
    if (!theme.trim()) return setErr('Hackathon theme is required.')
    const h = Number(hours)
    if (!h || h < 1) return setErr('Enter a valid time limit (hours).')
    const filled = members.filter((m) => m.name.trim())
    if (filled.length === 0) return setErr('Add at least one team member with a name.')
    const missingSkills = filled.find((m) => m.skills.length === 0)
    if (missingSkills) return setErr(`Add at least one skill for ${missingSkills.name || 'each member'}.`)

    onSubmit({
      problem_statement: problem.trim(),
      hackathon_theme: theme.trim(),
      time_limit_hours: h,
      preferences: prefs.trim(),
      using_ai: usingAi,
      team_members: filled.map((m) => ({
        name: m.name.trim(),
        role: m.role.trim(),
        skills: m.skills,
        skill_level: m.skill_level,
      })),
    })
  }

  return (
    <form onSubmit={submit}>
      <div className="field">
        <label>Problem statement *</label>
        <textarea value={problem} onChange={(e) => setProblem(e.target.value)} placeholder={EXAMPLE} required />
        {!problem && (
          <button type="button" className="btn btn--ghost btn--sm" style={{ marginTop: 8 }} onClick={() => setProblem(EXAMPLE)}>
            Use example
          </button>
        )}
      </div>

      <div className="grid2">
        <div className="field">
          <label>Hackathon theme *</label>
          <input value={theme} onChange={(e) => setTheme(e.target.value)} placeholder="e.g. AI for healthcare" />
        </div>
        <div className="field">
          <label>Time limit (hours) *</label>
          <input type="number" min="1" max="168" value={hours} onChange={(e) => setHours(e.target.value)} />
        </div>
      </div>

      <div className="field">
        <label>Preferences / constraints (optional)</label>
        <input value={prefs} onChange={(e) => setPrefs(e.target.value)} placeholder="e.g. must use Python; no paid APIs" />
      </div>

      <div className="field">
        <label>Are you using AI tools to build this hackathon project?</label>
        <div className="toggle-row">
          <button type="button" className={`toggle ${usingAi ? 'toggle--on' : ''}`} onClick={() => setUsingAi(true)}>Yes</button>
          <button type="button" className={`toggle ${!usingAi ? 'toggle--on' : ''}`} onClick={() => setUsingAi(false)}>No</button>
          <span className="muted" style={{ fontSize: 12 }}>
            {usingAi
              ? 'The Tech agent may recommend AI/LLM tools where they add value.'
              : 'The Tech agent will avoid introducing AI/LLM tools and prefer your team’s skills.'}
          </span>
        </div>
      </div>

      <div className="field">
        <label>Team — names & skills drive task allocation and persona adaptation</label>
        {members.map((m, i) => (
          <MemberRow
            key={i}
            member={m}
            index={i}
            onChange={changeMember}
            onRemove={removeMember}
            canRemove={members.length > 1}
          />
        ))}
        <button type="button" className="btn btn--ghost btn--sm" onClick={addMember}>+ Add teammate</button>
      </div>

      {err && <div className="banner banner--error">{err}</div>}

      <div className="btn-row">
        <button type="submit" className="btn btn--primary" disabled={busy || !problem.trim()}>
          {busy ? 'Generating ideas…' : 'Generate ideas →'}
        </button>
      </div>
    </form>
  )
}
