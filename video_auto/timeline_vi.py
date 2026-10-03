"""Bản Python của scripts/align.js + build-timeline.js (skill ghep-anh-giong-doc).

Giữ nguyên từng quy tắc của bản gốc để timeline.txt ra giống hệt khi chạy skill
trên Claude AI, nhưng chạy offline, không cần Node. tests/test_timeline_vi.py
so sánh kết quả với bản JS gốc.
"""
import math
import re
from bisect import bisect_left
from pathlib import Path

KEEP = set('0123456789aàáảãạăằắẳẵặâầấẩẫậbcdđeèéẻẽẹêềếểễệfghiìíỉĩịjklmnoòóỏõọôồốổỗộơờớởỡợ'
           'pqrstuùúủũụưừứửữựvwxyỳýỷỹỵz')


def jsround(x):
    """Math.round của JavaScript (làm tròn .5 lên), khác round() của Python."""
    return math.floor(x + 0.5)


def nz(w):
    return ''.join(c for c in w.lower() if c in KEEP)


def doc_srt(txt):
    out = []
    for kh in re.split(r'\n\s*\n', txt.replace('\r', '')):
        d = kh.split('\n')
        i = next((k for k, x in enumerate(d) if '-->' in x), -1)
        if i < 0:
            continue
        p = []
        for x in d[i].split('-->'):
            m = re.search(r'(\d+):(\d+):(\d+)[,.](\d+)', x.strip())
            p.append(int(m[1]) * 3600 + int(m[2]) * 60 + int(m[3]) + int(m[4]) / 1000 if m else None)
        if len(p) < 2 or p[0] is None or p[1] is None:
            continue
        ws = [w for w in ' '.join(d[i + 1:]).strip().split() if w]
        for k, w in enumerate(ws):
            out.append((nz(w), p[0] + (p[1] - p[0]) * k / len(ws)))
    return [x for x in out if x[0]]


def _nwords(s):
    return len(s.split(' '))


def cau_co_ban(t):
    s = [x.strip() for x in re.findall(r'[^.?!]+[.?!]?', re.sub(r'\s+', ' ', t))]
    s = [x for x in s if x]
    m = []
    for x in s:
        if m and _nwords(x) < 6 and _nwords(m[-1]) < 14:
            m[-1] += ' ' + x
        else:
            m.append(x)
    return m


def _tach_doi(s):
    w = s.split(' ')
    b = None
    for i, x in enumerate(w):
        if re.search(r'[,:;]$', x) and 2 < i < len(w) - 2:
            if b is None or abs(i - len(w) / 2) < abs(b - len(w) / 2):
                b = i
    if b is None:
        b = math.floor(len(w) / 2) - 1
    if b < 0:
        b = 0
    return ' '.join(w[:b + 1]), ' '.join(w[b + 1:])


def ep_so_canh(sents, n):
    s = list(sents)
    guard = 0
    while len(s) < n and guard < 20000:
        guard += 1
        i = 0
        for k in range(1, len(s)):
            if _nwords(s[k]) > _nwords(s[i]):
                i = k
        if _nwords(s[i]) < 4:
            break
        s[i:i + 1] = list(_tach_doi(s[i]))
    guard = 0
    while len(s) > n and guard < 20000:
        guard += 1
        i, best = 0, 1e9
        for k in range(len(s) - 1):
            v = _nwords(s[k]) + _nwords(s[k + 1])
            if v < best:
                best, i = v, k
        s[i:i + 2] = [s[i] + ' ' + s[i + 1]]
    return s


def _neo(kw, sw):
    pos = {}
    for j, w in enumerate(sw):
        pos.setdefault(w, []).append(j)
    cand = []
    for i, w in enumerate(kw):
        ls = pos.get(w)
        if not ls or len(ls) > 12:
            continue
        for j in reversed(ls):
            cand.append((i, j))
    tail, idx, par = [], [], [0] * len(cand)
    for c, (_, j) in enumerate(cand):
        lo = bisect_left(tail, j)
        if lo == len(tail):
            tail.append(j)
            idx.append(c)
        else:
            tail[lo] = j
            idx[lo] = c
        par[c] = idx[lo - 1] if lo > 0 else -1
    mp = {}
    c = idx[len(tail) - 1] if tail else -1
    while c >= 0:
        mp[cand[c][0]] = cand[c][1]
        c = par[c]
    return mp


def _canh_tho(kich_ban, srt_text, n):
    w = doc_srt(srt_text)
    if not w:
        raise ValueError('SRT rỗng hoặc sai định dạng')
    sw = [x[0] for x in w]
    sc = cau_co_ban(kich_ban)
    if n > 0:
        sc = ep_so_canh(sc, n)
    kw, owner = [], []
    for i, c in enumerate(sc):
        for x in c.split(' '):
            v = nz(x)
            if v:
                kw.append(v)
                owner.append(i)
    mp = _neo(kw, sw)
    first = {}
    for i, o in enumerate(owner):
        if i in mp and o not in first:
            first[o] = w[mp[i]][1]
    cong = [0]
    for c in sc:
        cong.append(cong[-1] + _nwords(c))
    endw = w[-1][1] + 0.6
    st = []
    for i in range(len(sc)):
        if i in first:
            st.append(first[i])
            continue
        a = i - 1
        while a >= 0 and a not in first:
            a -= 1
        b = i + 1
        while b < len(sc) and b not in first:
            b += 1
        ta = first[a] if a >= 0 else 0
        tb = first[b] if b < len(sc) else endw
        wa = cong[a] if a >= 0 else 0
        wb = cong[b] if b < len(sc) else cong[len(sc)]
        r = (cong[i] - wa) / (wb - wa) if wb - wa > 0 else 0.5
        st.append(ta + (tb - ta) * r)
    prev = 0
    for i in range(len(st)):
        if st[i] < prev:
            st[i] = prev
        prev = st[i]
    return sc, st, w, len(sc) - len(first)


def _don_ngan(fr, minf, he_so):
    """Ảnh ngắn hơn minf thì mượn frame của ảnh kế bên (như epToiThieu trong align.js)."""
    for i in range(len(fr)):
        if fr[i] >= minf:
            continue
        need = minf - fr[i]
        for k in (i + 1, i - 1):
            if need <= 0 or k < 0 or k >= len(fr):
                continue
            spare = fr[k] - jsround(minf * he_so)
            take = min(need, max(spare, 0))
            if take > 0:
                fr[k] -= take
                fr[i] += take
                need -= take
        if need > 0:
            fr[i] += need
    return fr


def _frames_cau(st, w, fps, extra):
    end = w[-1][1] + 0.6
    fr = [jsround(v * fps) for v in st]
    for i in range(1, len(fr)):
        if fr[i] <= fr[i - 1]:
            fr[i] = fr[i - 1] + 1
    ef = max(jsround(end * fps), fr[-1] + extra)
    return [(fr[i + 1] if i + 1 < len(fr) else ef) - v for i, v in enumerate(fr)]


def tinh_canh(kich_ban, srt_text, n, fps=30, min_giay=1.0):
    sc, st, w, thieu = _canh_tho(kich_ban, srt_text, n)
    minf = max(1, jsround(min_giay * fps))
    ds = _don_ngan(_frames_cau(st, w, fps, minf), minf, 1.3)
    return [{'t': t, 'f': f} for t, f in zip(sc, ds)], thieu


def tinh_canh_theo_ban_do(kich_ban, srt_text, vai_anh, fps=30, min_giay=1.0):
    sc, st, w, _ = _canh_tho(kich_ban, srt_text, 0)
    if len(sc) != len(vai_anh):
        raise ValueError(f'Bản đồ có {len(vai_anh)} dòng nhưng kịch bản cắt ra {len(sc)} câu. '
                         'Chạy "liệt kê câu" để xem lại danh sách câu rồi sửa bản đồ.')
    dur = _frames_cau(st, w, fps, 1)
    minf = max(1, jsround(min_giay * fps))
    out = []
    for i, t in enumerate(sc):
        k = max(1, int(vai_anh[i]))
        base, du = divmod(dur[i], k)
        for j in range(k):
            out.append({'f': base + (1 if j < du else 0), 't': t, 'cau': i + 1, 'phan': j + 1, 'tong': k})
    fr = _don_ngan([o['f'] for o in out], minf, 1.2)
    for o, f in zip(out, fr):
        o['f'] = f
    return out


def _tc(fr, fps):
    f, s0 = fr % fps, fr // fps
    return f'{s0 // 3600:02d}:{s0 // 60 % 60:02d}:{s0 % 60:02d}:{f:02d}'


def build(kich_ban_path, srt_path, out_dir, so_anh=0, ban_do_path=None, fps=30, min_giay=1.0):
    """Giống: node build-timeline.js kichban srt [--so-anh N | --ban-do FILE] --out DIR"""
    kb = Path(kich_ban_path).read_text(encoding='utf-8-sig')
    srt = Path(srt_path).read_text(encoding='utf-8-sig')
    thieu = 0
    if ban_do_path:
        vai = [int(float(x)) for x in Path(ban_do_path).read_text(encoding='utf-8').split()]
        rows = tinh_canh_theo_ban_do(kb, srt, vai, fps, min_giay)
    else:
        canh, thieu = tinh_canh(kb, srt, so_anh, fps, min_giay)
        rows = canh
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / 'timeline.txt').write_text('\n'.join(str(r['f']) for r in rows) + '\n', encoding='utf-8')
    has_map = bool(ban_do_path)
    md = [f'# TIMELINE — {len(rows)} ảnh, khớp theo {Path(srt_path).name}', '',
          '| Ảnh | Bắt đầu | Kết thúc | Giữ | Frame |' + (' Câu |' if has_map else '') + ' Lời đọc |',
          '|---|---|---|---|---|' + ('---|' if has_map else '') + '---|']
    moc = 0
    for i, r in enumerate(rows, 1):
        giu = f"{r['f'] // fps:02d}:{r['f'] % fps:02d}"
        cols = [i, _tc(moc, fps), _tc(moc + r['f'], fps), giu, r['f']]
        if has_map:
            cols.append(f"{r['cau']} ({r['phan']}/{r['tong']})")
        cols.append(r['t'].replace('|', '/'))
        md.append('| ' + ' | '.join(map(str, cols)) + ' |')
        moc += r['f']
    (out / 'timeline-bang.md').write_text('\n'.join(md), encoding='utf-8')
    return len(rows), moc, thieu


def liet_ke(kich_ban_path):
    return cau_co_ban(Path(kich_ban_path).read_text(encoding='utf-8-sig'))
