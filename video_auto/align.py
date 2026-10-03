"""Căn từng ý của kịch bản vào mốc thời gian giọng đọc (word timestamps của Whisper).

Không cần LLM: kịch bản gốc và giọng đọc cùng nội dung nên so khớp chuỗi token
(difflib) rồi nội suy các token không khớp.
"""
from dataclasses import dataclass
from difflib import SequenceMatcher

from .textutil import tokens


@dataclass
class Word:
    text: str
    start: float
    end: float


@dataclass
class Span:
    index: int      # 1-based
    text: str
    start: float
    end: float


def _transcript_tokens(words: list[Word]):
    toks, starts, ends = [], [], []
    for w in words:
        ts = tokens(w.text)
        if not ts:
            continue
        step = (w.end - w.start) / len(ts)
        for i, t in enumerate(ts):
            toks.append(t)
            starts.append(w.start + i * step)
            ends.append(w.start + (i + 1) * step)
    return toks, starts, ends


def align_segments(segments: list[str], words: list[Word], total_duration: float) -> list[Span]:
    t_toks, t_starts, t_ends = _transcript_tokens(words)
    s_toks, owner = [], []
    for i, seg in enumerate(segments):
        ts = tokens(seg)
        s_toks.extend(ts)
        owner.extend([i] * len(ts))
    if not s_toks or not t_toks:
        raise ValueError("Kịch bản hoặc giọng đọc không có nội dung để căn.")

    # map: chỉ số token kịch bản -> chỉ số token giọng đọc (None nếu không khớp)
    mapping = [None] * len(s_toks)
    sm = SequenceMatcher(None, s_toks, t_toks, autojunk=False)
    for a, b, n in sm.get_matching_blocks():
        for k in range(n):
            mapping[a + k] = b + k

    # nội suy token không khớp theo token khớp gần nhất (tuyến tính)
    known = [i for i, m in enumerate(mapping) if m is not None]
    if not known:
        raise ValueError("Không khớp được kịch bản với giọng đọc (sai ngôn ngữ/file?).")
    pos = [None] * len(s_toks)
    for i in range(len(s_toks)):
        if mapping[i] is not None:
            pos[i] = float(mapping[i])
            continue
        left = max((k for k in known if k < i), default=None)
        right = min((k for k in known if k > i), default=None)
        if left is None:
            pos[i] = max(0.0, mapping[right] - (right - i))
        elif right is None:
            pos[i] = min(len(t_toks) - 1.0, mapping[left] + (i - left))
        else:
            frac = (i - left) / (right - left)
            pos[i] = mapping[left] + frac * (mapping[right] - mapping[left])

    def time_at(p: float) -> float:
        p = min(max(p, 0.0), len(t_toks) - 1.0)
        i = int(p)
        return t_starts[i] + (p - i) * (t_ends[i] - t_starts[i])

    first_tok = {}
    for i, o in enumerate(owner):
        first_tok.setdefault(o, i)
    starts = []
    for seg_i in range(len(segments)):
        if seg_i in first_tok:
            starts.append(time_at(pos[first_tok[seg_i]]))
        else:                      # ý rỗng token: kế thừa ý trước
            starts.append(starts[-1] if starts else 0.0)
    starts[0] = 0.0                # ảnh đầu luôn bắt đầu từ 0
    for i in range(1, len(starts)):  # đảm bảo không giảm
        starts[i] = max(starts[i], starts[i - 1])

    spans = []
    for i, seg in enumerate(segments):
        end = starts[i + 1] if i + 1 < len(segments) else total_duration
        spans.append(Span(i + 1, seg, starts[i], max(end, starts[i] + 0.1)))
    return spans
