"""Giao diện bấm nút theo đúng thứ tự quy trình (Tkinter, có sẵn trong Python trên Windows/Mac)."""
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

from .apps import launch, open_folder
from .config import load_project
from .pipeline import STEPS, run_all, step_open_capcut


def main(project_dir="."):
    root = tk.Tk()
    root.title("Video Auto")
    root.geometry("860x640")
    q: queue.Queue = queue.Queue()
    state = {"project": load_project(project_dir), "busy": False}

    def log(msg):
        q.put(str(msg))

    def pump():
        try:
            while True:
                logbox.insert(tk.END, q.get_nowait() + "\n")
                logbox.see(tk.END)
        except queue.Empty:
            pass
        root.after(150, pump)

    def run_bg(fn, label):
        if state["busy"]:
            messagebox.showinfo("Đang chạy", "Chờ bước hiện tại chạy xong.")
            return
        state["busy"] = True
        status.set(f"Đang chạy: {label} ...")

        def work():
            try:
                state["project"] = load_project(state["project"].root)   # đọc lại config mới nhất
                fn(state["project"])
                log(f"✔ Xong: {label}")
            except Exception as e:
                log(f"✖ LỖI ({label}): {e}")
            finally:
                state["busy"] = False
                root.after(0, lambda: status.set("Sẵn sàng"))

        threading.Thread(target=work, daemon=True).start()

    def choose_project():
        d = filedialog.askdirectory(title="Chọn thư mục dự án")
        if d:
            state["project"] = load_project(d)
            proj_var.set(str(state["project"].root))

    top = ttk.Frame(root, padding=8)
    top.pack(fill="x")
    proj_var = tk.StringVar(value=str(state["project"].root))
    ttk.Label(top, text="Dự án:").pack(side="left")
    ttk.Entry(top, textvariable=proj_var, width=70, state="readonly").pack(side="left", padx=6)
    ttk.Button(top, text="Chọn...", command=choose_project).pack(side="left")

    P = lambda: state["project"]
    helpers = {
        "prepare": [("Mở thư mục dự án", lambda: open_folder(P().root, log))],
        "images": [("Mở Gemini", lambda: launch(P().cfg["apps"]["browser_url_images"], log)),
                   ("Mở thư mục ảnh", lambda: open_folder(P().path("images_dir"), log))],
        "voice": [("Mở app giọng đọc", lambda: launch(P().cfg["apps"]["voice_app"], log)),
                  ("Mở thư mục voice", lambda: open_folder(P().path("voice_audio").parent, log))],
        "timeline": [("Mở thư mục output", lambda: open_folder(P().out, log))],
        "render": [("Mở CapCut + output", lambda: step_open_capcut(P(), log))],
    }

    body = ttk.Frame(root, padding=8)
    body.pack(fill="x")
    for key, title, fn in STEPS:
        row = ttk.Frame(body)
        row.pack(fill="x", pady=3)
        ttk.Label(row, text=title, width=38).pack(side="left")
        ttk.Button(row, text="Chạy bước này",
                   command=lambda f=fn, t=title: run_bg(lambda p: f(p, log), t)).pack(side="left", padx=4)
        for text, cmd in helpers.get(key, []):
            def safe(c=cmd):
                try:
                    c()
                except Exception as e:
                    log(f"✖ {e}")
            ttk.Button(row, text=text, command=safe).pack(side="left", padx=4)

    ttk.Button(root, text="▶ CHẠY TỰ ĐỘNG TOÀN BỘ", command=lambda: run_bg(
        lambda p: run_all(p, log), "Chạy tự động toàn bộ")).pack(fill="x", padx=8, pady=8, ipady=8)
    status = tk.StringVar(value="Sẵn sàng")
    ttk.Label(root, textvariable=status).pack(anchor="w", padx=8)
    logbox = scrolledtext.ScrolledText(root, height=18)
    logbox.pack(fill="both", expand=True, padx=8, pady=8)
    pump()
    root.mainloop()
