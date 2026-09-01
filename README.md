# Multi-Agent Hackathon Planner

A research prototype that turns a hackathon problem statement into a **validated, team-adaptive project blueprint** through a human-in-the-loop, debate-driven multi-agent pipeline.

It is deliberately *not* an autonomous coding agent. It is a **planning** system built to test three specific research claims and to measure them against a single-LLM baseline.

```
User Input → Idea Generation → Human Review → Multi-Agent Debate
   → Conflict Resolution → Alignment Gate → (Re-debate ≤3) → Persona Adaptation → Final Blueprint
```

## Research objectives

Every feature exists to serve one of these three claims:

1. **Debate-driven multi-agent coordination.** Three specialists (Tech, Timeline, Pitch) critique the *same* idea, an arbiter detects genuine conflicts between technology, schedule, pitch, and the original requirements, and the plan is revised to resolve them. This is *detect → critique → resolve → converge*, not parallel generation with a merge.

2. **Semantic alignment-gated convergence.** After each debate round the evolving solution is embedded (`all-MiniLM-L6-v2`) and compared to the original problem statement by **cosine similarity**. If the score falls below a configurable threshold (default `0.75`), another debate round is triggered — capped at **3 rounds** so it can never loop forever. No LLM is used to judge similarity.

3. **Persona-adaptive planning.** The *same* underlying plan is re-expressed for **beginner / intermediate / advanced** teams — only the depth, terminology, and hand-holding change, never the substance.

## Why a human stays in the loop

After idea generation the graph **pauses** (LangGraph `interrupt()`), and nothing proceeds until the user **selects**, **modifies**, or **regenerates**. Ideas are never auto-selected. The debate, gate, and persona stages run only on an idea a human chose.

## The four agents

| Agent | Responsibility | Output (structured JSON) |
|-------|----------------|--------------------------|
| **Idea Generator** | Propose ≤3 candidate ideas | title, problem, solution, target users |
| **Tech Stack Architect** | Technical feasibility + stack | feasibility, stack, risks, critique |
| **Timeline Scheduler** | Fit within the time budget | milestones, fit verdict, risks, critique |
| **Pitch Specialist** | Value, differentiation, impact | value prop, differentiation, pitch structure, critique |

No other agents exist. Conflict detection, routing, cosine similarity, round counting, and timeline arithmetic are all **deterministic code** — not LLM calls.

> **Setting it up?** [`RUNNING.md`](./RUNNING.md) has step-by-step Windows/macOS commands, provider choices, and troubleshooting.

## Quick start (Docker, zero API key)

The stack ships with a deterministic **mock LLM** so it runs end-to-end with no key:

```bash
docker compose up --build
# UI:       http://localhost:8080
# API docs: http://localhost:8000/docs
```

To use a real model, drop a `.env` beside `docker-compose.yml`:

```env
LLM_PROVIDER=google
MODEL_NAME=gemini-1.5-flash
LLM_API_KEY=your_key_here
```

> The backend image bundles `sentence-transformers` (and therefore torch), so the first build is large and the embedding model downloads on the first alignment call.

## Local development

**Backend**

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env           # set LLM_PROVIDER=mock for a keyless demo
uvicorn app.main:app --reload  # http://localhost:8000
```

**Frontend**

```bash
cd frontend
npm install
npm run dev                    # http://localhost:5173 (proxies /api → :8000)
```

## Testing & offline verification

The pure-logic core (cosine similarity, conflict detection, routing, persona derivation, baseline comparison) is dependency-light and verifiable without a network or model download:

```bash
cd backend
python tests/run_offline.py         # stdlib runner over pure-logic modules
python -m compileall app            # syntax-checks the whole backend

cd ../frontend
npm run check                       # bracket-balance check across src/
```

The full graph (LangGraph + Pydantic) is covered by `tests/test_integration_graph.py`, which runs under `pytest` once dependencies are installed (it self-skips if they are absent):

```bash
cd backend && pytest -q
```

## API surface

All routes are under `/api/projects`.

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/api/projects` | Create project + generate ideas (then pauses) |
| `POST` | `/api/projects/{id}/regenerate` | Regenerate candidate ideas |
| `POST` | `/api/projects/{id}/select` | Select an idea → run debate/gate/persona |
| `POST` | `/api/projects/{id}/modify` | Edit an idea → run the pipeline on it |
| `GET`  | `/api/projects/{id}/debate` | Agent analyses, conflicts, alignment history |
| `GET`  | `/api/projects/{id}/blueprint` | Final converged blueprint |
| `GET`  | `/api/projects/{id}/metrics` | Token / call / latency / round metrics |
| `POST` | `/api/projects/{id}/persona` | Re-adapt the plan for a skill level |
| `POST` | `/api/projects/{id}/baseline` | Run + cache the single-shot baseline |
| `POST` | `/api/projects/{id}/evaluation` | Proposed vs baseline comparison report |
| `GET`  | `/api/projects` | List projects |

## Token discipline

LLM calls are treated as expensive: ≤3 ideas, ≤3 debate rounds, concise prompts, structured JSON with Pydantic validation, only relevant state passed between agents (never full transcripts), and **no LLM** used for similarity, routing, validation, or arithmetic. Every run records LLM calls, input/output/total tokens, latency, and debate rounds, all surfaced live in the UI and in the evaluation report.

## Evaluation

The **Evaluation** panel (and `POST /evaluation`) runs the same problem through a single-LLM baseline and reports both side by side — calls, tokens, latency, debate rounds, conflicts detected/resolved, and final alignment. All numbers come from real runs; none are fabricated. See [`ARCHITECTURE.md`](./ARCHITECTURE.md) for the full evaluation design.

## Project layout

```
backend/    FastAPI + LangGraph + agents + alignment + baseline + tests
frontend/   React + Vite SPA (stage stepper, debate view, alignment meter)
docker-compose.yml   backend (uvicorn) + frontend (nginx, proxies /api)
ARCHITECTURE.md      graph, state, schema, token & evaluation strategy
```

## Stack

React + Vite · Python + FastAPI · LangGraph (state + interrupt + SQLite checkpointer) · Pydantic v2 · Sentence-Transformers + scikit-learn cosine · SQLite · Docker. One configurable LLM provider (Google Gemini), with a mock provider for offline/deterministic runs.
