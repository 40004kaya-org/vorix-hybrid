(function() {
  var cur = location.pathname.split('/').pop() || 'index.html';
  var menu = [
    {h:'index.html',      l:'مادر'},
    {h:'security.html',   l:'امنیت'},
    {h:'shop.html',       l:'فروشگاه'},
    {h:'shop-board.html', l:'برد فروشگاه'},
    {h:'world.html',      l:'جهانی'},
    {h:'cybermap.html',   l:'زنده'},
    {h:'discover.html',   l:'کشف'},
    {h:'mitre.html',      l:'MITRE'},
    {h:'sentinel.html',   l:'Sentinel'},
    {h:'alerts.html',     l:'هشدار'},
    {h:'livetail.html',   l:'Live'},
    {h:'metrics.html',    l:'متریک'},
    {h:'logs.html',       l:'لاگ'},
    {h:'layers.html',     l:'لایه'},
    {h:'events.html',     l:'رویداد'},
    {h:'attacks.html',    l:'حمله'},
    {h:'map.html',        l:'نقشه'},
    {h:'system.html',     l:'سیستم'}
  ];
  var html = '<div class="vx-nav"><div class="vx-nav-links">';
  menu.forEach(function(m) {
    var a = (m.h === cur) ? ' active' : '';
    html += '<a class="vx-nav-link' + a + '" href="' + m.h + '">' + m.l + '</a>';
  });
  html += '</div><div class="vx-live" id="vx-live"><span class="vx-led"></span><span class="vx-live-text">LIVE</span></div></div>';
  var st = document.createElement('style');
  st.textContent = '.vx-nav{display:flex;align-items:center;justify-content:space-between;background:#0a0e1a;border-bottom:1px solid #1e293b;padding:0 4px;margin:-10px -10px 12px -10px;gap:6px;overflow-x:auto;scrollbar-width:none}.vx-nav::-webkit-scrollbar{display:none}.vx-nav-links{display:flex;gap:0;flex-shrink:0}.vx-nav-link{display:inline-block;padding:10px 10px;color:#6b7280;text-decoration:none;font-size:11px;font-family:monospace;border-bottom:2px solid transparent;white-space:nowrap;transition:color .15s}.vx-nav-link:hover{color:#3b82f6;background:rgba(59,130,246,.05)}.vx-nav-link.active{color:#3b82f6;border-bottom-color:#3b82f6;font-weight:bold}.vx-live{display:flex;align-items:center;gap:5px;padding:6px 10px;margin-left:auto;background:#0a1a15;border:1px solid #059669;border-radius:12px;flex-shrink:0;font-size:10px;font-family:monospace;color:#059669;letter-spacing:1px}.vx-led{width:7px;height:7px;border-radius:50%;background:#059669;box-shadow:0 0 6px #059669;animation:vxp 1.8s infinite}.vx-live.stale .vx-led{background:#f59e0b;box-shadow:0 0 6px #f59e0b;animation:none}.vx-live.dead .vx-led{background:#ef4444;animation:none}@keyframes vxp{50%{opacity:.4}}';
  document.head.appendChild(st);
  document.body.insertAdjacentHTML('afterbegin', html);
  function up(){
    var el = document.getElementById('vx-live'); if (!el) return;
    fetch('../data/live.json?v=' + Date.now()).then(r=>r.json()).then(function(d) {
      var age = (Date.now() - new Date(d.ts).getTime()) / 1000;
      el.className = 'vx-live';
      var t = el.querySelector('.vx-live-text');
      if (age < 300) t.textContent = 'LIVE';
      else if (age < 900) { el.classList.add('stale'); t.textContent = 'STALE'; }
      else { el.classList.add('dead'); t.textContent = 'OFFLINE'; }
    }).catch(function() { el.className='vx-live dead'; });
  }
  up(); setInterval(up, 15000);
})();
