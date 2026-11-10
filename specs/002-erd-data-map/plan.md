# Plan — Sơ đồ dữ liệu (ERD) tương tác

## Quyết định

- **Nguồn dữ liệu:** `ERD_STAGES` trong `backend/app/seed_data.py`, phục vụ qua
  endpoint tĩnh `GET /api/erd` trong `routers/tracks.py` — cùng mẫu với
  `METHOD` (`GET /api/method`). Không tạo bảng database, không migration.
- **Hình dạng dữ liệu mỗi mốc:** `{day, title, note, tables: [{name, kind,
  note, columns: [{name, type, note, badge?, is_new?}], rows: [[...]],
  sql, fk?: {column, to_table, to_column}}], illustration_note?}`.
  `kind`: `model` (Day 1, chỉ Pydantic), `dict` (Day 2, dict bộ nhớ),
  `table` (Day 8+). `badge: "UNIQUE"` cho cột `start` từ Day 9.
  `is_new: true` cho cột `status` ở Day 10.
- **Dòng mẫu:** bookings b1 An `2026-11-07T10:00`–`11:00`, b2 Bình
  `2026-11-07T13:00`–`14:00` (Day 10: status `confirmed` / `cancelled`).
  audit_log: 1 dòng mẫu `booking_id=b1, action=created` (minh họa).
- **Frontend:** trang `#/erd` (`ErdPage` trong `App.tsx`), mục nav "Bản đồ dữ
  liệu"; bộ chọn 5 mốc; sơ đồ 2 thẻ bảng nằm ngang, bảng chưa xuất hiện thì mờ
  + nhãn "mở ở Day X"; đường nối FK vẽ bằng CSS giữa 2 thẻ (Day 8+); bấm thẻ
  bảng → panel chi tiết (cột, dòng mẫu, SQL). CSS thuần, không thư viện.
- **Kiểm thử:** test endpoint (`tests/test_erd.py`): đúng 5 mốc theo thứ tự,
  Day 8 có FK, Day 9 có UNIQUE, Day 10 có cột status, audit_log có ghi chú
  minh họa. jsdom: đổi mốc, bấm bảng, xem SQL.

## Thứ tự làm

A. Nội dung `ERD_STAGES` + endpoint + test → B. Frontend `#/erd` + CSS →
C. Build + jsdom → D. Deploy (chờ Tuan duyệt riêng).
