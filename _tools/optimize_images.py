#!/usr/bin/env python3
"""
BIVA · fotos livianas para la web.

Las fotos originales van en  _fotos/<SKU>/  (ej. _fotos/BV-COC-59/1.jpg, 2.jpg…).
El orden lo da el nombre: 1 es la foto principal. La carpeta _fotos no se publica.

Genera en images/p/:
  <slug>-1.jpg, <slug>-2.jpg…  (1200 px, página del producto)
  <slug>-sm.jpg                (600 px, grillas, buscador y carrusel)

Solo procesa fotos nuevas o cambiadas (compara una huella de cada original)
y borra las fotos de productos que ya no existen.
Guarda en products.json: "gallery", "thumb" e "image".
"""
import json, re, hashlib, pathlib
from PIL import Image, ImageOps

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / '_fotos'
OUT = ROOT / 'images' / 'p'
OUT.mkdir(parents=True, exist_ok=True)
MANIFEST = OUT / '.huellas.json'
EXTS = ('.jpg', '.jpeg', '.png', '.webp')
MAX_PHOTOS = 8

manifest = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}


def natural_key(p):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', p.stem)]


def photos_for(sku):
    folder = SRC / sku
    if not folder.is_dir():
        return []
    return sorted([f for f in folder.iterdir() if f.suffix.lower() in EXTS], key=natural_key)[:MAX_PHOTOS]


def fingerprint(src, width):
    h = hashlib.sha1(src.read_bytes()).hexdigest()[:16]
    return f'{h}:{width}'


def save(src, dst, width, quality):
    fp = fingerprint(src, width)
    if dst.exists() and manifest.get(dst.name) == fp:
        return False
    im = ImageOps.exif_transpose(Image.open(src))
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
    manifest[dst.name] = fp
    return True


def run():
    data = json.loads((ROOT / 'products.json').read_text(encoding='utf-8'))
    keep, made, missing = set(), 0, []
    for p in data['products']:
        srcs = photos_for(p['sku'])
        if not srcs:
            missing.append(p['sku'])
            p['gallery'], p['thumb'] = [], ''
            continue
        gallery = []
        for i, s in enumerate(srcs, 1):
            dst = OUT / f'{p["slug"]}-{i}.jpg'
            made += save(s, dst, 1200, 80)
            gallery.append(f'images/p/{dst.name}')
            keep.add(dst.name)
        thumb = OUT / f'{p["slug"]}-sm.jpg'
        made += save(srcs[0], thumb, 600, 78)
        keep.add(thumb.name)
        p['gallery'], p['thumb'], p['image'] = gallery, f'images/p/{thumb.name}', gallery[0]
        p.pop('images', None)

    removed = 0
    for f in OUT.glob('*.jpg'):
        if f.name not in keep:
            f.unlink()
            manifest.pop(f.name, None)
            removed += 1
    MANIFEST.write_text(json.dumps(dict(sorted(manifest.items())), indent=0) + '\n')
    (ROOT / 'products.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Fotos · {made} generadas, {removed} borradas, {len(keep)} en total')
    if missing:
        print(f'  ⚠ Sin fotos (no se publican): {", ".join(missing)} → subilas a _fotos/<SKU>/')
    return missing


if __name__ == '__main__':
    run()
