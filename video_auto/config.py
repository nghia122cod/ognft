"""Cấu hình. Mỗi video là 1 thư mục dự án có config.json (tạo bằng lệnh init)."""
import json
from pathlib import Path

DEFAULTS = {
    "kenh": "vi",                       # vi = Người Xưa Sống Sao (căn theo từ) | ja = kênh tâm lý Nhật (căn theo ký tự)
    "fps": 30,
    "width": 1920,
    "height": 1080,
    "downloads": "",                    # thư mục trình duyệt tải file về; để trống = ~/Downloads
    "thu_muc_voice": "",                # thư mục Voice dùng chung (vd Desktop/Voice); để trống = <video>/voice
    "thu_muc_anh_tai_ve": "",           # nơi extension Nghé nè lưu ảnh (vd "nghe ne anh"); app chép ảnh mới sang anh/
    "apps": {
        "claude": "https://claude.ai/new",
        "gemini": "https://gemini.google.com/app",
        "voice_app": "",                # app giọng đọc (lối tắt ElevenLabs trên Desktop) — lệnh tim-app tự điền
        "capcut": "",                   # lối tắt CapCut — lệnh tim-app tự điền
        "ghep_anh_bat": "",             # GHEP-ANH-TIMELINE.bat gốc — lệnh tim-app tự điền
    },
    "giong_doc": {                      # chỉ để hiện nhắc thông số khi mở app giọng đọc
        "giong": "Nhật Phong",
        "speed": "0.95",
        "stability": "40%",
        "similarity": "35%",
        "tu_dang_nhap": True,           # tự bấm ĐĂNG NHẬP (app đã "Nhớ tài khoản"; không lưu mật khẩu ở đây)
        "tieu_de_dang_nhap": "Đăng Nhập DGT ElevenLabs",
        "nut_dang_nhap": [0.276, 0.835],  # vị trí nút ĐĂNG NHẬP theo tỉ lệ cửa sổ (ngang, dọc)
    },
    "timeline": {
        "che_do": "claude_ai",          # claude_ai = chạy skill ghép giọng đọc trên Claude AI như cũ
                                        # tu_dong   = chạy cùng thuật toán của skill ngay trên máy (offline)
        "toi_thieu_giay": 1.0,
    },
    "mau_file": {                       # tên file skill kịch bản xuất ra (nhận từ Downloads)
        "prompt_anh": ["prompt-anh*.txt", "prompt*anh*.txt", "*prompt*.txt"],
        "kich_ban": ["kich-ban-tieng-nhat.txt", "kich-ban*.txt", "kichban*.txt", "script*.txt"],
        "kich_ban_bo_qua": ["*theo-y*"],          # bản tách ý không dùng cho giọng đọc
        "phu": ["units.json", "bando.txt", "kich-ban-theo-y.txt", "goi-san-xuat.md",
                "*sound*effect*.md", "*storyboard*.md"],
    },
    "cho_toi_da_phut": 240,             # chờ file ở các bước làm tay
}

# Tên file cố định trong thư mục dự án
F_PROMPT = "prompt-anh.txt"
D_VOICE = "voice"
F_KICH_BAN_TEN = "kich-ban.txt"
D_ANH = "anh"
F_TIMELINE = "timeline.txt"
F_VIDEO_ANH = "anh/video-anh.mp4"
AUDIO_EXT = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"}


def _merge(base, over):
    out = dict(base)
    for k, v in over.items():
        out[k] = _merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


class Project:
    def __init__(self, root, cfg):
        self.root = Path(root).resolve()
        self.cfg = cfg

    def p(self, rel) -> Path:
        return self.root / rel

    @property
    def downloads(self) -> Path:
        d = self.cfg.get("downloads")
        if d:
            return Path(d).expanduser()
        from .winpaths import known_folder
        return known_folder("Downloads") or Path.home() / "Downloads"

    @property
    def voice_dir(self) -> Path:
        d = self.cfg.get("thu_muc_voice")
        return Path(d).expanduser() if d else self.p(D_VOICE)

    @property
    def kich_ban(self) -> Path:
        return self.voice_dir / F_KICH_BAN_TEN

    def _newest_voice(self, exts):
        """File mới nhất trong thư mục voice, và phải mới hơn kịch bản của video này
        (thư mục Voice dùng chung nhiều video nên bỏ qua file của video cũ)."""
        d = self.voice_dir
        if not d.exists() or not self.kich_ban.exists():
            return None                 # chưa có kịch bản của video này thì chưa tính giọng/SRT nào
        since = self.kich_ban.stat().st_mtime - 1
        files = [f for f in d.iterdir() if f.is_file() and f.suffix.lower() in exts and f.stat().st_mtime >= since]
        return max(files, key=lambda f: f.stat().st_mtime) if files else None

    def voice_audio(self):
        return self._newest_voice(AUDIO_EXT)

    def srt(self):
        return self._newest_voice({".srt"})

    def save(self):
        (self.root / "config.json").write_text(json.dumps(self.cfg, ensure_ascii=False, indent=2), encoding="utf-8")


def load_project(root) -> Project:
    root = Path(root)
    cfg_path = root / "config.json"
    user = json.loads(cfg_path.read_text(encoding="utf-8")) if cfg_path.exists() else {}
    return Project(root, _merge(DEFAULTS, user))
