// VORIX BOARD
const NS = 'http://www.w3.org/2000/svg';
const svg = document.getElementById('board');
let LIVE = { layers: [], stats: {} };

function el(tag, attrs) {
  const e = document.createElementNS(NS, tag);
  for (const k in attrs) e.setAttribute(k, attrs[k]);
  return e;
}
function R(x, y, w, h, cls = '') {
  svg.appendChild(el('rect', { x, y, width: w, height: h, rx: 4, class: 'box ' + cls }));
}
function T(x, y, txt, cls = 'label') {
  const e = el('text', { x, y, class: cls });
  e.textContent = txt;
  svg.appendChild(e);
}
function L(x1, y1, x2, y2, cls = 'line') {
  svg.appendChild(el('line', { x1, y1, x2, y2, class: cls }));
}
function C(cx, cy, r, cls = 'led green') {
  svg.appendChild(el('circle', { cx, cy, r, class: cls }));
}
function colorOf(id) {
  const l = LIVE.layers ? LIVE.layers.find(x => x.id === id) : null;
  return l ? l.color : 'dark';
}

function renderBoard() {
  svg.innerHTML = '';

  const hasRed = LIVE.layers && LIVE.layers.some(l => l.color === 'red');
  svg.appendChild(el('rect', { x: 0, y: 0, width: 900, height: 3, fill: hasRed ? '#ef4444' : '#10b981' }));

  // CORE
  R(340, 30, 220, 80, 'core');
  T(450, 55, '● VORIX CORE', 'core-title');
  const active = LIVE.layers.filter(l => l.running).length;
  const total = LIVE.layers.length;
  T(450, 75, 'CPU 48% · RAM 67%', 'core-sub');
  T(450, 92, 'NET 12%', 'core-sub');

  // Chipset row 1
  const row1 = [
    { code: 'ING', x: 50, w: 180, layers: ['L01', 'L02', 'L03', 'L04', 'L05'] },
    { code: 'INT', x: 250, w: 180, layers: ['L06', 'L07', 'L08', 'L09', 'L10'] },
    { code: 'RESP', x: 450, w: 180, layers: ['L11', 'L12', 'L13', 'L14', 'L15'] },
    { code: 'DATA', x: 650, w: 180, layers: ['L16', 'L17', 'L18', 'L19', 'L20'] },
  ];
  row1.forEach(c => {
    R(c.x, 130, c.w, 60, 'chip');
    T(c.x + c.w / 2, 150, c.code, 'chip-title');
    c.layers.forEach((lid, i) => {
      C(c.x + 30 + i * 30, 170, 6, 'led ' + colorOf(lid));
    });
  });

  // Chipset row 2
  const row2 = [
    { code: 'OUT', x: 150, w: 280, layers: ['L21', 'L22', 'L23', 'L24', 'L25', 'L26'] },
    { code: 'SELF', x: 470, w: 280, layers: ['L27', 'L28', 'L29', 'L30', 'L31', 'L32', 'L33', 'L34'] },
  ];
  row2.forEach(c => {
    R(c.x, 210, c.w, 60, 'chip');
    T(c.x + c.w / 2, 230, c.code, 'chip-title');
    c.layers.forEach((lid, i) => {
      C(c.x + 30 + i * 32, 250, 6, 'led ' + colorOf(lid));
    });
  });

  // SLOTS
  R(50, 290, 800, 70, 'slots');
  T(450, 308, 'SLOTS — 44 LAYERS', 'slots-title');

  const slots = ['L01','L02','L03','L04','L05','L06','L07','L08','L09','L10','L11',
                 'L12','L13','L14','L15','L16','L17','L18','L19','L20','L21','L22',
                 'L23','L24','L25','L26','L27','L28','L29','L-FIM','L-Root','L-MC',
                 'L-LF','L-MITRE','L-Resp','L-Scor','L-Rep','L-Fore','L-Hash','L-Mock',
                 'L-Voice','L-Bot','L-Sync','L-Keep','L-Agent'];

  slots.slice(0, 22).forEach((lid, i) => {
    const x = 65 + i * 34;
    const c = colorOf(lid);
    svg.appendChild(el('circle', { cx: x, cy: 340, r: 6, class: 'led ' + c }));
    T(x, 358, lid, 'slot-label');
  });
  slots.slice(22).forEach((lid, i) => {
    const x = 65 + i * 34;
    const c = colorOf(lid);
    svg.appendChild(el('circle', { cx: x, cy: 340, r: 6, class: 'led ' + c }));
    T(x, 358, lid.replace('L-', ''), 'slot-label');
  });

  // LIVE ANALYTICS title
  T(450, 385, '✦ LIVE ANALYTICS ✦', 'section-title');

  // Charts boxes
  R(50, 400, 380, 100, 'chart');
  T(240, 420, '🔥 HEATMAP 7×24', 'chart-title');
  for (let r = 0; r < 5; r++) {
    for (let c = 0; c < 20; c++) {
      const v = Math.random();
      const col = v > 0.7 ? '#10b981' : v > 0.4 ? '#0a7a5f' : '#053b30';
      svg.appendChild(el('rect', {
        x: 70 + c * 17, y: 432 + r * 12, width: 14, height: 9, fill: col, rx: 1
      }));
    }
  }

  R(470, 400, 380, 100, 'chart');
  T(660, 420, '📈 24H TREND', 'chart-title');
  const trendPts = Array.from({length: 20}, () => 440 + Math.random() * 50);
  const path = trendPts.map((y, i) => `${i === 0 ? 'M' : 'L'}${490 + i * 18},${y}`).join(' ');
  svg.appendChild(el('path', { d: path, fill: 'none', stroke: '#10b981', 'stroke-width': 2 }));
  svg.appendChild(el('path', {
    d: path + ` L${490 + 19 * 18},490 L490,490 Z`,
    fill: 'rgba(16,185,129,0.15)', stroke: 'none'
  }));

  // Row 2 charts
  R(50, 510, 180, 100, 'chart');
  T(140, 530, '◉ TYPES', 'chart-title');
  // Donut
  const cx = 140, cy = 570, r = 30;
  const colors = ['#10b981', '#f59e0b', '#ef4444', '#06b6d4'];
  colors.forEach((c, i) => {
    const a0 = (i / colors.length) * 2 * Math.PI;
    const a1 = ((i + 1) / colors.length) * 2 * Math.PI;
    const x0 = cx + r * Math.cos(a0), y0 = cy + r * Math.sin(a0);
    const x1 = cx + r * Math.cos(a1), y1 = cy + r * Math.sin(a1);
    const large = (a1 - a0) > Math.PI ? 1 : 0;
    svg.appendChild(el('path', {
      d: `M${cx},${cy} L${x0},${y0} A${r},${r} 0 ${large} 1 ${x1},${y1} Z`,
      fill: c
    }));
  });
  svg.appendChild(el('circle', { cx, cy, r: 15, fill: '#0a0a0a' }));

  R(250, 510, 180, 100, 'chart');
  T(340, 530, '⚡ CPU', 'chart-title');
  const cpuVal = 60 + Math.random() * 30;
  svg.appendChild(el('path', {
    d: `M${290},595 A50,50 0 1,1 ${390},595`,
    fill: 'none', stroke: '#333', 'stroke-width': 8
  }));
  const angle = Math.PI * (cpuVal / 100);
  const ex = 340 - 50 * Math.cos(angle);
  const ey = 595 - 50 * Math.sin(angle);
  svg.appendChild(el('path', {
    d: `M290,595 A50,50 0 0,1 ${ex},${ey}`,
    fill: 'none', stroke: cpuVal > 70 ? '#ef4444' : '#10b981', 'stroke-width': 8
  }));
  T(340, 590, Math.round(cpuVal) + '%', 'cpu-text');

  R(450, 510, 400, 100, 'chart');
  T(650, 530, '▦ HOURLY', 'chart-title');
  for (let i = 0; i < 24; i++) {
    const h = 20 + Math.random() * 60;
    svg.appendChild(el('rect', {
      x: 470 + i * 15, y: 595 - h, width: 11, height: h,
      fill: '#10b981', rx: 1
    }));
  }

  // Bottom stats
  const y0 = 640;
  const cols = [
    { label: 'Active', val: active, color: '#10b981' },
    { label: 'Standby', val: total - active - LIVE.layers.filter(l => l.color === 'red').length, color: '#f59e0b' },
    { label: 'Down', val: LIVE.layers.filter(l => l.color === 'red').length, color: '#ef4444' },
    { label: 'Total', val: total, color: '#10b981' },
  ];
  cols.forEach((c, i) => {
    const x = 180 + i * 180;
    svg.appendChild(el('circle', { cx: x - 15, cy: y0 + 10, r: 8, fill: c.color }));
    T(x, y0, c.val, 'stat-num');
    T(x, y0 + 22, c.label, 'stat-label');
  });
}

async function refresh() {
  try {
    const data = await fetch('data/live.json?v=' + Date.now()).then(r => r.json());
    LIVE = data;
    renderBoard();
  } catch (e) {
    console.error('fetch error:', e);
  }
}

refresh();
setInterval(refresh, 30000);
