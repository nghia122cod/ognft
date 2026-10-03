"""So sánh bản Python với build-timeline.js gốc (cần Node; bỏ qua nếu không có)."""
import random
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from video_auto import timeline_vi

REF = Path(__file__).parent / "ref"
WORDS = ("người xưa ngủ ở đâu trong hang động lạnh lẽo, họ phải săn bắt hái lượm mỗi ngày; "
         "lửa là thứ quý giá nhất: không có lửa thì không sống nổi bạn có tin không").split()


def make_case(seed):
    rnd = random.Random(seed)
    sents = []
    for _ in range(rnd.randint(15, 40)):
        n = rnd.choice([3, 4, 5, 8, 12, 18, 25])
        s = " ".join(rnd.choice(WORDS) for _ in range(n))
        sents.append(s[0].upper() + s[1:] + rnd.choice([".", "?", "!", "."]))
    script = " ".join(sents)
    # SRT: đọc lại kịch bản, rớt/sai vài từ như phụ đề tự động CapCut
    words = [w for w in script.split() if rnd.random() > 0.05]
    words = [("x" + w) if rnd.random() < 0.05 else w for w in words]
    blocks, t, i, k = [], 0.0, 0, 1
    while i < len(words):
        n = rnd.randint(4, 9)
        chunk = words[i:i + n]
        d = len(chunk) * rnd.uniform(0.22, 0.32)
        a, b = t, t + d
        f = lambda x: f"{int(x//3600):02d}:{int(x//60%60):02d}:{int(x%60):02d},{int(round((x%1)*1000)) % 1000:03d}"
        blocks.append(f"{k}\n{f(a)} --> {f(b)}\n{' '.join(chunk)}\n")
        t, i, k = b + rnd.uniform(0, 0.4), i + n, k + 1
    return script, "\n".join(blocks)


@unittest.skipUnless(shutil.which("node"), "cần node để so với bản gốc")
class Parity(unittest.TestCase):
    def run_both(self, script, srt, extra_js, **kw):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "kb.txt").write_text(script, encoding="utf-8")
            (d / "g.srt").write_text(srt, encoding="utf-8")
            if "ban_do" in kw:
                (d / "bd.txt").write_text("\n".join(map(str, kw.pop("ban_do"))), encoding="utf-8")
                kw["ban_do_path"] = d / "bd.txt"
            subprocess.run(["node", REF / "build-timeline.js", d / "kb.txt", d / "g.srt", *extra_js,
                            "--out", d / "js"], check=True, capture_output=True)
            timeline_vi.build(d / "kb.txt", d / "g.srt", d / "py", **kw)
            for name in ("timeline.txt", "timeline-bang.md"):
                self.assertEqual((d / "js" / name).read_text(encoding="utf-8"),
                                 (d / "py" / name).read_text(encoding="utf-8"), name)

    def test_so_anh(self):
        for seed in range(12):
            script, srt = make_case(seed)
            n = len(timeline_vi.cau_co_ban(script)) + random.Random(seed).randint(-8, 15)
            with self.subTest(seed=seed):
                self.run_both(script, srt, ["--so-anh", str(n)], so_anh=n)

    def test_khong_ep(self):
        script, srt = make_case(99)
        self.run_both(script, srt, [], so_anh=0)

    def test_ban_do(self):
        for seed in range(6):
            script, srt = make_case(100 + seed)
            rnd = random.Random(seed)
            bd = [rnd.choice([0, 1, 1, 2, 3, 5]) for _ in timeline_vi.cau_co_ban(script)]
            with self.subTest(seed=seed):
                with tempfile.TemporaryDirectory() as d:
                    p = Path(d) / "bd.txt"
                    p.write_text("\n".join(map(str, bd)))
                    self.run_both(script, srt, ["--ban-do", str(p)], ban_do=bd)


if __name__ == "__main__":
    unittest.main()
