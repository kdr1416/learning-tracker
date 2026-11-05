"""Unit tests for the pure service logic (no HTTP, no DB)."""
from app.services import classify_booking, evaluate_day_gates


def test_duplicate_same_id_same_content_returns_existing():
    existing = {"id": "b1", "customer": "An", "start": "2026-11-07T10:00", "end": "2026-11-07T11:00"}
    new = dict(existing)
    assert classify_booking(existing, new) == "return_existing"


def test_duplicate_same_id_different_content_is_conflict():
    existing = {"id": "b1", "customer": "An", "start": "2026-11-07T10:00", "end": "2026-11-07T11:00"}
    new = {"id": "b1", "customer": "An", "start": "2026-11-07T12:00", "end": "2026-11-07T13:00"}
    assert classify_booking(existing, new) == "conflict"


def test_overlapping_different_id_is_conflict():
    existing = {"id": "b1", "customer": "An", "start": "2026-11-07T10:00", "end": "2026-11-07T11:00"}
    new = {"id": "b2", "customer": "Binh", "start": "2026-11-07T10:30", "end": "2026-11-07T11:30"}
    assert classify_booking(existing, new) == "conflict"


def test_non_overlapping_is_create():
    existing = {"id": "b1", "customer": "An", "start": "2026-11-07T10:00", "end": "2026-11-07T11:00"}
    new = {"id": "b2", "customer": "Binh", "start": "2026-11-07T12:00", "end": "2026-11-07T13:00"}
    assert classify_booking(existing, new) == "create"


def test_no_existing_is_create():
    assert classify_booking(None, {"id": "b1", "customer": "An",
                                   "start": "2026-11-07T10:00", "end": "2026-11-07T11:00"}) == "create"


def _full_work():
    txt = "Day la cau tra loi day du hon hai muoi ky tu de qua cong."
    return {"exercise_submission": txt, "test_result": txt, "explain_answer": txt,
            "flow_answer": txt, "role_answer": txt, "variant_answer": txt}


def test_gate_all_pass_with_quiz_75_and_full_work():
    gates = evaluate_day_gates(3, 4, _full_work())
    assert len(gates) == 7
    assert all(g.passed for g in gates)


def test_gate_quiz_below_75_fails():
    gates = evaluate_day_gates(2, 4, _full_work())
    assert [g for g in gates if g.key == "quiz"][0].passed is False


def test_gate_short_answer_fails():
    work = _full_work()
    work["explain_answer"] = "hieu roi"
    gates = evaluate_day_gates(4, 4, work)
    assert [g for g in gates if g.key == "explain"][0].passed is False


def test_gate_empty_work_fails_all_but_quiz():
    gates = evaluate_day_gates(4, 4, {})
    assert sum(g.passed for g in gates) == 1  # only quiz
