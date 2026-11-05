# Personal Learning Tracker — He thong hoc tap ca nhan hoa

He thong hoc theo ngay cho Tuan — thuc tap backend: **1 thang FastAPI
(Giai doan 1–4) roi 2 thang Spring Boot**, tren 1 du an duy nhat la
**Booking API**. Phuong phap: **Viet – Test – Giai thich**.
AI chi review sau khi tu viet va test, khong viet code loi.

Day la repo that (frontend + backend + database), khac voi ban web
artifact truoc day chi chay trong Muse. Repo nay do Muse build giup Tuan;
Tuan tu hoc va tu build Booking API.

## Tinh nang

- **Track → Module → Day**: Track Backend Intern, 3 Module, **14 Day**
  (Module 1 Day 1–7: FastAPI viet API tu dau; Module 2 Day 8–12:
  transaction va trung dong thoi; Module 3 Day 13–14: frontend goi API).
  Giai doan 4 (Deploy) va Spring Boot **chua chia Day** — se them theo
  cung khuon khi toi giai doan do.
- Moi Day co: muc tieu, vai tro trong du an, so do luong, cay du an
  Booking API (file nao lam gi), huong dan tung buoc, **trac nghiem
  4 cau cham that (dat ≥75%, luu diem tot nhat)**, bai tap cuoi ngay,
  va kiem tra hieu bai (nop bai, cau hoi luong, cau hoi vai tro,
  giai thich lai, cau bien the).
- **7 cong hoan thanh 1 Day, server kiem tra** (thieu thi tra ve ly do):
  trac nghiem ≥75%, da nop bai tap, da dan ket qua chay test,
  giai thich lai duoc, tra loi duoc cau hoi luong, cau hoi vai tro,
  cau bien the. Xem `backend/app/services.py::evaluate_day_gates`.
- **Checklist 50 muc** luu ben (hang ngay 8, cuoi tuan 5,
  FastAPI GĐ1 8 / GĐ2 5 / GĐ3 4 / GĐ4 3, Spring Boot 5+4+4+4).
- **Nhat ky buoi hoc** luu/xoa duoc: ngay, chu de, da lam gi, bi o dau,
  dung AI cho viec gi (truoc/sau khi tu viet), giai thich lai duoc khong,
  mai lam gi.
- Dashboard: tien do checklist x/50, tien do theo module, so Day
  hoan thanh, so bai nhat ky.

## Cau truc repo

```
learning-tracker/
├── backend/                 # FastAPI + SQLAlchemy + Pydantic + pytest
│   ├── app/
│   │   ├── main.py          # entrypoint, lifespan seed
│   │   ├── config.py        # DATABASE_URL (SQLite mac dinh)
│   │   ├── database.py      # engine / SessionLocal
│   │   ├── models.py        # Track/Module/Day/Quiz/Checklist/Journal
│   │   ├── schemas.py       # Pydantic schemas
│   │   ├── services.py      # logic thuan: phan loai trung/xung dot, 7 cong
│   │   ├── repositories.py  # chi truy cap DB
│   │   ├── seed.py          # nap seed (idempotent)
│   │   ├── seed_data.py     # noi dung 14 Day, 56 cau trac nghiem, 50 checklist
│   │   └── routers/         # tracks, days, checklist, journal, progress
│   ├── tests/               # pytest: logic trung + gate API
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                # React + Vite + TypeScript (CSS thuan, khong framework UI nang)
│   └── src/
│       ├── App.tsx          # Dashboard / Day list / Day detail / Checklist / Journal / Method
│       └── api.ts           # client goi API
├── docker-compose.yml       # postgres + backend + frontend
├── docs/adding-a-new-track.md
├── .env.example
└── README.md
```

## Chay local (khong can Docker)

```bash
# Backend — http://localhost:8000/docs
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --reload
# DB mac dinh: SQLite file backend/learning_tracker.db (tu tao + seed khi chay lan dau)

# Frontend — http://localhost:5173
cd frontend
npm install
npm run dev
# mac dinh goi API o http://localhost:8000/api (doi qua frontend/.env: VITE_API_URL)
```

## Chay bang Docker Compose

```bash
cp .env.example .env   # tuy chon; compose da co gia tri dev cho Postgres
docker compose up --build
# Frontend: http://localhost:5173 — Backend: http://localhost:8000/docs
```

## Test

```bash
cd backend && .venv/bin/python -m pytest tests/ -q
cd frontend && npm run build   # tsc + vite build
```

## Deploy (chua deploy — chi huong dan)

- **Frontend → Vercel**: import repo GitHub, root directory `frontend`,
  build command `npm run build`, output `dist`, dat bien moi truong
  `VITE_API_URL=https://<backend-url>/api`. Can ket noi Vercel truoc.
- **Backend → Render / Railway**: root directory `backend`,
  build `pip install -r requirements.txt`, start
  `uvicorn app.main:app --host 0.0.0.0 --port $PORT`,
  dat `DATABASE_URL` tro toi Postgres that.
- **Postgres → Neon / Supabase**: tao database free, lay connection
  string dang `postgresql+psycopg://USER:PASSWORD@HOST:5432/DB`,
  dat vao `DATABASE_URL` cua backend. Khong commit URL that vao repo.

## Them ky nang moi

Xem `docs/adding-a-new-track.md`: them Track/Module/Day vao
`backend/app/seed_data.py` theo dung khuon, luat 7 cong chi sua o
`backend/app/services.py::evaluate_day_gates`.

## English summary

A personal day-by-day learning tracker for a backend internship:
1 month FastAPI then 2 months Spring Boot, one project (Booking API),
method Write–Test–Explain. Fullstack monorepo: FastAPI + SQLAlchemy
(SQLite locally, PostgreSQL via `DATABASE_URL`), React + Vite + TypeScript.
14 seeded days with real quizzes (56 questions), a server-enforced
7-gate day-completion rule, 50 checklist items, and a study journal.
Run locally with the commands above; deploy frontend to Vercel,
backend to Render/Railway, Postgres to Neon/Supabase.
