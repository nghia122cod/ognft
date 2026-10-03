"""Đường dẫn thư mục đặc biệt của Windows (Desktop, Downloads) đọc từ registry.

Cần vì Desktop có thể nằm trong OneDrive với tên tiếng Việt (vd OneDrive\\Máy tính),
không phải ~/Desktop.
"""
import os
from pathlib import Path

_KEYS = {
    "Desktop": ["Desktop"],
    "Downloads": ["{374DE290-123F-4565-9164-39C4925E467B}"],
    "Pictures": ["My Pictures"],
    "Documents": ["Personal"],
}


def known_folder(name: str):
    try:
        import winreg
    except ImportError:          # không phải Windows
        return None
    for sub in (r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders",
                r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"):
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub) as k:
                for v in _KEYS[name]:
                    try:
                        p = Path(os.path.expandvars(winreg.QueryValueEx(k, v)[0]))
                        if p.is_dir():
                            return p
                    except OSError:
                        continue
        except OSError:
            continue
    return None
