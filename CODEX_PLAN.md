# Continuación · iteración 0.8 y nuevo prompt maestro

Leer AGENTS.md, docs/MASTER_REQUEST.md, docs/ITERATION_08.md y docs/BEHAVIOR_METRICS.md. El nuevo orden es clasificación/poblaciones → rediseño 1440×900 → constructor → Dual/rangos → postflop → explotaciones → pulido. No continuar el orden antiguo sin atender esta prioridad.

Estado: 180 reportes conservados, 169 pruebas; esquema 2/análisis 3. Importador TXT, reconstrucción y datos permanecen. Base local: data/population-v2.duckdb, 70.038 manos/308.439 decisiones/4.140 resúmenes/14 errores. No se incluyen originales o bases en Git.

Entregado en 0.8: src/behavior.py (31 métricas/opciones, AND/OR con evidencia desconocida, scores no calibrados, preview, aplicación/rollback auditados, grupos snapshot), src/behavior_ui.py (editor y tablas virtualizadas, worker), filtros actor_group/opponent_group en exploradores. Se conservan reglas simples y todas las funciones anteriores.

Verificador real: python -m scripts.validate_behavior --db RUTA --output INFORME.json; seis frecuencias y tres volúmenes por jugador HU €5, 1.200 jugadores, cero discrepancias. No equivale a validar independientemente todas las métricas. Mantener regresiones y oráculos de iteraciones anteriores; los informes 03–07 siguen describiendo el catálogo existente.

Próximo bloque Fase 1: denominadores reproducibles WTSD/WWSF/W$SD y defensa BB más detallada, edición anidada visual y revisiones. No estimar showdown solo por cartas reveladas. Preparar Fase 2: dashboard útil, organización global y reutilización del modelo QTableView en tablas antiguas. Resolución principal 1440×900, también 1920×1080 y 2560×1440.

Límites: etiquetas globales actuales, snapshots de grupos actualizados solo explícitamente, sin incertidumbre agrupada ni corrección de múltiples búsquedas. El editor admite un nivel AND/OR por regla y conjuntos de reglas; el motor admite anidamientos. Las reglas de clasificación anteriores y nuevas reevalúan etiquetas automáticas; ambas protegen manuales. No convertir puntuaciones ni frecuencias en rentabilidad.

Conservar funciones de referencias/EV anteriores, pero NO ampliar solvers ni comparación teórica en esta etapa. NO trabajar en EXE, PyInstaller, Inno Setup o instaladores. Python/start_windows.bat y .venv existentes, sin nuevas dependencias. No borrar ni reimportar datos para actualizar. Cualquier migración futura requiere backup verificado.
