"""Ghi timeline.txt và phụ đề SRT."""
from .textutil import split_subtitle_chunks


def fmt_srt(t: float) -> str:
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def write_timeline(path, spans, images):
    """Mỗi dòng: số ý <TAB> bắt đầu <TAB> kết thúc <TAB> tên ảnh (giây, 3 chữ số thập phân)."""
    lines = ["# index\tstart_s\tend_s\timage"]
    for sp, img in zip(spans, images):
        lines.append(f"{sp.index}\t{sp.start:.3f}\t{sp.end:.3f}\t{img.name}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def read_timeline(path):
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        i, a, b, name = line.split("\t")
        rows.append((int(i), float(a), float(b), name))
    return rows


def write_srt(path, spans, max_chars):
    """Phụ đề lấy nguyên văn từ kịch bản; thời gian chia theo độ dài chữ trong từng ý."""
    out, n = [], 0
    for sp in spans:
        chunks = split_subtitle_chunks(sp.text, max_chars) or [sp.text]
        total = sum(len(c) for c in chunks) or 1
        t = sp.start
        for c in chunks:
            d = (sp.end - sp.start) * len(c) / total
            n += 1
            out.append(f"{n}\n{fmt_srt(t)} --> {fmt_srt(t + d)}\n{c}\n")
            t += d
    path.write_text("\n".join(out), encoding="utf-8")
    return n
