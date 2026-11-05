"""Pure service logic — kept free of FastAPI so pytest can test it directly.

1. Booking duplicate/conflict classification (the exact rule from the
   roadmap, reused here as the domain example the tracker teaches):
   - same id AND same content  -> return the existing booking (idempotent)
   - same time slot, different content -> real conflict, HTTP 409
   - otherwise -> create a new booking
2. The 7-gate day-completion rule (mirrors the artifact's rule).
"""
from dataclasses import dataclass


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


def evaluate_day_gates(best_quiz_score: int, best_quiz_total: int, work: dict) -> list[Gate]:
    """7 gates. quiz_passed needs >= 75% (3/4 on a 4-question quiz).
    Text answers need at least 20 non-space characters — a one-word
    answer is not an explanation."""
    def text_ok(field: str) -> bool:
        return len((work.get(field) or "").strip()) >= 20

    quiz_passed = bool(best_quiz_total) and (best_quiz_score / best_quiz_total) >= 0.75
    return [
        Gate("quiz", "Trac nghiem dat >= 75% (diem tot nhat)", quiz_passed),
        Gate("exercise", "Da nop bai tap cuoi ngay", text_ok("exercise_submission")),
        Gate("test_result", "Da dan ket qua chay test (vd: 4/4 tests passed)", text_ok("test_result")),
        Gate("explain", "Giai thich lai duoc bai hoc (khong mo tai lieu)", text_ok("explain_answer")),
        Gate("flow", "Tra loi duoc cau hoi ve luong (flow)", text_ok("flow_answer")),
        Gate("role", "Tra loi duoc cau hoi ve vai tro trong du an", text_ok("role_answer")),
        Gate("variant", "Tra loi duoc cau bien the (doi 1 dieu kien)", text_ok("variant_answer")),
    ]
