"""Mở ứng dụng/thư mục/trình duyệt do người dùng khai báo trong config.json."""
import os
import subprocess
import sys
import webbrowser
from pathlib import Path


def launch(target: str, log=print):
    """Chỉ mở đúng mục tiêu được khai báo; không chạy gì khác."""
    if not target:
        raise RuntimeError("Chưa cấu hình đường dẫn ứng dụng này trong config.json (mục apps).")
    if target.startswith(("http://", "https://")):
        webbrowser.open(target)
    elif sys.platform.startswith("win"):
        os.startfile(target)          # noqa: S606 - đường dẫn do người dùng cấu hình
    elif sys.platform == "darwin":
        subprocess.Popen(["open", target])
    else:
        subprocess.Popen(["xdg-open", target])
    log(f"Đã mở: {target}")


def open_folder(path: Path, log=print):
    path.mkdir(parents=True, exist_ok=True)
    launch(str(path), log)
