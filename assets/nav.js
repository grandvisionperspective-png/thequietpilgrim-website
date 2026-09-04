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

// Ambient pill: lazy-create an <audio> element on first click, fade in/out.
(function () {
  var pill = document.querySelector('.ambient-pill');
  if (!pill) return;
  var src = pill.getAttribute('data-ambient');
  if (!src) return;
  var labelEl = pill.querySelector('.label');
  var audio = null;
  var fadeTimer = null;

  function fadeTo(target, ms) {
    if (!audio) return;
    if (fadeTimer) clearInterval(fadeTimer);
    var step = 50;
    var diff = target - audio.volume;
    var steps = Math.max(1, Math.round(ms / step));
    var inc = diff / steps;
    fadeTimer = setInterval(function () {
      var next = audio.volume + inc;
      if ((inc > 0 && next >= target) || (inc < 0 && next <= target)) {
        audio.volume = target;
        clearInterval(fadeTimer);
        fadeTimer = null;
        if (target === 0) audio.pause();
      } else {
        audio.volume = next;
      }
    }, step);
  }

  pill.addEventListener('click', function () {
    var on = pill.getAttribute('aria-pressed') === 'true';
    if (!audio) {
      audio = new Audio(src);
      audio.loop = true;
      audio.volume = 0;
    }
    if (on) {
      pill.setAttribute('aria-pressed', 'false');
      if (labelEl) labelEl.textContent = 'Play ambient';
      fadeTo(0, 600);
    } else {
      pill.setAttribute('aria-pressed', 'true');
      if (labelEl) labelEl.textContent = 'Pause ambient';
      audio.play().catch(function () {});
      fadeTo(0.35, 1200);
    }
  });
})();


// Join the table: waitlist capture. Any form.join-table posts to the worker.
(function () {
  var WAITLIST_URL = "https://tqp-lead.barrie-helm.workers.dev/waitlist";
  var forms = document.querySelectorAll("form.join-table");
  Array.prototype.forEach.call(forms, function (f) {
    f.addEventListener("submit", function (ev) {
      ev.preventDefault();
      var emailEl = f.querySelector('input[type="email"]');
      var email = ((emailEl && emailEl.value) || "").trim();
      if (!email || email.indexOf("@") === -1) return;
      var btn = f.querySelector("button");
      var hp = f.querySelector('input[name="company"]');
      if (btn) { btn.disabled = true; btn.textContent = "One moment"; }
      fetch(WAITLIST_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email, company: (hp && hp.value) || "", source: f.getAttribute("data-source") || "waitlist", page: location.pathname })
      }).then(function (r) { return r.ok; }).then(function (ok) {
        var row = f.querySelector(".jt-row"), line = f.querySelector(".jt-line"), done = f.querySelector(".jt-done");
        if (ok) { try { document.dispatchEvent(new CustomEvent("tqp:joined", { detail: { source: f.getAttribute("data-source") || "waitlist" } })); } catch (e) {}
          if (row) row.style.display = "none"; if (line) line.style.display = "none"; if (done) done.hidden = false; }
        else if (btn) { btn.disabled = false; btn.textContent = "Join"; }
      }).catch(function () { if (btn) { btn.disabled = false; btn.textContent = "Join"; } });
    });
  });
})();
