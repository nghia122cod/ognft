"""Tự bấm nút trong cửa sổ app khác trên Windows (chỉ dùng ctypes, không cần cài thêm).

Dùng cho màn hình "Đăng Nhập DGT ElevenLabs": app giọng đọc đã nhớ tài khoản, chỉ cần
bấm ĐĂNG NHẬP. Không đọc, không gõ, không lưu tài khoản/mật khẩu.
"""
import subprocess
import sys
import time
import unicodedata
from pathlib import Path


def _norm(s):
    return unicodedata.normalize("NFC", s).casefold()


def _api():
    import ctypes
    from ctypes import wintypes
    return ctypes, wintypes, ctypes.windll.user32


def _title(hwnd):
    ctypes, _, user32 = _api()
    n = user32.GetWindowTextLengthW(hwnd)
    buf = ctypes.create_unicode_buffer(n + 1)
    user32.GetWindowTextW(hwnd, buf, n + 1)
    return buf.value


def tim_cua_so(tieu_de: str):
    """Cửa sổ đang hiện có tiêu đề chứa `tieu_de` (không phân biệt hoa thường/dấu dựng sẵn)."""
    ctypes, wintypes, user32 = _api()
    want = _norm(tieu_de)
    found = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def cb(hwnd, _):
        if user32.IsWindowVisible(hwnd) and want in _norm(_title(hwnd)):
            found.append(hwnd)
            return False
        return True

    user32.EnumWindows(cb, 0)
    return found[0] if found else None


def ds_cua_so():
    """Tiêu đề mọi cửa sổ đang hiện (để chẩn đoán khi không tìm thấy)."""
    ctypes, wintypes, user32 = _api()
    out = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def cb(hwnd, _):
        if user32.IsWindowVisible(hwnd):
            t = _title(hwnd)
            if t.strip():
                out.append(t)
        return True

    user32.EnumWindows(cb, 0)
    return out


def _dpi_aware(user32):
    """Tọa độ thật của màn hình khi Windows phóng to 125%/150% (PER_MONITOR_AWARE_V2 = -4)."""
    import ctypes
    try:
        f = user32.SetThreadDpiAwarenessContext
        f.argtypes, f.restype = [ctypes.c_ssize_t], ctypes.c_ssize_t
        return f(-4)
    except (AttributeError, OSError):
        return None


def _elevated(pid=None):
    """Tiến trình có chạy quyền Admin không (None = không đọc được)."""
    ctypes, wintypes, _ = _api()
    k32, adv = ctypes.windll.kernel32, ctypes.windll.advapi32
    h = k32.GetCurrentProcess() if pid is None else k32.OpenProcess(0x1000, False, pid)
    if not h:
        return None
    tok = wintypes.HANDLE()
    try:
        if not adv.OpenProcessToken(h, 0x0008, ctypes.byref(tok)):
            return None
        val, ret = wintypes.DWORD(), wintypes.DWORD()
        if not adv.GetTokenInformation(tok, 20, ctypes.byref(val), 4, ctypes.byref(ret)):
            return None
        return bool(val.value)
    finally:
        if tok:
            k32.CloseHandle(tok)
        if pid is not None:
            k32.CloseHandle(h)


def _pid(hwnd):
    ctypes, wintypes, user32 = _api()
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return pid.value


def _len_truoc(hwnd):
    """Đưa cửa sổ lên trên cùng. Windows chặn SetForegroundWindow nếu không bấm phím Alt trước."""
    _, _, user32 = _api()
    user32.ShowWindow(hwnd, 9)                   # SW_RESTORE
    user32.keybd_event(0x12, 0, 0, 0)            # Alt xuống
    user32.keybd_event(0x12, 0, 2, 0)            # Alt lên
    user32.SetForegroundWindow(hwnd)
    user32.BringWindowToTop(hwnd)
    time.sleep(0.4)


def diem_bam(hwnd, rel_x, rel_y):
    ctypes, wintypes, user32 = _api()
    r = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(r))
    return (int(r.left + (r.right - r.left) * rel_x), int(r.top + (r.bottom - r.top) * rel_y),
            (r.left, r.top, r.right, r.bottom))


def _trung_cua_so(hwnd, x, y):
    """Điểm (x, y) có đúng nằm trên cửa sổ đăng nhập không (không bị cửa sổ khác che)."""
    ctypes, wintypes, user32 = _api()
    user32.WindowFromPoint.argtypes = [wintypes.POINT]
    user32.WindowFromPoint.restype = wintypes.HWND
    w = user32.WindowFromPoint(wintypes.POINT(x, y))
    return bool(w) and user32.GetAncestor(w, 2) == hwnd    # GA_ROOT


def _click(x, y):
    ctypes, wintypes, user32 = _api()
    pt = wintypes.POINT()
    user32.GetCursorPos(ctypes.byref(pt))
    user32.SetCursorPos(x, y)
    time.sleep(0.05)
    user32.mouse_event(0x0002, 0, 0, 0, 0)       # chuột trái xuống
    time.sleep(0.05)
    user32.mouse_event(0x0004, 0, 0, 0, 0)       # chuột trái lên
    time.sleep(0.1)
    user32.SetCursorPos(pt.x, pt.y)              # trả chuột về chỗ cũ


def _enter():
    _, _, user32 = _api()
    user32.keybd_event(0x0D, 0, 0, 0)
    user32.keybd_event(0x0D, 0, 2, 0)


def _cho_dong(tieu_de, giay):
    end = time.time() + giay
    while time.time() < end:
        if not tim_cua_so(tieu_de):
            return True
        time.sleep(0.5)
    return False


def _cho_mo(tieu_de, giay):
    end = time.time() + giay
    while time.time() < end:
        h = tim_cua_so(tieu_de)
        if h:
            return h
        time.sleep(0.5)
    return None


def _chup(x, y, out: Path, log):
    """Chụp màn hình, đánh dấu ô đỏ tại điểm sẽ bấm (dùng FFmpeg gdigrab)."""
    try:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "gdigrab", "-i", "desktop",
                        "-frames:v", "1", "-vf",
                        f"drawbox=x={x - 12}:y={y - 12}:w=24:h=24:color=red:t=4", str(out)],
                       check=True, timeout=20)
        log(f"Ảnh chụp có ô đỏ = chỗ app định bấm: {out}")
        return out
    except Exception as e:  # chỉ để chẩn đoán, lỗi chụp không làm hỏng việc bấm
        log(f"(Không chụp được màn hình: {e})")
        return None


def tu_dang_nhap(cfg: dict, log=print, cho_mo=45, chan_doan=None):
    """Chờ cửa sổ đăng nhập rồi bấm ĐĂNG NHẬP. Trả True nếu cửa sổ đã đóng (đăng nhập xong).

    chan_doan: thư mục để lưu ảnh chụp + in chi tiết (lệnh `thu-dang-nhap`).
    """
    if not sys.platform.startswith("win") or not cfg.get("tu_dang_nhap", True):
        return False
    tieu_de = cfg.get("tieu_de_dang_nhap", "Đăng Nhập DGT ElevenLabs")
    rel_x, rel_y = cfg.get("nut_dang_nhap", [0.276, 0.835])
    ct = log if chan_doan else (lambda *_: None)

    hwnd = _cho_mo(tieu_de, cho_mo)
    if not hwnd:
        log(f"Không thấy cửa sổ '{tieu_de}' sau {cho_mo} giây (có thể app đã đăng nhập sẵn).")
        ct("Các cửa sổ đang mở: " + " | ".join(ds_cua_so()[:25]))
        return False
    ct(f"Thấy cửa sổ: '{_title(hwnd)}'")
    _, _, user32 = _api()
    old = _dpi_aware(user32)
    try:
        time.sleep(1.5)                          # đợi app tự điền tài khoản đã nhớ
        me, other = _elevated(), _elevated(_pid(hwnd))
        ct(f"Quyền Admin: Video Auto={me}, app giọng đọc={other}")
        if other and not me:
            log("⚠ App giọng đọc đang chạy quyền Admin nên Windows chặn Video Auto bấm hộ. "
                "Cách sửa: chuột phải MO-VIDEO-AUTO.bat → Run as administrator.")
        _len_truoc(hwnd)
        x, y, rect = diem_bam(hwnd, rel_x, rel_y)
        trung = _trung_cua_so(hwnd, x, y)
        ct(f"Khung cửa sổ {rect}, điểm bấm ({x}, {y}), nằm trên cửa sổ đăng nhập: {trung}")
        if chan_doan:
            _chup(x, y, Path(chan_doan) / "chan-doan-dang-nhap.png", log)
        _click(x, y)
        if _cho_dong(tieu_de, 6):
            log("✔ Đã tự bấm Đăng nhập app giọng đọc.")
            return True
        ct("Bấm chuột chưa được → thử phím Enter.")
        _len_truoc(hwnd)
        _enter()
        if _cho_dong(tieu_de, 6):
            log("✔ Đã tự bấm Đăng nhập app giọng đọc (phím Enter).")
            return True
    finally:
        if old:
            user32.SetThreadDpiAwarenessContext(old)
    log("⚠ Chưa tự đăng nhập được — bạn bấm nút ĐĂNG NHẬP giúp. "
        "Chạy CHAN-DOAN-DANG-NHAP.bat rồi gửi ảnh để sửa.")
    return False
