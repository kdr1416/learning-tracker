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


class DayWorkIn(BaseModel):
    exercise_submission: str = ""
    test_result: str = ""
    explain_answer: str = ""
    flow_answer: str = ""
    role_answer: str = ""
    variant_answer: str = ""


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
