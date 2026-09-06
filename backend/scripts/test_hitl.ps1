# test_hitl.ps1 - end-to-end check of the human-in-the-loop interrupt/resume.
# Run the backend first:  python -m uvicorn app.main:app --port 8000
# Then:                   powershell -ExecutionPolicy Bypass -File scripts\test_hitl.ps1
$ErrorActionPreference = "Stop"
$base = "http://localhost:8000"
function Pass($m){ Write-Host "PASS: $m" -ForegroundColor Green }
function Fail($m){ Write-Host "FAIL: $m" -ForegroundColor Red; exit 1 }

# 0) health
try { $h = Invoke-RestMethod "$base/health"; Pass "health -> $($h.status), provider=$($h.llm_provider)" }
catch { Fail "backend not reachable at $base ($_)" }

# 1) create project -> should PAUSE at human_review (interrupt_before) and return ideas
$body = @{
  problem_statement = "Students struggle to track assignments and deadlines across courses."
  hackathon_theme   = "education"
  time_limit_hours  = 24
  preferences       = "web app"
  team_members      = @(@{ role = "Full-stack"; skill_level = "intermediate" })
} | ConvertTo-Json
$create = Invoke-RestMethod -Method Post "$base/api/projects" -ContentType "application/json" -Body $body
$projectId = $create.project_id
if (-not $projectId) { Fail "no project_id returned" }
if ($create.status -ne "awaiting_selection") { Fail "expected awaiting_selection, got '$($create.status)'" }
if (-not $create.ideas -or $create.ideas.Count -lt 1) { Fail "no candidate ideas returned" }
$ideaId = $create.ideas[0].id
Pass "create -> project=$projectId, status=awaiting_selection, $($create.ideas.Count) idea(s) [INTERRUPT held]"

# 2) select an idea -> should RESUME past human_review and run to completion
$sel = Invoke-RestMethod -Method Post "$base/api/projects/$projectId/select" -ContentType "application/json" -Body (@{ idea_id = $ideaId } | ConvertTo-Json)
if ($sel.status -ne "completed") { Fail "after select expected completed, got '$($sel.status)'" }
if (-not $sel.blueprint) { Fail "no blueprint after select (pipeline did not finish)" }
Pass "select '$ideaId' -> status=completed, blueprint present [RESUME worked]"

# 3) evaluation -> must be 200 now (previously 422)
try { $eval = Invoke-RestMethod -Method Post "$base/api/projects/$projectId/evaluation"; Pass "evaluation -> 200 OK (no 422)" }
catch { Fail "evaluation still failing: $_" }

Write-Host "`nALL CHECKS PASSED - interrupt held, resume completed, evaluation 200." -ForegroundColor Cyan
