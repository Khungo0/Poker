# Spin Population Lab · escritorio 0.8

Aplicación de investigación **offline** de Spins iPoker/ChampionPoker. Evolución del prototipo adjunto: interfaz PySide6 oscura, DuckDB y un importador del formato TXT real aportado. Diseñada para **1440×900, 1920×1080 y 2560×1440**, con layout adaptable y escalado Qt. No incluye HUD ni lectura de mesas.


## Actualizar y seguir usando Python

Actualiza el código en la misma carpeta, conservando `.venv` y tus datos, y vuelve a abrir **start_windows.bat**. No hay dependencias nuevas ni necesitas reinstalar Python. La base existente es compatible y no hay que reimportar historiales. El empaquetado/instalador está aplazado; no se construye automáticamente al actualizar código.

**Nuevo en 0.8 · clasificación y poblaciones:** se conservan los **180 reportes**. En **Regulares y Fishes → Métricas y poblaciones** puedes consultar 31 métricas/opciones por contexto, combinar reglas AND/OR, revisar evidencia, aplicar/deshacer clasificaciones y guardar grupos sin cambiar etiquetas. Los grupos se filtran como actor/rival en ambos exploradores. Los resultados nuevos usan tablas con búsqueda, ordenación, barras y exportación.

**169 pruebas pasan**. Un verificador independiente coincide por jugador en seis frecuencias y tres contadores de volumen de 1.200 rivales HU de €5. [Definiciones](docs/BEHAVIOR_METRICS.md), [cómo probar y pendientes](docs/ITERATION_08.md). El nuevo [prompt maestro](docs/MASTER_REQUEST.md) empieza por clasificación; no se amplían solvers ni comparación teórica.

**Nuevo en 0.7:** **180 reportes**, conservando los 138 anteriores. Se añaden limped multiway y respuestas frente a raises/reraises con roles persistentes, además de búsqueda visual de presets por términos como `3H limped` o `raise SB`.

**162 pruebas pasan**. Los 42 reportes nuevos coinciden con un verificador de acciones originales en 2.377 oportunidades sumadas, sin discrepancias. No se cambia el esquema ni se requiere reimportación. [Verificación tras la interrupción, uso y pendientes](docs/ITERATION_07.md).

**Nuevo en 0.6:** 138 reportes (los 79 anteriores más 59 de SRP multiway/river), clasificación con vista previa y aplicación transaccional, comparación Reg/Fish con intervalos y diferencia en puntos porcentuales, consultas del Explorer cancelables en segundo plano y replayer situado antes de la decisión. Clasificación, importación, leaks, estrategias y referencias usan paneles modernos de edición/resultados.

**151 pruebas pasan**. Los 59 reportes nuevos coinciden con un oráculo de historiales originales en 3.384 oportunidades sumadas, sin discrepancias. [Cómo probar y qué falta](docs/ITERATION_06.md).

## Nuevo: investigación por secuencias

Abre **Panel de estudio → Tercer barrel · respuestas**, selecciona stake y población y pulsa **Investigar secuencia**. Usa el constructor plegable para añadir acciones/roles/condiciones. Doble clic en una acción abre la rama siguiente; doble clic en una mano abre el replayer. Guarda la investigación con un nombre para recuperarla desde el panel de estudio.

La primera apertura de una base 0.2 crea un backup verificado y migra/regenera el contexto; puede tardar alrededor de un minuto en esta muestra. Se muestra progreso y la operación admite cancelación con rollback. **Datos y configuración** permite crear backups y restaurarlos como una copia nueva. Conserva también `imports/`.

El [informe de la iteración 0.3](docs/ITERATION_03.md) conserva la validación del motor y la migración. El spot prioritario tiene 196 respuestas verificadas con un algoritmo independiente; **no se califican como Fish sin etiquetas**. La especificación completa está en [PRODUCT_REQUEST.md](docs/PRODUCT_REQUEST.md).

## Nuevo en 0.4: contexto por rol y catálogo de reportes

El **Explorador de secuencias** ofrece **27 reportes** y un constructor personalizado: aperturas HU/3H, BB frente a limp/minraise/shove, limp frente a iso, respuestas a 3bet, squeeze y botes limpeados. Se distinguen las oportunidades de apostar un barrel (bet/check) de las respuestas a ese barrel (fold/call/raise).

En **Poblaciones por rol**, fija por ejemplo A = Reg y B = Fish. Las etiquetas, subperfiles y jugadores concretos se mantienen al avanzar a la siguiente acción. En los presets de barrels A apuesta y B defiende; en los demás, la descripción indica las posiciones de cada rol. Los filtros superiores **Actor de este nodo** y **Rival directo de este nodo** siguen aplicándose a la decisión actual.

El constructor permite limitar el tamaño de cada paso en BB o porcentaje de bote, elegir el rol/posición/calle de la siguiente decisión y exigir que exista una subida legal. Las investigaciones antiguas siguen abriendo y la base conserva el esquema 2: esta actualización no regenera ni reimporta datos.

Validación: **124 pruebas pasan**; el contraste independiente de los originales coincide en 15.392 aperturas HU, 743 respuestas a minraise y 765 oportunidades de squeeze 3H de €5. Consulta [ITERATION_04.md](docs/ITERATION_04.md) para los denominadores, límites y fases pendientes. El programa completo sigue en desarrollo.

## Nuevo en 0.5: SRP y escritorio de investigación

Se añaden **52 reportes SRP**, manteniendo los 27 anteriores: **79 reportes** en total. Incluyen cbet, donk, probe, delayed cbet, stabs y segundo/tercer barrel, con oportunidades de apostar y respuestas separadas. HU y 3H conservan sus posiciones y roles. Los desgloses por textura y tamaño enfrentado están en la pestaña **Tamaños y texturas** del explorador de secuencias; la textura también puede filtrarse desde los controles avanzados.

**Population Explorer** usa ahora filtros laterales ajustables, tarjetas de muestra y pestañas de tabla/gráfico. La apariencia nativa Qt se actualiza en todas las vistas. El explorador de secuencias reúne árbol, manos originales y desgloses en pestañas para aprovechar 1920×1080 y 2560×1440.

**142 pruebas pasan**. Los 52 reportes SRP coinciden con una máquina de estados independiente sobre historiales originales (17.315 oportunidades sumadas, cero discrepancias). El tercer barrel limped conserva sus 196 oportunidades verificadas. Consulta [POSTFLOP_SRP.md](docs/POSTFLOP_SRP.md) para las definiciones y [ITERATION_05.md](docs/ITERATION_05.md) para estado y pendientes.

La actualización corrige nueve all-ins que abrían calle y estaban etiquetados como raises: son bets. El análisis sube a versión 3 con backup verificado y regeneración transaccional automática; conserva esquema, manos, etiquetas y estrategias. No necesitas reimportar datos.

## Abrir en Windows

Con Python 3.12 instalado, ejecutar `start_windows.bat`. La primera instalación necesita Internet para las dependencias; después la aplicación funciona offline. Alternativamente:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python desktop.py
```

Los datos se guardan en `%LOCALAPPDATA%\SpinPopulationLab\population.duckdb`; originales archivados en `imports/` junto a la BD. No se incluyen historiales personales en el instalador. En Linux se usa `~/.local/share/SpinPopulationLab`; `--db RUTA` permite elegir otra ubicación.

1. Extraer el RAR localmente e importar su carpeta de TXT desde **Importar historiales**. Los resúmenes se distinguen de las manos. Revisar los errores conservados.
2. Seleccionar **EUR 5.00**, HU/3H, spot, calle, posición, stack, acción anterior y textura en **Population Explorer**. El tamaño enfrentado se filtra en porcentaje de bote. Se puede restringir jugador y secuencia exacta. Hero queda excluido por defecto y puede incluirse con una casilla.
3. Inspeccionar manos y reconstrucción desde el explorador; exportar los resultados a CSV.
4. Etiquetar jugadores manualmente; opcionalmente definir y aplicar reglas VPIP/PFR. No hay reglas ni etiquetas iniciales inventadas.
5. Añadir referencias propias con los filtros del Explorer en **Leak Finder**. Guardar hipótesis por Reg/Fish en **Strategy Builder**. Las referencias de solver usan el [esquema documentado](docs/REFERENCE_FORMAT.md).

## Implementado y probado

- Lectura de TXT iPoker y resúmenes PokerTracker, UTF-8/BOM, metadata de stake, formatos de fecha y cartas parciales.
- Reconstrucción en enteros: antes, ciegas cortas, raise-to, call/all-in, devoluciones, orden de actuación, reapertura y cierre de apuestas, conciliación del bote y premios.
- Deduplicación por ID y hash, detección de conflictos, transacciones, archivo original y cuarentena; regeneración de observaciones.
- Decisiones HU/3H preflop y postflop, secuencia completa, tamaño, stacks, boards y textura; filtro separado de actor/rival.
- Conteos, frecuencias, jugadores/torneos únicos, Wilson 95%, concentración por jugador, tablas, gráfico y matriz condicionada a cartas reveladas.
- Clasificación manual/automática configurable, referencias explícitas, detección exploratoria de desviaciones, estrategias editables/exportables.
- Importación JSON de referencias/rangos y modelo EV terminal HU explícitamente condicionado a supuestos aportados.
- Interfaz desktop con importación en segundo plano. Empaquetado PyInstaller, Inno Setup y workflow Windows preparados.

Ver [validación](docs/VALIDATION.md) y [semántica y limitaciones](docs/DATA_MODEL.md). Las frecuencias observadas no demuestran EV; las cartas ocultas permanecen desconocidas.

## Desarrollo y validación

```bash
python -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q
.venv/bin/python -m src.cli import --db data/population.duckdb /ruta/a/TXT
.venv/bin/python -m src.cli status --db data/population.duckdb
.venv/bin/python -m src.cli rebuild --db data/population.duckdb
.venv/bin/python desktop.py --db data/population.duckdb
```

En este workspace la importación validada está en `data/population-v2.duckdb`. Los tests usan manos reales con nombres sustituidos y escenarios sintéticos identificados en los tests. Nunca se importan los fixtures a una base personal automáticamente.

El empaquetado y el instalador quedan aplazados por petición del usuario. Se conservan los scripts históricos, pero el flujo de desarrollo y uso recomendado continúa siendo Python y `start_windows.bat`. El workflow de empaquetado es únicamente manual y no se activa con los pushes.

## Pendiente antes de considerar el producto terminado

- Resolver las 14 manos del archivo real que carecen de ciegas nominales verificables; se necesita exportación completa o replayer para contrastarlas.
- Ejecutar y verificar EXE e instalador en Windows, DPI 100/125/150%, distribución limpia y actualización; firma digital opcional.
- Validación independiente contra replayer de la sala; stress/benchmark con millones de manos, paginación y consultas en segundo plano.
- Adaptadores de formatos nativos de solvers; matrices interactivas de sus rangos y modelos EV completos multi-street/raises/sidepots/ICM.
- Inferencia robusta por jugador/torneo y corrección de búsquedas múltiples; calibración externa de las clasificaciones. Los IC actuales son binomiales exploratorios.
- Migración guiada de la antigua base SQLite y finalización del asistente de estadísticas/rangos. El prototipo Streamlit/XML original permanece en `app.py`, requiere `requirements-legacy.txt` y usa otra BD; no es el flujo recomendado para los TXT reales.

El repositorio distribuye código y fixtures con nombres sustituidos; los historiales originales y la base personal están excluidos de Git. Usar únicamente historiales propios o autorizados.
