/* BIVA · medición de visitas
   ─────────────────────────────────────────────────────────────
   Para activarla, completá los dos códigos y guardá el archivo:
     GA_ID       → Google Analytics 4 (empieza con "G-")
     CLARITY_ID  → Microsoft Clarity (10 letras/números)
   Si un código queda vacío, esa herramienta simplemente no se carga.

   Eventos que se envían a Google Analytics:
     whatsapp_click  · clic en cualquier botón de WhatsApp (con el SKU si es de un producto)
     email_click     · clic en info@bivasil.com
     instagram_click · clic en Instagram
     search          · búsqueda en el buscador del sitio (término)
     search_select   · producto elegido desde el buscador
   ───────────────────────────────────────────────────────────── */
(function () {
  var GA_ID = 'G-RXC32V3Y2S';
  var CLARITY_ID = 'yxmoq1ccux';

  if (location.hostname !== 'bivasil.com' && location.hostname !== 'www.bivasil.com') return; // no medir pruebas locales

  /* Google Analytics 4 */
  window.dataLayer = window.dataLayer || [];
  function gtag() { dataLayer.push(arguments); }
  window.gtag = gtag;
  if (GA_ID) {
    var s = document.createElement('script');
    s.async = true;
    s.src = 'https://www.googletagmanager.com/gtag/js?id=' + GA_ID;
    document.head.appendChild(s);
    gtag('js', new Date());
    gtag('config', GA_ID);
  }

  /* Microsoft Clarity (mapas de calor y grabaciones de sesión) */
  if (CLARITY_ID) {
    (function (c, l, a, r, i, t, y) {
      c[a] = c[a] || function () { (c[a].q = c[a].q || []).push(arguments); };
      t = l.createElement(r); t.async = 1; t.src = 'https://www.clarity.ms/tag/' + i;
      y = l.getElementsByTagName(r)[0]; y.parentNode.insertBefore(t, y);
    })(window, document, 'clarity', 'script', CLARITY_ID);
  }

  function track(name, params) {
    if (GA_ID) gtag('event', name, params || {});
    if (CLARITY_ID && window.clarity) window.clarity('event', name);
  }

  function skuFrom(text) {
    var m = decodeURIComponent(text || '').match(/BV-[A-Z]{3}-\d+/);
    return m ? m[0] : '';
  }

  var pageSku = skuFrom((document.querySelector('.pd-info .eyebrow') || {}).textContent || '');

  document.addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('a[href]');
    if (!a) return;
    var href = a.getAttribute('href');
    if (/wa\.me\//.test(href)) {
      track('whatsapp_click', { sku: skuFrom(href) || pageSku || '(general)', ubicacion: location.pathname });
    } else if (/^mailto:/.test(href)) {
      track('email_click', { sku: skuFrom(href) || pageSku || '(general)', ubicacion: location.pathname });
    } else if (/instagram\.com/.test(href)) {
      track('instagram_click', { ubicacion: location.pathname });
    } else if (a.classList.contains('nav-search-result')) {
      track('search_select', { destino: href });
    }
  }, true);

  var timer;
  document.addEventListener('input', function (e) {
    if (!e.target.classList || !e.target.classList.contains('nav-search-input')) return;
    clearTimeout(timer);
    var term = e.target.value.trim();
    if (term.length < 3) return;
    timer = setTimeout(function () { track('search', { search_term: term.toLowerCase() }); }, 1500);
  });
})();
