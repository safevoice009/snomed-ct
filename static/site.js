/* SICCE site.js — marketing-layer motion & behavior. Zero overlap with app.js workbench logic. */
(function () {
  'use strict';

  // 1. Nav scroll state
  var nav = document.getElementById('site-nav');
  if (nav) {
    var onScroll = function () {
      nav.classList.toggle('is-scrolled', window.scrollY > 12);
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  // 2. Scroll-reveal (respects reduced motion)
  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var reveals = document.querySelectorAll('.reveal');
  if (!reduced && 'IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add('is-visible'); io.unobserve(e.target); }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
    reveals.forEach(function (el) { io.observe(el); });
  } else {
    reveals.forEach(function (el) { el.classList.add('is-visible'); });
  }

  // 3. FAQ accordion
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

  // 4. Smooth anchor offset for fixed navbar
  document.querySelectorAll('a[href^="#"]').forEach(function (link) {
    link.addEventListener('click', function (ev) {
      var targetId = link.getAttribute('href');
      if (!targetId || targetId === '#') return;
      var target = document.querySelector(targetId);
      if (!target) return;
      ev.preventDefault();
      var top = target.getBoundingClientRect().top + window.scrollY - 76;
      window.scrollTo({ top: top, behavior: 'smooth' });
      history.replaceState(null, '', targetId);
    });
  });

})();
