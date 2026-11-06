# Data Model: Learning Tracker v2 (Phase 1)

Derived from `backend/app/models.py` (v1). All changes are additive. No column is
dropped, no progress row is rewritten.

## Changed: `Day` (new content columns)

| Column | Type | Notes |
|---|---|---|
| `importance` | String | `must` \| `should` \| `nice` — Enterprise Context Card level. Default `should`. |
| `real_world_use` | Text | Enterprise card: plain-language real-world application. Default `""`. |
| `pitfalls` | Text (JSON list) | Enterprise card: ≥2 common beginner mistakes. Default `"[]"`. |
| `bug_code` | Text | Spot the Bug snippet, 5–10 lines, stored with `\n` separators. Default `""`. |
| `bug_line` | Integer, nullable | 0-based index of the single wrong line. Default `NULL`. |
| `bug_reasons` | Text (JSON list) | 4 reason options. Default `"[]"`. |
| `bug_correct_reason` | Integer, nullable | Index into `bug_reasons`. Default `NULL`. |
| `followup_questions` | Text (JSON list) | Exactly 2 Feynman follow-up questions. Default `"[]"` (falls back to `variant_question` if empty). |

Existing Day columns unchanged: `flow_steps` (reused by Flow Puzzle, D-4),
`variant_question`, `explain_prompt`, `role_in_project`, quiz relation.

## Changed: `DayWork` (new gate-result columns)

| Column | Type | Notes |
|---|---|---|
| `flow_puzzle_passed` | Boolean | Set True only by a correct puzzle submission. Default False. |
| `bug_passed` | Boolean | Set True only by a correct line + reason submission. Default False. |
| `self_note` | Text | Learner's own-words note. Gate: ≥2 sentences AND ≥80 non-space chars. Default `""`. |
| `followup_answers` | Text (JSON list) | Answers to the 2 follow-up questions; each ≥20 non-space chars. Default `"[]"` (falls back to `variant_answer` if empty). |
| `summary` | Text | Final Feynman summary (simple re-explanation). Gate: ≥80 non-space chars. Default `""`. |

Existing `DayWork` columns unchanged and still stored: `exercise_submission`,
`test_result`, `explain_answer`, `flow_answer`, `role_answer`, `variant_answer`,
`completed`. `completed=True` is grandfathered — never re-evaluated against v2 gates.

## New: `ExtensionTopic` (Unexplored Scope nodes)

| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `track_id` | Integer FK → tracks.id | Which skill the extension belongs to. |
| `related_day_number` | Integer, nullable | Day after which this extension is suggested (NULL = track-level). |
| `title` | String | e.g. "Mã hóa mật khẩu Bcrypt". |
| `description` | Text | Why it matters + where it will be taught (or "chưa có bài học"). |
| `order` | Integer | Display order. |

Seeded from `seed_data.py` (`EXTENSION_TOPICS`), matched by
`(track_id, title)` on refresh; progress tables untouched.

## Unchanged tables

`Track`, `Module`, `QuizQuestion`, `QuizAttempt`, `ChecklistItem`, `JournalEntry`
— no changes. `ProgressOut` counts unchanged.

## Derived data (not stored)

- **Skill tree node state**: computed at read time from `DayWork.completed`,
  any gate progress (`QuizAttempt` exists / any `DayWork` field non-empty), and
  the unlock rule (D-7). States: `mastered` / `in_progress` / `available` /
  `locked` / `unexplored` (the last only for `ExtensionTopic` rows).
- **Feynman final summary view**: learner's `DayWork.summary` + mastered concepts
  (gates passed) + gaps corrected (follow-up answers) + 5 self-test questions =
  the Day's 4 quiz questions + `variant_question`. No extra storage.
- **Gate evaluation**: pure function `evaluate_day_gates(best_quiz, work_dict) ->
  list[Gate]` in `services.py`, same shape as v1 (key/label/passed).

## Migration

`backend/app/migrate.py`, run in `lifespan` before `seed()`:

- `CREATE TABLE IF NOT EXISTS` is already handled by `create_all` for
  `ExtensionTopic`.
- For each new column above: `ALTER TABLE <table> ADD COLUMN IF NOT EXISTS
  <col> <type>` — Postgres syntax; SQLite accepts the same `ADD COLUMN`
  form (no `IF NOT EXISTS` on old SQLite, but Python 3.12's bundled SQLite
  supports it; the helper checks `PRAGMA table_info` first on SQLite).
- The helper never issues UPDATE/DELETE against `day_work`, `quiz_attempts`,
  `checklist_items`, `journal_entries`.

## Seed refresh

`seed._refresh_content` extended: for each Day (matched by number) also refresh
`importance`, `real_world_use`, `pitfalls`, `bug_*`, `followup_questions`;
for each `ExtensionTopic` (matched by title) refresh description/related day.
Quiz `correct_index` and order are never changed by refresh. Progress rows are
never touched (existing guarantee, re-verified by test).
