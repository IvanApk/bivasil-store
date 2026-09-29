#!/usr/bin/env python3
"""
BIVA · genera una página estática por producto en /productos/<slug>/index.html
a partir de products.json. Borra las páginas de productos que ya no existen.

Normalmente no se corre solo: usar  python3 _tools/build.py
"""
import json, html, re, shutil, pathlib, urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = 'https://bivasil.com'
OUT = ROOT / 'productos'

data = json.loads((ROOT / 'products.json').read_text(encoding='utf-8'))
site = data['site']
products = data['products']
PHONE = site['contact']['whatsapp']
WA = PHONE.lstrip('+')
EMAIL = site['contact']['email']
IG = site['contact']['instagram']

CAT = {
    'cocina': {'label': 'Cocina', 'long': 'Cocina y bazar', 'href': '/cocina.html'},
    'jardin': {'label': 'Jardín', 'long': 'Jardín', 'href': '/jardin.html'},
}
CUR = ' aria-current="true"'
e = lambda s: html.escape(str(s or ''), quote=True)
ARROW = '<svg class="arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M5 12h14M13 5l7 7-7 7"/></svg>'
WA_ICON = '<svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M.057 24l1.687-6.163c-1.041-1.804-1.588-3.849-1.587-5.946.003-6.556 5.338-11.891 11.893-11.891 3.181.001 6.167 1.24 8.413 3.488 2.245 2.248 3.481 5.236 3.48 8.414-.003 6.557-5.338 11.892-11.893 11.892-1.99-.001-3.951-.5-5.688-1.448l-6.305 1.654zm6.597-3.807c1.676.995 3.276 1.591 5.392 1.592 5.448 0 9.886-4.434 9.889-9.885.002-5.462-4.415-9.89-9.881-9.892-5.452 0-9.887 4.434-9.889 9.884-.001 2.225.651 3.891 1.746 5.634l-.999 3.648 3.742-.981z"/></svg>'


def page_url(p):
    return f'/productos/{p["slug"]}/'


def clean_name(p):
    return re.sub(r'\s*·\s*', ' ', p['name']).strip()


def split_name(p):
    parts = [x.strip() for x in p['name'].split('·')]
    return parts[0], (' · '.join(parts[1:]) if len(parts) > 1 else '')


def first_sentence(text, limit=160):
    text = (text or '').strip()
    m = re.match(r'(.+?[.!?])(\s|$)', text)
    s = m.group(1) if m else text
    return s if len(s) <= limit else s[:limit - 1].rsplit(' ', 1)[0] + '…'


def lead(p):
    return (p.get('shortDescription') or '').strip() or first_sentence(p['description'])


def meta_desc(p):
    base = lead(p).rstrip('.')
    tail = '. Venta mayorista a comercios, envíos a todo el país.'
    d = base + tail
    return d if len(d) <= 165 else first_sentence(base, 165 - len(tail)).rstrip('.…') + tail


def wa_link(p):
    msg = f'Hola BIVA. Quería consultar por: {clean_name(p)} ({p["sku"]}). ¿Me pasan precio mayorista y stock?'
    return f'https://wa.me/{WA}?text={urllib.parse.quote(msg)}'


def mail_link(p):
    q = urllib.parse.urlencode({'subject': f'Consulta mayorista · {clean_name(p)} ({p["sku"]})'}, quote_via=urllib.parse.quote)
    return f'mailto:{EMAIL}?{q}'


def related(p, n=4):
    pool = [x for x in products if x['id'] != p['id'] and x['category'] == p['category']]
    tags = set(p.get('tags') or [])
    pool.sort(key=lambda x: (-len(tags & set(x.get('tags') or [])), products.index(x)))
    if len(pool) < n:
        pool += [x for x in products if x['id'] != p['id'] and x not in pool][:n - len(pool)]
    return pool[:n]


def abs_img(path):
    return BASE + '/' + path.lstrip('/')


def ld_json(p):
    cat = CAT.get(p['category'], {'label': p['category'], 'href': '/'})
    url = BASE + page_url(p)
    prod = {
        "@type": "Product",
        "@id": url + "#product",
        "name": clean_name(p),
        "sku": p['sku'],
        "description": p['description'],
        "image": [abs_img(i) for i in p['gallery']],
        "category": cat['long'] if 'long' in cat else cat['label'],
        "url": url,
        "brand": {"@type": "Brand", "name": "BIVA"},
        "offers": {
            "@type": "Offer",
            "url": url,
            "availability": "https://schema.org/InStock" if p['availability'] == 'in_stock' else "https://schema.org/PreOrder",
            "priceCurrency": site.get('currency', 'ARS'),
            "eligibleCustomerType": "http://purl.org/goodrelations/v1#Business",
            "areaServed": {"@type": "Country", "name": "Argentina"},
            "seller": {"@id": BASE + "/#org"}
        }
    }
    if p.get('materials'):
        prod["material"] = ", ".join(p['materials'])
    if p.get('tags'):
        prod["keywords"] = ", ".join(p['tags'])
    graph = [
        {"@type": "Organization", "@id": BASE + "/#org", "name": "BIVA", "url": BASE + "/",
         "email": EMAIL, "telephone": PHONE, "sameAs": [IG]},
        prod,
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Inicio", "item": BASE + "/"},
            {"@type": "ListItem", "position": 2, "name": cat['label'], "item": BASE + cat['href']},
            {"@type": "ListItem", "position": 3, "name": clean_name(p), "item": url}]},
    ]
    return json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False).replace('</', '<\\/')


def render(p):
    cat = CAT.get(p['category'], {'label': p['category'].title(), 'long': p['category'].title(), 'href': '/'})
    title_main, title_sub = split_name(p)
    name = clean_name(p)
    url = BASE + page_url(p)
    page_title = f'{name} por mayor · BIVA'
    desc = meta_desc(p)
    in_stock = p['availability'] == 'in_stock'
    fit = ' contain' if p.get('imageFit') == 'contain' else ''
    gal = p['gallery']
    og_img = abs_img(gal[0])

    thumbs = ''
    if len(gal) > 1:
        thumbs = '<div class="pd-thumbs" role="list">' + ''.join(
            f'<button class="pd-thumb" type="button" role="listitem" data-src="/{e(src)}" aria-label="Ver foto {i} de {len(gal)}"'
            f'{CUR if i == 1 else ""}><img src="/{e(src)}" alt="" loading="lazy" /></button>'
            for i, src in enumerate(gal, 1)) + '</div>'

    feats = ''
    if p.get('features'):
        feats = ('<div class="pd-section"><h2>Características</h2><ul class="pd-features">'
                 + ''.join(f'<li>{e(f)}</li>' for f in p['features']) + '</ul></div>')

    specs = [('SKU', p['sku']), ('Categoría', cat['long']),
             ('Disponibilidad', 'En stock' if in_stock else 'Próximo ingreso')]
    if p.get('materials'):
        specs.append(('Materiales', ', '.join(p['materials']).capitalize()))
    if p.get('useCases'):
        specs.append(('Ideal para', ', '.join(p['useCases']).capitalize()))
    if p.get('packSize'):
        specs.append(('Unidades por bulto', p['packSize']))
    if p.get('minOrder'):
        specs.append(('Pedido mínimo', p['minOrder']))
    specs.append(('Venta', 'Solo mayoristas · precio a consultar'))
    specs.append(('Envíos', 'A todo el país'))
    specs_html = ''.join(f'<div><dt>{e(k)}</dt><dd>{e(v)}</dd></div>' for k, v in specs)

    rel = ''.join(
        f'<a class="rel-card" href="{page_url(r)}">'
        f'<div class="product-frame"><img class="product-img{" contain" if r.get("imageFit") == "contain" else ""}" src="/{e(r["thumb"])}" alt="{e(clean_name(r))}" loading="lazy" /></div>'
        f'<span>{e(CAT.get(r["category"], {"label": ""})["label"])} · {e(r["sku"])}</span><h3>{e(clean_name(r))}</h3></a>'
        for r in related(p))

    return f'''<!doctype html>
<html lang="es-AR">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{e(page_title)}</title>
<meta name="description" content="{e(desc)}" />
<link rel="canonical" href="{url}" />
<meta name="robots" content="index, follow, max-image-preview:large" />
<meta name="theme-color" content="#333330" />
<link rel="icon" href="/favicon.svg" type="image/svg+xml" />
<link rel="icon" href="/favicon-32.png" sizes="32x32" type="image/png" />
<link rel="apple-touch-icon" href="/apple-touch-icon.png" />
<meta property="og:type" content="product" />
<meta property="og:site_name" content="BIVA" />
<meta property="og:locale" content="es_AR" />
<meta property="og:title" content="{e(name)} · BIVA mayorista" />
<meta property="og:description" content="{e(desc)}" />
<meta property="og:url" content="{url}" />
<meta property="og:image" content="{og_img}" />
<meta name="twitter:card" content="summary_large_image" />
<script type="application/ld+json">{ld_json(p)}</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Gloock&family=Work+Sans:wght@300;400;500;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/styles.css" />
<link rel="stylesheet" href="/catalog.css" />
<link rel="stylesheet" href="/product.css" />
</head>
<body>

<div class="wholesale-banner">
  Solo mayoristas <span class="dot"></span> Importación directa · Envíos a todo el país
  <a href="/contacto.html">Cómo comprar →</a>
</div>

<nav class="nav">
  <div class="nav-inner">
    <a href="/" class="wordmark">BI<span class="v">V</span>A</a>
    <div class="nav-links">
      <a href="/">Inicio</a>
      <a href="/cocina.html"{' class="active"' if p['category'] == 'cocina' else ''}>Cocina</a>
      <a href="/jardin.html"{' class="active"' if p['category'] == 'jardin' else ''}>Jardín</a>
      <a href="/nosotros.html">Nosotros</a>
      <a href="/contacto.html">Contacto</a>
    </div>
    <a class="nav-cta" href="https://wa.me/{WA}" target="_blank" rel="noopener">
      {WA_ICON}
      WhatsApp
    </a>
  </div>
</nav>

<main class="pd">
  <div class="wrap">
    <nav class="crumbs" aria-label="Ruta">
      <ol>
        <li><a href="/">Inicio</a></li>
        <li><a href="{cat['href']}">{e(cat['label'])}</a></li>
        <li><span aria-current="page">{e(name)}</span></li>
      </ol>
    </nav>

    <div class="pd-grid" style="margin-top: 32px;">
      <div class="pd-gallery">
        <div class="pd-main">
          <div class="product-frame"><img class="product-img{fit}" id="pd-main-img" src="/{e(gal[0])}" alt="{e(name)}" width="1200" height="1200" fetchpriority="high" /></div>
        </div>
        {thumbs}
      </div>

      <div class="pd-info">
        <div class="eyebrow">{e(cat['label'])} · {e(p['sku'])}</div>
        <h1 class="pd-title">{e(title_main)}{f' <em>{e(title_sub)}</em>' if title_sub else ''}</h1>
        <p class="h-tagline pd-lead">{e(lead(p))}</p>
        <div class="pd-pills">
          <span class="pill{'' if in_stock else ' pd-pill-next'}">{'En stock' if in_stock else 'Próximo ingreso'}</span>
          <span class="pill">Solo mayoristas</span>
          <span class="pill">Envíos a todo el país</span>
        </div>
        <div class="pd-actions">
          <a class="btn btn-dark" href="{e(wa_link(p))}" target="_blank" rel="noopener">Pedir precio mayorista {ARROW}</a>
          <a class="pd-mail" href="{e(mail_link(p))}">o escribinos a {e(EMAIL)}</a>
        </div>
        <p class="pd-note">Te respondemos con precio, stock y costo de envío a tu localidad.</p>

        <div class="pd-section">
          <h2>Descripción</h2>
          <p>{e(p['description'])}</p>
        </div>
        {feats}
        <div class="pd-section">
          <h2>Ficha</h2>
          <dl class="pd-specs">{specs_html}</dl>
        </div>
      </div>
    </div>
  </div>
</main>

<section class="pd-how">
  <div class="wrap">
    <div class="eyebrow light">Cómo comprar mayorista</div>
    <h2 class="h-section" style="color: var(--blanco-roto); margin-top: 20px;">Tres pasos, desde cualquier provincia.</h2>
    <div class="pd-how-grid">
      <div class="pd-how-step"><div class="n">01</div><h3>Escribinos</h3><p>Por WhatsApp o mail, contanos qué comercio tenés y qué productos te interesan.</p></div>
      <div class="pd-how-step"><div class="n">02</div><h3>Te pasamos lista</h3><p>Precios mayoristas, stock real y fotos. En la Costa Atlántica, también visita con muestra.</p></div>
      <div class="pd-how-step"><div class="n">03</div><h3>Despachamos</h3><p>Stock propio en Argentina. Enviamos a todo el país; en la Costa Atlántica, 24–72 hs.</p></div>
    </div>
  </div>
</section>

<section class="pd-related">
  <div class="wrap">
    <div class="pd-related-head">
      <h2 class="h-section">También te puede interesar</h2>
      <a href="{cat['href']}">Ver todo {e(cat['label'])} →</a>
    </div>
    <div class="pd-related-grid">{rel}</div>
  </div>
</section>

<footer class="footer">
  <div class="footer-inner">
    <div>
      <div class="wordmark-big">BI<span class="v">V</span>A</div>
      <div class="tagline">Pragmatismo · Diseño · Calidad</div>
      <p style="max-width: 32ch; line-height: 1.55;">Importadora y distribuidora mayorista para el hogar. Desde Mar del Plata a todo el país.</p>
    </div>
    <div>
      <h4>Catálogo</h4>
      <ul>
        <li><a href="/cocina.html">Cocina</a></li>
        <li><a href="/jardin.html">Jardín</a></li>
        <li><a href="/#catalogo">Todo el catálogo</a></li>
      </ul>
    </div>
    <div>
      <h4>Empresa</h4>
      <ul>
        <li><a href="/nosotros.html">Nosotros</a></li>
        <li><a href="/contacto.html">Contacto</a></li>
      </ul>
    </div>
    <div>
      <h4>Contacto</h4>
      <ul>
        <li><a href="https://wa.me/{WA}" target="_blank" rel="noopener">WhatsApp · 11 5311 6412</a></li>
        <li><a href="mailto:{EMAIL}">{EMAIL}</a></li>
        <li><a href="{IG}" target="_blank" rel="noopener">@bivasil.store</a></li>
      </ul>
    </div>
  </div>
  <div class="footer-bottom">
    <span>© 2026 BIVA · Mar del Plata, Argentina</span>
    <span>Solo mayoristas · bivasil.com</span>
  </div>
</footer>

<script>
/* Galería: cambiar foto principal */
(function() {{
  var main = document.getElementById('pd-main-img');
  document.querySelectorAll('.pd-thumb').forEach(function(b) {{
    b.addEventListener('click', function() {{
      main.src = b.dataset.src;
      document.querySelectorAll('.pd-thumb').forEach(function(x) {{ x.removeAttribute('aria-current'); }});
      b.setAttribute('aria-current', 'true');
    }});
  }});
}})();
</script>
<script src="/catalog.js"></script>
<script src="/site.js"></script>
</body>
</html>
'''


# write pages, remove stale ones
OUT.mkdir(exist_ok=True)
current = set()
for p in products:
    d = OUT / p['slug']
    d.mkdir(exist_ok=True)
    (d / 'index.html').write_text(render(p), encoding='utf-8')
    current.add(p['slug'])
for d in OUT.iterdir():
    if d.is_dir() and d.name not in current:
        shutil.rmtree(d)

# keep product URLs in products.json pointing at the pages
changed = False
for p in products:
    if p.get('url') != page_url(p):
        p['url'] = page_url(p)
        changed = True
if changed:
    (ROOT / 'products.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

print(f'OK · {len(products)} páginas de producto en /productos/')
