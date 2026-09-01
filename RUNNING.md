# Running the project

Windows-focused (PowerShell). Substitute `source .venv/bin/activate` and `cp` on macOS/Linux.

---

## Before you start — two first-run downloads

Neither is a bug; both happen once and then cache. Plan for bandwidth and time.

| What | Size | When | Why |
|---|---|---|---|
| `pip install -r requirements.txt` | ~2 GB | first install | `sentence-transformers` pulls in **torch** |
| `all-MiniLM-L6-v2` model | ~90 MB | first alignment call | downloaded from HuggingFace on demand |

**The embedding model is needed even with `LLM_PROVIDER=mock`.** The mock replaces the *LLM*, not the *alignment gate* — the gate is real cosine similarity by design (research objective 2), so it always loads the real model. You need network access for the first run that reaches the alignment stage.

---

## Prerequisites

- **Python 3.10+** — `python --version`
- **Node 18+** — `node --version`
- **Docker Desktop** (only for the Docker route)

---

## Route A — Docker (one command, no API key)

Best for a demo or a clean check that everything wires together.

```powershell
cd multi-agent-hackathon-planner
docker compose up --build
```

| | |
|---|---|
| UI | http://localhost:8080 |
| API docs (Swagger) | http://localhost:8000/docs |

The first build is slow (torch). Compose defaults to `LLM_PROVIDER=mock`, so it runs with no key.

To use real Gemini, create `.env` **next to `docker-compose.yml`** (not in `backend/`):

```env
LLM_PROVIDER=google
MODEL_NAME=gemini-1.5-flash
LLM_API_KEY=your_key_here
```

Then `docker compose up --build` again.

Stop with `Ctrl+C`; `docker compose down` removes containers. Project data lives in the `planner-data` volume and survives restarts — `docker compose down -v` wipes it.

---

## Route B — Local dev (what you want while implementing)

Hot reload on both sides. **Two terminals, both stay open.**

### Terminal 1 — backend

```powershell
cd multi-agent-hackathon-planner\backend

python -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt

copy .env.example .env
```

Now open `backend\.env` and set the provider:

```env
# keyless deterministic runs — start here
LLM_PROVIDER=mock

# ...or real Gemini
# LLM_PROVIDER=google
# LLM_API_KEY=your_key_here
```

Start it:

```powershell
uvicorn app.main:app --reload --port 8000
```

Check: http://localhost:8000/health → `{"status":"ok"}`

### Terminal 2 — frontend

```powershell
cd multi-agent-hackathon-planner\frontend

npm install
npm run dev
```

Open **http://localhost:5173**.

Vite proxies `/api` → `http://localhost:8000`, so the frontend needs no URL config, and CORS never comes into play.

---

## Which provider to use while implementing

| | `mock` | `google` |
|---|---|---|
| API key | none | required |
| Cost | zero | real tokens |
| Output | fixed, deterministic | varies per run |
| Use it for | UI work, debugging the graph, tests, demos | validating prompt quality, collecting research data |

Develop against `mock` — it's free, instant, and reproducible, which makes UI and state bugs far easier to isolate. Switch to `google` only when you're specifically evaluating what the LLM produces. Get a key from Google AI Studio.

---

## Walking the pipeline in the UI

1. **Setup** — fill in the problem statement (there's a *Use example* button), theme, time limit, and team members with skill levels. Submit.
2. **Human review** — up to 3 ideas appear and the backend **pauses here**. Nothing advances until you act: **Select**, **Modify**, or **Regenerate**.
3. On select/modify the pipeline runs debate → conflicts → alignment gate → (re-debate if score < 0.75, max 3 rounds) → persona → blueprint.
4. Use the **stepper at the top** to move between Debate, Alignment, Persona, and Blueprint views of the finished run.
5. **Evaluation** panel → *Run evaluation* runs the single-LLM baseline and shows both side by side. Costs 1 extra LLM call, then caches.

The metrics bar (calls, tokens, latency, rounds) updates live at every step.

---

## Tests

```powershell
cd backend
.venv\Scripts\activate
pytest -q
```

Verification that needs no dependencies at all:

```powershell
python -m compileall app        # syntax-check the whole backend
python tests\run_offline.py     # 39 pure-logic tests, stdlib only

cd ..\frontend
npm run check                   # bracket balance across src/
```

---

## Tuning the research knobs

In `backend\.env` — restart uvicorn after editing:

```env
ALIGNMENT_THRESHOLD=0.75   # raise to force more re-debate rounds
MAX_DEBATE_ROUNDS=3        # hard cap on the loop
MAX_IDEAS=3                # candidates per generation
```

Raising `ALIGNMENT_THRESHOLD` to something like `0.9` is the easiest way to *see* the re-debate loop fire, since most solutions won't clear that bar on round 1.

---

## Troubleshooting

**`uvicorn` not recognized** — the venv isn't active. Re-run `.venv\Scripts\activate`; your prompt should show `(.venv)`.

**PowerShell blocks activation** (`running scripts is disabled`) — run once as your user:
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

**Frontend loads but every call fails** — the backend isn't running or isn't on port 8000. Confirm http://localhost:8000/health, and that `vite.config.js` proxies to that port.

**First idea generation hangs a long time** — that's the one-time model download. Watch the backend terminal for HuggingFace progress.

**`LLM_API_KEY` errors while using mock** — `LLM_PROVIDER` isn't actually `mock`. Confirm `backend\.env` exists (not just `.env.example`) and holds `LLM_PROVIDER=mock`.

**Want a clean slate** — stop the backend and delete `backend\hackathon_planner.db` and `backend\checkpoints.sqlite`. They're recreated at startup. The checkpoint DB holds paused graph state, so deleting it drops in-flight projects.

**Port already in use** — `uvicorn app.main:app --reload --port 8001`, and update the proxy target in `frontend\vite.config.js` to match.
