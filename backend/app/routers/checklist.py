from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter()


@router.get("/checklist", response_model=list[schemas.ChecklistItemOut])
def list_checklist(db: Session = Depends(get_db)):
    return db.query(models.ChecklistItem).order_by(models.ChecklistItem.order).all()


@router.put("/checklist/{item_id}", response_model=schemas.ChecklistItemOut)
def toggle_checklist(item_id: int, payload: schemas.ChecklistToggleIn, db: Session = Depends(get_db)):
    item = db.query(models.ChecklistItem).filter(models.ChecklistItem.id == item_id).first()
    if not item:
        raise HTTPException(404, "Checklist item not found")
    item.done = payload.done
    db.commit()
    db.refresh(item)
    return item
