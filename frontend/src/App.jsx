import { useState } from 'react'
import { api, errMsg } from './api.js'
import Stepper from './components/Stepper.jsx'
import SetupForm from './components/SetupForm.jsx'
import IdeaReview from './components/IdeaReview.jsx'
import DebatePanel from './components/DebatePanel.jsx'
import AlignmentGate from './components/AlignmentGate.jsx'
import PersonaCompare from './components/PersonaCompare.jsx'
import BlueprintView from './components/BlueprintView.jsx'
import { Panel, Banner, Loading } from './components/ui.jsx'

const RESULT_VIEWS = ['debate', 'alignment', 'persona', 'blueprint']

export default function App() {
  const [stage, setStage] = useState('setup') // setup | review | result
  const [projectId, setProjectId] = useState(null)
  const [ideas, setIdeas] = useState([])
  const [evaluations, setEvaluations] = useState([])
  const [blueprint, setBlueprint] = useState(null)
  const [persona, setPersona] = useState(null)
  const [debate, setDebate] = useState(null)
  const [alignment, setAlignment] = useState(null)
  const [resultView, setResultView] = useState('debate')
  const [busy, setBusy] = useState(false)
  const [busyLabel, setBusyLabel] = useState('')
  const [error, setError] = useState('')

  const guard = async (label, fn) => {
    setBusy(true)
    setBusyLabel(label)
    setError('')
    try {
      return await fn()
    } catch (e) {
      setError(errMsg(e))
    } finally {
      setBusy(false)
      setBusyLabel('')
    }
  }

  const reset = () => {
    setStage('setup')
    setProjectId(null)
    setIdeas([])
    setEvaluations([])
    setBlueprint(null)
    setPersona(null)
    setDebate(null)
    setAlignment(null)
    setResultView('debate')
    setError('')
  }

  const create = (payload) =>
    guard('Generating ideas…', async () => {
      const r = await api.createProject(payload)
      setProjectId(r.project_id)
      setIdeas(r.ideas || [])
      setEvaluations(r.evaluations || [])
      setStage('review')
    })

  const regenerate = () =>
    guard('Regenerating ideas…', async () => {
      const r = await api.regenerate(projectId)
      setIdeas(r.ideas || [])
      setEvaluations(r.evaluations || [])
    })

  const finish = async (r) => {
    setBlueprint(r.blueprint || null)
    setPersona(r.persona_adapted_plan || null)
    const [d, a] = await Promise.all([
      api.getDebate(projectId),
      api.getAlignment(projectId).catch(() => null),
    ])
    setDebate(d)
    setAlignment(a?.report || null)
    setStage('result')
    setResultView('debate')
  }

  const select = (id) =>
    guard('Running debate → alignment → persona…', async () => {
      await finish(await api.selectIdea(projectId, id))
    })

  const modify = (idea) =>
    guard('Running debate → alignment → persona…', async () => {
      await finish(await api.modifyIdea(projectId, idea))
    })

  const reached = new Set(['setup'])
  if (stage === 'review') {
    reached.add('ideas')
    reached.add('review')
  }
  if (stage === 'result') {
    ;['ideas', 'review', 'debate', 'alignment', 'persona', 'blueprint'].forEach((k) => reached.add(k))
  }
  const current = stage === 'setup' ? 'setup' : stage === 'review' ? 'review' : resultView

  const onJump = (key) => {
    if (key === 'setup') return reset()
    if (stage === 'result' && RESULT_VIEWS.includes(key)) setResultView(key)
  }

  // Prev/Next navigation across the result-stage views.
  const idx = RESULT_VIEWS.indexOf(resultView)
  const goPrev = () => idx > 0 && setResultView(RESULT_VIEWS[idx - 1])
  const goNext = () => idx < RESULT_VIEWS.length - 1 && setResultView(RESULT_VIEWS[idx + 1])

  const ResultNav = () => (
    <div className="btn-row result-nav">
      <button className="btn btn--ghost btn--sm" onClick={goPrev} disabled={idx <= 0}>← Previous</button>
      <button className="btn btn--ghost btn--sm" onClick={goNext} disabled={idx >= RESULT_VIEWS.length - 1}>Next →</button>
    </div>
  )

  return (
    <div className="app">
      <header className="app__header">
        <div className="brand">
          <div className="brand__mark">◧</div>
          <div className="brand__title">
            Agentic Hackathon Planner
            <small>idea generation · multi-agent debate · alignment · persona adaptation</small>
          </div>
        </div>
        <div className="header__note">
          {projectId ? <>project <b className="mono">{String(projectId).slice(0, 8)}</b></> : 'human-in-the-loop pipeline'}
        </div>
      </header>

      <Stepper current={current} reached={reached} onJump={onJump} />

      {error && <Banner kind="error">{error}</Banner>}

      {stage === 'setup' && (
        <Panel idx="01" title="Project setup" sub="Describe the problem, theme, time limit, and team. Ideas are generated but never auto-selected.">
          <SetupForm onSubmit={create} busy={busy} />
        </Panel>
      )}

      {stage === 'review' && (
        <Panel idx="03" title="Human review" sub="Select an idea, modify one, or regenerate. You control this gate.">
          {busy ? <Loading label={busyLabel} /> : (
            <IdeaReview ideas={ideas} evaluations={evaluations} onSelect={select} onModify={modify} onRegenerate={regenerate} busy={busy} />
          )}
        </Panel>
      )}

      {stage === 'result' && (
        <>
          {busy && <Panel title="Working"><Loading label={busyLabel} /></Panel>}
          {!busy && resultView === 'debate' && (
            <Panel idx="04" title="Multi-agent debate" sub="Tech and Timeline specialists critique the same idea; conflicts (complexity vs. time) are detected and resolved. Pitch is prepared at the final stage.">
              <DebatePanel debate={debate} />
              <ResultNav />
            </Panel>
          )}
          {!busy && resultView === 'alignment' && (
            <Panel idx="05" title="Theme & problem alignment" sub="How well the chosen solution fits your theme, problem, users, and time limit.">
              <AlignmentGate report={alignment} />
              <ResultNav />
            </Panel>
          )}
          {!busy && resultView === 'persona' && (
            <Panel idx="06" title="Persona adaptation" sub="The same plan re-explained for beginner, intermediate, and advanced teams.">
              <PersonaCompare defaultPlan={persona} onAdapt={(p) => api.adaptPersona(projectId, p)} />
              <ResultNav />
            </Panel>
          )}
          {!busy && resultView === 'blueprint' && (
            <Panel idx="07" title="Final blueprint" sub="The converged, human-approved plan. Download as PDF or editable DOCX.">
              <BlueprintView blueprint={blueprint} projectId={projectId} />
              <ResultNav />
            </Panel>
          )}
        </>
      )}
    </div>
  )
}
