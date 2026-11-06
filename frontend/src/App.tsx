import { useEffect, useState } from 'react'
import { api, type ChecklistItem, type Day, type DayStatus, type DayWork, type JournalEntry, type Progress, type SkillTree, type Track } from './api'

type Route = { page: 'dashboard' | 'days' | 'day' | 'checklist' | 'journal' | 'method' | 'tree'; dayNumber?: number }

function parseHash(): Route {
  const h = window.location.hash.replace(/^#\/?/, '')
  if (h.startsWith('day/')) return { page: 'day', dayNumber: Number(h.slice(4)) }
  if (h === 'days') return { page: 'days' }
  if (h === 'tree') return { page: 'tree' }
  if (h === 'checklist') return { page: 'checklist' }
  if (h === 'journal') return { page: 'journal' }
  if (h === 'method') return { page: 'method' }
  return { page: 'dashboard' }
}
const go = (hash: string) => { window.location.hash = hash }

const NAV: { hash: string; label: string; page: Route['page'] }[] = [
  { hash: '#/', label: 'Tổng quan', page: 'dashboard' },
  { hash: '#/days', label: 'Ngày 1–14', page: 'days' },
  { hash: '#/tree', label: 'Cây kỹ năng', page: 'tree' },
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
        {route.page === 'tree' && <SkillTreePage tracks={tracks} />}
        {route.page === 'day' && day && <DayDetail day={day} />}
        {route.page === 'day' && !day && tracks.length > 0 && <p>Không tìm thấy Day {route.dayNumber}.</p>}
        {route.page === 'checklist' && <ChecklistPage />}
        {route.page === 'journal' && <JournalPage />}
        {route.page === 'method' && <MethodPage />}
      </main>
      <footer className="site-footer">
        <p>Phương pháp: Viết – Test – Giải thích · Một ngày chỉ tính là xong khi qua đủ 6 cổng.</p>
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
          Mở ngày tiếp theo, làm trắc nghiệm (đạt ≥ 75%), nộp bài tập, xếp đúng luồng chạy,
          bắt đúng lỗi trong code, giải thích lại bằng lời của mình rồi mới bấm hoàn thành.
          Không tick tay khi chưa qua đủ cổng.
        </p>
        <div className="hero-actions">
          <button onClick={() => go(nextDay <= p.total_days ? `#/day/${nextDay}` : '#/days')}>
            {p.completed_days === 0 ? 'Bắt đầu Day 1' : nextDay <= p.total_days ? `Tiếp tục Day ${nextDay}` : 'Xem lại các Day'}
          </button>
          <button className="secondary" onClick={() => go('#/tree')}>Xem cây kỹ năng</button>
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

const TREE_STATE_LABEL: Record<string, string> = {
  mastered: '✓ Đã vững', in_progress: 'Đang học', available: 'Đã mở', locked: '🔒 Chưa mở',
}

function SkillTreePage({ tracks }: { tracks: Track[] }) {
  const [tree, setTree] = useState<SkillTree | null>(null)
  const [error, setError] = useState('')
  useEffect(() => {
    if (tracks.length === 0) return
    api.skillTree(tracks[0].id).then(setTree).catch((e: Error) => setError(e.message))
  }, [tracks])
  if (error) return <p className="error">Không tải được cây kỹ năng: {error}</p>
  if (!tree) return <p className="loading">Đang tải cây kỹ năng…</p>
  return (
    <div>
      <div className="page-head">
        <h2>Cây kỹ năng</h2>
        <p>Đi từ trên xuống theo thứ tự Day: hoàn thành Day trước mới mở Day sau. Đường thân chính
          là 14 Day nối nhau; nhánh rẽ ngang là chủ đề mở rộng gắn với đúng Day liên quan — biết
          nó tồn tại để sau này tự tìm.</p>
      </div>
      <div className="tree-trunk">
        {tree.modules.map(m => (
          <div key={m.module_id} className="tree-module">
            <div className="tree-module-label">
              <span className="tree-dot tree-dot-module" />
              <span>{m.title}</span>
            </div>
            {m.days.map(d => (
              <div key={d.day_id}>
                <div className="tree-row">
                  <span className={`tree-dot tree-dot-${d.state}`} />
                  <button className={`tree-node tree-${d.state}`}
                    disabled={d.state === 'locked'}
                    onClick={() => go(`#/day/${d.number}`)}>
                    <span className="tree-node-number">Day {d.number}</span>
                    <span className="tree-node-title">{d.title.replace(/^Day \d+ — /, '')}</span>
                    <span className="tree-node-state">{TREE_STATE_LABEL[d.state]} · {d.gates_passed}/{d.gates_total} cổng</span>
                  </button>
                </div>
                {m.extensions.filter(e => e.related_day_number === d.number).map(e => (
                  <div key={e.id} className="tree-row tree-row-branch">
                    <div className="tree-node tree-ext">
                      <span className="tree-node-number">Mở rộng · sau Day {e.related_day_number}</span>
                      <span className="tree-node-title">{e.title}</span>
                      <span className="tree-node-state">{e.description}</span>
                    </div>
                  </div>
                ))}
              </div>
            ))}
            {m.extensions.filter(e => !m.days.some(d => d.number === e.related_day_number)).map(e => (
              <div key={e.id} className="tree-row tree-row-branch">
                <div className="tree-node tree-ext">
                  <span className="tree-node-number">Mở rộng</span>
                  <span className="tree-node-title">{e.title}</span>
                  <span className="tree-node-state">{e.description}</span>
                </div>
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  )
}

function badgeLabel(path: string): string {
  if (path.endsWith('main.py')) return 'Điểm vào'
  if (path.includes('/routers/')) return 'Router'
  if (path.includes('/services/')) return 'Service'
  if (path.includes('/repositories/')) return 'Repo'
  if (path.endsWith('schemas.py')) return 'Model'
  if (path.endsWith('models.py')) return 'Bảng DB'
  if (path.endsWith('database.py')) return 'Kết nối'
  if (path.startsWith('tests/')) return 'Test'
  return 'File'
}
const BADGE_CLASS: Record<string, string> = {
  'Điểm vào': 'entry', 'Router': 'router', 'Service': 'service', 'Repo': 'repo',
  'Model': 'model', 'Bảng DB': 'db', 'Kết nối': 'conn', 'Test': 'test', 'File': 'file',
}

interface PTreeNode { name: string; path: string; role?: string; children: Map<string, PTreeNode> }
function buildProjectTree(tree: Record<string, string>): PTreeNode {
  const root: PTreeNode = { name: '', path: '', children: new Map() }
  for (const [p, role] of Object.entries(tree)) {
    const parts = p.split('/')
    let node = root
    parts.forEach((part, i) => {
      const isFile = i === parts.length - 1
      if (!node.children.has(part)) {
        node.children.set(part, {
          name: part, path: parts.slice(0, i + 1).join('/'),
          role: isFile ? role : undefined, children: new Map(),
        })
      }
      node = node.children.get(part)!
    })
  }
  return root
}
function countFiles(n: PTreeNode): number {
  let c = 0
  n.children.forEach(ch => { c += ch.role !== undefined ? 1 : countFiles(ch) })
  return c
}

function ProjectTree({ tree }: { tree: Record<string, string> }) {
  const root = buildProjectTree(tree)
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set())
  const toggle = (path: string) => setCollapsed(prev => {
    const next = new Set(prev)
    if (next.has(path)) next.delete(path)
    else next.add(path)
    return next
  })
  const renderNode = (node: PTreeNode): React.ReactNode => {
    if (node.role !== undefined) {
      const label = badgeLabel(node.path)
      return (
        <div className="ptree-file" key={node.path}>
          <span className="ptree-name">📄 {node.name}</span>
          <span className={`ptree-badge ptree-badge-${BADGE_CLASS[label]}`}>{label}</span>
          <span className="ptree-role">{node.role}</span>
        </div>
      )
    }
    const closed = collapsed.has(node.path)
    return (
      <div className="ptree-folder" key={node.path}>
        <button className="ptree-folder-head" onClick={() => toggle(node.path)}>
          <span>{closed ? '▸' : '▾'}</span> 📁 {node.name}
          <span className="ptree-count">{countFiles(node)} file</span>
        </button>
        {!closed && (
          <div className="ptree-children">
            {[...node.children.values()].map(ch => renderNode(ch))}
          </div>
        )}
      </div>
    )
  }
  return (
    <div className="ptree">
      <p className="ptree-intro">Mỗi file làm đúng một việc — bấm vào thư mục để thu gọn / mở ra.</p>
      {[...root.children.values()].map(ch => renderNode(ch))}
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
    self_note: '', followup_answers: [], summary: '',
  })
  const [msg, setMsg] = useState('')
  const [err, setErr] = useState('')
  // --- v2 interactive state (reset per Day) ---
  // --- flow simulator state (reset per Day) ---
  const [simIdx, setSimIdx] = useState(0)
  const [simStep, setSimStep] = useState(-1) // -1 = chưa chạy; n = đã chạy tới bước n
  const [simRunning, setSimRunning] = useState(false)
  const [codeStep, setCodeStep] = useState<number | null>(null) // bước nào đang mở code
  const sim = day.sim_scenarios[simIdx] ?? null
  const simFinished = !!sim && simStep >= 0 &&
    (simStep === sim.steps.length - 1 || sim.steps[simStep].status === 'fail')
  useEffect(() => {
    if (!simRunning || !sim) return
    if (simFinished || simStep >= sim.steps.length - 1) { setSimRunning(false); return }
    const t = setTimeout(() => setSimStep(s => s + 1), 900)
    return () => clearTimeout(t)
  }, [simRunning, simStep, sim, simFinished])
  const [shuffled, setShuffled] = useState<number[]>([])
  const [picked, setPicked] = useState<number[]>([])
  const [puzzleResult, setPuzzleResult] = useState<{ passed: boolean; first_wrong_position?: number } | null>(null)
  const [puzzleDone, setPuzzleDone] = useState(false)
  const [selLine, setSelLine] = useState<number | null>(null)
  const [selReason, setSelReason] = useState<number | null>(null)
  const [bugResult, setBugResult] = useState<{ passed: boolean; line_correct?: boolean; reason_correct?: boolean } | null>(null)
  const [bugDone, setBugDone] = useState(false)
  const [pasteWarn, setPasteWarn] = useState(false)
  const refreshStatus = async () => {
    const s = await api.dayStatus(day.id)
    setStatus(s)
    const gate = (k: string) => s.gates.find(g => g.key === k)?.passed ?? false
    setPuzzleDone(gate('flow_puzzle'))
    setBugDone(gate('bug'))
  }
  useEffect(() => {
    setAnswers(day.quiz.map(() => -1)); setQuizResult(null); setMsg(''); setErr('')
    setSimIdx(0); setSimStep(-1); setSimRunning(false); setCodeStep(null); setPicked([]); setPuzzleResult(null); setBugResult(null)
    setSelLine(null); setSelReason(null); setPasteWarn(false)
    setShuffled([...day.flow_steps.keys()].sort(() => Math.random() - 0.5))
    refreshStatus().catch(() => undefined)
    api.getWork(day.id).then(w => setWork({
      ...w, self_note: w.self_note ?? '', followup_answers: w.followup_answers ?? [], summary: w.summary ?? '',
    })).catch(() => undefined)
  }, [day.id])
  const submitQuiz = async () => {
    if (answers.some(a => a < 0)) { setErr('Hãy chọn đáp án cho cả 4 câu trước khi nộp.'); return }
    setErr('')
    try {
      const r = await api.submitQuiz(day.id, answers)
      setQuizResult(r)
      await refreshStatus()
    } catch (e) { setErr(e instanceof Error ? e.message : String(e)) }
  }
  const saveWork = async () => {
    setErr(''); setMsg('')
    try {
      await api.saveWork(day.id, work)
      await refreshStatus()
      setMsg('Đã lưu bài làm.')
    } catch (e) { setErr(e instanceof Error ? e.message : String(e)) }
  }
  const submitPuzzle = async () => {
    setErr('')
    if (picked.length !== day.flow_steps.length) { setErr('Hãy xếp đủ các bước vào thứ tự của bạn trước khi nộp.'); return }
    try {
      const r = await api.submitFlowPuzzle(day.id, picked)
      setPuzzleResult(r)
      if (r.passed) { setPuzzleDone(true); await refreshStatus() }
    } catch (e) { setErr(e instanceof Error ? e.message : String(e)) }
  }
  const submitBug = async () => {
    setErr('')
    if (selLine === null || selReason === null) { setErr('Hãy chọn một dòng code và một lý do trước khi nộp.'); return }
    try {
      const r = await api.submitBug(day.id, selLine, selReason)
      setBugResult(r)
      if (r.passed) { setBugDone(true); await refreshStatus() }
    } catch (e) { setErr(e instanceof Error ? e.message : String(e)) }
  }
  const complete = async () => {
    setErr(''); setMsg('')
    try {
      const s = await api.completeDay(day.id)
      setStatus(s); setMsg('Chúc mừng — Day này đã hoàn thành (đủ 6 cổng).')
    } catch (e) {
      const m = e instanceof Error ? e.message : String(e)
      setErr(`Chưa hoàn thành được. Còn thiếu: ${m}`)
      await refreshStatus()
    }
  }
  const set = (k: keyof DayWork, v: string) => setWork(w => ({ ...w, [k]: v }))
  const setFollowup = (i: number, v: string) => setWork(w => {
    const a = [...(w.followup_answers ?? [])]
    while (a.length < 2) a.push('')
    a[i] = v
    return { ...w, followup_answers: a }
  })
  const passedGates = status ? status.gates.filter(g => g.passed).length : 0
  const importanceLabel: Record<string, string> = {
    must: 'Bắt buộc phải vững', should: 'Nên vững', nice: 'Biết thêm thì tốt',
  }
  const bugLines = day.bug_code ? day.bug_code.split('\n') : []
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
              : `Đã qua ${passedGates}/6 cổng · Điểm trắc nghiệm tốt nhất: ${status.best_quiz_score}/${status.best_quiz_total}`}
          </p>
        )}
      </div>
      <div className="card"><h3>Mục tiêu</h3><p>{day.objective}</p>
        <h3>Vai trò trong dự án Booking API</h3><p>{day.role_in_project}</p></div>
      {(day.real_world_use || day.pitfalls.length > 0) && (
        <div className="card ent-card">
          <h3>Thẻ doanh nghiệp — kiến thức này để làm gì</h3>
          <p><span className={`importance-badge importance-${day.importance}`}>
            {importanceLabel[day.importance] ?? 'Nên vững'}</span></p>
          <p>{day.real_world_use}</p>
          <h3>Lỗi người mới hay gặp</h3>
          <ul>{day.pitfalls.map((p, i) => <li key={i}>{p}</li>)}</ul>
        </div>
      )}
      <div className="card"><h3>Mô phỏng luồng — chọn tình huống, chạy từng bước</h3>
        {day.sim_scenarios.length === 0 ? <p>Day này chưa có tình huống mô phỏng.</p> : sim && (<>
          <div className="sim-scenarios">
            {day.sim_scenarios.map((sc, i) => (
              <button key={i} className={`sim-scenario ${i === simIdx ? 'active' : ''}`}
                onClick={() => { setSimIdx(i); setSimStep(-1); setSimRunning(false) }}>{sc.title}</button>
            ))}
          </div>
          <p className="sim-input"><b>Đầu vào:</b></p>
          <pre className="sim-input-pre">{sim.input}</pre>
          <div className="sim-controls">
            <button className="primary" disabled={simRunning || simFinished}
              onClick={() => { if (simStep === -1) setSimStep(0); setSimRunning(true) }}>▶ Chạy mô phỏng</button>
            <button className="secondary" disabled={simRunning || simFinished || simStep >= sim.steps.length - 1}
              onClick={() => setSimStep(s => s + 1)}>Bước tiếp →</button>
            <button className="secondary" disabled={simStep === -1 && !simRunning}
              onClick={() => { setSimStep(-1); setSimRunning(false) }}>Đặt lại</button>
          </div>
          <div className="sim-flow-start">▶ Bắt đầu</div>
          <ol className="sim-track">
            {day.flow_steps.map((s, i) => {
              const st = sim.steps[i]
              const state = i <= simStep ? st.status : (i === simStep + 1 && simRunning ? 'running' : 'pending')
              return (
                <li key={i} className={`sim-step sim-${state}`}>
                  <span className="sim-step-head"><span className="sim-step-icon">
                    {state === 'ok' ? '✓' : state === 'fail' ? '✗' : state === 'skip' ? '–' : state === 'running' ? '▶' : '○'}
                  </span><span><b>Bước {i + 1}:</b> {s}</span></span>
                  {i <= simStep && <span className="sim-step-note">{st.note}</span>}
                  {day.flow_step_code[i] && (<>
                    <button className="sim-code-toggle" onClick={() => setCodeStep(codeStep === i ? null : i)}>
                      {codeStep === i ? '▾ Ẩn code' : '▸ Xem code'}
                    </button>
                    {codeStep === i && (
                      <span className="sim-code-block">
                        <pre className="sim-code">{day.flow_step_code[i].code}</pre>
                        <span className="sim-step-note">{day.flow_step_code[i].note}</span>
                      </span>
                    )}
                  </>)}
                </li>
              )
            })}
          </ol>
          {simFinished && (
            <p className={`sim-result ${sim.steps[simStep].status === 'fail' ? 'sim-result-fail' : ''}`}>
              <b>Kết quả:</b> {sim.result}
            </p>
          )}
        </>)}
        <h3>Cây dự án — file chạm tới</h3>
        <ProjectTree tree={day.project_tree} /></div>
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
        <h3>Flow Puzzle — xếp đúng luồng chạy</h3>
        {puzzleDone ? (
          <p className="ok">Đã xếp đúng luồng — cổng này qua rồi.</p>
        ) : (
          <>
            <p className="muted">Bấm một bước để đưa nó vào thứ tự của bạn. Bấm lại một bước đã xếp để gỡ ra.</p>
            <p><b>Các bước chưa xếp:</b></p>
            <div className="puzzle-pool">
              {shuffled.filter(i => !picked.includes(i)).map(i => (
                <button key={i} className="secondary puzzle-step" onClick={() => setPicked(p => [...p, i])}>
                  {day.flow_steps[i]}
                </button>
              ))}
            </div>
            <p><b>Thứ tự của bạn:</b></p>
            <ol className="puzzle-order">
              {picked.map((i, pos) => (
                <li key={i}><button className="secondary puzzle-step" onClick={() => setPicked(p => p.filter(x => x !== i))}>
                  {pos + 1}. {day.flow_steps[i]} <span aria-hidden>✕</span>
                </button></li>
              ))}
              {picked.length === 0 && <li className="muted">Chưa xếp bước nào.</li>}
            </ol>
            <button onClick={submitPuzzle}>Nộp thứ tự</button>{' '}
            <button className="secondary" onClick={() => { setPicked([]); setPuzzleResult(null); setShuffled([...day.flow_steps.keys()].sort(() => Math.random() - 0.5)) }}>Xếp lại từ đầu</button>
            {puzzleResult && !puzzleResult.passed && (
              <p className="error">Chưa đúng — vị trí đầu tiên sai là bước thứ {(puzzleResult.first_wrong_position ?? 0) + 1} trong thứ tự của bạn. Đọc lại sơ đồ luồng phía trên rồi xếp lại.</p>
            )}
          </>
        )}
      </div>
      <div className="card">
        <h3>Spot the Bug — bắt đúng lỗi trong đoạn code</h3>
        {bugLines.length === 0 ? (
          <p className="muted">Day này chưa có bài Spot the Bug.</p>
        ) : bugDone ? (
          <p className="ok">Đã bắt đúng lỗi — cổng này qua rồi.</p>
        ) : (
          <>
            <p className="muted">Đoạn code dưới đây có đúng <b>một</b> dòng sai. Bấm chọn dòng nghi ngờ, rồi chọn lý do.</p>
            <div className="bug-code">
              {bugLines.map((line, i) => (
                <button key={i} className={`bug-line ${selLine === i ? 'selected' : ''}`} onClick={() => setSelLine(i)}>
                  <span className="bug-line-no">{i}</span><code>{line || ' '}</code>
                </button>
              ))}
            </div>
            <p><b>Vì sao dòng đó sai?</b></p>
            {day.bug_reasons.map((r, i) => (
              <button key={i} className={`quiz-opt ${selReason === i ? 'selected' : ''}`} onClick={() => setSelReason(i)}>
                <span className="quiz-opt-letter">{String.fromCharCode(65 + i)}</span>{r}
              </button>
            ))}
            <button onClick={submitBug}>Nộp đáp án</button>
            {bugResult && !bugResult.passed && (
              <p className="error">
                Chưa đúng — dòng bạn chọn {bugResult.line_correct ? 'đúng' : 'sai'}, lý do bạn chọn {bugResult.reason_correct ? 'đúng' : 'sai'}.
                {bugResult.line_correct ? ' Đọc lại lý thuyết rồi chọn lý do khác.' : ' Đọc kỹ lại từng dòng rồi chọn lại.'}
              </p>
            )}
          </>
        )}
      </div>
      <div className="card">
        <h3>Vòng Feynman — giải thích lại bằng lời của mình</h3>
        <p className="muted">1. Chọn khái niệm (chính là Day này) → 2. Giải thích lại → 3. Trả lời câu biến thể →
          4. Học lại chỗ còn bí → 5. Tóm tắt cuối Day. Còn bí ở cổng nào thì quay lại phần hướng dẫn
          từng bước phía trên, làm lại từ file trống, rồi viết lại bản tóm tắt.</p>
        <label>Giải thích lại bằng lời của mình (ít nhất 2 câu, ≥ 80 ký tự — không copy)</label>
        <textarea rows={4} value={work.self_note}
          onChange={e => set('self_note', e.target.value)}
          onPaste={e => { e.preventDefault(); setPasteWarn(true) }}
          placeholder="Gõ bằng lời của mình — không dán từ nơi khác." />
        {pasteWarn && <p className="error">Đã chặn dán — hãy gõ bằng lời của mình, đó mới là bằng chứng bạn hiểu.</p>}
        {day.followup_questions.map((q, i) => (
          <div key={i}>
            <label>Câu biến thể {i + 1}: {q}</label>
            <textarea rows={3} value={work.followup_answers?.[i] ?? ''} onChange={e => setFollowup(i, e.target.value)} />
          </div>
        ))}
        <label>Bản tóm tắt cuối Day (≥ 80 ký tự, viết như đang dạy lại cho người khác)</label>
        <textarea rows={4} value={work.summary} onChange={e => set('summary', e.target.value)} />
        <h3>5 câu tự kiểm tra cuối Day</h3>
        <p className="muted">4 câu trắc nghiệm ở trên + 1 câu biến thể: <b>{day.variant_question}</b></p>
        <ol>{day.quiz.map(q => <li key={q.id}>{q.question}</li>)}</ol>
        <button onClick={saveWork}>Lưu bài làm</button>
      </div>
      <div className="card">
        <h3>6 cổng hoàn thành {status && <span className="pill">{passedGates}/6</span>}</h3>
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
