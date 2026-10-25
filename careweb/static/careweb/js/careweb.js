/* Care Anmore — careweb front-end behaviour (no dependencies) */
(function () {
  'use strict';

  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------- Image fallback: hide photos that fail so the branded artwork shows ---------- */
  document.querySelectorAll('.arch img, .service-card__media img, .media-stack__main img').forEach(function (img) {
    function hide() { img.style.visibility = 'hidden'; }
    if (img.complete && img.naturalWidth === 0) hide();
    img.addEventListener('error', hide);
  });

  /* ---------- Mobile navigation ---------- */
  var toggle = document.querySelector('.menu-toggle');
  var nav = document.getElementById('main-nav');
  var header = document.querySelector('.site-header');

  function setNav(open) {
    if (!nav || !toggle) return;
    nav.classList.toggle('is-open', open);
    toggle.setAttribute('aria-expanded', String(open));
    document.body.classList.toggle('nav-open', open);
    if (open && header) {
      document.documentElement.style.setProperty('--offset-top', Math.max(0, header.getBoundingClientRect().top) + 'px');
    }
  }
  if (toggle) {
    toggle.addEventListener('click', function () {
      setNav(toggle.getAttribute('aria-expanded') !== 'true');
    });
  }
  window.addEventListener('resize', function () {
    if (window.innerWidth > 980) setNav(false);
  });

  /* ---------- Dropdowns ---------- */
  var dropdownButtons = document.querySelectorAll('[data-dropdown]');
  function closeDropdowns(except) {
    dropdownButtons.forEach(function (btn) {
      if (btn === except) return;
      btn.setAttribute('aria-expanded', 'false');
      var menu = document.getElementById(btn.getAttribute('aria-controls'));
      if (menu) menu.classList.remove('is-open');
    });
  }
  dropdownButtons.forEach(function (btn) {
    var menu = document.getElementById(btn.getAttribute('aria-controls'));
    btn.addEventListener('click', function (e) {
      e.stopPropagation();
      var open = btn.getAttribute('aria-expanded') !== 'true';
      closeDropdowns(btn);
      btn.setAttribute('aria-expanded', String(open));
      if (menu) menu.classList.toggle('is-open', open);
    });
  });
  document.addEventListener('click', function (e) {
    if (!e.target.closest('.has-dropdown')) closeDropdowns();
  });
  document.addEventListener('keydown', function (e) {
    if (e.key !== 'Escape') return;
    var openBtn = document.querySelector('[data-dropdown][aria-expanded="true"]');
    closeDropdowns();
    if (openBtn) openBtn.focus();
    if (nav && nav.classList.contains('is-open')) { setNav(false); toggle.focus(); }
  });

  /* ---------- Header shadow & back to top ---------- */
  var backTop = document.querySelector('.back-to-top');
  function onScroll() {
    var y = window.scrollY;
    if (header) header.classList.toggle('is-scrolled', y > 8);
    if (backTop) backTop.classList.toggle('is-visible', y > 700);
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();
  if (backTop) {
    backTop.addEventListener('click', function () {
      window.scrollTo({ top: 0, behavior: reduceMotion ? 'auto' : 'smooth' });
      var skip = document.getElementById('main-content');
      if (skip) skip.focus({ preventScroll: true });
    });
  }

  /* ---------- Hero carousel ---------- */
  document.querySelectorAll('[data-carousel]').forEach(function (root) {
    var slides = Array.prototype.slice.call(root.querySelectorAll('.hero-slide'));
    if (slides.length < 2) return;
    var dots = Array.prototype.slice.call(root.querySelectorAll('.hero__dot'));
    var prev = root.querySelector('[data-prev]');
    var next = root.querySelector('[data-next]');
    var playBtn = root.querySelector('[data-play]');
    var count = root.querySelector('.hero__count');
    var live = root.querySelector('[data-live]');
    var interval = parseInt(root.getAttribute('data-interval'), 10) || 7000;
    var index = 0;
    var timer = null;
    var userPaused = reduceMotion;
    var hoverPaused = false;

    root.style.setProperty('--hero-interval', interval + 'ms');

    function show(i, announce) {
      index = (i + slides.length) % slides.length;
      slides.forEach(function (s, n) {
        var active = n === index;
        s.classList.toggle('is-active', active);
        s.setAttribute('aria-hidden', String(!active));
        s.querySelectorAll('a, button').forEach(function (el) { el.tabIndex = active ? 0 : -1; });
      });
      dots.forEach(function (d) { d.removeAttribute('aria-current'); });
      void root.offsetWidth; // reflow so the progress bar animation restarts
      if (dots[index]) dots[index].setAttribute('aria-current', 'true');
      if (count) count.textContent = (index + 1) + ' / ' + slides.length;
      if (announce && live) live.textContent = 'Slide ' + (index + 1) + ' of ' + slides.length;
      restart();
    }

    function stop() { if (timer) { clearTimeout(timer); timer = null; } }
    function restart() {
      stop();
      var playing = !userPaused && !hoverPaused;
      root.classList.toggle('is-playing', !userPaused);
      root.classList.toggle('is-paused', hoverPaused && !userPaused);
      if (playing) timer = setTimeout(function () { show(index + 1, false); }, interval);
    }
    function setUserPaused(p) {
      userPaused = p;
      if (playBtn) {
        playBtn.setAttribute('aria-label', p ? 'Play slideshow' : 'Pause slideshow');
        playBtn.querySelector('use').setAttribute('href', p ? '#i-play' : '#i-pause');
      }
      restart();
    }

    if (prev) prev.addEventListener('click', function () { show(index - 1, true); });
    if (next) next.addEventListener('click', function () { show(index + 1, true); });
    if (playBtn) playBtn.addEventListener('click', function () { setUserPaused(!userPaused); });
    dots.forEach(function (d, n) { d.addEventListener('click', function () { show(n, true); }); });

    // Pause while the pointer or keyboard focus is inside; resume with a fresh full interval.
    root.addEventListener('mouseenter', function () { hoverPaused = true; restart(); });
    root.addEventListener('mouseleave', function () { hoverPaused = false; show(index, false); });
    root.addEventListener('focusin', function () { hoverPaused = true; restart(); });
    root.addEventListener('focusout', function (e) {
      if (!root.contains(e.relatedTarget)) { hoverPaused = false; show(index, false); }
    });
    root.addEventListener('keydown', function (e) {
      if (e.target.closest('input, textarea, select')) return;
      if (e.key === 'ArrowLeft') { show(index - 1, true); }
      if (e.key === 'ArrowRight') { show(index + 1, true); }
    });

    // swipe on touch screens
    var startX = null;
    root.addEventListener('touchstart', function (e) { startX = e.touches[0].clientX; }, { passive: true });
    root.addEventListener('touchend', function (e) {
      if (startX === null) return;
      var dx = e.changedTouches[0].clientX - startX;
      if (Math.abs(dx) > 50) show(index + (dx < 0 ? 1 : -1), true);
      startX = null;
    });

    document.addEventListener('visibilitychange', function () {
      if (document.hidden) stop(); else restart();
    });

    setUserPaused(userPaused);
    show(0, false);
  });

  /* ---------- Enquiry form: mark the field needed for the chosen contact method ---------- */
  var method = document.getElementById('id_contact_method');
  if (method) {
    var marks = { email: document.querySelector('[data-req-for="email"]'), phone: document.querySelector('[data-req-for="phone"]') };
    function updateReq() {
      Object.keys(marks).forEach(function (k) { if (marks[k]) marks[k].hidden = method.value !== k; });
    }
    method.addEventListener('change', updateReq);
    updateReq();
  }

  /* ---------- Error summary focus ---------- */
  var summary = document.querySelector('.error-summary');
  if (summary) summary.focus();

  /* ---------- Contents list: highlight the current section ---------- */
  var contentsLinks = document.querySelectorAll('.contents-list a[href^="#"]');
  if (contentsLinks.length && 'IntersectionObserver' in window) {
    var map = {};
    contentsLinks.forEach(function (a) { map[a.getAttribute('href').slice(1)] = a; });
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting && map[en.target.id]) {
          contentsLinks.forEach(function (a) { a.removeAttribute('aria-current'); });
          map[en.target.id].setAttribute('aria-current', 'true');
        }
      });
    }, { rootMargin: '-20% 0px -70% 0px' });
    Object.keys(map).forEach(function (id) { var el = document.getElementById(id); if (el) io.observe(el); });
  }
})();
