"""Seed the DB from seed_data.py. Idempotent: if a track already exists,
do nothing (so user progress is never wiped on restart)."""
from sqlalchemy.orm import Session

from . import models
from .seed_data import CHECKLIST, DAYS, MODULES, TRACK, TREE, dumps


def seed(db: Session) -> None:
    if db.query(models.Track).first():
        return
    track = models.Track(slug=TRACK["slug"], title=TRACK["title"], description=TRACK["description"])
    db.add(track)
    db.flush()
    module_by_order = {}
    for m in MODULES:
        mod = models.Module(track_id=track.id, slug=m["slug"], title=m["title"],
                            description=m["description"], order=m["order"])
        db.add(mod)
        db.flush()
        module_by_order[m["order"]] = mod
    for d in DAYS:
        day = models.Day(
            module_id=module_by_order[d["module"]].id,
            number=d["number"], slug=d["slug"], title=d["title"],
            objective=d["objective"], role_in_project=d["role"],
            flow_steps=dumps(d["flow"]), project_tree=dumps(TREE),
            guide_steps=dumps(d["guide"]), exercise=d["exercise"],
            exercise_deliverables=dumps(d["deliverables"]),
            exercise_pass_criteria=dumps(d["pass"]),
            flow_question=d["flow_q"], role_question=d["role_q"],
            variant_question=d["variant_q"], explain_prompt=d["explain"],
        )
        db.add(day)
        db.flush()
        for qq in d["quiz"]:
            db.add(models.QuizQuestion(
                day_id=day.id, question=qq["question"],
                options=dumps(qq["options"]), correct_index=qq["correct_index"],
                explanation=qq["explanation"]))
    for i, (group, text) in enumerate(CHECKLIST):
        db.add(models.ChecklistItem(group=group, text=text, order=i))
    db.commit()
