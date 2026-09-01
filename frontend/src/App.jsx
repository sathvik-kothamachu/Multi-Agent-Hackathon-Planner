import { useState } from 'react'
import { api, errMsg } from './api.js'
import Stepper from './components/Stepper.jsx'
import MetricsBar from './components/MetricsBar.jsx'
import SetupForm from './components/SetupForm.jsx'
import IdeaReview from './components/IdeaReview.jsx'
import DebatePanel from './components/DebatePanel.jsx'
import AlignmentGate from './components/AlignmentGate.jsx'
import PersonaCompare from './components/PersonaCompare.jsx'
import BlueprintView from './components/BlueprintView.jsx'
import Evaluation from './components/Evaluation.jsx'
import { Panel, Banner, Loading } from './components/ui.jsx'

const RESULT_VIEWS = ['debate', 'alignment', 'persona', 'blueprint']

export default function App() {
  const [stage, setStage] = useState('setup') // setup | review | result
  const [projectId, setProjectId] = useState(null)
  const [ideas, setIdeas] = useState([])
  const [metrics, setMetrics] = useState(null)
  const [blueprint, setBlueprint] = useState(null)
  const [persona, setPersona] = useState(null)
  const [debate, setDebate] = useState(null)
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
    setMetrics(null)
    setBlueprint(null)
    setPersona(null)
    setDebate(null)
    setResultView('debate')
    setError('')
  }

  const create = (payload) =>
    guard('Generating ideas…', async () => {
      const r = await api.createProject(payload)
      setProjectId(r.project_id)
      setIdeas(r.ideas || [])
      setMetrics(r.metrics || null)
      setStage('review')
    })

  const regenerate = () =>
    guard('Regenerating ideas…', async () => {
      const r = await api.regenerate(projectId)
      setIdeas(r.ideas || [])
      setMetrics(r.metrics || null)
    })

  const finish = async (r) => {
    setBlueprint(r.blueprint || null)
    setPersona(r.persona_adapted_plan || null)
    setMetrics(r.metrics || null)
    const d = await api.getDebate(projectId)
    setDebate(d)
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

  return (
    <div className="app">
      <header className="app__header">
        <div className="brand">
          <div className="brand__mark">◧</div>
          <div className="brand__title">
            Multi-Agent Hackathon Planner
            <small>debate · alignment gate · persona adaptation</small>
          </div>
        </div>
        <div className="header__note">
          {projectId ? <>project <b className="mono">{String(projectId).slice(0, 8)}</b></> : 'human-in-the-loop pipeline'}
        </div>
      </header>

      <Stepper current={current} reached={reached} onJump={onJump} />

      {metrics && (
        <div className="panel">
          <div className="metric__label" style={{ marginBottom: 10 }}>Live efficiency metrics</div>
          <MetricsBar metrics={metrics} />
        </div>
      )}

      {error && <Banner kind="error">{error}</Banner>}

      {stage === 'setup' && (
        <Panel idx="01" title="Project setup" sub="Describe the problem, theme, time limit, and team. Ideas are generated but never auto-selected.">
          <SetupForm onSubmit={create} busy={busy} />
        </Panel>
      )}

      {stage === 'review' && (
        <Panel idx="03" title="Human review" sub="Select an idea, modify one, or regenerate. You control this gate.">
          {busy ? <Loading label={busyLabel} /> : (
            <IdeaReview ideas={ideas} onSelect={select} onModify={modify} onRegenerate={regenerate} busy={busy} />
          )}
        </Panel>
      )}

      {stage === 'result' && (
        <>
          {busy && <Panel title="Working"><Loading label={busyLabel} /></Panel>}
          {!busy && resultView === 'debate' && (
            <Panel idx="04" title="Multi-agent debate" sub="Tech, Timeline, and Pitch specialists critique the same idea; the arbiter detects and resolves conflicts.">
              <DebatePanel debate={debate} />
            </Panel>
          )}
          {!busy && resultView === 'alignment' && (
            <Panel idx="05" title="Semantic alignment gate" sub="Cosine similarity between the original goal and the evolving solution (Sentence Transformers — no LLM).">
              <AlignmentGate debate={debate} />
            </Panel>
          )}
          {!busy && resultView === 'persona' && (
            <Panel idx="06" title="Persona adaptation">
              <PersonaCompare defaultPlan={persona} onAdapt={(p) => api.adaptPersona(projectId, p)} />
            </Panel>
          )}
          {!busy && resultView === 'blueprint' && (
            <Panel idx="07" title="Final blueprint" sub="The converged, human-approved plan.">
              <BlueprintView blueprint={blueprint} />
            </Panel>
          )}
          {!busy && (
            <Panel title="Evaluation vs baseline">
              <Evaluation onRun={() => api.getEvaluation(projectId)} />
            </Panel>
          )}
        </>
      )}
    </div>
  )
}
