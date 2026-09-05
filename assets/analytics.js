/* The Quiet Pilgrim: one small measurement layer.
   Fill the two ids below and every page reports page views plus the moments
   that matter: a WhatsApp tap, an email tap, a note sent, a join. */
(function () {
  var GA4_ID = "G-EXSDG14TDN";        /* e.g. "G-XXXXXXXXXX" */
  var META_PIXEL_ID = ""; /* e.g. "1234567890" */

  if (GA4_ID) {
    var s = document.createElement("script");
    s.async = true; s.src = "https://www.googletagmanager.com/gtag/js?id=" + GA4_ID;
    document.head.appendChild(s);
    window.dataLayer = window.dataLayer || [];
    window.gtag = function () { window.dataLayer.push(arguments); };
    window.gtag("js", new Date());
    window.gtag("config", GA4_ID, { anonymize_ip: true });
  }
  if (META_PIXEL_ID) {
    !function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?n.callMethod.apply(n,arguments):n.queue.push(arguments)};if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version="2.0";n.queue=[];t=b.createElement(e);t.async=!0;t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}(window,document,"script","https://connect.facebook.net/en_US/fbevents.js");
    window.fbq("init", META_PIXEL_ID);
    window.fbq("track", "PageView");
  }

  function track(name, params) {
    params = params || {};
    params.page = location.pathname;
    try { if (window.gtag) window.gtag("event", name, params); } catch (e) {}
    try { if (window.fbq) window.fbq("trackCustom", name, params); } catch (e) {}
    if (name === "note_sent" || name === "whatsapp_click") {
      try { if (window.fbq) window.fbq("track", "Lead", params); } catch (e) {}
    }
  }
  window.tqpTrack = track;

  function where(el) {
    var sec = el.closest("nav, header, footer, section");
    if (!sec) return "page";
    if (sec.tagName === "NAV") return "nav";
    if (sec.tagName === "FOOTER") return "footer";
    var lab = sec.querySelector(".label, .pre, .frame");
    return (lab && lab.textContent.trim().toLowerCase()) || sec.className || "section";
  }

  document.addEventListener("click", function (e) {
    var a = e.target.closest && e.target.closest("a[href]");
    if (!a) return;
    var h = a.getAttribute("href") || "";
    if (h.indexOf("wa.me") !== -1) track("whatsapp_click", { placement: where(a) });
    else if (h.indexOf("mailto:") === 0) track("email_click", { placement: where(a) });
    else if (h.indexOf("/write/") === 0) track("write_click", { placement: where(a) });
  }, true);

  document.addEventListener("tqp:note_sent", function (e) { track("note_sent", (e && e.detail) || {}); });
  document.addEventListener("tqp:joined", function (e) { track("join_list", (e && e.detail) || {}); });
})();
