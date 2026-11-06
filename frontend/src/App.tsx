import { useEffect, useState } from 'react'
import { api, type ChecklistItem, type Day, type DayStatus, type DayWork, type JournalEntry, type Progress, type Track } from './api'

type Route = { page: 'dashboard' | 'days' | 'day' | 'checklist' | 'journal' | 'method'; dayNumber?: number }

function parseHash(): Route {
  const h = window.location.hash.replace(/^#\/?/, '')
  if (h.startsWith('day/')) return { page: 'day', dayNumber: Number(h.slice(4)) }
  if (h === 'days') return { page: 'days' }
  if (h === 'checklist') return { page: 'checklist' }
  if (h === 'journal') return { page: 'journal' }
  if (h === 'method') return { page: 'method' }
  return { page: 'dashboard' }
}
const go = (hash: string) => { window.location.hash = hash }

const NAV: { hash: string; label: string; page: Route['page'] }[] = [
  { hash: '#/', label: 'Tổng quan', page: 'dashboard' },
  { hash: '#/days', label: 'Ngày 1–14', page: 'days' },
  { hash: '#/checklist', label: 'Checklist', page: 'checklist' },
  { hash: '#/journal', label: 'Nhật ký', page: 'journal' },
  { hash: '#/method', label: 'Phương pháp', page: 'method' },
]

export default function App() {
  const [route, setRoute] = useState<Route>(parseHash())
  const [tracks, setTracks] = useState<Track[]>([])
  const [error, setError] = useState('')
  useEffect(() => {
    const onHash = () => setRoute(parseHash())
    window.addEventListener('hashchange', onHash)
    api.tracks().then(setTracks).catch((e: Error) => setError(
      `Không kết nối được backend (${e.message}). Hãy chạy backend trước: cd backend && .venv/bin/uvicorn app.main:app --reload`))
    return () => window.removeEventListener('hashchange', onHash)
  }, [])
  const allDays: Day[] = tracks.flatMap(t => t.modules.flatMap(m => m.days))
  const day = route.dayNumber ? allDays.find(d => d.number === route.dayNumber) : undefined
  const activePage = route.page === 'day' ? 'days' : route.page
  return (
    <>
      <header className="site-header">
        <div className="header-inner">
          <div className="brand">
            <span className="brand-mark">LT</span>
            <div>
              <h1>Learning Tracker</h1>
              <p className="brand-sub">Backend Intern · FastAPI → Spring Boot · Booking API</p>
            </div>
          </div>
          <nav>
            {NAV.map(n => (
              <a key={n.hash} href={n.hash} className={activePage === n.page ? 'active' : ''}>{n.label}</a>
            ))}
          </nav>
        </div>
      </header>
      <main>
        {error && <div className="error">{error}</div>}
        {route.page === 'dashboard' && <Dashboard />}
        {route.page === 'days' && <DayList tracks={tracks} />}
        {route.page === 'day' && day && <DayDetail day={day} />}
        {route.page === 'day' && !day && tracks.length > 0 && <p>Không tìm thấy Day {route.dayNumber}.</p>}
        {route.page === 'checklist' && <ChecklistPage />}
        {route.page === 'journal' && <JournalPage />}
        {route.page === 'method' && <MethodPage />}
      </main>
      <footer className="site-footer">
        <p>Phương pháp: Viết – Test – Giải thích · Một ngày chỉ tính là xong khi qua đủ 7 cổng.</p>
      </footer>
    </>
  )
}

function Dashboard() {
  const [p, setP] = useState<Progress | null>(null)
  useEffect(() => { api.progress().then(setP).catch(() => undefined) }, [])
  if (!p) return <p className="loading">Đang tải tiến độ…</p>
  const checklistPct = p.total_checklist ? Math.round((p.done_checklist / p.total_checklist) * 100) : 0
  const daysPct = p.total_days ? Math.round((p.completed_days / p.total_days) * 100) : 0
  const nextDay = p.completed_days + 1
  return (
    <div>
      <section className="hero">
        <p className="eyebrow">Lộ trình 3 tháng · 1 dự án duy nhất: Booking API</p>
        <h2>Hôm nay học gì?</h2>
        <p className="hero-text">
          Mở ngày tiếp theo, làm trắc nghiệm (đạt ≥ 75%), nộp bài tập, trả lời 4 câu hiểu bài,
          rồi mới bấm hoàn thành. Không tick tay khi chưa qua đủ cổng.
        </p>
        <div className="hero-actions">
          <button onClick={() => go(nextDay <= p.total_days ? `#/day/${nextDay}` : '#/days')}>
            {p.completed_days === 0 ? 'Bắt đầu Day 1' : nextDay <= p.total_days ? `Tiếp tục Day ${nextDay}` : 'Xem lại các Day'}
          </button>
          <button className="secondary" onClick={() => go('#/days')}>Xem danh sách Day</button>
        </div>
      </section>
      <div className="stat-grid">
        <div className="stat-card">
          <span className="stat-value">{p.done_checklist}<small>/{p.total_checklist}</small></span>
          <span className="stat-label">Mục checklist đã xong</span>
          <div className="progress"><div style={{ width: `${checklistPct}%` }} /></div>
          <span className="stat-note">{checklistPct}% hoàn thành</span>
        </div>
        <div className="stat-card">
          <span className="stat-value">{p.completed_days}<small>/{p.total_days}</small></span>
          <span className="stat-label">Day đã hoàn thành</span>
          <div className="progress"><div style={{ width: `${daysPct}%` }} /></div>
          <span className="stat-note">{daysPct}% hoàn thành</span>
        </div>
        <div className="stat-card">
          <span className="stat-value">{p.journal_count}</span>
          <span className="stat-label">Bài nhật ký buổi học</span>
          <span className="stat-note">Ghi lại mỗi buổi: làm gì, bí ở đâu, mai làm gì</span>
        </div>
      </div>
      {p.days_by_module.map(m => (
        <div className="card module-progress" key={m.module}>
          <div className="module-progress-head">
            <h3>{m.module}</h3>
            <span className="pill">{m.done}/{m.total} Day</span>
          </div>
          <div className="progress"><div style={{ width: `${m.total ? (m.done / m.total) * 100 : 0}%` }} /></div>
        </div>
      ))}
    </div>
  )
}

function DayList({ tracks }: { tracks: Track[] }) {
  return (
    <div>
      <div className="page-head">
        <h2>Lộ trình theo ngày</h2>
        <p>Mỗi Day là một buổi học: mục tiêu rõ, trắc nghiệm chấm thật, bài tập cuối ngày và kiểm tra hiểu bài.</p>
      </div>
      {tracks.map(t => (
        <div key={t.id}>
          <p className="track-intro">{t.description}</p>
          {t.modules.map(m => (
            <section className="card module-card" key={m.id}>
              <h3>{m.title}</h3>
              <p className="muted">{m.description}</p>
              <div className="grid">
                {m.days.map(d => (
                  <button key={d.id} className="secondary day-card" onClick={() => go(`#/day/${d.number}`)}>
                    <span className="day-number">Day {d.number}</span>
                    <span className="day-title">{d.title.replace(/^Day \d+ — /, '')}</span>
                  </button>
                ))}
              </div>
            </section>
          ))}
        </div>
      ))}
      <p className="note"><i>Giai đoạn 4 (Deploy) và Spring Boot chưa chia Day — sẽ thêm theo cùng khuôn Track → Module → Day.</i></p>
    </div>
  )
}

function DayDetail({ day }: { day: Day }) {
  const [answers, setAnswers] = useState<number[]>(() => day.quiz.map(() => -1))
  const [quizResult, setQuizResult] = useState<{ score: number; total: number; passed: boolean; best_score: number; best_total: number } | null>(null)
  const [status, setStatus] = useState<DayStatus | null>(null)
  const [work, setWork] = useState<DayWork>({
    day_id: day.id, completed: false, exercise_submission: '', test_result: '',
    explain_answer: '', flow_answer: '', role_answer: '', variant_answer: '',
  })
  const [msg, setMsg] = useState('')
  const [err, setErr] = useState('')
  useEffect(() => {
    setAnswers(day.quiz.map(() => -1)); setQuizResult(null); setMsg(''); setErr('')
    api.dayStatus(day.id).then(setStatus).catch(() => undefined)
    api.getWork(day.id).then(setWork).catch(() => undefined)
  }, [day.id])
  const submitQuiz = async () => {
    if (answers.some(a => a < 0)) { setErr('Hãy chọn đáp án cho cả 4 câu trước khi nộp.'); return }
    setErr('')
    try {
      const r = await api.submitQuiz(day.id, answers)
      setQuizResult(r)
      setStatus(await api.dayStatus(day.id))
    } catch (e) { setErr(e instanceof Error ? e.message : String(e)) }
  }
  const saveWork = async () => {
    setErr(''); setMsg('')
    try {
      await api.saveWork(day.id, work)
      setStatus(await api.dayStatus(day.id))
      setMsg('Đã lưu bài làm.')
    } catch (e) { setErr(e instanceof Error ? e.message : String(e)) }
  }
  const complete = async () => {
    setErr(''); setMsg('')
    try {
      const s = await api.completeDay(day.id)
      setStatus(s); setMsg('Chúc mừng — Day này đã hoàn thành (đủ 7 cổng).')
    } catch (e) {
      const m = e instanceof Error ? e.message : String(e)
      setErr(`Chưa hoàn thành được. Còn thiếu: ${m}`)
      setStatus(await api.dayStatus(day.id))
    }
  }
  const set = (k: keyof DayWork, v: string) => setWork(w => ({ ...w, [k]: v }))
  const passedGates = status ? status.gates.filter(g => g.passed).length : 0
  return (
    <div>
      <button className="secondary" onClick={() => go('#/days')}>← Tất cả Day</button>
      <div className="page-head">
        <p className="eyebrow">Day {day.number} / 14</p>
        <h2>{day.title}</h2>
        {status && (
          <p className="muted">
            {status.completed
              ? 'Day này đã hoàn thành.'
              : `Đã qua ${passedGates}/7 cổng · Điểm trắc nghiệm tốt nhất: ${status.best_quiz_score}/${status.best_quiz_total}`}
          </p>
        )}
      </div>
      <div className="card"><h3>Mục tiêu</h3><p>{day.objective}</p>
        <h3>Vai trò trong dự án Booking API</h3><p>{day.role_in_project}</p></div>
      <div className="card"><h3>Sơ đồ luồng</h3><ol className="flow-list">{day.flow_steps.map((s, i) => <li key={i}>{s}</li>)}</ol>
        <h3>Cây dự án — file chạm tới</h3>
        <pre>{Object.entries(day.project_tree).map(([k, v]) => `${k}\n  → ${v}`).join('\n')}</pre></div>
      <div className="card"><h3>Hướng dẫn từng bước</h3><ol>{day.guide_steps.map((s, i) => <li key={i}>{s}</li>)}</ol></div>
      <div className="card">
        <h3>Trắc nghiệm (4 câu, đạt ≥ 75% — điểm tốt nhất được lưu)</h3>
        {status && <p>Điểm tốt nhất: <b>{status.best_quiz_score}/{status.best_quiz_total}</b> {status.quiz_passed ? '— đã đạt' : '— chưa đạt'}</p>}
        {day.quiz.map((q, qi) => (
          <div key={q.id} className="quiz-question">
            <p><b>Câu {qi + 1}:</b> {q.question}</p>
            {q.options.map((o, oi) => (
              <button key={oi} className={`quiz-opt ${answers[qi] === oi ? 'selected' : ''}`}
                onClick={() => setAnswers(a => a.map((v, i) => i === qi ? oi : v))}>
                <span className="quiz-opt-letter">{String.fromCharCode(65 + oi)}</span>{o}
              </button>
            ))}
            {quizResult && <p className="quiz-explain"><i>Giải thích: {q.explanation}</i></p>}
          </div>
        ))}
        <button onClick={submitQuiz}>Nộp trắc nghiệm</button>
        {quizResult && <p className={quizResult.passed ? 'ok' : 'error'}>
          Bạn được {quizResult.score}/{quizResult.total} {quizResult.passed ? '— đạt.' : '— chưa đạt 75%, hãy làm lại.'} Điểm tốt nhất: {quizResult.best_score}/{quizResult.best_total}.</p>}
      </div>
      <div className="card">
        <h3>Bài tập cuối ngày</h3><p>{day.exercise}</p>
        <p><b>Deliverables:</b></p><ul>{day.exercise_deliverables.map((d, i) => <li key={i}>{d}</li>)}</ul>
        <p><b>Tiêu chí pass:</b></p><ul>{day.exercise_pass_criteria.map((d, i) => <li key={i}>{d}</li>)}</ul>
        <label>Bài nộp (code / link / mô tả ngắn)</label>
        <textarea rows={4} value={work.exercise_submission} onChange={e => set('exercise_submission', e.target.value)} />
        <label>Kết quả chạy test (dán output pytest, vd: 4/4 passed)</label>
        <textarea rows={2} value={work.test_result} onChange={e => set('test_result', e.target.value)} />
      </div>
      <div className="card">
        <h3>Kiểm tra hiểu bài (mỗi câu cần ≥ 20 ký tự)</h3>
        <label>{day.explain_prompt}</label>
        <textarea rows={3} value={work.explain_answer} onChange={e => set('explain_answer', e.target.value)} />
        <label>Câu hỏi luồng: {day.flow_question}</label>
        <textarea rows={3} value={work.flow_answer} onChange={e => set('flow_answer', e.target.value)} />
        <label>Câu hỏi vai trò: {day.role_question}</label>
        <textarea rows={3} value={work.role_answer} onChange={e => set('role_answer', e.target.value)} />
        <label>Câu biến thể: {day.variant_question}</label>
        <textarea rows={3} value={work.variant_answer} onChange={e => set('variant_answer', e.target.value)} />
        <button onClick={saveWork}>Lưu bài làm</button>
      </div>
      <div className="card">
        <h3>7 cổng hoàn thành {status && <span className="pill">{passedGates}/7</span>}</h3>
        {status ? status.gates.map(g => (
          <p key={g.key} className={g.passed ? 'gate-pass' : 'gate-fail'}>{g.passed ? '✓' : '✗'} {g.label}</p>
        )) : <p>Đang tải…</p>}
        {msg && <p className="ok">{msg}</p>}
        {err && <p className="error">{err}</p>}
        <button onClick={complete} disabled={status?.completed}>Hoàn thành Day {day.number}</button>
        {status?.completed && <p className="ok">Day này đã hoàn thành.</p>}
      </div>
    </div>
  )
}

function ChecklistPage() {
  const [items, setItems] = useState<ChecklistItem[]>([])
  useEffect(() => { api.checklist().then(setItems).catch(() => undefined) }, [])
  const groups = [...new Set(items.map(i => i.group))]
  const done = items.filter(i => i.done).length
  return (
    <div>
      <div className="page-head">
        <h2>Checklist — {done}/{items.length}</h2>
        <p>Chỉ tick khi đã qua đủ 3 bước Viết – Test – Giải thích. Không tick hàng loạt cuối tuần.</p>
      </div>
      <div className="progress progress-lg"><div style={{ width: `${items.length ? (done / items.length) * 100 : 0}%` }} /></div>
      {groups.map(g => (
        <div className="card" key={g}>
          <h3>{g}</h3>
          {items.filter(i => i.group === g).map(i => (
            <label key={i.id} className="check-item">
              <input type="checkbox" checked={i.done}
                onChange={async e => {
                  const updated = await api.toggleChecklist(i.id, e.target.checked)
                  setItems(prev => prev.map(x => x.id === i.id ? updated : x))
                }} />
              <span style={{ textDecoration: i.done ? 'line-through' : 'none' }}>{i.text}</span>
            </label>
          ))}
        </div>
      ))}
    </div>
  )
}

function JournalPage() {
  const [entries, setEntries] = useState<JournalEntry[]>([])
  const [form, setForm] = useState<Omit<JournalEntry, 'id'>>({
    date: new Date().toISOString().slice(0, 10), topic: '', done: '', stuck: '',
    ai_use: '', can_explain: '', next_step: '',
  })
  useEffect(() => { api.journal().then(setEntries).catch(() => undefined) }, [])
  const submit = async () => {
    const created = await api.createJournal(form)
    setEntries(prev => [created, ...prev])
    setForm(f => ({ ...f, topic: '', done: '', stuck: '', ai_use: '', can_explain: '', next_step: '' }))
  }
  return (
    <div>
      <div className="card">
        <h2>Nhật ký buổi học</h2>
        <label>Ngày</label><input type="date" value={form.date} onChange={e => setForm(f => ({ ...f, date: e.target.value }))} />
        <label>Chủ đề</label><input value={form.topic} onChange={e => setForm(f => ({ ...f, topic: e.target.value }))} />
        <label>Đã làm gì</label><textarea rows={2} value={form.done} onChange={e => setForm(f => ({ ...f, done: e.target.value }))} />
        <label>Bị ở đâu</label><textarea rows={2} value={form.stuck} onChange={e => setForm(f => ({ ...f, stuck: e.target.value }))} />
        <label>Dùng AI cho việc gì, trước hay sau khi tự viết</label><textarea rows={2} value={form.ai_use} onChange={e => setForm(f => ({ ...f, ai_use: e.target.value }))} />
        <label>Giải thích lại được không</label><input value={form.can_explain} onChange={e => setForm(f => ({ ...f, can_explain: e.target.value }))} />
        <label>Ngày mai làm gì</label><textarea rows={2} value={form.next_step} onChange={e => setForm(f => ({ ...f, next_step: e.target.value }))} />
        <button onClick={submit}>Lưu nhật ký</button>
      </div>
      {entries.map(e => (
        <div className="card" key={e.id}>
          <h3>{e.date} — {e.topic}</h3>
          <p><b>Đã làm:</b> {e.done}</p><p><b>Bị:</b> {e.stuck}</p>
          <p><b>AI:</b> {e.ai_use}</p><p><b>Giải thích được:</b> {e.can_explain}</p>
          <p><b>Mai:</b> {e.next_step}</p>
          <button className="secondary" onClick={async () => {
            await api.deleteJournal(e.id)
            setEntries(prev => prev.filter(x => x.id !== e.id))
          }}>Xóa</button>
        </div>
      ))}
    </div>
  )
}

function MethodPage() {
  const [m, setM] = useState<{ name: string; steps: { title: string; body: string }[]; ai_rules: string[] } | null>(null)
  useEffect(() => { api.method().then(setM).catch(() => undefined) }, [])
  if (!m) return <p className="loading">Đang tải…</p>
  return (
    <div>
      <div className="page-head">
        <h2>Phương pháp: {m.name}</h2>
        <p>Một chủ đề chỉ tính là xong khi qua đủ 3 bước, theo đúng thứ tự.</p>
      </div>
      {m.steps.map((s, i) => <div className="card step-card" key={s.title}><span className="step-number">Bước {i + 1}</span><h3>{s.title}</h3><p>{s.body}</p></div>)}
      <div className="card"><h3>Quy tắc dùng AI</h3><ul>{m.ai_rules.map((r, i) => <li key={i}>{r}</li>)}</ul></div>
      <div className="card"><h3>Bài kiểm tra hàng ngày</h3>
        <p>Mỗi ngày 45 phút, bắt đầu bằng kiểm tra từ file trống, không AI viết code lõi. Chán thì làm bản micro 15 phút thay vì bỏ hẳn. Fail thì hôm sau làm lại đúng bài đó.</p></div>
    </div>
  )
}
