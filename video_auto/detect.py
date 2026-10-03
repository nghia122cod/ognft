"""Tự dò đường dẫn app trên máy Windows (Desktop + Start Menu) để điền config.json.

Chỉ ĐỌC tên file/thư mục, không mở hay sửa gì. Dò đúng những thứ quy trình cần:
lối tắt ElevenLabs (app giọng đọc), CapCut, GHEP-ANH-TIMELINE.bat và thư mục Voice trên Desktop.
"""
import fnmatch
import os
from pathlib import Path

TIM = {
    # ưu tiên đúng thứ người dùng khoanh: Dgt_ElevenlabsVP.exe - Lối tắt
    "voice_app": ["*eleven*.lnk", "*eleven*.exe", "*eleven*.url"],
    "capcut": ["capcut.lnk", "capcut*.lnk", "capcut*.exe"],
    "ghep_anh_bat": ["ghep-anh-timeline*.bat", "ghep-anh*.bat", "ghep_anh*.bat", "ghep*anh*.bat", "ghep-anh*.lnk"],
    # Mo_Tool_Giong_Doc.bat: công cụ ghép ảnh thành video theo frame (KHÔNG phải app giọng đọc)
    "ghep_anh_tool": ["mo_tool_giong_doc*"],
}
# Không thuộc quy trình (người dùng xác nhận): CHAY-MINI-CAPCUT.bat, xuong-timeline
BO_QUA = {
    "chay-mini-capcut*", "xuong-timeline*",
}
TEN_THU_MUC_ANH = ("nghe ne anh", "nghé nè ảnh", "nghe-ne-anh", "nghene anh")


def desktops():
    env = os.environ
    home = Path.home()
    from .winpaths import known_folder
    cands = [known_folder("Desktop"), home / "Desktop", home / "OneDrive" / "Desktop",
             home / "OneDrive" / "Máy tính", home / "OneDrive" / "Màn hình nền", home / "OneDrive" / "Bàn làm việc"]
    for k in ("OneDrive", "OneDriveConsumer", "OneDriveCommercial"):
        if env.get(k):
            cands.append(Path(env[k]) / "Desktop")
    if env.get("PUBLIC"):
        cands.append(Path(env["PUBLIC"]) / "Desktop")
    seen, out = set(), []
    for c in cands:
        if c and c.is_dir() and c.resolve() not in seen:
            seen.add(c.resolve())
            out.append(c)
    return out


def _start_menu():
    env = os.environ
    roots = [Path(env[k]) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
             for k in ("APPDATA", "ProgramData") if env.get(k)]
    return [r for r in roots if r.is_dir()]


def _find(folders, patterns, deep=False):
    """Mẫu đứng trước được ưu tiên (vd lối tắt ElevenLabs trước Mo_Tool_Giong_Doc)."""
    files = []
    for d in folders:
        try:
            files += [f for f in (d.rglob("*") if deep else d.iterdir()) if f.is_file()]
        except OSError:
            continue
    for pat in patterns:
        for f in files:
            if fnmatch.fnmatch(f.name.lower(), pat) and not any(fnmatch.fnmatch(f.name.lower(), b) for b in BO_QUA):
                return f
    return None


def tim_app():
    """Trả dict {khoá config: đường dẫn} cho những gì tìm thấy."""
    dk = desktops()
    found = {}
    for key, pats in TIM.items():
        f = _find(dk, pats) or (_find(_start_menu(), pats, deep=True) if not key.startswith("ghep") else None)
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
    anh = _tim_thu_muc_anh(dk)
    if anh:
        found["thu_muc_anh_tai_ve"] = str(anh)
    return found


def _tim_thu_muc_anh(dk):
    """Thư mục ảnh của extension Nghé nè ("nghe ne anh"), tìm sâu 2 cấp ở các chỗ hay dùng."""
    from .winpaths import known_folder
    home = Path.home()
    roots = dk + [known_folder("Downloads"), known_folder("Pictures"), known_folder("Documents"),
                  home, home / "Downloads", home / "OneDrive", home / "Pictures"]
    seen = set()
    for r in roots:
        if not r or not r.is_dir() or r.resolve() in seen:
            continue
        seen.add(r.resolve())
        try:
            for a in r.iterdir():
                if not a.is_dir() or a.name.startswith("."):
                    continue
                if a.name.lower() in TEN_THU_MUC_ANH:
                    return a
                try:
                    for b in a.iterdir():
                        if b.is_dir() and b.name.lower() in TEN_THU_MUC_ANH:
                            return b
                except OSError:
                    continue
        except OSError:
            continue
    return None


def ap_dung(project, log=print):
    """Điền những đường dẫn tìm được vào config.json (không ghi đè ô người dùng đã tự điền)."""
    found = tim_app()
    ten = {"voice_app": "App giọng đọc (ElevenLabs)", "capcut": "CapCut",
           "ghep_anh_bat": "GHEP-ANH-TIMELINE.bat", "ghep_anh_tool": "Mo_Tool_Giong_Doc (ghép ảnh theo frame)",
           "thu_muc_voice": "Thư mục Voice",
           "thu_muc_anh_tai_ve": "Thư mục ảnh Nghé nè"}
    o_goc = ("thu_muc_voice", "thu_muc_anh_tai_ve")       # khoá nằm ở gốc config, không trong apps
    changed = False
    for key, label in ten.items():
        cur = project.cfg.get(key) if key in o_goc else project.cfg["apps"].get(key)
        val = found.get(key)
        if cur:
            log(f"  {label}: {cur} (đã có trong config)")
        elif val:
            if key in o_goc:
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
