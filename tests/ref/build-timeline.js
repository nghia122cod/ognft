#!/usr/bin/env node
/*
Dùng:
  node build-timeline.js <kichban.txt> <phude.srt> [tuy-chon]

Tuỳ chọn:
  --so-anh N        Ép đúng N ảnh, chia đều theo quy tắc gộp/tách câu (không có bản đồ)
  --ban-do FILE      File text, mỗi dòng một số nguyên = số ảnh của câu đó, theo
                     đúng thứ tự câu do cauCoBan() cắt ra (chạy không có --so-anh
                     và --ban-do trước để xem danh sách câu gốc rồi đối chiếu
                     với storyboard, xem README trong SKILL.md)
  --fps N            Mặc định 30
  --toi-thieu S       Giây tối thiểu mỗi ảnh, mặc định 1.0
  --lietke            Chỉ in danh sách câu gốc kèm số thứ tự, không tính timeline
                     (dùng để dựng --ban-do bằng tay)

Ra: in timeline.txt ra <outdir>/timeline.txt và bảng đối chiếu ra <outdir>/timeline-bang.md
  --out DIR          Thư mục ghi ra, mặc định thư mục hiện tại
*/
const fs = require('fs');
const path = require('path');
const { docSRT, cauCoBan, tinhCanh, tinhCanhTheoBanDo } = require('./align.js');

function arg(name, def) {
  const i = process.argv.indexOf(name);
  return i >= 0 ? process.argv[i + 1] : def;
}
function flag(name) { return process.argv.includes(name); }

const kbPath = process.argv[2];
const srtPath = process.argv[3];
if (!kbPath || !srtPath) {
  console.error('Thiếu tham số. Dùng: node build-timeline.js kichban.txt phude.srt [--so-anh N | --ban-do map.txt] [--fps 30] [--toi-thieu 1.0] [--out DIR]');
  process.exit(1);
}
const kichBan = fs.readFileSync(kbPath, 'utf8');
const srt = fs.readFileSync(srtPath, 'utf8');
const fps = parseInt(arg('--fps', '30'), 10);
const toiThieu = parseFloat(arg('--toi-thieu', '1.0'));
const outDir = arg('--out', '.');

if (flag('--lietke')) {
  const s = cauCoBan(kichBan.replace(/\s+/g, ' '));
  s.forEach((t, i) => console.log((i + 1) + '\t' + t));
  console.error('\nTổng ' + s.length + ' câu. Dùng số thứ tự này khi viết file --ban-do.');
  process.exit(0);
}

function tc(fr) {
  const f = fr % fps, s0 = Math.floor(fr / fps), s = s0 % 60, m = Math.floor(s0 / 60) % 60, h = Math.floor(s0 / 3600);
  const z = n => String(n).padStart(2, '0');
  return z(h) + ':' + z(m) + ':' + z(s) + ':' + z(f);
}
const giu = fr => String(Math.floor(fr / fps)).padStart(2, '0') + ':' + String(fr % fps).padStart(2, '0');

let frames, rows; // rows: [{f,t,cau?,phan?,tong?}]

const banDoPath = arg('--ban-do', null);
if (banDoPath) {
  const vaiAnh = fs.readFileSync(banDoPath, 'utf8').trim().split(/\s+/).map(Number);
  rows = tinhCanhTheoBanDo(kichBan, srt, vaiAnh, fps, toiThieu);
} else {
  const N = parseInt(arg('--so-anh', '0'), 10);
  const r = tinhCanh(kichBan, srt, N, fps, toiThieu);
  if (r.thieu > 0) console.error('Cảnh báo: ' + r.thieu + ' cảnh không neo được trực tiếp vào SRT, đã nội suy.');
  rows = r.canh.map(c => ({ f: c.f, t: c.t }));
}
frames = rows.map(r => r.f);

fs.mkdirSync(outDir, { recursive: true });
fs.writeFileSync(path.join(outDir, 'timeline.txt'), frames.join('\n') + '\n');

let moc = 0;
const hasMap = !!banDoPath;
const head = hasMap
  ? '| Ảnh | Bắt đầu | Kết thúc | Giữ | Frame | Câu | Lời đọc |\n|---|---|---|---|---|---|---|'
  : '| Ảnh | Bắt đầu | Kết thúc | Giữ | Frame | Lời đọc |\n|---|---|---|---|---|---|';
const md = ['# TIMELINE — ' + rows.length + ' ảnh, khớp theo ' + path.basename(srtPath), '', head];
rows.forEach((r, i) => {
  const cols = hasMap
    ? [i + 1, tc(moc), tc(moc + r.f), giu(r.f), r.f, r.cau + ' (' + r.phan + '/' + r.tong + ')', r.t.replace(/\|/g, '/')]
    : [i + 1, tc(moc), tc(moc + r.f), giu(r.f), r.f, r.t.replace(/\|/g, '/')];
  md.push('| ' + cols.join(' | ') + ' |');
  moc += r.f;
});
fs.writeFileSync(path.join(outDir, 'timeline-bang.md'), md.join('\n'));

const tong = frames.reduce((a, b) => a + b, 0);
console.error('Xong. ' + rows.length + ' ảnh, tổng ' + tc(tong) + '. Ghi vào ' + outDir + '/timeline.txt và timeline-bang.md');
