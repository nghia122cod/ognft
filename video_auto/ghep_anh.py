"""Bản Python của GHEP-ANH-TIMELINE.bat: cùng quy tắc kiểm tra, cùng lệnh FFmpeg, cùng kết quả video-anh.mp4.

Khác bản .bat ở 2 điểm:
- Đọc số đầu tên file theo hệ 10. Bản .bat dùng `set /a`, nên số có 0 ở đầu bị hiểu
  là hệ 8 (012 -> 10, 08/09 -> lỗi). Bản này đọc đúng 012 = 12.
- Có thêm bước "sửa ảnh" (đổi đuôi, thêm số vào đầu tên). Ảnh gốc được chuyển vào
  thư mục _goc/, không bị xóa.
"""
import re
import shutil
from pathlib import Path

from .media import need, run

EXTS = ["jpg", "jpeg", "jfif", "png", "webp", "bmp"]
VF = ("scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,"
      "fps={fps},format=yuv420p")


class LoiGhep(Exception):
    pass


def doc_timeline(path: Path):
    """Mỗi dòng lấy phần đầu (tách bởi , ; khoảng trắng); chỉ nhận số nguyên dương."""
    frames = []
    for line in Path(path).read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith(";"):
            continue
        tok = re.split(r"[,;\s]+", line)[0]
        if re.fullmatch(r"[0-9]+", tok):
            frames.append(int(tok))
    if not frames:
        raise LoiGhep("Timeline không có dòng số hợp lệ.")
    return frames


def _anh(folder: Path, ext=None):
    return sorted(p for p in folder.iterdir()
                  if p.is_file() and p.suffix[1:].lower() in ([ext] if ext else EXTS))


def _so_dau(name: str):
    tok = re.split(r"[.\-_ ]", name, maxsplit=1)[0]
    return int(tok) if re.fullmatch(r"[0-9]+", tok) else None


def kiem_tra(timeline: Path, folder: Path, fps=30):
    """Trả về dict thông tin; ném LoiGhep với thông báo giống bản .bat khi sai."""
    folder = Path(folder)
    if not folder.is_dir():
        raise LoiGhep("Không thấy thư mục ảnh.")
    if not Path(timeline).exists():
        raise LoiGhep("Không thấy file timeline.")
    ext = next((e for e in EXTS if _anh(folder, e)), None)
    if not ext:
        raise LoiGhep("Thư mục không có ảnh nào.")
    files = _anh(folder, ext)
    lan = [e for e in EXTS if e != ext and _anh(folder, e)]
    if lan:
        raise LoiGhep(f"Thư mục lẫn đuôi file khác: {' '.join('.' + e for e in lan)}. "
                      f"Đổi hết về .{ext} (bấm \"Sửa ảnh\") rồi chạy lại.")
    frames = doc_timeline(timeline)
    n = len(frames)
    info = {"ext": ext, "so_anh": len(files), "frames": frames, "tong_frame": sum(frames),
            "ngan": sum(1 for f in frames if f < 15)}
    if len(files) != n:
        raise LoiGhep(f"Số ảnh ({len(files)}) khác số dòng timeline ({n}).")
    dat = {}
    for f in files:
        k = _so_dau(f.stem)
        if k is None:
            raise LoiGhep(f"File này không bắt đầu bằng số: {f.name}. "
                          "Mỗi tên file phải bắt đầu bằng số thứ tự cảnh.")
        if k < 1:
            raise LoiGhep(f"Số không hợp lệ ở file {f.name}")
        if k > n:
            raise LoiGhep(f"File {f.name} có số {k} vượt quá {n}")
        if k in dat:
            raise LoiGhep(f"Hai ảnh cùng mang số {k}: {dat[k].name} và {f.name}")
        dat[k] = f
    thieu = [i for i in range(1, n + 1) if i not in dat]
    if thieu:
        raise LoiGhep(f"Chỉ đặt được {len(dat)}/{n} ảnh, thiếu số: {', '.join(map(str, thieu[:30]))}")
    info["thu_tu"] = [dat[i] for i in range(1, n + 1)]
    return info


def tom_tat(info, fps=30):
    tf = info["tong_frame"]
    ts = tf // fps
    o = info["thu_tu"]
    fr = info["frames"]
    n = len(o)
    lines = [f"Ảnh      : {info['so_anh']} file đuôi .{info['ext']}",
             f"Timeline : {n} dòng | {tf} frame | {ts // 60} phút {ts % 60} giây"]
    if info["ngan"]:
        lines.append(f"Chú ý    : {info['ngan']} cảnh ngắn dưới 0.5 giây")
    lines.append(f"Đối chiếu: {info['so_anh']} ảnh = {n} dòng (KHỚP)")
    lines.append("-" * 50)
    for i in range(min(3, n)):
        lines.append(f"  Ảnh {i + 1} ({fr[i]} frame) = {o[i].name}")
    lines.append("  ...")
    for i in range(max(3, n - 3), n):
        lines.append(f"  Ảnh {i + 1} = {o[i].name}")
    lines.append("-" * 50)
    lines.append(f"Ảnh 1 phải là cảnh mở đầu, ảnh {n} phải là cảnh kết.")
    return "\n".join(lines)


def _dem_frame(video: Path):
    out = run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=nb_frames",
               "-of", "csv=p=0", video], log=lambda *_: None).strip()
    if not out or out == "N/A":
        out = run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries",
                   "stream=nb_read_frames", "-of", "csv=p=0", video], log=lambda *_: None).strip()
    try:
        return int(out)
    except ValueError:
        return None


def ghep(info, folder: Path, fps=30, width=1920, height=1080, log=print):
    """Ghép thành <thư mục ảnh>/video-anh.mp4; tự chuyển sang chế độ khớp tuyệt đối nếu lệch > 1 frame."""
    need("ffmpeg")
    folder = Path(folder)
    work = folder / "_ghep"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir()
    ext = info["ext"]
    for i, src in enumerate(info["thu_tu"], 1):
        shutil.copy2(src, work / f"{i:05d}.{ext}")
    vf = VF.format(w=width, h=height, fps=fps)
    lines = []
    for i, f in enumerate(info["frames"], 1):
        lines += [f"file '{i:05d}.{ext}'", f"duration {f // fps}.{(f % fps) * 1000000 // fps:06d}"]
    lines.append(f"file '{len(info['frames']):05d}.{ext}'")
    (work / "danhsach.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    out = folder / "video-anh.mp4"
    log("Đang ghép video...")
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0",
         "-i", work / "danhsach.txt", "-r", fps, "-vf", vf, "-c:v", "libx264", "-crf", "18",
         "-preset", "veryfast", out], log=lambda *_: None)
    if not out.exists():
        raise LoiGhep("Không tạo được video.")
    tf = info["tong_frame"]
    nf = _dem_frame(out)
    if nf is None:
        log("[!] Không đọc được số frame.")
        return out
    log(f"Cần có: {tf} frame | Thực tế: {nf} frame")
    if abs(nf - tf) <= 1:
        log(f"Lệch: {abs(nf - tf)} frame (ĐẠT)")
        return out
    log(f"Lệch: {abs(nf - tf)} frame (KHÔNG ĐẠT) → chuyển sang chế độ khớp tuyệt đối, render từng ảnh.")
    clip = work / "clip"
    clip.mkdir()
    noi = []
    for i, f in enumerate(info["frames"], 1):
        if i % 20 == 1:
            log(f"  [{i}/{len(info['frames'])}]")
        run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-loop", "1", "-i", work / f"{i:05d}.{ext}",
             "-frames:v", f, "-vf", vf, "-r", fps, "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
             clip / f"{i:05d}.mp4"], log=lambda *_: None)
        noi.append(f"file 'clip/{i:05d}.mp4'")
    (work / "noiclip.txt").write_text("\n".join(noi) + "\n", encoding="utf-8")
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0",
         "-i", work / "noiclip.txt", "-c", "copy", out], log=lambda *_: None)
    log(f"Cần có: {tf} frame | Thực tế: {_dem_frame(out)} frame")
    return out


def sua_anh(folder: Path, log=print):
    """Sửa lỗi hay gặp, KHÔNG xóa ảnh: bản gốc chuyển vào _goc/.

    - Lẫn đuôi: đổi hết về đuôi chiếm đa số (jpeg/jfif chỉ đổi tên, png/webp/bmp chuyển bằng ffmpeg).
    - Tên không bắt đầu bằng số nhưng có số ở giữa/cuối (vd 'Gemini_Image (12).png') → '12-...'.
    """
    folder = Path(folder)
    files = _anh(folder)
    if not files:
        raise LoiGhep("Thư mục không có ảnh nào.")
    dem = {}
    for f in files:
        e = f.suffix[1:].lower()
        e = "jpg" if e in ("jpeg", "jfif") else e
        dem[e] = dem.get(e, 0) + 1
    dich = max(dem, key=dem.get)
    goc = folder / "_goc"
    sua = 0
    for f in files:
        e = f.suffix[1:].lower()
        stem = f.stem
        if _so_dau(stem) is None:
            nums = re.findall(r"\d+", stem)
            if nums:
                stem = f"{int(nums[-1])}-{stem}"
        same_type = (e == dich) or (dich == "jpg" and e in ("jpeg", "jfif"))
        new = folder / f"{stem}.{dich}"
        if new == f:
            continue
        if new.exists():
            raise LoiGhep(f"Không sửa được {f.name}: đã có file {new.name}")
        goc.mkdir(exist_ok=True)
        backup = goc / f.name
        shutil.copy2(f, backup)
        if same_type:
            f.rename(new)
        else:
            need("ffmpeg")
            run(["ffmpeg", "-y", "-loglevel", "error", "-i", f, "-q:v", "2", new], log=lambda *_: None)
            f.unlink()
        log(f"  {f.name} → {new.name}")
        sua += 1
    log(f"Đã sửa {sua} ảnh (bản gốc lưu ở _goc/)." if sua else "Không có gì cần sửa.")
    return sua
