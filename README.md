# Video Auto — quy trình 7 bước

App tự động theo **đúng** quy trình làm video hiện tại. Bước nào làm trên app khác thì app mở đúng app,
thư mục, file cần dùng, hiện hướng dẫn, rồi **tự chờ file kết quả** để đi tiếp. Bước máy làm được thì tự chạy.

| # | Bước | App làm gì |
|---|---|---|
| 1 | Skill tạo kịch bản (Claude AI) | Mở Claude AI, chờ bạn tải file về Downloads, tự chép: prompt → `prompt-anh.txt`, kịch bản → `voice/kich-ban.txt` (bỏ qua `kich-ban-theo-y`), kèm `units.json`, `bando.txt`, `goi-san-xuat.md` nếu có |
| 2 | Gemini + extension Nghé nè | Mở Gemini + thư mục dự án, đếm ảnh tới khi đủ số prompt; ảnh tải về Downloads được tự chép vào `anh/` |
| 3 | App giọng đọc trên máy | Mở app, nhắc thông số giọng (giọng, speed, stability, similarity), chờ file âm thanh trong `voice/` |
| 4 | CapCut phụ đề → SRT | Mở CapCut, hiện các bước xuất SRT, chờ file `.srt` trong `voice/` (hoặc Downloads) |
| 5 | Skill ghép giọng đọc → timeline.txt | `claude_ai`: mở Claude AI, chờ `timeline.txt` tải về. `tu_dong`: chạy **cùng thuật toán** của skill ngay trên máy (kết quả giống hệt, đã kiểm thử so với `build-timeline.js`) |
| 6 | Ghép ảnh theo timeline | Bản Python của `GHEP-ANH-TIMELINE.bat`: cùng bước kiểm tra, cùng màn hình ảnh đầu/cuối, hỏi xác nhận, cùng lệnh FFmpeg, tự chuyển chế độ khớp tuyệt đối. Nút **Sửa ảnh** để sửa đuôi/tên |
| 7 | CapCut: giọng + video + sound effect | Tính mốc sound effect theo giọng đọc thật → `sound-effects-capcut.md`; nếu `sfx/` có file trùng tên hiệu ứng thì ghép sẵn `sfx-track.wav`; mở CapCut |

## Cài đặt (Windows)
1. Python 3.10+ (tích "Add to PATH") và FFmpeg: `winget install Gyan.FFmpeg`.
2. Không cần cài thêm thư viện.
3. Bấm đúp `MO-VIDEO-AUTO.bat` (tự cập nhật bản mới rồi mở app), bấm **Video mới**. Lần đầu app tự dò trên Desktop: lối tắt ElevenLabs, CapCut,
   `GHEP-ANH-TIMELINE.bat` và thư mục `Voice` (bấm **Tìm app trên máy** để dò lại). Thiếu gì thì **Sửa config**.

## Lệnh
```
python -m video_auto gui    -p videos\ten-video
python -m video_auto status -p videos\ten-video
python -m video_auto run    -p videos\ten-video [--tu 3]
python -m video_auto kich_ban|anh|giong|srt|timeline|ghep|capcut -p ...
python -m video_auto kiem-tra-anh | sua-anh | liet-ke | tim-app -p ...
```

## Khác bản .bat cũ
- Số đầu tên ảnh đọc đúng hệ 10. Bản `.bat` dùng `set /a` nên `012` bị hiểu là 10 và `08`, `09` báo lỗi.
- Sửa ảnh không xóa gì: bản gốc lưu ở `anh/_goc/`.

Kiểm thử: `python -m unittest discover -s . -p "test_*.py" -t .`
