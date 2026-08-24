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
