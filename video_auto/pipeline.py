"""Chuỗi bước theo đúng quy trình của người dùng. Mỗi bước chạy riêng được."""
import json

from . import images as imgmod
from .align import Word, align_segments
from .apps import launch, open_folder
from .media import duration
from .outputs import read_timeline, write_srt, write_timeline
from .render import render_video
from .stt import transcribe
from .textutil import read_text, split_segments
from .tts import make_voice


def _segments(project):
    p = project.path("segments")
    if not p.exists():
        raise RuntimeError(f"Thiếu {p}. Đây là kịch bản tách theo ý (mỗi ý cách nhau 1 dòng trống).")
    segs = split_segments(read_text(p))
    if not segs:
        raise RuntimeError(f"{p} trống.")
    return segs


def step_prepare(project, log=print):
    """Bước 1: kiểm tra thư mục/dữ liệu đầu vào, tạo thư mục còn thiếu."""
    for key in ("images_dir", "output_dir"):
        project.path(key).mkdir(parents=True, exist_ok=True)
    project.path("voice_audio").parent.mkdir(parents=True, exist_ok=True)
    segs = _segments(project)
    log(f"Kịch bản: {len(segs)} ý → cần {len(segs)} ảnh (001..{len(segs):03d}).")
    vt = project.path("voice_text")
    if not vt.exists():
        vt.write_text("\n".join(segs), encoding="utf-8")
        log(f"Tạo {vt.name} từ segments.txt (có thể chỉnh lại nếu cần).")
    return segs


def step_images(project, log=print):
    """Bước 2: mở Gemini để tạo ảnh (thủ công), rồi kiểm tra ảnh."""
    segs = _segments(project)
    _, _, _, problems = imgmod.scan(project.path("images_dir"), len(segs))
    if problems:
        log("Ảnh chưa đủ/chưa khớp: " + "; ".join(problems))
    else:
        log(f"Ảnh đủ {len(segs)}/{len(segs)}.")
    return problems


def step_voice(project, log=print):
    return make_voice(project, log)


def step_subtitles_timeline(project, log=print):
    """Bước 3: Whisper -> căn ý theo giọng -> timeline.txt + phụ đề SRT."""
    segs = _segments(project)
    audio = project.path("voice_audio")
    if not audio.exists():
        raise RuntimeError(f"Chưa có {audio}. Chạy bước giọng đọc trước.")
    total = duration(audio)
    words = transcribe(project, audio, log)
    spans = align_segments(segs, words, total)
    imgs = imgmod.resolve(project.path("images_dir"), len(segs),
                          project.out / "images_fixed", autofix=True, log=log)
    write_timeline(project.out / "timeline.txt", spans, imgs)
    n = write_srt(project.out / "voice.srt", spans, project.cfg["video"]["subtitle_max_chars"])
    short = [s for s in spans if s.end - s.start < 1.0]
    if short:
        log("⚠ Ý có thời lượng < 1s (kiểm tra căn): " + ", ".join(str(s.index) for s in short[:15]))
    log(f"Đã ghi timeline.txt ({len(spans)} ý) và voice.srt ({n} dòng phụ đề).")
    (project.out / "images_map.json").write_text(
        json.dumps([str(p) for p in imgs], ensure_ascii=False), encoding="utf-8")


def step_render(project, log=print):
    """Bước 4: ghép ảnh + giọng + nhạc + sfx -> final.mp4."""
    tl = project.out / "timeline.txt"
    mp = project.out / "images_map.json"
    if not tl.exists() or not mp.exists():
        raise RuntimeError("Chưa có timeline. Chạy bước phụ đề/timeline trước.")
    from pathlib import Path
    rows = read_timeline(tl)
    imgs = [Path(p) for p in json.loads(mp.read_text(encoding="utf-8"))]
    return render_video(project, rows, imgs, project.path("voice_audio"),
                        project.out / "voice.srt", log)


def step_open_capcut(project, log=print):
    launch(project.cfg["apps"]["capcut"], log)
    open_folder(project.out, log)


STEPS = [
    ("prepare", "1. Kiểm tra dữ liệu & thư mục", step_prepare),
    ("images", "2. Ảnh (mở Gemini, kiểm tra ảnh)", step_images),
    ("voice", "3. Giọng đọc", step_voice),
    ("timeline", "4. Phụ đề + timeline", step_subtitles_timeline),
    ("render", "5. Dựng video + âm thanh", step_render),
]


def run_all(project, log=print, stop_on_missing_images=True):
    """Chạy tự động toàn bộ. Dừng và báo rõ nếu ảnh chưa đủ (bước duy nhất làm tay)."""
    segs = step_prepare(project, log)
    problems = step_images(project, log)
    if problems and stop_on_missing_images:
        imgs_n = len([p for p in project.path("images_dir").glob("*") if p.is_file()]) \
            if project.path("images_dir").exists() else 0
        if imgs_n < len(segs):
            raise RuntimeError(f"Dừng: mới có {imgs_n}/{len(segs)} ảnh. Tạo đủ ảnh rồi chạy lại.")
    step_voice(project, log)
    step_subtitles_timeline(project, log)
    return step_render(project, log)
