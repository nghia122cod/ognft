"""Mô phỏng trọn 7 bước: người dùng tải file về Downloads ở các bước làm tay, app tự nhận và đi tiếp."""
import json
import subprocess
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

from video_auto import ghep_anh, sfx, steps
from video_auto.config import load_project
from tests.test_timeline_vi import make_case


def ff(*args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *map(str, args)], check=True)


class AutoUI(steps.UI):
    def __init__(self):
        self.logs, self.asked = [], []
        self.stop = threading.Event()

    def log(self, msg):
        self.logs.append(str(msg))

    def confirm(self, msg):
        self.asked.append(msg)
        return True


class GhepAnhTest(unittest.TestCase):
    def test_loi_va_sua(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            tl = d / "timeline.txt"
            tl.write_text("45\n31\n60\n", encoding="utf-8")
            a = d / "anh"
            a.mkdir()
            ff("-f", "lavfi", "-i", "color=red:s=320x180", "-frames:v", 1, a / "001-mo-dau.jpg")
            ff("-f", "lavfi", "-i", "color=green:s=320x180", "-frames:v", 1, a / "Gemini_Image (2).png")
            ff("-f", "lavfi", "-i", "color=blue:s=320x180", "-frames:v", 1, a / "03_ket.jpg")
            with self.assertRaisesRegex(ghep_anh.LoiGhep, "lẫn đuôi"):
                ghep_anh.kiem_tra(tl, a)
            ghep_anh.sua_anh(a, log=lambda *_: None)
            self.assertTrue((a / "_goc" / "Gemini_Image (2).png").exists())   # bản gốc còn nguyên
            info = ghep_anh.kiem_tra(tl, a)
            self.assertEqual([f.name for f in info["thu_tu"]],
                             ["001-mo-dau.jpg", "2-Gemini_Image (2).jpg", "03_ket.jpg"])  # 03 = 3, không phải hệ 8
            out = ghep_anh.ghep(info, a, 30, 320, 180, log=lambda *_: None)
            self.assertEqual(ghep_anh._dem_frame(out), 136)

    def test_bao_loi(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "t.txt").write_text("30\n30\n", encoding="utf-8")
            (d / "1.jpg").write_bytes(b"x")
            with self.assertRaisesRegex(ghep_anh.LoiGhep, r"Số ảnh \(1\) khác số dòng timeline \(2\)"):
                ghep_anh.kiem_tra(d / "t.txt", d)
            (d / "1-b.jpg").write_bytes(b"x")
            with self.assertRaisesRegex(ghep_anh.LoiGhep, "Hai ảnh cùng mang số 1"):
                ghep_anh.kiem_tra(d / "t.txt", d)


class SfxTest(unittest.TestCase):
    def test_bang(self):
        md = ("## 8. Sound effects\n\n| Ảnh # | Thời điểm | Sound Effect (CapCut search) | Mục đích |\n"
              "|---|---|---|---|\n| 1 | 0:00 | Whoosh Transition | mở đầu |\n| 3 | 0:07 | Notification Ping | nhấn |\n")
        rows = sfx.doc_bang(md)
        self.assertEqual([(r["anh"], r["sfx"]) for r in rows], [(1, "Whoosh Transition"), (3, "Notification Ping")])


class FullFlow(unittest.TestCase):
    def test_bay_buoc(self):
        script, srt = make_case(7)
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            dl, proj = d / "Downloads", d / "video1"
            dl.mkdir()
            proj.mkdir()
            (proj / "config.json").write_text(json.dumps({
                "downloads": str(dl), "width": 320, "height": 180,
                "timeline": {"che_do": "tu_dong"}, "cho_toi_da_phut": 0.5}), encoding="utf-8")
            p = load_project(proj)
            from video_auto import timeline_vi
            n = len(timeline_vi.cau_co_ban(script))
            ui = AutoUI()

            def nguoi_dung():
                """Làm thay người dùng ở các app khác: tải file về Downloads theo đúng thứ tự."""
                time.sleep(0.5)
                (dl / "prompt-anh-gemini-theo-y.txt").write_text(
                    "\n".join(f"{i} scene {i}" for i in range(1, n + 1)), encoding="utf-8")
                (dl / "kich-ban-theo-y.txt").write_text("không được dùng làm giọng đọc", encoding="utf-8")
                (dl / "kich-ban.txt").write_text(script, encoding="utf-8")
                (dl / "goi-san-xuat.md").write_text(
                    "| Ảnh # | Thời điểm | Sound Effect (CapCut search) | Mục đích |\n|---|---|---|---|\n"
                    "| 2 | 0:05 | Whoosh Transition | chuyển |\n", encoding="utf-8")
                time.sleep(1)
                for i in range(1, n + 1):          # extension tải ảnh về Downloads
                    ff("-f", "lavfi", "-i", f"color=0x{i*40%255:02x}2080:s=320x180", "-frames:v", 1,
                       dl / f"{i:03d}-canh.jpg")
                time.sleep(1)
                ff("-f", "lavfi", "-i", "sine=duration=3", p.root / "voice" / "giong-doc.mp3")
                time.sleep(1)
                (dl / "giong-doc.srt").write_text(srt, encoding="utf-8")   # CapCut xuất SRT

            p.root.joinpath("voice").mkdir()
            (p.root / "sfx").mkdir()
            ff("-f", "lavfi", "-i", "sine=frequency=900:duration=0.3", p.root / "sfx" / "Whoosh Transition.wav")
            threading.Thread(target=nguoi_dung, daemon=True).start()
            with mock.patch.object(steps, "launch"), mock.patch.object(steps, "open_folder"), \
                    mock.patch("video_auto.watch.time.sleep", lambda s, _z=time.sleep: _z(0.2)):
                try:
                    steps.run_all(p, ui)
                except Exception:
                    print("\n".join(ui.logs))
                    raise
            log = "\n".join(ui.logs)
            self.assertEqual((proj / "voice" / "kich-ban.txt").read_text(encoding="utf-8"), script, log)
            self.assertEqual(len(ghep_anh.doc_timeline(proj / "timeline.txt")), n)
            frames = sum(ghep_anh.doc_timeline(proj / "timeline.txt"))
            self.assertLessEqual(abs(ghep_anh._dem_frame(proj / "anh" / "video-anh.mp4") - frames), 1)  # như .bat: lệch ≤ 1 frame là ĐẠT
            self.assertIn("Whoosh Transition", (proj / "sound-effects-capcut.md").read_text(encoding="utf-8"))
            self.assertTrue((proj / "sfx-track.wav").exists())
            self.assertTrue((proj / ".da-xuat").exists())
            self.assertTrue(all(s.done(p) for s in steps.STEPS))


if __name__ == "__main__":
    unittest.main()


class DetectTest(unittest.TestCase):
    def test_tim_tren_desktop(self):
        """Đúng tên file trên Desktop thật của người dùng (OneDrive\\Máy tính)."""
        from video_auto import detect
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            dk = home / "OneDrive" / "Máy tính"
            dk.mkdir(parents=True)
            for name in ("Mo_Tool_Giong_Doc.bat - Lối tắt.lnk", "Dgt_ElevenlabsVP.exe - Lối tắt.lnk", "CapCut.lnk",
                         "GHEP-ANH-TIMELINE.bat4.bat", "CHAY-MINI-CAPCUT.bat", "xuong-timeline - Lối tắt.lnk",
                         "Zalo.lnk"):
                (dk / name).write_bytes(b"")
            (dk / "Voice").mkdir()
            (home / "Pictures" / "nghe ne anh").mkdir(parents=True)
            with mock.patch.object(Path, "home", lambda: home), mock.patch.dict("os.environ", {}, clear=True):
                p = load_project(home / "video1")
                detect.ap_dung(p, log=lambda *_: None)
            p = load_project(home / "video1")
            self.assertTrue(p.cfg["apps"]["voice_app"].endswith("Dgt_ElevenlabsVP.exe - Lối tắt.lnk"))
            self.assertTrue(p.cfg["apps"]["capcut"].endswith("CapCut.lnk"))
            self.assertTrue(p.cfg["apps"]["ghep_anh_bat"].endswith("GHEP-ANH-TIMELINE.bat4.bat"))
            self.assertTrue(p.cfg["apps"]["ghep_anh_tool"].endswith("Mo_Tool_Giong_Doc.bat - Lối tắt.lnk"))
            self.assertEqual(p.voice_dir, dk / "Voice")
            self.assertEqual(Path(p.cfg["thu_muc_anh_tai_ve"]), home / "Pictures" / "nghe ne anh")
