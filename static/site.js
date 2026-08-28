/* ============================================================
   SICCE site.js v6 — Atelier motion layer
   Lenis · GSAP · Three.js sculptural specimen · custom cursor ·
   magnetic buttons · DX layer (curl export, response mirror,
   drag-drop, toasts). Every integration guarded; zero app.js edits.
   ============================================================ */
(function () {
  'use strict';

  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var isSmall = window.innerWidth < 900;
  var fine = window.matchMedia('(hover: hover) and (pointer: fine)').matches;

  /* ---------- LENIS ---------- */
  var lenis = null;
  if (!reduced && typeof Lenis !== 'undefined') {
    try {
      lenis = new Lenis({ duration: 1.15, easing: function (t) { return Math.min(1, 1.001 - Math.pow(2, -10 * t)); } });
      function raf(time) { lenis.raf(time); requestAnimationFrame(raf); }
      requestAnimationFrame(raf);
    } catch (e) { lenis = null; }
  }

  /* ---------- PROGRESS + NAV ---------- */
  var progress = document.getElementById('scroll-progress');
  var nav = document.getElementById('site-nav');
  function onScroll() {
    var h = document.documentElement.scrollHeight - window.innerHeight;
    if (progress && h > 0) progress.style.width = ((window.scrollY / h) * 100) + '%';
    if (nav) nav.classList.toggle('is-scrolled', window.scrollY > 12);
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  var burger = document.getElementById('nav-burger');
  var mobile = document.getElementById('nav-mobile');
  if (burger && mobile) {
    burger.addEventListener('click', function () { mobile.classList.toggle('open'); });
    mobile.querySelectorAll('a').forEach(function (a) {
      a.addEventListener('click', function () { mobile.classList.remove('open'); });
    });
  }

  /* ---------- ANCHORS (Lenis-aware) ---------- */
  document.querySelectorAll('a[href^="#"]').forEach(function (link) {
    link.addEventListener('click', function (ev) {
      var href = link.getAttribute('href');
      if (!href || href === '#') return;
      var target = document.querySelector(href);
      if (!target) return;
      ev.preventDefault();
      if (lenis) lenis.scrollTo(target, { offset: -78 });
      else window.scrollTo({ top: target.getBoundingClientRect().top + window.scrollY - 78, behavior: reduced ? 'auto' : 'smooth' });
      history.replaceState(null, '', href);
    });
  });

  /* ---------- CUSTOM CURSOR ---------- */
  if (fine && !reduced) {
    var dot = document.getElementById('cursor-dot');
    var ring = document.getElementById('cursor-ring');
    if (dot && ring) {
      var cx = -100, cy = -100, rx = -100, ry = -100;
      window.addEventListener('mousemove', function (e) {
        cx = e.clientX; cy = e.clientY;
        dot.style.left = cx + 'px'; dot.style.top = cy + 'px';
      }, { passive: true });
      (function ringLoop() {
        rx += (cx - rx) * 0.16; ry += (cy - ry) * 0.16;
        ring.style.left = rx + 'px'; ring.style.top = ry + 'px';
        requestAnimationFrame(ringLoop);
      })();
      document.querySelectorAll('a, button, input, select, textarea, .magnetic').forEach(function (el) {
        el.addEventListener('mouseenter', function () { ring.classList.add('is-hover'); });
        el.addEventListener('mouseleave', function () { ring.classList.remove('is-hover'); });
      });
    }
  }

  /* ---------- MAGNETIC BUTTONS ---------- */
  if (fine && !reduced) {
    document.querySelectorAll('.magnetic').forEach(function (el) {
      el.addEventListener('mousemove', function (e) {
        var r = el.getBoundingClientRect();
        var x = e.clientX - r.left - r.width / 2;
        var y = e.clientY - r.top - r.height / 2;
        el.style.transform = 'translate(' + x * 0.18 + 'px,' + y * 0.22 + 'px)';
      });
      el.addEventListener('mouseleave', function () { el.style.transform = ''; });
    });
  }

  /* ---------- THREE.JS SPECIMEN — sculptural composition ---------- */
  var canvas = document.getElementById('hero-canvas');
  if (canvas && !reduced && !isSmall && typeof THREE !== 'undefined') {
    try {
      var renderer = new THREE.WebGLRenderer({ canvas: canvas, alpha: true, antialias: true });
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

      var scene = new THREE.Scene();
      var camera = new THREE.PerspectiveCamera(42, 1, 0.1, 100);
      camera.position.set(0, 0, 9);

      scene.add(new THREE.HemisphereLight(0xffffff, 0xdfe8e2, 0.95));
      var key = new THREE.DirectionalLight(0xffffff, 0.85);
      key.position.set(5, 7, 6);
      scene.add(key);
      var rim = new THREE.PointLight(0x0e7c66, 0.9, 40);
      rim.position.set(-7, -4, 5);
      scene.add(rim);

      var group = new THREE.Group();
      scene.add(group);

      // sculptural core: dark ink torus knot, clearcoat feel
      var core = new THREE.Mesh(
        new THREE.TorusKnotGeometry(1.55, 0.46, 240, 36),
        new THREE.MeshStandardMaterial({ color: 0x14171c, metalness: 0.42, roughness: 0.26 })
      );
      group.add(core);

      // orbiting viridian icosahedra — "molecules"
      var orbiters = [];
      for (var i = 0; i < 5; i++) {
        var m = new THREE.Mesh(
          new THREE.IcosahedronGeometry(0.24 + (i % 3) * 0.07, 0),
          new THREE.MeshStandardMaterial({ color: 0x0e7c66, flatShading: true, metalness: 0.2, roughness: 0.4 })
        );
        m.userData = {
          r: 2.9 + i * 0.55,
          speed: 0.22 + i * 0.07,
          phase: (i / 5) * Math.PI * 2,
          incl: 0.35 + (i % 2) * 0.5
        };
        group.add(m);
        orbiters.push(m);
      }

      // fine particle field
      var PCOUNT = 650;
      var ppos = new Float32Array(PCOUNT * 3);
      for (var p = 0; p < PCOUNT; p++) {
        var rad = 5.5 + Math.random() * 4.5;
        var th = Math.random() * Math.PI * 2;
        var ph = Math.acos(2 * Math.random() - 1);
        ppos[p * 3] = rad * Math.sin(ph) * Math.cos(th);
        ppos[p * 3 + 1] = rad * Math.cos(ph) * 0.75;
        ppos[p * 3 + 2] = rad * Math.sin(ph) * Math.sin(th);
      }
      var pgeo = new THREE.BufferGeometry();
      pgeo.setAttribute('position', new THREE.BufferAttribute(ppos, 3));
      var field = new THREE.Points(pgeo, new THREE.PointsMaterial({ color: 0x8b929e, size: 0.035, transparent: true, opacity: 0.5, depthWrite: false }));
      scene.add(field);

      var mx = 0, tx = 0, my = 0, ty = 0;
      window.addEventListener('mousemove', function (e) {
        tx = (e.clientX / window.innerWidth - 0.5);
        ty = (e.clientY / window.innerHeight - 0.5);
      }, { passive: true });

      function sizeRenderer() {
        var w = canvas.clientWidth || 480;
        var h = canvas.clientHeight || 560;
        renderer.setSize(w, h, false);
        camera.aspect = w / h;
        camera.updateProjectionMatrix();
      }
      sizeRenderer();
      window.addEventListener('resize', sizeRenderer);

      var visible = true;
      var heroSec = document.querySelector('.v3-hero');
      if ('IntersectionObserver' in window && heroSec) {
        new IntersectionObserver(function (en) { visible = en[0].isIntersecting; }, { threshold: 0 }).observe(heroSec);
      }

      var clock = new THREE.Clock();
      (function loop() {
        requestAnimationFrame(loop);
        if (!visible) return;
        var t = clock.getElapsedTime();
        mx += (tx - mx) * 0.045; my += (ty - my) * 0.045;
        core.rotation.x = t * 0.16 + my * 0.4;
        core.rotation.y = t * 0.21 + mx * 0.6;
        orbiters.forEach(function (m) {
          var u = m.userData;
          var a = t * u.speed + u.phase;
          m.position.set(Math.cos(a) * u.r, Math.sin(a * 0.8) * u.r * u.incl * 0.4, Math.sin(a) * u.r);
          m.rotation.x = t * 0.5; m.rotation.y = t * 0.4;
        });
        group.rotation.y = mx * 0.35;
        group.rotation.x = my * 0.25;
        field.rotation.y = t * 0.02;
        camera.lookAt(0, 0, 0);
        renderer.render(scene, camera);
      })();
    } catch (err) { /* WebGL/CDN unavailable — static fallback */ }
  }

  /* ---------- GSAP CHOREOGRAPHY ---------- */
  if (!reduced && typeof gsap !== 'undefined') {
    try {
      if (typeof ScrollTrigger !== 'undefined') gsap.registerPlugin(ScrollTrigger);

      var tl = gsap.timeline({ defaults: { ease: 'power3.out' } });
      ['.v3-hero__eyebrow', '.v3-hero h1', '.v3-hero__sub', '.v3-hero__ctas', '.hero-proofrow', '.v3-hero__specimen'].forEach(function (sel, idx) {
        var el = document.querySelector(sel);
        if (el) tl.from(el, { y: 36, autoAlpha: 0, duration: 0.95 }, 0.1 * idx);
      });

      document.querySelectorAll('[data-reveal]').forEach(function (el) {
        gsap.from(el, { y: 40, autoAlpha: 0, duration: 0.95, ease: 'power3.out', scrollTrigger: { trigger: el, start: 'top 86%', once: true } });
      });

      [['.v3-bento .v3-cell', 0.08], ['.v3-pipeline .v3-step', 0.09], ['.v3-truthgrid .v3-truth', 0.09], ['.v3-statsbar .v3-stat', 0.06]].forEach(function (cfg) {
        document.querySelectorAll(cfg[0]).forEach(function (el, i) {
          gsap.from(el, { y: 34, autoAlpha: 0, duration: 0.85, delay: (i % 4) * cfg[1], ease: 'power3.out', scrollTrigger: { trigger: el, start: 'top 90%', once: true } });
        });
      });

      var quote = document.querySelector('.v3-quote');
      if (quote) gsap.from(quote, { autoAlpha: 0, y: 44, duration: 1.15, ease: 'power3.out', scrollTrigger: { trigger: quote, start: 'top 82%', once: true } });

      document.querySelectorAll('[data-count]').forEach(function (el) {
        var endVal = parseInt(el.getAttribute('data-count'), 10) || 0;
        var obj = { v: 0 };
        gsap.to(obj, {
          v: endVal, duration: 1.7, ease: 'power2.out',
          scrollTrigger: { trigger: el, start: 'top 92%', once: true },
          onUpdate: function () { el.textContent = String(Math.round(obj.v)); }
        });
      });
    } catch (e) { /* optional */ }
  } else {
    document.querySelectorAll('[data-count]').forEach(function (el) { el.textContent = el.getAttribute('data-count') || '0'; });
  }

  /* ---------- FAQ ---------- */
  document.querySelectorAll('.v3-faq__item').forEach(function (item) {
    var q = item.querySelector('.v3-faq__q');
    var a = item.querySelector('.v3-faq__a');
    if (!q || !a) return;
    q.addEventListener('click', function () {
      var isOpen = item.classList.toggle('open');
      a.style.maxHeight = isOpen ? a.scrollHeight + 'px' : '0px';
      var chev = q.querySelector('.chev');
      if (chev) chev.textContent = isOpen ? '▾' : '▸';
    });
  });

  /* ============================================================
     DX LAYER — request capture · curl export · response mirror ·
     drag-drop · toasts · key auto-select (zero app.js edits)
     ============================================================ */
  var last = { url: null, method: null, requestHeaders: null, body: null, responseText: null, statusText: null };

  var toastEl = null, toastTimer = null;
  function toast(msg) {
    if (!toastEl) { toastEl = document.createElement('div'); toastEl.className = 'pp-toast'; document.body.appendChild(toastEl); }
    toastEl.textContent = msg;
    toastEl.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { toastEl.classList.remove('show'); }, 2200);
  }
  function copyText(text, okMsg) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(function () { toast(okMsg || 'Copied'); }, function () { fallbackCopy(text, okMsg); });
    } else { fallbackCopy(text, okMsg); }
  }
  function fallbackCopy(text, okMsg) {
    var ta = document.createElement('textarea');
    ta.value = text; ta.style.position = 'fixed'; ta.style.opacity = '0';
    document.body.appendChild(ta); ta.select();
    try { document.execCommand('copy'); toast(okMsg || 'Copied'); } catch (e) { toast('Copy failed'); }
    document.body.removeChild(ta);
  }

  var origFetch = window.fetch;
  if (typeof origFetch === 'function') {
    window.fetch = function (input, init) {
      try {
        var url = typeof input === 'string' ? input : (input && input.url) || '';
        if (url.indexOf('/api/v1/parse') !== -1 || url.indexOf('/api/v1/ocr-parse') !== -1) {
          last.url = url;
          last.method = (init && init.method) || (input && input.method) || 'GET';
          last.body = (init && init.body) || null;
          var hdrs = {};
          if (init && init.headers) {
            if (init.headers instanceof Headers) { init.headers.forEach(function (v, k) { hdrs[k] = v; }); }
            else { hdrs = Object.assign({}, init.headers); }
          }
          last.requestHeaders = hdrs;
          return origFetch.apply(this, arguments).then(function (res) {
            try {
              res.clone().text().then(function (txt) {
                last.statusText = res.status;
                last.responseText = txt;
                renderDevhubResponse();
              }).catch(function () {});
            } catch (e) {}
            return res;
          });
        }
      } catch (e) {}
      return origFetch.apply(this, arguments);
    };
  }

  function prettyBody() {
    if (!last.body) return null;
    try {
      if (typeof last.body === 'string' && last.body.trim().indexOf('{') === 0) {
        return JSON.stringify(JSON.parse(last.body), null, 2);
      }
      return String(last.body);
    } catch (e) { return String(last.body); }
  }
  function renderDevhubResponse() {
    var pre = document.getElementById('devhub-response');
    var badge = document.getElementById('devhub-response-status');
    if (!pre || !last.responseText) return;
    var out = last.responseText;
    try { out = JSON.stringify(JSON.parse(last.responseText), null, 2); } catch (e) {}
    pre.textContent = '// HTTP ' + (last.statusText || '') + ' — live response from /api/v1/parse\n' + out;
    if (badge) {
      badge.textContent = 'HTTP ' + (last.statusText || '') + ' · live';
      badge.style.color = last.statusText && last.statusText < 400 ? '#7cc8b8' : '#f0a8a8';
    }
  }

  function buildCurl() {
    var base = window.location.origin;
    var url = last.url || (base + '/api/v1/parse');
    if (url.indexOf('http') !== 0) url = base + url;
    var method = last.method || 'POST';
    var lines = ['curl -X ' + method + ' "' + url + '"'];
    var headers = last.requestHeaders || {};
    var hasAuth = false;
    Object.keys(headers).forEach(function (k) {
      var lk = k.toLowerCase();
      if (lk === 'content-type' && String(headers[k]).indexOf('multipart') !== -1) return;
      lines.push('  -H "' + k + ': ' + String(headers[k]).replace(/"/g, '\\"') + '"');
      if (lk === 'x-api-key' || lk === 'authorization') hasAuth = true;
    });
    if (!hasAuth) lines.push('  -H "X-API-KEY: test-dev-key"');
    var body = prettyBody();
    if (body && method !== 'GET' && method !== 'HEAD') {
      lines.push("  -d '" + body.replace(/'/g, "'\\''") + "'");
    }
    return lines.join(' \\\n');
  }
  var curlBtn = document.getElementById('btn-copy-curl');
  if (curlBtn) {
    curlBtn.addEventListener('click', function () {
      copyText(buildCurl(), last.url ? 'cURL copied — paste & run' : 'Sample cURL copied (run a parse first for your exact request)');
    });
  }
  var copyResp = document.getElementById('btn-copy-response');
  if (copyResp) {
    copyResp.addEventListener('click', function () {
      var pre = document.getElementById('devhub-response');
      if (pre) copyText(pre.textContent, 'Response copied');
    });
  }
  var skKey = document.getElementById('sk-key-visual');
  if (skKey) {
    skKey.addEventListener('click', function () { copyText('sicce_xxxxxxxxxxxxxxxx', 'Sample key format copied'); });
  }

  /* ---------- drag & drop ---------- */
  var stage = document.getElementById('optical-doc-container');
  var fileInput = document.getElementById('rx-file-input');
  if (stage && fileInput) {
    var hint = null;
    function showHint(show) {
      if (show) {
        if (!hint) { hint = document.createElement('div'); hint.className = 'drag-hint-float'; hint.textContent = 'Drop prescription to parse'; stage.appendChild(hint); }
        stage.classList.add('drag-over');
      } else {
        if (hint) { hint.remove(); hint = null; }
        stage.classList.remove('drag-over');
      }
    }
    ['dragenter', 'dragover'].forEach(function (evt) {
      stage.addEventListener(evt, function (e) { e.preventDefault(); showHint(true); });
    });
    ['dragleave', 'drop'].forEach(function (evt) {
      stage.addEventListener(evt, function (e) { e.preventDefault(); showHint(false); });
    });
    stage.addEventListener('drop', function (e) {
      var files = e.dataTransfer && e.dataTransfer.files;
      if (!files || !files.length) return;
      try {
        var dt = new DataTransfer();
        dt.items.add(files[0]);
        fileInput.files = dt.files;
        fileInput.dispatchEvent(new Event('change', { bubbles: true }));
        toast('Prescription received — parsing');
      } catch (err) { toast('Could not read dropped file'); }
    });
    window.addEventListener('dragover', function (e) { e.preventDefault(); });
    window.addEventListener('drop', function (e) { if (!stage.contains(e.target)) e.preventDefault(); });
  }

  /* ---------- key selector auto-hide ---------- */
  function hideSingleKey() {
    var sel = document.getElementById('active-key-select');
    if (sel && sel.options.length <= 1) {
      var wrap = sel.closest('.key-selector');
      if (wrap) wrap.classList.add('hidden-single');
    }
  }
  if (document.readyState === 'loading') {
    window.addEventListener('DOMContentLoaded', hideSingleKey);
  } else { hideSingleKey(); }

})();
