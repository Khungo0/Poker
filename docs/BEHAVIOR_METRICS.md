# Métricas, reglas y poblaciones · 0.8

## Datos y denominadores

`src/behavior.py` define un catálogo de 31 métricas/opciones (25 frecuencias de oportunidad, VPIP, PFR, diferencia VPIP−PFR y tres contadores). Se consulta por HU/3H, stake, fechas, stack inicial efectivo, jugador y categoría del rival directo. Hero se excluye por defecto. No se usan cartas ocultas ni ganancias para deducir Reg/Fish.

Manos, torneos y días cuentan manos **con decisión preflop** del jugador. No cuentan walks como manos con decisión. Los torneos se identifican por session; los días por fecha normalizada. VPIP y PFR se calculan una vez por jugador/mano, usando todas sus acciones preflop. Los filtros de contexto se evalúan sobre su primera decisión preflop. VPIP−PFR es el indicador pareado «participó voluntariamente y no subió», sobre ese mismo denominador, no la resta de dos intervalos independientes.

Las métricas de decisiones filtran cada oportunidad antes de observar su resultado; no mezclan el tamaño elegido en la respuesta con el tamaño enfrentado. Limp/fold-call-raise se refiere a HU SB limp frente a iso/shove. Minraise es open no all-in a 2 BB; las respuestas fold/call comparten denominador. 3bet es una decisión con exactamente una subida previa preflop; incluye oportunidades frente a iso y distingue shove como numerador separado.

Postflop se usan los contextos del motor versionado: bet sin apuesta enfrentada en limped puro, cbet flop, fold vs cbet, check-raise con subida legal, probe, segundo/tercer barrel, folds frente a ellos, y acciones agresivas por calle. La agresión se define como (bet+raise+check-raise)/decisiones de esa calle: **no es AF ni AFq**. Cada decisión real cuenta; una ronda reabierta puede aportar otra oportunidad. No se inventan decisiones de all-ins.

Con filtro de rival en estas métricas se exige rival directo identificado: BTN first-in multiway no recibe una identidad ficticia ni se confunde con un rival sin clasificar. Las categorías aplicadas siguen siendo actuales, no históricas. El stack inicial efectivo multiway es el máximo contestable con algún rival; no sustituye un enfrentamiento HU concreto.

Cero oportunidades significa métrica ausente/indeterminada, no 0%. Una frecuencia con oportunidades muestra casos, denominador e IC Wilson. Los contadores de volumen no reciben un intervalo binomial.

## Reglas

Las hojas tienen métrica, intervalo y muestra mínima (frecuencias: mínimo 30). Para frecuencias se exige que **todo el IC Wilson** esté dentro del intervalo, no solo el punto observado. Los contadores se evalúan en unidades de volumen.

El motor permite AND/OR anidados, hasta cinco niveles. La interfaz permite agrupar condiciones en un AND u OR por regla y combinar varias reglas en un conjunto; los árboles anidados más profundos están soportados por el motor, pendientes de editor visual completo. No se exige SQL.

Se usa lógica de tres estados: verdadero, falso y evidencia insuficiente. La ausencia de una métrica no satisface un intervalo que contiene cero. AND con una condición falsa es falso; OR con una verdadera es verdadero; cuando no se puede decidir se mantiene desconocido.

Las puntuaciones configurables suman pesos de reglas satisfechas. No son probabilidades ni calibración de fuerza. Si reglas satisfechas asignan categorías o subperfiles incompatibles, el resultado es conflicto: no se resuelve con un peso arbitrario. Las etiquetas manuales prevalecen siempre.

La previsualización muestra jugadores, propuesta, estado, puntuación y evidencia por condición/regla (casos, oportunidades, IC e intervalo exigido). No escribe. La aplicación es transaccional: reevalúa automáticas del contexto y conserva etiquetas fuera del contexto, registros, manuales e historial. Si una automática del contexto ya no satisface evidencia, pasa a Sin clasificar de forma auditada.

Cada aplicación conserva antes/después, reglas, contexto y evidencia en `classification_run`. Deshacer restaura etiquetas/perfiles/reglas anteriores y registra la operación. Se bloquea si existen etiquetas/perfiles o reglas posteriores diferentes; no sobrescribe decisiones manuales posteriores. La interfaz exige volver a previsualizar si cambiaron datos o etiquetas desde la consulta.

## Grupos sin etiquetas

Una población personalizada guarda condición, contexto, miembros y fecha en `documents` (kind `population`). No modifica etiquetas Reg/Fish. Es un **snapshot explícito**, no una clasificación permanente ni un grupo que cambie silenciosamente al importar.

Se puede recuperar, editar y guardar con el mismo nombre para actualizar miembros. Los exploradores aplican `actor_group` y `opponent_group` como filtros de membresía; si se combinan con Reg/Fish, se usa su intersección. Una población vacía o inexistente no aporta oportunidades. Las consultas guardadas referencian el nombre del grupo y usarán su snapshot vigente si lo actualizas; aún no fijan automáticamente una versión histórica de miembros.

No hay migración de esquema: se reutiliza `documents`, manteniendo esquema 2/análisis 3. Los reportes, reglas simples y funciones anteriores se conservan.

## Verificación y límites

`python -m scripts.validate_behavior --db RUTA --output INFORME.json` compara métricas por jugador con acciones originales HU de €5 en solo lectura. Resultado en la base real: **1.200 jugadores**, cero discrepancias en seis frecuencias y tres contadores de volumen:

| Métrica | Casos / oportunidades |
|---|---:|
| VPIP | 18.625 / 30.088 |
| PFR | 9.683 / 30.088 |
| VPIP−PFR | 8.942 / 30.088 |
| Limp HU SB | 6.572 / 15.392 |
| Fold BB vs minraise HU | 286 / 743 |
| Fold frente a tercer barrel HU, todos los tipos de bote | 108 / 213 |

El último denominador **no es** el spot prioritario de limped HU (196 oportunidades): incluye otros botes. Tampoco se atribuyen estos números a Fish sin etiquetas.

Las demás métricas usan el motor validado y tienen pruebas de oportunidades; no se presentan como contrastadas independientemente todas sus variantes reales. WTSD, WWSF, W$SD, defensa BB más detallada y otras métricas de showdown permanecen pendientes. No se sustituye WTSD por «mostró cartas», que induciría sesgo.

Wilson sigue siendo exploratorio: dependencia por jugador, múltiples búsquedas, selección de población a partir de la misma muestra y clasificación temporal pueden sesgar conclusiones. No se demuestra EV ni que una categoría corresponda a ganador/perdedor. La clasificación es global por jugador; el contexto filtra evidencia, no crea una etiqueta separada permanente para cada modalidad.
