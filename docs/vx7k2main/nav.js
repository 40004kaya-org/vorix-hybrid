(function() {
  var cur = location.pathname.split('/').pop() || 'index.html';
  var menu = [
    {h:'index.html',l:'داشبورد'},
    {h:'metrics.html',l:'متریک'},
    {h:'discover.html',l:'Discover'},{h:'logs.html',l:'لاگ‌ها'},
    {h:'events.html',l:'رویدادها'},
    {h:'layers.html',l:'لایه‌ها'}
  ];
  var html='<div class="vx-nav"><div class="vx-nav-links">';
  menu.forEach(function(m){
    var a=(m.h===cur)?' active':'';
    html+='<a class="vx-nav-link'+a+'" href="'+m.h+'">'+m.l+'</a>';
  });
  html+='</div><div class="vx-live" id="vx-live"><span class="vx-led"></span><span class="vx-live-text">LIVE</span></div></div>';
  var s=document.createElement('style');
  s.textContent=`
.vx-nav{display:flex;align-items:center;justify-content:space-between;background:#0a0e1a;border-bottom:1px solid #10b981;padding:0 4px;margin:-10px -10px 12px -10px;gap:6px;overflow-x:auto;scrollbar-width:none}
.vx-nav::-webkit-scrollbar{display:none}
.vx-nav-links{display:flex;gap:2px;flex-shrink:0}
.vx-nav-link{display:inline-block;padding:10px 12px;color:#6b7280;text-decoration:none;font-size:12px;font-family:ui-monospace,monospace;border-bottom:2px solid transparent;white-space:nowrap}
.vx-nav-link:hover{color:#10b981}
.vx-nav-link.active{color:#10b981;border-bottom-color:#10b981;font-weight:bold}
.vx-live{display:flex;align-items:center;gap:5px;padding:6px 10px;margin-left:auto;background:#0a1a15;border:1px solid #10b981;border-radius:12px;flex-shrink:0;font-size:10px;font-family:ui-monospace,monospace;color:#10b981;letter-spacing:1px}
.vx-led{width:7px;height:7px;border-radius:50%;background:#10b981;box-shadow:0 0 6px #10b981,0 0 12px #10b981;animation:vxp 1.8s ease-in-out infinite}
.vx-live.stale .vx-led{background:#f59e0b;box-shadow:0 0 6px #f59e0b;animation:none}
.vx-live.dead .vx-led{background:#ef4444;box-shadow:0 0 6px #ef4444;animation:none}
@keyframes vxp{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.4;transform:scale(.85)}}
`;
  document.head.appendChild(s);
  document.body.insertAdjacentHTML('afterbegin',html);
  function up(){
    var el=document.getElementById('vx-live');if(!el)return;
    fetch('../data/live.json?v='+Date.now()).then(r=>r.json()).then(function(d){
      var age=(Date.now()-new Date(d.ts).getTime())/1000;
      el.className='vx-live';
      var t=el.querySelector('.vx-live-text');
      if(age<180)t.textContent='LIVE';
      else if(age<600){el.classList.add('stale');t.textContent='STALE';}
      else{el.classList.add('dead');t.textContent='OFFLINE';}
    }).catch(function(){
      el.className='vx-live dead';
      el.querySelector('.vx-live-text').textContent='OFFLINE';
    });
  }
  up();setInterval(up,15000);
})();
