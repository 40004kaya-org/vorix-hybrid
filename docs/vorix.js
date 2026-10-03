// ══════════════════════════════════════════
// VORIX Datacenter — Live
// ══════════════════════════════════════════

const SECTIONS = {
  ingress:      { code: 'ING',  name: 'Ingress',      fa: 'ورودی' },
  intelligence: { code: 'INT',  name: 'Intelligence', fa: 'هوشمند' },
  response:     { code: 'RES',  name: 'Response',     fa: 'واکنش' },
  data:         { code: 'DATA', name: 'Data',         fa: 'داده' },
  output:       { code: 'OUT',  name: 'Output',       fa: 'خروجی' },
};

const LAYER_META = {
  "L01": "ingress", "L02": "ingress", "L03": "intelligence", "L04": "ingress",
  "L05": "data", "L06": "ingress", "L07": "ingress", "L08": "ingress",
  "L09": "ingress", "L10": "response", "L11": "data", "L12": "data",
  "L13": "ingress", "L15": "ingress", "L16": "ingress", "L17": "ingress",
  "L18": "data", "L19": "intelligence", "L21": "intelligence",
  "L22": "ingress", "L23": "ingress", "L24": "ingress", "L25": "data",
  "L26": "data", "L29": "intelligence", "L31": "data",
  "L-FIM": "intelligence", "L-Root": "intelligence",
  "L-MC": "output", "L-LF": "output", "L-MITRE": "intelligence",
  "L-Resp": "response", "L-Scor": "response",
  "L-Rep": "output", "L-Fore": "response",
  "L-Hash": "data", "L-Mock": "data", "L-Voice": "output",
  "L-Bot": "output", "L-Sync": "output", "L-Keep": "output", "L-Agent": "output",
};

let LIVE = { layers: [], stats: {} };

// ─── Circuit Board ───
function renderCircuit() {
  const el = document.getElementById('circuit');
  if (!el) return;
  
  const order = ['ingress', 'intelligence', 'response', 'data', 'output'];
  
  let html = '';
  order.forEach((section, i) => {
    const layers = LIVE.layers.filter(l => LAYER_META[l.id] === section);
    const active = layers.filter(l => l.color === 'green').length;
    const total = layers.length;
    const hasRed = layers.some(l => l.color === 'red');
    
    let color = 'green';
    if (hasRed) color = 'red';
    else if (layers.some(l => l.color === 'orange')) color = 'orange';
    else if (layers.every(l => l.color === 'yellow')) color = 'yellow';
    else if (active === 0) color = 'dark';
    
    // Arrow before (not first)
    if (i > 0) {
      html += `<div class="circuit-arrow ${hasRed ? 'danger' : ''}">→</div>`;
    }
    
    const s = SECTIONS[section];
    html += `
      <div class="stage-card">
        <div class="stage-code">${s.code}</div>
        <div class="stage-led ${color}"></div>
        <div class="stage-name">${s.fa}</div>
        <div class="stage-count">${active}/${total}</div>
      </div>
    `;
  });
  
  el.innerHTML = html;
}

// ─── Racks ───
function renderRacks() {
  const el = document.getElementById('racks');
  if (!el) return;
  
  const order = ['ingress', 'intelligence', 'response', 'data', 'output'];
  
  el.innerHTML = order.map(section => {
    const layers = LIVE.layers.filter(l => LAYER_META[l.id] === section);
    const active = layers.filter(l => l.color === 'green').length;
    const total = layers.length;
    const hasRed = layers.some(l => l.color === 'red');
    
    const bladesHTML = layers.map(l => `
      <a class="blade ${l.color === 'red' ? 'blade-red' : ''}" 
         href="https://t.me/vorix_security_bot?start=layer_${l.id}"
         target="_blank" 
         title="${l.id} - ${l.mode}"
         style="text-decoration:none;color:inherit;display:flex">
        <div class="blade-led ${l.color}"></div>
        <div class="blade-name">${l.id}</div>
      </a>
    `).join('');
    
    const s = SECTIONS[section];
    return `
      <div class="rack ${hasRed ? 'rack-red' : ''}">
        <div class="rack-top"></div>
        <div class="rack-glass"></div>
        <div class="rack-blades">${bladesHTML}</div>
        <div class="rack-label">
          <div class="rack-label-name">${s.code}</div>
          <div class="rack-label-count">${active}/${total}</div>
        </div>
      </div>
    `;
  }).join('');
}

// ─── Stats Bar ───
function renderStats() {
  const el = document.getElementById('stats');
  if (!el) return;
  
  const s = LIVE.stats;
  el.innerHTML = `
    <div class="stat-box green">
      <div class="stat-dot green"></div>
      <div class="stat-content">
        <div class="stat-value">${s.green || 0}</div>
        <div class="stat-label">ACTIVE</div>
      </div>
    </div>
    <div class="stat-box yellow">
      <div class="stat-dot yellow"></div>
      <div class="stat-content">
        <div class="stat-value">${s.yellow || 0}</div>
        <div class="stat-label">STANDBY</div>
      </div>
    </div>
    <div class="stat-box red">
      <div class="stat-dot red"></div>
      <div class="stat-content">
        <div class="stat-value">${s.red || 0}</div>
        <div class="stat-label">DOWN</div>
      </div>
    </div>
    <div class="stat-box blue">
      <div class="stat-dot blue"></div>
      <div class="stat-content">
        <div class="stat-value">${s.total || 0}</div>
        <div class="stat-label">TOTAL</div>
      </div>
    </div>
  `;
}

// ─── Alert System ───
function updateAlerts() {
  const s = LIVE.stats;
  const ceiling = document.getElementById('ceiling-alert');
  const banner = document.getElementById('alert-banner');
  
  if (!ceiling || !banner) return;
  
  if (s.red > 0) {
    ceiling.className = 'ceiling-alert red';
    banner.className = 'alert-banner show';
    banner.textContent = `🚨 ${s.red} لایه قطع شده — بررسی کن!`;
  } else if (s.yellow > 25) {
    ceiling.className = 'ceiling-alert orange';
    banner.className = 'alert-banner show';
    banner.textContent = `⚠️ ${s.yellow} لایه در حالت Standby`;
    setTimeout(() => banner.classList.remove('show'), 4000);
  } else {
    ceiling.className = 'ceiling-alert';
    banner.classList.remove('show');
  }
}

// ─── Clock ───
function tick() {
  const el = document.getElementById('clock');
  if (el) el.textContent = new Date().toLocaleTimeString('fa-IR', { hour12: false });
}

// ─── Load ───
async function load() {
  try {
    const data = await fetch('data/live.json?v=' + Date.now()).then(r => r.json());
    LIVE = data;
    renderCircuit();
    renderRacks();
    renderStats();
    updateAlerts();
  } catch (e) {
    console.error('Load error:', e);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  tick();
  setInterval(tick, 1000);
  load();
  setInterval(load, 30000);
});
