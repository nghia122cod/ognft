"""Dựng video bằng FFmpeg: ảnh (Ken Burns) -> concat -> trộn giọng/nhạc/sfx -> (đốt phụ đề)."""
import shlex
from pathlib import Path

from .media import need, run
from .textutil import read_text


def parse_sfx(path: Path, n_images: int, starts: dict, base: Path, log=print):
    """sfx_cues.txt: mỗi dòng `số_ý  file_âm_thanh  [âm_lượng]`. Phát tại lúc ảnh đó bắt đầu."""
    cues = []
    if not path or not path.exists():
        return cues
    for ln, line in enumerate(read_text(path).splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = shlex.split(line)
        try:
            idx = int(parts[0])
            f = (base / parts[1]) if not Path(parts[1]).is_absolute() else Path(parts[1])
            vol = float(parts[2]) if len(parts) > 2 else None
        except (ValueError, IndexError):
            log(f"⚠ sfx_cues.txt dòng {ln} sai định dạng, bỏ qua: {line}")
            continue
        if idx not in starts or not f.exists():
            log(f"⚠ sfx_cues.txt dòng {ln}: không có ý {idx} hoặc thiếu file {f}, bỏ qua")
            continue
        cues.append((starts[idx], f, vol))
    return cues


def _clip(img, dur, i, v, out, log):
    w, h, fps = v["width"], v["height"], v["fps"]
    frames = max(2, round(dur * fps))
    if v["ken_burns"]:
        zoom = "min(zoom+0.0006,1.12)" if i % 2 else "if(eq(on,1),1.12,max(zoom-0.0006,1.0))"
        vf = (f"scale={w*2}:{h*2}:force_original_aspect_ratio=increase,crop={w*2}:{h*2},"
              f"zoompan=z='{zoom}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={w}x{h}:fps={fps},setsar=1,format=yuv420p")
    else:
        vf = (f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},"
              f"fps={fps},setsar=1,format=yuv420p")
    run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", img, "-vf", vf,
         "-frames:v", frames, "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", out], log=lambda *_: None)


def render_video(project, rows, images, audio, srt, log=print):
    """rows: [(index,start,end,imgname)], images: list[Path] cùng thứ tự."""
    need("ffmpeg")
    v = project.cfg["video"]
    work = project.out / "_clips"
    work.mkdir(exist_ok=True)
    clips = []
    for k, ((idx, a, b, _), img) in enumerate(zip(rows, images)):
        # bù sai số làm tròn: mỗi clip dài đúng (b - a), clip cuối không cắt
        clip = work / f"c{idx:03d}.mp4"
        _clip(img, b - a, k, v, clip, log)
        clips.append(clip)
        if k % 10 == 0:
            log(f"  dựng ảnh {k+1}/{len(rows)}")
    listing = work / "list.txt"
    listing.write_text("".join(f"file '{c.as_posix()}'\n" for c in clips), encoding="utf-8")
    silent = project.out / "video_silent.mp4"
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", listing,
         "-c", "copy", silent], log=lambda *_: None)

    starts = {idx: a for idx, a, _, _ in rows}
    sfx = parse_sfx(project.path("sfx_cues"), len(rows), starts, project.root, log)
    music = project.path("music")
    music = music if music and music.exists() else None

    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-i", audio]
    n_in = 2
    filt, mix = [], ["[1:a]"]
    if music:
        cmd += ["-stream_loop", "-1", "-i", music]
        filt.append(f"[{n_in}:a]volume={v['music_volume']}[mus]")
        mix.append("[mus]")
        n_in += 1
    for j, (t, f, vol) in enumerate(sfx):
        cmd += ["-i", f]
        ms = int(t * 1000)
        filt.append(f"[{n_in}:a]volume={vol if vol is not None else v['sfx_volume']},adelay={ms}|{ms}[s{j}]")
        mix.append(f"[s{j}]")
        n_in += 1
    vmap = "0:v"
    if v["burn_subtitles"] and srt:
        style = f"FontSize={v['subtitle_font_size']},Outline=2,MarginV=40"
        sp = str(srt).replace("\\", "/").replace(":", "\\:")
        filt.append(f"[0:v]subtitles='{sp}':force_style='{style}'[vout]")
        vmap = "[vout]"
    final = project.out / "final.mp4"
    if len(mix) > 1:
        filt.append("".join(mix) + f"amix=inputs={len(mix)}:duration=first:normalize=0[aout]")
        amap = "[aout]"
    else:
        amap = "1:a"
    cmd += (["-filter_complex", ";".join(filt)] if filt else [])
    cmd += ["-map", vmap, "-map", amap, "-c:v", "copy" if vmap == "0:v" else "libx264",
            "-c:a", "aac", "-b:a", "192k", "-shortest", final]
    run(cmd, log=lambda *_: None)
    log(f"Đã xuất {final}" + (f" (+{len(sfx)} sound effect)" if sfx else "") + (" (+nhạc nền)" if music else ""))
    return final
