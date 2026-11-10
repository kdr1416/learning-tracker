# Tasks — Bản tin tuần (Weekly Retro) theo Module

- [x] T001 Thêm schemas `RetroDayOut`/`RetroModuleOut`/`RetroIn` trong `backend/app/schemas.py`
- [x] T002 Viết router `backend/app/routers/retro.py` (GET /api/retro, POST /api/retro/{module_id}) + đăng ký trong `main.py`
- [x] T003 Viết test `backend/tests/test_retro.py` — chạy đỏ trước khi có code
- [x] T004 Chạy pytest toàn bộ, phải pass
- [x] T005 Thêm types + `api.retro()`/`api.saveRetro()` trong `frontend/src/api.ts`
- [x] T006 Thêm `RetroSection` trên Dashboard trong `frontend/src/App.tsx`
- [x] T007 CSS cho thẻ Retro
- [x] T008 `npm run build` pass
- [x] T009 Kiểm tra jsdom: Dashboard hiện thẻ Retro Module 1 (chưa xong → chưa mở câu hỏi); sau khi xong Module 1 (bằng dữ liệu test) thì lưu được 3 câu
- [ ] T010 Báo Tuan (gộp chung với Hạng 2) + hỏi deploy

## Ghi chú kiểm tra (10/11/2026)

- pytest: 57 passed toàn bộ (51 trước đó + 6 test_retro mới).
- jsdom: Dashboard hiện section "Nhìn lại theo Module"; Module 1 chưa xong
  thì thẻ "Chưa mở"; xong hết 7 Day thì hiện 3 ô trả lời, lưu xong báo
  "Đã lưu retro", tải lại hiện "Đã viết retro ngày ...", journal có đúng
  1 entry topic "Retro Module 1: ..." với đủ 3 câu trả lời.
- Lưu ý: 1 assert jsdom ban đầu sai (kiểm tra "Chưa mở" biến mất khỏi toàn
  trang trong khi Module 2/3 vẫn chưa xong nên vẫn hiện) — không phải lỗi app.
- DB local đã xóa file learning_tracker.db sau khi kiểm tra xong và khởi động
  lại sạch: health ok, tiến độ 0/50 0/14, retro 0/7 0/5 0/2, Day 2 có
  correct_code. Không đụng tới Neon production.
