"""Pure service logic — kept free of FastAPI so pytest can test it directly.

1. Booking duplicate/conflict classification (the exact rule from the
   roadmap, reused here as the domain example the tracker teaches):
   - same id AND same content  -> return the existing booking (idempotent)
   - same time slot, different content -> real conflict, HTTP 409
   - otherwise -> create a new booking
2. The v2 6-gate day-completion rule (Feynman + Viet - Test - Giai thich,
   unified): quiz, exercise+test, flow puzzle, spot the bug, self-note +
   variant/follow-up, final summary. Server-enforced; the frontend tick is
   never evidence.
3. Skill-tree state derivation (computed from progress, never stored).
"""
import re
from dataclasses import dataclass

from sqlalchemy.orm import Session

from . import models


def classify_booking(existing, new):
    """existing: dict|None with keys id, customer, start, end.
    new: dict with the same keys.
    Returns 'return_existing' | 'conflict' | 'create'."""
    if existing is None:
        return "create"
    if existing["id"] == new["id"]:
        same_content = (
            existing.get("customer") == new.get("customer")
            and existing.get("start") == new.get("start")
            and existing.get("end") == new.get("end")
        )
        return "return_existing" if same_content else "conflict"
    overlap = new["start"] < existing["end"] and existing["start"] < new["end"]
    return "conflict" if overlap else "create"


@dataclass
class Gate:
    key: str
    label: str
    passed: bool


def _nonspace_len(text: str) -> int:
    return len(re.sub(r"\s+", "", text or ""))


def _sentence_count(text: str) -> int:
    """Split on sentence-ending punctuation and newlines; count non-empty parts."""
    parts = [p.strip() for p in re.split(r"[.!?\n]+", text or "") if p.strip()]
    return len(parts)


def _text_ok(field_value: str, min_chars: int = 20) -> bool:
    return _nonspace_len(field_value) >= min_chars


def evaluate_day_gates(best_quiz_score: int, best_quiz_total: int, work: dict) -> list[Gate]:
    """6 gates (plan decisions D-1..D-3).
    - quiz: best score >= 75%.
    - exercise: exercise_submission AND test_result, each >= 20 non-space chars.
    - flow_puzzle / bug: boolean flags set only by a correct submission.
    - self_note: note has >= 2 sentences AND >= 80 non-space chars, AND either
      2 follow-up answers (>= 20 chars each) or — while a Day has no follow-up
      questions stored yet (before Phase C content) — a valid variant answer.
    - summary: final Feynman summary >= 80 non-space chars.
    Old v1 fields (explain/flow/role answers) are still stored but no longer gates.
    """
    def text_ok(field: str, min_chars: int = 20) -> bool:
        return _text_ok(work.get(field) or "", min_chars)

    quiz_passed = bool(best_quiz_total) and (best_quiz_score / best_quiz_total) >= 0.75
    exercise_passed = text_ok("exercise_submission") and text_ok("test_result")

    note = work.get("self_note") or ""
    note_ok = _sentence_count(note) >= 2 and _nonspace_len(note) >= 80
    followups = [a for a in (work.get("followup_answers") or []) if isinstance(a, str)]
    followups_ok = (
        sum(1 for a in followups if _nonspace_len(a) >= 20) >= 2
        or (not followups and text_ok("variant_answer"))
    )
    self_note_passed = note_ok and followups_ok

    return [
        Gate("quiz", "Trắc nghiệm đạt >= 75% (điểm tốt nhất)", quiz_passed),
        Gate("exercise", "Đã nộp bài tập cuối ngày + kết quả chạy test", exercise_passed),
        Gate("flow_puzzle", "Xếp đúng luồng chạy (Flow Puzzle)",
             bool(work.get("flow_puzzle_passed"))),
        Gate("bug", "Bắt đúng lỗi trong đoạn code (Spot the Bug)",
             bool(work.get("bug_passed"))),
        Gate("self_note", "Giải thích lại bằng lời của mình + trả lời câu biến thể",
             self_note_passed),
        Gate("summary", "Đã viết bản tóm tắt cuối Day (Feynman)",
             _nonspace_len(work.get("summary") or "") >= 80),
    ]


# --- Skill tree (derived state, never stored) ---

def ordered_days(db: Session, track_id: int) -> list[models.Day]:
    """All Days of a track in learning order: modules by order, days by number."""
    track = db.query(models.Track).filter(models.Track.id == track_id).first()
    if track is None:
        return []
    days: list[models.Day] = []
    for mod in sorted(track.modules, key=lambda m: m.order):
        days.extend(sorted(mod.days, key=lambda d: d.number))
    return days


def _has_any_progress(db: Session, day_id: int) -> bool:
    """True once the learner has done anything on the Day (quiz attempt, any
    work field, or any gate flag). Used for the in_progress state."""
    if db.query(models.QuizAttempt).filter_by(day_id=day_id).first():
        return True
    work = db.query(models.DayWork).filter_by(day_id=day_id).first()
    if work is None:
        return False
    return bool(
        (work.exercise_submission or "").strip()
        or (work.test_result or "").strip()
        or (work.self_note or "").strip()
        or (work.summary or "").strip()
        or work.flow_puzzle_passed
        or work.bug_passed
    )


def day_state(db: Session, day: models.Day) -> str:
    """mastered | in_progress | available | locked (plan decision D-7).
    Sequential unlock: a Day is available only when the previous Day in the
    track is completed; the first Day is always available."""
    work = db.query(models.DayWork).filter_by(day_id=day.id).first()
    if work is not None and work.completed:
        return "mastered"
    days = ordered_days(db, day.module.track_id)
    idx = next((i for i, d in enumerate(days) if d.id == day.id), None)
    if idx is None or idx == 0:
        unlocked = True
    else:
        prev = db.query(models.DayWork).filter_by(day_id=days[idx - 1].id).first()
        unlocked = bool(prev is not None and prev.completed)
    if not unlocked:
        return "locked"
    return "in_progress" if _has_any_progress(db, day.id) else "available"


def is_locked(db: Session, day: models.Day) -> bool:
    return day_state(db, day) == "locked"
