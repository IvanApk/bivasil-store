#!/usr/bin/env python3
"""
BIVA · copias livianas de las fotos de producto.

    python3 _tools/optimize_images.py

Por cada producto de products.json toma su foto principal y las fotos
hermanas (mismo nombre terminado en _2, -3, etc.) y genera en images/p/:
  <slug>-1.jpg, <slug>-2.jpg…  (1200 px, para la página del producto)
  <slug>-sm.jpg                (600 px, para grillas, buscador y carrusel)
Los originales no se tocan. Guarda las rutas nuevas en products.json
("slug", "gallery", "thumb"). Solo procesa lo que falta o cambió.
"""
import json, re, pathlib, unicodedata
from PIL import Image, ImageOps

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / 'images' / 'p'
OUT.mkdir(parents=True, exist_ok=True)
EXTS = ('.jpg', '.jpeg', '.png', '.webp')


def slugify(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode()
    s = re.sub(r'[^a-zA-Z0-9]+', '-', s).strip('-').lower()
    return re.sub(r'-+', '-', s)


def siblings(path):
    """All photos of the same product: foo_1.jpg -> foo_1, foo_2, foo_3…"""
    p = ROOT / path
    m = re.match(r'^(.*?)([_-])(\d+)(-alt)?$', p.stem)
    found = []
    if m:
        base, sep = m.group(1), m.group(2)
        for f in sorted(p.parent.iterdir()):
            if f.suffix.lower() not in EXTS:
                continue
            mm = re.match(r'^' + re.escape(base) + re.escape(sep) + r'(\d+)(-alt)?$', f.stem)
            if mm:
                found.append((int(mm.group(1)), bool(mm.group(2)), f))
        found.sort(key=lambda t: (t[0], t[1]))
        return [f for _, _, f in found]
    return [p]


def save(src, dst, width, quality):
    if dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime:
        return
    im = Image.open(src)
    im = ImageOps.exif_transpose(im)
    if im.mode in ('RGBA', 'LA', 'P'):
        im = im.convert('RGBA')
        bg = Image.new('RGB', im.size, (238, 234, 226))  # crema
        bg.paste(im, mask=im.split()[-1])
        im = bg
    else:
        im = im.convert('RGB')
    if im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    im.save(dst, 'JPEG', quality=quality, optimize=True, progressive=True)


data = json.loads((ROOT / 'products.json').read_text(encoding='utf-8'))
used = set()
for p in data['products']:
    slug = p.get('slug') or slugify(p['id'])
    if slug in used:
        slug = slugify(p['id'] + '-' + p['sku'])
    used.add(slug)
    p['slug'] = slug
    srcs = []
    for img in (p.get('images') or []) + [p['image']]:
        for s in siblings(img):
            if s not in srcs:
                srcs.append(s)
    # the declared cover goes first
    cover = ROOT / p['image']
    if cover in srcs:
        srcs.remove(cover)
        srcs.insert(0, cover)
    srcs = srcs[:6]
    gallery = []
    for i, s in enumerate(srcs, 1):
        dst = OUT / f'{slug}-{i}.jpg'
        save(s, dst, 1200, 80)
        gallery.append(f'images/p/{dst.name}')
    thumb = OUT / f'{slug}-sm.jpg'
    save(srcs[0], thumb, 600, 78)
    p['gallery'] = gallery
    p['thumb'] = f'images/p/{thumb.name}'

(ROOT / 'products.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
n = len(list(OUT.glob('*.jpg')))
mb = sum(f.stat().st_size for f in OUT.glob('*.jpg')) / 1e6
print(f'OK · {len(data["products"])} productos · {n} archivos · {mb:.1f} MB en images/p/')
