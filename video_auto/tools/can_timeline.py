#!/usr/bin/env python3
"""Căn 384 (hay N) ảnh-theo-ý vào giọng đọc thật bằng file SRT tiếng Nhật.

Dùng:  python3 can_timeline.py units.json giongdoc.srt --out THU_MUC [--fps 30]

Giọng đọc được thu từ kịch bản GỐC (mỗi câu một dòng, đọc liền mạch).
Script ghép toàn bộ chữ trong SRT, gán thời gian cho từng ký tự (nội suy trong mỗi
khối phụ đề), dò khớp với kịch bản theo từng ký tự (bỏ dấu câu, khoảng trắng),
rồi lấy thời điểm bắt đầu của từng ý làm điểm đổi ảnh.
Ra:
- timeline.txt      dòng N = số frame ảnh N được giữ (dùng cho GHEP-ANH-TIMELINE.bat)
- timeline-bang.md  bảng ảnh | bắt đầu | độ dài | lời đọc, để kiểm tra
"""
import json, re, sys, os, difflib

def ts(s):
    h, m, rest = s.strip().replace('.', ',').split(':')
    sec, ms = rest.split(',')
    return int(h) * 3600 + int(m) * 60 + int(sec) + int(ms) / 1000

KEEP = re.compile(r'[^\s、。，,．.！？!?「」『』（）()・…ー―\-"\'“”]')
def norm(s):
    return ''.join(KEEP.findall(s))

def doc_srt(path):
    txt = open(path, encoding='utf-8-sig').read().replace('\r', '')
    chars, times, end = [], [], 0.0
    for blk in re.split(r'\n\s*\n', txt):
        lines = blk.strip().split('\n')
        i = next((k for k, l in enumerate(lines) if '-->' in l), None)
        if i is None: continue
        a, b = [ts(x) for x in lines[i].split('-->')]
        t = norm(''.join(lines[i + 1:]))
        for k, ch in enumerate(t):
            chars.append(ch); times.append(a + (b - a) * k / max(len(t), 1))
        end = max(end, b)
    return ''.join(chars), times, end

def main():
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(1)
    out = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else '.'
    fps = int(sys.argv[sys.argv.index('--fps') + 1]) if '--fps' in sys.argv else 30
    units = json.load(open(sys.argv[1], encoding='utf-8'))
    srt, times, end = doc_srt(sys.argv[2])
    script, starts = '', []
    for _, m in units:
        starts.append(len(script)); script += norm(m)
    sm = difflib.SequenceMatcher(None, script, srt, autojunk=False)
    mp = {}
    for a, b, n in sm.get_matching_blocks():
        for k in range(n): mp[a + k] = b + k
    ty_le = sum(n for _, _, n in sm.get_matching_blocks()) / max(len(script), 1)
    keys = sorted(mp)
    import bisect
    def tg(pos):
        j = bisect.bisect_left(keys, pos)
        if j < len(keys) and keys[j] - pos < 40:
            return times[mp[keys[j]]] - (keys[j] - pos) * 0.12
        if j > 0: return times[mp[keys[j - 1]]] + (pos - keys[j - 1]) * 0.12
        return 0.0
    st = [0.0] + [tg(p) for p in starts[1:]]
    for i in range(1, len(st)):
        st[i] = max(st[i], st[i - 1] + 0.3)
    st.append(max(end, st[-1] + 0.5))
    fr = [round(x * fps) for x in st]
    dur = [fr[i + 1] - fr[i] for i in range(len(units))]
    os.makedirs(out, exist_ok=True)
    open(os.path.join(out, 'timeline.txt'), 'w').write('\n'.join(map(str, dur)) + '\n')
    rows = [f'| {i+1} | {st[i]:.2f}s | {dur[i]/fps:.2f}s | {units[i][1]} |' for i in range(len(units))]
    open(os.path.join(out, 'timeline-bang.md'), 'w', encoding='utf-8').write(
        f'# Timeline ({fps}fps) — khớp {ty_le:.0%} ký tự với SRT\n\n| Ảnh | Bắt đầu | Độ dài | Lời đọc |\n|---|---|---|---|\n' + '\n'.join(rows) + '\n')
    print(f'Xong: {len(units)} ảnh, tổng {sum(dur)/fps:.1f}s, khớp {ty_le:.0%} ký tự.')
    if ty_le < 0.85:
        print('CẢNH BÁO: SRT khác kịch bản nhiều (có thể do phụ đề tự động viết kanji/kana khác). Kiểm tra timeline-bang.md.', file=sys.stderr)

if __name__ == '__main__':
    main()
