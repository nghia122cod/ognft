"""Tự bấm nút trong cửa sổ app khác trên Windows (chỉ dùng ctypes, không cần cài thêm).

Dùng cho màn hình "Đăng Nhập DGT ElevenLabs": app giọng đọc đã nhớ tài khoản, chỉ cần
bấm ĐĂNG NHẬP. Không đọc, không gõ, không lưu tài khoản/mật khẩu.
"""
import sys
import time
import unicodedata


def _norm(s):
    return unicodedata.normalize("NFC", s).casefold()


def _api():
    import ctypes
    from ctypes import wintypes
    return ctypes, wintypes, ctypes.windll.user32


def tim_cua_so(tieu_de: str):
    ctypes, wintypes, user32 = _api()
    want = _norm(tieu_de)
    found = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def cb(hwnd, _):
        if user32.IsWindowVisible(hwnd):
            n = user32.GetWindowTextLengthW(hwnd)
            if n:
                buf = ctypes.create_unicode_buffer(n + 1)
                user32.GetWindowTextW(hwnd, buf, n + 1)
                if want in _norm(buf.value):
                    found.append(hwnd)
                    return False
        return True

    user32.EnumWindows(cb, 0)
    return found[0] if found else None


def _dpi_aware(user32):
    """Tọa độ thật của màn hình khi Windows phóng to 125%/150% (PER_MONITOR_AWARE_V2 = -4)."""
    import ctypes
    try:
        f = user32.SetThreadDpiAwarenessContext
        f.argtypes, f.restype = [ctypes.c_ssize_t], ctypes.c_ssize_t
        return f(-4)
    except (AttributeError, OSError):
        return None


def _bam(hwnd, rel_x, rel_y):
    ctypes, wintypes, user32 = _api()
    old = _dpi_aware(user32)
    try:
        user32.ShowWindow(hwnd, 9)              # SW_RESTORE
        user32.SetForegroundWindow(hwnd)
        time.sleep(0.4)
        r = wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(r))
        x = int(r.left + (r.right - r.left) * rel_x)
        y = int(r.top + (r.bottom - r.top) * rel_y)
        pt = wintypes.POINT()
        user32.GetCursorPos(ctypes.byref(pt))
        user32.SetCursorPos(x, y)
        user32.mouse_event(0x0002, 0, 0, 0, 0)  # chuột trái xuống
        user32.mouse_event(0x0004, 0, 0, 0, 0)  # chuột trái lên
        time.sleep(0.1)
        user32.SetCursorPos(pt.x, pt.y)          # trả chuột về chỗ cũ
    finally:
        if old:
            user32.SetThreadDpiAwarenessContext(old)


def _enter(hwnd):
    _, _, user32 = _api()
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.3)
    user32.keybd_event(0x0D, 0, 0, 0)
    user32.keybd_event(0x0D, 0, 2, 0)


def _cho_dong(tieu_de, giay):
    end = time.time() + giay
    while time.time() < end:
        if not tim_cua_so(tieu_de):
            return True
        time.sleep(0.5)
    return False


def tu_dang_nhap(cfg: dict, log=print, cho_mo=30):
    """Chờ cửa sổ đăng nhập hiện ra rồi bấm ĐĂNG NHẬP. Trả True nếu cửa sổ đã đóng (đăng nhập xong)."""
    if not sys.platform.startswith("win") or not cfg.get("tu_dang_nhap", True):
        return False
    tieu_de = cfg.get("tieu_de_dang_nhap", "Đăng Nhập DGT ElevenLabs")
    rel_x, rel_y = cfg.get("nut_dang_nhap", [0.276, 0.835])
    end = time.time() + cho_mo
    hwnd = None
    while time.time() < end and not hwnd:
        hwnd = tim_cua_so(tieu_de)
        if not hwnd:
            time.sleep(0.5)
    if not hwnd:
        log("Không thấy màn hình đăng nhập (có thể app đã đăng nhập sẵn).")
        return False
    time.sleep(1.0)                              # đợi app điền sẵn tài khoản đã nhớ
    _bam(hwnd, rel_x, rel_y)
    if _cho_dong(tieu_de, 6):
        log("✔ Đã tự bấm Đăng nhập app giọng đọc.")
        return True
    _enter(hwnd)
    if _cho_dong(tieu_de, 6):
        log("✔ Đã tự bấm Đăng nhập app giọng đọc (phím Enter).")
        return True
    log("⚠ Chưa tự đăng nhập được — bạn bấm nút ĐĂNG NHẬP giúp. "
        "(Nếu ô mật khẩu trống, hãy tick 'Nhớ tài khoản' rồi đăng nhập 1 lần.)")
    return False
