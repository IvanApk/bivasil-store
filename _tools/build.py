#!/usr/bin/env python3
"""
BIVA · reconstruye todo lo generado a partir de products.json.

    python3 _tools/build.py

1. optimize_images.py  → fotos livianas en images/p/
2. build_products.py   → una página por producto en /productos/<slug>/
3. build_seo.py        → datos estructurados, catálogo rastreable, sitemap, robots, llms.txt
"""
import runpy, pathlib
here = pathlib.Path(__file__).resolve().parent
for s in ('optimize_images.py', 'build_products.py', 'build_seo.py'):
    runpy.run_path(str(here / s), run_name='__main__')
