# Diseño — Rediseño visual de carruseles Data Snake

> Fecha: 2026-07-03.

## Objetivo

Mejorar la estética de las placas generadas por Data Snake sin copiar literalmente las
referencias provistas. La dirección aprobada es: **tomar la estructura editorial/modular
de las referencias y mantener identidad propia de Data Snake**.

El resultado buscado es que los carruseles se vean menos planos y más diseñados: tapas
con carácter, interiores técnicos legibles, bloques modulares para código/beneficios y
una navegación visual de carrusel consistente.

## Referencias usadas

Las imágenes en `referencia/` muestran un sistema con:

- Títulos grandes, condensados y muy jerárquicos.
- Alternancia de fondos claros, oscuros y de color sólido.
- Placas interiores con bloques tipo “qué hace”, “cómo lo probás”, “link” o código.
- Footer persistente con handle, paginación, “desliza” y “guardar”.
- Acentos fuertes por sección.

La adaptación para Data Snake no debe ser un clon. Se toma la lógica de composición, no
la identidad visual exacta.

## Identidad Data Snake

Se conserva:

- Marca: `@data.snake`.
- Eslogan: “Herramientas, resultados y carrera en data”.
- Paleta base de `src/config.py`: fondo dark, Ocean Blue, verde del logo y violeta como
  acento secundario.
- Tono técnico, orientado a resultados, para gente que ya está en data/tech.

Se ajusta:

- El sistema deja de ser “todo dark plano”.
- El azul Data Snake puede aparecer como fondo de tapa o acento dominante.
- El verde del logo pasa a funcionar como acento técnico principal.
- El violeta/naranja se usan con moderación para distinguir tipos de contenido o placas
  especiales.

## Sistema visual propuesto

### Tapa

La portada debe ser una pieza editorial fuerte:

- Fondo sólido de marca, preferentemente `COLOR_ACENTO` o dark según el tipo de pieza.
- Header superior con `@data.snake` y número de placa, por ejemplo `01 / 06`.
- Kicker corto: categoría o contexto (`Herramientas · data`, `Comparativa`, `SQL`).
- Título enorme, en mayúsculas, máximo 3-4 líneas.
- Subtítulo breve, concreto y orientado al resultado.
- Footer con “desliza”, puntos de progreso y “guardar”.

La tapa debe entenderse en un segundo y no depender de párrafos largos.

### Placas interiores

Las placas interiores usan una estructura modular:

- Header con handle y progreso.
- Kicker de sección: `— opción 01`, `— skill`, `— veredicto`, `— caso`.
- Título grande, pero menor que portada.
- Línea/acento corto bajo el título.
- Texto principal en 1-2 frases.
- Módulo interno cuando aporte claridad:
  - `› qué hace`
  - `› cuándo conviene`
  - `› pruébalo`
  - `› regla simple`
  - `› código`

Los módulos deben parecer parte de una herramienta/data product: sobrios, técnicos,
con borde o superficie definida, no tarjetas decorativas.

### Código y terminal

Las placas con snippets deben usar un bloque tipo terminal/editor:

- Fondo más oscuro que la placa.
- Tipografía mono.
- Borde/acento lateral en verde o azul.
- Máximo de líneas visible sin apretar el texto.
- Si el código es largo, priorizar fragmento o ejemplo de uso en vez de llenar la placa.

### Alternancia de fondos

El carrusel debe alternar, de forma controlada:

- Tapa en color sólido de marca.
- Placas dark técnicas.
- Algunas placas claras para respirar, sobre todo veredictos/cierres o comparativas.

No todas las placas deben usar todos los recursos. La consistencia viene de la grilla,
tipografía, header/footer y módulos, no de repetir exactamente el mismo layout.

## Plantillas afectadas

El rediseño impacta:

- `plantillas/_estilos.html`
- `plantillas/portada.html`
- `plantillas/idea.html`
- `plantillas/comparativa.html`
- `plantillas/codigo.html`
- `plantillas/cierre.html`

El renderer y el orquestador no deberían cambiar salvo que haga falta pasar metadatos de
paginación o variantes visuales por placa.

## Criterios de aceptación

- El dry-run genera placas PNG sin errores.
- Las placas mantienen 1080×1350.
- La tapa tiene jerarquía clara y no se ve como template genérico.
- Las placas interiores tienen módulos técnicos legibles.
- El texto no se pisa ni se sale del canvas.
- Hay footer/paginación consistente.
- El sistema mantiene identidad Data Snake y no copia literalmente las referencias.
- `python -m pytest -q` sigue pasando.
- `python -m src.main --dry-run` genera un lote revisable.

## Fuera de alcance

- Cambiar lógica de selección de contenido.
- Cambiar prompts de redacción salvo ajustes menores para adaptar títulos/subtítulos al
  nuevo sistema.
- Incorporar imágenes externas o fotos.
- Rediseñar la marca/logo.

## Aprobación de dirección

Dirección aprobada por el usuario: **tomar estructura editorial/modular de las
referencias y mantener más identidad propia de marca**.
