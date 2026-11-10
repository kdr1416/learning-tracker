# Tasks — Spot the Bug thành So sánh đối chứng

- [x] T001 Thêm cột `correct_code` vào model `Day` + migration `migrate.py`
- [x] T002 Thêm `correct_code` cho Day 2, 3, 5, 9 trong `seed_data.py` + `_day_fields` trong `seed.py`
- [x] T003 Thêm `correct_code` vào `DayOut`, bỏ `bug_line` + `bug_correct_reason` khỏi `DayOut` và `_day_out`
- [x] T004 Helper `diff_bug_lines` (difflib) + sửa `submit_bug` nhận dòng thuộc tập diff, trả `diff_lines`/`diff_lines_correct` trong `BugOut`
- [x] T005 Viết test `backend/tests/test_bug_contrast.py` — chạy đỏ trước khi có code
- [x] T006 Chạy pytest toàn bộ, phải pass
- [x] T007 Thêm `correct_code` + diff vào type `Day`/`BugOut` trong `frontend/src/api.ts`
- [x] T008 Giao diện đối chứng 2 cột trong `DayDetail` (chỉ khi có `correct_code`), tô sáng sau khi nộp
- [x] T009 CSS cho layout đối chứng + dòng tô sáng
- [x] T010 `npm run build` pass
- [x] T011 Kiểm tra jsdom trên Day 2: chọn dòng 3 → pass; chọn dòng 0 → fail + tô sáng dòng 3 sau khi nộp
- [ ] T012 Báo Tuan (gộp chung với Hạng 3) + hỏi deploy

## Ghi chú kiểm tra (10/11/2026)

- pytest: 57 passed toàn bộ (51 trước đó + 6 test_bug_contrast mới).
- jsdom 6/6 pass: Day 2 chọn sai dòng 0 → "Chưa đúng" + tô sáng 2 dòng diff;
  chọn dòng 3 + lý do C → qua cổng; Day 5 chọn dòng 2 (trong tập diff,
  khác bug_line=3) + lý do B → qua cổng; Day 1 giữ giao diện 1 đoạn code.
- Sửa rò rỉ đáp án có sẵn: `_day_out` từng gửi cả `bug_line` và
  `bug_correct_reason` ra browser (dù type frontend cố tình giấu) — đã bỏ
  khỏi DayOut, test `test_day_out_hides_answer_key` khóa lại.
- Bài học jsdom: giữa các lần .click() cần chờ ~300ms để React kịp cập nhật
  state; test fail phải chạy TRƯỚC test pass (pass đổi bug_passed làm form
  biến mất ở lần tải sau); pkill -f tự giết shell của mình khi lệnh chứa
  literal "8000" — giết backend local bằng PID thật, không dùng pkill.
- Lỗi merge seed_data: chèn dict entry bằng script phải nhớ dấu phẩy cuối
  dòng mới (đã sửa 2 lần: thừa dấu phẩy sau bug_line, thiếu dấu phẩy sau
  correct_code).
