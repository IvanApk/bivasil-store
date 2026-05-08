/* BIVA · Catálogo compartido + búsqueda + WhatsApp prefilled
   Usado por ambas variantes del rediseño y por el sitio actual.
   Carga products.json una vez y expone window.BIVA. */

(function() {
  const WHATSAPP_NUMBER = '5491153116412';

  async function loadCatalog() {
    if (window.BIVA && window.BIVA.products) return window.BIVA;
    try {
      const res = await fetch('products.json');
      const data = await res.json();
      window.BIVA = data;
      return data;
    } catch (e) {
      console.error('[BIVA] No se pudo cargar products.json', e);
      return null;
    }
  }

  function buildWhatsAppLink(product) {
    let msg;
    if (product) {
      msg = `Hola BIVA. Quería consultar por: ${product.name} (${product.sku}). ¿Me pasan precio mayorista y stock?`;
    } else {
      msg = `Hola BIVA. Quería consultar por catálogo y precios mayoristas.`;
    }
    return `https://wa.me/${WHATSAPP_NUMBER}?text=${encodeURIComponent(msg)}`;
  }

  function searchProducts(query, products) {
    if (!query) return products;
    const q = query.toLowerCase().trim();
    return products.filter(p => {
      const haystack = [
        p.name, p.shortDescription, p.description,
        p.category, ...(p.tags || []), ...(p.useCases || []),
        ...(p.materials || []), p.sku
      ].join(' ').toLowerCase();
      return haystack.includes(q);
    });
  }

  function filterByCategory(products, categoryId) {
    if (!categoryId || categoryId === 'all') return products;
    return products.filter(p => p.category === categoryId);
  }

  /* Nav search · lupa expandible siempre visible */
  function mountNavSearch() {
    const navInner = document.querySelector('.nav-inner');
    if (!navInner || document.querySelector('.nav-search')) return;

    const wrap = document.createElement('div');
    wrap.className = 'nav-search';
    wrap.innerHTML = `
      <button class="nav-search-toggle" aria-label="Buscar productos" aria-expanded="false">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
          <circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>
        </svg>
      </button>
      <div class="nav-search-panel" hidden>
        <div class="nav-search-inner">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" class="nav-search-icon">
            <circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>
          </svg>
          <input type="search" class="nav-search-input" placeholder="Buscar producto, material, uso…" autocomplete="off" />
          <button class="nav-search-close" aria-label="Cerrar">×</button>
        </div>
        <div class="nav-search-results" role="listbox"></div>
        <div class="nav-search-empty" hidden>Sin resultados. <a href="https://wa.me/${WHATSAPP_NUMBER}" target="_blank">Consultá por WhatsApp →</a></div>
      </div>
    `;
    // Insert before nav-cta
    const cta = navInner.querySelector('.nav-cta');
    navInner.insertBefore(wrap, cta);

    const toggle = wrap.querySelector('.nav-search-toggle');
    const panel = wrap.querySelector('.nav-search-panel');
    const input = wrap.querySelector('.nav-search-input');
    const closeBtn = wrap.querySelector('.nav-search-close');
    const results = wrap.querySelector('.nav-search-results');
    const empty = wrap.querySelector('.nav-search-empty');

    const openPanel = () => {
      panel.hidden = false;
      requestAnimationFrame(() => {
        panel.classList.add('open');
        input.focus();
      });
      toggle.setAttribute('aria-expanded', 'true');
    };
    const closePanel = () => {
      panel.classList.remove('open');
      toggle.setAttribute('aria-expanded', 'false');
      setTimeout(() => { panel.hidden = true; }, 220);
    };

    toggle.addEventListener('click', () => {
      if (panel.hidden) openPanel(); else closePanel();
    });
    closeBtn.addEventListener('click', closePanel);
    document.addEventListener('keydown', e => {
      if (e.key === 'Escape' && !panel.hidden) closePanel();
      if ((e.key === 'k' || e.key === 'K') && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        panel.hidden ? openPanel() : closePanel();
      }
    });

    let allProducts = [];
    loadCatalog().then(data => {
      if (data) allProducts = data.products;
    });

    input.addEventListener('input', () => {
      const q = input.value.trim();
      if (!q) {
        results.innerHTML = '';
        empty.hidden = true;
        return;
      }
      const matches = searchProducts(q, allProducts).slice(0, 6);
      if (!matches.length) {
        results.innerHTML = '';
        empty.hidden = false;
        return;
      }
      empty.hidden = true;
      results.innerHTML = matches.map(p => `
        <a class="nav-search-result" href="${p.url}">
          <div class="nsr-thumb" style="background-image:url('${p.image}')"></div>
          <div class="nsr-body">
            <span class="nsr-cat">${p.category === 'cocina' ? 'Cocina' : 'Jardín'}</span>
            <span class="nsr-name">${p.name}</span>
            <span class="nsr-desc">${p.shortDescription}</span>
          </div>
          <svg class="nsr-arrow" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M5 12h14M13 5l7 7-7 7"/></svg>
        </a>
      `).join('');
    });
  }

  window.BIVAUtils = {
    loadCatalog,
    buildWhatsAppLink,
    searchProducts,
    filterByCategory
  };

  document.addEventListener('DOMContentLoaded', mountNavSearch);
})();
