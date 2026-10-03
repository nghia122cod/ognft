"""Tiện ích ffmpeg/ffprobe."""
import shutil
import subprocess


def need(tool: str):
    if not shutil.which(tool):
        raise RuntimeError(f"Không tìm thấy '{tool}'. Cài FFmpeg và thêm vào PATH (https://ffmpeg.org).")


def run(cmd: list[str], log=print):
    log("$ " + " ".join(str(c) for c in cmd[:6]) + (" ..." if len(cmd) > 6 else ""))
    p = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if p.returncode != 0:
        raise RuntimeError(f"Lệnh {cmd[0]} lỗi:\n{p.stderr[-1500:]}")
    return p.stdout


def duration(path) -> float:
    need("ffprobe")
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
               "-of", "default=nw=1:nk=1", path], log=lambda *_: None)
    return float(out.strip())
