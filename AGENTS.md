# Instrucciones para Codex

- Objetivo: analizador offline de tendencias poblacionales **Regs vs Fishes** para Spins iPoker, HU y 3-handed. Interfaz en español para Windows.
- No implementar HUD, lectura de mesas en vivo, asistencia en tiempo real, bots, scraping ni datamining. Usar solamente historiales propios/importados con permiso de la sala.
- Fuente de verdad: historiales XML reales aportados por el usuario; no adivinar códigos de acciones o semántica de importes. Ante dudas, registrar warnings y no producir estadísticas falsas.
- Para cada estadística registrar la **oportunidad** real y el resultado; validar con fixtures y denominadores. Mantener separado jugador que actúa vs tipo de oponente.
- Reg/Fish: por defecto etiquetado manual y 'Sin clasificar'; no afirmar clasificación automática fiable con muestras pequeñas.
- Nunca asumir cartas privadas conocidas si no se muestran; distinguir información de showdown y rangos inferidos.
- Mostrar tamaño de muestra e incertidumbre, así como filtros por stake, número de jugadores, posición y BB efectivas.
- Para cualquier sugerencia explotativa añadir baseline claramente identificado, cálculo EV (si existe) y validación por muestras; nunca etiquetar una diferencia estadística como +chipEV sin justificarla.
- Priorizar tests reproducibles, parser seguro, duplicados y registro de errores; no perder datos importados.
- Mantener todas las mejoras documentadas en README.md y agregar pruebas.
