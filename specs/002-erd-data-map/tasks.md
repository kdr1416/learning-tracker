# Tasks — Sơ đồ dữ liệu (ERD) tương tác

- [x] T001 Viết `ERD_STAGES` (5 mốc Day 1, 2, 8, 9, 10) trong `backend/app/seed_data.py`
- [x] T002 Thêm schemas `ErdColumn/ErdTable/ErdStage/ErdOut` trong `backend/app/schemas.py`
- [x] T003 Thêm endpoint `GET /api/erd` trong `backend/app/routers/tracks.py`
- [x] T004 Viết test `backend/tests/test_erd.py` (5 mốc, FK Day 8, UNIQUE Day 9, status Day 10, ghi chú minh họa audit_log) — chạy đỏ trước khi có code
- [x] T005 Chạy pytest toàn bộ, phải pass
- [x] T006 Thêm types + `api.erd()` trong `frontend/src/api.ts`
- [x] T007 Thêm route `#/erd` + mục nav "Bản đồ dữ liệu" trong `frontend/src/App.tsx`
- [x] T008 Viết component `ErdPage`: bộ chọn mốc, sơ đồ 2 bảng, panel chi tiết khi bấm bảng
- [x] T009 CSS cho trang ERD (thẻ bảng, huy hiệu UNIQUE, bảng mờ + nhãn "mở ở Day X", đường nối FK)
- [x] T010 `npm run build` pass
- [x] T011 Kiểm tra jsdom: đổi mốc Day 1→10, bấm bảng audit_log xem SQL, không lỗi JS
- [x] T012 Báo Tuan + hỏi deploy (frontend + backend, backend không cần migration)

## Ghi chú deploy (10/11/2026)

- GitHub snapshot commit a4ef4b345521f9e6921f0a2e76370bfe83435561 (đã xác nhận head
  khớp trước và sau push); sync record đã thêm entry thứ 5 (76 paths).
- Vercel: team tuan-learning-tracker đã kiểm tra Hobby trước khi deploy;
  deployment frontend-f5e587l21.
- Render: deploy thủ công dep-dbp8nr142hec73btt2h0, commit a4ef4b3, Live 10:14.
- Kiểm tra live: /api/health ok, /api/progress 0/50 0/14 giữ nguyên,
  /api/erd trả 5 mốc [1,2,8,9,10], Day 9 có UNIQUE, Day 10 có cột status.
  Frontend production (bundle index-Gn_rYGZK.js) có "Bản đồ dữ liệu",
  erd-stage-btn/erd-table/erd-badge và "Xem code" còn nguyên.

## Ghi chú kiểm tra (10/11/2026)

- pytest: 45 passed (39 cũ + 6 mới test_erd). Chạy bằng `.venv/bin/python -m pytest`
  (lệnh `pytest` trực tiếp không tìm thấy module `app` vì backend/ không nằm trên sys.path).
- jsdom 16/16 pass: đổi mốc Day 1→8→9→10, bấm audit_log xem SQL + ghi chú minh họa,
  huy hiệu 🔒 UNIQUE (Day 9), cột status MỚI + dòng cancelled (Day 10), không lỗi JS.
- Backend chạy local :8000 để kiểm tra, đã tắt sau khi xong. Không tạo file DB lạ trong repo.
- /tmp/pw-check đã bị xóa sau lần thay VM trước — đã cài lại jsdom ở đó.
