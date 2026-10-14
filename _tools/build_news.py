#!/usr/bin/env python3
"""
BIVA · sección Novedades (/novedades/).

Cada novedad es un archivo de texto en  _novedades/AAAA-MM-DD-titulo-corto.md :

    ---
    titulo: Llegó la vajilla Drift
    fecha: 2026-10-20
    resumen: Una línea que se ve en el listado y en Google.
    imagen: drift-llegada.jpg        (foto en _novedades/fotos/, o un SKU: BV-COC-17)
    productos: BV-COC-17, BV-COC-18  (opcional: muestra esas fichas al final)
    ---
    Texto de la novedad. Admite **negrita**, listas con "-" y [links](https://…).

Genera /novedades/index.html y /novedades/<slug>/index.html, y fotos livianas en images/n/.
Normalmente se corre desde  python3 _tools/build.py
"""
import json, html, re, shutil, datetime, pathlib, hashlib, urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / '_novedades'
OUT = ROOT / 'novedades'
IMG = ROOT / 'images' / 'n'
BASE = 'https://bivasil.com'
MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto',
         'septiembre', 'octubre', 'noviembre', 'diciembre']
e = lambda s: html.escape(str(s or ''), quote=True)
cn = lambda s: re.sub(r'\s*·\s*', ' ', s).strip()


def slug_of(path):
    return re.sub(r'^\d{4}-\d{2}-\d{2}-', '', path.stem)


def parse(path):
    raw = path.read_text(encoding='utf-8')
    m = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)$', raw, re.S)
    meta, body = ({}, raw) if not m else ({}, m.group(2))
    if m:
        for line in m.group(1).splitlines():
            if ':' in line:
                k, v = line.split(':', 1)
                meta[k.strip().lower()] = v.strip()
    fecha = meta.get('fecha') or path.stem[:10]
    try:
        d = datetime.date.fromisoformat(fecha)
    except ValueError:
        d = datetime.date.today()
    return {
        'slug': slug_of(path),
        'titulo': meta.get('titulo') or slug_of(path).replace('-', ' ').capitalize(),
        'fecha': d,
        'resumen': meta.get('resumen', ''),
        'imagen': meta.get('imagen', ''),
        'productos': [s.strip() for s in meta.get('productos', '').split(',') if s.strip()],
        'borrador': meta.get('borrador', '').lower() in ('si', 'sí', 'true', '1'),
        'body': body.strip(),
    }


def load_posts():
    if not SRC.is_dir():
        return []
    posts = [parse(p) for p in sorted(SRC.glob('*.md'))]
    posts = [p for p in posts if not p['borrador'] and p['fecha'] <= datetime.date.today()]
    return sorted(posts, key=lambda p: p['fecha'], reverse=True)


def fecha_larga(d):
    return f'{d.day} de {MESES[d.month - 1]} de {d.year}'


def to_html(md):
    try:
        import markdown
        return markdown.markdown(md, extensions=['extra', 'sane_lists'])
    except ImportError:  # fallback mínimo
        paras = [p.strip() for p in md.split('\n\n') if p.strip()]
        return '\n'.join(f'<p>{e(p)}</p>' for p in paras)


def plain(md):
    t = re.sub(r'!\[[^\]]*\]\([^)]*\)', '', md)
    t = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', t)
    return re.sub(r'\s+', ' ', re.sub(r'[*_#>`-]', ' ', t)).strip()


def optimize(src, dst, width=1200):
    from PIL import Image, ImageOps
    fp = hashlib.sha1(src.read_bytes()).hexdigest()[:12]
    stamp = dst.with_suffix('.huella')
    if dst.exists() and stamp.exists() and stamp.read_text() == fp:
        return
    im = ImageOps.exif_transpose(Image.open(src)).convert('RGB')
    if im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    im.save(dst, 'JPEG', quality=80, optimize=True, progressive=True)
    stamp.write_text(fp)


def run():
    products = json.loads((ROOT / 'products.json').read_text(encoding='utf-8'))
    site = products['site']
    prods = {p['sku']: p for p in products['products'] if p.get('published', True) and p.get('gallery')}
    WA = site['contact']['whatsapp'].lstrip('+')
    EMAIL = site['contact']['email']
    IG = site['contact']['instagram']
    posts = load_posts()

    IMG.mkdir(parents=True, exist_ok=True)
    keep = set()
    for p in posts:
        img = p['imagen']
        if re.match(r'^BV-[A-Z]{3}-\d+$', img) and img in prods:
            p['img'] = prods[img]['gallery'][0]
        elif img and (SRC / 'fotos' / img).is_file():
            dst = IMG / f'{p["slug"]}.jpg'
            optimize(SRC / 'fotos' / img, dst)
            keep.update({dst.name, dst.with_suffix('.huella').name})
            p['img'] = f'images/n/{dst.name}'
        elif p['productos'] and p['productos'][0] in prods:
            p['img'] = prods[p['productos'][0]]['gallery'][0]
        else:
            p['img'] = 'images/og-bivasil.jpg'
        p['url'] = f'/novedades/{p["slug"]}/'
        p['desc'] = p['resumen'] or plain(p['body'])[:155]
    for f in IMG.glob('*'):
        if f.name not in keep:
            f.unlink()

    head = lambda title, desc, url, image, extra='': f'''<!doctype html>
<html lang="es-AR">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}" />
<link rel="canonical" href="{url}" />
<meta name="robots" content="index, follow, max-image-preview:large" />
<meta name="theme-color" content="#333330" />
<link rel="icon" href="/favicon.ico" sizes="48x48" />
<link rel="icon" href="/favicon.svg" type="image/svg+xml" />
<link rel="icon" href="/favicon-96.png" sizes="96x96" type="image/png" />
<link rel="apple-touch-icon" href="/apple-touch-icon.png" />
<link rel="manifest" href="/site.webmanifest" />
<meta property="og:type" content="article" />
<meta property="og:site_name" content="BIVA" />
<meta property="og:locale" content="es_AR" />
<meta property="og:title" content="{e(title)}" />
<meta property="og:description" content="{e(desc)}" />
<meta property="og:url" content="{url}" />
<meta property="og:image" content="{BASE}/{image}" />
<meta name="twitter:card" content="summary_large_image" />
{extra}
<script src="/analytics.js" defer></script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Gloock&family=Work+Sans:wght@300;400;500;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/styles.css" />
<link rel="stylesheet" href="/catalog.css" />
<link rel="stylesheet" href="/product.css" />
<link rel="stylesheet" href="/news.css" />
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
      <a href="/cocina.html">Cocina</a>
      <a href="/jardin.html">Jardín</a>
      <a href="/novedades/" class="active">Novedades</a>
      <a href="/nosotros.html">Nosotros</a>
      <a href="/contacto.html">Contacto</a>
    </div>
    <a class="nav-cta" href="https://wa.me/{WA}" target="_blank" rel="noopener">WhatsApp</a>
  </div>
</nav>
'''
    foot = f'''
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
        <li><a href="/novedades/">Novedades</a></li>
        <li><a href="/contacto.html">Contacto</a></li>
        <li><a href="/preguntas-frecuentes.html">Preguntas frecuentes</a></li>
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
    <span>© {datetime.date.today().year} BIVA · Mar del Plata, Argentina</span>
    <span>Solo mayoristas · bivasil.com</span>
  </div>
</footer>
<script src="/catalog.js"></script>
<script src="/site.js"></script>
</body>
</html>
'''
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()

    # listado
    cards = ''.join(f'''
      <a class="nw-card" href="{p['url']}">
        <div class="product-frame wide"><img class="product-img" src="/{e(p['img'])}" alt="{e(p['titulo'])}" loading="lazy" /></div>
        <time datetime="{p['fecha'].isoformat()}">{fecha_larga(p['fecha'])}</time>
        <h2>{e(p['titulo'])}</h2>
        <p>{e(p['desc'])}</p>
      </a>''' for p in posts) or '<p class="nw-empty">Pronto vas a encontrar acá las últimas llegadas y novedades de BIVA.</p>'
    list_ld = json.dumps({"@context": "https://schema.org", "@type": "Blog", "@id": BASE + "/novedades/#blog",
        "name": "Novedades BIVA", "url": BASE + "/novedades/", "inLanguage": "es-AR",
        "publisher": {"@id": BASE + "/#org"},
        "blogPost": [{"@type": "BlogPosting", "headline": p['titulo'], "url": BASE + p['url'],
                      "datePublished": p['fecha'].isoformat()} for p in posts]}, ensure_ascii=False)
    (OUT / 'index.html').write_text(
        head('Novedades · Llegadas y lanzamientos · BIVA mayorista',
             'Últimas llegadas, productos nuevos y novedades de BIVA, importador mayorista de cocina, bazar y jardín con envíos a todo el país.',
             BASE + '/novedades/', 'images/og-bivasil.jpg',
             f'<script type="application/ld+json">{list_ld}</script>')
        + f'''
<main class="nw">
  <div class="wrap">
    <div class="eyebrow">Novedades</div>
    <h1 class="h-display" style="margin-top: 20px;">Lo último<br/><em class="sage">en el depósito.</em></h1>
    <p class="h-tagline" style="margin-top: 28px;">Llegadas, productos nuevos y todo lo que pasa en BIVA.</p>
    <div class="nw-grid">{cards}
    </div>
  </div>
</main>''' + foot, encoding='utf-8')

    # cada novedad
    for i, p in enumerate(posts):
        url = BASE + p['url']
        rel = [prods[s] for s in p['productos'] if s in prods]
        rel_html = ''
        if rel:
            rel_html = '<section class="nw-products"><h2 class="h-section">Productos de esta novedad</h2><div class="pd-related-grid">' + ''.join(
                f'<a class="rel-card" href="{r["url"]}"><div class="product-frame"><img class="product-img" src="/{e(r["thumb"])}" alt="{e(r["name"])}" loading="lazy" /></div>'
                f'<span>{e(r["sku"])}</span><h3>{e(cn(r["name"]))}</h3></a>' for r in rel) + '</div></section>'
        msg = urllib.parse.quote(f'Hola BIVA. Vi la novedad "{p["titulo"]}" en la web y quería consultar precios mayoristas.')
        others = [o for o in posts if o is not p][:3]
        more = ''
        if others:
            more = '<section class="nw-more"><h2 class="eyebrow">Más novedades</h2><ul>' + ''.join(
                f'<li><a href="{o["url"]}"><time>{fecha_larga(o["fecha"])}</time> {e(o["titulo"])}</a></li>' for o in others) + '</ul></section>'
        ld = json.dumps({"@context": "https://schema.org", "@graph": [
            {"@type": "BlogPosting", "@id": url + "#post", "headline": p['titulo'], "description": p['desc'],
             "datePublished": p['fecha'].isoformat(), "dateModified": p['fecha'].isoformat(),
             "image": BASE + '/' + p['img'], "url": url, "inLanguage": "es-AR", "mainEntityOfPage": url,
             "author": {"@type": "Organization", "name": "BIVA", "url": BASE + "/"},
             "publisher": {"@type": "Organization", "@id": BASE + "/#org", "name": "BIVA",
                           "logo": {"@type": "ImageObject", "url": BASE + "/logo-512.png"}},
             **({"about": [{"@type": "Product", "name": r['name'], "sku": r['sku'], "url": BASE + r['url']} for r in rel]} if rel else {})},
            {"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Inicio", "item": BASE + "/"},
                {"@type": "ListItem", "position": 2, "name": "Novedades", "item": BASE + "/novedades/"},
                {"@type": "ListItem", "position": 3, "name": p['titulo'], "item": url}]}]}, ensure_ascii=False).replace('</', '<\\/')
        d = OUT / p['slug']
        d.mkdir()
        (d / 'index.html').write_text(
            head(f'{p["titulo"]} · Novedades BIVA', p['desc'], url, p['img'],
                 f'<meta property="article:published_time" content="{p["fecha"].isoformat()}" />\n<script type="application/ld+json">{ld}</script>')
            + f'''
<main class="nw nw-post">
  <div class="wrap">
    <nav class="crumbs" aria-label="Ruta"><ol><li><a href="/">Inicio</a></li><li><a href="/novedades/">Novedades</a></li><li><span aria-current="page">{e(p['titulo'])}</span></li></ol></nav>
    <article>
      <time class="eyebrow" datetime="{p['fecha'].isoformat()}">{fecha_larga(p['fecha'])}</time>
      <h1 class="pd-title">{e(p['titulo'])}</h1>
      {f'<p class="h-tagline">{e(p["resumen"])}</p>' if p['resumen'] else ''}
      <div class="nw-hero product-frame wide"><img class="product-img" src="/{e(p['img'])}" alt="{e(p['titulo'])}" /></div>
      <div class="nw-body">{to_html(p['body'])}</div>
      <div class="pd-actions">
        <a class="btn btn-dark" href="https://wa.me/{WA}?text={msg}" target="_blank" rel="noopener">Consultar por WhatsApp</a>
        <a class="pd-mail" href="mailto:{EMAIL}">o escribinos a {EMAIL}</a>
      </div>
    </article>
    {rel_html}
    {more}
  </div>
</main>''' + foot, encoding='utf-8')

    print(f'Novedades · {len(posts)} publicadas')
    return posts


if __name__ == '__main__':
    run()
