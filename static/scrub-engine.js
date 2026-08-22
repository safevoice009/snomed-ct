/* ============================================================================
   scroll-world — SICCE Enterprise Healthcare 3D Film Engine
   High-Precision Medical Technology Flight with Optical Laser Reticle
   ============================================================================ */

function mountScrollWorld(container, config) {
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const coarse = window.matchMedia('(hover: none) and (pointer: coarse)').matches;
  const smallMQ = window.matchMedia('(max-width: 860px)');
  const isMobile = () => coarse || smallMQ.matches;
  const SECTIONS = config.sections || [];
  const DIVE_W = config.diveScroll || 1.4;
  const CROSSFADE = (config.crossfade != null) ? config.crossfade : 0.14;
  const N = SECTIONS.length;
  if (!N) return;

  container.classList.add('sw-root');

  const SEGMENTS = [];
  SECTIONS.forEach((s, i) => {
    const dive = {
      kind: 'dive',
      si: i,
      still: s.still,
      accent: s.accent,
      w: s.scroll || DIVE_W,
      linger: s.linger || 0.45,
      huds: s.huds || []
    };
    SEGMENTS.push(dive);
    s._seg = dive;
  });
  const NSEG = SEGMENTS.length;

  // DOM
  const sky = el('div', 'sw-sky');
  if (config.atmosphere !== false) {
    sky.appendChild(el('div', 'sw-sky__grad'));
    sky.appendChild(el('div', 'sw-sky__glow'));
  }
  const particles = el('div', 'sw-particles');
  sky.appendChild(particles);

  // Precision Optical Laser Reticle
  const reticleContainer = el('div', 'sw-scanner-reticle');
  reticleContainer.innerHTML = `
    <div class="sw-reticle-ring"></div>
    <div class="sw-reticle-inner"></div>
    <div class="sw-reticle-cross-h"></div>
    <div class="sw-reticle-cross-v"></div>
    <div class="sw-reticle-label" id="sw-reticle-telemetry">OCR: SCANNING ACTIVE (42ms)</div>
  `;

  const scrollbar = el('div', 'sw-scrollbar');
  const scrollbarFill = el('span');
  scrollbar.appendChild(scrollbarFill);

  const topbar = el('div', 'sw-topbar');
  if (config.brand) {
    const brand = el('a', 'sw-brand');
    brand.href = config.brand.href || '#top';
    brand.appendChild(el('span', 'sw-brand__mark'));
    const nm = el('span', 'sw-brand__name');
    nm.textContent = config.brand.name || 'SICCE';
    brand.appendChild(nm);
    topbar.appendChild(brand);
  }
  const nav = el('nav', 'sw-nav');
  if (config.nav !== false) topbar.appendChild(nav);

  if (config.cta && config.cta.label) {
    const c = el('a', 'sw-topcta');
    c.href = config.cta.href || '#sandbox';
    c.textContent = config.cta.label;
    topbar.appendChild(c);
  }

  const stage = el('div', 'sw-stage');
  const copylayer = el('div', 'sw-copylayer');
  const route = el('div', 'sw-route');
  const hint = el('div', 'sw-hint');
  const hintText = el('span');
  hintText.textContent = config.hint || 'scroll to fly in';
  hint.appendChild(hintText);
  hint.appendChild(el('i'));
  const track = el('div', 'sw-track');

  [sky, reticleContainer, scrollbar, topbar, stage, copylayer, route, hint, track].forEach(n => container.appendChild(n));

  // Segment Scenes with Clean Enterprise HUD Telemetry
  SEGMENTS.forEach(s => {
    const scene = el('div', 'sw-scene');
    scene.style.setProperty('--sw-accent', s.accent || '');
    
    const viewport = el('div', 'sw-scene__viewport');
    const img = el('img', 'sw-scene__still');
    img.alt = '';
    img.decoding = 'async';
    img.loading = 'eager';
    img.src = s.still;
    viewport.appendChild(img);

    // Floating 3D HUD Indicators
    if (s.huds && s.huds.length) {
      const hudLayer = el('div', 'sw-scene__hud-layer');
      s.huds.forEach((h, idx) => {
        const badge = el('div', `sw-hud-badge sw-hud-badge--${idx + 1}`);
        badge.innerHTML = `<span class="sw-hud-dot"></span><span>${esc(h)}</span>`;
        hudLayer.appendChild(badge);
      });
      viewport.appendChild(hudLayer);
      s.hudLayer = hudLayer;
    }

    scene.appendChild(viewport);
    stage.appendChild(scene);
    s.el = scene;
    s.viewport = viewport;
    s.img = img;
    s.cur = 0;
    s.target = 0;
    s.visible = false;
  });

  // Per-Section Copy Cards & Waypoints
  const copies = [], dots = [];
  SECTIONS.forEach((s, i) => {
    const c = el('article', 'sw-copy');
    c.style.setProperty('--sw-accent', s.accent || '');
    c.innerHTML =
      `<span class="sw-copy__num">${pad(i + 1)} / ${pad(N)}</span>` +
      (s.eyebrow ? `<span class="sw-copy__eyebrow">${esc(s.eyebrow)}</span>` : '') +
      (s.title ? `<h2 class="sw-copy__title">${esc(s.title)}</h2>` : '') +
      (s.body ? `<p class="sw-copy__body">${esc(s.body)}</p>` : '') +
      (s.tags && s.tags.length ? `<ul class="sw-copy__tags">${s.tags.map(t => `<li>${esc(t)}</li>`).join('')}</ul>` : '') +
      (s.cta ? `<div class="sw-copy__cta">${ctaBtns(s.cta)}</div>` : '');
    copylayer.appendChild(c);
    copies.push(c);

    const dot = el('button', 'sw-route__dot');
    dot.style.setProperty('--sw-accent', s.accent || '');
    dot.innerHTML = `<span class="sw-route__label">${esc(s.label || '')}</span><i></i>`;
    dot.addEventListener('click', () => jumpTo(i));
    route.appendChild(dot);
    dots.push(dot);

    if (config.nav !== false) {
      const b = el('button', 'sw-nav__item');
      b.textContent = s.label || '';
      b.addEventListener('click', () => jumpTo(i));
      nav.appendChild(b);
    }
  });

  // 3D Parallax & Mouse Flight Tracking
  let mouseX = 0, mouseY = 0, targetMouseX = 0, targetMouseY = 0;
  window.addEventListener('mousemove', (e) => {
    const cx = window.innerWidth / 2;
    const cy = window.innerHeight / 2;
    targetMouseX = (e.clientX - cx) / cx;
    targetMouseY = (e.clientY - cy) / cy;
  }, { passive: true });

  // Math & Layout
  const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  const smooth = x => { x = clamp(x); return x * x * (3 - 2 * x); };
  const lingerEase = (x, L) => { L = clamp(L); const c = x - 0.5; return (1 - L) * x + L * (4 * c * c * c + 0.5); };
  
  let vh = window.innerHeight, stageX = 0, totalW = 0, activeIndex = -1, ticking = false;
  let laidOutW = window.innerWidth;

  function layout() {
    vh = window.innerHeight;
    laidOutW = window.innerWidth;
    stageX = window.innerWidth > 860 ? 4 : 0;
    let off = 0;
    SEGMENTS.forEach(s => {
      s.start = off * vh;
      off += s.w;
      s.end = off * vh;
    });
    totalW = off;
    track.style.height = (totalW * vh + vh) + 'px';
    read();
  }

  function jumpTo(i) {
    const seg = SECTIONS[i]._seg;
    window.scrollTo({
      top: container.offsetTop + seg.start + (seg.end - seg.start) * 0.5,
      behavior: reduce ? 'auto' : 'smooth'
    });
  }

  const reticleTelemetry = document.getElementById('sw-reticle-telemetry');

  function read() {
    const scrollY = window.scrollY || window.pageYOffset;
    const containerTop = container.offsetTop || 0;
    const y = Math.max(0, scrollY - containerTop);
    const fade = CROSSFADE * vh;
    let ci = 0;
    for (let i = 0; i < NSEG; i++) if (y >= SEGMENTS[i].start) ci = i;

    // Smooth lerp mouse tracking
    mouseX += (targetMouseX - mouseX) * 0.08;
    mouseY += (targetMouseY - mouseY) * 0.08;

    // Animate Precision Optical Laser Reticle Position
    const progress = clamp(y / (totalW * vh), 0, 1);
    const retX = window.innerWidth * 0.52 + Math.sin(progress * Math.PI * 3) * (window.innerWidth * 0.18) + mouseX * 25;
    const retY = window.innerHeight * 0.25 + (progress * window.innerHeight * 0.5) + mouseY * 20;

    reticleContainer.style.transform = `translate3d(${retX}px, ${retY}px, 0)`;
    reticleContainer.style.opacity = (progress > 0.02 && progress < 0.98) ? '1' : '0';

    if (reticleTelemetry) {
      if (ci === 0) reticleTelemetry.textContent = 'OPTICAL INTAKE: PARSING (38ms)';
      else if (ci === 1) reticleTelemetry.textContent = 'DPDP DE-IDENTIFIER: CLEAN (12ms)';
      else if (ci === 2) reticleTelemetry.textContent = 'SNOMED GIN: 100k MATCH (14ms)';
      else if (ci === 3) reticleTelemetry.textContent = 'FHIR R4 ENGINE: ASSEMBLED (22ms)';
      else if (ci === 4) reticleTelemetry.textContent = 'ABDM VAULT: PURGE SEALED (8ms)';
    }

    for (let i = 0; i < NSEG; i++) {
      const s = SEGMENTS[i];
      const local = clamp((y - s.start) / (s.end - s.start), 0, 1);
      s.target = s.linger ? lingerEase(local, s.linger) : local;
      let outside = 0;
      if (y < s.start) outside = s.start - y;
      else if (y > s.end) outside = y - s.end;
      const op = smooth(1 - outside / fade);
      s.el.style.opacity = op;
      s.visible = op > 0.001;
      s.el.style.zIndex = (i === ci) ? '120' : String(100 + Math.round(op * 10));

      // 3D Camera Depth Tilt & Push-in
      const rotY = reduce ? 0 : mouseX * 6.0;
      const rotX = reduce ? 0 : -mouseY * 5.0;
      const sc = reduce ? 1 : 1.0 + local * 0.18;
      const zTranslate = reduce ? 0 : (local * 45);

      s.viewport.style.transform = `perspective(1200px) rotateX(${rotX.toFixed(2)}deg) rotateY(${rotY.toFixed(2)}deg) translateZ(${zTranslate.toFixed(1)}px)`;
      s.img.style.transform = `translateX(${stageX}vw) scale(${sc.toFixed(3)})`;

      if (s.hudLayer) {
        const hudOp = smooth(1 - Math.abs(local - 0.5) / 0.4);
        s.hudLayer.style.opacity = hudOp;
        s.hudLayer.style.transform = `translate3d(${mouseX * -10}px, ${mouseY * -8}px, 30px)`;
      }
    }

    for (let i = 0; i < N; i++) {
      const seg = SECTIONS[i]._seg;
      const pr = clamp((y - seg.start) / (seg.end - seg.start), 0, 1);
      const before = y < seg.start, after = y > seg.end;
      let cop;
      if (i === 0) cop = after ? 0 : smooth(1 - pr / 0.65);
      else if (i === N - 1) cop = before ? 0 : smooth(pr / 0.45);
      else cop = (before || after) ? 0 : smooth(1 - Math.abs(pr - 0.5) / 0.5);

      const c = copies[i];
      c.style.opacity = cop;
      c.style.transform = reduce ? 'none' : `translateY(${(0.5 - pr) * 5}vh)`;
      c.style.pointerEvents = cop > 0.5 ? 'auto' : 'none';
    }

    const cur = SEGMENTS[ci];
    const near = clamp(cur ? cur.si : 0, 0, N - 1);
    if (near !== activeIndex) {
      activeIndex = near;
      dots.forEach((d, k) => d.classList.toggle('is-active', k === near));
      nav.querySelectorAll('.sw-nav__item').forEach((n, k) => n.classList.toggle('is-active', k === near));
      container.style.setProperty('--sw-accent', SECTIONS[near].accent || '');
    }

    scrollbarFill.style.transform = `scaleX(${clamp(y / (totalW * vh))})`;
    hint.style.opacity = clamp(1 - y / (0.4 * vh));
    if (particles) particles.style.transform = `translate3d(0, ${-y * 0.04}px, 0)`;
    ticking = false;
  }

  function animLoop() {
    read();
    requestAnimationFrame(animLoop);
  }

  seedParticles(particles, reduce || coarse);
  window.addEventListener('scroll', () => {
    if (!ticking) {
      ticking = true;
      requestAnimationFrame(read);
    }
  }, { passive: true });

  window.addEventListener('resize', layout);
  window.addEventListener('orientationchange', layout);
  layout();
  requestAnimationFrame(animLoop);

  // Helpers
  function el(tag, cls) {
    const n = document.createElement(tag);
    if (cls) n.className = cls;
    return n;
  }
  function pad(n) { return String(n).padStart(2, '0'); }
  function esc(s) { return String(s).replace(/[&<>\"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c])); }
  function ctaBtns(cta) {
    let h = '';
    if (cta.primary) h += `<a class="sw-btn sw-btn--primary" href="${esc(cta.primary.href || '#')}">${esc(cta.primary.label)}</a>`;
    if (cta.secondary) h += `<a class="sw-btn sw-btn--ghost" href="${esc(cta.secondary.href || '#')}">${esc(cta.secondary.label)}</a>`;
    return h;
  }
}

function seedParticles(host, reduce) {
  if (!host || reduce) return;
  const kinds = ['dot', 'dot', 'ring'];
  const seeds = [7, 23, 41, 58, 71, 88, 12, 34, 52, 66, 83, 95, 18, 29, 47, 63, 77, 91, 5, 38];
  for (let k = 0; k < 18; k++) {
    const s = document.createElement('span');
    s.className = 'sw-pt sw-pt--' + kinds[k % kinds.length];
    s.style.left = seeds[k % seeds.length] + 'vw';
    s.style.top = ((seeds[(k * 3) % seeds.length] * 1.3) % 100) + 'vh';
    s.style.setProperty('--sw-sc', (0.5 + ((seeds[(k * 5) % seeds.length] % 60) / 60) * 1.1).toFixed(2));
    const dur = 14 + (seeds[(k * 7) % seeds.length] % 20);
    s.style.animationDuration = dur + 's';
    s.style.animationDelay = (-(seeds[(k * 2) % seeds.length] % dur)) + 's';
    host.appendChild(s);
  }
}
