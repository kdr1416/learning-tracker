# Plan — Spot the Bug thành So sánh đối chứng

## Quyết định

- **Dữ liệu:** `Day.correct_code` (Text, server_default `''`); migration thêm
  `("days", "correct_code", "TEXT", "''")` vào `migrate.py`; seed qua
  `_day_fields` (`d.get("correct_code", "")`) để refresh cập nhật nội dung cũ.
- **Diff:** helper `diff_bug_lines(bug_code, correct_code)` trong
  `routers/days.py`, dùng `difflib.SequenceMatcher(autojunk=False)` trên list
  dòng; opcode `replace`/`delete` → chỉ số 0-based bên code sai,
  `replace`/`insert` → chỉ số 0-based bên code đúng. Tập diff của 4 Day:
  Day 2 `[3]`, Day 3 `[6]`, Day 5 `[2, 3]`, Day 9 `[7]` — đều chứa `bug_line` cũ.
- **Endpoint:** `submit_bug` giữ kiểm tra phạm vi line/reason; khi Day có
  `correct_code` thì `line_ok = line in diff_lines`, ngược lại
  `line_ok = line == bug_line`. Trả `diff_lines` + `diff_lines_correct` trong
  cả hai trường hợp đúng/sai (chỉ sau khi nộp, không lộ qua `DayOut`).
- **Chống rò rỉ:** bỏ `bug_line` và `bug_correct_reason` khỏi `DayOut` và
  `_day_out` (frontend không dùng hai trường này; test dùng trực tiếp model).
- **Frontend:** `Day.correct_code` trong `api.ts`; khi có `correct_code` thì
  section Spot the Bug vẽ hai cột: bên sai bấm chọn dòng được, bên đúng chỉ
  xem; sau khi nộp (`bugResult` khác null) tô sáng `diff_lines` /
  `diff_lines_correct`. `BugOut` type thêm hai trường diff.
- **Kiểm thử:** `tests/test_bug_contrast.py`: 4 Day nhận đúng dòng diff (kể
  cả dòng 2 của Day 5), từ chối dòng ngoài diff, `diff_lines` trả về đúng,
  Day không có `correct_code` vẫn chấm theo `bug_line`, `DayOut` không còn
  `bug_line`/`bug_correct_reason`.

## Thứ tự làm

A. Model + migration + seed + endpoint + test → B. Frontend contrast + CSS →
C. Build + jsdom (Day 2: chọn dòng 3 đúng, chọn dòng 0 sai + tô sáng sau nộp).
