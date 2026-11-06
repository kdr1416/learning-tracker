# Research: Learning Tracker v2 (Phase 0)

## Decisions

### 1. Unified gate set: 6 gates, not 7 + 6

v1 has 7 gates (quiz, exercise, test_result, explain, flow, role, variant). The
spec's Feynman flow and the personal method overlap heavily: "explain" (v1) IS the
Feynman explain step; "flow" and "role" answers are subsumed by the Flow Puzzle,
the Enterprise Context Card, and the follow-up/variant answers. Stacking both sets
would give 10+ gates and invite tick-box behaviour.

**Decision**: 6 gates — quiz, exercise+test, flow puzzle, spot the bug, self-note +
variant/follow-up, final summary. v1 text fields (`explain_answer`,
`flow_answer`, `role_answer`) stay as columns but stop being gates. Rationale:
fewer, harder gates beat many soft ones; the variant answer is the strongest
evidence of understanding and is kept.

### 2. Migration without Alembic

The production DB (Neon Postgres) already has v1 tables. `Base.metadata.create_all`
creates missing tables but never alters existing ones, so new columns need explicit
`ALTER TABLE ... ADD COLUMN IF NOT EXISTS`. Alternatives considered:

- **Alembic**: the standard tool, but it adds a migrations directory, env.py, and
  a revision workflow for a single-user app with no migration history. Rejected
  for this scale.
- **Startup migration helper** (`migrate.py`, idempotent DDL, run in `lifespan`
  before `seed()`): one file, no new dependency, same `IF NOT EXISTS` pattern
  works on SQLite (local) and Postgres (Neon). **Chosen.**
- **Wipe + reseed**: forbidden by Constitution I.

The helper must be proven on a copy of a v1-schema database with fake progress
before any production deploy.

### 3. Skill tree state is derived, not stored

Node state (Mastered / In Progress / Available / Locked / Unexplored Scope) is
computed from `DayWork` + quiz attempts + the unlock rule at read time
(`GET /tracks/{id}/skill-tree`). No state column is stored, so state can never
drift from progress. Unexplored Scope nodes are the only stored tree data, in a
small `ExtensionTopic` table seeded from `seed_data.py`.

### 4. Flow Puzzle reuses `flow_steps`

Each Day already stores `flow_steps` (ordered list). The puzzle is a presentation
of that same data: frontend shuffles, learner re-orders, server compares index
order. No new content field, no duplicate source of truth, and every Day gets a
puzzle for free. Risk: a Day with <2 flow steps makes a trivial puzzle — the
content check in Phase C asserts ≥3 steps per Day (all 14 Days currently have
≥3; verified from `seed_data.py`).

### 5. Bug snippets are authored content, not generated

One snippet per Day, exactly one unambiguous wrong line. Generated snippets risk
ambiguous or multiple bugs, which would teach the wrong lesson and make the gate
unfair. Authoring is manual and reviewed by reading; the largest effort in v2 is
Phase C content, not code.

### 6. Self-Note paste block is UX, not evidence

`onPaste` prevention + right-click menu suppression can be bypassed (DevTools,
browser extensions, mobile keyboards). The spec already states this. Evidence is
the variant/follow-up answer, which cannot be pasted into understanding. No
server-side attempt is made to detect paste.

### 7. MCP admin deferred to phase 2

The user asked for MCP admin (add/edit lessons, topics, content). A direct
MCP-to-Neon write path needs decisions on where the server runs and how it
authenticates to production — unanswered questions (see spec FR-009 NEEDS
CLARIFICATION). The repo-driven admin path already works in v1 (edit seed →
push → redeploy → seed refresh preserves progress). **Decision**: v2 ships with
the repo path; MCP is phase 2 after P1–P4 are live.

### 8. Deploy realities carried over from v1

- Render does not auto-deploy on pushes made via the GitHub API snapshot flow;
  backend deploys must be triggered manually and verified live.
- Render free sleeps after ~15 min idle; first request can take ~50 s — the
  frontend must show loading, not a connection error.
- Vercel frontend redeploys via CLI (`vercel deploy --prod --scope
  tuan-learning-tracker`); `VITE_API_URL` must end with `/api`.

## Alternatives considered and rejected

| Alternative | Why rejected |
|---|---|
| Keep v1 7 gates and add 3 new gates (10 total) | Two overlapping checklists; tick-box behaviour; contradicts Constitution II |
| Store skill-tree state in a column | Drifts from progress; needs sync logic on every write |
| Auto-generate bug snippets / enterprise cards with AI | Ambiguous bugs, generic cards, unverified Vietnamese; violates hand-checked content rule |
| Build MCP admin in v2 | Unanswered auth/hosting questions; delays the learning core (P1–P4) |
| New repo for v2 | Duplicates the whole stack and deploy; user chose upgrade, keep progress |
