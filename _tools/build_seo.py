#!/usr/bin/env python3
"""
BIVA · generador SEO/GEO estático.

Correr cada vez que cambie products.json:
    python3 _tools/build_seo.py

Qué hace (todo idempotente, se puede correr las veces que haga falta):
  - Inyecta en el <head> de cada página: canonical, Open Graph, Twitter, favicon
    y JSON-LD estático (Organization / WebSite / ItemList / Breadcrumb).
  - Inyecta un catálogo en HTML plano (<noscript>) para que buscadores y
    crawlers de IA que no ejecutan JavaScript puedan leer los productos.
  - Regenera sitemap.xml, robots.txt y llms.txt.

La carpeta empieza con "_" para que GitHub Pages (Jekyll) no la publique.
"""
import json, html, re, datetime, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = 'https://bivasil.com'
TODAY = datetime.date.today().isoformat()

data = json.loads((ROOT / 'products.json').read_text(encoding='utf-8'))
site = data['site']
products = data['products']
EMAIL = site['contact']['email']
PHONE = site['contact']['whatsapp']
IG = site['contact']['instagram']

CAT_LABEL = {'cocina': 'Cocina y bazar', 'jardin': 'Jardín'}

PAGES = {
    'index.html':    {'path': '/',              'crumb': None},
    'cocina.html':   {'path': '/cocina.html',   'crumb': 'Cocina'},
    'jardin.html':   {'path': '/jardin.html',   'crumb': 'Jardín'},
    'nosotros.html': {'path': '/nosotros.html', 'crumb': 'Nosotros'},
    'contacto.html': {'path': '/contacto.html', 'crumb': 'Contacto'},
}

ORG = {
    "@type": "Organization",
    "@id": BASE + "/#org",
    "name": "BIVA",
    "alternateName": ["BIVASIL", "BIVA Importadora"],
    "url": BASE + "/",
    "logo": BASE + "/apple-touch-icon.png",
    "image": BASE + "/images/og-biva.jpg",
    "description": site['description'],
    "email": EMAIL,
    "telephone": PHONE,
    "slogan": "Pragmatismo · Diseño · Calidad",
    "knowsAbout": ["importación de artículos para el hogar", "utensilios de cocina", "bazar", "vajilla", "jardín", "venta mayorista"],
    "address": {
        "@type": "PostalAddress",
        "addressLocality": "Mar del Plata",
        "addressRegion": "Buenos Aires",
        "addressCountry": "AR"
    },
    "areaServed": {"@type": "Country", "name": "Argentina"},
    "contactPoint": {
        "@type": "ContactPoint",
        "telephone": PHONE,
        "email": EMAIL,
        "contactType": "sales",
        "areaServed": "AR",
        "availableLanguage": "es"
    },
    "sameAs": [IG]
}


def abs_url(p):
    return BASE + '/' + p.lstrip('/')


def product_ld(p):
    item = {
        "@type": "Product",
        "name": p['name'].strip(),
        "sku": p['sku'],
        "description": p['description'],
        "image": [abs_url(i) for i in (p.get('gallery') or p.get('images') or [p['image']])[:3]],
        "category": CAT_LABEL.get(p['category'], p['category']),
        "url": abs_url(p['url']),
        "brand": {"@type": "Brand", "name": "BIVA"},
        "offers": {
            "@type": "Offer",
            "availability": "https://schema.org/InStock" if p['availability'] == 'in_stock' else "https://schema.org/PreOrder",
            "priceCurrency": site.get('currency', 'ARS'),
            "eligibleCustomerType": "http://purl.org/goodrelations/v1#Business",
            "areaServed": "AR",
            "seller": {"@id": BASE + "/#org"}
        }
    }
    if p.get('materials'):
        item["material"] = ", ".join(p['materials'])
    return item


def itemlist(items, name):
    return {
        "@type": "ItemList",
        "name": name,
        "numberOfItems": len(items),
        "itemListElement": [{"@type": "ListItem", "position": i + 1, "item": product_ld(p)} for i, p in enumerate(items)]
    }


def page_meta(fname, t):
    title = re.search(r'<title>(.*?)</title>', t, re.S).group(1).strip()
    m = re.search(r'<meta name="description" content="(.*?)"', t)
    desc = m.group(1) if m else site['description']
    return title, desc


def head_block(fname, t):
    cfg = PAGES[fname]
    url = BASE + cfg['path']
    title, desc = page_meta(fname, t)
    graph = [ORG]
    if fname == 'index.html':
        graph.append({"@type": "WebSite", "@id": BASE + "/#web", "url": BASE + "/", "name": "BIVA",
                      "inLanguage": "es-AR", "publisher": {"@id": BASE + "/#org"}})
        graph.append(itemlist(products, "Catálogo mayorista BIVA"))
    else:
        graph.append({"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Inicio", "item": BASE + "/"},
            {"@type": "ListItem", "position": 2, "name": cfg['crumb'], "item": url}]})
        if fname in ('cocina.html', 'jardin.html'):
            cat = fname.split('.')[0]
            graph.append(itemlist([p for p in products if p['category'] == cat], f"{CAT_LABEL[cat]} · catálogo mayorista BIVA"))
    ld = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False)
    e = html.escape
    return f'''<!-- SEO:START (generado por _tools/build_seo.py — no editar a mano) -->
<link rel="canonical" href="{url}" />
<meta name="robots" content="index, follow, max-image-preview:large" />
<meta name="theme-color" content="#333330" />
<link rel="icon" href="favicon.svg" type="image/svg+xml" />
<link rel="icon" href="favicon-32.png" sizes="32x32" type="image/png" />
<link rel="apple-touch-icon" href="apple-touch-icon.png" />
<meta property="og:type" content="website" />
<meta property="og:site_name" content="BIVA" />
<meta property="og:locale" content="es_AR" />
<meta property="og:title" content="{e(title, quote=True)}" />
<meta property="og:description" content="{e(html.unescape(desc), quote=True)}" />
<meta property="og:url" content="{url}" />
<meta property="og:image" content="{BASE}/images/og-biva.jpg" />
<meta property="og:image:width" content="1200" />
<meta property="og:image:height" content="630" />
<meta property="og:image:alt" content="BIVA · Importador mayorista de cocina, bazar y jardín" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:image" content="{BASE}/images/og-biva.jpg" />
<script type="application/ld+json">{ld}</script>
<!-- SEO:END -->'''


def noscript_catalog(items, heading):
    rows = []
    for p in items:
        mats = ', '.join(p.get('materials') or [])
        status = 'En stock' if p['availability'] == 'in_stock' else 'Próximo ingreso'
        rows.append(
            f'<li id="p-{html.escape(p["id"])}"><h3><a href="{html.escape(p["url"])}">{html.escape(p["name"].strip())}</a></h3>'
            f'<p>{html.escape(p["description"])}</p>'
            f'<p>SKU {html.escape(p["sku"])} · {CAT_LABEL.get(p["category"], "")} · {status}'
            + (f' · Materiales: {html.escape(mats)}' if mats else '') + '</p></li>')
    return ('<!-- STATIC-CATALOG:START (generado) -->\n<noscript><section class="wrap" style="padding:40px 0">'
            f'<h2>{heading}</h2><p>Precios mayoristas a pedido por WhatsApp {PHONE} o {EMAIL}. Envíos a todo el país.</p>'
            f'<ul>{"".join(rows)}</ul></section></noscript>\n<!-- STATIC-CATALOG:END -->')


def replace_block(t, start, end, new, anchor_before=None, anchor_after=None):
    pat = re.compile(re.escape(start) + r'.*?' + re.escape(end), re.S)
    if pat.search(t):
        return pat.sub(lambda m: new, t)
    if anchor_before:
        return t.replace(anchor_before, new + '\n' + anchor_before, 1)
    return t.replace(anchor_after, anchor_after + '\n' + new, 1)


# old tags now handled by the SEO block
OLD_HEAD = [
    r'\n?<!-- Open Graph -->',
    r'\n?<meta property="og:[^>]*>',
    r'\n?<meta name="twitter:[^>]*>',
    r'\n?<!-- JSON-LD: Organization \+ ItemList del catálogo -->',
]

for fname in PAGES:
    p = ROOT / fname
    t = p.read_text(encoding='utf-8')
    if 'SEO:START' not in t:
        for pat in OLD_HEAD:
            t = re.sub(pat, '', t)
    t = replace_block(t, '<!-- SEO:START', '<!-- SEO:END -->', head_block(fname, t), anchor_before='<link rel="preconnect" href="https://fonts.googleapis.com">')
    if fname == 'index.html':
        t = replace_block(t, '<!-- STATIC-CATALOG:START', '<!-- STATIC-CATALOG:END -->',
                          noscript_catalog(products, 'Catálogo mayorista BIVA'), anchor_before='<div class="catalog-empty" hidden>')
    elif fname in ('cocina.html', 'jardin.html'):
        cat = fname.split('.')[0]
        t = replace_block(t, '<!-- STATIC-CATALOG:START', '<!-- STATIC-CATALOG:END -->',
                          noscript_catalog([x for x in products if x['category'] == cat], CAT_LABEL[cat] + ' por mayor'),
                          anchor_before='<div class="vit-empty"')
    p.write_text(t, encoding='utf-8')

# sitemap.xml
urls = ''.join(f'  <url><loc>{BASE}{c["path"]}</loc><lastmod>{TODAY}</lastmod></url>\n' for c in PAGES.values())
urls += ''.join(f'  <url><loc>{abs_url(p["url"])}</loc><lastmod>{TODAY}</lastmod><image:image><image:loc>{abs_url(p["gallery"][0])}</image:loc></image:image></url>\n' for p in products if p.get('gallery'))
(ROOT / 'sitemap.xml').write_text(
    '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n' + urls + '</urlset>\n',
    encoding='utf-8')

# robots.txt — permitir buscadores y asistentes de IA
(ROOT / 'robots.txt').write_text(f'''# BIVA · bivasil.com
User-agent: *
Allow: /

# Asistentes y buscadores de IA: bienvenidos (GEO)
User-agent: GPTBot
Allow: /
User-agent: OAI-SearchBot
Allow: /
User-agent: ChatGPT-User
Allow: /
User-agent: ClaudeBot
Allow: /
User-agent: Claude-SearchBot
Allow: /
User-agent: PerplexityBot
Allow: /
User-agent: Google-Extended
Allow: /

Sitemap: {BASE}/sitemap.xml
''', encoding='utf-8')

# llms.txt — resumen legible para modelos de lenguaje
lines = [
    '# BIVA', '',
    '> BIVA (BIVASIL) es una importadora y distribuidora mayorista argentina de artículos para el hogar: '
    'utensilios de cocina, bazar, vajilla, organización y jardín. Base y depósito en Mar del Plata, '
    'provincia de Buenos Aires. Vende solo a comercios (bazares, ferreterías, casas de cocina, tiendas de deco) '
    'y hace envíos a todo el país. Precios mayoristas a pedido.', '',
    '## Datos clave',
    '- Modelo: B2B, solo mayoristas. No vende al consumidor final.',
    '- Importación directa, stock propio ya nacionalizado en Argentina.',
    '- Cobertura: todo el país. Visitas con muestra en Mar del Plata y la Costa Atlántica; entrega 24–72 h en esa zona.',
    f'- Contacto: WhatsApp {PHONE} · {EMAIL} · Instagram {IG}',
    '- Horario: lunes a viernes, 9 a 18 h.',
    '- Cómo comprar: escribir por WhatsApp indicando tipo de comercio → BIVA envía lista con precios mayoristas y stock → despacho.', '',
    '## Páginas',
    f'- [Inicio y catálogo completo]({BASE}/)',
    f'- [Cocina y bazar]({BASE}/cocina.html)',
    f'- [Jardín]({BASE}/jardin.html)',
    f'- [Nosotros]({BASE}/nosotros.html)',
    f'- [Contacto]({BASE}/contacto.html)', '',
]
for cat in ('cocina', 'jardin'):
    lines.append(f'## Catálogo · {CAT_LABEL[cat]}')
    for p in products:
        if p['category'] != cat:
            continue
        st = '' if p['availability'] == 'in_stock' else ' (próximo ingreso)'
        lines.append(f'- [{p["name"].strip()}]({abs_url(p["url"])}) [{p["sku"]}]{st}: {(p["shortDescription"].strip() or p["description"].split(". ")[0]).rstrip(".")}')
    lines.append('')
(ROOT / 'llms.txt').write_text('\n'.join(lines), encoding='utf-8')

print(f'OK · {len(products)} productos · {TODAY}')
