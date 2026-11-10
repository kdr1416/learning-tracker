# Plan — Bản tin tuần (Weekly Retro) theo Module

## Quyết định

- **Tính toán ở server:** router mới `backend/app/routers/retro.py`, đăng ký
  trong `main.py` (prefix `/api`). Tái dùng `_status` từ `routers/days.py`
  để lấy gates từng Day (không viết lại luật cổng).
- **Kỹ năng yếu nhất:** đếm cổng trượt trên các Day CHƯA xong trong Module
  (Day xong rồi thì cổng qua hết, không tính). Hòa nhau thì lấy cổng có thứ
  tự ưu tiên theo danh sách gates (quiz → exercise → flow_puzzle → bug →
  self_note → summary).
- **Nhận biết đã retro:** `JournalEntry.topic == "Retro Module {order}: {title}"`
  (chuỗi cố định, một Module một bài). `retro_date` lấy từ entry đó.
- **Ngày:** server lấy ngày hôm nay theo `ZoneInfo("Asia/Ho_Chi_Minh")`
  (không tin ngày client gửi).
- **Frontend:** section "Nhìn lại theo Module" trên Dashboard
  (`RetroSection` trong `App.tsx`): mỗi Module một thẻ; Module xong + chưa
  retro thì hiện 3 textarea + nút lưu; đã retro thì hiện ngày đã viết + nút
  xem nhật ký. `api.ts` thêm types + `api.retro()` / `api.saveRetro()`.
- **Kiểm thử:** `tests/test_retro.py`: Module chưa xong → `can_retro` false,
  POST → 400; xong hết Day → `can_retro` true + `weakest_skill` đúng cổng
  trượt nhiều nhất; POST tạo đúng 1 journal entry đúng topic; POST lần 2 →
  409; câu trống → 422; Module không có → 404.

## Thứ tự làm

A. Schemas + router + test → B. Frontend RetroSection + CSS → C. Build +
jsdom (Dashboard hiện thẻ Retro, lưu thử 3 câu) → D. Deploy gộp với Hạng 2
(chờ Tuan duyệt riêng).
