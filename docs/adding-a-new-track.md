# Them Track / Module / Day moi (dung lai cho ky nang khac)

He thong nay khong cung ten FastAPI hay Booking API vao schema DB.
Cau truc chung: **Track → Module → Day → QuizQuestion**, kem
**ChecklistItem** va **JournalEntry** dung chung cho moi track.

## Cach 1 — nhanh nhat: them vao seed (cho track moi)

1. Mo `backend/app/seed_data.py`.
2. Them 1 Track moi vao `TRACK`/`MODULES`/`DAYS` (hoac tao file
   `seed_data_<skill>.py` rieng roi import vao `seed.py`).
3. Moi Day can co:
   - `objective`, `role` (vai tro trong du an that cua ky nang do)
   - `flow` (so do luong, list cac buoc)
   - `guide` (huong dan tung buoc)
   - `quiz`: dung 4 cau, moi cau co `options` (4 lua chon),
     `correct_index` va `explanation` — cau hoi phai gan voi bai tap that,
     khong viet cau chung chung.
   - `exercise` + `deliverables` + `pass` (tieu chi pass cu the)
   - `flow_q`, `role_q`, `variant_q`, `explain` (4 cau hieu bai)
4. Xoa DB dev (`rm backend/learning_tracker.db`) roi chay lai backend —
   `seed()` chi chay khi DB trong, nen no se nap track moi.
   Chu y: cach nay chi dung cho DB dev. Voi DB that, viet migration/
   script seed rieng, dung xoa DB.

## Cach 2 — dung API (khi da co admin)

Hien tai API chi co GET tracks va cac endpoint tien do; endpoint
POST /api/tracks (tao track/module/day) chua co — them no vao
`backend/app/routers/tracks.py` theo dung mau router/service/repository
da co, roi frontend goi no tu 1 trang Admin don gian.

## Quy tac 7 cong (khong doi theo ky nang)

1. Trac nghiem dat ≥75% (diem tot nhat)
2. Da nop bai tap cuoi ngay
3. Da dan ket qua chay test
4. Giai thich lai duoc (≥20 ky tu)
5. Tra loi duoc cau hoi luong
6. Tra loi duoc cau hoi vai tro
7. Tra loi duoc cau bien the

Sua luat nay thi sua o `backend/app/services.py::evaluate_day_gates`
(1 cho duy nhat) — dung sua rac rac o router hay frontend.
