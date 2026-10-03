"""Bước giọng đọc: edge-tts (miễn phí) hoặc app giọng đọc ngoài."""
import asyncio
import time

from .apps import launch
from .textutil import read_text


def make_voice(project, log=print):
    v = project.cfg["voice"]
    text_path = project.path("voice_text")
    audio = project.path("voice_audio")
    audio.parent.mkdir(parents=True, exist_ok=True)

    if v["mode"] == "external":
        app = project.cfg["apps"].get("voice_app")
        if audio.exists():
            log(f"Đã có {audio.name}, bỏ qua bước tạo giọng.")
            return audio
        if not app:
            raise RuntimeError("Chưa đặt apps.voice_app trong config.json.")
        log(f"Mở app giọng đọc. Hãy nạp {text_path} và lưu kết quả thành {audio}.")
        launch(app, log)
        deadline = time.time() + v["external_wait_seconds"]
        last = -1
        while time.time() < deadline:
            if audio.exists():
                size = audio.stat().st_size
                if size > 0 and size == last:      # file đã ổn định (ghi xong)
                    return audio
                last = size
            time.sleep(3)
        raise TimeoutError(f"Hết thời gian chờ {audio}.")

    try:
        import edge_tts
    except ImportError as e:
        raise RuntimeError("Thiếu edge-tts: pip install -r requirements.txt") from e
    text = read_text(text_path).strip()
    if not text:
        raise RuntimeError(f"{text_path} trống.")
    log(f"Tạo giọng bằng edge-tts ({v['name']}, rate {v['rate']}) ...")

    async def go():
        comm = edge_tts.Communicate(text, v["name"], rate=v["rate"], pitch=v["pitch"], volume=v["volume"])
        await comm.save(str(audio))

    asyncio.run(go())
    log(f"Đã lưu {audio}")
    return audio
