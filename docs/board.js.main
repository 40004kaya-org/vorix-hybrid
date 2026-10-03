// ═══════════════════════════════════════════
// VORIX BOARD — SVG (برد + چارت‌ها)
// ═══════════════════════════════════════════

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

// ─── رسم کل برد ───
function renderBoard() {
  svg.innerHTML = '';

  // Alert خط بالا
  const hasRed = LIVE.layers && LIVE.layers.some(l => l.color === 'red');
  svg.appendChild(el('rect', { x: 0, y: 0, width: 900, height: 3, fill: hasRed ? '#ef4444' : '#10b981' }));

  // ═══ CORE ═══
  R(340, 20, 220, 85, 'green');
  T(450, 45, '◉ VORIX CORE', 'title');
  T(450, 65, 'CPU 48% · RAM 67%', 'sub');
  T(450, 85, 'NET 12%', 'sub');
  L(450, 105, 450, 135);

  // ═══ Row 1: ING, INT, RESP, DATA ═══
  const row1 = [
    { code: 'ING',  x: 40,  w: 190, layers: ['L01','L02','L04','L06','L09','L13','L15','L-Root'] },
    { code: 'INT',  x: 245, w: 170, layers: ['L03','L21','L-MITRE'] },
    { code: 'RESP', x: 430, w: 200, layers: ['L10','L-Resp','L-Scor','L-Fore'] },
    { code: 'DATA', x: 645, w: 215, layers: ['L05','L11','L12','L31','L-Hash','L-Mock'] },
  ];
  row1.forEach(chip => {
    const colors = chip.layers.map(colorOf);
    let c = 'green';
    if (colors.includes('red')) c = 'red';
    else if (colors.includes('orange')) c = 'orange';
    else if (colors.every(x => x === 'yellow')) c = 'yellow';

    R(chip.x, 135, chip.w, 65, c);
    T(chip.x + chip.w / 2, 158, chip.code);

    const leds = Math.min(chip.layers.length, 8);
    const spacing = 18;
    const startX = chip.x + chip.w / 2 - ((leds - 1) * spacing) / 2;
    chip.layers.slice(0, 8).forEach((lid, i) => {
      const col = colorOf(lid);
      const cls = 'led ' + col + (col === 'red' ? ' pulse' : col === 'green' ? ' pulse' : '');
      C(startX + i * spacing, 185, 6, cls);
    });
  });
  L(230, 167, 245, 167);
  L(415, 167, 430, 167);
  L(630, 167, 645, 167);
  L(450, 200, 450, 230);

  // ═══ Row 2: OUT, SELF ═══
  const row2 = [
    { code: 'OUT',  x: 130, w: 290, layers: ['L-MC','L-LF','L-Rep','L-Voice','L-Bot','L-Sync','L-Agent'] },
    { code: 'SELF', x: 480, w: 290, layers: ['L16','L17','L18','L-Keep','L19','L25','L29','L-FIM'] },
  ];
  row2.forEach(chip => {
    const colors = chip.layers.map(colorOf);
    let c = 'green';
    if (colors.includes('red')) c = 'red';
    else if (colors.includes('orange')) c = 'orange';
    else if (colors.every(x => x === 'yellow')) c = 'yellow';

    R(chip.x, 230, chip.w, 65, c);
    T(chip.x + chip.w / 2, 253, chip.code);

    const leds = Math.min(chip.layers.length, 9);
    const spacing = 18;
    const startX = chip.x + chip.w / 2 - ((leds - 1) * spacing) / 2;
    chip.layers.slice(0, 9).forEach((lid, i) => {
      const col = colorOf(lid);
      const cls = 'led ' + col + (col === 'red' ? ' pulse' : col === 'green' ? ' pulse' : '');
      C(startX + i * spacing, 280, 6, cls);
    });
  });
  L(420, 262, 480, 262);
  L(450, 295, 450, 325);

  // ═══ SLOTS 44 ═══
  R(40, 325, 820, 100);
  T(450, 345, 'SLOTS — 44 LAYERS', 'chart-label');

  const allLayers = [
    'L01','L02','L03','L04','L05','L06','L07','L08','L09','L10','L11',
    'L12','L13','L15','L16','L17','L18','L19','L21','L22','L23','L24',
    'L25','L26','L29','L31','L-FIM','L-Root','L-MC','L-LF','L-MITRE',
    'L-Resp','L-Scor','L-Rep','L-Fore','L-Hash','L-Mock','L-Voice',
    'L-Bot','L-Sync','L-Keep','L-Agent',
  ];
  const sW = 32, sH = 32, sGap = 4;
  const rowW = 22 * (sW + sGap) - sGap;
  const startX = 450 - rowW / 2;

  allLayers.slice(0, 44).forEach((lid, i) => {
    const col = i < 22 ? 0 : 1;
    const idx = i % 22;
    const x = startX + idx * (sW + sGap);
    const y = 358 + col * (sH + sGap);
    const color = colorOf(lid);
    let cls = '';
    if (color === 'red') cls = 'red';
    else if (color === 'orange') cls = 'orange';
    R(x, y, sW, sH, cls);
    T(x + sW / 2, y + 14, lid.replace('L-','').replace('L',''), 'sub');
    C(x + sW / 2, y + 25, 3, 'led ' + color);
  });

  // ═══ Divider بین برد و چارت‌ها ═══
  L(40, 440, 860, 440, 'line thin');
  T(450, 460, '◈ LIVE ANALYTICS ◈', 'chart-label');

  // ═══ HEATMAP (7×24) ═══
  renderHeatmap(40, 475, 400, 110);

  // ═══ LINE CHART ═══
  renderLineChart(460, 475, 400, 110);

  // ═══ Bottom Chart Row ═══
  renderDonut(40, 610, 200, 110);
  renderGauge(260, 610, 200, 110);
  renderBars(480, 610, 380, 110);

  // ═══ Bottom Stats ═══
  L(40, 745, 860, 745, 'line thin');
  const stats = LIVE.stats || { green: 19, yellow: 22, red: 1, total: 42 };
  const statArr = [
    { color: 'green',  label: 'Active',  value: stats.green || 0,  x: 180 },
    { color: 'yellow', label: 'Standby', value: stats.yellow || 0, x: 380 },
    { color: 'red',    label: 'Down',    value: stats.red || 0,    x: 580 },
    { color: 'blue',   label: 'Total',   value: stats.total || 0,  x: 780 },
  ];
  statArr.forEach(s => {
    C(s.x, 780, 7, 'led ' + (s.color === 'blue' ? 'green' : s.color) + ' pulse');
    T(s.x + 20, 778, String(s.value), 'label');
    T(s.x + 20, 793, s.label, 'sub');
  });
}

// ═══ HEATMAP ═══
function renderHeatmap(x, y, w, h) {
  R(x, y, w, h);
  T(x + w/2, y + 15, '🔥 HEATMAP 7×24', 'chart-label');

  const cols = 24, rows = 7;
  const cellW = (w - 40) / cols;
  const cellH = (h - 40) / rows;
  const startX = x + 20;
  const startY = y + 25;

  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const lvl = Math.floor(Math.random() * 5);
      const cls = 'hm l' + lvl;
      svg.appendChild(el('rect', {
        x: startX + c * cellW + 0.5,
        y: startY + r * cellH + 0.5,
        width: cellW - 1,
        height: cellH - 1,
        class: cls,
        rx: 1
      }));
    }
  }
}

// ═══ LINE CHART ═══
function renderLineChart(x, y, w, h) {
  R(x, y, w, h);
  T(x + w/2, y + 15, '📈 24H TREND', 'chart-label');

  const points = [];
  const N = 24;
  for (let i = 0; i < N; i++) points.push(Math.random() * 0.7 + 0.1);

  const padding = 20;
  const chartW = w - padding * 2;
  const chartH = h - 40;
  const baseY = y + h - 15;

  // Grid
  for (let i = 0; i <= 4; i++) {
    const gy = y + 25 + (chartH / 4) * i;
    svg.appendChild(el('line', {
      x1: x + padding, y1: gy,
      x2: x + w - padding, y2: gy,
      stroke: '#1a2233', 'stroke-width': 0.5
    }));
  }

  // Path
  let path = '';
  let areaPath = '';
  points.forEach((p, i) => {
    const px = x + padding + (chartW / (N - 1)) * i;
    const py = baseY - p * chartH;
    if (i === 0) { path = `M${px},${py}`; areaPath = `M${px},${baseY} L${px},${py}`; }
    else { path += ` L${px},${py}`; areaPath += ` L${px},${py}`; }
  });
  areaPath += ` L${x + padding + chartW},${baseY} Z`;

  svg.appendChild(el('path', { d: areaPath, class: 'line area' }));
  svg.appendChild(el('path', { d: path, class: 'line' }));

  // End dot
  const lastX = x + padding + chartW;
  const lastY = baseY - points[N-1] * chartH;
  C(lastX, lastY, 3, 'led green pulse');
}

// ═══ DONUT ═══
function renderDonut(x, y, w, h) {
  R(x, y, w, h);
  T(x + w/2, y + 15, '🎯 TYPES', 'chart-label');

  const cx = x + w / 2;
  const cy = y + 25 + (h - 40) / 2;
  const r1 = 32, r2 = 20;

  const data = [
    { v: 40, c: '#ef4444' },
    { v: 25, c: '#f97316' },
    { v: 20, c: '#f59e0b' },
    { v: 15, c: '#10b981' },
  ];
  const total = data.reduce((s, d) => s + d.v, 0);
  let angle = -Math.PI / 2;

  data.forEach(d => {
    const a1 = angle;
    const a2 = angle + (d.v / total) * Math.PI * 2;

    const x1 = cx + r1 * Math.cos(a1), y1 = cy + r1 * Math.sin(a1);
    const x2 = cx + r1 * Math.cos(a2), y2 = cy + r1 * Math.sin(a2);
    const xi1 = cx + r2 * Math.cos(a1), yi1 = cy + r2 * Math.sin(a1);
    const xi2 = cx + r2 * Math.cos(a2), yi2 = cy + r2 * Math.sin(a2);
    const large = (a2 - a1) > Math.PI ? 1 : 0;

    const d_path = `M${x1},${y1} A${r1},${r1} 0 ${large} 1 ${x2},${y2} L${xi2},${yi2} A${r2},${r2} 0 ${large} 0 ${xi1},${yi1} Z`;
    svg.appendChild(el('path', { d: d_path, fill: d.c, opacity: 0.85 }));

    angle = a2;
  });
}

// ═══ GAUGE ═══
function renderGauge(x, y, w, h) {
  R(x, y, w, h);
  T(x + w/2, y + 15, '⚡ CPU', 'chart-label');

  const cx = x + w / 2;
  const cy = y + h - 20;
  const r = 35;
  const val = Math.random() * 0.5 + 0.4; // 40-90%
  const endAngle = Math.PI + Math.PI * val;

  // Background arc
  const bgA1 = Math.PI;
  const bgA2 = Math.PI * 2;
  const bg_x1 = cx + r * Math.cos(bgA1), bg_y1 = cy + r * Math.sin(bgA1);
  const bg_x2 = cx + r * Math.cos(bgA2), bg_y2 = cy + r * Math.sin(bgA2);
  svg.appendChild(el('path', {
    d: `M${bg_x1},${bg_y1} A${r},${r} 0 0 1 ${bg_x2},${bg_y2}`,
    stroke: '#1a2233', 'stroke-width': 8, fill: 'none', 'stroke-linecap': 'round'
  }));

  // Value arc
  const v_x2 = cx + r * Math.cos(endAngle), v_y2 = cy + r * Math.sin(endAngle);
  const col = val > 0.75 ? '#ef4444' : val > 0.55 ? '#f59e0b' : '#10b981';
  svg.appendChild(el('path', {
    d: `M${bg_x1},${bg_y1} A${r},${r} 0 0 1 ${v_x2},${v_y2}`,
    stroke: col, 'stroke-width': 8, fill: 'none', 'stroke-linecap': 'round'
  }));

  // Text
  const txt = el('text', { x: cx, y: cy - 5, class: 'title', style: 'font-size:18px;fill:' + col });
  txt.textContent = Math.round(val * 100) + '%';
  svg.appendChild(txt);
}

// ═══ BARS ═══
function renderBars(x, y, w, h) {
  R(x, y, w, h);
  T(x + w/2, y + 15, '📊 HOURLY', 'chart-label');

  const N = 24;
  const padding = 15;
  const chartW = w - padding * 2;
  const chartH = h - 40;
  const barW = chartW / N - 2;
  const baseY = y + h - 15;

  for (let i = 0; i < N; i++) {
    const v = Math.random() * 0.9 + 0.1;
    const barH = v * chartH;
    const bx = x + padding + i * (chartW / N);
    const by = baseY - barH;
    svg.appendChild(el('rect', {
      x: bx, y: by, width: barW, height: barH,
      rx: 2, fill: '#10b981', opacity: 0.6 + v * 0.4
    }));
  }
}

// ═══ Load ═══
async function load() {
  try {
    const data = await fetch('data/live.json?v=' + Date.now()).then(r => r.json());
    LIVE = data;
  } catch (e) {
    LIVE = {
      layers: [
        { id: 'L01', color: 'green' }, { id: 'L02', color: 'yellow' },
        { id: 'L03', color: 'green' }, { id: 'L04', color: 'green' },
        { id: 'L05', color: 'yellow' }, { id: 'L06', color: 'green' },
        { id: 'L07', color: 'yellow' }, { id: 'L08', color: 'green' },
        { id: 'L09', color: 'green' }, { id: 'L10', color: 'green' },
        { id: 'L11', color: 'yellow' }, { id: 'L12', color: 'yellow' },
        { id: 'L13', color: 'yellow' }, { id: 'L15', color: 'yellow' },
        { id: 'L16', color: 'yellow' }, { id: 'L17', color: 'green' },
        { id: 'L18', color: 'yellow' }, { id: 'L19', color: 'green' },
        { id: 'L21', color: 'green' }, { id: 'L22', color: 'yellow' },
        { id: 'L23', color: 'yellow' }, { id: 'L24', color: 'yellow' },
        { id: 'L25', color: 'green' }, { id: 'L26', color: 'yellow' },
        { id: 'L29', color: 'green' }, { id: 'L31', color: 'yellow' },
        { id: 'L-FIM', color: 'green' }, { id: 'L-Root', color: 'green' },
        { id: 'L-MC', color: 'green' }, { id: 'L-LF', color: 'green' },
        { id: 'L-MITRE', color: 'yellow' }, { id: 'L-Resp', color: 'yellow' },
        { id: 'L-Scor', color: 'yellow' }, { id: 'L-Rep', color: 'yellow' },
        { id: 'L-Fore', color: 'yellow' }, { id: 'L-Hash', color: 'yellow' },
        { id: 'L-Mock', color: 'yellow' }, { id: 'L-Voice', color: 'yellow' },
        { id: 'L-Bot', color: 'green' }, { id: 'L-Sync', color: 'red' },
        { id: 'L-Keep', color: 'green' }, { id: 'L-Agent', color: 'green' },
      ],
      stats: { green: 19, yellow: 22, red: 1, total: 42 }
    };
  }
  renderBoard();
}

document.addEventListener('DOMContentLoaded', () => {
  load();
  setInterval(load, 30000);
});
