# Feature Specification: Learning Tracker v2 — Feynman + Skill Tree + Enterprise Context + Anti-AI Gates

**Feature Branch**: `001-learning-tracker-v2`

**Created**: 2026-11-06

**Status**: Draft — awaiting Tuan's approval before plan/tasks/implementation

**Input**: User description: "Thiết lập trang web học theo phương pháp Feynman kết hợp
phương pháp cá nhân hoá Viết - Test - Giải thích. Bài học chia theo chủ đề, kỹ năng,
có module cùng bài học theo ngày (ví dụ chủ đề FastAPI). Có hướng dẫn, lý thuyết đơn
giản, sơ đồ luồng tương tác, bài tập nghiệm thu cho từng ngày, kiểm tra đảm bảo hiểu
nhuần nhuyễn cách dùng và vai trò của bài học trong đồ án thực tế. Thêm: (1) Bản đồ
Cây Kiến Thức với 4 trạng thái; (2) Thẻ Thông Tin Thực Tế Doanh Nghiệp cho mỗi chủ đề;
(3) Cơ chế Active Recall chống phụ thuộc AI: Flow Puzzle, Spot the Bug, Self-Note
chặn paste. Muse là admin, có thể kết nối MCP để thêm/sửa bài học, chủ đề, nội dung."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Hoàn thành 1 Day bằng phương pháp Feynman thống nhất (Priority: P1)

Tuan mở một Day (ví dụ Day 1 Pydantic), học lý thuyết ngắn gọn và sơ đồ luồng, tự
viết code từ file trống và chạy test, rồi đi qua vòng Feynman ngay trong trang Day:
chọn khái niệm chính → giải thích bằng lời của mình như đang dạy người mới → hệ
thống hỏi lại 1–2 câu xoáy vào chỗ hổng (câu biến thể đổi điều kiện) → học lại đúng
phần hổng → giải thích lại gọn hơn → ra bản tóm tắt cuối Day. Chỉ khi qua đủ mọi
cổng thì Day mới được tính hoàn thành; fail cổng nào thì làm lại đúng Day đó.

**Why this priority**: Đây là lõi của v2 — nếu vòng Feynman không ép được hiểu thật
thì mọi tính năng khác chỉ là trang trí. Nó thay thế bộ 7 cổng v1 bằng một bộ cổng
thống nhất, không để hai checklist song song.

**Independent Test**: Mở Day 1 trên bản deploy, làm đủ các cổng và thấy Day chuyển
thành hoàn thành; bỏ qua một cổng (ví dụ không trả lời câu biến thể) thì Day vẫn
chưa hoàn thành và server trả về danh sách cổng còn thiếu.

**Acceptance Scenarios**:

1. **Given** Day chưa hoàn thành, **When** Tuan nộp đủ mọi cổng (quiz ≥75%, bài tập +
   kết quả test, Flow Puzzle đúng, Spot the Bug đúng, Self-Note + câu biến thể đúng,
   bản tóm tắt cuối Day), **Then** server đánh dấu Day hoàn thành và cây kiến thức
   chuyển Day đó sang trạng thái Mastered.
2. **Given** Day chưa hoàn thành, **When** Tuan nộp thiếu một cổng, **Then** server
   trả HTTP 400 kèm danh sách cổng còn thiếu, Day vẫn chưa hoàn thành.
3. **Given** Tuan trả lời sai câu biến thể, **When** hệ thống chỉ ra phần hổng và
   yêu cầu giải thích lại, **Then** Tuan có thể nộp lại giải thích mà không mất các
   cổng đã qua.
4. **Given** một Day đã hoàn thành ở v1 (7 cổng cũ), **When** hệ thống nâng cấp lên
   v2, **Then** Day đó vẫn giữ trạng thái hoàn thành (grandfathered), không bắt làm
   lại các cổng mới.

### User Story 2 — Nhìn cây kiến thức và biết mình đang ở đâu (Priority: P1)

Tuan mở trang tổng quan và thấy cây kiến thức của track Backend Intern: các nhánh
từ cơ bản đến nâng cao (Module 1 → Module 2 → Module 3), mỗi Day là một node với 1
trong 4 trạng thái: Mastered (đã tự code và qua đủ cổng), In Progress (đang học),
Available (đã mở khóa, nhánh kế tiếp), Unexplored Scope (kiến thức mở rộng liên quan
mà người mới thường không biết để tự tìm — ví dụ học xong đăng nhập cơ bản thì gợi
ý Bcrypt, hết hạn phiên). Day chưa mở khóa không vào được.

**Why this priority**: Cây kiến thức là bản đồ điều hướng chính của v2; không có nó
thì các Day rời rạc như v1 và Tuan không thấy được vùng mù của mình.

**Independent Test**: Mở trang cây kiến thức, thấy đủ 14 Day với trạng thái đúng theo
tiến độ thật (hiện tại 0/14), bấm vào node Unexplored Scope thấy gợi ý mở rộng.

**Acceptance Scenarios**:

1. **Given** Tuan chưa hoàn thành Day nào, **When** mở cây kiến thức, **Then** chỉ
   Day 1 ở trạng thái Available, Day 2–14 Locked (chưa mở khóa), các node mở rộng
   hiện ở trạng thái Unexplored Scope.
2. **Given** Tuan hoàn thành Day 1, **When** mở lại cây, **Then** Day 1 chuyển sang
   Mastered, Day 2 chuyển sang Available.
3. **Given** một Day đang làm dở (đã qua ít nhất 1 cổng), **When** mở cây, **Then**
   Day đó hiện In Progress.
4. **Given** Tuan bấm vào node Unexplored Scope (ví dụ "Mã hóa mật khẩu Bcrypt"),
   **When** xem chi tiết, **Then** thấy vì sao nó liên quan tới chủ đề vừa học và nó
   thuộc track/module nào sẽ dạy (hoặc ghi rõ "chưa có bài học").

### User Story 3 — Hiểu bài học dùng để làm gì ở công ty thật (Priority: P2)

Mỗi Day có một Thẻ Thông Tin Thực Tế Doanh Nghiệp: mức độ quan trọng (Must-have /
Should-have / Nice-to-have), ứng dụng thực tế bằng ngôn ngữ đời thường (ví dụ
"Validation chặn người dùng nhập chữ vào ô số tiền, tránh làm sập hệ thống thanh
toán"), và lỗi người mới hay gặp (ví dụ copy-paste code mẫu mà không hiểu validation
chạy ở đâu). Tuan đọc thẻ trước khi làm bài để biết vì sao bài này đáng học và nó
đóng vai trò gì trong đồ án Booking API.

**Why this priority**: Đây là phần trả lời câu "hiểu nhuần nhuyễn vai trò của bài
học trong đồ án thực tế" — thiếu nó thì Tuan chỉ biết làm bài tập mà không biết vì
sao công ty cần kỹ năng đó.

**Independent Test**: Mở bất kỳ Day nào, thấy thẻ doanh nghiệp với đủ 3 phần (mức
quan trọng, ứng dụng thực tế, lỗi hay gặp), nội dung đúng với chủ đề của Day đó.

**Acceptance Scenarios**:

1. **Given** mở Day 1 (Pydantic validation), **When** xem thẻ doanh nghiệp, **Then**
   thấy mức quan trọng, một ví dụ ứng dụng thực tế bằng lời đời thường, và ít nhất
   2 lỗi người mới hay gặp liên quan tới validation.
2. **Given** mở Day 3 (trùng id / xung đột 409), **When** xem thẻ, **Then** ví dụ
   thực tế nói rõ hậu quả khi không xử lý trùng (đặt trùng lịch, thu tiền 2 lần).

### User Story 4 — Qua 3 cổng chống phụ thuộc AI dưới 3 phút mỗi cổng (Priority: P2)

Để đánh dấu hiểu một chủ đề, Tuan vượt qua 3 kiểm tra tư duy ngắn thay vì bài kiểm
tra nặng nề: (a) Flow Puzzle — sắp xếp các khối hành động theo đúng thứ tự dữ liệu
đi (ví dụ: bấm nút → kiểm tra dữ liệu → lưu DB → trả thông báo); (b) Spot the Bug —
đoạn code ngắn 5–10 dòng có 1 lỗi logic, bấm chọn dòng sai và chọn lý do; (c)
Self-Note "giải thích cho chính mình" — tự gõ 2–3 câu bằng lời của mình, khung ghi
chú chặn paste (Ctrl+V).

**Why this priority**: Ba cổng này là bằng chứng chống "học vẹt bằng AI": xếp đúng
luồng chứng tỏ hiểu thứ tự, bắt đúng lỗi chứng tỏ đọc được code, tự gõ lại chứng tỏ
tổng hợp được bằng ngôn từ của mình.

**Independent Test**: Trên một Day, làm Flow Puzzle sai thứ tự thì báo sai và cho
làm lại; chọn đúng dòng lỗi nhưng sai lý do thì chưa qua cổng Spot the Bug; Self-Note
dán văn bản vào thì không nhập được (paste bị chặn) và nộp ghi chú quá ngắn thì
server từ chối.

**Acceptance Scenarios**:

1. **Given** Flow Puzzle của Day 2, **When** Tuan xếp sai thứ tự 2 bước, **Then**
   hệ thống báo sai, chỉ rõ cặp bước bị đảo, cho xếp lại mà không mất các cổng khác.
2. **Given** Spot the Bug của một Day, **When** Tuan chọn đúng dòng lỗi nhưng chọn
   sai lý do, **Then** cổng chưa qua, hệ thống gợi ý đọc lại phần lý thuyết liên quan.
3. **Given** khung Self-Note, **When** Tuan bấm Ctrl+V, **Then** không có văn bản
   nào được dán vào; khi nộp ghi chú dưới 2 câu hoặc quá ngắn, server từ chối với
   lý do rõ ràng.
4. **Given** Tuan làm đúng cả 3 cổng, **When** kiểm tra trạng thái Day, **Then** 3
   cổng đều hiện đã qua và được lưu bền (tải lại trang vẫn còn).

### User Story 5 — Admin thêm/sửa bài học, chủ đề, nội dung (Priority: P3)

Muse, với vai trò admin, thêm được chủ đề/kỹ năng mới (Track mới), module, Day mới,
và sửa được nội dung bài học (lý thuyết, quiz, Flow Puzzle, Spot the Bug, thẻ doanh
nghiệp) mà không cần Tuan thao tác kỹ thuật. Ở v2, đường admin mặc định là sửa
content trong repo rồi đẩy lên GitHub + redeploy (đã chạy ở v1); kết nối MCP để
thao tác trực tiếp là phase 2 trong v2, sau khi P1–P4 chạy ổn.

**Why this priority**: Không có đường admin thì mỗi lần thêm kỹ năng mới đều phải
sửa code tay; nhưng MCP là phần phức tạp (xác thực, ghi thẳng vào DB production)
nên không được làm trước lõi học tập.

**Independent Test**: Thêm một Track mới (ví dụ kỹ năng mới) qua đường admin và thấy
nó xuất hiện trên trang tổng quan mà không mất tiến độ track cũ; sửa một câu quiz
và thấy nội dung mới sau khi redeploy.

**Acceptance Scenarios**:

1. **Given** admin thêm 1 Day mới vào Module 1, **When** deploy xong, **Then** Day
   mới xuất hiện trong cây kiến thức ở trạng thái Available/Locked đúng luật mở
   khóa, tiến độ 14 Day cũ không đổi.
2. **Given** admin sửa nội dung một Day đã có người học dở, **When** seed refresh
   chạy, **Then** nội dung mới được cập nhật nhưng DayWork, QuizAttempt, checklist
   và nhật ký giữ nguyên.

### Edge Cases

- Tuan tải lại trang giữa chừng khi đang làm Flow Puzzle: trạng thái các cổng đã qua
  phải còn nguyên (lưu server-side), puzzle đang làm dở có thể làm lại từ đầu.
- Render free ngủ sau ~15 phút không dùng: lần tải đầu sau khi ngủ có thể chậm
  ~50 giây; giao diện phải hiện trạng thái đang tải chứ không báo lỗi kết nối sai.
- Tuan hoàn thành Day 1 rồi mới nâng cấp lên v2 (hoặc ngược lại): luật grandfathered
  ở US-1 scenario 4 phải giữ đúng.
- Self-Note gõ bằng tiếng Việt không dấu: hệ thống vẫn chấp nhận (chỉ kiểm tra độ
  dài/số câu), không ép phải có dấu.
- Nội dung Day chưa có Flow Puzzle / Spot the Bug (Day cũ soạn trước v2): Day đó
  hiện rõ "đang bổ sung", không được tính là qua cổng khi chưa có dữ liệu.
- Tuan mở 2 tab cùng lúc và nộp cổng ở cả hai: server lấy lần nộp sau cùng cho từng
  cổng, không tạo trạng thái mâu thuẫn.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Hệ thống MUST có một bộ cổng hoàn thành Day thống nhất (gộp Feynman +
  Viết - Test - Giải thích), gồm: quiz ≥75%, bài tập + kết quả test đã nộp, Flow
  Puzzle đúng, Spot the Bug đúng (dòng + lý do), Self-Note (≥2 câu, đủ dài) +
  trả lời đúng câu biến thể, bản tóm tắt cuối Day. Server MUST kiểm tra lại toàn bộ
  trước khi đánh dấu hoàn thành; client tick không có giá trị.
- **FR-002**: Mỗi Day MUST có vòng Feynman trong trang: chọn khái niệm chính, ô
  giải thích đơn giản, 1–2 câu hỏi lại (biến thể đổi điều kiện) từ ngân hàng câu
  hỏi theo từng Day, phần học lại trỏ đúng đoạn lý thuyết liên quan, ô giải thích
  lại, và bản tóm tắt cuối Day (giải thích đơn giản, khái niệm đã nắm, lỗi đã sửa,
  5 câu tự kiểm tra sau này, vùng yếu nhất).
- **FR-003**: Hệ thống MUST có trang cây kiến thức cho mỗi Track: node là Module
  (nhánh) và Day, 4 trạng thái Mastered / In Progress / Available / Unexplored
  Scope; luật mở khóa mặc định là tuần tự trong Module (Day N mở khi Day N-1 đã
  Mastered), Module sau mở khi Module trước xong; Day Locked không vào được trang
  chi tiết.
- **FR-004**: Mỗi Day MUST có Thẻ Thông Tin Thực Tế Doanh Nghiệp gồm: mức quan
  trọng (Must-have / Should-have / Nice-to-have), ứng dụng thực tế bằng ngôn ngữ
  đời thường, ít nhất 2 lỗi người mới hay gặp.
- **FR-005**: Mỗi Day MUST có 1 Flow Puzzle (các bước từ flow của Day, xáo trộn
  thứ tự, người học xếp lại đúng) và 1 Spot the Bug (code 5–10 dòng, đúng 1 lỗi
  logic, chọn dòng sai + chọn lý do trong các lựa chọn cho sẵn). Server MUST chấm
  đúng/sai; làm sai được làm lại không giới hạn.
- **FR-006**: Khung Self-Note MUST chặn paste (Ctrl+V / menu chuột phải) ở
  client và server MUST từ chối ghi chú dưới 2 câu hoặc quá ngắn; nội dung ghi chú
  được lưu bền theo Day.
- **FR-007**: Hệ thống MUST giữ nguyên toàn bộ tiến độ v1 sau nâng cấp: 14 Day,
  56 quiz, 50 checklist, DayWork/QuizAttempt/ChecklistItem.done/JournalEntry
  không đổi; `/api/progress` sau nâng cấp vẫn trả đúng số đã có. Day hoàn thành ở
  v1 được grandfathered (FR-001 áp dụng cho Day chưa hoàn thành).
- **FR-008**: Hệ thống MUST hỗ trợ nhiều Track/kỹ năng trên cùng cấu trúc chung
  Track → Module → Day (không tạo bảng riêng theo kỹ năng); thêm Track mới không
  được ảnh hưởng Track cũ.
- **FR-009**: Admin (Muse) MUST thêm/sửa được Track, Module, Day và toàn bộ nội
  dung (lý thuyết, quiz, Flow Puzzle, Spot the Bug, thẻ doanh nghiệp, cây kiến
  thức) qua repo + redeploy; seed refresh chỉ cập nhật trường nội dung, không chạm
  tiến độ. Kết nối MCP để thao tác trực tiếp là phase 2, [NEEDS CLARIFICATION:
  MCP server chạy ở đâu, xác thực với Neon DB production bằng cách nào, và có cho
  phép ghi thẳng DB hay chỉ sửa file content trong repo].
- **FR-010**: Toàn bộ giao diện và nội dung MUST là tiếng Việt có dấu đúng chính
  tả, kiểm tra bằng cách đọc thật; cấm dùng script tự động thêm dấu.
- **FR-011**: Sơ đồ luồng của mỗi Day MUST hiển thị tương tác được (xem từng bước
  dữ liệu đi qua), tái dùng dữ liệu flow đã có của Day, không vẽ ảnh tĩnh.
- **FR-012**: Hệ thống MUST giữ nguyên deploy free-tier hiện tại (Vercel Hobby
  frontend, Render free backend, Neon free Postgres) và URL hiện tại
  https://frontend-ten-smoky-41.vercel.app.

### Key Entities

- **Track**: một kỹ năng/chủ đề lớn (ví dụ Backend Intern); có nhiều Module.
- **Module**: một nhánh trong cây kiến thức (ví dụ FastAPI: viết API từ đầu); có
  nhiều Day theo thứ tự.
- **Day**: một bài học theo ngày; có lý thuyết, sơ đồ luồng, bài tập, quiz,
  Enterprise Context Card, Flow Puzzle, Spot the Bug, ngân hàng câu biến thể, và
  trạng thái cổng hoàn thành.
- **SkillTreeNode**: trạng thái suy ra từ tiến độ (Mastered / In Progress /
  Available / Locked / Unexplored Scope) + liên kết prerequisite (Day trước,
  Module trước) + gợi ý mở rộng (Unexplored Scope).
- **EnterpriseContextCard**: mức quan trọng, ứng dụng thực tế, lỗi hay gặp; gắn
  với một Day.
- **FlowPuzzle**: danh sách bước đã xáo trộn + thứ tự đúng; gắn với một Day.
- **BugSnippet**: code 5–10 dòng, dòng lỗi, các lựa chọn lý do + lý do đúng; gắn
  với một Day.
- **DayWork (mở rộng)**: thêm kết quả Flow Puzzle, Spot the Bug, Self-Note, câu
  biến thể, bản tóm tắt cuối Day; các trường v1 giữ nguyên.
- **FeynmanSummary**: bản tóm tắt cuối Day của người học (giải thích đơn giản,
  khái niệm đã nắm, lỗi đã sửa, 5 câu tự kiểm tra, vùng yếu nhất).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Tuan hoàn thành được Day 1 trên bản v2 live chỉ bằng bộ cổng mới, và
  server từ chối khi thiếu bất kỳ cổng nào (kiểm tra bằng API).
- **SC-002**: Sau nâng cấp, `/api/progress` trả đúng tiến độ v1 (hiện 0/50 checklist,
  0/14 Day) và không Day nào đã hoàn thành bị mất trạng thái.
- **SC-003**: Cây kiến thức hiển thị đủ 14 Day với trạng thái đúng luật mở khóa;
  100% Day có Enterprise Context Card, Flow Puzzle và Spot the Bug (Day nào chưa
  có thì hiện rõ "đang bổ sung" thay vì tính qua cổng).
- **SC-004**: Backend pytest pass, frontend build pass, kiểm tra live trên URL
  production (health, tracks, progress) trước khi báo xong.
- **SC-005**: Admin thêm được 1 Day mới qua repo + redeploy mà không mất tiến độ cũ
  (kiểm tra bằng `/api/progress` trước/sau).

## Assumptions

- Một người dùng duy nhất (Tuan); không có đăng nhập, tài khoản, phân quyền
  người dùng trong v2.
- Nội dung v2 ban đầu chỉ bao phủ 14 Day FastAPI hiện có (Giai đoạn 1–3); Giai
  đoạn 4 (deploy) và Spring Boot vẫn là backlog nội dung riêng, chia Day sau theo
  cùng khuôn, không thuộc spec này.
- Luật mở khóa tuần tự là mặc định; nếu Tuan muốn mở tự do mọi Day thì đổi thành
  một cấu hình, không sửa code sâu.
- MCP admin là phase 2; v2 dùng đường admin qua repo đã chạy ở v1.
- Render không tự deploy khi push qua GitHub API nên backend v2 cần deploy thủ
  công + kiểm tra live sau đó.
- Ngưỡng Self-Note (số câu, độ dài tối thiểu) và số câu hỏi lại Feynman (1–2 câu)
  sẽ chốt số cụ thể ở bước plan; spec này chốt nguyên tắc và cổng.
