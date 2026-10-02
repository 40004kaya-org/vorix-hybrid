// ══════════════════════════════════════════
// VORIX Dashboard — Main JS
// ══════════════════════════════════════════

const STATE = {
  stats: {},
  events: [],
  layers: [],
  currentPage: 'dashboard',
  filters: { severity: 'ALL', type: 'ALL', search: '' },
  chart: null,
  pieChart: null,
};

// ─── LAYERS ───
const LAYER_LIST = [
  { name: 'L01 Anti-Kill', status: 'active' },
  { name: 'L03 Behavioral', status: 'active' },
  { name: 'L04 Auto-Block', status: 'active' },
  { name: 'L06 GeoIP', status: 'active' },
  { name: 'L08 Net Monitor', status: 'active' },
  { name: 'L09 Rate Limit', status: 'active' },
  { name: 'L10 Red Alert', status: 'active' },
  { name: 'L17 Watchdog', status: 'active' },
  { name: 'L19 Password Leak', status: 'active' },
  { name: 'L21 ML Anomaly', status: 'active' },
  { name: 'L25 SSL Monitor', status: 'active' },
  { name: 'L29-30 Identity', status: 'active' },
  { name: 'L-FIM', status: 'active' },
  { name: 'L-Rootkit', status: 'active' },
  { name: 'L-Multichannel', status: 'active' },
];

// ─── HELPERS ───
function fmtTime(ts) {
  try {
    const d = new Date(ts);
    return d.toLocaleString('fa-IR', { hour12: false });
  } catch(e) { return ts || '—'; }
}

function fmtTimeShort(ts) {
  try {
    const d = new Date(ts);
    const diff = (Date.now() - d.getTime()) / 1000;
    if (diff < 60) return 'همین الان';
    if (diff < 3600) return Math.floor(diff/60) + ' دقیقه پیش';
    if (diff < 86400) return Math.floor(diff/3600) + ' ساعت پیش';
    return Math.floor(diff/86400) + ' روز پیش';
  } catch(e) { return ts || '—'; }
}

function getEventType(e) {
  return e.event_type || e.event || e.attack || e.type || 'UNKNOWN';
}

function getEventSeverity(e) {
  const sev = (e.severity || e.level || 'INFO').toUpperCase();
  if (sev === 'WARNING') return 'WARN';
  if (sev === 'ERROR' || sev === 'CRITICAL') return 'CRITICAL';
  return sev;
}

function getEventMessage(e) {
  if (e.message) return e.message;
  if (e.event) return e.event;
  if (e.event_type) return e.event_type;
  if (e.attack) return e.attack + (e.ip ? ' از ' + e.ip : '');
  return JSON.stringify(e).slice(0, 100);
}

// ─── NAVIGATION ───
function navigate(page) {
  STATE.currentPage = page;
  document.querySelectorAll('.nav-link').forEach(l => {
    l.classList.toggle('active', l.dataset.page === page);
  });
  document.querySelectorAll('[data-page-content]').forEach(p => {
    p.classList.toggle('hidden', p.dataset.pageContent !== page);
  });
  if (page === 'dashboard') renderCharts();
}

// ─── LOAD DATA ───
async function loadData() {
  try {
    const bust = '?v=' + Date.now();
    const [stats, events] = await Promise.all([
      fetch('stats.json' + bust).then(r => r.json()),
      fetch('events.json' + bust).then(r => r.json()),
    ]);
    STATE.stats = stats;
    STATE.events = events;
    renderAll();
  } catch(e) {
    console.error('Load error:', e);
  }
}

// ─── RENDER ───
function renderAll() {
  renderStats();
  renderEvents();
  renderLayers();
  renderCharts();
  updateClock();
}

function renderStats() {
  const s = STATE.stats;
  document.getElementById('stat-total').textContent = s.total || 0;
  document.getElementById('stat-critical').textContent = s.critical || 0;
  document.getElementById('stat-blocked').textContent = s.blocked || 0;
  document.getElementById('stat-status').textContent = 'فعال';
  document.getElementById('last-update').textContent = fmtTime(s.last_update);
}

function renderEvents() {
  const container = document.getElementById('events-list');
  const allContainer = document.getElementById('all-events-list');
  
  let events = STATE.events.slice().reverse();
  
  // Dashboard: only 10 latest
  const latest = events.slice(0, 10);
  container.innerHTML = latest.length 
    ? latest.map(renderEventHTML).join('')
    : '<div class="empty"><div class="empty-icon">📭</div>رویدادی ثبت نشده</div>';
  
  // All events: apply filters
  let filtered = events;
  if (STATE.filters.severity !== 'ALL') {
    filtered = filtered.filter(e => getEventSeverity(e) === STATE.filters.severity);
  }
  if (STATE.filters.search) {
    const q = STATE.filters.search.toLowerCase();
    filtered = filtered.filter(e => 
      getEventMessage(e).toLowerCase().includes(q) ||
      getEventType(e).toLowerCase().includes(q) ||
      JSON.stringify(e).toLowerCase().includes(q)
    );
  }
  
  allContainer.innerHTML = filtered.length
    ? filtered.map(renderEventHTML).join('')
    : '<div class="empty"><div class="empty-icon">🔍</div>رویدادی مطابق فیلتر پیدا نشد</div>';
  
  // Add click handlers
  document.querySelectorAll('.event').forEach(el => {
    el.onclick = () => showEventDetail(el.dataset.eventId);
  });
}

function renderEventHTML(e, i) {
  const sev = getEventSeverity(e);
  const type = getEventType(e);
  const ts = e.ts || e.timestamp || '';
  const msg = getEventMessage(e);
  const id = btoa(JSON.stringify(e)).slice(0, 20) + '-' + i;
  
  return `
    <div class="event ${sev}" data-event-id="${id}" data-event-json='${JSON.stringify(e).replace(/'/g, "&#39;")}'>
      <div class="event-header">
        <span class="event-type">${type}</span>
        <span class="event-time">${fmtTimeShort(ts)}</span>
      </div>
      <div class="event-msg">${msg}</div>
    </div>
  `;
}

function renderLayers() {
  const container = document.getElementById('layers-grid');
  container.innerHTML = LAYER_LIST.map(l => `
    <div class="layer-card">
      <div class="layer-icon"></div>
      <div class="layer-info">
        <div class="layer-name">${l.name}</div>
        <div class="layer-sub">${l.status === 'active' ? 'فعال' : 'غیرفعال'}</div>
      </div>
    </div>
  `).join('');
}

function renderCharts() {
  if (typeof Chart === 'undefined') return;
  
  // ─── LINE CHART: Events in last 7 days ───
  const ctx1 = document.getElementById('events-chart');
  if (ctx1) {
    const days = [];
    const counts = [];
    for (let i = 6; i >= 0; i--) {
      const d = new Date();
      d.setDate(d.getDate() - i);
      days.push(d.toLocaleDateString('fa-IR', { month: 'short', day: 'numeric' }));
      const dayStart = new Date(d).setHours(0,0,0,0);
      const dayEnd = dayStart + 86400000;
      const count = STATE.events.filter(e => {
        const t = new Date(e.ts || e.timestamp || 0).getTime();
        return t >= dayStart && t < dayEnd;
      }).length;
      counts.push(count);
    }
    
    if (STATE.chart) STATE.chart.destroy();
    STATE.chart = new Chart(ctx1, {
      type: 'line',
      data: {
        labels: days,
        datasets: [{
          label: 'رویدادها',
          data: counts,
          borderColor: '#10b981',
          backgroundColor: 'rgba(16,185,129,0.1)',
          tension: 0.4,
          fill: true,
          pointRadius: 4,
          pointHoverRadius: 6,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
        },
        scales: {
          x: {
            grid: { color: 'rgba(255,255,255,0.05)' },
            ticks: { color: '#9ca3af', font: { size: 10 } }
          },
          y: {
            grid: { color: 'rgba(255,255,255,0.05)' },
            ticks: { color: '#9ca3af', font: { size: 10 } },
            beginAtZero: true,
          }
        }
      }
    });
  }
  
  // ─── PIE CHART: Attack types ───
  const ctx2 = document.getElementById('types-chart');
  if (ctx2) {
    const types = {};
    STATE.events.forEach(e => {
      const t = getEventType(e);
      types[t] = (types[t] || 0) + 1;
    });
    const labels = Object.keys(types).slice(0, 6);
    const data = labels.map(l => types[l]);
    const colors = ['#ef4444', '#f59e0b', '#10b981', '#3b82f6', '#8b5cf6', '#06b6d4'];
    
    if (STATE.pieChart) STATE.pieChart.destroy();
    STATE.pieChart = new Chart(ctx2, {
      type: 'doughnut',
      data: {
        labels: labels.length ? labels : ['خالی'],
        datasets: [{
          data: data.length ? data : [1],
          backgroundColor: colors.slice(0, labels.length || 1),
          borderWidth: 0,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom',
            labels: { color: '#9ca3af', font: { size: 10 }, boxWidth: 10 }
          }
        }
      }
    });
  }
}

// ─── MODAL ───
function showEventDetail(id) {
  const el = document.querySelector(`[data-event-id="${id}"]`);
  if (!el) return;
  try {
    const e = JSON.parse(el.dataset.eventJson);
    const body = document.getElementById('modal-body');
    body.innerHTML = `
      <div style="margin-bottom:12px">
        <span class="badge ${getEventSeverity(e)}">${getEventSeverity(e)}</span>
      </div>
      <div style="margin-bottom:16px">
        <div style="color:var(--muted);font-size:12px;margin-bottom:4px">نوع</div>
        <div style="font-size:16px;font-weight:600">${getEventType(e)}</div>
      </div>
      <div style="margin-bottom:16px">
        <div style="color:var(--muted);font-size:12px;margin-bottom:4px">پیام</div>
        <div>${getEventMessage(e)}</div>
      </div>
      <div style="margin-bottom:16px">
        <div style="color:var(--muted);font-size:12px;margin-bottom:4px">زمان</div>
        <div>${fmtTime(e.ts || e.timestamp)}</div>
      </div>
      <div>
        <div style="color:var(--muted);font-size:12px;margin-bottom:4px">داده کامل</div>
        <div class="code-block">${JSON.stringify(e, null, 2)}</div>
      </div>
    `;
    document.getElementById('event-modal').classList.add('open');
  } catch(e) { console.error(e); }
}

function closeModal() {
  document.getElementById('event-modal').classList.remove('open');
}

// ─── CLOCK ───
function updateClock() {
  const el = document.getElementById('clock');
  if (el) el.textContent = new Date().toLocaleString('fa-IR', { hour12: false });
}

// ─── INIT ───
document.addEventListener('DOMContentLoaded', () => {
  // Nav
  document.querySelectorAll('.nav-link').forEach(l => {
    l.onclick = () => navigate(l.dataset.page);
  });
  
  // Filters
  document.querySelectorAll('.filter-btn[data-severity]').forEach(b => {
    b.onclick = () => {
      document.querySelectorAll('.filter-btn[data-severity]').forEach(x => x.classList.remove('active'));
      b.classList.add('active');
      STATE.filters.severity = b.dataset.severity;
      renderEvents();
    };
  });
  
  // Search
  const search = document.getElementById('search-input');
  if (search) {
    search.oninput = (e) => {
      STATE.filters.search = e.target.value;
      renderEvents();
    };
  }
  
  // Modal close
  document.getElementById('event-modal').onclick = (e) => {
    if (e.target.id === 'event-modal') closeModal();
  };
  
  // Initial load
  loadData();
  setInterval(loadData, 30000);
  setInterval(updateClock, 1000);
});
