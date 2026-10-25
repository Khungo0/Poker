# Continuación de investigación · iteración 0.4

Se revisaron los cambios preparados de 0.3, el commit previo, AGENTS.md, README, CODEX_PLAN, la especificación completa y los informes existentes. Las 89 pruebas anteriores se ejecutaron satisfactoriamente antes de continuar; ese avance se guardó en `6a503ad`. Esta entrega amplía la fase 2 sobre el motor existente.

## Funcionalidades añadidas

- **Poblaciones por rol persistente**: categoría Reg/Fish/Sin clasificar, subperfil y jugador concreto para A/B/C. Cambiar de calle o de actor no cambia la identidad ni la condición de cada rol. Un rol sin jugador vinculado se excluye si tiene restricciones; no se considera un jugador sin clasificar.
- **27 reportes preconfigurados**, además del constructor personalizado: 19 preflop, tres respuestas a barrels limped y cinco reportes adicionales de oportunidades de apostar/afrontar un raise en limped pots.
- Preflop HU: primera decisión de SB; BB frente a limp, minraise, raise y shove; SB limp frente a iso o shove; SB frente a 3bet, incluido shove.
- Preflop 3H: BTN first-in; SB tras BTN fold o frente a apertura; BB frente a BTN, SB, uno o dos limps; oportunidad de squeeze; BTN frente a 3bet de SB/BB con fold del tercero.
- Postflop limped HU: oportunidad de bet flop de BB o de SB tras check, oportunidad de segundo/tercer barrel del mismo apostador, respuesta del apostador al raise de flop. Se mantienen los tres reportes de respuesta a barrels ya validados.
- Constructor: tamaño de un paso previo en BB o porcentaje de bote; selección de rol, calle y posición de la siguiente decisión; exigencia de subida legal. HU no ofrece BTN ni un tercer rol.
- Guardar, recuperar y exportar incluye las restricciones por rol. Los documentos antiguos se cargan con los nuevos campos vacíos. Atrás restaura secuencia y filtros. Los resultados obtenidos con una selección que cambió durante la consulta se descartan; tampoco se permite abrir una rama con filtros diferentes de los consultados.
- El acceso desde el panel de estudio agrega una sola entrada al historial de navegación.

## Denominadores y contexto

Un reporte selecciona el prefijo **anterior** a la decisión objetivo. Fold/call/raise/shove comparten denominador cuando son resultados de esa decisión. No se filtra el tamaño de la respuesta futura para construir ese denominador.

Minraise significa open raise no all-in **hasta 2 BB totales**, con las ciegas ya incluidas. Los shoves a 2 BB se estudian como shove. Un all-in corto que solo completa parte de la ciega no es un open shove; conserva la clasificación de limp/completar.

El preset de squeeze requiere BTN raise no all-in, SB call y una decisión de BB en la que todavía sea legal subir. Excluye BB sin fichas suficientes para subir y la línea en que SB foldea. La mano sigue siendo 3H aunque un jugador foldee; no se cambia su formato a HU.

Oportunidad de segundo barrel: A apostó flop, B pagó y A puede apostar o pasar turn. Respuesta a segundo barrel: A **ya apostó turn** y B decide. Son denominadores diferentes. Lo mismo se aplica al tercer barrel. Se incluyen agresores en ambas posiciones HU, con el check previo del defensor cuando corresponde; un cambio de agresor rompe la línea.

Ejemplo de contexto persistente: A = Reg y B = Fish, A bet flop → B call. Al avanzar, A actúa turn pero B sigue siendo el Fish que pagó. Los filtros superiores de actor/rival y las columnas comparativas Reg/Fish corresponden al **actor de la decisión actual**, manteniendo también las restricciones por rol. Si se fija B = Fish en un nodo de B, la comparación Reg queda vacía por esa restricción; no se elimina silenciosamente el filtro.

Hero continúa excluido como actor por defecto. Las restricciones por rol no aplican automáticamente esa exclusión a otros participantes del prefijo. Las etiquetas son las actuales, incluso al consultar períodos antiguos. No se ha implementado clasificación histórica ni inferencia de cartas ocultas.

## Verificación contra originales

`python -m scripts.validate_preflop_presets --db RUTA --output INFORME.json` abre DuckDB en solo lectura. Su oráculo recorre las acciones originales y las aportaciones; no usa las observaciones derivadas para construir los resultados esperados.

Selección: **EUR 5.00**, formato indicado, Hero excluido como actor, sin clasificación inventada.

| Reporte | Oportunidades | Resultados comprobados |
|---|---:|---|
| HU SB primera decisión | 15.392 | 2.971 fold; 6.572 limp/completar; 2.357 raise; 3.492 shove |
| HU BB frente a minraise | 743 | 286 fold; 315 call; 23 raise; 119 shove |
| 3H BB oportunidad de squeeze | 765 | 228 fold; 416 call; 32 raise; 89 shove |

Para los tres reportes: **cero oportunidades omitidas, añadidas o con resultado distinto**. Al construir el oráculo se contrastó expresamente el all-in corto que solo completa la ciega; no se alteró el importador ni la clasificación existente para obtener la coincidencia.

El verificador independiente del spot prioritario se volvió a ejecutar:

```bash
python -m scripts.validate_sequences --db RUTA --output INFORME.json
```

Continúa coincidiendo en **196 oportunidades: 100 fold, 88 call y 8 raise**, sin discrepancias. La base de trabajo no tiene etiquetas de población; estas cifras **no son estadísticas de Fishes** ni demuestran una estrategia rentable.

Los 27 reportes se ejecutaron sobre la base real, comprobando que los casos suman su denominador. La comprobación independiente desde originales cubre los tres reportes preflop de la tabla y el tercer barrel prioritario; no se presenta como validación externa de todo el catálogo. Los casos sintéticos cubren cada preset restante y las restricciones de navegación/contexto.

Se conservaron **70.038 manos, 308.439 decisiones, 4.140 resúmenes y 14 errores**. Esta versión mantiene esquema 2 y análisis 2; no requiere rebuild ni reimportación. Los originales, la base y sus backups continúan fuera de Git.

## Pruebas e interfaz

`QT_QPA_PLATFORM=offscreen python -m pytest -q`: **124 pruebas pasan** (89 anteriores + 35 nuevas). Se prueban los 19 presets preflop, el denominador completo ante minraise, squeeze imposible, bet/check para barrels en ambas posiciones, flop bet, bet/fold frente a raise, tres roles distintos, rol opcional sin vincular, subperfiles, parámetros de jugador, carga de documentos antiguos y navegación Qt con filtros guardados.

Se renderizó la aplicación completa a **1920×1080 y 2560×1440** en Linux, incluido el constructor expandido con desplazamiento. Se revisó visualmente la vista 1920×1080. Las pruebas conservan también la comprobación 1440×900 del panel. Esto no verifica Windows, su escalado DPI ni un instalador 0.4.

## Fases y siguiente trabajo

| Fase | Completado en su alcance actual | Pendiente |
|---|---|---|
| 1 · Motor | Importador real, reconstrucción, secuencias, migración y regresiones | Replayer de la sala, headers de 14 manos ambiguas e investigación externa |
| 2 · Investigación | Barrels limped, roles poblacionales persistentes y 27 presets comprobados | Catálogo postflop SRP completo, donk/probe/delayed cbet por secuencia, tamaños/texturas en reportes avanzados |
| 3 · Interfaz | Vistas de secuencias, estudio/replayer y nuevos controles | Rediseño integral del Explorer y del resto de vistas |
| 4 · Rangos/comparación | Comparación básica Reg/Fish por nodo y ponderación por jugador | Matrices avanzadas, familias postflop, comparación arbitraria y constructor completo de estadísticas |
| 5 · Estrategias | Evidencia, estados, versiones y replayer | Leak Finder con incertidumbre agrupada/múltiples búsquedas; EV por árboles |
| 6 · Producto | Backups verificados, migración, consultas en worker y pruebas | Millones de manos, restauración activa guiada, build/instalación Windows y DPI reales |

Ninguna fase se declara íntegramente terminada mientras conserve esos pendientes. El siguiente bloque de desarrollo es ampliar las secuencias postflop SRP, manteniendo oportunidades y roles explícitos. La investigación web sigue sin verificarse desde este entorno: la iteración anterior recibió 403 y esta entrega no atribuye nuevos hallazgos a fuentes externas.
