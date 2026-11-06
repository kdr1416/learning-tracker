"""SQLAlchemy models. Generic Track -> Module -> Day structure so the
same system can be reused for another skill: add a Track, its Modules,
then Days with quiz questions attached. No skill-specific tables."""
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .database import Base


class Track(Base):
    __tablename__ = "tracks"
    id = Column(Integer, primary_key=True)
    slug = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, default="")
    modules = relationship("Module", back_populates="track", cascade="all, delete-orphan")


class Module(Base):
    __tablename__ = "modules"
    id = Column(Integer, primary_key=True)
    track_id = Column(Integer, ForeignKey("tracks.id"), nullable=False)
    slug = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, default="")
    order = Column(Integer, default=0)
    track = relationship("Track", back_populates="modules")
    days = relationship("Day", back_populates="module", cascade="all, delete-orphan")


class Day(Base):
    __tablename__ = "days"
    id = Column(Integer, primary_key=True)
    module_id = Column(Integer, ForeignKey("modules.id"), nullable=False)
    number = Column(Integer, nullable=False)  # Day 1..14, global across the track
    slug = Column(String, nullable=False)
    title = Column(String, nullable=False)
    objective = Column(Text, default="")
    role_in_project = Column(Text, default="")  # vai tro trong du an Booking API
    flow_steps = Column(Text, default="")  # JSON list of strings
    project_tree = Column(Text, default="")  # JSON: {path: role}
    guide_steps = Column(Text, default="")  # JSON list of strings
    exercise = Column(Text, default="")  # de bai cuoi ngay
    exercise_deliverables = Column(Text, default="")  # JSON list
    exercise_pass_criteria = Column(Text, default="")  # JSON list
    flow_question = Column(Text, default="")
    role_question = Column(Text, default="")
    variant_question = Column(Text, default="")
    explain_prompt = Column(Text, default="")
    # --- v2: Enterprise Context Card ---
    importance = Column(String, default="should", server_default="should")  # must | should | nice
    real_world_use = Column(Text, default="", server_default="")
    pitfalls = Column(Text, default="[]", server_default="[]")  # JSON list of strings
    # --- v2: Spot the Bug ---
    bug_code = Column(Text, default="", server_default="")
    bug_line = Column(Integer, nullable=True)  # 0-based index of the wrong line
    bug_reasons = Column(Text, default="[]", server_default="[]")  # JSON list of 4 strings
    bug_correct_reason = Column(Integer, nullable=True)  # index into bug_reasons
    # --- v2: Feynman follow-ups ---
    followup_questions = Column(Text, default="[]", server_default="[]")  # JSON list, exactly 2
    module = relationship("Module", back_populates="days")
    quiz_questions = relationship("QuizQuestion", back_populates="day", cascade="all, delete-orphan")


class ExtensionTopic(Base):
    """Unexplored Scope node on the skill tree: a related concept the
    learner usually does not know to look for (e.g. Bcrypt after basic
    login). Content only — no progress attached."""
    __tablename__ = "extension_topics"
    id = Column(Integer, primary_key=True)
    track_id = Column(Integer, ForeignKey("tracks.id"), nullable=False)
    related_day_number = Column(Integer, nullable=True)
    title = Column(String, nullable=False)
    description = Column(Text, default="")
    order = Column(Integer, default=0)


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"
    id = Column(Integer, primary_key=True)
    day_id = Column(Integer, ForeignKey("days.id"), nullable=False)
    question = Column(Text, nullable=False)
    options = Column(Text, nullable=False)  # JSON list of 4 strings
    correct_index = Column(Integer, nullable=False)
    explanation = Column(Text, default="")
    day = relationship("Day", back_populates="quiz_questions")


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"
    id = Column(Integer, primary_key=True)
    day_id = Column(Integer, ForeignKey("days.id"), nullable=False)
    score = Column(Integer, nullable=False)
    total = Column(Integer, nullable=False)
    answers = Column(Text, default="")  # JSON list of chosen indexes


class DayWork(Base):
    """One row per day: the learner's submitted evidence. The 7-gate
    completion rule is evaluated from this row + the best quiz score."""
    __tablename__ = "day_work"
    id = Column(Integer, primary_key=True)
    day_id = Column(Integer, ForeignKey("days.id"), unique=True, nullable=False)
    exercise_submission = Column(Text, default="")
    test_result = Column(Text, default="")  # e.g. "4/4 tests passed" pasted from pytest
    explain_answer = Column(Text, default="")
    flow_answer = Column(Text, default="")
    role_answer = Column(Text, default="")
    variant_answer = Column(Text, default="")
    completed = Column(Boolean, default=False)
    # --- v2 gate results (v1 text fields above stay, but stop being gates) ---
    flow_puzzle_passed = Column(Boolean, default=False, server_default="0")
    bug_passed = Column(Boolean, default=False, server_default="0")
    self_note = Column(Text, default="", server_default="")
    followup_answers = Column(Text, default="[]", server_default="[]")  # JSON list of strings
    summary = Column(Text, default="", server_default="")  # final Feynman summary


class ChecklistItem(Base):
    __tablename__ = "checklist_items"
    id = Column(Integer, primary_key=True)
    group = Column(String, nullable=False)  # e.g. "Hàng ngày", "Giai đoạn 1"
    text = Column(Text, nullable=False)
    order = Column(Integer, default=0)
    done = Column(Boolean, default=False)


class JournalEntry(Base):
    __tablename__ = "journal_entries"
    id = Column(Integer, primary_key=True)
    date = Column(String, nullable=False)  # YYYY-MM-DD
    topic = Column(String, default="")
    done = Column(Text, default="")
    stuck = Column(Text, default="")
    ai_use = Column(Text, default="")  # dung AI cho viec gi, truoc/sau khi tu viet
    can_explain = Column(String, default="")  # co / khong, phan nao chua duoc
    next_step = Column(Text, default="")
