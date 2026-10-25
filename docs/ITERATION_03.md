# Investigación por secuencias · iteración 0.3

## Entregado

Se conserva el proyecto y su importador, base de datos, etiquetas y herramientas anteriores. La especificación íntegra del usuario está en PRODUCT_REQUEST.md.

- Contexto de decisiones versionado: formato de torneo Spin 3-max independiente de HU/3H, jugadores activos, stack inicial, efectivo al principio de calle, SPR, iniciativa preflop, tipo de bote y número de barrel.
- `limped`, `limp_iso`, `srp`, `3bet`, `4bet+` y `unraised`. El tipo preflop refleja solo lo ocurrido hasta la decisión; postflop refleja toda la ronda preflop.
- Cbet se reserva al primer bet del agresor preflop en flop. Segundo/tercer barrel requieren al mismo primer apostador en calles consecutivas; un raise rompe esa continuidad. La respuesta recibe la etiqueta correspondiente. No hay CBET/VS_CBET en botes limpeados puros.
- `facing_bb` es el coste efectivo de pagar, limitado por el stack del actor. `facing_pct` sigue siendo la apuesta **anunciada** respecto al bote anterior; puede superar la cantidad igualable. La UI lo identifica expresamente.
- Motor SQL de prefijos consecutivos, roles A/B/C distintos y vinculados a jugadores concretos, pasos opcionales, exclusión de acciones y límites de tamaño. Nunca salta acciones silenciosamente. Vinculaciones ambiguas para una misma decisión se excluyen.
- Presets HU limped: respuesta a bet flop, segundo barrel y tercer barrel. El prefijo termina **antes** del resultado; fold/call/raise comparten denominador. Los check-raises postflop se agrupan como raise en el informe, conservando el detalle original en las manos.
- Frecuencia por decisión, promedio de frecuencias por jugador, IC Wilson por decisión, jugadores únicos, contribución máxima y frecuencia de llegada con denominador explícito. La llegada usa manos del mismo formato/stake/período: otros filtros, incluidas etiquetas, solo afectan al numerador. No es una probabilidad estimada de transición entre dos nodos ya filtrados.
- Constructor visual, navegación siguiente/anterior, tamaño anunciado, fechas, SPR, stack editable y presets 5/6/8/10/12/15/20/25 BB ±1 (los extremos son editables), población/subperfil de actor y rival, Hero opt-in. Mis investigaciones guarda/restaura filtros y secuencia; se pueden exportar a JSON sin editar código.
- Panel de estudio, comparación Reg/Fish en las ramas, replayer con mesa de 2/3 asientos, pasos, boards, stacks, apuestas y originales. Las cartas no repartidas a Hero permanecen ocultas hasta la revelación del resumen. No hay simulación de cartas desconocidas.
- Subperfiles manuales y soporte de reglas por HU/3H. Las etiquetas manuales prevalecen; no se añaden umbrales por defecto. Se registra el historial de cambios de etiquetas a partir de esta versión.
- Estrategias con estados, evidencia capturada al guardar, fecha y versiones. «EV evaluado» requiere modelo, supuestos y resultado explícitos; la UI no inventa esos datos.
- Consultas de secuencia en worker cancelable, migración con pantalla de progreso, cancelación de importación entre archivos completos, backup y restauración como copia nueva.

## Backup y migración

Schema 1 → 2. Antes de cambiar esquema se hace CHECKPOINT y copia verificada mediante SHA-256, con manifiesto de tablas y conteos en `backups/`. Columnas nuevas y regeneración de observaciones se ejecutan en una transacción. Error/cancelación conserva la versión anterior. Una base de versión desconocida se rechaza. Se preservan originales, errores, clasificaciones y documentos. No se migran automáticamente bases SQLite.

El backup contiene la base, incluyendo los textos de manos y resúmenes. Para conservar también los archivos originales completos, guardar la carpeta `imports/`. Restaurar requiere un destino inexistente y verifica el checksum; no reemplaza la base abierta.

En la base de trabajo la migración inicial tardó aproximadamente 66 s. Se conservaron 70.038 manos, 308.439 decisiones, 4.140 resúmenes y 14 errores. Se verificó igualdad de IDs, orden, resultados, actores, rivales, efectivos y tamaños anunciados. Cambios justificados: 18.680 etiquetas de spot y 16.717 costes de call limitados por stack. Cero CBET/VS_CBET en limped puro.

## Spot prioritario verificado

Selección: HU, EUR 5.00, SB limp → BB check; A bet flop → B call; A bet turn → B call; A bet river → decisión de B. Se permite el check previo de B cuando juega fuera de posición. A y B son los mismos jugadores en todas las calles. Hero excluido como defensor.

- 196 oportunidades, 164 jugadores.
- 100 folds, 88 calls, 8 raises (incluidos check-raises).
- Fold: 51,02%; IC Wilson 95%: 44,07%–57,93%.
- Llegada: 196 / 30.818 manos HU de €5.
- La base no contiene etiquetas de jugadores: **no es una estadística de Fishes**. Con población Fish el denominador es cero, hasta que el usuario clasifique sus rivales.

`python scripts/validate_sequences.py --db RUTA --output INFORME.json` contrasta IDs y resultados con un algoritmo independiente que recorre las acciones originales, sin usar el motor SQL de secuencias. Resultado: 196 contra 196; cero omitidas, adicionales o resultados distintos.

Revisión manual de los TXT: fixtures de call, fold/overbet y check-raise. Ejemplo 12543199593: bote preflop 70; flop +60; turn +194; river empieza con 324 y apuesta 180 → 55,56% de bote. El defensor paga; bote final 684. Los tres historiales completos con nombres sustituidos se conservan en `tests/fixtures/third_barrel_real_anonymized.txt`.

Esta revisión manual del texto y el replayer propio no sustituyen una verificación contra el cliente/replayer original de la sala.

## Investigación externa

Se intentó consultar Hand2Note, PokerTracker, Two Plus Two y Reddit. El proxy del entorno respondió `403 Forbidden` a todos. **No se ha leído esa documentación ni se atribuyen hallazgos a esas fuentes.** Se guardaron dominios adicionales en el borrador de red para revisión, sin afirmar que ya estén activos. La implementación usa requisitos del usuario y el código/los datos disponibles, sin copiar recursos de terceros.

## Estado de las fases

| Fase | Estado |
|---|---|
| 1: auditoría/motor | Motor, migración y regresión implementados y probados. Investigación externa bloqueada y 14 manos ambiguas aún excluidas. |
| 2: investigación avanzada | Spot prioritario y tres presets limped verificados; constructor general disponible. Falta completar todo el catálogo preflop/postflop de la especificación. |
| 3: visual | Nuevas vistas de secuencias, estudio y replayer, controles y eliminación de varios bloques JSON. Rediseño integral aún parcial. |
| 4: rangos/comparación | Comparación Reg/Fish por rama y ponderación por jugador implementadas. Matrices avanzadas, familias postflop y constructor completo de estadísticas pendientes. |
| 5: estrategias | Versiones, estados y evidencia guardada. Ranking avanzado de leaks y evaluación EV de árboles pendientes. |
| 6: producto | Backups, migración, workers y pruebas ampliadas. Benchmark de millones, restauración guiada activa, Windows/DPI/instalador y actualización distribuida pendientes. |

Limitaciones estadísticas: Wilson supone independencia; la ponderación por jugador no lleva todavía intervalo cluster-bootstrap. No se corrigen múltiples búsquedas. Las etiquetas actuales se aplican también a períodos históricos: el registro de cambios no proporciona aún clasificación histórica sin información futura. Las ramas comparadas mantienen los filtros actuales; al avanzar, el filtro de población se aplica al **nuevo actor** de la decisión, no a un rol persistente. Los roles A/B sí preservan identidad, pero el editor aún no ofrece categorías fijas por rol arbitrario. Cancelación/rollback y backup no constituyen benchmark a millones de manos.

## Pruebas de esta entrega

`QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q`: **89 pruebas pasan**, incluidas las 68 previas. Se añaden ambos sentidos de agresión HU, fold/call/raise como denominador común, all-in, rol defensor frente a agresor, cambio de agresor, exclusión de limp/iso, checks opcionales, fechas/tamaños, copia/restauración, cancelación con rollback, subperfiles y auditoría de etiquetas, orden postflop distinto en 3H, coste de call y manos reales revisadas. También se prueba el worker de consulta y recuperación de filtros guardados, y se renderizan vistas a 1440×900, 1920×1080 y 2560×1440.

La entrada de escritorio arranca en Linux con preparación de datos en segundo plano. Las pruebas usan UTF-8 explícito para evitar discrepancias de codificación en Windows. Aún falta validar Windows y DPI reales.
