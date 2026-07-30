# Diseño — El tip repartido en dos placas

## Problema

El tip es el único tipo con una sola idea, así que su carrusel queda en tres slides (portada + una placa de contenido + cierre) y esa única placa de contenido carga las tres secciones del tipo: `el problema`, `el código` y `por qué funciona`. En la edición del 2026-07-28 la placa se ve visiblemente saturada: texto, snippet y explicación apilados sin aire.

Los demás tipos no tienen este problema porque reparten una placa por unidad —una opción en comparativa, una skill en rol, un cambio en novedad— y cada placa termina con dos secciones.

## Objetivo

Repartir las secciones del tip en dos placas de contenido, llevando el carrusel de tres a cuatro slides, sin agregar secciones nuevas al tipo.

## Alcance

- El tip pasa a rendear dos placas de contenido: `el problema` + `el código` en la primera, `por qué funciona` sola en la segunda.
- La segunda placa va sin título y sin deck: solo el kicker y el panel.
- La sección que queda sola en su placa admite un texto más largo que las que comparten placa.
- Novedad, comparativa y rol no cambian.
- El reel, la exportación a `ParaSubir/` y la página web no se tocan: descubren las placas por glob de `[0-9][0-9].png` y absorben el conteo nuevo solos.

## Diseño

### El reparto vive en datos

`src/contenido.py` ya es la única fuente de los labels de sección por tipo. Suma ahí una constante que describe cómo se agrupan esas secciones en placas, y una función que la lee con un default:

```python
PLACAS_POR_TIPO: dict[str, list[list[str]]] = {
    "tip": [["el problema", "el código"], ["por qué funciona"]],
}

def grupos_de_placa(tipo: str) -> list[list[str]]:
    """Cómo se reparten las secciones de UNA idea entre placas.
    Por defecto: una sola placa con todas las secciones del tipo."""
    return PLACAS_POR_TIPO.get(tipo, [SECCIONES_POR_TIPO[tipo]])
```

El default es lo que mantiene intactos a los otros tres tipos: un grupo con todos sus labels, es decir una placa por idea, exactamente como hoy.

Ningún módulo fuera de `contenido.py` nombra el string `"tip"` para decidir el reparto. `main.construir_placas` y `contratos.validar` consultan `grupos_de_placa`.

### Las placas se arman por idea × grupo

`main.construir_placas` deja de emitir una placa por idea y pasa a emitir una placa por cada grupo de cada idea. Para cada idea, las secciones se indexan por label y cada grupo toma las suyas en el orden que fija el grupo.

La primera placa de una idea lleva `titulo` y `deck` como hoy. Las placas siguientes de la misma idea los llevan vacíos. El `kicker` es el mismo en todas las placas de una idea (`tip 01`), porque identifica la unidad de contenido, no la placa.

La alternancia de variante clara/oscura sigue calculándose sobre el índice de idea, sin cambios. Para el reparto del tip esto no produce ninguna diferencia visible: ambas placas del tip caen en `dark` con la regla actual y también caerían en `dark` si se contaran placas, así que no hay motivo para tocarla.

El conteo de slides (`slide_index` / `slide_total`) y los puntitos de progreso ya se derivan del largo final de la lista de placas, así que reflejan las cuatro slides sin cambios.

### La plantilla omite el título cuando viene vacío

`plantillas/contenido.html` envuelve el `<h2 class="title title-medium">` en un condicional, igual que ya hace con el deck.

No hace falta tocar `plantillas/_estilos.html`. El bloque de contenido se centra entre el header y el pie mediante `.kicker { margin-top:auto }` combinado con `.plate-footer { margin-top:auto }`, y el panel abraza su contenido en vez de estirarse. Una placa con kicker + panel queda entonces centrada y compacta, sin caja vacía.

### El tope de caracteres pasa a ser por sección

Hoy `MAX_CHARS_SECCION_TEXTO = 260` aplica igual a toda sección. El límite existe porque `.plate` tiene `overflow:hidden` y lo que se pasa se corta.

Una sección que ocupa su placa sola dispone de mucho más alto, así que `src/contenido.py` suma un segundo tope, `MAX_CHARS_SECCION_SOLA`. El valor de arranque es 520 y se confirma o corrige midiendo sobre el PNG renderizado con el peor caso real; el número no se fija a ojo.

`contratos.validar` elige el tope por sección: si el label queda solo en su grupo según `grupos_de_placa`, usa `MAX_CHARS_SECCION_SOLA`; si comparte grupo, usa `MAX_CHARS_SECCION_TEXTO`. Las secciones de novedad, comparativa y rol siguen validando contra 260, porque sus grupos tienen dos labels.

### El prompt pide un texto más largo para esa sección

`prompts.prompt_tip` indica que `por qué funciona` va sola en su placa y pide 3-4 oraciones (~350-500 caracteres). `REGLAS_IDEAS` sigue igual —1-2 oraciones— para las demás secciones y los demás tipos: la instrucción específica del tip la sobrescribe solo para ese label.

## Decisión asumida: el plan B queda corto

El plan B —redacción local sin IA, cuando Gemini falla dos veces seguidas— arma `por qué funciona` con el campo `explicacion` de `datos/tips.json`, que hoy mide entre 83 y 156 caracteres. En una placa dedicada ese texto se va a ver corto.

Se deja así a propósito. El plan B es un salvavidas infrecuente y la placa sigue siendo legible; engordar los quince tips a mano es trabajo aparte, que se hará si el resultado molesta al verlo en producción. No es un pendiente que bloquee este cambio.

## Pruebas

- Los grupos de `grupos_de_placa("tip")`, concatenados, dan exactamente `SECCIONES_POR_TIPO["tip"]`: ninguna sección se pierde ni se duplica al repartir.
- `grupos_de_placa` devuelve un único grupo con todos los labels para novedad, comparativa y rol.
- `construir_placas("tip", ...)` devuelve cuatro placas: portada, dos de contenido y cierre.
- La primera placa de contenido del tip lleva `el problema` y `el código`; la segunda lleva solo `por qué funciona`.
- La segunda placa de contenido del tip viene con `titulo` y `deck` vacíos, y con el mismo `kicker` que la primera.
- `construir_placas` para comparativa y rol devuelve la misma cantidad de placas que antes del cambio.
- `slide_total` vale 4 en todas las placas del tip y `slide_index` numera 1 a 4.
- `contratos.validar` acepta un `por qué funciona` de más de 260 caracteres y por debajo de `MAX_CHARS_SECCION_SOLA`.
- `contratos.validar` rechaza un `el problema` de más de 260 caracteres, porque comparte placa.
- El render de una placa sin `titulo` no emite el `<h2>` y sí emite el panel.

## Verificación manual

Correr `python -m src.main --dry-run` y mirar los PNG del tip. Confirmar que la placa 02 respira, que la 03 no se lee huérfana y que ningún texto queda cortado por el `overflow:hidden`. Ajustar `MAX_CHARS_SECCION_SOLA` si el peor caso desborda.

## Criterios de aceptación

1. El carrusel de tip tiene cuatro slides y ninguna placa se ve saturada.
2. La placa 02 muestra el problema y el código; la placa 03 muestra solo por qué funciona, sin título ni deck.
3. Los carruseles de novedad, comparativa y rol salen idénticos a como salían antes.
4. Ningún texto se corta por desborde en las placas renderizadas.
5. La suite de pruebas existente y las nuevas pruebas pasan.
