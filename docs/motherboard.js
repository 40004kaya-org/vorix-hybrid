// VORIX Motherboard — Live

const CHIPSETS = {
  c1: [
    { id: 'ingress',      code: 'ING',  name: 'ورودی',    layers: ['L01','L02','L04','L06','L09','L13','L15','L-Root'] },
    { id: 'intelligence', code: 'INT',  name: 'هوشمند',   layers: ['L03','L21','L-MITRE'] },
    { id: 'response',     code: 'RESP', name: 'واکنش',    layers: ['L10','L-Resp','L-Scor','L-Fore'] },
    { id: 'data',         code: 'DATA', name: 'داده',      layers: ['L05','L11','L12','L31','L-Hash','L-Mock'] }
  ],
  c2: [
    { id: 'output',       code: 'OUT',  name: 'خروجی',    layers: ['L-MC','L-LF','L-Rep','L-Voice','L-Bot','L-Sync','L-Agent'] },
    { id: 'selfdefense',  code: 'SELF', name: 'خودحفاظت', layers: ['L16','L17','L18','L-Keep','L19','L25','L29','L-FIM'] },
    { id: 'identity',     code: 'IDENT',name: 'هویت',     layers: ['L23','L24','L26'] }
  ]
};

const LAYER_NAMES = {
  "L01":"Anti-Kill","L02":"Threat Intel","L03":"Behavioral","L04":"Auto-Block",
  "L05":"Data Quarantine","L06":"GeoIP Block","L07":"Net Behavior","L08":"Net Monitor",
  "L09":"Rate Limiter","L10":"Red Alert","L11":"DNS Sinkhole","L12":"Reverse DNS",
  "L13":"UA Filter","L15":"Fingerprint","L16":"Killswitch","L17":"Watchdog",
  "L18":"Backup Verifier","L19":"Password Leak","L21":"ML Anomaly",
  "L22":"Header Analysis","L23":"Cookie Anomaly","L24":"Session Hijack",
  "L25":"SSL Monitor","L26":"HSTS","L29":"Identity","L31":"Log Encryption",
  "L-FIM":"FIM","L-Root":"Rootkit","L-MC":"Multichannel","L-LF":"LiveFeed",
  "L-MITRE":"MITRE","L-Resp":"Response","L-Scor":"Scoring","L-Rep":"Reports",
  "L-Fore":"Forensics","L-Hash":"HashChain","L-Mock":"Mocker","L-Voice":"Voice",
  "L-Bot":"Bot","L-Sync":"Sync","L-Keep":"Keepalive","L-Agent":"Agent",
};

let LIVE = { layers: [], stats: {} };

function colorOf(id) {
  const l = LIVE.layers.find(x => x.id === id);
  return l ? l.color : 'dark';
}

// ─── Render Chipset ───
function renderChipset(elId, items) {
  const el = document.getElementById(elId);
  if (!el) return;
  
  el.innerHTML = items.map(item => {
    // LEDهای ریز هر لایه
    const ledsHTML = item.layers.map(id => {
      const color = colorOf(id);
      return `<div class="led ${color}" title="${id}"></div>`;
    }).join('');
    
    // شمارش
    const colors = item.layers.map(id => colorOf(id));
    const active = colors.filter(c => c === 'green').length;
    const warn = colors.filter(c => c === 'yellow' || c === 'orange').length;
    const bad = colors.filter(c => c === 'red').length;
    
    return `
      <div class="chip" onclick="openSection('${item.id}')">
        <div class="chip-name">${item.code}</div>
        <div class="chip-leds">${ledsHTML}</div>
        <div class="chip-count">
          <span class="ok">${active}</span> ·
          <span class="warn">${warn}</span> ·
          <span class="bad">${bad}</span>
        </div>
      </div>
    `;
  }).join('');
}

// ─── Render Slots (44) ───
function renderSlots() {
  const el = document.getElementById('slots');
  if (!el) return;
  
  const allLayers = [];
  CHIPSETS.c1.forEach(s => s.layers.forEach(id => allLayers.push(id)));
  CHIPSETS.c2.forEach(s => s.layers.forEach(id => allLayers.push(id)));
  
  el.innerHTML = allLayers.map(id => {
    const color = colorOf(id);
    return `
      <div class="slot ${color}" onclick="openLayer('${id}')" title="${LAYER_NAMES[id] || id}">
        <div class="slot-led ${color}"></div>
        <div class="slot-code">${id}</div>
      </div>
    `;
  }).join('');
}

// ─── Render I/O Ports ───
function renderIOPorts() {
  const el = document.getElementById('ioports');
  if (!el) return;
  
  const ports = [
    { name: 'Phone', icon: '📱' },
    { name: 'Web',   icon: '🌐' },
    { name: 'Bot',   icon: '🤖' },
    { name: 'API',   icon: '📊' },
  ];
  
  el.innerHTML = ports.map(p => `
    <div class="ioport">
      <div class="ioport-led"></div>
      <span>${p.icon}</span>
      <span class="ioport-name">${p.name}</span>
    </div>
  `).join('');
}

// ─── Render Bottom Metrics ───
function renderBottom() {
  const el = document.getElementById('bottom');
  if (!el) return;
  
  const s = LIVE.stats || {};
  el.innerHTML = `
    <div class="bm green">
      <div class="bm-dot green"></div>
      <div>
        <div class="bm-num">${s.green || 0}</div>
        <div class="bm-lbl">Active</div>
      </div>
    </div>
    <div class="bm yellow">
      <div class="bm-dot yellow"></div>
      <div>
        <div class="bm-num">${s.yellow || 0}</div>
        <div class="bm-lbl">Standby</div>
      </div>
    </div>
    <div class="bm red">
      <div class="bm-dot red"></div>
      <div>
        <div class="bm-num">${s.red || 0}</div>
        <div class="bm-lbl">Down</div>
      </div>
    </div>
    <div class="bm blue">
      <div class="bm-dot blue"></div>
      <div>
        <div class="bm-num">${s.total || 0}</div>
        <div class="bm-lbl">Total</div>
      </div>
    </div>
  `;
}

// ─── Core Metrics (CPU/RAM/Net) ───
function updateCoreMetrics() {
  const s = LIVE.stats || {};
  const cpu = s.cpu || Math.floor(Math.random() * 40 + 30);
  const ram = s.ram || Math.floor(Math.random() * 30 + 50);
  const net = Math.floor(Math.random() * 20 + 5);
  
  setMetric('cpu', cpu);
  setMetric('ram', ram);
  setMetric('net', net);
}

function setMetric(id, val) {
  const bar = document.getElementById(id + '-bar');
  const txt = document.getElementById(id + '-val');
  if (!bar || !txt) return;
  
  bar.style.width = Math.min(100, val) + '%';
  txt.textContent = val + '%';
  
  let color = 'green';
  if (val > 85) color = 'red';
  else if (val > 70) color = 'orange';
  else if (val > 55) color = 'yellow';
  
  bar.className = 'metric-fill ' + (color !== 'green' ? color : '');
  txt.className = 'metric-value ' + (color !== 'green' ? color : '');
}

// ─── Alert ───
function updateAlert() {
  const s = LIVE.stats || {};
  const el = document.getElementById('alert');
  const pill = document.getElementById('status-pill');
  if (!el || !pill) return;
  
  if (s.red > 0) {
    el.className = 'alert-line red';
    pill.textContent = `⚠ ${s.red} DOWN`;
    pill.style.color = 'var(--red)';
    pill.style.borderColor = 'rgba(239,68,68,0.3)';
  } else {
    el.className = 'alert-line';
    pill.textContent = 'ONLINE';
    pill.style.color = 'var(--green)';
    pill.style.borderColor = 'rgba(16,185,129,0.3)';
  }
}

// ─── Clock ───
function tick() {
  const el = document.getElementById('clock');
  if (el) el.textContent = new Date().toLocaleTimeString('fa-IR', { hour12: false });
}

// ─── Load Data ───
async function load() {
  try {
    const data = await fetch('data/live.json?v=' + Date.now()).then(r => r.json());
    LIVE = data;
    renderChipset('chipset1', CHIPSETS.c1);
    renderChipset('chipset2', CHIPSETS.c2);
    renderSlots();
    renderIOPorts();
    renderBottom();
    updateCoreMetrics();
    updateAlert();
  } catch (e) {
    console.error('Load error:', e);
  }
}

// ─── Deep links ───
function openLayer(id) {
  window.open('https://t.me/vorix_security_bot?start=layer_' + id, '_blank');
}

function openSection(id) {
  window.open('https://t.me/vorix_security_bot?start=section_' + id, '_blank');
}

document.addEventListener('DOMContentLoaded', () => {
  tick();
  setInterval(tick, 1000);
  load();
  setInterval(load, 30000);
  setInterval(updateCoreMetrics, 5000);
});
