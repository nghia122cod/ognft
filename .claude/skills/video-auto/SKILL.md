---
name: video-auto
description: Chạy tự động quy trình làm video (kịch bản tách ý + ảnh -> giọng đọc -> Whisper -> phụ đề SRT + timeline -> dựng video + nhạc + sound effect) bằng app video_auto. Dùng khi người dùng nói "chạy video auto", "làm video tự động", "tạo giọng đọc và ghép ảnh", "chạy quy trình", "ghép ảnh giọng đọc", hoặc bấm skill này.
---

# Video Auto

## Phạm vi (bắt buộc tuân thủ)
- Chỉ đọc/ghi trong **thư mục dự án** người dùng chỉ định (mặc định thư mục hiện tại). Không đụng file nào ngoài đó.
- Chỉ chạy các lệnh `python -m video_auto ...` dưới đây. Không cài thêm phần mềm, không sửa cấu hình hệ thống, không xóa file.
- Chỉ mở ứng dụng (CapCut, app giọng đọc, Gemini) khi người dùng yêu cầu và đúng đường dẫn khai báo trong `config.json`.
- Việc gì ngoài yêu cầu: hỏi trước.

## Dữ liệu đầu vào trong thư mục dự án
- `segments.txt`: kịch bản tách theo ý, mỗi ý cách nhau 1 dòng trống (1 ý = 1 ảnh).
- `voice/voice_text.txt`: văn bản đọc (nếu thiếu, app tự tạo từ segments.txt).
- `images/`: ảnh đã tạo bằng Gemini, tên có số thứ tự ý (001.png, 002.png...).
- `sfx_cues.txt` (tùy chọn): mỗi dòng `số_ý file_sfx [âm_lượng]`.
- `config.json`: giọng đọc, đường dẫn app, kích thước video (tạo bằng `python -m video_auto init -p <dự án>`).

## Cách chạy
1. Kiểm tra `segments.txt` và `images/` có đủ. Nếu chưa có `config.json`: `python -m video_auto init -p <dự án>`.
2. Chạy toàn bộ: `python -m video_auto run -p <dự án>`.
   Từng bước riêng: `prepare`, `images`, `voice`, `timeline`, `render`.
3. Nếu dừng vì thiếu ảnh: báo rõ thiếu ảnh số nào, bảo người dùng tạo thêm ảnh rồi chạy lại. Không tự bịa/nhân đôi ảnh.
4. Xong, báo đường dẫn `output/final.mp4`, `output/timeline.txt`, `output/voice.srt` và mọi cảnh báo trong log (ý < 1 giây, ảnh bị đánh số lại...).

## Lưu ý
- Ảnh gốc không bao giờ bị đổi tên/xóa; bản đã chuẩn hóa được chép sang `output/images_fixed/`.
- Giọng đọc `voice.mode = "external"`: app mở app giọng đọc ngoài, chờ file `voice/voice.mp3` xuất hiện.
- Cần FFmpeg trong PATH và `pip install -r requirements.txt`.
