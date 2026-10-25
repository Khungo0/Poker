# Spin Population Lab · escritorio 0.4

Aplicación de investigación **offline** de Spins iPoker/ChampionPoker. Evolución del prototipo adjunto: interfaz PySide6 oscura, DuckDB y un importador del formato TXT real aportado. Diseñada para **1440×900, 1920×1080 y 2560×1440**, con layout adaptable y escalado Qt. No incluye HUD ni lectura de mesas.


## Nuevo: investigación por secuencias

Abre **Panel de estudio → Tercer barrel · respuestas**, selecciona stake y población y pulsa **Investigar secuencia**. Usa el constructor plegable para añadir acciones/roles/condiciones. Doble clic en una acción abre la rama siguiente; doble clic en una mano abre el replayer. Guarda la investigación con un nombre para recuperarla desde el panel de estudio.

La primera apertura de una base 0.2 crea un backup verificado y migra/regenera el contexto; puede tardar alrededor de un minuto en esta muestra. Se muestra progreso y la operación admite cancelación con rollback. **Datos y configuración** permite crear backups y restaurarlos como una copia nueva. Conserva también `imports/`.

El [informe de la iteración 0.3](docs/ITERATION_03.md) conserva la validación del motor y la migración. El spot prioritario tiene 196 respuestas verificadas con un algoritmo independiente; **no se califican como Fish sin etiquetas**. La especificación completa está en [PRODUCT_REQUEST.md](docs/PRODUCT_REQUEST.md).

## Nuevo en 0.4: contexto por rol y catálogo de reportes

El **Explorador de secuencias** ofrece **27 reportes** y un constructor personalizado: aperturas HU/3H, BB frente a limp/minraise/shove, limp frente a iso, respuestas a 3bet, squeeze y botes limpeados. Se distinguen las oportunidades de apostar un barrel (bet/check) de las respuestas a ese barrel (fold/call/raise).

En **Poblaciones por rol**, fija por ejemplo A = Reg y B = Fish. Las etiquetas, subperfiles y jugadores concretos se mantienen al avanzar a la siguiente acción. En los presets de barrels A apuesta y B defiende; en los demás, la descripción indica las posiciones de cada rol. Los filtros superiores **Actor de este nodo** y **Rival directo de este nodo** siguen aplicándose a la decisión actual.

El constructor permite limitar el tamaño de cada paso en BB o porcentaje de bote, elegir el rol/posición/calle de la siguiente decisión y exigir que exista una subida legal. Las investigaciones antiguas siguen abriendo y la base conserva el esquema 2: esta actualización no regenera ni reimporta datos.

Validación: **124 pruebas pasan**; el contraste independiente de los originales coincide en 15.392 aperturas HU, 743 respuestas a minraise y 765 oportunidades de squeeze 3H de €5. Consulta [ITERATION_04.md](docs/ITERATION_04.md) para los denominadores, límites y fases pendientes. El programa completo sigue en desarrollo.

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

Para construir Windows: `powershell -ExecutionPolicy Bypass -File packaging/build_windows.ps1`, con Python 3.12 e Inno Setup 6 instalados. Se generan una carpeta portable y un instalador por usuario. El workflow `.github/workflows/windows.yml` ejecuta tests y publica artefactos de CI cuando se ejecuta en GitHub. **No se ha ejecutado todavía un build/instalación Windows en esta sesión Linux.**

## Pendiente antes de considerar el producto terminado

- Resolver las 14 manos del archivo real que carecen de ciegas nominales verificables; se necesita exportación completa o replayer para contrastarlas.
- Ejecutar y verificar EXE e instalador en Windows, DPI 100/125/150%, distribución limpia y actualización; firma digital opcional.
- Validación independiente contra replayer de la sala; stress/benchmark con millones de manos, paginación y consultas en segundo plano.
- Adaptadores de formatos nativos de solvers; matrices interactivas de sus rangos y modelos EV completos multi-street/raises/sidepots/ICM.
- Inferencia robusta por jugador/torneo y corrección de búsquedas múltiples; calibración externa de las clasificaciones. Los IC actuales son binomiales exploratorios.
- Migración guiada de la antigua base SQLite y finalización del asistente de estadísticas/rangos. El prototipo Streamlit/XML original permanece en `app.py`, requiere `requirements-legacy.txt` y usa otra BD; no es el flujo recomendado para los TXT reales.

El repositorio distribuye código y fixtures con nombres sustituidos; los historiales originales y la base personal están excluidos de Git. Usar únicamente historiales propios o autorizados.
