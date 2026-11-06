"""Seed the DB from seed_data.py.

First run: insert track, modules, days, quiz questions and checklist.
Later runs: refresh ONLY the content fields (titles, descriptions,
objectives, quiz text, checklist text) from seed_data.py, matched by
slug / day number / checklist order — so a content edit (e.g. adding
Vietnamese diacritics) reaches an already-seeded database.

Progress is NEVER touched here: QuizAttempt, DayWork (including
``completed``), ChecklistItem.done and JournalEntry rows are left
exactly as they are.
"""
from sqlalchemy.orm import Session

from . import models
from .seed_data import CHECKLIST, DAYS, EXTENSION_TOPICS, MODULES, TRACK, TREE, dumps


def _day_fields(d: dict) -> dict:
    return {
        "title": d["title"],
        "objective": d["objective"],
        "role_in_project": d["role"],
        "flow_steps": dumps(d["flow"]),
        "project_tree": dumps(TREE),
        "guide_steps": dumps(d["guide"]),
        "exercise": d["exercise"],
        "exercise_deliverables": dumps(d["deliverables"]),
        "exercise_pass_criteria": dumps(d["pass"]),
        "flow_question": d["flow_q"],
        "role_question": d["role_q"],
        "variant_question": d["variant_q"],
        "explain_prompt": d["explain"],
        # --- v2 content (defaults keep the v1 seed working unchanged) ---
        "importance": d.get("importance", "should"),
        "real_world_use": d.get("real_world_use", ""),
        "pitfalls": dumps(d.get("pitfalls", [])),
        "bug_code": d.get("bug_code", ""),
        "bug_line": d.get("bug_line"),
        "bug_reasons": dumps(d.get("bug_reasons", [])),
        "bug_correct_reason": d.get("bug_correct_reason"),
        "followup_questions": dumps(d.get("followup_questions", [])),
        "sim_scenarios": dumps(d.get("sim_scenarios", [])),
        "flow_step_code": dumps(d.get("flow_step_code", [])),
    }


def _refresh_extension_topics(db: Session, track_id: int) -> None:
    """Sync Unexplored Scope nodes: matched by title, content only."""
    existing = {t.title: t for t in db.query(models.ExtensionTopic).filter_by(track_id=track_id).all()}
    for i, t in enumerate(EXTENSION_TOPICS):
        row = existing.get(t["title"])
        if row is None:
            db.add(models.ExtensionTopic(
                track_id=track_id, related_day_number=t.get("related_day_number"),
                title=t["title"], description=t.get("description", ""), order=i))
        else:
            row.related_day_number = t.get("related_day_number")
            row.description = t.get("description", "")
            row.order = i


def _refresh_content(db: Session, track: models.Track) -> None:
    """Update content fields of an existing seeded track in place."""
    track.title = TRACK["title"]
    track.description = TRACK["description"]
    modules_by_order = {m.order: m for m in track.modules}
    for m in MODULES:
        mod = modules_by_order.get(m["order"])
        if mod is None:
            continue
        mod.title = m["title"]
        mod.description = m["description"]
        days_by_number = {d.number: d for d in mod.days}
        for d in [x for x in DAYS if x["module"] == m["order"]]:
            day = days_by_number.get(d["number"])
            if day is None:
                continue
            for key, value in _day_fields(d).items():
                setattr(day, key, value)
            # Quiz questions: matched by position (seed order is stable).
            questions = sorted(day.quiz_questions, key=lambda q: q.id)
            for qq, new_q in zip(questions, d["quiz"]):
                qq.question = new_q["question"]
                qq.options = dumps(new_q["options"])
                qq.correct_index = new_q["correct_index"]
                qq.explanation = new_q["explanation"]
    # Checklist: matched by order; text/group refresh, done flag untouched.
    items_by_order = {i.order: i for i in db.query(models.ChecklistItem).all()}
    for i, (group, text) in enumerate(CHECKLIST):
        item = items_by_order.get(i)
        if item is not None:
            item.group = group
            item.text = text
    _refresh_extension_topics(db, track.id)
    db.commit()


def seed(db: Session) -> None:
    track = db.query(models.Track).first()
    if track is not None:
        _refresh_content(db, track)
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
            number=d["number"], slug=d["slug"], **_day_fields(d),
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
    _refresh_extension_topics(db, track.id)
    db.commit()
