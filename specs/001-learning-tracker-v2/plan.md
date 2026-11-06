# Implementation Plan: Learning Tracker v2

**Branch**: `001-learning-tracker-v2` | **Date**: 2026-11-06 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-learning-tracker-v2/spec.md`

## Summary

Upgrade the live single-user learning tracker (FastAPI + React + SQLAlchemy, 14 Days,
56 quiz questions, 50 checklist items, deployed on Vercel Hobby + Render free +
Neon free Postgres) to v2 without losing any progress: replace the v1 7-gate Day
completion rule with one unified 6-gate Feynman set, add a visual skill tree with
sequential unlock, an Enterprise Context Card per Day, three anti-AI gates (Flow
Puzzle, Spot the Bug, Self-Note with paste blocked), and an interactive flow
diagram. Content for all 14 Days is authored by hand in `seed_data.py`. Admin in v2
stays repo-driven (edit seed → push → redeploy); MCP admin is phase 2 and out of
scope here.

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript + React + Vite (frontend)

**Primary Dependencies**: FastAPI 0.162, SQLAlchemy 2.1, Pydantic 2.14, pytest 9.2,
psycopg 3 (Postgres only); React + Vite (frontend, plain CSS, no component library)

**Storage**: SQLite locally (`DATABASE_URL` unset), PostgreSQL 18 on Neon in
production (`DATABASE_URL` env). No Alembic — schema is created by
`Base.metadata.create_all` in `app.main.lifespan` plus a startup migration helper
(see Risks).

**Testing**: backend `pytest` (`backend/tests/`); frontend `npm run build` (tsc +
vite); local SQLite smoke check of `/api/tracks`; live curl checks after deploy.

**Target Platform**: Web, single user (Tuan), desktop + mobile responsive.

**Project Type**: Web application (monorepo: `backend/` + `frontend/`).

**Performance Goals**: No new performance target — one user, 14 Days. Render free
sleeps after ~15 min idle; first request after idle may take ~50 s (accepted, show
a loading state, not an error).

**Constraints**: Free tiers only (Vercel Hobby, Render free, Neon free). Vietnamese
UI with correct diacritics, verified by reading, never by an auto-accent script.
Progress tables are never wiped (Constitution I). Render does NOT auto-deploy on
pushes made via the GitHub API — backend changes need a manual deploy + live check.

**Scale/Scope**: 1 track, 3 modules, 14 Days, 56 quiz questions in v2 scope. Phase 4
(deploy) and Spring Boot Day splits are separate content backlog, NOT in this plan.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

- [x] I. Progress never wiped — migration adds columns/tables only (`ADD COLUMN IF
  NOT EXISTS`, `create_all` for new tables); no UPDATE/DELETE on progress rows;
  `DayWork.completed=True` is grandfathered and never re-evaluated against new gates.
- [x] II. One unified gate set — 6 gates below replace the v1 7 gates; all enforced
  in `services.evaluate_day_gates` + `POST /days/{id}/complete` (400 + missing list).
  Paste-blocking and drag-drop are UX only, never evidence.
- [x] III. Advisor, not agreeable assistant — plan flags the two open risks below
  honestly instead of hiding them; Vietnamese throughout.
- [x] IV. Honest content, checked by hand — Phase C content is hand-written and
  read back; no accent scripts; no inflated claims.
- [x] V. Tuan approves before implementation — this plan is presented for approval;
  no code is written until he approves plan (tasks.md comes after).
- [x] VI. Free tiers only, simple by default — no new services, no new paid tiers;
  no new tables per skill (generic Track → Module → Day reused).
- [x] VII. Evidence before completion — each phase ends with pytest + build + API
  checks; final verification is live curl against production URLs.

## Decisions Locked in This Plan (numbers the spec left open)

- **D-1 Self-Note**: ≥2 sentences AND ≥80 non-space characters, else server rejects.
- **D-2 Feynman follow-ups**: exactly 2 per Day (stored as JSON list on Day);
  each answer needs ≥20 non-space characters.
- **D-3 Final summary**: ≥80 non-space characters.
- **D-4 Flow Puzzle**: reuses the Day's existing `flow_steps`; frontend shuffles
  display order; learner submits the ordered list of step indexes; server compares
  against stored order. No new content field needed for steps.
- **D-5 Spot the Bug**: 1 snippet per Day, 5–10 lines, exactly 1 wrong line, 4
  reason options, 1 correct reason. Server validates line AND reason.
- **D-6 The 5 self-test questions** in the Feynman final summary are derived, not
  stored: the Day's 4 quiz questions + its variant question.
- **D-7 Sequential unlock**: Day N unlocks when Day N−1 in the same Module is
  completed; first Day of a Module unlocks when the previous Module is fully
  completed; Day 1 is always available. Lock is enforced server-side (locked Day
  returns 403 on work/quiz submit, not just hidden in UI).
- **D-8 v1 gate fields retired, not deleted**: `explain_answer`, `flow_answer`,
  `role_answer` columns stay in `DayWork` (old answers remain readable) but are no
  longer gates. The role understanding is now checked via the Enterprise Context
  Card + variant/follow-up answers.

## Project Structure

### Documentation (this feature)

```text
specs/001-learning-tracker-v2/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── api-v2.md
└── tasks.md             # Phase 2 output (NOT created by plan; needs plan approval)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── models.py        # Day += enterprise card + puzzle/bug fields; DayWork += v2 gates; ExtensionTopic (new)
│   ├── schemas.py       # DayOut / DayWorkIn-Out / DayStatusOut += v2 fields; SkillTreeOut (new)
│   ├── services.py      # evaluate_day_gates: 7 gates -> 6 gates; unlock computation
│   ├── repositories.py  # get_work/upsert_work unchanged shape; + helpers for puzzle/bug attempts
│   ├── seed.py          # _refresh_content extended to new content fields
│   ├── seed_data.py     # 14 Days += enterprise card, bug snippet, follow-ups, extension topics
│   ├── migrate.py       # NEW: idempotent ALTER TABLE ... ADD COLUMN IF NOT EXISTS, run in lifespan
│   └── routers/
│       ├── days.py      # status/work/complete reworked for 6 gates; + puzzle/bug submit endpoints
│       ├── tracks.py    # _day_out += v2 fields; + GET /tracks/{id}/skill-tree
│       ├── progress.py  # unchanged (counts only)
│       └── ...
└── tests/
    ├── test_services.py # gate evaluation incl. grandfathering
    ├── test_api_gate.py # complete endpoint, 400 + missing list
    └── test_v2_gates.py # NEW: puzzle/bug/self-note/summary/skill-tree/migration

frontend/
├── src/
│   ├── api.ts           # types + calls for skill-tree, puzzle, bug, extended work
│   ├── App.tsx          # SkillTree page, Day page Feynman flow, puzzle/bug/self-note UI,
│   │                    # enterprise card, interactive flow diagram, locked states
│   └── index.css        # skill-tree, puzzle, bug, card styles (extends v1 design system)
└── ...

**Structure Decision**: Keep the existing monorepo layout and layering
(router / service / repository / schemas). No new backend service, no new
frontend framework, no per-skill tables.
```

## Implementation Phases

### Phase A — Data model + migration (backend only, no UI change)

1. Add columns/tables per `data-model.md` (Day enterprise card + bug fields +
   follow-ups; DayWork v2 gate fields; `ExtensionTopic` table).
2. Add `backend/app/migrate.py`: idempotent `ALTER TABLE ... ADD COLUMN IF NOT
   EXISTS` for every new column; new tables via existing `create_all`. Call it in
   `lifespan` BEFORE `seed()`. Never touch progress rows.
3. Prove the migration on a copy of a v1-schema SQLite DB: create v1 schema, insert
   fake progress (1 completed Day, 1 done checklist, 1 quiz attempt), run the app,
   assert progress is byte-identical and new columns exist.
4. Tests: `test_v2_gates.py` migration test + existing 13 tests still pass.

### Phase B — Gate logic + API (backend only)

1. Rewrite `services.evaluate_day_gates` to the 6-gate set (D-1–D-3 thresholds);
   keep the `Gate(key, label, passed)` shape so the frontend contract is stable.
2. Grandfathering: `_status()` returns `completed=True` as stored; `POST
   /complete` on an already-completed Day returns current status (no re-check).
   Uncompleted Days are evaluated against the 6 new gates only.
3. New endpoints (see `contracts/api-v2.md`): `POST /days/{id}/flow-puzzle`,
   `POST /days/{id}/bug`, `GET /tracks/{id}/skill-tree`; extend `PUT /days/{id}/work`
   with the new fields; lock enforcement (D-7) in days router.
4. Extend `seed._refresh_content` to the new content fields (match by day number /
   position); progress untouched.
5. Tests: gate matrix (each gate missing → 400 with that gate named), puzzle
   wrong-order → fail, bug right-line-wrong-reason → fail, self-note too short →
   400, locked Day submit → 403, grandfathered Day → still complete.

### Phase C — Content authoring (14 Days, hand-written)

1. For each of the 14 Days, author in `seed_data.py`: Enterprise Context Card
   (importance + plain-language real-world use + ≥2 pitfalls), 1 BugSnippet
   (5–10 lines, 1 wrong line, 4 reasons), 2 follow-up questions, extension
   topics (Unexplored Scope) per Module.
2. Flow Puzzle needs no new content (reuses `flow_steps`, D-4).
3. Verification: read every new string back (Vietnamese diacritics by eye, no
   scripts); run the local SQLite smoke check and eyeball `/api/tracks` output;
   assert every Day has a card + bug + 2 follow-ups, else the Day shows
   "đang bổ sung" and its gates cannot pass.
4. This phase is the largest effort — content, not code. It can be split per
   Module (Module 1 first) and reviewed in chunks.

### Phase D — Frontend

1. `api.ts`: new types + calls (skill tree, puzzle, bug, extended work fields).
2. Skill Tree page (`#/` dashboard addition + `#/tree` route): nodes with 4 states
   + locked handling; Unexplored Scope nodes with explanations.
3. Day page rework: Feynman flow section (concept → explain → follow-ups → relearn
   pointer → re-explain → final summary), Enterprise Context Card, interactive flow
   diagram (step-through of `flow_steps`), Flow Puzzle (click/drag to order),
   Spot the Bug (click line + pick reason), Self-Note textarea with paste blocked
   (`onPaste={e => e.preventDefault()}` + note text), gate progress x/6.
4. Keep all existing routes and the 7-gate display replaced by the 6-gate display;
   keep method/checklist/journal pages unchanged.
5. `npm run build` must pass; manual click-through of Day 1 end-to-end on local
   dev server.

### Phase E — Deploy + live verification

1. Push to GitHub (snapshot push, as in v1).
2. Redeploy frontend on Vercel (`vercel deploy --prod --scope tuan-learning-tracker`).
3. Manually deploy backend on Render (auto-deploy does not fire on API pushes)
   and wait for Live.
4. Live checks: `/api/health`, `/api/progress` (must equal pre-deploy numbers),
   `/api/tracks` (accented v2 content present), skill-tree endpoint, complete
   Day 1 flow on the production site.
5. Report to Tuan with the live link.

## Risks

| Risk | Impact | Mitigation |
|---|---|---|
| `create_all` does NOT add columns to the existing Neon tables — new Day/DayWork columns would silently not exist in production | Backend crashes on first v2 request after deploy | Phase A migration helper with explicit `ADD COLUMN IF NOT EXISTS`; prove it on a v1-schema copy before deploy; verify live with a read of the new fields |
| Content volume (14 cards + 14 bug snippets + 28 follow-ups + extension topics), all hand-written Vietnamese | Phase C dominates the work; a rushed snippet teaches the wrong bug | Split per Module, review in chunks; every snippet must have exactly 1 unambiguous wrong line; read-back check before push |
| Sequential unlock changes navigation (v1 lets Tuan open any Day) | Tuan may find it restrictive | Already in the approved spec (D-7); if he dislikes it in use, it becomes a config flag, not a rewrite |
| Paste-blocking is client-side only | A determined user can bypass it; it is not evidence | Stated in spec: evidence is the variant answer + explanation, not the paste block |
| Render manual deploy forgotten | Production stays on v1 backend while frontend expects v2 API | Phase E checklist explicitly includes manual Render deploy + live verification before reporting done |

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| Startup migration helper (`migrate.py`) instead of Alembic | One-file, idempotent `ADD COLUMN IF NOT EXISTS` fits a single-user app with no migration history | Alembic adds a migrations folder, env config, and a new operational step for a 1-user free-tier app |
| New `ExtensionTopic` table instead of stuffing into seed JSON | Unexplored Scope nodes need per-track querying and stable identity for the tree | Seed-only JSON cannot be queried/updated independently of the Day list |

## Verification (per phase)

- Phase A: `pytest -q` (13 existing + new migration test), migration proof on v1-schema copy.
- Phase B: `pytest -q` incl. gate matrix, puzzle/bug, lock, grandfathering; local
  SQLite smoke check of new endpoints via TestClient.
- Phase C: content completeness assertion (every Day: card + bug + 2 follow-ups);
  read-back of all new Vietnamese strings.
- Phase D: `npm run build` pass; local click-through of Day 1 full gate flow.
- Phase E: live curl checks listed above; `/api/progress` unchanged numbers.
