/* ============================================================
   SICCE site.js v5 — premium motion layer
   Lenis smooth scroll · GSAP choreography · Three.js hero field.
   Zero overlap with app.js workbench logic; every integration
   guarded so the page degrades gracefully if a CDN fails.
   ============================================================ */
(function () {
  'use strict';

  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var isSmall = window.innerWidth < 720;

  /* ---------- LENIS SMOOTH SCROLL ---------- */
  var lenis = null;
  if (!reduced && typeof Lenis !== 'undefined') {
    try {
      lenis = new Lenis({ duration: 1.15, easing: function (t) { return Math.min(1, 1.001 - Math.pow(2, -10 * t)); } });
      function raf(time) { lenis.raf(time); requestAnimationFrame(raf); }
      requestAnimationFrame(raf);
    } catch (e) { lenis = null; }
  }

  /* ---------- SCROLL PROGRESS ---------- */
  var progress = document.getElementById('scroll-progress');
  function updateProgress() {
    var h = document.documentElement.scrollHeight - window.innerHeight;
    if (progress && h > 0) progress.style.width = ((window.scrollY / h) * 100) + '%';
  }

  /* ---------- NAV ---------- */
  var nav = document.getElementById('site-nav');
  function navState() {
    if (nav) nav.classList.toggle('is-scrolled', window.scrollY > 12);
    updateProgress();
  }
  window.addEventListener('scroll', navState, { passive: true });
  navState();

  var burger = document.getElementById('nav-burger');
  var mobile = document.getElementById('nav-mobile');
  if (burger && mobile) {
    burger.addEventListener('click', function () {
      var open = mobile.classList.toggle('open');
      burger.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    mobile.querySelectorAll('a').forEach(function (a) {
      a.addEventListener('click', function () { mobile.classList.remove('open'); });
    });
  }

  /* ---------- ANCHOR NAVIGATION (Lenis-aware) ---------- */
  document.querySelectorAll('a[href^="#"]').forEach(function (link) {
    link.addEventListener('click', function (ev) {
      var href = link.getAttribute('href');
      if (!href || href === '#') return;
      var target = document.querySelector(href);
      if (!target) return;
      ev.preventDefault();
      var offset = -78;
      if (lenis) { lenis.scrollTo(target, { offset: offset }); }
      else {
        var top = target.getBoundingClientRect().top + window.scrollY + offset;
        window.scrollTo({ top: top, behavior: reduced ? 'auto' : 'smooth' });
      }
      history.replaceState(null, '', href);
    });
  });

  /* ---------- THREE.JS HERO PARTICLE HELIX ---------- */
  var canvas = document.getElementById('hero-canvas');
  var heroSection = document.querySelector('.v3-hero');
  if (canvas && !reduced && !isSmall && typeof THREE !== 'undefined') {
    try {
      var renderer = new THREE.WebGLRenderer({ canvas: canvas, alpha: true, antialias: true });
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      var scene = new THREE.Scene();
      var camera = new THREE.PerspectiveCamera(50, 1, 0.1, 100);
      camera.position.z = 14;

      // Double-helix point cloud: clinical-data motif
      var COUNT = isSmall ? 900 : 2200;
      var positions = new Float32Array(COUNT * 3);
      var colors = new Float32Array(COUNT * 3);
      var ink = new THREE.Color('#14171c');
      var vir = new THREE.Color('#0e7c66');
      var sky = new THREE.Color('#5b8fb9');
      for (var i = 0; i < COUNT; i++) {
        var t = (i / COUNT) * Math.PI * 22;
        var strand = i % 2 === 0 ? 0 : Math.PI;
        var r = 3.4;
        positions[i * 3] = Math.cos(t + strand) * r + (Math.random() - 0.5) * 0.55;
        positions[i * 3 + 1] = (i / COUNT - 0.5) * 17;
        positions[i * 3 + 2] = Math.sin(t + strand) * r + (Math.random() - 0.5) * 0.55;
        var c = i % 3 === 0 ? vir : (i % 3 === 1 ? ink.clone().lerp(vir, 0.35) : sky.clone().lerp(ink, 0.55));
        colors[i * 3] = c.r; colors[i * 3 + 1] = c.g; colors[i * 3 + 2] = c.b;
      }
      var geo = new THREE.BufferGeometry();
      geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
      geo.setAttribute('color', new THREE.BufferAttribute(colors, 3));
      var mat = new THREE.PointsMaterial({ size: 0.055, vertexColors: true, transparent: true, opacity: 0.75, depthWrite: false });
      var helix = new THREE.Points(geo, mat);
      helix.rotation.x = 0.42;
      helix.position.y = 0.4;
      scene.add(helix);

      var mouseX = 0, targetX = 0;
      window.addEventListener('mousemove', function (e) {
        targetX = (e.clientX / window.innerWidth - 0.5) * 0.6;
      }, { passive: true });

      function sizeRenderer() {
        var w = canvas.clientWidth || window.innerWidth;
        var h = canvas.clientHeight || window.innerHeight;
        renderer.setSize(w, h, false);
        camera.aspect = w / h;
        camera.updateProjectionMatrix();
      }
      sizeRenderer();
      window.addEventListener('resize', sizeRenderer);

      var visible = true;
      if ('IntersectionObserver' in window && heroSection) {
        new IntersectionObserver(function (entries) {
          visible = entries[0].isIntersecting;
        }, { threshold: 0 }).observe(heroSection);
      }

      var clock = new THREE.Clock();
      (function animate() {
        requestAnimationFrame(animate);
        if (!visible) return;
        mouseX += (targetX - mouseX) * 0.04;
        helix.rotation.y += 0.0016;
        helix.rotation.z = mouseX * 0.25;
        camera.position.x = mouseX * 1.6;
        camera.lookAt(scene.position);
        renderer.render(scene, camera);
      })();
    } catch (err) { /* CDN/WEBGL unavailable — page still works fully */ }
  }

  /* ---------- GSAP CHOREOGRAPHY ---------- */
  if (!reduced && typeof gsap !== 'undefined') {
    try {
      if (typeof ScrollTrigger !== 'undefined') gsap.registerPlugin(ScrollTrigger);

      // hero entrance
      var heroEls = ['.v3-hero__eyebrow', '.v3-hero h1', '.v3-hero__sub', '.v3-hero__ctas', '.hero-proofrow'];
      var tl = gsap.timeline({ defaults: { ease: 'power3.out' } });
      heroEls.forEach(function (sel, idx) {
        var el = document.querySelector(sel);
        if (el) tl.from(el, { y: 34, autoAlpha: 0, duration: 0.9 }, 0.12 * idx);
      });

      // generic reveals
      document.querySelectorAll('[data-reveal]').forEach(function (el) {
        gsap.from(el, {
          y: 40, autoAlpha: 0, duration: 0.95, ease: 'power3.out',
          scrollTrigger: { trigger: el, start: 'top 86%', once: true }
        });
      });

      // stagger grids
      [['.v3-bento .v3-cell', 0.08], ['.v3-pipeline .v3-step', 0.09], ['.v3-truthgrid .v3-truth', 0.09]].forEach(function (cfg) {
        var els = document.querySelectorAll(cfg[0]);
        els.forEach(function (el, i) {
          gsap.from(el, {
            y: 36, autoAlpha: 0, duration: 0.85, delay: (i % 3) * cfg[1], ease: 'power3.out',
            scrollTrigger: { trigger: el, start: 'top 88%', once: true }
          });
        });
      });

      // dark interlude quote
      var quote = document.querySelector('.v3-quote');
      if (quote) {
        gsap.from(quote, {
          autoAlpha: 0, y: 44, duration: 1.1, ease: 'power3.out',
          scrollTrigger: { trigger: quote, start: 'top 82%', once: true }
        });
      }

      // counters
      document.querySelectorAll('[data-count]').forEach(function (el) {
        var endVal = parseInt(el.getAttribute('data-count'), 10) || 0;
        var obj = { v: 0 };
        gsap.to(obj, {
          v: endVal, duration: 1.6, ease: 'power2.out',
          scrollTrigger: { trigger: el, start: 'top 90%', once: true },
          onUpdate: function () { el.textContent = String(Math.round(obj.v)); }
        });
      });
    } catch (e) { /* motion layer optional */ }
  } else {
    // reduced-motion / no-GSAP fallback: show everything immediately
    document.querySelectorAll('[data-count]').forEach(function (el) {
      el.textContent = el.getAttribute('data-count') || '0';
    });
  }

  /* ---------- FAQ ACCORDION ---------- */
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

})();

/* ============================================================
   v5.2 DX LAYER — Deepgram/Veryfi-inspired developer experience
   Captures real workbench traffic (fetch monkey-patch, zero
   app.js edits) to power: Copy-as-cURL · DevHub response mirror ·
   drag-drop upload · sandbox-key auto-select · toasts.
   ============================================================ */
(function () {
  'use strict';

  var last = { url: null, method: null, requestHeaders: null, body: null, responseText: null, status: null };

  /* ---------- toast ---------- */
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

  /* ---------- fetch interceptor: capture parse traffic ---------- */
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
              var cloned = res.clone();
              cloned.text().then(function (txt) {
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

  /* ---------- devhub response mirror ---------- */
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
    if (!pre) return;
    if (!last.responseText) return;
    var out = last.responseText;
    try { out = JSON.stringify(JSON.parse(last.responseText), null, 2); } catch (e) {}
    pre.textContent = '// HTTP ' + (last.statusText || '') + ' — live response from /api/v1/parse\n' + out;
    if (badge) {
      badge.textContent = 'HTTP ' + (last.statusText || '') + ' · live';
      badge.style.color = last.statusText && last.statusText < 400 ? '#7cc8b8' : '#f0a8a8';
    }
  }

  /* ---------- copy as cURL ---------- */
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
      if (lk === 'content-type' && String(headers[k]).indexOf('multipart') !== -1) return; // curl sets multipart boundary itself
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

  /* ---------- devhub response copy ---------- */
  var copyResp = document.getElementById('btn-copy-response');
  if (copyResp) {
    copyResp.addEventListener('click', function () {
      var pre = document.getElementById('devhub-response');
      if (pre) copyText(pre.textContent, 'Response copied');
    });
  }

  /* ---------- sandbox key visual: click to copy sample ---------- */
  var skKey = document.getElementById('sk-key-visual');
  if (skKey) {
    skKey.addEventListener('click', function () { copyText('sicce_xxxxxxxxxxxxxxxx', 'Sample key format copied'); });
  }

  /* ---------- drag & drop prescription upload ---------- */
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
    // whole-page drop guard: prevent browser from navigating away
    window.addEventListener('dragover', function (e) { e.preventDefault(); });
    window.addEventListener('drop', function (e) { if (!stage.contains(e.target)) e.preventDefault(); });
  }

  /* ---------- key selector: hide when only one key ---------- */
  window.addEventListener('DOMContentLoaded', function () {
    var sel = document.getElementById('active-key-select');
    if (sel && sel.options.length <= 1) {
      var wrap = sel.closest('.key-selector');
      if (wrap) wrap.classList.add('hidden-single');
    }
  });
  if (document.readyState !== 'loading') {
    var sel2 = document.getElementById('active-key-select');
    if (sel2 && sel2.options.length <= 1) {
      var wrap2 = sel2.closest('.key-selector');
      if (wrap2) wrap2.classList.add('hidden-single');
    }
  }

})();
