import argparse
import sys

from .config import load_project
from .pipeline import STEPS, run_all, step_open_capcut

NAMES = {k: fn for k, _, fn in STEPS}


def main(argv=None):
    ap = argparse.ArgumentParser(prog="video_auto")
    ap.add_argument("command", choices=["run", "gui", "init", "capcut", *NAMES])
    ap.add_argument("--project", "-p", default=".", help="Thư mục dự án")
    a = ap.parse_args(argv)
    if a.command == "gui":
        from .gui import main as gui_main
        return gui_main(a.project)
    project = load_project(a.project)
    try:
        if a.command == "init":
            project.root.mkdir(parents=True, exist_ok=True)
            project.save()
            (project.root / "images").mkdir(exist_ok=True)
            (project.root / "voice").mkdir(exist_ok=True)
            print(f"Đã tạo config.json trong {project.root}")
        elif a.command == "run":
            run_all(project)
        elif a.command == "capcut":
            step_open_capcut(project)
        else:
            NAMES[a.command](project)
    except Exception as e:  # báo lỗi rõ cho người dùng, không in traceback dài
        print(f"LỖI: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
