"""Columnas de la planilla de productos (compartido por sync_sheet.py y export_sheet.py)."""

# (encabezado en la planilla, clave interna, ancho de columna, ayuda)
COLUMNS = [
    ('SKU',                 'sku',              13, 'Código único. Es el nombre de la carpeta de fotos: _fotos/<SKU>/. No lo cambies una vez publicado.'),
    ('Nombre',              'name',             38, 'Usá " · " para separar la variante: "Juego de Bowls · Cerámica Blanca".'),
    ('Categoría',           'category',         12, 'Cocina o Jardín.'),
    ('Estado',              'availability',     16, 'En stock · Sin stock · Próximo ingreso.'),
    ('Publicado',           'published',        11, 'Sí = aparece en la web. No = oculto (la página deja de existir).'),
    ('Descripción corta',   'shortDescription', 45, 'Una línea. Se ve en el catálogo y debajo del título.'),
    ('Descripción',         'description',      60, 'El texto largo de la página del producto.'),
    ('Características',     'features',         45, 'Una por línea (Alt+Enter en Excel, Ctrl+Enter en Google Sheets).'),
    ('Materiales',          'materials',        28, 'Separados por coma.'),
    ('Ideal para',          'useCases',         28, 'Separados por coma.'),
    ('Etiquetas',           'tags',             28, 'Palabras para el buscador, separadas por coma.'),
    ('Unidades por bulto',  'packSize',         12, 'Opcional. Ej: 12'),
    ('Pedido mínimo',       'minOrder',         14, 'Opcional. Ej: 1 bulto'),
    ('Medidas',             'dimensions',       22, 'Opcional. Ej: 30 × 20 × 2 cm'),
    ('Foto',                'imageFit',         13, 'Recortada (llena el cuadro) o Completa (se ve entera, con margen).'),
    ('Dirección web',       'slug',             34, 'Se completa sola la primera vez. No la cambies: rompería los links ya compartidos.'),
]

CATEGORIES = {'cocina': 'Cocina', 'jardin': 'Jardín'}
AVAILABILITY = {'in_stock': 'En stock', 'out_of_stock': 'Sin stock', 'pre_order': 'Próximo ingreso'}
IMAGE_FIT = {'cover': 'Recortada', 'contain': 'Completa'}
