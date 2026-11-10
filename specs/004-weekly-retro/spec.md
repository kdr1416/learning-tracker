# Spec — Bản tin tuần (Weekly Retro) theo Module

Branch: `004-weekly-retro` · Ngày: 2026-11-10 · Trạng thái: đã duyệt thiết kế (Tuan, 10/11/2026)

## Bối cảnh

Đề xuất ngày 08/11 (Hạng 3): cuối mỗi tuần (hoặc mỗi Module) hệ thống tự tạo
thẻ nhìn lại theo Gibbs (1988). Tuan duyệt thiết kế 10/11: retro theo Module
(vì dữ liệu thật không lưu ngày hoàn thành Day nên không chia tuần được),
không thêm `completed_at` trong đợt này.

## User stories

- **US1 (P1) — Thấy thẻ Retro khi xong Module.** Trên Dashboard, mỗi Module
  có một thẻ Retro: Day nào xong, cổng nào đang trượt, kỹ năng yếu nhất tính
  từ cổng trượt thật, Day tiếp theo là gì. Module chưa xong thì thẻ chỉ hiện
  tiến độ, chưa mở câu hỏi.
- **US2 (P1) — Viết retro, lưu vào nhật ký.** Module xong hết các Day thì mở
  3 câu hỏi (điều gì chạy tốt / chỗ nào kẹt lâu nhất / tuần sau làm khác gì).
  Trả lời xong lưu thành một bài nhật ký (topic "Retro Module X"). Mỗi Module
  chỉ viết retro một lần.

## Yêu cầu chức năng

- FR-001: `GET /api/retro` trả về từng Module: tổng Day, Day xong, từng Day
  (xong chưa + cổng nào trượt), kỹ năng yếu nhất (cổng trượt nhiều nhất ở
  các Day chưa xong, kèm số lần), Day tiếp theo, `can_retro`, `retro_done`,
  `retro_date`.
- FR-002: Kỹ năng = nhãn của cổng: quiz "Hiểu khái niệm", exercise "Viết code
  chạy được", flow_puzzle "Hiểu luồng chạy", bug "Đọc và bắt lỗi code",
  self_note "Giải thích lại bằng lời mình", summary "Tóm tắt cuối Day".
  Không có cổng trượt thì `weakest_skill` là null.
- FR-003: `POST /api/retro/{module_id}` với `{answers: [3 câu]}`: 404 nếu
  Module không có; 400 nếu chưa xong hết Day; 409 nếu đã viết retro rồi;
  422 nếu câu nào trống. Tạo một `JournalEntry` (ngày hôm nay theo giờ
  TP HCM), trả 201.
- FR-004: Không thêm bảng mới, không migration. Dùng lại bảng nhật ký có sẵn.

## Ngoài phạm vi

- Không làm retro theo tuần thật — cần cột `completed_at` ở DayWork, để sau
  (dữ liệu hiện tại 0 Day xong nên thêm sau không mất gì).
- Không gửi nhắc retro (không cron/email); thẻ chỉ nằm trên Dashboard.
