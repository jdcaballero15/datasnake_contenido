# Diseño — Placas densas (rediseño visual v2)

Fecha: 2026-07-13
Estado: aprobado (pendiente de plan de implementación)

## Problema

Las placas actuales (post-rediseño de 2026-07-03) tienen tres defectos, en orden de
prioridad según el dueño de la cuenta:

1. **Ritmo y jerarquía (principal).** Una placa de contenido muestra: kicker → título
   88px → regla → tarjeta con 2–3 líneas a 38px. Lo más importante para el lector —la
   explicación— es lo más chico de la placa, y el contenido ocupa cerca de un tercio del
   lienzo: el resto es aire. No es un artefacto del `--dry-run`: los textos reales de los
   bancos rondan los 120–180 caracteres, así que con contenido real el vacío persiste.
   La causa es estructural: **una idea trae muy poco contenido** (`titulo` + `texto`), y
   ninguna plantilla llena una placa de 1080×1350 con eso.
2. **Color.** La portada usa el azul `#2A7FA8` como fondo con texto casi negro: se lee
   apagado y "sucio". El verde y el violeta de la marca (los colores del logo) casi no
   aparecen.
3. **Consistencia entre tipos.** Las 4 piezas de un lote se ven idénticas; lo único que
   cambia es el kicker.

## Referencia

`referencia/Captura desde 2026-07-03 16-55-*.png` (carrusel de @adrian.alvarezl). Rasgos
que queremos adoptar:

- Portada de color saturado con título negro en condensada ultra-bold, más un deck de dos
  líneas chico.
- Placas de contenido **densas**: kicker → título gigante en acento → deck bold → panel con
  **varias secciones etiquetadas** (`➤ QUÉ HACE`, `➤ CÓMO LO INSTALAS`, `➤ LINK`), cuerpo
  chico pero abundante, con bloque de código embebido cuando corresponde.
- Ritmo de fondos: placas oscuras alternadas con alguna placa clara, cambiando el color del
  título.
- La estructura se **repite igual en cada placa**: eso es lo que la hace ver profesional.

Lo que NO adoptamos: el naranja (no es color de marca; pelearía con el logo verde/violeta).

## Decisiones

| Decisión | Elegido | Por qué |
|---|---|---|
| Alcance | Rediseño completo, **por etapas** | Llegar a la referencia exige tocar el contrato de contenido, no solo el CSS; hacerlo por etapas evita apostar todo de una a que Gemini respete un contrato más complejo al primer intento |
| Labels de sección | **Fijos por tipo, definidos en el código** | Consistencia semana a semana + validación estricta; los bancos son más simples de llenar |
| Color | **Paleta de marca con el ritmo de la referencia** | Verde `#2EE6A6` en el rol del turquesa, violeta `#7C5CBF` en el rol del naranja |
| Tipografía de títulos | **Anton** (Google Fonts) | Condensada ultra-bold: es la mitad del carácter de la referencia. Archivo 900 es demasiado ancha y blanda |

## Modelo de contenido

Una idea pasa de `{titulo, texto}` a:

```
titulo     str            — gigante, en color acento
deck       str            — 1–2 líneas, bold: resume la idea de un vistazo
secciones  [{label, texto}] — 2–3 bloques etiquetados; labels fijos por tipo
codigo     str | None     — opcional, se renderiza en mono dentro de su sección
```

Labels fijos por tipo (definidos en el código, no en el contenido):

| Tipo | Secciones |
|---|---|
| `novedad` | ➤ QUÉ CAMBIÓ · ➤ POR QUÉ IMPORTA |
| `comparativa` | ➤ CUÁNDO CONVIENE · ➤ DÓNDE DUELE |
| `rol` | ➤ POR QUÉ TE LA PIDEN · ➤ CÓMO LA PRACTICÁS (cada placa es una skill del rol) |
| `tip` | ➤ EL PROBLEMA · ➤ EL CÓDIGO · ➤ POR QUÉ FUNCIONA |

Descartado: la sección `➤ SUELDO` del borrador inicial. Los bancos no traen sueldos y
`VOZ_DE_MARCA` prohíbe inventar números, así que solo se podría llenar inventando.
El `veredicto` de una comparativa tampoco entra en las placas (las secciones son fijas):
sigue viviendo en el caption.

En `tip`, el `codigo` se renderiza dentro de la sección `EL CÓDIGO`; deja de existir la
placa `codigo.html` separada.

## Sistema visual

**Tipografía**

- Títulos: **Anton** (un solo peso; condensada, alta, angosta).
- Deck y cuerpo: **Archivo** (500 / 700 / 900) — la que ya usamos.
- Código: **JetBrains Mono**.

**Color** (sobre la paleta existente de `src/config.py`, sin colores nuevos)

- Portada: fondo verde `#2EE6A6`, texto midnight `#111827`.
- Placa de contenido oscura: fondo `#111827`, título verde `#2EE6A6`, deck `#FFFFFF`,
  cuerpo `#CBD5E1`, panel `#1C2B3A`.
- Placa de contenido clara: fondo hueso `#EEE9E1`, título violeta `#7C5CBF`, cuerpo
  `#111827`, panel oscuro `#111827` con cuerpo `#CBD5E1`. Aplica a las placas de contenido
  cuyo número de idea es múltiplo de 3 (la 3ª, la 6ª): si una pieza tiene menos de 3 ideas,
  simplemente no lleva placa clara.
- Cierre: oscuro, con logo.
- El azul `#2A7FA8` deja de ser fondo de portada; queda para detalles.

**Layout de la placa de contenido**

```
@data.snake                                    03 / 08     ← header (sin cambios)
— TIP 02                                                   ← kicker
TÍTULO GIGANTE.                                            ← Anton, acento
Deck bold, una o dos líneas.                               ← Archivo 700, blanco
┌───────────────────────────────────────────┐
│ ➤ EL PROBLEMA                              │              ← panel de secciones
│ cuerpo ~32–34px …                          │
│ ➤ EL CÓDIGO                                │
│ [bloque mono]                              │
│ ➤ POR QUÉ FUNCIONA                         │
│ cuerpo …                                   │
└───────────────────────────────────────────┘
DESLIZA →            • • ● • •           GUARDAR ■          ← footer (sin cambios)
```

El contenido arranca arriba y **baja llenando**: se elimina el `margin-top:auto` que hoy
centra el bloque y produce el aire muerto. Header y footer se mantienen: ya coinciden con
la referencia.

## Etapas

**Etapa 1 — sistema visual + datos propios**

- Plantillas nuevas (`portada`, `contenido`, `cierre`), `_estilos.html` con Anton, la paleta
  y la variante clara; se elimina `codigo.html` (el código pasa a ser una sección).
- Bancos evergreen (`datos/comparativas.json`, `datos/roles.json`, `datos/tips.json`)
  enriquecidos con `deck` y `secciones`.
- La `novedad` (Gemini/RSS) se adapta al modelo nuevo con un puente mínimo: su `texto`
  actual entra como una sola sección. Nada se rompe mientras Gemini siga con el contrato
  viejo.

**Etapa 2 — Gemini**

- `src/redaccion/prompts.py`: prompts que pidan `deck` + `secciones` completas por tipo.
- `src/redaccion/contratos.py`: validación de la estructura nueva (secciones presentes,
  labels esperados, largos máximos).
- `src/main.py:plan_b()`: arma `deck` + `secciones` sin IA a partir del propio item.

## Verificación

Los tests no alcanzan: cada cambio se verifica **renderizando de verdad** (`python -m
src.main --dry-run`) y mirando los PNG resultantes. Los tests de render y contratos se
actualizan al modelo nuevo; el resto de la suite debe seguir en verde.
