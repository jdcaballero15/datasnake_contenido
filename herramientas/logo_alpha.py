"""Convierte el logo de marca (arte luminoso sobre fondo negro) en un PNG cuadrado
con transparencia real, que es lo que las placas embeben.

    pip install pillow   # no va en requirements.txt: esto no corre en el pipeline
    python herramientas/logo_alpha.py marca/logos/logo-fuente.jpg marca/logos/logo.png

Solo hace falta correrlo si cambia el logo de la marca. El arte es luminoso sobre un
fondo casi-negro, así que alpha = max(r,g,b) recupera la silueta y conserva el glow
como degradado. Después "des-premultiplica" el color para que no quede lavado.
"""
import sys
from PIL import Image

ORIGEN, DESTINO = sys.argv[1], sys.argv[2]

img = Image.open(ORIGEN).convert("RGB")
ancho, alto = img.size
px = img.load()

# El "negro" del fondo no es puro: es un degradado que llega a ~35. Todo lo que
# esté por debajo de PISO es fondo y se descarta; el resto se reescala a 0-255.
PISO = 48
ESCALA = 255 / (255 - PISO)

salida = Image.new("RGBA", (ancho, alto))
sp = salida.load()
for y in range(alto):
    for x in range(ancho):
        r, g, b = px[x, y]
        pico = max(r, g, b)
        if pico <= PISO:
            sp[x, y] = (0, 0, 0, 0)
            continue
        a = min(255, int((pico - PISO) * ESCALA))
        # unpremultiply: devuelve el color a plena saturación
        f = 255 / pico
        sp[x, y] = (min(255, int(r * f)), min(255, int(g * f)), min(255, int(b * f)), a)

# Recorta el vacío y centra en un lienzo cuadrado con aire.
caja = salida.split()[3].point(lambda v: 255 if v > 12 else 0).getbbox()
arte = salida.crop(caja)
lado = max(arte.size) + 24
lienzo = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
lienzo.paste(arte, ((lado - arte.width) // 2, (lado - arte.height) // 2))
lienzo.save(DESTINO)
print(f"{ORIGEN} {img.size} -> {DESTINO} {lienzo.size} (bbox arte: {caja})")
