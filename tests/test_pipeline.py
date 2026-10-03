import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from video_auto.align import Word, align_segments
from video_auto.config import load_project
from video_auto.images import scan
from video_auto.pipeline import step_render, step_subtitles_timeline
from video_auto.textutil import split_segments

SEGS = ["Xin chào các bạn, hôm nay chúng ta nói về người xưa.",
        "Họ ngủ ở đâu? Trong hang động, tất nhiên rồi.",
        "Còn đồ ăn thì sao, họ phải đi săn mỗi ngày.",
        "Cảm ơn đã xem video này."]


def words_for(segs, per=0.4, drift=True):
    out, t = [], 0.0
    for s in segs:
        for w in s.split():
            out.append(Word((" " + w) if drift else w, t, t + per))
            t += per
    return out, t


class AlignTest(unittest.TestCase):
    def test_exact(self):
        words, total = words_for(SEGS)
        spans = align_segments(SEGS, words, total)
        self.assertEqual(spans[0].start, 0.0)
        n0 = len(SEGS[0].split())
        self.assertAlmostEqual(spans[1].start, n0 * 0.4, places=2)
        self.assertAlmostEqual(spans[-1].end, total, places=2)

    def test_whisper_errors_do_not_shift(self):
        words, total = words_for(SEGS)
        words[3] = Word(" bạng", words[3].start, words[3].end)      # sai chữ
        del words[10]                                                # rớt 1 từ
        words.insert(5, Word(" ờ", words[5].start, words[5].start))  # thừa 1 từ
        spans = align_segments(SEGS, words, total)
        n0 = len(SEGS[0].split())
        self.assertAlmostEqual(spans[1].start, n0 * 0.4, delta=0.5)
        self.assertTrue(all(b.start >= a.start for a, b in zip(spans, spans[1:])))

    def test_japanese(self):
        segs = ["今日は心理学のお話です。", "一人が好きな人の特徴。"]
        words = [Word(c, i * 0.2, i * 0.2 + 0.2) for i, c in enumerate("".join(segs))]
        spans = align_segments(segs, words, len(words) * 0.2)
        self.assertAlmostEqual(spans[1].start, len(segs[0]) * 0.2, delta=0.25)

    def test_split_numbered(self):
        self.assertEqual(split_segments("1. Một\n\n2. Hai\n"), ["Một", "Hai"])
        self.assertEqual(split_segments("1. Một\n\n3. Ba"), ["1. Một", "3. Ba"])


class ImagesTest(unittest.TestCase):
    def test_scan_reports(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            for name in ("001.png", "002.png", "004.png", "004_copy.png"):
                (d / name).write_bytes(b"x")
            _, _, _, problems = scan(d, 4)
            self.assertTrue(any("Thiếu ảnh số: 3" in p for p in problems))
            self.assertTrue(any("Trùng" in p for p in problems))


class EndToEnd(unittest.TestCase):
    def test_full(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "images").mkdir()
            (root / "voice").mkdir()
            (root / "segments.txt").write_text("\n\n".join(SEGS), encoding="utf-8")
            words, total = words_for(SEGS)
            for i in range(4):   # ảnh đặt tên lộn xộn không số -> phải tự sửa theo thứ tự thời gian
                subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                                f"color=c={['red','green','blue','yellow'][i]}:s=640x360",
                                "-frames:v", "1", str(root / "images" / f"Gemini_Generated_{chr(97+i)}.png")], check=True)
                import os, time
                os.utime(root / "images" / f"Gemini_Generated_{chr(97+i)}.png", (time.time() + i, time.time() + i))
            audio = root / "voice" / "voice.mp3"
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                            f"sine=frequency=440:duration={total}", str(audio)], check=True)
            (root / "sfx_cues.txt").write_text("2 whoosh.wav 0.5\n", encoding="utf-8")
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                            "sine=frequency=900:duration=0.3", str(root / "whoosh.wav")], check=True)
            p = load_project(root)
            p.cfg["video"].update(width=640, height=360, fps=15, burn_subtitles=True)
            (p.out / "words.json").write_text(json.dumps([w.__dict__ for w in words]), encoding="utf-8")
            logs = []
            step_subtitles_timeline(p, logs.append)
            tl = (p.out / "timeline.txt").read_text(encoding="utf-8")
            self.assertEqual(len([l for l in tl.splitlines() if not l.startswith("#")]), 4)
            self.assertIn("001.png", tl)
            srt = (p.out / "voice.srt").read_text(encoding="utf-8")
            self.assertIn("-->", srt)
            final = step_render(p, logs.append)
            self.assertTrue(final.exists() and final.stat().st_size > 1000)
            out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                  "-of", "default=nw=1:nk=1", str(final)], capture_output=True, text=True)
            self.assertAlmostEqual(float(out.stdout), total, delta=0.6)


if __name__ == "__main__":
    unittest.main()
