(function () {
  var nav = document.querySelector('nav.nav');
  if (!nav) return;
  var btn = nav.querySelector('.hamburger');
  var panel = nav.querySelector('ul');
  if (!btn || !panel) return;

  function setOpen(open) {
    nav.classList.toggle('open', open);
    document.body.classList.toggle('nav-open', open);
    btn.setAttribute('aria-expanded', open ? 'true' : 'false');
  }

  btn.addEventListener('click', function () {
    setOpen(!nav.classList.contains('open'));
  });

  panel.addEventListener('click', function (e) {
    if (e.target.tagName === 'A') setOpen(false);
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && nav.classList.contains('open')) setOpen(false);
  });

  window.addEventListener('resize', function () {
    if (window.innerWidth > 720 && nav.classList.contains('open')) setOpen(false);
  });
})();
