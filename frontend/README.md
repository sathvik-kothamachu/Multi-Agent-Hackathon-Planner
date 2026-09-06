# Frontend — Multi-Agent Hackathon Planner

React 18 + Vite single-page client for the planner pipeline. It walks the user
through the mandated workflow and visibly surfaces every research contribution:

1. **Setup** — problem, theme, time limit, team profile
2. **Idea Generation** — up to 3 candidates
3. **Human Review** — select / modify / regenerate (never auto-selected)
4. **Multi-Agent Debate** — Tech / Timeline / Pitch analyses + detected conflicts
5. **Alignment Gate** — the signature cosine-similarity meter vs the original goal
6. **Persona Adaptation** — the same plan re-explained per skill level
7. **Final Blueprint** — the converged plan
   plus an **Evaluation** panel: proposed pipeline vs single-shot baseline.

A persistent metrics bar shows LLM calls, tokens, latency, and debate rounds.

## Develop

```bash
npm install
npm run dev        # http://localhost:5173  (proxies /api -> http://localhost:8000)
```

Start the backend separately (`uvicorn app.main:app --reload` in `../backend`).
For a zero-key demo, run the backend with `LLM_PROVIDER=mock`.

## Build

```bash
npm run build      # -> dist/
npm run preview
```

## Offline check

```bash
npm run check      # node scripts/check_delims.mjs — bracket balance across src/
```

## API contract

All calls are relative (`/api/...`) so the same build works behind the Vite dev
proxy and the nginx reverse proxy in Docker. See `src/api.js`. Field names mirror
the backend Pydantic schemas exactly (`team_members`, `idea_id`, `idea`, `persona`).
