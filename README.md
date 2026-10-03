# Video Auto

App miễn phí tự động hóa quy trình: **kịch bản tách ý + ảnh → giọng đọc → Whisper → phụ đề SRT + timeline → video + nhạc + sound effect**.

## Cài đặt (Windows)
1. Cài Python 3.10+ và FFmpeg (thêm vào PATH).
2. `pip install -r requirements.txt`

## Dùng
```
python -m video_auto init -p projects\demo     # tạo config.json
python -m video_auto gui  -p projects\demo     # giao diện bấm nút (hoặc RUN.bat)
python -m video_auto run  -p projects\demo     # chạy tự động toàn bộ
```
Từng bước: `prepare`, `images`, `voice`, `timeline`, `render`, `capcut`.

## Thư mục dự án
```
segments.txt        kịch bản tách ý (mỗi ý cách nhau 1 dòng trống)
voice/voice_text.txt  văn bản đọc (tự tạo nếu thiếu)
voice/voice.mp3     giọng đọc (tự tạo, hoặc lưu từ app giọng đọc ngoài)
images/001.png ...  ảnh từ Gemini, đúng số ý
sfx_cues.txt        (tùy chọn) "số_ý file_sfx [âm_lượng]"
config.json         giọng, app, kích thước video, đường dẫn CapCut/app giọng đọc
output/             timeline.txt, voice.srt, video_silent.mp4, final.mp4
```

## Điểm chính
- Căn ảnh vào giọng đọc bằng so khớp văn bản (không cần LLM, không tốn tiền); Whisper sai vài chữ vẫn không lệch.
- Phụ đề lấy nguyên văn kịch bản.
- Ảnh sai số/đuôi: báo rõ, tự chuẩn hóa sang `output/images_fixed/` (ảnh gốc giữ nguyên).
- `config.json` → `voice.mode: "external"` để dùng app giọng đọc có sẵn trên máy; `apps.capcut` để mở CapCut.

Test: `python -m unittest discover -s tests`
