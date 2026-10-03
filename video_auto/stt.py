"""Whisper (faster-whisper) lấy mốc thời gian từng từ từ file giọng đọc."""
import json

from .align import Word


def transcribe(project, audio, log=print) -> list[Word]:
    cache = project.out / "words.json"
    if cache.exists() and cache.stat().st_mtime >= audio.stat().st_mtime:
        log("Dùng lại kết quả Whisper đã lưu (words.json).")
        return [Word(**w) for w in json.loads(cache.read_text(encoding="utf-8"))]
    try:
        from faster_whisper import WhisperModel
    except ImportError as e:
        raise RuntimeError("Thiếu faster-whisper: pip install -r requirements.txt") from e
    s = project.cfg["stt"]
    log(f"Whisper model '{s['model']}' đang chạy (lần đầu sẽ tải model) ...")
    model = WhisperModel(s["model"], device=s["device"], compute_type=s["compute_type"])
    lang = project.cfg["language"]
    segs, _ = model.transcribe(str(audio), language=lang, word_timestamps=True,
                               vad_filter=False, condition_on_previous_text=False)
    words = [Word(w.word, w.start, w.end) for seg in segs for w in (seg.words or [])]
    if not words:
        raise RuntimeError("Whisper không nhận ra từ nào trong file giọng đọc.")
    cache.write_text(json.dumps([w.__dict__ for w in words], ensure_ascii=False), encoding="utf-8")
    log(f"Nhận diện {len(words)} từ.")
    return words
