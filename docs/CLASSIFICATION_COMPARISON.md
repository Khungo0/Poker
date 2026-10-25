# Clasificación y comparaciones 0.6

La vista previa de reglas es de solo lectura: muestra propuestas, conflictos, falta de evidencia y etiquetas manuales protegidas antes de aplicar nada. Sigue requiriendo mínimo de manos y que el IC completo esté dentro del intervalo configurado. Ningún umbral ni etiqueta se añade automáticamente.

La aplicación de reglas es ahora una única transacción: un error revierte etiquetas, subperfiles, historial y reglas activas. Las etiquetas manuales se conservan. La retirada de una etiqueta automática al reevaluar se registra y elimina también el subperfil automático obsoleto, que antes podía seguir filtrando a un jugador sin etiqueta vigente.

La confianza mostrada es fuerza heurística de evidencia, no probabilidad calibrada de pertenecer a Reg/Fish. Los perfiles manuales se recuperan al seleccionar un jugador. Las clasificaciones siguen siendo actuales, no históricas por fecha.

La pestaña Reg vs Fish de secuencias muestra oportunidades, jugadores, frecuencias, IC Wilson para cada grupo y diferencia en puntos porcentuales. Cero casos con denominador positivo se muestra como 0%, con su intervalo; denominador cero se muestra sin muestra. No se presenta un IC de diferencia ni se supone independencia entre grupos/manos. Los filtros de roles permanecen activos: pueden dejar uno de los grupos vacío por diseño.

Las manos del Explorer y de secuencias abren el replayer antes de la decisión elegida, con board de esa calle y cartas privadas aún ocultas salvo Hero conocido. No se adelantan resultados de showdown.
