// Layout check: every text element must sit inside the trim with a safe margin,
// and no two text elements may overlap.  node check.mjs <dir>
import { spawn } from 'node:child_process';
import { mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const dir = process.argv[2];
const SAFE = 12; // mm from the trim edge
const edge = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', ['--headless=new', '--remote-debugging-port=9351',
  `--user-data-dir=${mkdtempSync(join(tmpdir(), 'edge-'))}`, '--no-first-run', 'about:blank'], { stdio: 'ignore' });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let t; for (let i = 0; i < 40; i++) { try { t = await (await fetch('http://127.0.0.1:9351/json')).json(); break; } catch { await sleep(250); } }
const ws = new WebSocket(t.find((x) => x.type === 'page').webSocketDebuggerUrl); await new Promise((r) => (ws.onopen = r));
let id = 0; const pend = new Map(); ws.onmessage = (e) => { const m = JSON.parse(e.data); if (m.id) pend.get(m.id)?.(m.result ?? m.error); };
const send = (method, params = {}) => new Promise((r) => { pend.set(++id, r); ws.send(JSON.stringify({ id, method, params })); });
await send('Page.enable'); await send('Runtime.enable');
await send('Page.navigate', { url: 'file:///' + join(dir, '_render.html').replace(/\\/g, '/') });
await sleep(2500);
const r = await send('Runtime.evaluate', { returnByValue: true, expression: `(() => {
  const svg = document.querySelector('svg'); const out = { boxes: [], issues: [] };
  const texts = [...svg.querySelectorAll('text')].filter(t => !t.closest('#car-999'));
  for (const t of texts) { const b = t.getBBox(); out.boxes.push({ s: t.textContent, x: b.x, y: b.y, w: b.width, h: b.height }); }
  for (const sel of ['#car-999', '#qr-application-form', '#logo-mark']) { const el = svg.querySelector(sel); if (!el) continue; const r = el.getBoundingClientRect(), sv = svg.getBoundingClientRect(), k = 426 / sv.width; out.boxes.push({ s: sel, x: (r.left - sv.left) * k - 3, y: (r.top - sv.top) * k - 3, w: r.width * k, h: r.height * k }); }
  for (const b of out.boxes) {
    if (b.x < ${SAFE} || b.y < ${SAFE} || b.x + b.w > 420 - ${SAFE} || b.y + b.h > 594 - ${SAFE}) out.issues.push('near edge: ' + b.s + ' ' + JSON.stringify([+b.x.toFixed(1), +b.y.toFixed(1), +(b.x+b.w).toFixed(1), +(b.y+b.h).toFixed(1)]));
  }
  const pad = 0.4;
  for (let i = 0; i < out.boxes.length; i++) for (let j = i + 1; j < out.boxes.length; j++) {
    const a = out.boxes[i], b = out.boxes[j];
    if (a.x < b.x + b.w + pad && b.x < a.x + a.w + pad && a.y < b.y + b.h - pad && b.y < a.y + a.h - pad) out.issues.push('overlap: "' + a.s + '" / "' + b.s + '"');
  }
  const els = { qr: '#qr-application-form', car: '#car-999', logo: '#logo-mark' };
  out.objects = Object.fromEntries(Object.entries(els).map(([k, s]) => { const b = svg.querySelector(s).getBBox(); const m = svg.querySelector(s).getCTM(); return [k, [b.x, b.y, b.width, b.height].map(v => +v.toFixed(1))]; }));
  out.fontsReady = [...document.fonts].map(f => f.family + ':' + f.status);
  return out; })()` });
const v = r.result.value;
console.log('text elements:', v.boxes.length, '| fonts:', v.fontsReady.join(', '));
console.log(v.issues.length ? v.issues.join('\n') : 'no overlaps, all text inside the safe area');
ws.close(); edge.kill(); process.exit(0);
