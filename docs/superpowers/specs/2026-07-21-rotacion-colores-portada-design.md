# Diseño — Rotación fija de colores en portadas

## Objetivo

Evitar que todos los carruseles comiencen con la misma portada verde neón. Cada lote diario usará una portada de color distinto, siguiendo una secuencia fija, predecible y reproducible.

## Alcance

- Agregar cuatro variantes de portada: verde, violeta, azul y coral.
- Seleccionar la variante a partir de la fecha del lote, usando un ciclo determinista.
- Mantener sin cambios las placas de contenido y de cierre.

## Diseño

`src/config.py` definirá la paleta y el orden del ciclo. `src/main.py` derivará la variante de portada desde la fecha ya usada para nombrar el lote: la misma fecha siempre devuelve el mismo color y la fecha siguiente avanza una posición.

La portada recibirá una variante explícita, por ejemplo `cover-blue`. Las reglas de `plantillas/_estilos.html` asignarán a cada variante su fondo y color de texto, preservando contraste legible y el resto de la composición de la portada.

No se agregará estado persistente: el cálculo por fecha evita que reintentos del mismo día cambien el color y elimina una dependencia adicional de `estado/`.

## Pruebas

- La elección para una fecha es estable.
- Fechas consecutivas avanzan en el ciclo y este vuelve al inicio después de cuatro días.
- `construir_placas()` entrega la variante seleccionada a la portada, mientras las demás placas conservan sus variantes actuales.
- El render de cada variante conserva la clase CSS esperada.

## Criterios de aceptación

1. Los carruseles de días consecutivos no usan siempre el mismo color de portada.
2. La sucesión sigue el orden verde → violeta → azul → coral → verde.
3. Regenerar un lote de la misma fecha conserva su color.
4. La suite de pruebas existente y las nuevas pruebas pasan.
