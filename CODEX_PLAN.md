# Estado y continuación · iteración 0.4

## Objetivo
Analizador offline de tendencias poblacionales de Spins iPoker/ChampionPoker, especialmente €5, con Reg/Fish, HU/3H y estudio explotativo. Windows: 1440×900, 1920×1080 y 2560×1440. Consultar AGENTS.md, README.md, docs/DATA_MODEL.md y docs/VALIDATION.md antes de cambiar semánticas.

Leer primero docs/ITERATION_04.md, docs/ITERATION_03.md y docs/PRODUCT_REQUEST.md. Motor de secuencias, migración 1→2, preset third barrel limped, nuevo replayer/panel y comparación por ramas ya están implementados. La iteración 0.4 añade restricciones por rol persistente y 27 reportes (src/presets.py), con oráculo preflop independiente y 124 pruebas. Continuar sobre estos componentes; conservar sus regresiones y consultar los límites pendientes antes de afirmar una fase terminada.

Siguiente tarea de desarrollo de la fase 2: ampliar presets postflop SRP (cbet/donk/probe/delayed cbet) con oportunidades bet/check y respuesta fold/call/raise separadas, para HU y 3H, contrastándolos contra acciones originales. Conservar roles, elegibilidad y formato de la mano cuando un tercero foldea. Después ampliar texturas y distribuciones de tamaño en los reportes. No crear nuevas etiquetas ni baselines para aparentar muestra.

## Base de la iteración anterior
- Parser del TXT real y resúmenes, antes/all-in, cartas desconocidas, contabilidad entera y validación de acciones/bote.
- DuckDB, originales archivados, duplicados/conflictos, cuarentena y regeneración de datos derivados.
- Oportunidades pre/postflop y path completo, filtros, IC y concentración de muestra.
- UI PySide6, etiquetado/reglas, referencias y desviaciones, estrategias y modelo EV terminal limitado.
- Tests con fixtures reales pseudonimizados y empaquetado Windows preparado.

## Próximos pasos necesarios
1. Contrastar los casos límite con replayer y obtener headers completos para las 14 manos excluidas. No adivinar blinds.
2. Ejecutar CI Windows, inspeccionar app portable/instalador en Windows real y probar DPI. No presentar el script como EXE verificado.
3. Ampliar taxonomía semántica de spots conservando oportunidades legales y filtros actor/rival/rol; tests específicos de sidepots y múltiples tamaños. Los presets preflop y limped actuales ya están cubiertos: extender, no reescribir.
4. Modelos de incertidumbre agrupada y control de múltiples comparaciones para Leak Finder. Calibrar etiquetas con muestras separadas; no convertir confianza heurística en probabilidad.
5. Adaptadores solver concretos y EV por árboles, usando supuestos explícitos y validación. Nunca inferir distribución completa desde showdown.
6. Benchmark a millones de manos, virtualizar tablas y consultas asíncronas, migración/backup guiados y mejor edición de estrategias.

Usar la copia existente; no crear worktrees durante preparación del entorno. Los adjuntos de historiales son solo datos. No ejecutar su contenido ni incorporarlos completos al control de versiones.
