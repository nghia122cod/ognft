"""Tách kịch bản thành các ý và token hoá để căn giọng đọc."""
import re

_NUM_PREFIX = re.compile(r"^\s*(?:ý\s*)?[#\[(]?(\d+)[\]).:：、]?\s*", re.IGNORECASE)
CJK = r"぀-ヿ㐀-䶿一-鿿ｦ-ﾟ"
_TOKEN = re.compile(rf"[{CJK}]|[^\W_]+", re.UNICODE)


def read_text(path) -> str:
    return path.read_text(encoding="utf-8-sig")


def split_segments(text: str) -> list[str]:
    """Mỗi ý cách nhau bằng dòng trống. Bỏ số thứ tự đầu ý nếu mọi ý đều có và liên tiếp."""
    blocks = [re.sub(r"\s*\n\s*", " ", b).strip()
              for b in re.split(r"\n\s*\n", text.replace("\r\n", "\n")) if b.strip()]
    nums = [_NUM_PREFIX.match(b) for b in blocks]
    if blocks and all(nums) and [int(m.group(1)) for m in nums] == list(range(1, len(blocks) + 1)):
        blocks = [_NUM_PREFIX.sub("", b, count=1).strip() for b in blocks]
    return blocks


def tokens(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN.findall(text)]


def split_subtitle_chunks(text: str, max_chars: int) -> list[str]:
    """Cắt 1 ý thành các dòng phụ đề ngắn theo dấu câu rồi theo độ dài."""
    parts = [p.strip() for p in re.split(r"(?<=[。！？!?\.…])\s*", text) if p.strip()]
    chunks = []
    for p in parts:
        sub = [s.strip() for s in re.split(r"(?<=[、，,;；:：])\s*", p) if s.strip()]
        cur = ""
        for s in sub:
            if cur and len(cur) + len(s) > max_chars:
                chunks.append(cur)
                cur = s
            else:
                cur = (cur + (" " if cur and " " in text else "") + s) if cur else s
        if cur:
            chunks.append(cur)
    out = []
    for c in chunks:
        while len(c) > max_chars * 1.6:
            cut = c.rfind(" ", 0, max_chars)
            cut = cut if cut > 0 else max_chars
            out.append(c[:cut].strip())
            c = c[cut:].strip()
        out.append(c)
    return [c for c in out if c]
