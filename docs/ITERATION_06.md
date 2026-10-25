# Iteración 0.6 · investigación y estudio por Python

Se continúa desde `ff799d6`, conservando los 79 reportes y los datos. Esta iteración no construye ejecutables ni instaladores, no ejecuta PyInstaller ni Inno Setup y no cambia dependencias. El workflow de empaquetado deja de dispararse automáticamente con los pushes; queda manual y aplazado.

## Funciones entregadas

- **59 reportes adicionales: 138 en total**, más constructor. SRP BTN contra SB y BB, respuestas separadas según la acción del tercero, barrels con dos defensores o tras fold de uno, y river lead/stab y sus respuestas después de turn check-through o dos calles sin apuesta. Ver [ADVANCED_SPOTS.md](ADVANCED_SPOTS.md).
- Clasificación con **vista previa sin escrituras**, conflictos y evidencia insuficiente visibles. Aplicación transaccional con rollback, etiquetas manuales protegidas y limpieza de subperfiles automáticos retirados. Búsqueda de jugadores y recuperación de categoría/subperfil al seleccionarlos.
- Pestaña Reg/Fish con muestras, jugadores, frecuencias, IC por grupo y diferencias en puntos porcentuales. Los grupos con cero casos se distinguen de los grupos sin muestra. No se afirma EV ni significación de la diferencia. Ver [CLASSIFICATION_COMPARISON.md](CLASSIFICATION_COMPARISON.md).
- Manos del Explorer y de secuencias abren el **replayer antes de la decisión seleccionada**, manteniendo ocultas las cartas no conocidas entonces.
- Consultas interactivas del Population Explorer en **worker cancelable**, con rechazo de resultados si cambiaron los filtros. Las cargas iniciales y algunas actualizaciones internas siguen siendo síncronas.
- Rediseño de **clasificación, importación, Leak Finder, Strategy Builder y referencias/EV**: editor lateral con scroll, resultados en paneles ajustables y pestañas. Conservan controles, guardado, exportaciones y callbacks anteriores; se mantienen tema nativo, Explorer, estudio, secuencias y configuración.

## Validación y datos

Suite completa: **151 pruebas pasan** (142 anteriores + 9 nuevas). Incluye ambos resultados de triple barrel multiway, roles persistentes, river check-through, conservación del catálogo anterior, fixtures reales, preview sin mutación, prioridad manual, conflictos, rollback de reglas, comparación con cero casos, replayer en el punto correcto, búsqueda/selección y consultas Qt en segundo plano.

Los originales de €5 se contrastaron con una máquina de estados independiente sobre acciones/importes, en solo lectura:

- 59 reportes, **3.384 oportunidades sumadas**.
- Cero oportunidades omitidas, adicionales o con resultado distinto.
- Cbet BTN multiway: 188 oportunidades; SB frente a cbet: 151; BB después de SB call: 43; BB después de SB fold: 71.
- Turn barrel con los dos callers: nueve oportunidades. Triple barrel river con los tres todavía en la mano: **cero casos reales como actor no Hero** en esta selección; sus casos positivos se prueban con manos sintéticas.
- Cinco historiales reales con nombres sustituidos añadidos a los fixtures y conciliados. No se importan automáticamente a la base del usuario.

Las sumas de reportes no son manos independientes: una misma mano puede aportar varios nodos. Las frecuencias no demuestran EV. IC Wilson exploratorios, etiquetas actuales y confianza de clasificación no calibrada siguen siendo límites explícitos.

La base de trabajo conserva **70.038 manos, 308.439 decisiones, 4.140 resúmenes y 14 registros en cuarentena**. Esta versión no cambia esquema 2 ni análisis 3: no requiere regeneración o reimportación. Historiales originales, backups y base personal permanecen fuera de Git.

Todas las vistas se renderizaron a **1920×1080 y 2560×1440** en Linux/offscreen; se revisaron visualmente clasificación y Leak Finder. No sustituye una comprobación física de la aplicación Python en Windows y sus DPI.

```bash
QT_QPA_PLATFORM=offscreen python -m pytest -q
python -m scripts.validate_advanced --db RUTA --output INFORME.json
```

## Cómo probar en Windows

1. Cierra la aplicación y actualiza el código en la misma carpeta. Si utilizas Git, ejecuta `git pull`. Conserva `.venv` y tu carpeta de datos.
2. Abre **start_windows.bat**, igual que antes. Reutiliza el Python del entorno existente; no se necesita reinstalar Python ni instalar dependencias nuevas.
3. En **Explorador de secuencias**, prueba los presets **3H SRP multiway** o los de **river**. Comprueba filtros de población/roles y las pestañas de comparación y manos. Doble clic en una mano abre la decisión en el replayer.
4. En **Regulares y Fishes**, selecciona un jugador, revisa su etiqueta y usa **Previsualizar reglas sin guardar** antes de aplicar reglas propias. La previsualización no cambia las etiquetas.
5. En Population Explorer, **Investigar población** consulta en segundo plano y **Cancelar consulta** interrumpe el trabajo. No cierres mientras haya una consulta activa.

La ubicación habitual de la base sigue siendo `%LOCALAPPDATA%\SpinPopulationLab\population.duckdb`. No borres esa carpeta, `imports/` ni los backups para actualizar. Si usas una ruta personalizada, continúa abriendo esa misma base.

## Fases y pendientes

| Fase | Estado y trabajo pendiente |
|---|---|
| 2 · Investigación | Se cubre el bloque multiway SRP y river de esta entrega, manteniendo barrels limped y SRP anteriores. Pendientes: catálogo multiway después de raises posteriores, árboles de sidepots más amplios, limped multiway y otras líneas river. No se declara completa la fase en toda la extensión del prompt. |
| 3 · Interfaz | Las pantallas principales comparten ahora estructura de escritorio con editor/resultados; navegación a replayer mejorada. Pendientes: pulido de estados vacíos, búsqueda de presets, paginación/virtualización de tablas y revisión Windows/DPI por Python. |
| Clasificación/comparación | Preview, atomicidad y comparación por nodo entregados. Pendientes: calibración externa, clasificación histórica y comparación arbitraria de dos escenarios/fechas/stacks. |
| Rangos/leaks/EV | Funcionalidades anteriores conservadas. Pendientes: rangos avanzados, incertidumbre agrupada, múltiples búsquedas y EV por árboles. |
| Datos/producto | 14 historiales ambiguos siguen excluidos; pendiente contraste con el replayer original y benchmark a millones. Empaquetado e instalador explícitamente aplazados por petición del usuario. |
