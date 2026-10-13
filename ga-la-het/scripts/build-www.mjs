// Bọc src/index.html (bản dùng cho artifact, không có khung HTML) thành trang đầy đủ cho app.
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
const page = readFileSync(new URL('../src/index.html', import.meta.url), 'utf8');
const html = `<!doctype html><html lang="vi"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover,user-scalable=no">
<style>:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px);box-sizing:border-box;height:100%}</style>
</head><body>
${page}
</body></html>
`;
mkdirSync(new URL('../www/', import.meta.url), { recursive: true });
writeFileSync(new URL('../www/index.html', import.meta.url), html);
console.log('www/index.html ready');
