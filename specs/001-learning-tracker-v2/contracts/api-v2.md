# API Contracts: Learning Tracker v2 (Phase 1)

Base: same as v1 (`/api`, JSON). All v1 endpoints keep their paths and response
shapes; v2 only adds fields/endpoints. `DayStatusOut` keeps `{day_id, completed,
best_quiz_score, best_quiz_total, quiz_passed, gates[], all_gates_passed, missing[]}`
— the `gates` list now has 6 entries with keys
`quiz | exercise | flow_puzzle | bug | self_note | summary`.

## New: Skill tree

### `GET /api/tracks/{track_id}/skill-tree`

Response `SkillTreeOut`:

```json
{
  "track_id": 1,
  "modules": [
    {
      "module_id": 1, "title": "Module 1 — FastAPI: viết API từ đầu", "order": 1,
      "days": [
        {"day_id": 1, "number": 1, "title": "Day 1 — ...", "state": "available",
         "gates_passed": 0, "gates_total": 6}
      ],
      "extensions": [
        {"id": 1, "title": "Mã hóa mật khẩu Bcrypt",
         "description": "...", "related_day_number": 3, "state": "unexplored"}
      ]
    }
  ]
}
```

`state` ∈ `mastered | in_progress | available | locked | unexplored`.
Rules: `mastered` ⇔ `DayWork.completed`; `in_progress` ⇔ any gate passed or any
work field non-empty; `available` ⇔ previous Day in Module completed (Day 1 of
Module 1 always available; first Day of a later Module ⇔ previous Module fully
completed); otherwise `locked`.

## New: Flow Puzzle

### `POST /api/days/{day_id}/flow-puzzle`

Request: `{"order": [2, 0, 1, 3]}` — learner's ordering as indexes into the Day's
stored `flow_steps`.

Response 200: `{"passed": true, "correct_order": [0, 1, 2, 3]}` (also sets
`DayWork.flow_puzzle_passed`).

Response 200 with `passed: false` when wrong (NOT an error — retry allowed):
`{"passed": false, "first_wrong_position": 1}` — names the first position where
the learner's order diverges, no full answer given.

Errors: 404 Day not found; 403 Day locked (D-7).

## New: Spot the Bug

### `POST /api/days/{day_id}/bug`

Request: `{"line": 4, "reason": 1}` — 0-based line index + reason option index.

Response 200: `{"passed": true}` (sets `DayWork.bug_passed`) or
`{"passed": false, "line_correct": true, "reason_correct": false}` — tells the
learner which half was right, so they can re-read the relevant theory.

Errors: 404 Day not found; 403 Day locked.

## Extended: Day work

### `PUT /api/days/{day_id}/work`

v1 fields unchanged. New optional fields (all default `""` / `[]`):

```json
{
  "exercise_submission": "...", "test_result": "...",
  "explain_answer": "...", "flow_answer": "...", "role_answer": "...",
  "variant_answer": "...",
  "self_note": "...", "followup_answers": ["...", "..."], "summary": "..."
}
```

Validation (400 with a clear message): `self_note` must be ≥2 sentences AND ≥80
non-space characters; each `followup_answers` entry ≥20 non-space characters;
`summary` ≥80 non-space characters. `GET /days/{id}/work` returns the same
extended shape.

### `GET /api/days/{day_id}/status` — unchanged path, new gate list

`gates` (6): `quiz` (best score ≥75%), `exercise` (exercise + test_result each
≥20 chars), `flow_puzzle`, `bug`, `self_note` (note + both follow-up answers
valid), `summary` (≥80 chars). `all_gates_passed` and `missing[]` as in v1.

### `POST /api/days/{day_id}/complete` — unchanged path, new rules

- Already `completed=True` → 200 with current status (grandfathered, no re-check).
- Otherwise all 6 gates must pass, else 400 `{"missing": [...]}`.
- Locked Day → 403.

## Extended: Tracks

### `GET /api/tracks`, `GET /api/tracks/{track_id}`

`DayOut` gains: `importance`, `real_world_use`, `pitfalls[]`, `bug_code`,
`bug_line`, `bug_reasons[]`, `bug_correct_reason`, `followup_questions[]`.
**Note**: `bug_line` and `bug_correct_reason` (the answers) are returned to the
client — the frontend needs them only after a correct submission for the
explanation view; until the gate passes, the frontend MUST NOT reveal them.
Server does not enforce this; it is a frontend rule, recorded here so the
reviewer checks it. (Alternative considered — a separate "reveal" endpoint —
rejected as over-engineering for a single-user app; the learner cheating the
gate only cheats themself, and the variant answer remains the real check.)

## Unchanged

`POST /days/{id}/quiz`, `GET /api/checklist`, `PUT /api/checklist/{id}`,
`GET/POST/DELETE /api/journal`, `GET /api/progress`, `GET /api/method`,
`GET /api/health` — no changes.
