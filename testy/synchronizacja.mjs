// Test synchronizacji dźwięku i animacji odtwarzacza ▶ (wymaga Node 22+ i Edge albo Chrome).
//
//   node testy/synchronizacja.mjs [strony/04-mrugaj-gwiazdko.html]
//
// Każdy scenariusz uruchamia osobną przeglądarkę w tle (headless) i podmienia w niej AudioContext:
// udawany (z opóźnionym startem dźwięku, opóźnieniem głośnika albo wolnym tworzeniem nut) albo
// prawdziwy, tylko podglądany. Test mierzy, o ile podświetlenie klocka jest przesunięte względem
// chwili, w której nutę SŁYCHAĆ (>0 = animacja spóźniona, <0 = animacja wyprzedza dźwięk).
import { spawn } from 'node:child_process';
import { existsSync, mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

// Dopuszczalne przesunięcie: typowo ≤ 1 klatka; pierwsza nuta po serii szybkich kliknięć bywa
// 1–4 klatki później (przeglądarka w tle). Pierwotny błąd dawał 300–600 ms przez cały utwór.
const MEDIAN_MS = 20, WORST_MS = 80;
const PAGE = pathToFileURL(resolve(process.argv[2] || 'strony/04-mrugaj-gwiazdko.html')).href;
const BROWSER = [
  process.env.KOLOROWE_PIANINO_BROWSER,
  'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
  'C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe',
  'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  '/usr/bin/google-chrome', '/usr/bin/chromium',
].find(p => p && existsSync(p));
const sleep = ms => new Promise(r => setTimeout(r, ms));

function inject({ fake, delay = 0, latency = 0, nodeMs = 0 }) {
  return `(() => {
    window.__tones = []; window.__fresh = true;
    const busy = () => { const t = performance.now() + ${nodeMs}; while (performance.now() < t) {} };
    if (${fake}) {
      function P(v){ this.value = v; }
      P.prototype.setValueAtTime = P.prototype.exponentialRampToValueAtTime =
        P.prototype.setTargetAtTime = P.prototype.cancelScheduledValues = function(){};
      function N(){} N.prototype.connect = function(){}; N.prototype.disconnect = function(){};
      function Ctx(){ this._born = performance.now(); this.state = 'running'; this.destination = new N();
        this.outputLatency = ${latency}; window.__ctx = this; }
      Object.defineProperty(Ctx.prototype, 'currentTime', { get(){
        return Math.max(0, (performance.now() - this._born) / 1000 - ${delay}); } });
      Ctx.prototype.getOutputTimestamp = function(){
        return { contextTime: Math.max(0, this.currentTime - ${latency}), performanceTime: performance.now() }; };
      Ctx.prototype.resume = function(){ return Promise.resolve(); };
      Ctx.prototype.createGain = function(){ busy(); const n = new N(); n.gain = new P(1); return n; };
      Ctx.prototype.createDynamicsCompressor = function(){ return new N(); };
      Ctx.prototype.createOscillator = function(){ busy(); const n = new N(); n.frequency = new P(0);
        n.start = t => window.__tones.push(t); n.stop = () => {}; return n; };
      window.AudioContext = window.webkitAudioContext = Ctx;
    } else {
      const Native = window.AudioContext;
      window.AudioContext = window.webkitAudioContext = class extends Native {
        constructor(...a){ super(...a); window.__ctx = this; }
        createOscillator(){ const o = super.createOscillator(); const st = o.start.bind(o);
          o.start = t => { window.__tones.push(t); st(t); }; return o; }
      };
    }
    window.__heard = () => {  // czas zegara audio, który słychać w tej chwili
      const c = window.__ctx; if (!c) return NaN;
      const ts = c.getOutputTimestamp ? c.getOutputTimestamp() : null;
      if (ts && ts.contextTime > 0) return ts.contextTime + (performance.now() - ts.performanceTime) / 1000;
      return c.currentTime - (c.outputLatency || 0);
    };
  })();`;
}

const MEASURE = (clicks, listen) => `(async () => {
  const page = document.querySelector('.melody');
  const data = JSON.parse(page.getAttribute('data-play'));
  const marks = [];
  new MutationObserver(ms => { for (const m of ms) { const el = m.target;
    if (el.classList.contains('blk') && el.classList.contains('on'))
      marks.push([window.__heard(), +el.getAttribute('data-n')]); } })
    .observe(page, { subtree: true, attributes: true, attributeFilter: ['class'] });
  const btn = page.querySelector('.play');
  let from = 0;  // liczymy tylko nuty z ostatniego uruchomienia (wcześniejsze zostały zatrzymane i wyciszone)
  for (const gap of ${JSON.stringify(clicks)}) {
    from = window.__tones.length; marks.length = 0;
    btn.click(); await new Promise(r => setTimeout(r, gap));
  }
  await new Promise(r => setTimeout(r, ${listen}));
  btn.click();
  const starts = window.__tones.slice(from).filter((_, i) => i % 3 === 0);
  const notes = data.seq.filter(e => e[0] !== null);
  const offs = []; let k = 0;
  for (const [heard, n] of marks) {
    while (k < notes.length && notes[k][2] !== n) k++;
    if (k >= notes.length || k >= starts.length) break;
    offs.push(Math.round((heard - starts[k]) * 1000)); k++;
  }
  return offs;
})()`;

async function scenario(opts, clicks = [0], listen = 4000) {
  const port = 9300 + Math.floor(Math.random() * 600);
  const profile = mkdtempSync(join(tmpdir(), 'kp-test-'));
  const proc = spawn(BROWSER, ['--headless=new', `--remote-debugging-port=${port}`, `--user-data-dir=${profile}`,
    '--autoplay-policy=no-user-gesture-required', '--window-size=1600,900', 'about:blank'], { stdio: 'ignore' });
  try {
    let list;
    for (let n = 0; n < 80 && !list; n++) {
      try { list = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json(); } catch { await sleep(250); }
    }
    const ws = new WebSocket(list.find(t => t.type === 'page').webSocketDebuggerUrl);
    await new Promise(r => ws.onopen = r);
    let seq = 0; const pending = new Map();
    ws.onmessage = e => { const m = JSON.parse(e.data); if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); } };
    const send = (method, params = {}) => new Promise(r => { const id = ++seq; pending.set(id, r); ws.send(JSON.stringify({ id, method, params })); });
    await send('Page.enable'); await send('Runtime.enable');
    await send('Page.addScriptToEvaluateOnNewDocument', { source: inject(opts) });
    await send('Page.navigate', { url: PAGE });
    for (let n = 0; n < 100; n++) {
      const r = await send('Runtime.evaluate', { expression: 'window.__fresh === true && document.readyState', returnByValue: true });
      if (r.result?.result?.value === 'complete') break;
      await sleep(50);
    }
    const r = await send('Runtime.evaluate', { expression: MEASURE(clicks, listen), awaitPromise: true, returnByValue: true });
    ws.close();
    return r.result?.result?.value || [];
  } finally {
    proc.kill();
    await sleep(300);
    try { rmSync(profile, { recursive: true, force: true }); } catch {}
  }
}

if (!BROWSER) { console.error('Nie znaleziono Edge/Chrome – ustaw KOLOROWE_PIANINO_BROWSER'); process.exit(2); }
const cases = [
  ['wolne tworzenie nut (1 ms na węzeł audio)', { fake: true, nodeMs: 1 }],
  ['dźwięk startuje 400 ms po kliknięciu', { fake: true, delay: 0.4, latency: 0.05 }],
  ['słuchawki Bluetooth (opóźnienie 250 ms)', { fake: true, delay: 0.3, latency: 0.25 }],
  ['szybkie klikanie ▶ ■ ▶ co 30 ms', { fake: true, nodeMs: 1 }, [0, 30, 30]],
  ['prawdziwy AudioContext przeglądarki', { fake: false }],
];
let failed = 0;
for (const [name, opts, clicks] of cases) {
  const offs = await scenario(opts, clicks);
  const worst = offs.length ? Math.max(...offs.map(Math.abs)) : null;
  const median = offs.length ? [...offs].map(Math.abs).sort((a, b) => a - b)[offs.length >> 1] : null;
  const ok = offs.length >= 3 && median <= MEDIAN_MS && worst <= WORST_MS;
  if (!ok) failed++;
  console.log(`${ok ? 'OK  ' : 'BŁĄD'} ${name.padEnd(44)} podświetleń: ${String(offs.length).padStart(2)}, ` +
              `przesunięcie: ${offs.length ? `mediana ${median} ms, zakres ${Math.min(...offs)}…${Math.max(...offs)} ms` : 'brak pomiaru'}`);
}
process.exit(failed ? 1 : 0);
