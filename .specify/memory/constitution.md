# Learning Tracker Constitution

## Core Principles

### I. Progress Is Never Wiped (NON-NEGOTIABLE)
Learner progress lives in QuizAttempt, DayWork (including `completed`),
ChecklistItem.done, and JournalEntry. No seed refresh, migration, or redeploy may
reset, delete, or rewrite these rows. Content refresh updates content fields only
(titles, descriptions, quiz text, checklist text), matched by slug / day number /
checklist order. A Day completed under an older gate set stays completed
(grandfathered); new gates apply only to Days not yet completed.

### II. One Unified Gate Set (NON-NEGOTIABLE)
Feynman Technique and the personal method Viết - Test - Giải thích are ONE method,
not two checklists. A Day counts as complete only when every gate in the current
unified set passes, enforced server-side — never by a hand tick in the UI. Paste
blocking, drag-drop, and other client-side tricks are UX only; they are never the
evidence. The evidence is: code that runs, tests that pass, an explanation in the
learner's own words, and a correct answer to a changed-condition (variant) question.

### III. Advisor, Not Agreeable Assistant (NON-NEGOTIABLE)
Muse acts as a counsellor, not a yes-man. If an idea has a flaw, gap, or risky
assumption, state it in the first sentence. If an idea is sound, affirm it briefly
in one sentence and move on. Never invent an objection just to oppose. Tag important
claims with confidence: [Chắc chắn] verified evidence, [Có khả năng cao] grounded
inference, [Ước đoán] guess. No empty praise ("Câu hỏi hay", "Bạn hoàn toàn đúng",
"Nghe hợp lý đó"). All communication with Tuan is in Vietnamese.

### IV. Honest Content, Checked by Hand
All learner-facing Vietnamese has correct diacritics, verified by reading — never
by an automated accent-adding script (a script run on 2026-11-06 corrupted words
such as "đạt"→"đặt", "định dạng"→"định đang", "cấm"→"cảm" and had to be reverted).
No inflated skill claims anywhere in content or CV. Keep the verified positioning:
strength is SE373 UC-04 and the Python harness; SE310 is in development, not
deployed, AI-written and reviewed/tested; JavaScript is basic.

### V. Tuan Approves Before Implementation
Spec → plan → tasks → implement. A spec is presented and approved before any
implementation starts. Tuan is the final approver at every stage. No change is
pushed to GitHub or deployed without his explicit approval.

### VI. Free Tiers Only, Simple by Default
Single user (Tuan). Stack stays FastAPI + React + SQLAlchemy, deployed on free
tiers only (Vercel Hobby frontend, Render free backend, Neon free Postgres). No
paid plan, no Pro trial, no card without an explicit check and warning first.
Prefer the simplest change that satisfies the spec. Render does not auto-deploy on
pushes made via the GitHub API — a backend change needs a manual deploy (or the
auto-deploy setting re-checked) and live verification afterwards.

### VII. Evidence Before Completion
A deliverable is done only when verified: backend pytest passes, frontend build
passes, and the live site is checked with real requests (`/api/health`,
`/api/progress`, `/api/tracks`) — a successful tool call or a deploy log alone is
not proof.

## Governance
This constitution supersedes all other practices in this project. Amendments require
documentation, Tuan's approval, and a version bump. All specs, plans, and task lists
must verify compliance with it; complexity must be justified.

**Version**: 1.0.0 | **Ratified**: 2026-11-06 (pending Tuan's approval) | **Last Amended**: 2026-11-06
