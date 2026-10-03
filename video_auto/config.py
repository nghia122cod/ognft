"""Cấu hình dự án. Mọi đường dẫn được đọc từ config.json trong thư mục dự án."""
import json
from pathlib import Path

DEFAULTS = {
    "language": "vi",                      # vi | ja | en ...
    "voice": {
        "mode": "edge",                    # edge = tạo bằng edge-tts | external = mở app giọng đọc, chờ file
        "name": "vi-VN-HoaiMyNeural",      # ja: ja-JP-NanamiNeural, en: en-US-AriaNeural
        "rate": "+0%",                     # tốc độ, vd "-10%"
        "pitch": "+0Hz",
        "volume": "+0%",
        "external_wait_seconds": 1800,     # chờ tối đa khi dùng app giọng đọc ngoài
    },
    "stt": {
        "model": "small",                  # tiny/base/small/medium/large-v3
        "device": "auto",
        "compute_type": "auto",
    },
    "video": {
        "width": 1920,
        "height": 1080,
        "fps": 30,
        "ken_burns": True,
        "burn_subtitles": False,
        "subtitle_max_chars": 28,
        "subtitle_font_size": 18,
        "music_volume": 0.12,
        "sfx_volume": 0.8,
    },
    "apps": {                              # để trống nếu không dùng
        "capcut": "",
        "voice_app": "",
        "browser_url_images": "https://gemini.google.com/app",
    },
    "files": {
        "segments": "segments.txt",        # kịch bản tách theo ý, mỗi ý cách nhau 1 dòng trống
        "voice_text": "voice/voice_text.txt",
        "image_prompts": "image_prompts.txt",
        "images_dir": "images",
        "voice_audio": "voice/voice.mp3",
        "sfx_cues": "sfx_cues.txt",
        "music": "",                       # file nhạc nền, tùy chọn
        "output_dir": "output",
    },
}


def _merge(base: dict, over: dict) -> dict:
    out = dict(base)
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out


class Project:
    def __init__(self, root, cfg: dict):
        self.root = Path(root).resolve()
        self.cfg = cfg

    def path(self, key: str) -> Path:
        value = self.cfg["files"][key]
        return self.root / value if value else None

    @property
    def out(self) -> Path:
        d = self.path("output_dir")
        d.mkdir(parents=True, exist_ok=True)
        return d

    def save(self):
        (self.root / "config.json").write_text(
            json.dumps(self.cfg, ensure_ascii=False, indent=2), encoding="utf-8")


def load_project(root) -> Project:
    root = Path(root)
    cfg_path = root / "config.json"
    user = {}
    if cfg_path.exists():
        user = json.loads(cfg_path.read_text(encoding="utf-8"))
    return Project(root, _merge(DEFAULTS, user))
