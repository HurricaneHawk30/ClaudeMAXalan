// Обложка Forbidden Earth 1280×720: кадр + большой текст + янтарная строка снизу.
// node make_thumbnail.js --image path.jpg --title "THIS IS EARTH" --accent "10 PLACES THAT LOOK ALIEN" --out thumbnail.jpg [--pos "50% 45%"] [--size 168]
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const args = {};
for (let i = 2; i < process.argv.length; i += 2) args[process.argv[i].replace(/^--/, '')] = process.argv[i + 1];
for (const k of ['image', 'title', 'accent', 'out']) if (!args[k]) { console.error('нужен --' + k); process.exit(1); }
const pos = args.pos || '50% 50%';
const size = parseInt(args.size || '168', 10);
const esc = s => s.replace(/&/g, '&amp;').replace(/</g, '&lt;');
const fonts = path.join(__dirname, 'fonts');
const img = 'data:image/jpeg;base64,' + fs.readFileSync(args.image).toString('base64');

const html = `<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{font-family:Oswald;font-weight:600;src:url(file://${fonts}/oswald-latin-600-normal.woff2)}
@font-face{font-family:Oswald;font-weight:700;src:url(file://${fonts}/oswald-latin-700-normal.woff2)}
body{margin:0}</style></head><body>
<div style="position:relative;width:1280px;height:720px;overflow:hidden;background:#0E1116;font-family:Oswald,Impact,sans-serif">
<img src="${img}" style="position:absolute;left:0;top:0;width:1280px;height:720px;object-fit:cover;object-position:${pos};filter:saturate(1.1) contrast(1.05)">
<div style="position:absolute;inset:0;background:linear-gradient(0deg,rgba(14,17,22,.9) 0%,rgba(14,17,22,.5) 32%,rgba(14,17,22,0) 56%)"></div>
<div style="position:absolute;left:0;right:0;bottom:40px;display:flex;flex-direction:column;align-items:center;gap:4px">
<div style="font-weight:700;font-size:${size}px;line-height:${size}px;letter-spacing:.01em;color:#ECE6DA;text-shadow:0 6px 24px rgba(0,0,0,.6);white-space:nowrap">${esc(args.title)}</div>
<div style="font-weight:600;font-size:50px;line-height:56px;letter-spacing:.14em;color:#F2A93B;white-space:nowrap">${esc(args.accent)}</div>
</div></div></body></html>`;

(async () => {
  const tmp = path.join(require('os').tmpdir(), 'fe_thumb_' + process.pid + '.html');
  fs.writeFileSync(tmp, html);
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 1 });
  await p.goto('file://' + tmp);
  await p.waitForTimeout(500);
  const w = await p.evaluate(() => Math.max(...[...document.querySelectorAll('div[style*="nowrap"]')].map(d => d.scrollWidth)));
  if (w > 1200) console.warn('ВНИМАНИЕ: текст шире кадра (' + w + ' px) — сократи или задай --size меньше');
  await p.screenshot({ path: args.out, type: 'jpeg', quality: 92 });
  await b.close();
  fs.unlinkSync(tmp);
  console.log('готово: ' + args.out);
})();
