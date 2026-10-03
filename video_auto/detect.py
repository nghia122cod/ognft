"""Tự dò đường dẫn app trên máy Windows (Desktop + Start Menu) để điền config.json.

Chỉ ĐỌC tên file/thư mục, không mở hay sửa gì. Dò đúng những thứ quy trình cần:
lối tắt ElevenLabs (app giọng đọc), CapCut, GHEP-ANH-TIMELINE.bat và thư mục Voice trên Desktop.
"""
import fnmatch
import os
from pathlib import Path

TIM = {
    "voice_app": ["*eleven*.lnk", "*eleven*.exe", "*eleven*.url"],
    "capcut": ["capcut*.lnk", "capcut*.exe"],
    "ghep_anh_bat": ["ghep-anh*.bat", "ghep_anh*.bat", "ghep-anh*.lnk", "ghep*anh*.bat"],
}


def desktops():
    env = os.environ
    home = Path.home()
    cands = [home / "Desktop", home / "OneDrive" / "Desktop", home / "OneDrive" / "Màn hình nền"]
    for k in ("OneDrive", "OneDriveConsumer", "OneDriveCommercial"):
        if env.get(k):
            cands.append(Path(env[k]) / "Desktop")
    if env.get("PUBLIC"):
        cands.append(Path(env["PUBLIC"]) / "Desktop")
    seen, out = set(), []
    for c in cands:
        if c.is_dir() and c.resolve() not in seen:
            seen.add(c.resolve())
            out.append(c)
    return out


def _start_menu():
    env = os.environ
    roots = [Path(env[k]) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
             for k in ("APPDATA", "ProgramData") if env.get(k)]
    return [r for r in roots if r.is_dir()]


def _find(folders, patterns, deep=False):
    for d in folders:
        it = d.rglob("*") if deep else d.iterdir()
        try:
            for f in it:
                if f.is_file() and any(fnmatch.fnmatch(f.name.lower(), p) for p in patterns):
                    return f
        except OSError:
            continue
    return None


def tim_app():
    """Trả dict {khoá config: đường dẫn} cho những gì tìm thấy."""
    dk = desktops()
    found = {}
    for key, pats in TIM.items():
        f = _find(dk, pats) or (_find(_start_menu(), pats, deep=True) if key != "ghep_anh_bat" else None)
        if f:
            found[key] = str(f)
    if "capcut" not in found and os.environ.get("LOCALAPPDATA"):
        exe = Path(os.environ["LOCALAPPDATA"]) / "CapCut" / "Apps" / "CapCut.exe"
        if exe.exists():
            found["capcut"] = str(exe)
    for d in dk:
        v = next((x for x in d.iterdir() if x.is_dir() and x.name.lower() == "voice"), None)
        if v:
            found["thu_muc_voice"] = str(v)
            break
    return found


def ap_dung(project, log=print):
    """Điền những đường dẫn tìm được vào config.json (không ghi đè ô người dùng đã tự điền)."""
    found = tim_app()
    ten = {"voice_app": "App giọng đọc (ElevenLabs)", "capcut": "CapCut",
           "ghep_anh_bat": "GHEP-ANH-TIMELINE.bat", "thu_muc_voice": "Thư mục Voice"}
    changed = False
    for key, label in ten.items():
        cur = project.cfg.get(key) if key == "thu_muc_voice" else project.cfg["apps"].get(key)
        val = found.get(key)
        if cur:
            log(f"  {label}: {cur} (đã có trong config)")
        elif val:
            if key == "thu_muc_voice":
                project.cfg[key] = val
            else:
                project.cfg["apps"][key] = val
            changed = True
            log(f"  {label}: {val}  ✔ tìm thấy")
        else:
            log(f"  {label}: KHÔNG tìm thấy — điền tay trong config.json")
    if changed:
        project.root.mkdir(parents=True, exist_ok=True)
        project.save()
        log("Đã lưu vào config.json.")
    return found
