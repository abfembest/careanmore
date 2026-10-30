/* Care Anmore dashboard: mobile sidebar */
(function () {
  var btn = document.querySelector('.menu-btn');
  function set(open) {
    document.body.classList.toggle('nav-open', open);
    if (btn) btn.setAttribute('aria-expanded', String(open));
  }
  if (btn) btn.addEventListener('click', function () { set(!document.body.classList.contains('nav-open')); });
  document.querySelectorAll('[data-close-nav]').forEach(function (el) { el.addEventListener('click', function () { set(false); }); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') set(false); });
})();
