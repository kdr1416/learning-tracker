from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter()


@router.get("/progress", response_model=schemas.ProgressOut)
def get_progress(db: Session = Depends(get_db)):
    total = db.query(models.ChecklistItem).count()
    done = db.query(models.ChecklistItem).filter(models.ChecklistItem.done.is_(True)).count()
    days = db.query(models.Day).all()
    completed = db.query(models.DayWork).filter(models.DayWork.completed.is_(True)).count()
    by_module = []
    for m in db.query(models.Module).order_by(models.Module.order).all():
        day_ids = [d.id for d in m.days]
        done_m = db.query(models.DayWork).filter(
            models.DayWork.day_id.in_(day_ids),
            models.DayWork.completed.is_(True)).count() if day_ids else 0
        by_module.append({"module": m.title, "total": len(day_ids), "done": done_m})
    return schemas.ProgressOut(
        total_checklist=total, done_checklist=done,
        total_days=len(days), completed_days=completed,
        days_by_module=by_module,
        journal_count=db.query(models.JournalEntry).count())
