"""Chờ file xuất hiện (bước làm tay) — chỉ đọc, không đụng file khác."""
import fnmatch
import time
from pathlib import Path


def match(name: str, patterns, ignore=()):
    n = name.lower()
    return any(fnmatch.fnmatch(n, p.lower()) for p in patterns) and \
        not any(fnmatch.fnmatch(n, p.lower()) for p in ignore)


def newest(folder: Path, patterns, since=0.0, ignore=()):
    if not folder.exists():
        return None
    c = [f for f in folder.iterdir() if f.is_file() and f.stat().st_mtime >= since
         and match(f.name, patterns, ignore) and not f.name.endswith((".crdownload", ".part", ".tmp"))]
    return max(c, key=lambda f: f.stat().st_mtime) if c else None


def wait_for(check, timeout_s, log=print, msg="Đang chờ...", stop=None, every=3):
    """check() trả về giá trị khác None khi xong. File phải đứng yên 2 lần kiểm tra (đã ghi xong)."""
    end = time.time() + timeout_s
    last, last_size, t_log = None, -1, 0
    while time.time() < end:
        if stop is not None and stop.is_set():
            raise InterruptedError("Đã dừng.")
        r = check()
        if r is not None:
            size = r.stat().st_size if isinstance(r, Path) else 0
            if r == last and size == last_size and size >= 0:
                return r
            last, last_size = r, size
        if time.time() - t_log > 60:
            log(msg)
            t_log = time.time()
        time.sleep(every)
    raise TimeoutError("Hết thời gian chờ. " + msg)
