const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!r.ok) {
    let detail: unknown = r.statusText
    try { detail = (await r.json()).detail } catch { /* keep statusText */ }
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail))
  }
  return r.json() as Promise<T>
}

export interface QuizQ { id: number; question: string; options: string[]; explanation: string }
export interface SimStep { status: 'ok' | 'fail' | 'skip'; note: string }
export interface SimScenario { title: string; input: string; steps: SimStep[]; result: string }
export interface StepCode { code: string; note: string }
export interface Day {
  id: number; number: number; slug: string; title: string; objective: string
  role_in_project: string; flow_steps: string[]; project_tree: Record<string, string>
  guide_steps: string[]; exercise: string; exercise_deliverables: string[]
  exercise_pass_criteria: string[]; flow_question: string; role_question: string
  variant_question: string; explain_prompt: string; quiz: QuizQ[]
  // --- v2 fields. bug_line / bug_correct_reason are deliberately NOT in
  // the frontend type: the answer key must never reach the browser.
  importance: string; real_world_use: string; pitfalls: string[]
  bug_code: string; bug_reasons: string[]; followup_questions: string[]
  sim_scenarios: SimScenario[]
  flow_step_code: StepCode[]
}
export interface Module { id: number; slug: string; title: string; description: string; order: number; days: Day[] }
export interface Track { id: number; slug: string; title: string; description: string; modules: Module[] }
export interface Gate { key: string; label: string; passed: boolean }
export interface DayStatus {
  day_id: number; completed: boolean; best_quiz_score: number; best_quiz_total: number
  quiz_passed: boolean; gates: Gate[]; all_gates_passed: boolean; missing: string[]
}
export interface DayWork {
  day_id: number; completed: boolean; exercise_submission: string; test_result: string
  explain_answer: string; flow_answer: string; role_answer: string; variant_answer: string
  self_note: string; followup_answers: string[]; summary: string
}
export interface SkillTreeDay {
  day_id: number; number: number; title: string
  state: 'mastered' | 'in_progress' | 'available' | 'locked'
  gates_passed: number; gates_total: number
}
export interface SkillTreeExtension {
  id: number; title: string; description: string
  related_day_number: number | null; state: string
}
export interface SkillTreeModule {
  module_id: number; title: string; order: number
  days: SkillTreeDay[]; extensions: SkillTreeExtension[]
}
export interface SkillTree { track_id: number; modules: SkillTreeModule[] }
export interface ChecklistItem { id: number; group: string; text: string; order: number; done: boolean }
export interface JournalEntry { id: number; date: string; topic: string; done: string; stuck: string; ai_use: string; can_explain: string; next_step: string }
export interface ErdColumn { name: string; type: string; note: string; badge: string | null; is_new: boolean }
export interface ErdFk { column: string; to_table: string; to_column: string }
export interface ErdTable {
  name: string; kind: 'model' | 'dict' | 'table'; present: boolean; note: string
  illustration: string; columns: ErdColumn[]; rows: string[][]; sql: string; fk: ErdFk | null
}
export interface ErdStage { day: number; title: string; note: string; tables: ErdTable[] }
export interface Progress {
  total_checklist: number; done_checklist: number; total_days: number
  completed_days: number; days_by_module: { module: string; total: number; done: number }[]
  journal_count: number
}

export const api = {
  tracks: () => req<Track[]>('/tracks'),
  method: () => req<{ name: string; steps: { title: string; body: string }[]; ai_rules: string[]; daily_test: Record<string, unknown> }>('/method'),
  erd: () => req<ErdStage[]>('/erd'),
  progress: () => req<Progress>('/progress'),
  dayStatus: (id: number) => req<DayStatus>(`/days/${id}/status`),
  submitQuiz: (id: number, answers: number[]) =>
    req<{ score: number; total: number; passed: boolean; best_score: number; best_total: number }>(`/days/${id}/quiz`, { method: 'POST', body: JSON.stringify({ answers }) }),
  getWork: (id: number) => req<DayWork>(`/days/${id}/work`),
  saveWork: (id: number, work: Omit<DayWork, 'day_id' | 'completed'>) =>
    req<DayWork>(`/days/${id}/work`, { method: 'PUT', body: JSON.stringify(work) }),
  completeDay: (id: number) => req<DayStatus>(`/days/${id}/complete`, { method: 'POST' }),
  skillTree: (trackId: number) => req<SkillTree>(`/tracks/${trackId}/skill-tree`),
  submitFlowPuzzle: (id: number, order: number[]) =>
    req<{ passed: boolean; correct_order?: number[]; first_wrong_position?: number }>(
      `/days/${id}/flow-puzzle`, { method: 'POST', body: JSON.stringify({ order }) }),
  submitBug: (id: number, line: number, reason: number) =>
    req<{ passed: boolean; line_correct?: boolean; reason_correct?: boolean }>(
      `/days/${id}/bug`, { method: 'POST', body: JSON.stringify({ line, reason }) }),
  checklist: () => req<ChecklistItem[]>('/checklist'),
  toggleChecklist: (id: number, done: boolean) =>
    req<ChecklistItem>(`/checklist/${id}`, { method: 'PUT', body: JSON.stringify({ done }) }),
  journal: () => req<JournalEntry[]>('/journal'),
  createJournal: (e: Omit<JournalEntry, 'id'>) =>
    req<JournalEntry>('/journal', { method: 'POST', body: JSON.stringify(e) }),
  deleteJournal: (id: number) => req<void>(`/journal/${id}`, { method: 'DELETE' }),
}
