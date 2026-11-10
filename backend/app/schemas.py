from pydantic import BaseModel, Field


class QuizQuestionOut(BaseModel):
    id: int
    question: str
    options: list[str]
    explanation: str

    model_config = {"from_attributes": True}


class DayOut(BaseModel):
    id: int
    number: int
    slug: str
    title: str
    objective: str
    role_in_project: str
    flow_steps: list[str]
    project_tree: dict[str, str]
    guide_steps: list[str]
    exercise: str
    exercise_deliverables: list[str]
    exercise_pass_criteria: list[str]
    flow_question: str
    role_question: str
    variant_question: str
    explain_prompt: str
    # --- v2 fields (defaults keep old payloads valid) ---
    importance: str = "should"
    real_world_use: str = ""
    pitfalls: list[str] = []
    bug_code: str = ""
    bug_reasons: list[str] = []
    # correct_code is the fixed version shown side by side (only Days 2, 3, 5, 9).
    # bug_line / bug_correct_reason are deliberately NOT here: the answer key
    # must never reach the browser (they leaked via _day_out before spec 003).
    correct_code: str = ""
    followup_questions: list[str] = []
    sim_scenarios: list[dict] = []
    flow_step_code: list[dict] = []
    quiz: list[QuizQuestionOut] = []

    model_config = {"from_attributes": True}


class ModuleOut(BaseModel):
    id: int
    slug: str
    title: str
    description: str
    order: int
    days: list[DayOut] = []

    model_config = {"from_attributes": True}


class TrackOut(BaseModel):
    id: int
    slug: str
    title: str
    description: str
    modules: list[ModuleOut] = []

    model_config = {"from_attributes": True}


class QuizAttemptIn(BaseModel):
    answers: list[int] = Field(..., min_length=1)


class QuizAttemptOut(BaseModel):
    id: int
    day_id: int
    score: int
    total: int
    passed: bool
    best_score: int
    best_total: int

    model_config = {"from_attributes": True}


class FlowPuzzleIn(BaseModel):
    order: list[int] = Field(..., min_length=1)


class FlowPuzzleOut(BaseModel):
    passed: bool
    correct_order: list[int] | None = None
    first_wrong_position: int | None = None


class BugIn(BaseModel):
    line: int
    reason: int


class BugOut(BaseModel):
    passed: bool
    line_correct: bool | None = None
    reason_correct: bool | None = None
    # 0-based differing lines, returned only AFTER a submission (never in DayOut):
    # diff_lines = buggy side, diff_lines_correct = fixed side.
    diff_lines: list[int] = []
    diff_lines_correct: list[int] = []


class DayWorkIn(BaseModel):
    exercise_submission: str = ""
    test_result: str = ""
    explain_answer: str = ""
    flow_answer: str = ""
    role_answer: str = ""
    variant_answer: str = ""
    # --- v2 fields (stored as given; thresholds are enforced by the gates,
    # not by this endpoint, so drafts can be saved incrementally) ---
    self_note: str = ""
    followup_answers: list[str] = []
    summary: str = ""


class DayWorkOut(DayWorkIn):
    day_id: int
    completed: bool


class GateOut(BaseModel):
    key: str
    label: str
    passed: bool


class DayStatusOut(BaseModel):
    day_id: int
    completed: bool
    best_quiz_score: int
    best_quiz_total: int
    quiz_passed: bool
    gates: list[GateOut]
    all_gates_passed: bool
    missing: list[str]


class SkillTreeDayOut(BaseModel):
    day_id: int
    number: int
    title: str
    state: str  # mastered | in_progress | available | locked
    gates_passed: int
    gates_total: int


class SkillTreeExtensionOut(BaseModel):
    id: int
    title: str
    description: str
    related_day_number: int | None = None
    state: str = "unexplored"


class SkillTreeModuleOut(BaseModel):
    module_id: int
    title: str
    order: int
    days: list[SkillTreeDayOut] = []
    extensions: list[SkillTreeExtensionOut] = []


class SkillTreeOut(BaseModel):
    track_id: int
    modules: list[SkillTreeModuleOut] = []


class ChecklistItemOut(BaseModel):
    id: int
    group: str
    text: str
    order: int
    done: bool

    model_config = {"from_attributes": True}


class ChecklistToggleIn(BaseModel):
    done: bool


class JournalIn(BaseModel):
    date: str
    topic: str = ""
    done: str = ""
    stuck: str = ""
    ai_use: str = ""
    can_explain: str = ""
    next_step: str = ""


class JournalOut(JournalIn):
    id: int

    model_config = {"from_attributes": True}


class ProgressOut(BaseModel):
    total_checklist: int
    done_checklist: int
    total_days: int
    completed_days: int
    days_by_module: list[dict]
    journal_count: int


# --- ERD (spec 002) ---
class ErdFk(BaseModel):
    column: str
    to_table: str
    to_column: str


class ErdColumn(BaseModel):
    name: str
    type: str
    note: str = ""
    badge: str | None = None
    is_new: bool = False


class ErdTable(BaseModel):
    name: str
    kind: str  # model | dict | table
    present: bool = True
    note: str = ""
    illustration: str = ""
    columns: list[ErdColumn] = []
    rows: list[list[str]] = []
    sql: str = ""
    fk: ErdFk | None = None


class ErdStage(BaseModel):
    day: int
    title: str
    note: str = ""
    tables: list[ErdTable] = []


# --- Weekly Retro per Module (spec 004) ---
class RetroDayOut(BaseModel):
    number: int
    title: str
    completed: bool
    failed_gates: list[str] = []  # skill labels of the gates currently failing


class RetroWeakestOut(BaseModel):
    skill: str
    count: int  # how many incomplete Days fail that gate


class RetroNextDayOut(BaseModel):
    number: int
    title: str


class RetroModuleOut(BaseModel):
    module_id: int
    title: str
    order: int
    total_days: int
    completed_days: int
    days: list[RetroDayOut] = []
    weakest_skill: RetroWeakestOut | None = None
    next_day: RetroNextDayOut | None = None
    can_retro: bool = False
    retro_done: bool = False
    retro_date: str | None = None
    questions: list[str] = []


class RetroIn(BaseModel):
    answers: list[str]  # exactly 3, one per Gibbs question, in order
