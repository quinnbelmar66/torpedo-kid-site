// Renders the poster SVG to a print PDF (A2 + 3 mm bleed) and a PNG preview
// using headless Edge.  node render.mjs <dir>
import { spawn } from 'node:child_process';
import { readFileSync, writeFileSync, mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const dir = process.argv[2];
const svg = readFileSync(join(dir, 'torpedo-kid-poster-A2.svg'), 'utf8').replace(/^<\?xml[^>]*>\s*/, '');
const page = `<!doctype html><html><head><meta charset="utf-8"><style>
@page { size: 426mm 600mm; margin: 0 } html, body { margin: 0; padding: 0; background: #fff }
svg { display: block; width: 426mm; height: 600mm }</style></head><body>${svg}</body></html>`;
const htmlPath = join(dir, '_render.html');
writeFileSync(htmlPath, page);

const edge = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', ['--headless=new', '--remote-debugging-port=9350',
  `--user-data-dir=${mkdtempSync(join(tmpdir(), 'edge-'))}`, '--no-first-run', '--hide-scrollbars', 'about:blank'], { stdio: 'ignore' });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let t; for (let i = 0; i < 40; i++) { try { t = await (await fetch('http://127.0.0.1:9350/json')).json(); break; } catch { await sleep(250); } }
const ws = new WebSocket(t.find((x) => x.type === 'page').webSocketDebuggerUrl); await new Promise((r) => (ws.onopen = r));
let id = 0; const pend = new Map(); ws.onmessage = (e) => { const m = JSON.parse(e.data); if (m.id) pend.get(m.id)?.(m.result ?? m.error); };
const send = (method, params = {}) => new Promise((r) => { pend.set(++id, r); ws.send(JSON.stringify({ id, method, params })); });
await send('Page.enable');
// 426 mm at 96 css px per inch
const pxW = Math.round((426 / 25.4) * 96), pxH = Math.round((600 / 25.4) * 96);
await send('Emulation.setDeviceMetricsOverride', { width: pxW, height: pxH, deviceScaleFactor: Number(process.argv[3] || 1), mobile: false });
await send('Page.navigate', { url: 'file:///' + htmlPath.replace(/\\/g, '/') });
await sleep(2500);
const pdf = await send('Page.printToPDF', { preferCSSPageSize: true, printBackground: true, marginTop: 0, marginBottom: 0, marginLeft: 0, marginRight: 0 });
writeFileSync(join(dir, 'torpedo-kid-poster-A2-print.pdf'), Buffer.from(pdf.data, 'base64'));
const png = await send('Page.captureScreenshot', { format: 'png', clip: { x: 0, y: 0, width: pxW, height: pxH, scale: 1 } });
writeFileSync(join(dir, 'torpedo-kid-poster-A2-preview.png'), Buffer.from(png.data, 'base64'));
console.log('rendered', pxW, 'x', pxH, 'css px at scale', process.argv[3] || 1);
ws.close(); edge.kill(); process.exit(0);
