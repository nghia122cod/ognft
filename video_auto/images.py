"""Kiểm tra ảnh khớp số ý; sửa theo kiểu không phá hủy (chép sang images_fixed)."""
import re
import shutil
from pathlib import Path

EXTS = {".png", ".jpg", ".jpeg", ".webp"}
_NUM = re.compile(r"(\d+)")


def _num(p: Path):
    m = _NUM.findall(p.stem)
    return int(m[-1]) if m else None


def scan(images_dir: Path, n: int):
    files = sorted(p for p in images_dir.glob("*") if p.suffix.lower() in EXTS) if images_dir.exists() else []
    by_num: dict[int, list[Path]] = {}
    unnumbered = []
    for f in files:
        k = _num(f)
        if k is None:
            unnumbered.append(f)
        else:
            by_num.setdefault(k, []).append(f)
    problems = []
    missing = [i for i in range(1, n + 1) if i not in by_num]
    dups = {k: v for k, v in by_num.items() if len(v) > 1}
    extra = sorted(k for k in by_num if k > n or k < 1)
    if missing:
        problems.append(f"Thiếu ảnh số: {_ranges(missing)}")
    if dups:
        problems.append("Trùng số: " + ", ".join(f"{k}({len(v)} file)" for k, v in sorted(dups.items())))
    if extra:
        problems.append(f"Ảnh thừa số: {_ranges(extra)}")
    if unnumbered:
        problems.append(f"{len(unnumbered)} ảnh không có số trong tên")
    return files, by_num, unnumbered, problems


def _ranges(nums):
    out, start, prev = [], None, None
    for x in nums + [None]:
        if start is None:
            start = prev = x
        elif x is not None and x == prev + 1:
            prev = x
        else:
            out.append(str(start) if start == prev else f"{start}-{prev}")
            start = prev = x
    return ", ".join(out)


def resolve(images_dir: Path, n: int, work_dir: Path, autofix=True, log=print):
    """Trả list n đường dẫn ảnh theo thứ tự ý 1..n.

    Ảnh gốc không bị đổi tên/xóa. Khi cần sửa, bản đã chuẩn hoá được chép vào work_dir.
    """
    files, by_num, unnumbered, problems = scan(images_dir, n)
    if not files:
        raise RuntimeError(f"Không có ảnh trong {images_dir}")
    if not problems:
        log(f"Ảnh OK: {n}/{n}.")
        return [by_num[i][0] for i in range(1, n + 1)]

    for p in problems:
        log("⚠ " + p)
    if not autofix:
        raise RuntimeError("Ảnh chưa khớp số ý và autofix tắt.")

    numbered = [sorted(by_num[k])[0] for k in sorted(by_num) if 1 <= k]
    pool = numbered if not unnumbered else sorted(unnumbered, key=lambda p: p.stat().st_mtime)
    if len(pool) == n:
        log(f"Tự sửa: đánh lại số 1..{n} theo thứ tự {'thời gian tạo' if unnumbered else 'số hiện có'} (chép vào {work_dir.name}/).")
        chosen = pool
    elif len(pool) > n and not unnumbered:
        log(f"Tự sửa: lấy ảnh số 1..{n}, bỏ ảnh thừa.")
        chosen = [by_num[i][0] if i in by_num else None for i in range(1, n + 1)]
        if any(c is None for c in chosen):
            raise RuntimeError("Không tự sửa được: thiếu ảnh " + _ranges([i for i, c in enumerate(chosen, 1) if c is None]))
    else:
        raise RuntimeError(
            f"Không tự sửa được: có {len(pool)} ảnh nhưng kịch bản có {n} ý. "
            "Hãy tạo thêm/bỏ bớt ảnh rồi chạy lại.")

    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir(parents=True)
    out = []
    for i, src in enumerate(chosen, 1):
        dst = work_dir / f"{i:03d}{src.suffix.lower()}"
        shutil.copy2(src, dst)
        out.append(dst)
    return out
