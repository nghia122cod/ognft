"""7 bước đúng theo quy trình của người dùng.

Bước làm trên app khác (Claude AI, Gemini + Nghé nè, app giọng đọc, CapCut): app mở đúng
app/thư mục/file cần dùng, hiện hướng dẫn, rồi tự chờ file kết quả xuất hiện để đi tiếp.
Bước máy làm được (nhận file, timeline offline, ghép ảnh, danh sách sound effect): tự chạy.
"""
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from . import ghep_anh, sfx, timeline_vi
from .apps import launch, open_folder
from .config import AUDIO_EXT, D_ANH, F_PROMPT, F_TIMELINE, F_VIDEO_ANH, Project
from .watch import match, newest, wait_for

IMG_EXT = {"." + e for e in ghep_anh.EXTS}


class UI:
    """Giao diện tối thiểu cho các bước. GUI và CLI đều cài lớp này."""
    stop = None

    def log(self, msg):
        print(msg)

    def confirm(self, msg) -> bool:
        return input(msg + " [c/k]: ").strip().lower() in ("c", "co", "có", "y", "yes", "")


@dataclass
class Step:
    key: str
    title: str
    huong_dan: Callable[[Project], str]
    done: Callable[[Project], bool]
    auto: Callable[[Project, UI], object]
    buttons: list = field(default_factory=list)


def _wait_s(p):
    return p.cfg["cho_toi_da_phut"] * 60


def _copy(src: Path, dst: Path, ui):
    """Chép (không di chuyển) file người dùng tải về; bỏ qua nếu bản ở dự án đã mới nhất."""
    if dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime and dst.stat().st_size == src.stat().st_size:
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    ui.log(f"  Chép {src.name} → {dst}")


def _mtime(f):
    return f.stat().st_mtime - 1 if f and f.exists() else time.time()


def _try_launch(target, ui, ten):
    if target:
        launch(target, ui.log)
    else:
        ui.log(f"(Chưa khai báo đường dẫn {ten} trong config.json → mục apps. Hãy tự mở {ten}.)")


# ---------- Bước 1: kịch bản ----------
def so_prompt(p: Project):
    f = p.p(F_PROMPT)
    if not f.exists():
        return 0
    return sum(1 for l in f.read_text(encoding="utf-8-sig").splitlines() if re.match(r"\s*\d+", l))


def nhan_file_kich_ban(p: Project, ui: UI, since=0.0):
    m = p.cfg["mau_file"]
    dl = p.downloads
    got = {}
    pr = newest(dl, m["prompt_anh"], since)
    kb = newest(dl, m["kich_ban"], since, ignore=m["kich_ban_bo_qua"] + m["prompt_anh"])
    if pr:
        _copy(pr, p.p(F_PROMPT), ui)
        got["prompt"] = pr
    if kb:
        _copy(kb, p.kich_ban, ui)
        got["kich_ban"] = kb
    for pat in m["phu"]:
        f = newest(dl, [pat], since)
        if f:
            _copy(f, p.root / f.name, ui)
    return got


def b1_done(p):
    return p.p(F_PROMPT).exists() and p.kich_ban.exists()


def b1_auto(p, ui):
    start = time.time() - 1800      # nhận cả file vừa tải trong 30 phút trước
    if not b1_done(p):
        launch(p.cfg["apps"]["claude"], ui.log)
        ui.log("Chạy skill tạo kịch bản trên Claude AI, tải file prompt ảnh + kịch bản giọng đọc về máy.")

        def check():
            nhan_file_kich_ban(p, ui, start)
            return p.kich_ban if b1_done(p) else None
        wait_for(check, _wait_s(p), ui.log, f"Đang chờ file prompt ảnh + kịch bản trong {p.downloads} ...", ui.stop)
    ui.log(f"✔ Kịch bản: {p.kich_ban.name} | Prompt ảnh: {so_prompt(p)} ảnh")


# ---------- Bước 2: ảnh ----------
def anh_list(p):
    d = p.p(D_ANH)
    return [f for f in d.iterdir() if f.is_file() and f.suffix.lower() in IMG_EXT] if d.exists() else []


def b2_done(p):
    n = so_prompt(p)
    return n > 0 and len(anh_list(p)) >= n


def chep_anh_downloads(p, ui, since):
    dst = p.p(D_ANH)
    dst.mkdir(exist_ok=True)
    have = {f.name for f in anh_list(p)}
    n = 0
    for f in p.downloads.iterdir() if p.downloads.exists() else []:
        if f.is_file() and f.suffix.lower() in IMG_EXT and f.stat().st_mtime >= since and f.name not in have:
            shutil.copy2(f, dst / f.name)
            n += 1
    if n:
        ui.log(f"  Chép {n} ảnh mới từ Downloads vào anh/")


def b2_auto(p, ui):
    n = so_prompt(p)
    if n == 0:
        raise RuntimeError("Chưa có prompt-anh.txt (bước 1).")
    p.p(D_ANH).mkdir(exist_ok=True)
    if not b2_done(p):
        start = _mtime(p.p(F_PROMPT))       # chỉ nhận ảnh tải về sau file prompt
        launch(p.cfg["apps"]["gemini"], ui.log)
        open_folder(p.root, ui.log)
        ui.log(f"Mở extension Nghé nè → nạp {F_PROMPT} → tạo {n} ảnh. Ảnh lưu vào anh/ "
               "(hoặc để tải về Downloads, app tự chép sang).")

        def check():
            chep_anh_downloads(p, ui, start)
            return p.p(D_ANH) if b2_done(p) else None
        wait_for(check, _wait_s(p), ui.log, f"Đang chờ ảnh: {len(anh_list(p))}/{n}", ui.stop, every=5)
    ui.log(f"✔ Ảnh: {len(anh_list(p))}/{n}")


# ---------- Bước 3: giọng đọc ----------
def b3_done(p):
    return p.voice_audio() is not None


def b3_auto(p, ui):
    if not p.kich_ban.exists():
        raise RuntimeError("Chưa có kich-ban.txt trong thư mục Voice (bước 1).")
    if not b3_done(p):
        start = _mtime(p.kich_ban)
        _try_launch(p.cfg["apps"]["voice_app"], ui, "app giọng đọc")
        open_folder(p.voice_dir, ui.log)
        g = p.cfg["giong_doc"]
        ui.log(f"Trong app giọng đọc: giọng {g['giong']}, speed {g['speed']}, stability {g['stability']}, "
               f"similarity {g['similarity']} → nạp kich-ban.txt trong thư mục Voice → tạo → lưu vào thư mục Voice.")

        def check():
            f = newest(p.downloads, ["*" + e for e in AUDIO_EXT], start)
            if f and not b3_done(p):
                _copy(f, p.voice_dir / f.name, ui)
            return p.voice_audio()
        wait_for(check, _wait_s(p), ui.log, "Đang chờ file giọng đọc trong thư mục Voice ...", ui.stop)
    ui.log(f"✔ Giọng đọc: {p.voice_audio().name}")


# ---------- Bước 4: phụ đề CapCut → SRT ----------
def b4_done(p):
    return p.srt() is not None


def b4_auto(p, ui):
    if not b3_done(p):
        raise RuntimeError("Chưa có giọng đọc (bước 3).")
    if not b4_done(p):
        start = _mtime(p.voice_audio())     # SRT phải mới hơn file giọng đọc
        _try_launch(p.cfg["apps"]["capcut"], ui, "CapCut")
        open_folder(p.voice_dir, ui.log)
        ui.log(HD_CAPCUT_SRT)

        def check():
            f = newest(p.downloads, ["*.srt"], start)
            if f and not b4_done(p):
                _copy(f, p.voice_dir / f.name, ui)
            return p.srt()
        wait_for(check, _wait_s(p), ui.log, "Đang chờ file .srt trong thư mục Voice ...", ui.stop)
    ui.log(f"✔ Phụ đề: {p.srt().name}")


HD_CAPCUT_SRT = ("CapCut máy tính: Dự án mới → thêm file giọng đọc trong thư mục Voice → Văn bản → Phụ đề tự động → "
                 "chọn ngôn ngữ → Tạo → Xuất → bỏ tích Video → tích Phụ đề → định dạng SRT → lưu vào thư mục Voice.")


# ---------- Bước 5: timeline ----------
def so_dong_timeline(p):
    f = p.p(F_TIMELINE)
    try:
        return len(ghep_anh.doc_timeline(f)) if f.exists() else 0
    except ghep_anh.LoiGhep:
        return 0


def b5_done(p):
    return p.p(F_TIMELINE).exists() and so_dong_timeline(p) > 0


def timeline_tu_dong(p, ui):
    fps = p.cfg["fps"]
    mn = p.cfg["timeline"]["toi_thieu_giay"]
    srt = p.srt()
    if p.cfg["kenh"] == "ja":
        units = p.root / "units.json"
        if not units.exists():
            raise RuntimeError("Kênh Nhật cần units.json (skill kịch bản xuất ra) trong thư mục dự án.")
        tool = Path(__file__).parent / "tools" / "can_timeline.py"
        r = subprocess.run([sys.executable, str(tool), str(units), str(srt), "--out", str(p.root),
                            "--fps", str(fps)], capture_output=True, text=True, encoding="utf-8")
        ui.log((r.stdout + r.stderr).strip())
        if r.returncode:
            raise RuntimeError("can_timeline.py lỗi.")
        return
    bando = p.root / "bando.txt"
    if bando.exists():
        n, tong, _ = timeline_vi.build(p.kich_ban, srt, p.root, ban_do_path=bando, fps=fps, min_giay=mn)
        ui.log(f"Chế độ bản đồ (bando.txt): {n} ảnh.")
    else:
        n_anh = len(anh_list(p)) or so_prompt(p)
        ui.log("⚠ Không có bando.txt. Theo skill ghép giọng đọc: ảnh đã có sẵn thì nên dùng chế độ bản đồ "
               "(đối chiếu từng ảnh với câu) — việc đó cần Claude AI. Đang dùng chế độ ép đúng số ảnh, "
               "hãy soi lại timeline-bang.md.")
        n, tong, thieu = timeline_vi.build(p.kich_ban, srt, p.root, so_anh=n_anh, fps=fps, min_giay=mn)
        if thieu:
            ui.log(f"Cảnh báo: {thieu} cảnh không neo được trực tiếp vào SRT, đã nội suy.")
    ui.log(f"Ghi timeline.txt + timeline-bang.md: {n} ảnh, {tong // fps // 60} phút {tong // fps % 60} giây.")


def b5_auto(p, ui):
    if not (b4_done(p) and b1_done(p)):
        raise RuntimeError("Cần có SRT (bước 4) và kịch bản (bước 1).")
    if not b5_done(p):
        if p.cfg["timeline"]["che_do"] == "tu_dong":
            timeline_tu_dong(p, ui)
        else:
            start = _mtime(p.srt())         # timeline phải mới hơn file SRT
            launch(p.cfg["apps"]["claude"], ui.log)
            open_folder(p.root, ui.log)
            ui.log(f"Trên Claude AI: tải lên {p.srt().name} + {p.kich_ban.name} (trong {p.voice_dir}) + {F_PROMPT} → chạy skill "
                   "ghép giọng đọc → tải timeline.txt về.")

            def check():
                f = newest(p.downloads, ["timeline*.txt"], start)
                if f:
                    _copy(f, p.p(F_TIMELINE), ui)
                    bang = newest(p.downloads, ["timeline-bang*.md"], start)
                    if bang:
                        _copy(bang, p.root / "timeline-bang.md", ui)
                return p.p(F_TIMELINE) if b5_done(p) else None
            wait_for(check, _wait_s(p), ui.log, f"Đang chờ timeline.txt trong {p.downloads} ...", ui.stop)
    n, a = so_dong_timeline(p), len(anh_list(p))
    ui.log(f"✔ Timeline: {n} dòng" + ("" if n == a else f"  ⚠ nhưng có {a} ảnh — bước 6 sẽ báo lỗi"))


# ---------- Bước 6: ghép ảnh ----------
def b6_done(p):
    v, t = p.p(F_VIDEO_ANH), p.p(F_TIMELINE)
    return v.exists() and t.exists() and v.stat().st_mtime >= t.stat().st_mtime


def b6_kiem_tra(p, ui):
    info = ghep_anh.kiem_tra(p.p(F_TIMELINE), p.p(D_ANH), p.cfg["fps"])
    ui.log(ghep_anh.tom_tat(info, p.cfg["fps"]))
    return info


def b6_sua(p, ui):
    ghep_anh.sua_anh(p.p(D_ANH), ui.log)


def b6_auto(p, ui):
    try:
        info = b6_kiem_tra(p, ui)
    except ghep_anh.LoiGhep as e:
        ui.log(f"[LỖI] {e}")
        fixable = any(s in str(e) for s in ("lẫn đuôi", "không bắt đầu bằng số"))
        if not fixable or not ui.confirm(f"{e}\n\nTự sửa tên/đuôi ảnh? (bản gốc lưu ở anh/_goc/)"):
            raise
        b6_sua(p, ui)
        info = b6_kiem_tra(p, ui)
    if not ui.confirm(ghep_anh.tom_tat(info, p.cfg["fps"]) + "\n\nĐúng thì bấm Có để ghép."):
        raise InterruptedError("Bạn đã dừng ở bước kiểm tra ảnh.")
    out = ghep_anh.ghep(info, p.p(D_ANH), p.cfg["fps"], p.cfg["width"], p.cfg["height"], ui.log)
    ui.log(f"✔ XONG: {out}")


# ---------- Bước 7: CapCut hoàn thiện ----------
def _bang_sfx(p):
    for pat in ("*sound*effect*.md", "goi-san-xuat.md", "*storyboard*.md", "*.md"):
        for f in sorted(p.root.glob(pat)):
            if f.name in ("timeline-bang.md", "sound-effects-capcut.md"):
                continue
            if sfx.doc_bang(f.read_text(encoding="utf-8-sig")):
                return f
    return None


def b7_sfx(p, ui):
    bang = _bang_sfx(p)
    if not bang:
        ui.log("Không thấy bảng sound effect (.md) trong thư mục dự án — bỏ qua danh sách SFX.")
        return
    frames = ghep_anh.doc_timeline(p.p(F_TIMELINE))
    rows = sfx.lam_danh_sach(bang, frames, p.root / "sound-effects-capcut.md", p.cfg["fps"])
    ui.log(f"Ghi sound-effects-capcut.md: {len(rows)} sound effect với mốc thời gian thật (từ {bang.name}).")
    sfx.lam_track(rows, p.root / "sfx", sum(frames), p.root / "sfx-track.wav", p.cfg["fps"], ui.log)


def b7_done(p):
    return (p.root / ".da-xuat").exists()


def b7_auto(p, ui):
    if not b6_done(p):
        raise RuntimeError("Chưa có anh/video-anh.mp4 (bước 6).")
    b7_sfx(p, ui)
    _try_launch(p.cfg["apps"]["capcut"], ui, "CapCut")
    open_folder(p.root, ui.log)
    extra = " + sfx-track.wav" if (p.root / "sfx-track.wav").exists() else ""
    ui.log(f"CapCut: thêm {p.voice_audio().name} + anh/video-anh.mp4{extra} → đặt sound effect theo "
           "sound-effects-capcut.md → xuất video.")
    if ui.confirm("Đã xuất video trong CapCut xong chưa?"):
        (p.root / ".da-xuat").write_text(time.strftime("%Y-%m-%d %H:%M"), encoding="utf-8")
        ui.log("✔ Hoàn tất video.")


def _hd(text):
    return lambda p: text


STEPS = [
    Step("kich_ban", "1. Tạo kịch bản (skill Claude AI)",
         _hd("Bấm skill tạo kịch bản → tải file prompt ảnh + kịch bản giọng đọc. App tự lấy từ Downloads: "
             "prompt → prompt-anh.txt, kịch bản → kich-ban.txt trong thư mục Voice."),
         b1_done, b1_auto,
         [("Mở Claude AI", lambda p, ui: launch(p.cfg["apps"]["claude"], ui.log)),
          ("Lấy file từ Downloads", lambda p, ui: nhan_file_kich_ban(p, ui))]),
    Step("anh", "2. Tạo ảnh (Gemini + Nghé nè)",
         lambda p: f"Mở Gemini → extension Nghé nè → nạp {F_PROMPT} ({so_prompt(p)} prompt) → tạo ảnh → lưu vào anh/.",
         b2_done, b2_auto,
         [("Mở Gemini", lambda p, ui: launch(p.cfg["apps"]["gemini"], ui.log)),
          ("Mở thư mục dự án", lambda p, ui: open_folder(p.root, ui.log)),
          ("Mở thư mục ảnh", lambda p, ui: open_folder(p.p(D_ANH), ui.log))]),
    Step("giong", "3. Tạo giọng đọc (app trên máy)",
         lambda p: (f"Mở app giọng đọc → giọng {p.cfg['giong_doc']['giong']}, speed {p.cfg['giong_doc']['speed']}, "
                    f"stability {p.cfg['giong_doc']['stability']}, similarity {p.cfg['giong_doc']['similarity']} → "
                    "nạp kich-ban.txt trong thư mục Voice → tạo → lưu vào thư mục Voice."),
         b3_done, b3_auto,
         [("Mở app giọng đọc", lambda p, ui: _try_launch(p.cfg["apps"]["voice_app"], ui, "app giọng đọc")),
          ("Mở thư mục Voice", lambda p, ui: open_folder(p.voice_dir, ui.log))]),
    Step("srt", "4. Phụ đề CapCut → SRT", _hd(HD_CAPCUT_SRT), b4_done, b4_auto,
         [("Mở CapCut", lambda p, ui: _try_launch(p.cfg["apps"]["capcut"], ui, "CapCut")),
          ("Mở thư mục Voice", lambda p, ui: open_folder(p.voice_dir, ui.log))]),
    Step("timeline", "5. Timeline (skill ghép giọng đọc)",
         lambda p: ("Claude AI: tải lên SRT + kịch bản + prompt ảnh → chạy skill ghép giọng đọc → tải timeline.txt."
                    if p.cfg["timeline"]["che_do"] == "claude_ai" else
                    "Tự động: chạy cùng thuật toán của skill ghép giọng đọc ngay trên máy."),
         b5_done, b5_auto,
         [("Mở Claude AI", lambda p, ui: launch(p.cfg["apps"]["claude"], ui.log)),
          ("Tính ngay trên máy", lambda p, ui: timeline_tu_dong(p, ui))]),
    Step("ghep", "6. Ghép ảnh theo timeline",
         _hd("Kiểm tra ảnh (đuôi, số đầu tên, số lượng) → xem ảnh đầu/cuối → ghép thành anh/video-anh.mp4."),
         b6_done, b6_auto,
         [("Kiểm tra ảnh", b6_kiem_tra), ("Sửa ảnh", b6_sua),
          ("Mở GHEP-ANH (.bat gốc)", lambda p, ui: _try_launch(p.cfg["apps"]["ghep_anh_bat"], ui, "GHEP-ANH-TIMELINE.bat"))]),
    Step("capcut", "7. CapCut: giọng + video + sound effect → xuất",
         _hd("Thêm giọng đọc + video-anh.mp4 vào CapCut, đặt sound effect theo sound-effects-capcut.md, xuất video."),
         b7_done, b7_auto,
         [("Làm danh sách SFX", b7_sfx),
          ("Mở CapCut", lambda p, ui: _try_launch(p.cfg["apps"]["capcut"], ui, "CapCut"))]),
]


def run_all(p: Project, ui: UI, tu=0):
    for st in STEPS[tu:]:
        if ui.stop is not None and ui.stop.is_set():
            raise InterruptedError("Đã dừng.")
        if st.done(p):
            ui.log(f"✔ {st.title} — đã xong, bỏ qua.")
            continue
        ui.log(f"\n=== {st.title} ===")
        st.auto(p, ui)
