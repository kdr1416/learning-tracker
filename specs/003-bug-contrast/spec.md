# Spec — Spot the Bug thành So sánh đối chứng

Branch: `003-bug-contrast` · Ngày: 2026-11-10 · Trạng thái: đã duyệt thiết kế (Tuan, 10/11/2026)

## Bối cảnh

Spot the Bug hiện tại chỉ đưa một đoạn code sai rồi hỏi "sai dòng nào".
Đề xuất ngày 08/11 (Hạng 2): đặt code sai và code đúng cạnh nhau để so sánh
đối chứng (Schwartz & Bransford 1998). Tuan duyệt thiết kế 10/11: KHÔNG tô
sáng trước khi nộp — người học tự tìm chỗ khác nhau rồi mới tô sáng sau khi nộp.

## User stories

- **US1 (P1) — So sánh hai bản.** Ở Day 2, 3, 5, 9, trang Day hiện hai đoạn
  code cạnh nhau ("Code sai" / "Code đúng"), chưa tô sáng chỗ nào.
- **US2 (P1) — Chỉ ra chỗ khác + lý do.** Người học bấm chọn dòng khác nhau
  bên code sai, rồi chọn 1 trong 4 lý do, rồi nộp. Server chấp nhận bất kỳ
  dòng nào nằm trong tập hợp các dòng khác nhau (Day 3 khác 1 dòng, Day 5
  khác 2 dòng).
- **US3 (P2) — Tô sáng sau khi nộp.** Sau khi nộp (đúng hay sai), chỗ khác
  được tô sáng ở cả hai bên + phản hồi dòng/lý do đúng-sai như cũ. Nộp đúng
  cả hai thì cổng bug qua.

## Yêu cầu chức năng

- FR-001: Thêm cột `correct_code` cho Day (migration + seed + DayOut). Chỉ
  4 Day nút thắt có nội dung: Day 2 (`bookings[b.id]`), Day 3 (`and` thay
  `or`), Day 5 (bỏ `raise` khỏi repository), Day 9 (`return 409`).
- FR-002: Server tự tính tập dòng khác nhau bằng difflib giữa `bug_code` và
  `correct_code` (tọa độ 0-based, khớp quy ước `bug_line` hiện tại).
- FR-003: `POST /api/days/{id}/bug` chấp nhận line thuộc tập diff khi Day có
  `correct_code`; các Day khác giữ nguyên so sánh `line == bug_line`.
- FR-004: `BugOut` thêm `diff_lines` (bên code sai) và `diff_lines_correct`
  (bên code đúng), trả về sau mỗi lần nộp.
- FR-005: `DayOut` KHÔNG còn gửi `bug_line` và `bug_correct_reason` ra
  browser — đáp án đã lọt ra ngoài qua `_day_out` dù type frontend cố tình
  giấu; tính năng mới đặt code đúng cạnh code sai nên không thể để đáp án
  nằm sẵn trong cùng payload. (Sửa rò rỉ có sẵn, không đổi hành vi chấm.)
- FR-006: Các Day không có `correct_code` giữ nguyên giao diện một đoạn code.

## Ngoài phạm vi

- Không đổi luật cổng bug (vẫn cần đúng cả dòng và lý do), không đổi quiz hay
  các cổng khác. Không thêm cột `bug_diff_lines` — diff tính lúc chạy.
