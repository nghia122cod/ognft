"""Sound effect cho bước CapCut cuối.

Đọc bảng sound effect skill kịch bản xuất ra (`Ảnh # | Thời điểm | Sound Effect (CapCut search) | Mục đích`),
tính lại thời điểm THẬT của từng ảnh theo timeline.txt (giọng đọc thật), rồi:
- ghi `sound-effects-capcut.md`: danh sách mốc HH:MM:SS:FF để đặt trong CapCut;
- nếu thư mục `sfx/` có file âm thanh trùng tên hiệu ứng (vd `Whoosh Transition.mp3`),
  ghép sẵn 1 track `sfx-track.wav` dài bằng video, chỉ cần kéo 1 lần vào CapCut.
"""
import re
from pathlib import Path

from .config import AUDIO_EXT
from .media import need, run


def doc_bang(md_text: str):
    rows, cols = [], None
    for line in md_text.splitlines():
        if not line.strip().startswith("|"):
            cols = None if not line.strip() else cols
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if all(re.fullmatch(r":?-+:?", c) for c in cells if c):
            continue
        low = [c.lower() for c in cells]
        if any("sound" in c or "hiệu ứng" in c for c in low):
            cols = {"anh": next((i for i, c in enumerate(low) if c.startswith("ảnh") or c.startswith("anh")), 0),
                    "sfx": next(i for i, c in enumerate(low) if "sound" in c or "hiệu ứng" in c),
                    "md": next((i for i, c in enumerate(low) if "mục đích" in c), None)}
            continue
        if cols is None:
            continue
        m = re.search(r"\d+", cells[cols["anh"]]) if cols["anh"] < len(cells) else None
        if not m or cols["sfx"] >= len(cells) or not cells[cols["sfx"]]:
            continue
        rows.append({"anh": int(m.group()), "sfx": cells[cols["sfx"]].strip("*\"' "),
                     "muc_dich": cells[cols["md"]] if cols["md"] is not None and cols["md"] < len(cells) else ""})
    return rows


def _tc(fr, fps):
    s = fr // fps
    return f"{s // 3600:02d}:{s // 60 % 60:02d}:{s % 60:02d}:{fr % fps:02d}"


def lam_danh_sach(bang_md: Path, frames, out_md: Path, fps=30):
    rows = doc_bang(bang_md.read_text(encoding="utf-8-sig"))
    starts = [0]
    for f in frames:
        starts.append(starts[-1] + f)
    lines = ["# Sound effect theo giọng đọc thật", "",
             "| Ảnh | Mốc CapCut | Sound Effect (tìm trong CapCut) | Mục đích |", "|---|---|---|---|"]
    ok = []
    for r in sorted(rows, key=lambda r: r["anh"]):
        if not 1 <= r["anh"] <= len(frames):
            continue
        r["frame"] = starts[r["anh"] - 1]
        ok.append(r)
        lines.append(f"| {r['anh']} | {_tc(r['frame'], fps)} | {r['sfx']} | {r['muc_dich']} |")
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return ok


def _key(s):
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def lam_track(rows, sfx_dir: Path, total_frames, out_wav: Path, fps=30, log=print):
    if not sfx_dir.exists():
        return None
    lib = {_key(f.stem): f for f in sfx_dir.iterdir() if f.suffix.lower() in AUDIO_EXT}
    used, missing = [], set()
    for r in rows:
        f = lib.get(_key(r["sfx"]))
        if f:
            used.append((r["frame"] / fps, f))
        else:
            missing.add(r["sfx"])
    if missing:
        log("Chưa có file trong sfx/ cho: " + ", ".join(sorted(missing)))
    if not used:
        return None
    need("ffmpeg")
    dur = total_frames / fps
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-t", f"{dur:.3f}", "-i",
           "anullsrc=r=48000:cl=stereo"]
    filt, mix = [], ["[0:a]"]
    for j, (t, f) in enumerate(used, 1):
        cmd += ["-i", f]
        ms = int(t * 1000)
        filt.append(f"[{j}:a]aresample=48000,adelay={ms}|{ms}[s{j}]")
        mix.append(f"[s{j}]")
    filt.append("".join(mix) + f"amix=inputs={len(mix)}:duration=first:normalize=0[out]")
    cmd += ["-filter_complex", ";".join(filt), "-map", "[out]", "-t", f"{dur:.3f}", out_wav]
    run(cmd, log=lambda *_: None)
    log(f"Đã ghép {len(used)} sound effect vào {out_wav.name}")
    return out_wav
