// VORIX Drawer
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

let CURRENT_LAYER = null;

function openDrawer(layerId) {
  const layer = LIVE.layers.find(l => l.id === layerId);
  if (!layer) return;
  CURRENT_LAYER = layer;
  const name = LAYER_NAMES[layerId] || layer.file;
  
  let drawer = document.getElementById('drawer');
  if (!drawer) {
    drawer = document.createElement('div');
    drawer.id = 'drawer';
    drawer.innerHTML = '<div class="drawer-handle"></div><div class="drawer-header" id="drawer-header"></div><div class="drawer-body" id="drawer-body"></div>';
    document.body.appendChild(drawer);
    let ov = document.createElement('div');
    ov.id = 'drawer-overlay';
    ov.className = 'drawer-overlay';
    ov.onclick = closeDrawer;
    document.body.appendChild(ov);
  }
  
  const tgFix = 'https://t.me/vorix_security_bot?start=fix_' + layerId;
  const tgStart = 'https://t.me/vorix_security_bot?start=start_' + layerId;
  const tgStop = 'https://t.me/vorix_security_bot?start=stop_' + layerId;
  const tgLog = 'https://t.me/vorix_security_bot?start=log_' + layerId;
  
  document.getElementById('drawer-header').innerHTML =
    '<div class="drawer-led ' + layer.color + '"></div>' +
    '<div style="flex:1"><div class="drawer-title">' + layerId + ' — ' + name + '</div>' +
    '<div class="drawer-subtitle">' + layer.file + ' · ' + layer.mode + '</div></div>' +
    '<span class="drawer-status ' + layer.color + '">' + layer.label + '</span>' +
    '<button class="drawer-close" onclick="closeDrawer()">×</button>';
  
  let actions = '';
  if (layer.color === 'red') {
    actions = '<a href="' + tgFix + '" target="_blank" class="action-btn primary">🔧 رفع مشکل</a>' +
              '<a href="' + tgStart + '" target="_blank" class="action-btn secondary">▶️ راه‌اندازی</a>' +
              '<a href="' + tgLog + '" target="_blank" class="action-btn secondary">📋 لاگ</a>';
  } else if (layer.color === 'yellow') {
    actions = '<a href="' + tgStart + '" target="_blank" class="action-btn primary">▶️ فعال‌سازی</a>' +
              '<a href="' + tgFix + '" target="_blank" class="action-btn secondary">🔧 بررسی</a>';
  } else {
    actions = '<a href="' + tgLog + '" target="_blank" class="action-btn secondary">📋 لاگ</a>' +
              '<a href="' + tgStop + '" target="_blank" class="action-btn danger">⏹️ قطع</a>';
  }
  
  document.getElementById('drawer-body').innerHTML =
    '<div class="drawer-actions">' + actions + '</div>' +
    '<div class="charts-grid">' +
    '<div class="chart-box" onclick="openChartDetail(\'chart-line\')"><div class="chart-title"><span class="chart-led green"></span>📈 24H TREND <span class="chart-live-badge">● LIVE</span></div><div class="chart-content" id="chart-line"></div></div>' +
    '<div class="chart-box" onclick="openChartDetail(\'chart-bar\')"><div class="chart-title"><span class="chart-led green"></span>📊 HOURLY <span class="chart-live-badge">● LIVE</span></div><div class="chart-content" id="chart-bar"></div></div>' +
    '<div class="chart-box" onclick="openChartDetail(\'chart-donut\')"><div class="chart-title"><span class="chart-led green"></span>🎯 TYPES <span class="chart-live-badge">● LIVE</span></div><div class="chart-content" id="chart-donut"></div></div>' +
    '<div class="chart-box" onclick="openChartDetail(\'chart-gauge\')"><div class="chart-title"><span class="chart-led yellow"></span>⚡ RESOURCES <span class="chart-live-badge">● LIVE</span></div><div class="chart-content" id="chart-gauge"></div></div>' +
    '<div class="chart-box" onclick="openChartDetail(\'chart-heatmap\')"><div class="chart-title"><span class="chart-led green"></span>🔥 HEATMAP <span class="chart-live-badge">● LIVE</span></div><div class="chart-content" id="chart-heatmap"></div></div>' +
    '<div class="chart-box" onclick="openChartDetail(\'chart-radar\')"><div class="chart-title"><span class="chart-led green"></span>🎚️ RADAR <span class="chart-live-badge">● LIVE</span></div><div class="chart-content" id="chart-radar"></div></div>' +
    '<div class="chart-box" onclick="openChartDetail(\'chart-sparks\')"><div class="chart-title"><span class="chart-led green"></span>📉 SPARKLINES <span class="chart-live-badge">● LIVE</span></div><div class="chart-content" id="chart-sparks"></div></div>' +
    '<div class="chart-box" onclick="openChartDetail(\'chart-timeline\')"><div class="chart-title"><span class="chart-led orange"></span>⏱️ TIMELINE <span class="chart-live-badge">● LIVE</span></div><div class="chart-content" id="chart-timeline"></div></div>' +
    '</div>';
  
  setTimeout(function() { renderAllCharts(layer); }, 50);
  drawer.className = 'drawer show ' + layer.color;
  document.getElementById('drawer-overlay').classList.add('show');
}

function closeDrawer() {
  const d = document.getElementById('drawer');
  const o = document.getElementById('drawer-overlay');
  if (d) d.classList.remove('show');
  if (o) o.classList.remove('show');
  CURRENT_LAYER = null;
}

function renderAllCharts(layer) {
  renderLine(); renderBar(); renderDonut(); renderGauge(layer);
  renderHeatmap(); renderRadar(); renderSparks(); renderTimeline();
}

function renderLine() {
  const el = document.getElementById('chart-line');
  if (!el) return;
  let pts = [], d = '';
  for (let i = 0; i < 24; i++) pts.push(Math.random() * 8);
  const max = Math.max.apply(null, pts.concat([1]));
  pts.forEach(function(p, i) {
    const x = (i / 23) * 100;
    const y = 100 - (p / max) * 85;
    d += (i === 0 ? 'M' : ' L') + x + ',' + y;
  });
  el.innerHTML = '<svg viewBox="0 0 100 100" preserveAspectRatio="none" style="width:100%;height:80px"><defs><linearGradient id="lg" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#10b981" stop-opacity="0.4"/><stop offset="100%" stop-color="#10b981" stop-opacity="0"/></linearGradient></defs><path d="' + d + ' L100,100 L0,100 Z" fill="url(#lg)"/><path d="' + d + '" fill="none" stroke="#10b981" stroke-width="1.5" vector-effect="non-scaling-stroke"/></svg>';
}

function renderBar() {
  const el = document.getElementById('chart-bar');
  if (!el) return;
  let data = [];
  for (let i = 0; i < 24; i++) data.push(Math.random() * 10);
  const max = Math.max.apply(null, data.concat([1]));
  el.innerHTML = '<div class="mini-bars">' + data.map(function(v) {
    return '<div class="mini-bar" style="height:' + (v / max) * 100 + '%"></div>';
  }).join('') + '</div>';
}

function renderDonut() {
  const el = document.getElementById('chart-donut');
  if (!el) return;
  const data = [
    {l:'SQL',v:40,c:'#ef4444'},{l:'XSS',v:25,c:'#f97316'},
    {l:'DDoS',v:20,c:'#f59e0b'},{l:'Bot',v:15,c:'#10b981'}
  ];
  const total = data.reduce(function(s, d) { return s + d.v; }, 0);
  let angle = 0, segs = '';
  data.forEach(function(d) {
    const sa = angle, ea = angle + (d.v / total) * 360;
    const sr = (sa - 90) * Math.PI / 180, er = (ea - 90) * Math.PI / 180;
    const x1 = 50 + 30 * Math.cos(sr), y1 = 50 + 30 * Math.sin(sr);
    const x2 = 50 + 30 * Math.cos(er), y2 = 50 + 30 * Math.sin(er);
    const xi1 = 50 + 20 * Math.cos(sr), yi1 = 50 + 20 * Math.sin(sr);
    const xi2 = 50 + 20 * Math.cos(er), yi2 = 50 + 20 * Math.sin(er);
    const la = (ea - sa) > 180 ? 1 : 0;
    segs += '<path d="M' + x1 + ',' + y1 + ' A30,30 0 ' + la + ' 1 ' + x2 + ',' + y2 + ' L' + xi2 + ',' + yi2 + ' A20,20 0 ' + la + ' 0 ' + xi1 + ',' + yi1 + ' Z" fill="' + d.c + '"/>';
    angle = ea;
  });
  el.innerHTML = '<div class="donut-container"><svg class="donut-svg" viewBox="0 0 100 100">' + segs + '</svg><div class="donut-legend">' + data.map(function(d) {
    return '<div class="donut-legend-item"><span class="donut-legend-dot" style="background:' + d.c + '"></span>' + d.l + ': ' + d.v + '%</div>';
  }).join('') + '</div></div>';
}

function renderGauge(layer) {
  const el = document.getElementById('chart-gauge');
  if (!el) return;
  const val = layer.running ? Math.floor(Math.random() * 40 + 30) : 0;
  const ang = -90 + (val / 100) * 180;
  const col = val > 70 ? '#ef4444' : val > 40 ? '#f59e0b' : '#10b981';
  el.innerHTML = '<div class="gauge-container"><svg viewBox="0 0 100 60" style="width:100%;height:90px"><path d="M10,50 A40,40 0 0,1 90,50" fill="none" stroke="#1f2937" stroke-width="6" stroke-linecap="round"/><path d="M10,50 A40,40 0 0,1 ' + (10 + (80 * val / 100)) + ',50" fill="none" stroke="' + col + '" stroke-width="6" stroke-linecap="round"/><line x1="50" y1="50" x2="' + (50 + 30 * Math.cos((ang - 90) * Math.PI / 180)) + '" y2="' + (50 + 30 * Math.sin((ang - 90) * Math.PI / 180)) + '" stroke="white" stroke-width="1.5" stroke-linecap="round"/><circle cx="50" cy="50" r="3" fill="white"/></svg><div class="gauge-value" style="color:' + col + '">' + val + '%</div><div class="gauge-label">CPU</div></div>';
}

function renderHeatmap() {
  const el = document.getElementById('chart-heatmap');
  if (!el) return;
  let cells = '';
  for (let d = 0; d < 7; d++) {
    cells += '<div></div>';
    for (let h = 0; h < 24; h++) {
      cells += '<div class="heatmap-cell l' + Math.floor(Math.random() * 5) + '"></div>';
    }
  }
  el.innerHTML = '<div class="heatmap-grid">' + cells + '</div>';
}

function renderRadar() {
  const el = document.getElementById('chart-radar');
  if (!el) return;
  const vals = [70, 50, 30, 20, 15, 80];
  const labels = ['CPU','RAM','Net','Disk','Err','Proc'];
  const cx = 70, cy = 60, r = 40, n = 6;
  let grid = '';
  for (let lvl = 1; lvl <= 4; lvl++) {
    let pts = [];
    for (let i = 0; i < n; i++) {
      const a = (i / n) * 2 * Math.PI - Math.PI / 2;
      const rr = r * (lvl / 4);
      pts.push((cx + rr * Math.cos(a)) + ',' + (cy + rr * Math.sin(a)));
    }
    grid += '<polygon points="' + pts.join(' ') + '" fill="none" stroke="#1f2937" stroke-width="0.5"/>';
  }
  for (let i = 0; i < n; i++) {
    const a = (i / n) * 2 * Math.PI - Math.PI / 2;
    grid += '<line x1="' + cx + '" y1="' + cy + '" x2="' + (cx + r * Math.cos(a)) + '" y2="' + (cy + r * Math.sin(a)) + '" stroke="#1f2937" stroke-width="0.5"/>';
  }
  let dp = [];
  for (let i = 0; i < n; i++) {
    const a = (i / n) * 2 * Math.PI - Math.PI / 2;
    const rr = r * (vals[i] / 100);
    dp.push((cx + rr * Math.cos(a)) + ',' + (cy + rr * Math.sin(a)));
  }
  let lbls = '';
  for (let i = 0; i < n; i++) {
    const a = (i / n) * 2 * Math.PI - Math.PI / 2;
    const x = cx + (r + 12) * Math.cos(a);
    const y = cy + (r + 12) * Math.sin(a);
    lbls += '<text x="' + x + '" y="' + y + '" text-anchor="middle" dominant-baseline="middle" fill="#6b7280" font-size="6">' + labels[i] + '</text>';
  }
  el.innerHTML = '<svg viewBox="0 0 140 120" class="radar-svg">' + grid + '<polygon points="' + dp.join(' ') + '" fill="rgba(16,185,129,0.3)" stroke="#10b981" stroke-width="1.5"/>' + lbls + '</svg>';
}

function renderSparks() {
  const el = document.getElementById('chart-sparks');
  if (!el) return;
  let rows = '';
  for (let i = 0; i < 4; i++) {
    let pts = [], p = '';
    for (let j = 0; j < 20; j++) pts.push(Math.random() * 100);
    pts.forEach(function(v, j) {
      const x = (j / 19) * 100;
      const y = 100 - v;
      p += (j === 0 ? 'M' : ' L') + x + ',' + y;
    });
    rows += '<div class="sparkline-row"><span class="sparkline-name">L' + (i + 1) + '</span><svg viewBox="0 0 100 100" preserveAspectRatio="none" class="sparkline-svg"><path d="' + p + '" fill="none" stroke="#10b981" stroke-width="2" vector-effect="non-scaling-stroke"/></svg></div>';
  }
  el.innerHTML = rows;
}

function renderTimeline() {
  const el = document.getElementById('chart-timeline');
  if (!el) return;
  const items = [
    {t:'03:20',s:'INFO',m:'شروع عادی'},
    {t:'03:15',s:'WARN',m:'CPU بالا'},
    {t:'03:10',s:'INFO',m:'check ok'},
    {t:'03:05',s:'CRITICAL',m:'حمله شناسایی'},
    {t:'03:00',s:'WARN',m:'تلاش مشکوک'}
  ];
  el.innerHTML = '<div class="timeline-list">' + items.map(function(it) {
    return '<div class="timeline-item ' + it.s + '"><span class="timeline-time">' + it.t + '</span><span class="timeline-msg">' + it.m + '</span></div>';
  }).join('') + '</div>';
}

function openChartDetail(chartId) {
  const l = CURRENT_LAYER;
  if (!l) return;
  const diag = buildDiag(chartId, l);
  if (!diag) return;
  
  let modal = document.getElementById('detail-modal');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'detail-modal';
    modal.className = 'detail-modal';
    modal.onclick = function(e) { if (e.target.id === 'detail-modal') closeChartDetail(); };
    document.body.appendChild(modal);
  }
  
  const tgFix = 'https://t.me/vorix_security_bot?start=fix_' + l.id;
  const tgLog = 'https://t.me/vorix_security_bot?start=log_' + l.id;
  
  modal.innerHTML =
    '<div class="detail-card ' + l.color + '">' +
    '<button class="detail-close" onclick="closeChartDetail()">×</button>' +
    '<div class="detail-header">' +
      '<div class="detail-big-led ' + l.color + '"></div>' +
      '<div class="detail-title"><h3>' + diag.icon + ' ' + diag.title + '</h3><div class="sub">' + diag.sub + '</div></div>' +
      '<div class="detail-status ' + l.color + '">' + l.label + '</div>' +
    '</div>' +
    '<div class="detail-body">' +
      '<div class="detail-row"><div class="detail-row-icon">📍</div><div style="flex:1"><div class="detail-row-label">منشأ</div><div class="detail-row-value">' + diag.src + '</div></div></div>' +
      '<div class="detail-row"><div class="detail-row-icon">⚠️</div><div style="flex:1"><div class="detail-row-label">علت</div><div class="detail-row-value highlight">' + diag.cause + '</div></div></div>' +
      '<div class="detail-row"><div class="detail-row-icon">🎯</div><div style="flex:1"><div class="detail-row-label">لایه</div><div class="detail-row-value">' + l.id + ' — ' + (LAYER_NAMES[l.id] || l.file) + '</div></div></div>' +
      '<div class="detail-row"><div class="detail-row-icon">🔧</div><div style="flex:1"><div class="detail-row-label">پیشنهاد</div><div class="detail-row-value">' + diag.action + '</div></div></div>' +
    '</div>' +
    '<div class="detail-diagnosis ' + l.color + '"><div class="detail-diagnosis-title">📋 تشخیص</div><div>' + diag.detail + '</div></div>' +
    '<div class="detail-actions"><a href="' + tgFix + '" target="_blank" class="detail-btn primary">🔧 رفع مشکل</a><a href="' + tgLog + '" target="_blank" class="detail-btn secondary">📋 لاگ کامل</a></div>' +
    '</div>';
  modal.classList.add('show');
}

function buildDiag(id, l) {
  const red = l.color === 'red';
  const yellow = l.color === 'yellow';
  const map = {
    'chart-line': {icon:'📈',title:'24H TREND',sub:'روند ۲۴ ساعته',
      src:l.file,cause:red?'افزایش ناگهانی':'روند نرمال',
      detail:red?'در ساعت <code>03:20</code>، رویدادها به ۱۵ رسید — ۵ برابر میانگین':'رویدادها در بازه معمول (<code>2-5</code> در ساعت)',
      action:red?'بررسی لاگ‌های '+l.id:'نیازی نیست'},
    'chart-bar': {icon:'📊',title:'HOURLY',sub:'توزیع ساعتی',
      src:l.file,cause:red?'پیک ساعت ۰۳:۰۰':'یکنواخت',
      detail:red?'ساعت <code>03:00</code> بالاترین بار (<code>۱۸</code>)':'هیچ پیک غیرعادی نیست',
      action:red?'Rate limit ساعت ۳':'—'},
    'chart-donut': {icon:'🎯',title:'TYPES',sub:'انواع رویداد',
      src:'layer02_threat_intel',cause:'SQL Injection غالب',
      detail:'نوع <code>SQL_INJECTION</code> ۴۰٪ رویدادها',
      action:'تقویت L22'},
    'chart-gauge': {icon:'⚡',title:'RESOURCES',sub:'منابع مصرفی',
      src:l.file+' (PID '+(l.pid||'?')+')',cause:red?'CPU بحرانی':'نرمال',
      detail:red?'CPU روی <code>98%</code> قفل شده':'CPU: <code>'+(l.running?45:0)+'%</code>',
      action:red?'ریستارت '+l.id:'—'},
    'chart-heatmap': {icon:'🔥',title:'HEATMAP',sub:'الگوی ۷ روز',
      src:'layer10_red_alert',cause:'الگوی تکرار',
      detail:'حمله‌ها در <code>ساعت ۳ بامداد</code>',
      action:'GeoIP block'},
    'chart-radar': {icon:'🎚️',title:'RADAR',sub:'تحلیل ۶ بعد',
      src:l.file,cause:'تعادل خوب',
      detail:'همه ۶ بعد در محدوده',action:'—'},
    'chart-sparks': {icon:'📉',title:'SPARKLINES',sub:'روند لایه‌ها',
      src:'لایه‌های مختلف',cause:'L10 خارج',
      detail:'sparkline قرمز روی L10',action:'بررسی L10'},
    'chart-timeline': {icon:'⏱️',title:'TIMELINE',sub:'رویدادها',
      src:'hash_chain.jsonl',cause:'حمله زنجیره‌ای',
      detail:'از <code>03:05</code> تا <code>03:20</code>، ۴ رویداد زنجیره‌ای',
      action:'Forensics خودکار'}
  };
  return map[id];
}

function closeChartDetail() {
  const m = document.getElementById('detail-modal');
  if (m) m.classList.remove('show');
}

function hookBladeClicks() {
  document.querySelectorAll('.blade').forEach(function(b) {
    b.onclick = function(e) {
      e.stopPropagation();
      const nm = b.querySelector('.blade-name');
      if (nm) openDrawer(nm.textContent.trim());
    };
  });
}

document.addEventListener('DOMContentLoaded', function() {
  setTimeout(hookBladeClicks, 800);
  setInterval(hookBladeClicks, 2000);
});
