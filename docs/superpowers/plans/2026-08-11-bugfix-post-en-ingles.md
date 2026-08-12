# Bugfix: el post se publicó en inglés — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Que Data Snake no pueda publicar en inglés, ni cuando Gemini falla.

**Architecture:** Dos cambios independientes. El primero evita que Gemini caiga a plan B por una razón evitable (no sabe el límite de caracteres que el validador le exige). El segundo es la red de seguridad: si una novedad cae a plan B igual, se publica un evergreen del banco —siempre en español— en vez del RSS crudo.

**Tech Stack:** Python 3, pytest.

## Global Constraints

- Todo el contenido publicado va en español rioplatense. `VOZ_DE_MARCA` (`src/redaccion/prompts.py`) es la fuente de esa regla.
- Los límites de caracteres nunca se escriben a mano dos veces: se derivan de `src/contenido.py`, que es donde viven medidos contra el PNG renderizado.
- Los tests corren con `python -m pytest` desde la raíz del repo (`pytest.ini` ya fija `testpaths = tests`).
- Rama de trabajo: `fix/post-en-ingles`, sacada de `main`. No commitear a `main` directo: el workflow publica desde ahí.

## Contexto: qué pasó exactamente

Corrida del 2026-08-11 (GitHub Actions run `31486595868`):

```
WARNING datasnake: Redacción de novedad falló (intento 1): novedad: idea 1 tiene
  'texto' de sección 'qué cambió' muy largo (331 > 260 chars, se corta en la placa)
WARNING datasnake: Redacción de novedad falló (intento 2): ... (295 > 260 chars ...)
WARNING datasnake: Gemini no disponible para novedad: plan B
```

1. `REGLAS_IDEAS` pide *"1-2 oraciones"* — nunca dice cuántos caracteres.
2. `contratos.validar` rechaza `texto` > `MAX_CHARS_SECCION_TEXTO` (260).
3. `redactar_pieza` agota sus 2 intentos → `plan_b`.
4. `plan_b("novedad")` arma el caption con `item['titulo']` y `item['resumen']` **crudos del RSS**, y los 4 feeds de `datos/feeds.json` son en inglés.

El plan B es la única ruta del sistema capaz de emitir inglés: todas las demás pasan por `VOZ_DE_MARCA`.

---

### Task 1: El prompt declara el tope real de caracteres

**Files:**
- Modify: `src/redaccion/prompts.py:27-33` (`REGLAS_IDEAS`) y los cuatro esqueletos JSON (`:62-63`, `:96-97`, `:132-133`, `:171`)
- Test: `tests/test_prompts.py`

**Interfaces:**
- Consumes: `src.contenido.MAX_CHARS_SECCION_TEXTO` (int, hoy 260)
- Produces: nada nuevo. `REGLAS_IDEAS` sigue siendo un str de módulo.

Importar `src.contenido` desde `src.redaccion.prompts` es seguro: `contenido.py` solo importa `html` y `re`, no hay ciclo.

- [ ] **Step 1: Write the failing test**

En `tests/test_prompts.py`, al final:

```python
def test_los_prompts_declaran_el_tope_de_caracteres_de_seccion():
    """El validador rechaza secciones de más de MAX_CHARS_SECCION_TEXTO, pero
    el prompt solo pedía "1-2 oraciones": Gemini escribía 295-331 chars de
    buena fe y la pieza caía a plan B (corrida 2026-08-11). El número sale de
    contenido.py para que no pueda desincronizarse del validador."""
    from src.contenido import MAX_CHARS_SECCION_TEXTO

    tope = str(MAX_CHARS_SECCION_TEXTO)
    generados = [
        prompts.prompt_novedad({"fuente": "f", "titulo": "t", "resumen": "r"}),
        prompts.prompt_comparativa({"tarea": "t", "veredicto": "v", "opciones": [
            {"nombre": "A", "cuando_conviene": "x.", "donde_duele": "y."}]}),
        prompts.prompt_rol({"rol": "r", "gancho": "g", "herramientas": ["SQL"],
                            "skills": [{"nombre": "s", "por_que": "p", "como_practicar": "c"}]}),
        prompts.prompt_tip({"titulo": "x", "lenguaje": "sql", "gancho": "g",
                            "codigo": "SELECT 1;", "explicacion": "e"}),
    ]

    for p in generados:
        assert tope in p
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_prompts.py::test_los_prompts_declaran_el_tope_de_caracteres_de_seccion -v`
Expected: FAIL — `assert '260' in p`. Ningún prompt menciona 260 hoy.

- [ ] **Step 3: Write minimal implementation**

En `src/redaccion/prompts.py`, agregar el import arriba del todo (después del docstring):

```python
from src.contenido import MAX_CHARS_SECCION_TEXTO
```

Reemplazar `REGLAS_IDEAS` por una f-string:

```python
REGLAS_IDEAS = f"""\
Cada "idea" es UNA placa del carrusel y va con: "titulo" (1-3 palabras, entra
gigante), "deck" (una oración que resume la idea) y "secciones". Las secciones
tienen LABELS FIJOS que no podés cambiar ni inventar: usá exactamente los que te
pido, todos, en ese orden. Cada "texto" de sección: 1-2 oraciones y COMO MÁXIMO
{MAX_CHARS_SECCION_TEXTO} caracteres, contando espacios. El tope es físico: la
placa recorta lo que se pasa, así que una sección más larga hace descartar la
pieza entera. Concretas, en lenguaje simple (traducí el término técnico la
primera vez), sin números inventados."""
```

En los cuatro esqueletos JSON, cambiar cada `"<1-2 oraciones>"` de un campo `"texto"` por:

```python
      {{"label": "qué cambió", "texto": "<1-2 oraciones, máx {MAX_CHARS_SECCION_TEXTO} caracteres>"}},
```

Los cuatro sitios: `prompt_novedad` (labels `qué cambió`, `por qué importa`), `prompt_comparativa` (`cuándo conviene`, `dónde duele`), `prompt_rol` (`por qué te la piden`, `cómo la practicás`), `prompt_tip` (solo `el problema` — `por qué funciona` ya tiene su propio tope de 350-500 y no se toca).

**Ojo con las llaves:** las cuatro funciones ya son f-strings con `{{` / `}}` escapados. Al meter `{MAX_CHARS_SECCION_TEXTO}` adentro del esqueleto JSON, las llaves del JSON siguen dobles y la de la variable va simple.

- [ ] **Step 4: Run the full prompt suite**

Run: `python -m pytest tests/test_prompts.py -v`
Expected: PASS, las 8 pruebas.

`test_prompt_tip_sigue_pidiendo_el_problema_corto` afirma `"1-2 oraciones" in p` — la redacción nueva conserva esa frase textual a propósito. Si falla, es que la borraste.

- [ ] **Step 5: Verify no other suite broke**

Run: `python -m pytest -q`
Expected: PASS. `REGLAS_IDEAS` es un string embebido en prompts; ningún otro módulo lo parsea.

- [ ] **Step 6: Commit**

```bash
git add src/redaccion/prompts.py tests/test_prompts.py
git commit -m "fix: el prompt declara el tope de caracteres que exige el validador"
```

---

### Task 2: Una novedad en plan B se reemplaza por un evergreen

**Files:**
- Modify: `src/main.py` — nueva función `redactar_lote`, usada desde `main()` (`:250-253`) y consultada en el registro de estado (`:268-270`)
- Test: `tests/test_main.py`

**Interfaces:**
- Consumes: `main.redactar_pieza(tipo, item, cfg) -> dict` (existente), `main.seleccionar(cfg, banco, cantidad, seed) -> list[dict]` (existente, importada de `src.fuentes.bancos`), `main.TIPOS` (existente)
- Produces: `main.redactar_lote(cfg, piezas, seed) -> tuple[list[dict], bool]`. Devuelve las redacciones en el mismo orden que `piezas`, y un bool `novedad_descartada`. **Muta `piezas` in-place** cuando sustituye: el llamador tiene que leer `piezas` después, no antes.

- [ ] **Step 1: Write the failing test**

En `tests/test_main.py`, al final:

```python
def test_novedad_en_plan_b_se_reemplaza_por_un_evergreen(monkeypatch, tmp_path):
    """El plan B de novedad copia título y resumen del RSS tal cual, y los
    feeds son en inglés: es la única ruta capaz de publicar en un idioma que
    no es el de la marca (corrida 2026-08-11). Ante la duda va un evergreen,
    que siempre está escrito en español en los bancos."""
    cfg = get_config()
    cfg.dir_estado = tmp_path

    def gemini_siempre_falla(prompt, key):
        raise main.GeminiError("sin cuota")

    monkeypatch.setattr(main, "generar_json", gemini_siempre_falla)
    monkeypatch.setattr(main.time, "sleep", lambda _s: None)

    piezas = [{"tipo": "novedad", "item": {
        "id": "http://x/1", "fuente": "Power BI",
        "titulo": "Announcing new Copilot features",
        "resumen": "Today we are announcing a set of improvements.",
    }}]

    redacciones, novedad_descartada = main.redactar_lote(cfg, piezas, seed=202627)

    assert novedad_descartada is True
    assert piezas[0]["tipo"] in cfg.tipos_evergreen
    assert len(redacciones) == 1
    assert "Announcing new Copilot features" not in redacciones[0]["caption"]
    assert "Today we are announcing" not in redacciones[0]["caption"]


def test_evergreen_en_plan_b_no_se_reemplaza(monkeypatch, tmp_path):
    """El plan B de los evergreen sale de los bancos, que están en español:
    ese camino no tiene nada de malo y se conserva tal cual."""
    cfg = get_config()
    cfg.dir_estado = tmp_path

    def gemini_siempre_falla(prompt, key):
        raise main.GeminiError("sin cuota")

    monkeypatch.setattr(main, "generar_json", gemini_siempre_falla)
    monkeypatch.setattr(main.time, "sleep", lambda _s: None)

    item = {"id": "t01", "titulo": "Rankear sin subconsultas", "lenguaje": "sql",
            "gancho": "Top N por grupo", "codigo": "SELECT 1;",
            "explicacion": "ROW_NUMBER numera dentro de cada grupo."}
    piezas = [{"tipo": "tip", "item": item}]

    redacciones, novedad_descartada = main.redactar_lote(cfg, piezas, seed=202627)

    assert novedad_descartada is False
    assert piezas[0]["tipo"] == "tip"
    assert redacciones[0]["plan_b"] is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_main.py -k redactar_lote -v`
Expected: FAIL con `AttributeError: module 'src.main' has no attribute 'redactar_lote'`.

Si en cambio falla con `AttributeError: ... has no attribute 'GeminiError'`, agregá `GeminiError` al import de `src.redaccion.gemini` en `main.py` — hoy ya está importado (`:22`), así que no debería pasar.

- [ ] **Step 3: Write minimal implementation**

En `src/main.py`, agregar después de `redactar_pieza` (`:104`):

```python
def redactar_lote(cfg: Config, piezas: list[dict], seed: int) -> tuple[list[dict], bool]:
    """Redacta cada pieza del lote. Devuelve (redacciones, novedad_descartada).

    Si la novedad cae a plan B, se reemplaza por un evergreen: plan_b("novedad")
    arma el caption con el título y el resumen del RSS tal cual, y los feeds son
    en inglés, así que ese camino publica en un idioma que no es el de la marca
    (pasó en la corrida 2026-08-11). Los bancos evergreen están escritos en
    español, así que ante la duda va eso.

    Muta `piezas` in-place cuando sustituye, para que registrar_usados y
    armar_pieza vean el item que realmente se publicó.
    """
    redacciones: list[dict] = []
    novedad_descartada = False
    for i, pieza in enumerate(piezas):
        red = redactar_pieza(pieza["tipo"], pieza["item"], cfg)
        if pieza["tipo"] == "novedad" and red.get("plan_b"):
            log.warning("Plan B de novedad: publicaría el RSS en inglés, va un evergreen")
            tipo_ev = cfg.tipos_evergreen[seed % len(cfg.tipos_evergreen)]
            banco, _ = TIPOS[tipo_ev]
            item = seleccionar(cfg, banco, 1, seed + 100 + i)[0]
            piezas[i] = {"tipo": tipo_ev, "item": item}
            # se reintenta con Gemini a propósito: el fallo puede haber sido del
            # material de la novedad (largo, formato) y no del modelo. Si vuelve
            # a fallar, el plan B del evergreen ya está en español.
            red = redactar_pieza(tipo_ev, item, cfg)
            novedad_descartada = True
        redacciones.append(red)
        time.sleep(cfg.pausa_entre_llamadas)
    return redacciones, novedad_descartada
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_main.py -k redactar_lote -v`
Expected: PASS, ambas.

- [ ] **Step 5: Conectar `redactar_lote` en `main()`**

Reemplazar el bucle de redacción (`src/main.py:250-253`):

```python
        seed = hoy.toordinal()
        novedad = feeds.elegir_novedad(cfg)
        piezas = plan_dia(cfg, seed, novedad)
        redacciones, novedad_descartada = redactar_lote(cfg, piezas, seed)
```

Y en el registro de estado (`:268-270`):

```python
    if not args.dry_run:
        # si la novedad se descartó, no se marca como vista: sigue disponible
        # para la corrida de mañana, cuando Gemini puede andar bien
        if novedad and not novedad_descartada:
            feeds.registrar_vista(cfg, novedad["id"])
```

En la rama `--dry-run`, inicializar `novedad_descartada = False` junto a `novedad = None` (`:245`), para que la variable exista en los dos caminos.

- [ ] **Step 6: Run the full suite**

Run: `python -m pytest -q`
Expected: PASS, todo.

- [ ] **Step 7: Verificar la corrida completa sin red**

Run: `python -m src.main --dry-run`
Expected: exit 0 y `salida/lote-<hoy>/` con las 4 piezas. Es el humo que confirma que `main()` sigue armando el lote con la firma nueva.

- [ ] **Step 8: Commit**

```bash
git add src/main.py tests/test_main.py
git commit -m "fix: la novedad que cae a plan B se reemplaza por un evergreen"
```

---

### Task 3: Verificación de punta a punta

**Files:** ninguno (solo verificación)

- [ ] **Step 1: Reproducir el escenario exacto del 2026-08-11**

El fallo original fue por largo, no por Gemini caído. Confirmar que con el prompt corregido el sistema no reproduce el bug, corriendo la suite completa más el dry-run:

Run: `python -m pytest -q && python -m src.main --dry-run`
Expected: PASS + exit 0.

- [ ] **Step 2: Abrir el PR**

```bash
git push -u origin fix/post-en-ingles
gh pr create --title "fix: el post no puede salir en ingles" --body "$(cat <<'EOF'
La corrida del 2026-08-11 publico en ingles. El log (run 31486595868) muestra
la cadena completa: el prompt pide "1-2 oraciones" sin decir cuantos caracteres,
el validador rechaza a los 260, Gemini escribio 331 y 295, se agotaron los dos
intentos y plan_b("novedad") copio el titulo y el resumen del RSS tal cual.

Dos cambios:

- El prompt declara el tope real, derivado de MAX_CHARS_SECCION_TEXTO para que
  no pueda desincronizarse del validador.
- Una novedad que igual cae a plan B se reemplaza por un evergreen del banco,
  que siempre esta en espanol. La novedad no se marca como vista, asi que
  sigue disponible para manana.

Va antes que la ampliacion de herramientas, que suma 4 feeds nuevos en ingles.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

- [ ] **Step 3: Confirmar en la próxima corrida real**

Después del merge, en la corrida siguiente verificar que no aparece el plan B:

```bash
gh run list --limit 1
gh run view <id> --log | grep -E "datasnake: (Redacción|Gemini|Plan B|Pieza)"
```

Expected: ninguna línea `Gemini no disponible` ni `Plan B de novedad`.
