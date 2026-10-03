"""Giao diện 7 bước đúng thứ tự quy trình. Mỗi bước: hướng dẫn, nút mở app/thư mục, trạng thái."""
import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, simpledialog, ttk

from .apps import launch
from .config import load_project
from .steps import STEPS, UI, run_all


class TkUI(UI):
    def __init__(self, root, q):
        self.root, self.q = root, q
        self.stop = threading.Event()

    def log(self, msg):
        self.q.put(("log", str(msg)))

    def confirm(self, msg):
        ev, ans = threading.Event(), {}
        self.q.put(("ask", (msg, ev, ans)))
        ev.wait()
        return ans.get("ok", False)


def main(project_dir="."):
    root = tk.Tk()
    root.title("Video Auto — quy trình 7 bước")
    root.geometry("1000x760")
    q = queue.Queue()
    ui = TkUI(root, q)
    st = {"p": load_project(project_dir), "busy": False}
    rows = {}

    def pump():
        try:
            while True:
                kind, val = q.get_nowait()
                if kind == "log":
                    logbox.insert(tk.END, val + "\n")
                    logbox.see(tk.END)
                elif kind == "ask":
                    msg, ev, ans = val
                    ans["ok"] = messagebox.askyesno("Xác nhận", msg)
                    ev.set()
                elif kind == "refresh":
                    refresh()
        except queue.Empty:
            pass
        root.after(150, pump)

    def refresh():
        p = st["p"]
        proj.set(str(p.root))
        for s in STEPS:
            mark, hd = rows[s.key]
            try:
                ok = s.done(p)
                mark.config(text="✔" if ok else "○", foreground="green" if ok else "gray")
                hd.config(text=s.huong_dan(p))
            except Exception as e:
                hd.config(text=f"(lỗi đọc trạng thái: {e})")

    def run_bg(fn, label):
        if st["busy"]:
            messagebox.showinfo("Đang chạy", "Đợi việc hiện tại xong hoặc bấm Dừng.")
            return
        st["busy"] = True
        ui.stop.clear()
        status.set(f"Đang chạy: {label}")

        def work():
            try:
                st["p"] = load_project(st["p"].root)
                fn(st["p"])
                ui.log(f"✔ Xong: {label}")
            except InterruptedError as e:
                ui.log(f"■ {e}")
            except Exception as e:
                ui.log(f"✖ LỖI ({label}): {e}")
            finally:
                st["busy"] = False
                q.put(("refresh", None))
                root.after(0, lambda: status.set("Sẵn sàng"))

        threading.Thread(target=work, daemon=True).start()

    def chon():
        d = filedialog.askdirectory(title="Chọn thư mục dự án (1 video)")
        if d:
            st["p"] = load_project(d)
            refresh()

    def moi():
        name = simpledialog.askstring("Video mới", "Tên video (tên thư mục):")
        if not name:
            return
        base = filedialog.askdirectory(title="Đặt thư mục video ở đâu?") or str(Path.cwd())
        p = load_project(Path(base) / name)
        p.root.mkdir(parents=True, exist_ok=True)
        if not (p.root / "config.json").exists():
            # mang cấu hình (đường dẫn app, giọng...) của dự án đang mở sang dự án mới
            p.cfg = st["p"].cfg
            p.save()
        for d in ("voice", "anh"):
            (p.root / d).mkdir(exist_ok=True)
        st["p"] = load_project(p.root)
        refresh()

    top = ttk.Frame(root, padding=8)
    top.pack(fill="x")
    proj = tk.StringVar()
    ttk.Label(top, text="Video:").pack(side="left")
    ttk.Entry(top, textvariable=proj, width=70, state="readonly").pack(side="left", padx=6)
    ttk.Button(top, text="Mở...", command=chon).pack(side="left")
    ttk.Button(top, text="Video mới", command=moi).pack(side="left", padx=4)
    ttk.Button(top, text="Sửa config", command=lambda: (st["p"].save() if not (st["p"].root / "config.json").exists() else None,
                                                     launch(str(st["p"].root / "config.json"), ui.log))
               ).pack(side="left")

    body = ttk.Frame(root, padding=(8, 0))
    body.pack(fill="x")
    for i, s in enumerate(STEPS):
        fr = ttk.LabelFrame(body, padding=4)
        fr.pack(fill="x", pady=2)
        head = ttk.Frame(fr)
        head.pack(fill="x")
        mark = ttk.Label(head, text="○", width=2, font=("", 12, "bold"))
        mark.pack(side="left")
        ttk.Label(head, text=s.title, width=40, font=("", 10, "bold")).pack(side="left")
        ttk.Button(head, text="▶ Chạy bước này",
                   command=lambda s=s: run_bg(lambda p: s.auto(p, ui), s.title)).pack(side="left", padx=2)
        for text, fn in s.buttons:
            ttk.Button(head, text=text, command=lambda f=fn, t=text: run_bg(lambda p: f(p, ui), t)).pack(side="left", padx=2)
        ttk.Button(head, text="Chạy từ đây", command=lambda i=i: run_bg(
            lambda p: run_all(p, ui, i), f"Tự động từ bước {i + 1}")).pack(side="right")
        hd = ttk.Label(fr, text="", wraplength=940, foreground="#444")
        hd.pack(fill="x", padx=24)
        rows[s.key] = (mark, hd)

    bar = ttk.Frame(root, padding=8)
    bar.pack(fill="x")
    ttk.Button(bar, text="▶ CHẠY TỰ ĐỘNG TOÀN BỘ", command=lambda: run_bg(
        lambda p: run_all(p, ui), "Chạy tự động toàn bộ")).pack(side="left", fill="x", expand=True, ipady=6)
    ttk.Button(bar, text="■ Dừng", command=ui.stop.set).pack(side="left", padx=6, ipady=6)
    status = tk.StringVar(value="Sẵn sàng")
    ttk.Label(root, textvariable=status).pack(anchor="w", padx=8)
    logbox = scrolledtext.ScrolledText(root, height=12)
    logbox.pack(fill="both", expand=True, padx=8, pady=(0, 8))
    refresh()
    pump()
    root.mainloop()
