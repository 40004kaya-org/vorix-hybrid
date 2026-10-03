// ═══════════════════════════════════════════
// VORIX BOARD — SVG رسم خط‌دار
// ═══════════════════════════════════════════

const NS = 'http://www.w3.org/2000/svg';
const svg = document.getElementById('board');

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
  const c = el('circle', { cx, cy, r, class: cls });
  svg.appendChild(c);
  return c;
}

// ─── رنگ بر اساس وضعیت ───
function colorOf(id) {
  const l = (LIVE && LIVE.layers) ? LIVE.layers.find(x => x.id === id) : null;
  return l ? l.color : 'dark';
}

// ─── رسم کل برد ───
function renderBoard() {
  svg.innerHTML = '';

  // ═══ CORE (بالا وسط) ═══
  R(340, 20, 220, 85, 'green');
  T(450, 45, '◉ VORIX CORE', 'title');
  T(450, 65, 'CPU 48% · RAM 67%', 'sub');
  T(450, 85, 'NET 12%', 'sub');

  // خط پایین به chipset
  L(450, 105, 450, 135);

  // ═══ Chipset Row 1 (4 تا) ═══
  const row1 = [
    { id: 'ingress',      code: 'ING',  x: 40,  w: 190, layers: ['L01','L02','L04','L06','L09','L13','L15','L-Root'] },
    { id: 'intelligence', code: 'INT',  x: 245, w: 170, layers: ['L03','L21','L-MITRE'] },
    { id: 'response',     code: 'RESP', x: 430, w: 200, layers: ['L10','L-Resp','L-Scor','L-Fore'] },
    { id: 'data',         code: 'DATA', x: 645, w: 215, layers: ['L05','L11','L12','L31','L-Hash','L-Mock'] },
  ];

  row1.forEach(chip => {
    const colors = chip.layers.map(colorOf);
    let c = 'green';
    if (colors.includes('red')) c = 'red';
    else if (colors.includes('orange')) c = 'orange';
    else if (colors.every(x => x === 'yellow')) c = 'yellow';

    R(chip.x, 135, chip.w, 65, c);
    T(chip.x + chip.w / 2, 158, chip.code);

    // LEDها
    const ledsPerRow = Math.min(chip.layers.length, 8);
    const ledSpacing = 18;
    const startX = chip.x + chip.w / 2 - ((ledsPerRow - 1) * ledSpacing) / 2;
    chip.layers.slice(0, 8).forEach((lid, i) => {
      const col = colorOf(lid);
      const cls = 'led ' + col + (col === 'red' ? ' pulse' : col === 'green' ? ' pulse' : '');
      C(startX + i * ledSpacing, 185, 6, cls);
    });
  });

  // خطوط بین chipset row 1
  L(230, 167, 245, 167);
  L(415, 167, 430, 167);
  L(630, 167, 645, 167);

  // خط پایین از وسط به row 2
  L(450, 200, 450, 230);

  // ═══ Chipset Row 2 (2 تا) ═══
  const row2 = [
    { id: 'output',      code: 'OUT',  x: 130, w: 290, layers: ['L-MC','L-LF','L-Rep','L-Voice','L-Bot','L-Sync','L-Agent'] },
    { id: 'selfdefense', code: 'SELF', x: 480, w: 290, layers: ['L16','L17','L18','L-Keep','L19','L25','L29','L-FIM'] },
  ];

  row2.forEach(chip => {
    const colors = chip.layers.map(colorOf);
    let c = 'green';
    if (colors.includes('red')) c = 'red';
    else if (colors.includes('orange')) c = 'orange';
    else if (colors.every(x => x === 'yellow')) c = 'yellow';

    R(chip.x, 230, chip.w, 65, c);
    T(chip.x + chip.w / 2, 253, chip.code);

    const ledsPerRow = Math.min(chip.layers.length, 9);
    const ledSpacing = 18;
    const startX = chip.x + chip.w / 2 - ((ledsPerRow - 1) * ledSpacing) / 2;
    chip.layers.slice(0, 9).forEach((lid, i) => {
      const col = colorOf(lid);
      const cls = 'led ' + col + (col === 'red' ? ' pulse' : col === 'green' ? ' pulse' : '');
      C(startX + i * ledSpacing, 280, 6, cls);
    });
  });

  L(420, 262, 480, 262);  // بین OUT و SELF

  // خط پایین
  L(450, 295, 450, 325);

  // ═══ SLOTS (44 لایه) ═══
  R(40, 325, 820, 105);
  T(450, 348, 'SLOTS — 44 LAYERS');

  // ۴۴ اسلات: ۲۲ × ۲
  const slotW = 32;
  const slotH = 32;
  const gap = 4;
  const totalW = 22 * (slotW + gap) - gap;
  const startX = 450 - totalW / 2;

  const allLayers = [
    'L01','L02','L03','L04','L05','L06','L07','L08','L09','L10','L11',
    'L12','L13','L15','L16','L17','L18','L19','L21','L22','L23','L24',
    'L25','L26','L29','L31','L-FIM','L-Root','L-MC','L-LF','L-MITRE',
    'L-Resp','L-Scor','L-Rep','L-Fore','L-Hash','L-Mock','L-Voice',
    'L-Bot','L-Sync','L-Keep','L-Agent',
  ];

  allLayers.slice(0, 44).forEach((lid, i) => {
    const col = i < 22 ? 0 : 1;
    const idx = i % 22;
    const x = startX + idx * (slotW + gap);
    const y = 360 + col * (slotH + gap);

    const color = colorOf(lid);
    let cls = '';
    if (color === 'red') cls = 'red';
    else if (color === 'orange') cls = 'orange';

    R(x, y, slotW, slotH, cls);
    T(x + slotW / 2, y + 12, lid.replace('L-', '').replace('L', ''), 'sub');

    // LED کوچیک
    const ledColor = colorOf(lid);
    C(x + slotW / 2, y + 24, 3, 'led ' + ledColor);
  });

  // خط پایین
  L(450, 430, 450, 445);

  // ═══ I/O Ports ═══
  const ports = [
    { name: '📱 Phone', x: 100 },
    { name: '🌐 Web',   x: 280 },
    { name: '🤖 Bot',   x: 460 },
    { name: '📊 API',   x: 640 },
  ];
  ports.forEach(p => {
    R(p.x, 445, 160, 40);
    T(p.x + 80, 470, p.name);
  });

  // ═══ Bottom Stats ═══
  const stats = [
    { color: 'green',  x: 160, label: '19' },
    { color: 'yellow', x: 340, label: '22' },
    { color: 'red',    x: 520, label: '1' },
    { color: 'blue',   x: 700, label: '42' },
  ];
  stats.forEach(s => {
    C(s.x, 530, 7, 'led ' + (s.color === 'blue' ? 'green' : s.color) + ' pulse');
    T(s.x + 20, 535, s.label, 'label');
  });

  // ═══ Alert خط بالا ═══
  const hasRed = LIVE.layers && LIVE.layers.some(l => l.color === 'red');
  if (hasRed) {
    svg.appendChild(el('rect', { x: 0, y: 0, width: 900, height: 3, fill: '#ef4444' }));
  } else {
    svg.appendChild(el('rect', { x: 0, y: 0, width: 900, height: 3, fill: '#10b981' }));
  }
}

// ─── Load Data ───
let LIVE = { layers: [], stats: {} };

async function load() {
  try {
    const data = await fetch('data/live.json?v=' + Date.now()).then(r => r.json());
    LIVE = data;
  } catch (e) {
    console.log('Using fallback data');
    // داده‌ی fallback
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
