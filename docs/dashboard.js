// ══════════════════════════════════════════
// VORIX Dashboard — Live Status
// ══════════════════════════════════════════

const LAYER_META = {
  "L01": {name: "Anti-Kill",       section: "selfdefense"},
  "L02": {name: "Threat Intel",    section: "ingress"},
  "L03": {name: "Behavioral",      section: "intelligence"},
  "L04": {name: "Auto-Block",      section: "response"},
  "L05": {name: "Data Quarantine", section: "data"},
  "L06": {name: "GeoIP Block",     section: "ingress"},
  "L07": {name: "Net Behavior",    section: "network"},
  "L08": {name: "Net Monitor",     section: "network"},
  "L09": {name: "Rate Limiter",    section: "ingress"},
  "L10": {name: "Red Alert",       section: "response"},
  "L11": {name: "DNS Sinkhole",    section: "network"},
  "L12": {name: "Reverse DNS",     section: "network"},
  "L13": {name: "UA Filter",       section: "ingress"},
  "L15": {name: "Fingerprint",     section: "ingress"},
  "L16": {name: "Killswitch",      section: "selfdefense"},
  "L17": {name: "Watchdog",        section: "selfdefense"},
  "L18": {name: "Backup Verifier", section: "selfdefense"},
  "L19": {name: "Password Leak",   section: "identity"},
  "L21": {name: "ML Anomaly",      section: "intelligence"},
  "L22": {name: "Header Analysis", section: "application"},
  "L23": {name: "Cookie Anomaly",  section: "application"},
  "L24": {name: "Session Hijack",  section: "application"},
  "L25": {name: "SSL Monitor",     section: "network"},
  "L26": {name: "HSTS",            section: "application"},
  "L29": {name: "Identity",        section: "identity"},
  "L31": {name: "Log Encryption",  section: "data"},
  "L-FIM":  {name: "FIM",           section: "selfdefense"},
  "L-Root": {name: "Rootkit",       section: "selfdefense"},
  "L-MC":   {name: "Multichannel",  section: "output"},
  "L-LF":   {name: "LiveFeed",      section: "output"},
  "L-MITRE":{name: "MITRE",         section: "intelligence"},
  "L-Resp": {name: "Response",      section: "response"},
  "L-Scor": {name: "Scoring",       section: "response"},
  "L-Rep":  {name: "Reports",       section: "output"},
  "L-Fore": {name: "Forensics",     section: "response"},
  "L-Hash": {name: "HashChain",     section: "data"},
  "L-Mock": {name: "Mocker",        section: "data"},
  "L-Voice":{name: "Voice",         section: "output"},
  "L-Bot":  {name: "Bot",           section: "output"},
  "L-Sync": {name: "Sync",          section: "output"},
  "L-Keep": {name: "Keepalive",     section: "selfdefense"},
  "L-Agent":{name: "Agent",         section: "output"},
};

const SECTION_NAMES = {
  ingress: 'INGRESS',
  intelligence: 'INTEL',
  response: 'RESPONSE',
  output: 'OUTPUT',
  data: 'DATA',
  network: 'NETWORK',
  selfdefense: 'SELF-DEF',
  identity: 'IDENTITY',
  application: 'APP',
};

let LIVE = { layers: [], stats: {} };

// ─── Circuit Board ───
function renderCircuit() {
  const el = document.getElementById('circuit');
  if (!el) return;
  
  const layers = LIVE.layers;
  
  const stages = [
    { label: 'NET',  name: 'اینترنت',     filter: [] },
    { label: 'ING',  name: 'Ingress',     filter: layers.filter(l => LAYER_META[l.id]?.section === 'ingress') },
    { label: 'INT',  name: 'Intelligence',filter: layers.filter(l => LAYER_META[l.id]?.section === 'intelligence') },
    { label: 'RES',  name: 'Response',    filter: layers.filter(l => LAYER_META[l.id]?.section === 'response') },
    { label: 'OUT',  name: 'Output',      filter: layers.filter(l => LAYER_META[l.id]?.section === 'output' ) },
  ];
  
  let html = '';
  stages.forEach((stage, i) => {
    if (i > 0) {
      const hasRed = stage.filter.some(l => l.color === 'red');
      html += `<div class="arrow ${hasRed ? 'danger' : ''}">→</div>`;
    }
    
    let stageColor = 'green';
    const total = stage.filter.length;
    const active = stage.filter.filter(l => l.color === 'green').length;
    
    if (total > 0) {
      const colors = stage.filter.map(l => l.color);
      if (colors.includes('red')) stageColor = 'red';
      else if (colors.includes('orange')) stageColor = 'orange';
      else if (colors.every(c => c === 'yellow')) stageColor = 'yellow';
    }
    
    html += `
      <div class="stage">
        <div class="stage-label">${stage.label}</div>
        <div class="bulb ${stageColor}"></div>
        <div class="stage-name">${stage.name}</div>
        <div class="stage-count">${total ? active + '/' + total : '—'}</div>
      </div>
    `;
  });
  
  el.innerHTML = html;
}

// ─── Stats ───
function renderStats() {
  const el = document.getElementById('stats');
  if (!el) return;
  
  const s = LIVE.stats;
  
  el.innerHTML = `
    <div class="stat-card green">
      <div class="stat-value">${s.green || 0}</div>
      <div class="stat-label">فعال</div>
    </div>
    <div class="stat-card yellow">
      <div class="stat-value">${s.yellow || 0}</div>
      <div class="stat-label">آماده</div>
    </div>
    <div class="stat-card red">
      <div class="stat-value">${s.red || 0}</div>
      <div class="stat-label">قطع</div>
    </div>
    <div class="stat-card blue">
      <div class="stat-value">${s.total || 0}</div>
      <div class="stat-label">کل</div>
    </div>
  `;
}

// ─── Lights Grid ───
function renderLayers() {
  const el = document.getElementById('layers-grid');
  const countEl = document.getElementById('layer-count');
  if (!el) return;
  
  if (countEl) countEl.textContent = `${LIVE.layers.length} لایه`;
  
  el.innerHTML = LIVE.layers.map(l => {
    const meta = LAYER_META[l.id] || { name: l.file, section: 'unknown' };
    return `
      <div class="light-node ${l.color}">
        <div class="node-bulb ${l.color}"></div>
        <div class="node-trace"></div>
        <div class="node-label section-${meta.section}">
          <div class="node-label-id">${l.id}</div>
          <div class="node-label-name">${meta.name}</div>
          <div class="node-label-section">${SECTION_NAMES[meta.section] || meta.section}</div>
        </div>
      </div>
    `;
  }).join('');
}

// ─── Clock ───
function tick() {
  const el = document.getElementById('clock');
  if (el) el.textContent = new Date().toLocaleTimeString('fa-IR', { hour12: false });
}

// ─── Load Live Data ───
async function load() {
  try {
    const data = await fetch('data/live.json?v=' + Date.now()).then(r => r.json());
    LIVE = data;
    renderCircuit();
    renderStats();
    renderLayers();
  } catch (e) {
    console.error('Load error:', e);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  tick();
  setInterval(tick, 1000);
  load();
  setInterval(load, 30000);  // هر ۳۰ ثانیه refresh
});
