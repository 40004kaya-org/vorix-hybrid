
// ═══════════════════════════════════════════════════
//  VX-OPS — Fingerprint & Trap Engine
// ═══════════════════════════════════════════════════
(function() {
  'use strict';

  // ─── Fingerprint Collection ───
  function canvasFP() {
    try {
      const c = document.createElement('canvas');
      c.width = 200; c.height = 40;
      const ctx = c.getContext('2d');
      ctx.textBaseline = 'top';
      ctx.font = '14px Arial';
      ctx.fillStyle = '#f60';
      ctx.fillRect(125, 1, 62, 20);
      ctx.fillStyle = '#069';
      ctx.fillText('VX-OPS', 2, 15);
      ctx.fillStyle = 'rgba(102,204,0,0.7)';
      ctx.fillText('VX-OPS', 4, 17);
      return c.toDataURL().slice(-50);
    } catch(e) { return 'canvas-err'; }
  }

  function webglFP() {
    try {
      const c = document.createElement('canvas');
      const gl = c.getContext('webgl') || c.getContext('experimental-webgl');
      if (!gl) return 'no-webgl';
      const dbg = gl.getExtension('WEBGL_debug_renderer_info');
      const vendor = dbg ? gl.getParameter(dbg.UNMASKED_VENDOR_WEBGL) : 'v?';
      const renderer = dbg ? gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL) : 'r?';
      return vendor + '|' + renderer;
    } catch(e) { return 'webgl-err'; }
  }

  async function collect() {
    const fp = {};
    fp.t = Date.now();
    fp.u = navigator.userAgent;
    fp.l = navigator.language;
    fp.langs = (navigator.languages || []).join(',');
    fp.plat = navigator.platform;
    fp.hc = navigator.hardwareConcurrency || '?';
    fp.dm = navigator.deviceMemory || '?';
    fp.tp = navigator.maxTouchPoints || 0;
    fp.sw = screen.width;
    fp.sh = screen.height;
    fp.cd = screen.colorDepth;
    fp.dpr = window.devicePixelRatio || 1;
    fp.tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
    fp.tzo = new Date().getTimezoneOffset();
    fp.canvas = canvasFP();
    fp.webgl = webglFP();
    fp.cookie = navigator.cookieEnabled;
    fp.dnt = navigator.doNotTrack;
    fp.ref = document.referrer || 'direct';
    fp.url = location.href;
    fp.path = location.pathname;
    fp.viewport = window.innerWidth + 'x' + window.innerHeight;

    // Battery (async)
    try {
      if (navigator.getBattery) {
        const b = await navigator.getBattery();
        fp.batt = Math.round(b.level * 100) + '%';
        fp.battChg = b.charging;
      }
    } catch(e) {}

    // Connection
    if (navigator.connection) {
      fp.conn = navigator.connection.effectiveType;
      fp.down = navigator.connection.downlink;
    }

    // Fonts probe
    try {
      const fonts = ['Arial','Verdana','Courier','Times','Comic Sans MS','Impact'];
      const avail = [];
      fonts.forEach(f => {
        if (document.fonts && document.fonts.check) {
          try { if (document.fonts.check('12px "' + f + '"')) avail.push(f[0]); } catch(e) {}
        }
      });
      fp.fonts = avail.join('');
    } catch(e) {}

    return fp;
  }

  // ─── Local Storage of Traps ───
  function logTrap(event, extra) {
    try {
      const KEY = '_vxt';
      const arr = JSON.parse(localStorage.getItem(KEY) || '[]');
      arr.push({ ev: event, t: Date.now(), x: extra || null });
      if (arr.length > 200) arr.splice(0, arr.length - 200);
      localStorage.setItem(KEY, JSON.stringify(arr));
    } catch(e) {}
  }

  // ─── Public API ───
  window.VX = {
    fp: collect,
    log: logTrap,

    // Fire trap and try to send
    async trap(event, extra) {
      const fp = await collect();
      logTrap(event, { extra: extra, fp_summary: {
        ua: fp.u.slice(0, 60),
        tz: fp.tz,
        sw: fp.sw,
        sh: fp.sh,
        plat: fp.plat,
        conn: fp.conn,
        ref: fp.ref
      }});

      // Try to send to webhook if configured
      const hook = localStorage.getItem('_vxhook');
      if (hook) {
        try {
          await fetch(hook, {
            method: 'POST',
            mode: 'no-cors',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ event: event, extra: extra, fp: fp })
          });
        } catch(e) {}
      }

      return fp;
    }
  };

  // ─── Auto Fingerprint on every page load ───
  window.addEventListener('load', async () => {
    const fp = await collect();
    logTrap('page_load', { url: fp.url });
  });

})();
