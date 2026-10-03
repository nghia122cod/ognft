import argparse
import sys

from .config import load_project
from .detect import ap_dung
from .steps import STEPS, UI, run_all

KEYS = [s.key for s in STEPS]


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):      # PowerShell/cmd: in tiếng Việt không bị lỗi mã hoá
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(prog="video_auto", description="Quy trình làm video 7 bước")
    ap.add_argument("command", choices=["gui", "init", "status", "run", *KEYS, "kiem-tra-anh", "sua-anh", "liet-ke", "tim-app"])
    ap.add_argument("--project", "-p", default=".", help="Thư mục dự án (1 video = 1 thư mục)")
    ap.add_argument("--tu", type=int, default=1, help="run: bắt đầu từ bước số mấy")
    a = ap.parse_args(argv)
    if a.command == "gui":
        from .gui import main as gui_main
        return gui_main(a.project)
    p = load_project(a.project)
    ui = UI()
    try:
        if a.command == "init":
            p.root.mkdir(parents=True, exist_ok=True)
            if not (p.root / "config.json").exists():
                p.save()
            for d in ("voice", "anh"):
                (p.root / d).mkdir(exist_ok=True)
            print(f"Đã tạo dự án {p.root}")
            print("Tìm app trên máy:")
            ap_dung(p)
        elif a.command == "tim-app":
            ap_dung(p)
        elif a.command == "status":
            for s in STEPS:
                print(("✔ " if s.done(p) else "○ ") + s.title)
        elif a.command == "run":
            run_all(p, ui, a.tu - 1)
        elif a.command == "liet-ke":
            from .timeline_vi import liet_ke
            for i, c in enumerate(liet_ke(p.kich_ban), 1):
                print(f"{i}\t{c}")
        elif a.command == "kiem-tra-anh":
            next(s for s in STEPS if s.key == "ghep").buttons[0][1](p, ui)
        elif a.command == "sua-anh":
            next(s for s in STEPS if s.key == "ghep").buttons[1][1](p, ui)
        else:
            next(s for s in STEPS if s.key == a.command).auto(p, ui)
    except (Exception, KeyboardInterrupt) as e:
        print(f"LỖI: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
