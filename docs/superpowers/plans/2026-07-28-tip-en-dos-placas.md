# El tip repartido en dos placas — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Repartir las tres secciones del tip en dos placas de contenido, llevando su carrusel de tres a cuatro slides, sin agregar secciones nuevas al tipo.

**Architecture:** El reparto se declara como dato en `src/contenido.py` (`PLACAS_POR_TIPO` + `grupos_de_placa`), con un default que deja intactos a novedad, comparativa y rol. `main.construir_placas` pasa a emitir una placa por cada grupo de cada idea; `contratos.validar` deriva de esos mismos grupos un tope de caracteres distinto para la sección que queda sola en su placa. Ningún módulo fuera de `contenido.py` nombra el string `"tip"` para decidir el reparto.

**Tech Stack:** Python 3, Jinja2, Playwright (Chromium), pytest.

## Global Constraints

- Español rioplatense en todo texto de usuario, comentarios y mensajes de commit. Los mensajes de commit van sin tildes (el repo los viene escribiendo así).
- Los labels de sección son fijos y viven solo en `src/contenido.py`. Nunca hardcodear un label como string literal fuera de ese archivo.
- Toda placa tiene `overflow:hidden`: un texto que se pasa de largo se corta en silencio. Cualquier tope de caracteres se confirma mirando un PNG renderizado, no a ojo.
- Novedad, comparativa y rol tienen que salir idénticas a como salían antes del cambio.
- Correr la suite completa con `python -m pytest` desde la raíz del repo.
- Trabajar sobre la rama `feat/tip-en-dos-placas`, que ya existe y tiene el spec commiteado.

---

### Task 1: El reparto de secciones como dato

**Files:**
- Modify: `src/contenido.py:44-56` (después de `SECCIONES_POR_TIPO` y `KICKER_POR_TIPO`)
- Test: `tests/test_contenido.py`

**Interfaces:**
- Consumes: `SECCIONES_POR_TIPO: dict[str, list[str]]`, ya existente en `src/contenido.py`.
- Produces: `PLACAS_POR_TIPO: dict[str, list[list[str]]]` y `grupos_de_placa(tipo: str) -> list[list[str]]`. Las tareas 2 y 4 consumen `grupos_de_placa`.

- [ ] **Step 1: Escribir los tests que fallan**

Agregar al final de `tests/test_contenido.py`:

```python
def test_grupos_de_placa_tip_se_parte_en_dos():
    """El tip es el único tipo con una sola idea: sin partirlo, sus tres
    secciones caen todas en la misma placa y la placa queda saturada."""
    assert contenido.grupos_de_placa("tip") == [
        ["el problema", "el código"],
        ["por qué funciona"],
    ]


def test_grupos_de_placa_los_demas_tipos_van_en_una_sola_placa():
    """El default es lo que mantiene intactos a los otros tres tipos: un grupo
    con todos sus labels, es decir una placa por idea, como siempre."""
    for tipo in ("novedad", "comparativa", "rol"):
        assert contenido.grupos_de_placa(tipo) == [contenido.SECCIONES_POR_TIPO[tipo]]


def test_grupos_de_placa_no_pierde_ni_duplica_ni_reordena_secciones():
    """Invariante del reparto: aplanar los grupos tiene que devolver
    exactamente los labels del tipo, en el mismo orden. Sin esto, un typo en
    PLACAS_POR_TIPO hace desaparecer una sección de la placa en silencio,
    porque construir_placas descarta los labels que no reconoce."""
    for tipo in contenido.SECCIONES_POR_TIPO:
        aplanado = [label for grupo in contenido.grupos_de_placa(tipo) for label in grupo]
        assert aplanado == contenido.SECCIONES_POR_TIPO[tipo], tipo
```

- [ ] **Step 2: Correr los tests para verificar que fallan**

Run: `python -m pytest tests/test_contenido.py -k grupos_de_placa -v`
Expected: FAIL con `AttributeError: module 'src.contenido' has no attribute 'grupos_de_placa'`

- [ ] **Step 3: Implementar**

En `src/contenido.py`, justo después del bloque `KICKER_POR_TIPO` (línea 56), agregar:

```python
PLACAS_POR_TIPO: dict[str, list[list[str]]] = {
    "tip": [["el problema", "el código"], ["por qué funciona"]],
}
"""Cómo se reparten las secciones de UNA idea entre placas del carrusel.

Solo aparece acá el tipo que necesita más de una placa. El tip es el único con
una sola idea, así que sin repartir sus tres secciones quedan apiladas en una
placa que se ve saturada; los demás tipos ya respiran porque emiten una placa
por unidad (una opción, una skill, un cambio).

El orden de los labels dentro de cada grupo, y el de los grupos entre sí, es el
orden en que se ven en el carrusel."""


def grupos_de_placa(tipo: str) -> list[list[str]]:
    """Los grupos de secciones de <tipo>: uno por placa de contenido.

    El default —un único grupo con todos los labels del tipo— es lo que deja a
    novedad, comparativa y rol exactamente como estaban: una placa por idea."""
    return PLACAS_POR_TIPO.get(tipo, [SECCIONES_POR_TIPO[tipo]])
```

- [ ] **Step 4: Correr los tests para verificar que pasan**

Run: `python -m pytest tests/test_contenido.py -v`
Expected: PASS (los tres nuevos y los que ya estaban)

- [ ] **Step 5: Commit**

```bash
git add src/contenido.py tests/test_contenido.py
git commit -m "feat: declarar el reparto de secciones en placas como dato"
```

---

### Task 2: `construir_placas` emite una placa por grupo

**Files:**
- Modify: `src/main.py:111-140` (función `construir_placas`)
- Test: `tests/test_main.py`

**Interfaces:**
- Consumes: `contenido.grupos_de_placa(tipo) -> list[list[str]]` de la Task 1.
- Produces: `construir_placas(tipo, red, variante_cover="cover-green") -> list[dict]`. Firma sin cambios. Las placas de continuación de una idea traen `titulo` y `deck` en `""` y el mismo `kicker` que la primera placa de esa idea.

- [ ] **Step 1: Arreglar el test existente que usa "tip" con secciones de comparativa**

`tests/test_main.py:52-58` llama a `construir_placas("tip", ...)` pasándole `IDEA`, cuyos labels son los de comparativa (`cuándo conviene` / `dónde duele`). Hoy pasa por casualidad: la plantilla no valida labels. Con el reparto, esos labels no pertenecen a ningún grupo del tip y la placa saldría vacía, así que el test dejaría de probar lo que dice probar.

El test mide la variante de portada, no nada específico del tip. Cambiar `"tip"` por `"comparativa"`:

```python
def test_construir_placas_usa_la_variante_de_portada_indicada():
    placas = main.construir_placas(
        "comparativa", {"titulo_portada": "X", "ideas": [IDEA]}, "cover-coral")

    assert placas[0]["variant"] == "cover-coral"
    assert placas[1]["variant"] == "dark"
    assert placas[-1]["variant"] == "close"
```

- [ ] **Step 2: Escribir los tests que fallan**

Agregar a `tests/test_main.py`, inmediatamente después de la constante `IDEA` (línea 34-36):

```python
IDEA_TIP = {"titulo": "DETECTÁ DUPLICADOS", "deck": "Encontrá qué filas se repiten.",
            "secciones": [
                {"label": "el problema", "texto": "Se cuelan registros idénticos."},
                {"label": "el código", "codigo": "SELECT 1;", "lenguaje": "sql"},
                {"label": "por qué funciona", "texto": "GROUP BY junta las filas iguales."},
            ]}
```

Y agregar estos tests al final del archivo:

```python
def test_construir_placas_tip_usa_dos_placas_de_contenido():
    """El tip tiene una sola idea con tres secciones: repartidas en dos placas,
    el carrusel pasa de tres slides a cuatro."""
    red = {"titulo_portada": "DETECTÁ\nDUPLICADOS", "ideas": [IDEA_TIP]}

    placas = main.construir_placas("tip", red)

    assert [p["plantilla"] for p in placas] == ["portada", "contenido", "contenido", "cierre"]
    assert [p["slide_index"] for p in placas] == [1, 2, 3, 4]
    assert {p["slide_total"] for p in placas} == {4}


def test_construir_placas_tip_reparte_las_secciones_en_orden():
    red = {"titulo_portada": "X", "ideas": [IDEA_TIP]}

    placas = main.construir_placas("tip", red)

    assert [s["label"] for s in placas[1]["secciones"]] == ["el problema", "el código"]
    assert [s["label"] for s in placas[2]["secciones"]] == ["por qué funciona"]
    # la sección de código viaja entera, con su snippet y su lenguaje
    assert placas[1]["secciones"][1] == {
        "label": "el código", "codigo": "SELECT 1;", "lenguaje": "sql"}


def test_construir_placas_continuacion_va_sin_titulo_ni_deck():
    """La segunda placa de una idea es continuación de la primera: repetir ahí
    el título gigante y el deck le roba el lugar al texto y se lee redundante.
    El kicker sí se repite: identifica la unidad de contenido, no la placa."""
    red = {"titulo_portada": "X", "ideas": [IDEA_TIP]}

    placas = main.construir_placas("tip", red)

    assert placas[1]["titulo"] == "DETECTÁ DUPLICADOS"
    assert placas[1]["deck"] == "Encontrá qué filas se repiten."
    assert placas[2]["titulo"] == ""
    assert placas[2]["deck"] == ""
    assert placas[2]["kicker"] == placas[1]["kicker"] == "tip 01"


def test_construir_placas_no_cambia_para_los_tipos_de_una_placa():
    """Regresión: comparativa y rol tienen un solo grupo, así que siguen
    emitiendo una placa por idea, con título y deck en todas."""
    red = {"titulo_portada": "X", "ideas": [IDEA, IDEA]}

    placas = main.construir_placas("comparativa", red)

    assert [p["plantilla"] for p in placas] == ["portada", "contenido", "contenido", "cierre"]
    assert all(p["titulo"] == "Excel" for p in placas[1:3])
    assert all(p["deck"] == "Limpiar filas" for p in placas[1:3])
    assert all(p["secciones"] == IDEA["secciones"] for p in placas[1:3])
```

- [ ] **Step 3: Correr los tests para verificar que fallan**

Run: `python -m pytest tests/test_main.py -k construir_placas -v`
Expected: FAIL. `test_construir_placas_tip_usa_dos_placas_de_contenido` falla con `AssertionError` porque hoy devuelve `['portada', 'contenido', 'cierre']`.

- [ ] **Step 4: Implementar**

En `src/main.py`, reemplazar el bucle de ideas de `construir_placas` (líneas 123-133) por:

```python
    for i, idea in enumerate(red["ideas"], start=1):
        por_label = {s["label"]: s for s in idea["secciones"]}
        # cada 3ª idea sale en placa clara: es el ritmo que evita que el
        # carrusel se lea como un bloque oscuro uniforme. Se cuenta por idea,
        # no por placa: las placas de una misma idea comparten variante.
        variante = "light" if i % 3 == 0 else "dark"
        for j, grupo in enumerate(contenido.grupos_de_placa(tipo)):
            placas.append({
                "plantilla": "contenido",
                "kicker": f"{palabra} {i:02d}",
                # título y deck van solo en la primera placa de la idea: las de
                # continuación arrancan directo con el panel (ver plantillas/
                # contenido.html, que omite el <h2> cuando el título viene vacío)
                "titulo": idea["titulo"] if j == 0 else "",
                "deck": idea.get("deck", "") if j == 0 else "",
                # los labels que no estén en la idea se descartan en vez de
                # reventar: una respuesta rara no tiene que voltear la pieza
                # entera. El invariante de grupos_de_placa (ver test_contenido)
                # es lo que garantiza que acá no se pierda nada por un typo.
                "secciones": [por_label[label] for label in grupo if label in por_label],
                "variant": variante,
            })
```

- [ ] **Step 5: Correr los tests para verificar que pasan**

Run: `python -m pytest tests/test_main.py -v`
Expected: PASS, incluyendo `test_tercera_idea_sale_en_placa_clara` y `test_construir_placas_pasa_secciones_y_kicker`, que no deben haber cambiado.

- [ ] **Step 6: Commit**

```bash
git add src/main.py tests/test_main.py
git commit -m "feat: emitir una placa de contenido por cada grupo de secciones"
```

---

### Task 3: La plantilla omite el título cuando viene vacío

**Files:**
- Modify: `plantillas/contenido.html:8`
- Test: `tests/test_render.py`

**Interfaces:**
- Consumes: el contexto de placa que produce `construir_placas` (Task 2), donde `titulo` puede ser `""`.
- Produces: nada que consuman otras tareas.

No hace falta tocar `plantillas/_estilos.html`: el bloque de contenido ya se centra entre header y pie vía `.kicker { margin-top:auto }` + `.plate-footer { margin-top:auto }`, y `.panel` abraza su contenido en vez de estirarse (ver el comentario en `_estilos.html:30-33`). Una placa con kicker + panel queda centrada y compacta sola.

- [ ] **Step 1: Escribir el test que falla**

Agregar a `tests/test_render.py`:

```python
def test_contenido_sin_titulo_no_emite_el_h2():
    """La placa de continuación de una idea va sin título: si la plantilla
    igual emite el <h2>, queda un hueco con el margin-top:16px del .title
    empujando el panel para abajo sin que se vea texto alguno."""
    html = _render("contenido", titulo="", deck="")

    assert "<h2" not in html
    assert 'class="panel"' in html
    assert 'class="kicker"' in html


def test_contenido_con_titulo_sigue_emitiendo_el_h2():
    html = _render("contenido")

    assert 'class="title title-medium"' in html
    assert "TOP N EN SQL" in html
```

- [ ] **Step 2: Correr los tests para verificar que fallan**

Run: `python -m pytest tests/test_render.py -k sin_titulo -v`
Expected: FAIL con `assert "<h2" not in html` — la plantilla emite el `<h2>` vacío.

- [ ] **Step 3: Implementar**

En `plantillas/contenido.html`, reemplazar la línea 8:

```html
  <h2 class="title title-medium">{{ titulo }}</h2>
```

por:

```html
  {% if titulo %}<h2 class="title title-medium">{{ titulo }}</h2>{% endif %}
```

- [ ] **Step 4: Correr los tests para verificar que pasan**

Run: `python -m pytest tests/test_render.py -v`
Expected: PASS. Requiere Chromium instalado (`python -m playwright install chromium`) para los tests que rendean PNG.

- [ ] **Step 5: Commit**

```bash
git add plantillas/contenido.html tests/test_render.py
git commit -m "feat: omitir el titulo en las placas de continuacion"
```

---

### Task 4: Tope de caracteres por sección

**Files:**
- Modify: `src/contenido.py` (después de `grupos_de_placa`, agregado en la Task 1)
- Modify: `src/redaccion/contratos.py:6` y `src/redaccion/contratos.py:67-77`
- Test: `tests/test_contenido.py`, `tests/test_contratos.py`

**Interfaces:**
- Consumes: `grupos_de_placa(tipo)` de la Task 1.
- Produces: `MAX_CHARS_SECCION_SOLA: int` y `max_chars_seccion(tipo: str, label: str) -> int` en `src/contenido.py`. La Task 6 recalibra el valor de la constante.

`MAX_CHARS_SECCION_SOLA` arranca en 520 y se confirma o corrige en la Task 6 midiendo sobre un PNG. No es el número final.

`contratos.py` sigue importando `MAX_CHARS_SECCION_TEXTO` además de la función nueva: `tests/test_contratos.py:112` lo referencia como `contratos.MAX_CHARS_SECCION_TEXTO` y ese test tiene que seguir pasando.

- [ ] **Step 1: Escribir los tests que fallan**

Agregar a `tests/test_contenido.py`:

```python
def test_max_chars_seccion_da_mas_lugar_a_la_que_va_sola():
    """"por qué funciona" ocupa su placa sola, así que tiene el alto entero
    para ella; "el problema" comparte placa con el snippet de código."""
    assert contenido.max_chars_seccion("tip", "por qué funciona") == contenido.MAX_CHARS_SECCION_SOLA
    assert contenido.max_chars_seccion("tip", "el problema") == contenido.MAX_CHARS_SECCION_TEXTO
    assert contenido.max_chars_seccion("tip", "el código") == contenido.MAX_CHARS_SECCION_TEXTO


def test_max_chars_seccion_de_los_tipos_de_dos_secciones():
    for tipo in ("novedad", "comparativa", "rol"):
        for label in contenido.SECCIONES_POR_TIPO[tipo]:
            assert contenido.max_chars_seccion(tipo, label) == contenido.MAX_CHARS_SECCION_TEXTO


def test_max_chars_seccion_label_desconocido_usa_el_tope_chico():
    """Un label que no está en ningún grupo cae al tope conservador en vez de
    romper: validar() ya rechaza los labels inventados por su cuenta."""
    assert contenido.max_chars_seccion("tip", "inventado") == contenido.MAX_CHARS_SECCION_TEXTO
```

Agregar a `tests/test_contratos.py`:

```python
def test_validar_acepta_por_que_funciona_largo_porque_va_solo_en_su_placa():
    """En el tip, "por qué funciona" ocupa una placa entera (ver
    contenido.grupos_de_placa), así que el tope de 260 —pensado para dos
    secciones por placa— no aplica: ahí entra bastante más texto."""
    from src.contenido import MAX_CHARS_SECCION_TEXTO
    idea = {"titulo": "t", "deck": "d", "secciones": [
        {"label": "el problema", "texto": "corto"},
        {"label": "por qué funciona", "texto": "x" * (MAX_CHARS_SECCION_TEXTO + 100)},
    ]}

    validar("tip", {**BASE, "ideas": [idea], "codigo": "SELECT 1;"})  # no levanta


def test_validar_rechaza_por_que_funciona_arriba_del_tope_de_seccion_sola():
    from src.contenido import MAX_CHARS_SECCION_SOLA
    idea = {"titulo": "t", "deck": "d", "secciones": [
        {"label": "el problema", "texto": "corto"},
        {"label": "por qué funciona", "texto": "x" * (MAX_CHARS_SECCION_SOLA + 1)},
    ]}

    with pytest.raises(ValueError, match="texto"):
        validar("tip", {**BASE, "ideas": [idea], "codigo": "SELECT 1;"})


def test_validar_rechaza_el_problema_largo_porque_comparte_placa_con_el_codigo():
    idea = {"titulo": "t", "deck": "d", "secciones": [
        {"label": "el problema", "texto": "x" * (contratos.MAX_CHARS_SECCION_TEXTO + 1)},
        {"label": "por qué funciona", "texto": "corto"},
    ]}

    with pytest.raises(ValueError, match="texto"):
        validar("tip", {**BASE, "ideas": [idea], "codigo": "SELECT 1;"})
```

- [ ] **Step 2: Correr los tests para verificar que fallan**

Run: `python -m pytest tests/test_contenido.py tests/test_contratos.py -k "max_chars or por_que_funciona or comparte_placa" -v`
Expected: FAIL con `AttributeError: module 'src.contenido' has no attribute 'max_chars_seccion'` y, en el test de contratos, con el `ValueError` de texto largo que hoy sí se levanta.

- [ ] **Step 3: Implementar en `src/contenido.py`**

Agregar después de `grupos_de_placa`:

```python
MAX_CHARS_SECCION_SOLA = 520
"""Tope de caracteres para una sección que ocupa su placa sola.

Cuando un grupo de grupos_de_placa tiene un solo label, esa sección no comparte
el panel con nadie: tiene el alto entero de la placa para ella, así que el tope
de MAX_CHARS_SECCION_TEXTO —calculado para dos secciones por panel— la deja
mucho más corta de lo que entra. El valor está medido sobre el PNG renderizado
del peor caso; ver docs/superpowers/plans/2026-07-28-tip-en-dos-placas.md."""


def max_chars_seccion(tipo: str, label: str) -> int:
    """El tope de caracteres del texto de <label> en <tipo>, según comparta
    placa o no.

    Un label que no pertenece a ningún grupo cae al tope conservador: validar()
    ya rechaza los labels inventados por su cuenta, y no es tarea de esta
    función decidir eso."""
    for grupo in grupos_de_placa(tipo):
        if label in grupo:
            return MAX_CHARS_SECCION_SOLA if len(grupo) == 1 else MAX_CHARS_SECCION_TEXTO
    return MAX_CHARS_SECCION_TEXTO
```

- [ ] **Step 4: Implementar en `src/redaccion/contratos.py`**

Cambiar el import de la línea 6:

```python
from src.contenido import (MAX_CHARS_SECCION_TEXTO, max_chars_seccion,
                           secciones_que_redacta_gemini)
```

Y reemplazar el chequeo de largo dentro del bucle de secciones (líneas 73-77):

```python
            tope = max_chars_seccion(tipo, seccion.get("label"))
            if len(texto) > tope:
                raise ValueError(
                    f"{tipo}: idea {i} tiene 'texto' de sección '{seccion.get('label')}' "
                    f"muy largo ({len(texto)} > {tope} chars, se corta en la placa)")
```

- [ ] **Step 5: Correr los tests para verificar que pasan**

Run: `python -m pytest tests/test_contenido.py tests/test_contratos.py -v`
Expected: PASS, incluyendo `test_validar_rechaza_texto_de_seccion_muy_largo`, que usa comparativa y sigue topeando en 260.

- [ ] **Step 6: Commit**

```bash
git add src/contenido.py src/redaccion/contratos.py tests/test_contenido.py tests/test_contratos.py
git commit -m "feat: topear el largo de seccion segun comparta placa o no"
```

---

### Task 5: El prompt pide un "por qué funciona" más largo

**Files:**
- Modify: `src/redaccion/prompts.py:141-174` (función `prompt_tip`)
- Test: `tests/test_prompts.py`

**Interfaces:**
- Consumes: nada de las tareas anteriores.
- Produces: nada que consuman otras tareas.

`REGLAS_IDEAS` no se toca: sigue pidiendo 1-2 oraciones para todos los tipos. La instrucción específica del tip la sobrescribe solo para ese label.

- [ ] **Step 1: Escribir el test que falla**

Agregar a `tests/test_prompts.py`:

```python
def test_prompt_tip_pide_por_que_funciona_mas_largo():
    """"por qué funciona" ocupa su placa sola (ver contenido.grupos_de_placa),
    así que el prompt tiene que pedir un texto que llene ese lugar en vez de
    las 1-2 oraciones genéricas de REGLAS_IDEAS."""
    item = {"titulo": "X", "lenguaje": "sql", "gancho": "g",
            "codigo": "SELECT 1;", "explicacion": "e"}

    p = prompts.prompt_tip(item)

    assert "3-4 oraciones" in p
    assert "350-500" in p


def test_prompt_tip_sigue_pidiendo_el_problema_corto():
    item = {"titulo": "X", "lenguaje": "sql", "gancho": "g",
            "codigo": "SELECT 1;", "explicacion": "e"}

    p = prompts.prompt_tip(item)

    assert "1-2 oraciones" in p
```

- [ ] **Step 2: Correr los tests para verificar que fallan**

Run: `python -m pytest tests/test_prompts.py -k prompt_tip -v`
Expected: FAIL con `assert "3-4 oraciones" in p`.

- [ ] **Step 3: Implementar**

En `src/redaccion/prompts.py`, dentro de `prompt_tip`, insertar un párrafo entre `{REGLAS_IDEAS}` y `{REGLAS_CAPTION}`:

```python
{REGLAS_IDEAS}

En este tipo, "por qué funciona" va SOLA en su propia placa del carrusel: ahí
tenés lugar de sobra, así que escribí 3-4 oraciones (~350-500 caracteres) que
expliquen la mecánica paso a paso y para qué le sirve a quien lee. "el problema"
comparte placa con el código, así que ahí sí van 1-2 oraciones.

{REGLAS_CAPTION}
```

Y en el bloque JSON del final, cambiar la línea de esa sección:

```python
      {{"label": "por qué funciona", "texto": "<3-4 oraciones, ~350-500 caracteres>"}}
```

- [ ] **Step 4: Correr los tests para verificar que pasan**

Run: `python -m pytest tests/test_prompts.py -v`
Expected: PASS, incluyendo `test_prompts_piden_secciones_con_los_labels_fijos`.

- [ ] **Step 5: Commit**

```bash
git add src/redaccion/prompts.py tests/test_prompts.py
git commit -m "feat: pedirle a Gemini un por-que-funciona mas largo en el tip"
```

---

### Task 6: Calibrar el tope midiendo el PNG del peor caso

**Files:**
- Create: `calibrar_placa_sola.py` en el directorio scratchpad de la sesión (script descartable, NO va al repo)
- Modify: `src/contenido.py` (solo el valor de `MAX_CHARS_SECCION_SOLA`, si la medición lo pide)

**Interfaces:**
- Consumes: `MAX_CHARS_SECCION_SOLA` y `max_chars_seccion` de la Task 4; la plantilla de la Task 3.
- Produces: el valor definitivo de `MAX_CHARS_SECCION_SOLA`.

Esta tarea es la que convierte el 520 provisorio en un número medido. El `overflow:hidden` de `.plate` corta el texto sin avisar y empuja el footer fuera de la placa, así que la única verificación válida es mirar el PNG.

- [ ] **Step 1: Escribir el script de calibración en el scratchpad**

```python
"""Rendea la placa de continuación del tip con un "por qué funciona" del largo
máximo permitido, para ver si entra. Descartable: no va al repo."""
from pathlib import Path

from src.config import get_config
from src.contenido import MAX_CHARS_SECCION_SOLA
from src.render.renderer import Renderer

# Texto realista (no "xxxx"): las palabras reales envuelven distinto que una
# tira sin espacios, y lo que importa es cuántas LÍNEAS ocupa, no los chars.
BASE = ("Al usar GROUP BY —que junta en un mismo paquete las filas idénticas— "
        "junto con HAVING COUNT —que cuenta cuántas veces aparece cada paquete— "
        "aislás solamente los grupos que se repiten más de una vez. De esta "
        "forma analizás el problema sin alterar la tabla original ni borrar "
        "nada todavía. Y si después decidís limpiar los duplicados, ya sabés "
        "exactamente qué filas vas a perder antes de tocarlas. ")

texto = (BASE * 5)[:MAX_CHARS_SECCION_SOLA]
print(f"largo del texto de prueba: {len(texto)}")

destino = Path(__file__).parent / "placa-sola-peor-caso.png"
with Renderer(get_config()) as r:
    r.render_placa({
        "plantilla": "contenido",
        "kicker": "tip 01",
        "titulo": "",
        "deck": "",
        "secciones": [{"label": "por qué funciona", "texto": texto}],
        "variant": "dark",
        "slide_index": 3,
        "slide_total": 4,
    }, destino)
print(f"listo: {destino}")
```

- [ ] **Step 2: Correr el script y mirar el PNG**

El script importa `src.*`, así que necesita la raíz del repo en el `PYTHONPATH`: al correr un archivo que vive en otro directorio, Python pone ahí el `sys.path[0]` y `import src` falla.

Run, parado en la raíz del repo (Bash): `PYTHONPATH=. python "<ruta-scratchpad>/calibrar_placa_sola.py"`
En PowerShell: `$env:PYTHONPATH="."; python "<ruta-scratchpad>\calibrar_placa_sola.py"`

Después **abrir el PNG y mirarlo**. Tres cosas concretas a verificar:
1. La última oración del texto se ve entera (no cortada a mitad de palabra ni de renglón).
2. El pie de la placa (`DESLIZA →`, los puntitos, `GUARDAR ■`) está visible dentro de la imagen.
3. Queda algo de margen entre el borde inferior del panel y el pie.

- [ ] **Step 3: Ajustar la constante si hace falta**

- Si el texto desborda o el pie se fue de la placa: bajar `MAX_CHARS_SECCION_SOLA` en `src/contenido.py` de a 40 y repetir el Step 2 hasta que entre con margen.
- Si sobra mucho aire (más de ~150px entre el panel y el pie): subir de a 40 y repetir.
- Si entra bien de una: dejar 520.

- [ ] **Step 4: Verificar el carrusel completo con datos reales**

Run: `python -m src.main --dry-run`

Abrir las cuatro placas de `salida/lote-<hoy>/04-tip/` (`01.png` a `04.png`) y verificar contra los criterios de aceptación del spec:
1. La placa 02 muestra `el problema` + `el código` y se ve menos cargada que la del 2026-07-28.
2. La placa 03 muestra solo `por qué funciona`, sin título ni deck, y no se lee huérfana.
3. Los contadores dicen `02 / 04` y `03 / 04`, con cuatro puntitos de progreso.

Nota: el `DRY_RUN` de `main.py:204-216` trae un `por qué funciona` corto (~120 caracteres), así que la placa 03 va a verse más vacía que en producción. Eso es esperable y no es motivo para cambiar la constante; la medición que manda es la del Step 2.

- [ ] **Step 5: Correr la suite completa**

Run: `python -m pytest`
Expected: PASS, sin tests salteados ni fallados.

- [ ] **Step 6: Commit**

Si la constante cambió:

```bash
git add src/contenido.py
git commit -m "fix: calibrar el tope de seccion sola contra el PNG renderizado"
```

Si no cambió, no hay nada que commitear: el script de calibración vive en el scratchpad y no entra al repo.

---

## Verificación final

- [ ] `python -m pytest` pasa entero.
- [ ] `git log --oneline main..HEAD` muestra el spec y un commit por tarea.
- [ ] Las cuatro placas del tip del `--dry-run` se miraron con los ojos, no solo por tests.
- [ ] `git diff main -- src/main.py` no introduce ningún `if tipo == "tip"`.
