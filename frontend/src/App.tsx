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

export default function App() {
  const [route, setRoute] = useState<Route>(parseHash())
  const [tracks, setTracks] = useState<Track[]>([])
  const [error, setError] = useState('')
  useEffect(() => {
    const onHash = () => setRoute(parseHash())
    window.addEventListener('hashchange', onHash)
    api.tracks().then(setTracks).catch((e: Error) => setError(
      `Khong ket noi duoc backend (${e.message}). Hay chay backend truoc: cd backend && .venv/bin/uvicorn app.main:app --reload`))
    return () => window.removeEventListener('hashchange', onHash)
  }, [])
  const allDays: Day[] = tracks.flatMap(t => t.modules.flatMap(m => m.days))
  const day = route.dayNumber ? allDays.find(d => d.number === route.dayNumber) : undefined
  return (
    <>
      <header>
        <h1>Learning Tracker — Backend Intern</h1>
        <nav>
          <a href="#/">Dashboard</a><a href="#/days">Day 1–14</a>
          <a href="#/checklist">Checklist</a><a href="#/journal">Nhat ky</a>
          <a href="#/method">Phuong phap</a>
        </nav>
      </header>
      <main>
        {error && <div className="error">{error}</div>}
        {route.page === 'dashboard' && <Dashboard />}
        {route.page === 'days' && <DayList tracks={tracks} />}
        {route.page === 'day' && day && <DayDetail day={day} />}
        {route.page === 'day' && !day && tracks.length > 0 && <p>Khong tim thay Day {route.dayNumber}.</p>}
        {route.page === 'checklist' && <ChecklistPage />}
        {route.page === 'journal' && <JournalPage />}
        {route.page === 'method' && <MethodPage />}
      </main>
    </>
  )
}

function Dashboard() {
  const [p, setP] = useState<Progress | null>(null)
  useEffect(() => { api.progress().then(setP).catch(() => undefined) }, [])
  if (!p) return <p>Dang tai tien do…</p>
  return (
    <div>
      <div className="card">
        <h2>Tong quan</h2>
        <p>Checklist: <b>{p.done_checklist}/{p.total_checklist}</b></p>
        <div className="progress"><div style={{ width: `${p.total_checklist ? (p.done_checklist / p.total_checklist) * 100 : 0}%` }} /></div>
        <p>Day hoan thanh: <b>{p.completed_days}/{p.total_days}</b> — Nhat ky: <b>{p.journal_count}</b> bai</p>
      </div>
      {p.days_by_module.map(m => (
        <div className="card" key={m.module}>
          <h3>{m.module}</h3>
          <p>{m.done}/{m.total} day hoan thanh</p>
          <div className="progress"><div style={{ width: `${m.total ? (m.done / m.total) * 100 : 0}%` }} /></div>
        </div>
      ))}
      <div className="card">
        <h3>Bat dau hom nay</h3>
        <p>Mo Day tiep theo, lam trac nghiem (dat ≥75%), nop bai tap, tra loi 4 cau hieu bai, roi moi bam hoan thanh.</p>
        <button onClick={() => go('#/days')}>Mo danh sach Day</button>
      </div>
    </div>
  )
}

function DayList({ tracks }: { tracks: Track[] }) {
  return (
    <div>
      {tracks.map(t => (
        <div key={t.id}>
          <h2>{t.title}</h2><p>{t.description}</p>
          {t.modules.map(m => (
            <div className="card" key={m.id}>
              <h3>{m.title}</h3><p>{m.description}</p>
              <div className="grid">
                {m.days.map(d => (
                  <button key={d.id} className="secondary" onClick={() => go(`#/day/${d.number}`)}>
                    Day {d.number} — {d.title.replace(/^Day \d+ — /, '')}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      ))}
      <p><i>Giai doan 4 (Deploy) va Spring Boot chua chia Day — se them theo cung khuon Track → Module → Day.</i></p>
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
    if (answers.some(a => a < 0)) { setErr('Hay chon dap an cho ca 4 cau truoc khi nop.'); return }
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
      setMsg('Da luu bai lam.')
    } catch (e) { setErr(e instanceof Error ? e.message : String(e)) }
  }
  const complete = async () => {
    setErr(''); setMsg('')
    try {
      const s = await api.completeDay(day.id)
      setStatus(s); setMsg('Chuc mung — Day nay da hoan thanh (du 7 cong).')
    } catch (e) {
      const m = e instanceof Error ? e.message : String(e)
      setErr(`Chua hoan thanh duoc. Con thieu: ${m}`)
      setStatus(await api.dayStatus(day.id))
    }
  }
  const set = (k: keyof DayWork, v: string) => setWork(w => ({ ...w, [k]: v }))
  return (
    <div>
      <button className="secondary" onClick={() => go('#/days')}>← Tat ca Day</button>
      <h2>Day {day.number} — {day.title}</h2>
      <div className="card"><h3>Muc tieu</h3><p>{day.objective}</p>
        <h3>Vai tro trong du an Booking API</h3><p>{day.role_in_project}</p></div>
      <div className="card"><h3>So do luong</h3><ol>{day.flow_steps.map((s, i) => <li key={i}>{s}</li>)}</ol>
        <h3>Cay du an — file cham toi</h3>
        <pre>{Object.entries(day.project_tree).map(([k, v]) => `${k}\n  → ${v}`).join('\n')}</pre></div>
      <div className="card"><h3>Huong dan tung buoc</h3><ol>{day.guide_steps.map((s, i) => <li key={i}>{s}</li>)}</ol></div>
      <div className="card">
        <h3>Trac nghiem (4 cau, dat ≥75% — diem tot nhat duoc luu)</h3>
        {status && <p>Diem tot nhat: <b>{status.best_quiz_score}/{status.best_quiz_total}</b> {status.quiz_passed ? '— da dat' : '— chua dat'}</p>}
        {day.quiz.map((q, qi) => (
          <div key={q.id} style={{ marginBottom: 16 }}>
            <p><b>Cau {qi + 1}:</b> {q.question}</p>
            {q.options.map((o, oi) => (
              <button key={oi} className={`quiz-opt ${answers[qi] === oi ? 'selected' : ''}`}
                onClick={() => setAnswers(a => a.map((v, i) => i === qi ? oi : v))}>{o}</button>
            ))}
            {quizResult && <p><i>Giai thich: {q.explanation}</i></p>}
          </div>
        ))}
        <button onClick={submitQuiz}>Nop trac nghiem</button>
        {quizResult && <p className={quizResult.passed ? 'ok' : 'error'}>
          Ban duoc {quizResult.score}/{quizResult.total} {quizResult.passed ? '— dat.' : '— chua dat 75%, hay lam lai.'} Diem tot nhat: {quizResult.best_score}/{quizResult.best_total}.</p>}
      </div>
      <div className="card">
        <h3>Bai tap cuoi ngay</h3><p>{day.exercise}</p>
        <p><b>Deliverables:</b></p><ul>{day.exercise_deliverables.map((d, i) => <li key={i}>{d}</li>)}</ul>
        <p><b>Tieu chi pass:</b></p><ul>{day.exercise_pass_criteria.map((d, i) => <li key={i}>{d}</li>)}</ul>
        <label>Bai nop (code / link / mo ta ngan)</label>
        <textarea rows={4} value={work.exercise_submission} onChange={e => set('exercise_submission', e.target.value)} />
        <label>Ket qua chay test (dan output pytest, vd: 4/4 passed)</label>
        <textarea rows={2} value={work.test_result} onChange={e => set('test_result', e.target.value)} />
      </div>
      <div className="card">
        <h3>Kiem tra hieu bai (moi cau can ≥20 ky tu)</h3>
        <label>{day.explain_prompt}</label>
        <textarea rows={3} value={work.explain_answer} onChange={e => set('explain_answer', e.target.value)} />
        <label>Cau hoi luong: {day.flow_question}</label>
        <textarea rows={3} value={work.flow_answer} onChange={e => set('flow_answer', e.target.value)} />
        <label>Cau hoi vai tro: {day.role_question}</label>
        <textarea rows={3} value={work.role_answer} onChange={e => set('role_answer', e.target.value)} />
        <label>Cau bien the: {day.variant_question}</label>
        <textarea rows={3} value={work.variant_answer} onChange={e => set('variant_answer', e.target.value)} />
        <button onClick={saveWork}>Luu bai lam</button>
      </div>
      <div className="card">
        <h3>7 cong hoan thanh</h3>
        {status ? status.gates.map(g => (
          <p key={g.key} className={g.passed ? 'gate-pass' : 'gate-fail'}>{g.passed ? '✓' : '✗'} {g.label}</p>
        )) : <p>Dang tai…</p>}
        {msg && <p className="ok">{msg}</p>}
        {err && <p className="error">{err}</p>}
        <button onClick={complete} disabled={status?.completed}>Hoan thanh Day {day.number}</button>
        {status?.completed && <p className="ok">Day nay da hoan thanh.</p>}
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
      <h2>Checklist — {done}/{items.length}</h2>
      <div className="progress"><div style={{ width: `${items.length ? (done / items.length) * 100 : 0}%` }} /></div>
      {groups.map(g => (
        <div className="card" key={g}>
          <h3>{g}</h3>
          {items.filter(i => i.group === g).map(i => (
            <label key={i.id} style={{ fontWeight: 'normal', display: 'flex', gap: 8, alignItems: 'flex-start' }}>
              <input type="checkbox" style={{ width: 'auto' }} checked={i.done}
                onChange={async e => {
                  const updated = await api.toggleChecklist(i.id, e.target.checked)
                  setItems(prev => prev.map(x => x.id === i.id ? updated : x))
                }} />
              <span style={{ textDecoration: i.done ? 'line-through' : 'none' }}>{i.text}</span>
            </label>
          ))}
        </div>
      ))}
      <p><i>Chi tick khi da qua du 3 buoc Viet - Test - Giai thich. Khong tick hang loat cuoi tuan.</i></p>
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
        <h2>Nhat ky buoi hoc</h2>
        <label>Ngay</label><input type="date" value={form.date} onChange={e => setForm(f => ({ ...f, date: e.target.value }))} />
        <label>Chu de</label><input value={form.topic} onChange={e => setForm(f => ({ ...f, topic: e.target.value }))} />
        <label>Da lam gi</label><textarea rows={2} value={form.done} onChange={e => setForm(f => ({ ...f, done: e.target.value }))} />
        <label>Bi o dau</label><textarea rows={2} value={form.stuck} onChange={e => setForm(f => ({ ...f, stuck: e.target.value }))} />
        <label>Dung AI cho viec gi, truoc hay sau khi tu viet</label><textarea rows={2} value={form.ai_use} onChange={e => setForm(f => ({ ...f, ai_use: e.target.value }))} />
        <label>Giai thich lai duoc khong</label><input value={form.can_explain} onChange={e => setForm(f => ({ ...f, can_explain: e.target.value }))} />
        <label>Ngay mai lam gi</label><textarea rows={2} value={form.next_step} onChange={e => setForm(f => ({ ...f, next_step: e.target.value }))} />
        <button onClick={submit}>Luu nhat ky</button>
      </div>
      {entries.map(e => (
        <div className="card" key={e.id}>
          <h3>{e.date} — {e.topic}</h3>
          <p><b>Da lam:</b> {e.done}</p><p><b>Bi:</b> {e.stuck}</p>
          <p><b>AI:</b> {e.ai_use}</p><p><b>Giai thich duoc:</b> {e.can_explain}</p>
          <p><b>Mai:</b> {e.next_step}</p>
          <button className="secondary" onClick={async () => {
            await api.deleteJournal(e.id)
            setEntries(prev => prev.filter(x => x.id !== e.id))
          }}>Xoa</button>
        </div>
      ))}
    </div>
  )
}

function MethodPage() {
  const [m, setM] = useState<{ name: string; steps: { title: string; body: string }[]; ai_rules: string[] } | null>(null)
  useEffect(() => { api.method().then(setM).catch(() => undefined) }, [])
  if (!m) return <p>Dang tai…</p>
  return (
    <div>
      <h2>Phuong phap: {m.name}</h2>
      {m.steps.map(s => <div className="card" key={s.title}><h3>{s.title}</h3><p>{s.body}</p></div>)}
      <div className="card"><h3>Quy tac dung AI</h3><ul>{m.ai_rules.map((r, i) => <li key={i}>{r}</li>)}</ul></div>
      <div className="card"><h3>Bai kiem tra hang ngay</h3>
        <p>Moi ngay 45 phut, bat dau bang kiem tra tu file trong, khong AI viet code loi. Chan thi lam ban micro 15 phut thay vi bo han. Fail thi hom sau lam lai dung bai do.</p></div>
    </div>
  )
}
