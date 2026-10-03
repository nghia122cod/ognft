---
name: video-auto
description: Chạy quy trình làm video 7 bước của người dùng bằng app video_auto - (1) skill tạo kịch bản -> prompt-anh.txt + voice/kich-ban.txt, (2) Gemini + extension Nghé nè tạo ảnh, (3) app giọng đọc trên máy, (4) CapCut phụ đề -> SRT, (5) skill ghép giọng đọc -> timeline.txt, (6) ghép ảnh theo timeline (bản Python của GHEP-ANH-TIMELINE.bat), (7) CapCut thêm giọng + video + sound effect -> xuất. Dùng khi người dùng nói "chạy video auto", "làm video", "chạy quy trình", "làm tiếp video", "ghép ảnh giọng đọc", "tới bước mấy rồi", hoặc bấm skill này.
---

# Video Auto — quy trình 7 bước

## Phạm vi (bắt buộc)
- Chỉ đọc/ghi trong **thư mục video** người dùng chỉ định, và chỉ ĐỌC thư mục Downloads để nhận file họ tải về.
- Chỉ chạy lệnh `python -m video_auto ...`. Không cài phần mềm, không sửa cấu hình hệ thống, không xóa file.
- Chỉ mở Claude AI, Gemini, app giọng đọc, CapCut đúng đường dẫn trong `config.json`.
- Việc gì ngoài yêu cầu: hỏi trước.

## Cách chạy
1. Hỏi tên/thư mục video nếu chưa rõ. Video mới: `python -m video_auto init -p <thư mục>`.
2. Xem đang ở bước nào: `python -m video_auto status -p <thư mục>`.
3. Mở giao diện cho người dùng bấm (cách chính): `python -m video_auto gui -p <thư mục>` (chạy nền).
   Hoặc chạy tự động không giao diện, trong nền (các bước làm tay sẽ chờ file tới 4 giờ):
   `python -m video_auto run -p <thư mục> [--tu N]`. Chạy 1 bước: `kich_ban | anh | giong | srt | timeline | ghep | capcut`.
4. Báo lại từng bước đã xong và mọi cảnh báo trong log.

## Việc Claude tự làm thay (khi được yêu cầu)
- **Bước 5, chế độ bản đồ** (ảnh đã có sẵn, không có `bando.txt`): làm đúng skill `ghep-anh-giong-doc` mục 2B.
  `python -m video_auto liet-ke -p <thư mục>` để có danh sách câu, đọc `prompt-anh.txt`, gán từng ảnh vào đúng
  câu (thứ tự không lùi), ghi `bando.txt` (dòng i = số ảnh của câu i, tổng = số ảnh), rồi đặt
  `"timeline": {"che_do": "tu_dong"}` trong config.json và chạy bước `timeline`.
  Soi 5-8 mốc trong `timeline-bang.md` trước khi báo xong.
- **Bước 7, sound effect**: nếu chưa có bảng sound effect, viết `sound-effects.md` theo dạng
  `| Ảnh # | Thời điểm | Sound Effect (CapCut search) | Mục đích |`, khoảng 35-45% số ảnh, tên hiệu ứng tiếng Anh
  như thư viện CapCut, rồi chạy bước `capcut` để có `sound-effects-capcut.md` theo mốc giọng đọc thật.

## Quy tắc ảnh (giống GHEP-ANH-TIMELINE.bat)
- Một đuôi file duy nhất; tên bắt đầu bằng số thứ tự; số ảnh = số dòng timeline.
- Lỗi đuôi/tên: `python -m video_auto sua-anh -p <thư mục>` (bản gốc lưu ở `anh/_goc/`). Thiếu ảnh thì báo
  số ảnh thiếu, không tự nhân đôi ảnh.
