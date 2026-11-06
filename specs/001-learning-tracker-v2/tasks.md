# Tasks: Learning Tracker v2 — Feynman + Skill Tree + Enterprise Context + Anti-AI Gates

**Input**: Design documents from `/specs/001-learning-tracker-v2/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api-v2.md

**Tests**: Included — the spec's success criteria (SC-001–SC-005) require server-side
gate checks, migration proof, and live verification, so tests are mandatory here.

**Organization**: Tasks are grouped by user story. Phase 2 (foundational: data
model + migration) blocks everything. Content authoring (Phase C) is the largest
effort and is split per Module.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US5, or Foundational)

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm the v1 baseline still passes before changing anything

- [ ] T001 Verify baseline: `cd backend && .venv/bin/python -m pytest -q` passes (13 tests) and `cd frontend && npm run build` passes on the current tree
- [ ] T002 [P] Confirm live baseline numbers: `GET /api/progress` on production returns the current counts (record them — deploy verification in Phase N compares against these)

## Phase 2: Foundational — Data model + migration (BLOCKS all stories) ⚠️

**Purpose**: v2 schema exists, migrates safely on top of v1 data, progress provably intact

- [ ] T003 [US1/US2/US3/US4] Add v2 columns to `Day` in `backend/app/models.py`: `importance`, `real_world_use`, `pitfalls` (JSON), `bug_code`, `bug_line`, `bug_reasons` (JSON), `bug_correct_reason`, `followup_questions` (JSON)
- [ ] T004 [US1/US4] Add v2 columns to `DayWork` in `backend/app/models.py`: `flow_puzzle_passed`, `bug_passed`, `self_note`, `followup_answers` (JSON), `summary`
- [ ] T005 [US2] Add `ExtensionTopic` model in `backend/app/models.py` (`track_id`, `related_day_number`, `title`, `description`, `order`)
- [ ] T006 Create `backend/app/migrate.py`: idempotent `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` for every column from T003–T004 (SQLite: check `PRAGMA table_info` first; Postgres: `IF NOT EXISTS`); never UPDATE/DELETE progress rows
- [ ] T007 Wire migration into `backend/app/main.py` lifespan: `migrate(engine)` BEFORE `seed(db)`; `create_all` still creates the new `ExtensionTopic` table
- [ ] T008 [P] Extend `seed_data.py`: add `EXTENSION_TOPICS = []` (content filled in Phase 5) and add the new Day keys with `.get()` defaults in `seed.py::_day_fields` so existing 14 Days seed unchanged
- [ ] T009 Extend `seed.py::_refresh_content` to refresh the new Day fields and `ExtensionTopic` rows (matched by day number / title); assert in code comments that progress rows are untouched
- [ ] T010 [P] Test migration proof in `backend/tests/test_v2_gates.py`: build a v1-schema SQLite DB, insert fake progress (1 completed Day, 1 done checklist item, 1 quiz attempt), run `migrate()` + `seed()`, assert progress is byte-identical and new columns exist
- [ ] T011 Run full backend suite: `pytest -q` passes (13 existing + new migration test)

**Checkpoint**: Foundation ready — v2 schema migrates safely, progress intact, user stories can begin

## Phase 3: User Story 1 — Unified Feynman Day completion (Priority: P1) 🎯 MVP

**Goal**: One 6-gate Day completion rule, server-enforced, with grandfathering

**Independent Test**: Day 1 completes on local server only when all 6 gates pass; missing any gate → 400 naming it; a v1-completed Day stays completed

### Tests for User Story 1 ⚠️ (write FIRST, ensure they FAIL before implementation)

- [x] T012 [P] [US1] Gate-matrix test in `backend/tests/test_v2_gates.py`: each of the 6 gates missing in turn → `POST /days/{id}/complete` returns 400 with that gate named
- [x] T013 [P] [US1] Grandfathering test: `DayWork(completed=True)` with empty v2 fields → status still `completed=True`, complete endpoint returns 200

### Implementation for User Story 1

- [x] T014 [US1] Rewrite `evaluate_day_gates` in `backend/app/services.py`: 7 gates → 6 gates (`quiz`, `exercise`, `flow_puzzle`, `bug`, `self_note`, `summary`) with thresholds D-1–D-3 from plan.md; keep `Gate(key, label, passed)` shape
- [x] T015 [US1] Rework `_status()` in `backend/app/routers/days.py` to read the v2 `DayWork` fields; grandfathered `completed=True` short-circuits the gate check
- [x] T016 [US1] Rework `POST /days/{id}/complete` in `backend/app/routers/days.py`: already-completed → 200; otherwise all 6 gates or 400 `{"missing": [...]}`; locked Day → 403
- [x] T017 [US1] Extend `DayWorkIn`/`DayWorkOut` in `backend/app/schemas.py` with `self_note`, `followup_answers`, `summary` (+ keep v1 fields). CORRECTION (2026-11-06): length validation is enforced by the gates at status/complete time, NOT by PUT — strict PUT validation would break saving drafts incrementally. Thresholds unchanged.
- [x] T018 [US1] Extend `DayOut` in `backend/app/schemas.py` + `_day_out` in `backend/app/routers/tracks.py` with the v2 Day fields (importance, real_world_use, pitfalls, bug fields, followup_questions)

**Checkpoint**: US1 fully functional and testable independently — the 6-gate rule works end to end on the API

## Phase 4: User Story 2 — Visual Skill Tree (Priority: P1)

**Goal**: Skill-tree page with 4 states + sequential unlock, enforced server-side

**Independent Test**: With 0/14 completed, only Day 1 is Available; after completing Day 1, Day 2 becomes Available; submitting work for a locked Day returns 403

### Tests for User Story 2 ⚠️

- [x] T019 [P] [US2] Skill-tree state test in `backend/tests/test_v2_gates.py`: 0 progress → Day 1 `available`, Day 2 `locked`; complete Day 1 → Day 2 `available`; partial work → `in_progress`
- [x] T020 [P] [US2] Lock-enforcement test: `PUT /work` and `POST /quiz` on a locked Day → 403

### Implementation for User Story 2

- [x] T021 [US2] Add unlock computation in `backend/app/services.py`: `day_state(db, day)` + `skill_tree(db, track_id)` deriving state from `DayWork`/quiz attempts and rule D-7
- [x] T022 [US2] Add `GET /api/tracks/{track_id}/skill-tree` in `backend/app/routers/tracks.py` returning `SkillTreeOut` (modules → days with state + gates x/6 → extension topics with `unexplored`)
- [x] T023 [US2] Enforce lock in `backend/app/routers/days.py`: quiz submit, work save, puzzle submit, bug submit on a locked Day → 403
- [x] T024 [US2] Frontend: add `#/tree` skill-tree page in `frontend/src/App.tsx` + API calls/types in `frontend/src/api.ts` (nodes with 4 states, locked nodes not clickable, extension nodes with explanation)
- [x] T025 [US2] Frontend: link the tree from the dashboard hero in `frontend/src/App.tsx`; style nodes in `frontend/src/index.css`

**Checkpoint**: US1 + US2 both work — gates + tree + unlock agree with each other

## Phase 5: User Story 3 — Enterprise Context Card (Priority: P2)

**Goal**: Every Day has a business-context card (importance, real-world use, pitfalls)

**Independent Test**: Every Day in `/api/tracks` has a non-empty card with ≥2 pitfalls; Day 1's card mentions validation in plain language

- [x] T026 [US3] Author Module 1 cards (Day 1–7) in `backend/app/seed_data.py`: importance + real-world use + ≥2 pitfalls per Day, hand-written Vietnamese with correct diacritics
- [x] T027 [US3] Author Module 2 cards (Day 8–12) in `backend/app/seed_data.py` (same bar as T026)
- [x] T028 [US3] Author Module 3 cards (Day 13–14) in `backend/app/seed_data.py` (same bar as T026)
- [x] T029 [P] [US3] Content-completeness test in `backend/tests/test_v2_gates.py`: assert every Day has card + bug + 2 follow-ups after seeding, else fail (a Day missing content must render "đang bổ sung")
- [x] T030 [US3] Frontend: render the Enterprise Context Card on the Day page in `frontend/src/App.tsx` (importance badge, real-world use, pitfalls list); style in `frontend/src/index.css`

**Checkpoint**: US3 works — cards exist for all 14 Days and render correctly

## Phase 6: User Story 4 — Three anti-AI gates (Priority: P2)

**Goal**: Flow Puzzle, Spot the Bug, Self-Note (paste blocked) as server-checked gates

**Independent Test**: Wrong puzzle order → fail with first-wrong position; right bug line + wrong reason → fail; paste into Self-Note does nothing; too-short note → 400

### Tests for User Story 4 ⚠️

- [x] T031 [P] [US4] Puzzle test: wrong order → `passed: false` + `first_wrong_position`; right order → `passed: true` and `DayWork.flow_puzzle_passed` set
- [x] T032 [P] [US4] Bug test: right line + wrong reason → fail; right line + right reason → pass and `DayWork.bug_passed` set
- [x] T033 [P] [US4] Self-note validation test: 1-sentence / <80-char note → 400; paste is client-side only (no server test needed)

### Implementation for User Story 4

- [x] T034 [US4] Add `POST /api/days/{id}/flow-puzzle` in `backend/app/routers/days.py`: compare submitted index order against stored `flow_steps`; set `flow_puzzle_passed` on success; 404/403 as per contracts/api-v2.md
- [x] T035 [US4] Add `POST /api/days/{id}/bug` in `backend/app/routers/days.py`: validate line AND reason; return which half was right on failure; set `bug_passed` on success
- [x] T036 [US4] Author Module 1 bug snippets + 2 follow-up questions per Day (Day 1–7) in `backend/app/seed_data.py`: 5–10 lines, exactly 1 unambiguous wrong line, 4 reasons
- [x] T037 [US4] Author Module 2 bug snippets + follow-ups (Day 8–12) in `backend/app/seed_data.py` (same bar as T036)
- [x] T038 [US4] Author Module 3 bug snippets + follow-ups (Day 13–14) in `backend/app/seed_data.py` (same bar as T036)
- [x] T039 [US4] Author extension topics (`EXTENSION_TOPICS` in `backend/app/seed_data.py`, ≥1 per Module, e.g. Bcrypt after login basics) + seed refresh covers them (see T009)
- [x] T040 [US4] Frontend: Flow Puzzle UI in `frontend/src/App.tsx` (click/drag to order steps, submit, retry on fail) + API in `frontend/src/api.ts`
- [x] T041 [US4] Frontend: Spot the Bug UI in `frontend/src/App.tsx` (click a line, pick a reason, show which half was right) + API in `frontend/src/api.ts`
- [x] T042 [US4] Frontend: Self-Note textarea in `frontend/src/App.tsx` with paste blocked (`onPaste` preventDefault + hint text) + Feynman flow section (concept → explain → follow-ups → relearn pointer → re-explain → final summary with the 5 derived self-test questions)
- [x] T043 [US4] Frontend: interactive flow diagram on the Day page (step-through of `flow_steps`, reusing existing data, no static images); replace the 7-gate display with the 6-gate display (x/6)

**Checkpoint**: US4 works — all three gates pass/fail correctly through the UI

## Phase 7: User Story 5 — Admin via repo (Priority: P3)

**Goal**: Adding a Day/Track or editing content via repo + redeploy, without losing progress

**Independent Test**: Add 1 Day via seed, redeploy locally, `/api/progress` numbers unchanged and the new Day appears in the tree

- [ ] T044 [US5] Verify admin path end to end on local: add 1 Day to Module 1 in `seed_data.py`, run server, confirm the Day appears and `/api/progress` is unchanged; then revert the test Day (it was a test, not content)
- [ ] T045 [US5] Document the admin path in `README.md` (edit seed → push → Vercel redeploy → Render manual deploy → live checks); MCP admin stays phase 2 (not in this phase)

**Checkpoint**: All user stories independently functional

## Phase 8: Polish & Deploy

**Purpose**: Full verification and production deploy

- [ ] T046 Run `quickstart.md` validation end to end locally: pytest, build, migration proof, local click-through of Day 1 full 6-gate flow
- [ ] T047 [P] Read back every new Vietnamese string added in Phases 5–6 (diacritics by eye, no scripts); fix anything wrong before push
- [ ] T048 Push to GitHub (snapshot push, as in v1)
- [ ] T049 Redeploy frontend: `vercel deploy --prod --yes --scope tuan-learning-tracker`
- [ ] T050 Manually deploy backend on Render (auto-deploy does not fire on API pushes) and wait for Live
- [ ] T051 Live verification: `/api/health`, `/api/progress` (numbers equal the T002 baseline), `/api/tracks` (v2 fields present, accented), `/api/tracks/1/skill-tree`, Day 1 gate flow on the production site
- [ ] T052 Report to Tuan with the live link + what changed vs v1

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — baseline check first.
- **Phase 2 (Foundational)**: Depends on Phase 1 — BLOCKS all user stories.
- **Phase 3 (US1)**: Depends on Phase 2. Delivers the MVP (unified gates).
- **Phase 4 (US2)**: Depends on Phase 2 + T014–T016 (gate/complete logic); can overlap with Phase 3 after T015.
- **Phase 5 (US3)**: Depends on Phase 2 (schema) — content only; can run in parallel with Phases 3–4.
> Phase C done 06/11/2026 (local, production NOT touched): 14 Days authored in `seed_data.py` via per-module fragments + merge script; content-completeness test T029 passes; pytest 24 passed; smoke check on temp DB: Day 1 card/bug/follow-ups + skill tree show correctly. Two fixes found during Phase C: (1) merge script's triple-quoted `bug_code` broke on code ending in `"` (Day 3) — repaired by switching to `repr()`; (2) skill-tree endpoint attached ALL extension topics to EVERY module — fixed in `routers/tracks.py` to filter by the module's day range (2 per module, 6 total).

> Phase 6 endpoints done 06/11/2026 (local, production NOT touched): `POST /api/days/{id}/flow-puzzle` and `POST /api/days/{id}/bug` per contracts/api-v2.md; tests written first (9 failed, 2 passed) then implementation; pytest 35 passed. Correction vs T033 wording: self-note length is NOT validated by PUT /work (drafts must save) — it is enforced by the gate at POST /complete (400 with the self-note gate listed), per the T017 correction. Test fix during the run: an empty Day used to test the 400 path must sort before Day 1 (number 0), otherwise the 403 lock fires first.

> Phase D done 06/11/2026 (local, production NOT touched): skill-tree page `#/tree` (4 node states, locked nodes disabled, dashed extension nodes) linked from dashboard hero + nav; Enterprise Context Card, step-through flow diagram, Flow Puzzle (click-to-order), Spot the Bug (click line + reason, names which half was right), Feynman section (paste-blocked self-note, 2 follow-ups, summary, 5 self-test recap) on the Day page; 7-gate display replaced by 6-gate display everywhere (footer, hero, Day header, gates card). Decisions: (1) the v1 "Kiểm tra hiểu bài" card (explain/flow/role/variant) was REMOVED from the Day page — those fields are no longer gates and the unified Feynman section replaces them; (2) `bug_line`/`bug_correct_reason` are deliberately NOT in the frontend `Day` type — the answer key never reaches the browser. Verification: `npm run build` (tsc + vite) passes; remote-browser check was IMPOSSIBLE (remote browser rejects localhost, localtunnel 403, cloudflared TLS failure) — verified instead with a local jsdom render of the production build against a temp backend: tree page (Đã mở/Chưa mở/Mở rộng) and Day 1 page (enterprise card, Bước 1/4, puzzle, bug, Feynman, 6 cổng) all render with zero JS errors.

- **Phase 6 (US4)**: Depends on Phase 2 (schema) + T014 (gates); puzzle/bug endpoints need the gate shape; content tasks T036–T039 can run in parallel with Phases 3–5.
- **Phase 7 (US5)**: Depends on Phases 2–6 working locally.
- **Phase 8 (Polish & Deploy)**: Depends on all desired stories complete; needs Tuan's approval before T048–T051 (push/deploy).

### Within Each User Story

- Tests FIRST, ensure they FAIL before implementation.
- Models before services; services before endpoints; endpoints before frontend.
- Content tasks (T026–T028, T036–T039) are hand-written and read back — no scripts.

### Parallel Opportunities

- T008, T010 (after T006), T019–T020, T031–T033 can run in parallel (different files).
- Content authoring per Module (T026/T027/T028, T036/T037/T038) can run in parallel.
- Frontend tasks within a story (T040–T043) share `App.tsx` — do sequentially, not in parallel.

## Implementation Strategy

### MVP First (US1 only)

1. Phase 1 → Phase 2 → Phase 3.
2. **STOP and VALIDATE**: 6-gate rule works on the API; grandfathering holds.
3. Then add US2 → US3 → US4 → US5 in order, validating each checkpoint.

### Notes

- [P] tasks = different files, no dependencies.
- Commit after each task or logical group; do not push/deploy until Phase 8 (T048+), which needs Tuan's approval.
- Stop at any checkpoint to validate the story independently.
- Never wipe progress: no UPDATE/DELETE on `day_work`, `quiz_attempts`, `checklist_items`, `journal_entries` in any task.
