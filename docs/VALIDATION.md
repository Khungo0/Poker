# Validación de esta iteración

Ejecutada en el entorno Linux de desarrollo. No equivale a certificación de Windows ni comparación visual con el replayer de ChampionPoker.

## Archivos originales

- RAR aportado: 4.211 TXT, 54.171.591 bytes extraídos.
- 71 archivos de manos: 70.052 registros GAME.
- 4.140 resúmenes PokerTracker, conservados sin generar estadísticas de acciones.
- 70.038 manos aceptadas, con conciliación de aportaciones, devoluciones y premios; 39.016 de 3 jugadores y 31.022 HU.
- 69.804 manos aceptadas de €5; 139 de €10, 39 de €20 y 56 de €25. Los stakes se mantienen separados.
- 14 manos rechazadas por ciegas nominales ausentes en headers con posts cortos/all-in. Los originales y errores están conservados; ninguna contribuye a estadísticas.
- 308.439 decisiones reconstruidas, de ellas 116.126 de Hero identificado mediante `Dealt to`. **El Explorer y las reglas excluyen Hero por defecto.**
- No se encontraron game IDs duplicados en el corpus original. Las pruebas independientes sí ejercitan duplicados exactos, nombres de archivo cambiados y conflictos del mismo ID.

## Repetibilidad

Importación completa en `data/population-v2.duckdb`: 70.038 manos, 308.439 observaciones, 4.140 resúmenes, 14 errores.

Regeneración transaccional de observaciones desde las manos originales: mismo número de decisiones. Reimportación posterior de los 4.211 archivos: 0 manos nuevas, 0 observaciones nuevas, 0 resúmenes nuevos, 0 errores adicionales. Los informes están en `data/validation-import.json`, `data/rebuild-report.json` y `data/reimport-report.json` (datos locales ignorados por Git).

Consulta comprobada (sin Hero): SB_FIRST, HU, EUR 5.00 = 15.392 oportunidades, 1.179 jugadores, 2.755 torneos. La mayor contribución individual es aproximadamente 1,58%. Es evidencia de funcionamiento de filtros/denominadores, **no una recomendación estratégica**. La consulta y consultas auxiliares del informe tardaron alrededor de 25 ms en esta instancia; no es un benchmark de millones de manos.

## Pruebas automatizadas

`QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q`: **68 passed**.

Incluye 47 manos reales completas con nombres sustituidos, pruebas del prototipo XML conservado, reconstrucción exacta de raise-to y calls, antes/all-ins/ciegas cortas, cartas X, devolución de excesos, subida corta que no reabre, delayed cbet/probe, call all-in que no es raise, orden inválido, importe inválido, truncado, duplicados/conflictos, filtros actor/rival, exclusión de Hero, etiquetas prioritarias, muestras insuficientes, documentos de referencia/estrategia, fórmula EV limitada y regeneración de observaciones.

Prueba Qt: abrir base temporal, importar fixtures, consultar spot y navegar las seis páginas a **1920×1080 y 2560×1440** mediante plataforma offscreen. También se renderizó el Explorer con la base real. No se ha comprobado el DPI ni la interacción física en Windows.

`pip check`: sin dependencias rotas. Compilación de módulos Python: correcta.

PyInstaller creó el bundle Linux y el ejecutable arrancó con Qt offscreen, creando su BD local; se terminó después de la comprobación. Esto solo valida el empaquetado y arranque en Linux, no sustituye el build Windows ni una prueba de interacción del ejecutable empaquetado.

## Pendiente de validación externa

- Verificación con replayer y recuperación de los headers completos de las 14 manos en cuarentena.
- Build e instalación en Windows y revisión a DPI 100/125/150%. El script PowerShell, PyInstaller, Inno Setup y workflow están preparados; su presencia no demuestra que el EXE Windows esté compilado o probado.
- Rendimiento con millones de manos, modelos EV generales y referencias solver reales: aún sin validar. No se han añadido etiquetas, baselines solver ni tendencias ficticias para aparentar resultados.
