# Quickstart: Learning Tracker v2 (Phase 1)

## Run locally

```bash
cd ~/workspace/learning-tracker/backend
.venv/bin/python -m pytest -q            # backend tests (13 in v1 + v2 tests)
.venv/bin/uvicorn app.main:app --reload  # http://localhost:8000/docs

cd ../frontend
npm run build                            # tsc + vite must pass
npm run dev                              # http://localhost:5173
```

## Prove the migration (Phase A, required before any deploy)

```bash
cd backend
# 1. Build a v1-schema DB with fake progress (script lives in backend/tests/
#    as a fixture in test_v2_gates.py; manual equivalent below)
rm -f /tmp/lt-v1.db
.venv/bin/python - <<'EOF'
# create ONLY the v1 tables, insert 1 completed Day + 1 done checklist item
# + 1 quiz attempt, then close. (See test file for the exact script.)
EOF
# 2. Point the app at it and start: DATABASE_URL=sqlite:////tmp/lt-v1.db
#    .venv/bin/uvicorn app.main:app
# 3. Assert: /api/progress returns the same numbers as before,
#    and GET /api/tracks shows the new v2 fields (importance, bug_code, ...).
```

## Smoke-check the new gates locally

```bash
# Day 1 flow (needs backend running on :8000)
curl -s localhost:8000/api/days/1/status | python3 -m json.tool   # 6 gates listed
curl -s -X POST localhost:8000/api/days/1/flow-puzzle \
  -H 'Content-Type: application/json' -d '{"order":[0,1,2,3]}'
curl -s -X POST localhost:8000/api/days/1/bug \
  -H 'Content-Type: application/json' -d '{"line":4,"reason":1}'
curl -s localhost:8000/api/tracks/1/skill-tree | python3 -m json.tool
curl -s localhost:8000/api/progress
```

## Deploy (Phase E)

```bash
# 1. Push via GitHub snapshot flow (local git has no remote; see v1 notes)
# 2. Frontend:
cd frontend && vercel deploy --prod --yes --scope tuan-learning-tracker
# 3. Backend: Render dashboard -> learning-tracker-backend -> Manual Deploy ->
#    Deploy latest commit (auto-deploy does NOT fire on API pushes)
# 4. Live checks:
curl -s https://learning-tracker-backend-z84h.onrender.com/api/health
curl -s https://learning-tracker-backend-z84h.onrender.com/api/progress
curl -s https://learning-tracker-backend-z84h.onrender.com/api/tracks/1/skill-tree | head -c 400
curl -s -o /dev/null -w "%{http_code}\n" https://frontend-ten-smoky-41.vercel.app/
```

## Content completeness check (Phase C)

Every Day must have: `importance` set, `real_world_use` non-empty, ≥2
`pitfalls`, `bug_code` with 5–10 lines, `bug_line` set, 4 `bug_reasons`,
`bug_correct_reason` set, exactly 2 `followup_questions`. A test asserts this
from the seeded DB; a Day missing any of them renders "đang bổ sung" and its
gates cannot pass.
