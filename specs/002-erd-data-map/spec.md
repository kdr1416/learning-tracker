# Spec — Sơ đồ dữ liệu (ERD) tương tác của Booking API

Branch: `002-erd-data-map` · Ngày: 2026-11-10 · Trạng thái: đã duyệt thiết kế (Tuan, 10/11/2026)

## Bối cảnh

Cây dự án cho thấy code nằm ở file nào, nhưng chưa cho thấy dữ liệu sống ở đâu.
Đề xuất ngày 08/11 (Hạng 1): thêm tab "Bản đồ dữ liệu" — sơ đồ 2 bảng
`bookings` và `audit_log` lớn dần theo từng Day. Tuan đã duyệt thiết kế
10/11/2026 (xem thiết kế 5 đoạn trong chat ai-job-search cùng ngày).

## User stories

- **US1 (P1) — Xem sơ đồ dữ liệu theo Day.** Người học mở tab "Bản đồ dữ liệu",
  chọn một mốc Day (1, 2, 8, 9, 10) và thấy đúng trạng thái lưu trữ của Day đó:
  Day 1 chỉ có model Pydantic, chưa lưu gì; Day 2 dict trong bộ nhớ; Day 8 hai
  bảng thật với đường nối khóa ngoại; Day 9 thêm huy hiệu 🔒 UNIQUE; Day 10
  thêm cột `status`.
- **US2 (P1) — Bấm vào bảng xem chi tiết.** Bấm vào một bảng thì panel chi tiết
  hiện: các cột, 2 dòng mẫu thật (b1 của An, b2 của Bình) và đoạn SQL migration.
- **US3 (P2) — Thấy ràng buộc xuất hiện đúng Day.** Huy hiệu UNIQUE chỉ xuất
  hiện từ Day 9, cột `status` chỉ xuất hiện từ Day 10, bảng `audit_log` chỉ
  xuất hiện từ Day 8 (trước đó hiện mờ kèm nhãn "mở ở Day 8").

## Yêu cầu chức năng

- FR-001: `GET /api/erd` trả về đúng 5 mốc theo thứ tự Day [1, 2, 8, 9, 10].
- FR-002: Mỗi mốc có đủ: tiêu đề, ghi chú ngắn, danh sách bảng; mỗi bảng có
  tên, loại (`model` | `dict` | `table`), các cột (tên, kiểu, ghi chú), dòng mẫu,
  đoạn SQL (có thể rỗng khi chưa có bảng).
- FR-003: Mốc Day 8 có đường nối khóa ngoại `audit_log.booking_id → bookings.id`.
- FR-004: Mốc Day 9 gắn badge UNIQUE cho cột `start` của `bookings`; mốc Day 10
  thêm cột `status` vào `bookings` (đánh dấu "mới").
- FR-005: Cột của `audit_log` được ghi rõ là minh họa (Day 8 chỉ nói INSERT
  audit_log, seed không định nghĩa cột thật) — hiển thị chú thích "minh họa,
  chốt cột thật khi triển khai".
- FR-006: Trang `#/erd` có bộ chọn mốc Day, sơ đồ 2 bảng, panel chi tiết khi
  bấm vào bảng. Không gắn cổng, không ảnh hưởng tiến độ hay mở khóa Day.
- FR-007: Không thêm bảng database, không migration, không thêm dịch vụ trả phí.

## Ngoài phạm vi

- Không cho sửa nội dung ERD qua giao diện (admin repo như các nội dung khác).
- Không thêm mốc cho các Day khác (3–7, 11–14: cách lưu dữ liệu không đổi).
- Không gắn ERD vào cổng hoàn thành Day hay quiz.
