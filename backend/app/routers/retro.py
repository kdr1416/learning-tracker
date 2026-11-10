"""Weekly Retro per Module (spec 004).

Computed live from real progress — no new tables, no migration. A Module
opens its retro once every Day in it is completed. Answers are saved as
one JournalEntry per Module (topic "Retro Module {order}: {title}").
Retro is per Module, not per week: DayWork stores no completion date,
so a real weekly split would need a completed_at column (deferred).
"""
from collections import Counter
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from .days import _status

router = APIRouter()

GATE_SKILL = {
    "quiz": "Hiểu khái niệm",
    "exercise": "Viết code chạy được",
    "flow_puzzle": "Hiểu luồng chạy",
    "bug": "Đọc và bắt lỗi code",
    "self_note": "Giải thích lại bằng lời mình",
    "summary": "Tóm tắt cuối Day",
}
GATE_ORDER = ["quiz", "exercise", "flow_puzzle", "bug", "self_note", "summary"]

RETRO_QUESTIONS = [
    "Điều gì chạy tốt trong Module này?",
    "Chỗ nào kẹt lâu nhất?",
    "Module sau làm khác gì?",
]


def _retro_topic(module: models.Module) -> str:
    return f"Retro Module {module.order}: {module.title}"


def _retro_entry(db: Session, module: models.Module):
    return (db.query(models.JournalEntry)
            .filter_by(topic=_retro_topic(module)).first())


@router.get("/retro", response_model=list[schemas.RetroModuleOut])
def list_retro(db: Session = Depends(get_db)):
    out = []
    modules = db.query(models.Module).order_by(models.Module.order).all()
    for module in modules:
        days = sorted(module.days, key=lambda d: d.number)
        day_rows = []
        failed: Counter = Counter()
        completed = 0
        next_day = None
        for d in days:
            status = _status(db, d.id)
            failed_keys = [g.key for g in status.gates if not g.passed]
            if status.completed:
                completed += 1
            else:
                for k in failed_keys:
                    failed[k] += 1
                if next_day is None:
                    next_day = {"number": d.number, "title": d.title}
            day_rows.append(schemas.RetroDayOut(
                number=d.number, title=d.title, completed=status.completed,
                failed_gates=[GATE_SKILL[k] for k in failed_keys]))
        weakest = None
        if failed:
            top_count = max(failed.values())
            top_key = next(k for k in GATE_ORDER if failed.get(k) == top_count)
            weakest = schemas.RetroWeakestOut(
                skill=GATE_SKILL[top_key], count=top_count)
        entry = _retro_entry(db, module)
        out.append(schemas.RetroModuleOut(
            module_id=module.id, title=module.title, order=module.order,
            total_days=len(days), completed_days=completed, days=day_rows,
            weakest_skill=weakest,
            next_day=(schemas.RetroNextDayOut(**next_day)
                      if next_day else None),
            can_retro=len(days) > 0 and completed == len(days),
            retro_done=entry is not None,
            retro_date=entry.date if entry else None,
            questions=RETRO_QUESTIONS))
    return out


@router.post("/retro/{module_id}", response_model=schemas.JournalOut,
             status_code=201)
def save_retro(module_id: int, payload: schemas.RetroIn,
               db: Session = Depends(get_db)):
    module = db.query(models.Module).filter_by(id=module_id).first()
    if module is None:
        raise HTTPException(404, "Module không tồn tại")
    days = sorted(module.days, key=lambda d: d.number)
    if not days or any(not _status(db, d.id).completed for d in days):
        raise HTTPException(
            400, "Chưa xong hết Day trong Module này — chưa viết retro được.")
    if _retro_entry(db, module) is not None:
        raise HTTPException(409, "Module này đã viết retro rồi.")
    answers = [a.strip() for a in (payload.answers or [])]
    if len(answers) != 3 or any(not a for a in answers):
        raise HTTPException(422, "Cần trả lời đủ 3 câu hỏi.")
    today = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).date().isoformat()
    entry = models.JournalEntry(
        date=today, topic=_retro_topic(module),
        done=answers[0], stuck=answers[1], next_step=answers[2])
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
