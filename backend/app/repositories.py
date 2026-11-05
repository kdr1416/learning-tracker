"""Repository layer: only DB access, no business rules."""
from sqlalchemy.orm import Session

from . import models


def get_track(db: Session):
    return db.query(models.Track).first()


def get_day(db: Session, day_id: int):
    return db.query(models.Day).filter(models.Day.id == day_id).first()


def get_day_by_number(db: Session, number: int):
    return db.query(models.Day).filter(models.Day.number == number).first()


def best_quiz(db: Session, day_id: int):
    rows = db.query(models.QuizAttempt).filter(models.QuizAttempt.day_id == day_id).all()
    if not rows:
        return 0, 0
    best = max(rows, key=lambda r: (r.score, -r.id))
    return best.score, best.total


def get_work(db: Session, day_id: int):
    return db.query(models.DayWork).filter(models.DayWork.day_id == day_id).first()


def upsert_work(db: Session, day_id: int, data: dict):
    work = get_work(db, day_id)
    if work is None:
        work = models.DayWork(day_id=day_id, **data)
        db.add(work)
    else:
        for k, v in data.items():
            setattr(work, k, v)
    db.commit()
    db.refresh(work)
    return work
