// ══════════════════════════════════════════
// VORIX Dashboard v2 — Circuit Style
// ══════════════════════════════════════════

const LAYERS = [
  { id: 'L01', name: 'Anti-Kill',       file: 'layer01_selfdefense',       section: 'selfdefense' },
  { id: 'L02', name: 'Threat Intel',    file: 'layer02_threat_intel',      section: 'ingress' },
  { id: 'L03', name: 'Behavioral',      file: 'layer03_behavioral',        section: 'intelligence' },
  { id: 'L04', name: 'Auto-Block',      file: 'layer04_auto_block',        section: 'response' },
  { id: 'L05', name: 'Data Quarantine', file: 'layer05_data_quarantine',   section: 'data' },
  { id: 'L06', name: 'GeoIP Block',     file: 'layer06_geoip_block',       section: 'ingress' },
  { id: 'L07', name: 'Net Behavior',    file: 'layer07_network_behavior',  section: 'network' },
  { id: 'L08', name: 'Net Monitor',     file: 'layer08_network_monitor',   section: 'network' },
  { id: 'L09', name: 'Rate Limiter',    file: 'layer09_rate_limiter',      section: 'ingress' },
  { id: 'L10', name: 'Red Alert',       file: 'layer10_red_alert',         section: 'response' },
  { id: 'L11', name: 'DNS Sinkhole',    file: 'layer11_dns_sinkhole',      section: 'network' },
  { id: 'L12', name: 'Reverse DNS',     file: 'layer12_reverse_dns',       section: 'network' },
  { id: 'L13', name: 'UA Filter',       file: 'layer13_ua_filter',         section: 'ingress' },
  { id: 'L15', name: 'Fingerprint',     file: 'layer15_fingerprint',       section: 'ingress' },
  { id: 'L16', name: 'Killswitch',      file: 'layer16_killswitch',        section: 'selfdefense' },
  { id: 'L17', name: 'Watchdog',        file: 'layer17_watchdog',          section: 'selfdefense' },
  { id: 'L18', name: 'Backup Verifier', file: 'layer18_backup_verifier',   section: 'selfdefense' },
  { id: 'L19', name: 'Password Leak',   file: 'layer19_password_leak',     section: 'identity' },
  { id: 'L21', name: 'ML Anomaly',      file: 'layer21_ml_anomaly',        section: 'intelligence' },
  { id: 'L22', name: 'Header Analysis', file: 'layer22_header_analysis',   section: 'application' },
  { id: 'L23', name: 'Cookie Anomaly',  file: 'layer23_cookie_anomaly',    section: 'application' },
  { id: 'L24', name: 'Session Hijack',  file: 'layer24_session_hijack',    section: 'application' },
  { id: 'L25', name: 'SSL Monitor',     file: 'layer25_ssl_monitor',       section: 'network' },
  { id: 'L26', name: 'HSTS',            file: 'layer26_hsts',              section: 'application' },
  { id: 'L29', name: 'Identity',        file: 'layer29_30_identity',       section: 'identity' },
  { id: 'L31', name: 'Log Encryption',  file: 'layer31_log_encryption',    section: 'data' },
  { id: 'L-FIM', name: 'FIM',           file: 'layer_fim',                 section: 'selfdefense' },
  { id: 'L-Root', name: 'Rootkit',      file: 'layer_rootkit',             section: 'selfdefense' },
  { id: 'L-MC', name: 'Multichannel',   file: 'layer_multichannel',        section: 'output' },
  { id: 'L-LF', name: 'LiveFeed',       file: 'layer_livefeed',            section: 'output' },
  { id: 'L-MITRE', name: 'MITRE',       file: 'layer_mitre',               section: 'intelligence' },
  { id: 'L-Resp', name: 'Response',     file: 'layer_response',            section: 'response' },
  { id: 'L-Scor', name: 'Scoring',      file: 'layer_scoring',             section: 'response' },
  { id: 'L-Rep', name: 'Reports',       file: 'layer_reports',             section: 'output' },
  { id: 'L-Fore', name: 'Forensics',    file: 'layer_forensics',           section: 'response' },
  { id: 'L-Hash', name: 'HashChain',    file: 'layer_hashchain',           section: 'data' },
  { id: 'L-Mock', name: 'Mocker',       file: 'layer_mocker',              section: 'data' },
  { id: 'L-Voice', name: 'Voice',       file: 'layer_voice',               section: 'output' },
  { id: 'L-Bot',  name: 'Bot',          file: 'vorix_bot',                 section: 'output' },
  { id: 'L-Sync', name: 'Sync',         file: 'sync_loop',                 section: 'output' },
  { id: 'L-Keep', name: 'Keepalive',    file: 'keepalive',                 section: 'selfdefense' },
  { id: 'L-Agent', name: 'Agent',       file: 'agent',                     section: 'output' },
];

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

// ─── Circuit Board ───
function renderCircuit(layers) {
  const el = document.getElementById('circuit');
  if (!el) return;
  
  const stages = [
    { label: 'NET',  name: 'اینترنت',     filter: [] },
    { label: 'ING',  name: 'Ingress',     filter: layers.filter(l => l.section === 'ingress') },
    { label: 'INT',  name: 'Intelligence',filter: layers.filter(l => l.section === 'intelligence') },
    { label: 'RES',  name: 'Response',    filter: layers.filter(l => l.section === 'response') },
    { label: 'OUT',  name: 'Output',      filter: layers.filter(l => l.section === 'output' ) },
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
function renderStats(layers) {
  const el = document.getElementById('stats');
  if (!el) return;
  
  const c = {
    green:  layers.filter(l => l.color === 'green').length,
    yellow: layers.filter(l => l.color === 'yellow').length,
    red:    layers.filter(l => l.color === 'red').length,
    total:  layers.length,
  };
  
  el.innerHTML = `
    <div class="stat-card green">
      <div class="stat-value">${c.green}</div>
      <div class="stat-label">فعال</div>
    </div>
    <div class="stat-card yellow">
      <div class="stat-value">${c.yellow}</div>
      <div class="stat-label">آماده</div>
    </div>
    <div class="stat-card red">
      <div class="stat-value">${c.red}</div>
      <div class="stat-label">قطع</div>
    </div>
    <div class="stat-card blue">
      <div class="stat-value">${c.total}</div>
      <div class="stat-label">کل</div>
    </div>
  `;
}

// ─── Lights با خط اتصال ───
function renderLayers(layers) {
  const el = document.getElementById('layers-grid');
  const countEl = document.getElementById('layer-count');
  if (!el) return;
  
  if (countEl) countEl.textContent = `${layers.length} لایه`;
  
  el.innerHTML = layers.map(l => `
    <div class="light-node ${l.color}">
      <div class="node-bulb ${l.color}"></div>
      <div class="node-trace"></div>
      <div class="node-label section-${l.section}">
        <div class="node-label-id">${l.id}</div>
        <div class="node-label-name">${l.name}</div>
        <div class="node-label-section">${SECTION_NAMES[l.section] || l.section}</div>
      </div>
    </div>
  `).join('');
}

// ─── Clock ───
function tick() {
  const el = document.getElementById('clock');
  if (el) el.textContent = new Date().toLocaleTimeString('fa-IR', { hour12: false });
}

// ─── Load ───
async function load() {
  const mockRunning = new Set([
    'layer01_selfdefense','layer03_behavioral','layer04_auto_block',
    'layer06_geoip_block','layer08_network_monitor','layer09_rate_limiter',
    'layer10_red_alert','layer17_watchdog','layer19_password_leak',
    'layer21_ml_anomaly','layer25_ssl_monitor','layer29_30_identity',
    'layer_fim','layer_rootkit','layer_multichannel','layer_livefeed',
    'vorix_bot','sync_loop','keepalive','agent'
  ]);
  
  const onDemand = new Set([
    'layer02_threat_intel','layer05_data_quarantine','layer07_network_behavior',
    'layer11_dns_sinkhole','layer12_reverse_dns','layer13_ua_filter',
    'layer15_fingerprint','layer16_killswitch','layer18_backup_verifier',
    'layer22_header_analysis','layer23_cookie_anomaly','layer24_session_hijack',
    'layer26_hsts','layer31_log_encryption','layer_mitre','layer_response',
    'layer_scoring','layer_reports','layer_forensics','layer_hashchain',
    'layer_mocker','layer_voice'
  ]);
  
  const enriched = LAYERS.map(l => {
    if (mockRunning.has(l.file)) 
      return { ...l, color: 'green', running: true };
    if (onDemand.has(l.file)) 
      return { ...l, color: 'yellow', running: false, mode: 'on-demand' };
    return { ...l, color: 'red', running: false };
  });
  
  renderCircuit(enriched);
  renderStats(enriched);
  renderLayers(enriched);
}

document.addEventListener('DOMContentLoaded', () => {
  tick();
  setInterval(tick, 1000);
  load();
  setInterval(load, 30000);
});
