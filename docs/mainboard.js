// VORIX Mainboard

const ROW1 = [
  { id: 'ingress',      code: 'ING',  layers: ['L01','L02','L04','L06','L09','L13','L15','L-Root'] },
  { id: 'intelligence', code: 'INT',  layers: ['L03','L21','L-MITRE'] },
  { id: 'response',     code: 'RESP', layers: ['L10','L-Resp','L-Scor','L-Fore'] },
  { id: 'data',         code: 'DATA', layers: ['L05','L11','L12','L31','L-Hash','L-Mock'] }
];

const ROW2 = [
  { id: 'output',       code: 'OUT',  layers: ['L-MC','L-LF','L-Rep','L-Voice','L-Bot','L-Sync','L-Agent'] },
  { id: 'selfdefense',  code: 'SELF', layers: ['L16','L17','L18','L-Keep','L19','L25','L29','L-FIM'] }
];

let LIVE = { layers: [], stats: {} };

function colorOf(id) {
  const l = LIVE.layers.find(x => x.id === id);
  return l ? l.color : 'dark';
}

function renderChip(chip) {
  // LEDهای ریز
  const leds = chip.layers.map(id => {
    const color = colorOf(id);
    return `<div class="led ${color}" title="${id}"></div>`;
  }).join('');
  
  // شمارش
  const colors = chip.layers.map(id => colorOf(id));
  const ok = colors.filter(c => c === 'green').length;
  const warn = colors.filter(c => c === 'yellow' || c === 'orange').length;
  const bad = colors.filter(c => c === 'red').length;
  const total = colors.length;
  
  // رنگ کلی chip (بدترین وضعیت)
  let chipColor = 'green';
  if (bad > 0) chipColor = 'red';
  else if (warn > 0) chipColor = 'orange';
  
  return `
    <div class="chip ${chipColor}" onclick="openSection('${chip.id}')">
      <div class="chip-head">${chip.code}</div>
      <div class="leds-row">${leds}</div>
      <div class="chip-stats">
        <span style="color:var(--green)">${ok}</span>
        <span style="color:var(--muted)">/</span>
        <span style="color:var(--yellow)">${warn}</span>
        <span style="color:var(--muted)">/</span>
        <span style="color:var(--red)">${bad}</span>
      </div>
    </div>
  `;
}

function renderRow(rowId, chips) {
  const el = document.getElementById(rowId);
  if (!el) return;
  el.innerHTML = chips.map(renderChip).join('');
}

function renderSlots() {
  const el = document.getElementById('slots');
  if (!el) return;
  
  const all = [];
  ROW1.forEach(c => c.layers.forEach(id => all.push(id)));
  ROW2.forEach(c => c.layers.forEach(id => all.push(id)));
  
  el.innerHTML = all.map(id => {
    const color = colorOf(id);
    return `
      <div class="slot ${color}" onclick="openLayer('${id}')" title="${id}">
        <div class="slot-dot ${color}"></div>
        <div class="slot-code">${id}</div>
      </div>
    `;
  }).join('');
}

function renderStats() {
  const el = document.getElementById('b-stats');
  if (!el) return;
  
  const s = LIVE.stats || {};
  el.innerHTML = `
    <div class="b-stat">
      <span class="b-dot green"></span>
      <span>${s.green || 0}</span>
    </div>
    <div class="b-stat">
      <span class="b-dot yellow"></span>
      <span>${s.yellow || 0}</span>
    </div>
    <div class="b-stat">
      <span class="b-dot red"></span>
      <span>${s.red || 0}</span>
    </div>
    <div class="b-stat">
      <span class="b-dot blue"></span>
      <span>${s.total || 42}</span>
    </div>
  `;
}

function updateAlert() {
  const s = LIVE.stats || {};
  const el = document.getElementById('alert');
  if (!el) return;
  if (s.red > 0) el.className = 'alert red';
  else el.className = 'alert';
}

function updateCorePercent() {
  const el = document.getElementById('core-pct');
  if (!el) return;
  const pct = Math.floor(Math.random() * 30 + 40);
  el.textContent = pct + '%';
}

async function load() {
  try {
    const data = await fetch('data/live.json?v=' + Date.now()).then(r => r.json());
    LIVE = data;
    renderRow('row1', ROW1);
    renderRow('row2', ROW2);
    renderSlots();
    renderStats();
    updateAlert();
  } catch (e) {
    console.error('Load error:', e);
  }
}

function openLayer(id) {
  window.open('https://t.me/vorix_security_bot?start=layer_' + id, '_blank');
}

function openSection(id) {
  window.open('https://t.me/vorix_security_bot?start=section_' + id, '_blank');
}

document.addEventListener('DOMContentLoaded', () => {
  load();
  setInterval(load, 30000);
  setInterval(updateCorePercent, 5000);
});
