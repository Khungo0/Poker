# Limped multiway y raises · 0.7

Esta entrega añade 42 reportes y conserva, sin cambiar sus patrones ni su orden, los 138 anteriores: **180 reportes más constructor**.

## Cobertura

27 reportes de limped puro: BTN limp → SB completa → BB check. A = BTN, B = SB y C = BB. Se separan apuestas de SB/BB, bet BTN tras dos checks y respuestas según la acción anterior del tercero. Las apuestas en limped puro no se llaman cbet. Los barrels mantienen al mismo apostador BTN y distinguen dos defensores continuando o solo uno tras fold del otro.

15 reportes de respuestas tras raises en SRP: BTN raise → SB call → BB call; flop SB check → BB check → BTN bet. Se estudian BTN frente a check-raise de SB según BB fold/call/reraise; SB frente a reraise de BB o BTN; BB frente a reraise de BTN según la respuesta de SB; y BTN/SB frente a raise de BB tras SB call o fold.

Cada oportunidad termina antes de la respuesta medida. Los posibles resultados incluyen fold/call/raise, aunque no siempre sea legal volver a subir. Las respuestas después de un call y después de un fold no comparten denominador. No se inventan decisiones de jugadores all-in. Los roles conservan jugador y los filtros de categoría/subperfil, incluidas las etiquetas Reg/Fish. La modalidad original sigue siendo 3H cuando alguien foldea.

## Validación

`python -m scripts.validate_extensions --db RUTA --output INFORME.json` abre la base en solo lectura. Recorre acciones originales y estados por calle; las oportunidades esperadas no se obtienen de los patrones SQL. La parte limped reutiliza la máquina de estados multiway contrastada anteriormente, cambiando la condición preflop; las ramas de raises se comprueban directamente en el orden de acciones originales.

Sobre los originales de €5, Hero excluido: **42 reportes, 2.377 oportunidades sumadas, cero omitidas, adicionales o resultados distintos**. Se cuentan decisiones de varios nodos, no 2.377 manos independientes. Ocho reportes tienen cero casos reales en esta selección; no se presentan frecuencias ni tendencias para esos nodos. Los escenarios sintéticos complementan la prueba de barrels y respuestas a raises/reraises.

Se añaden siete historiales reales con nombres sustituidos. Se comprueban conciliación del bote, premios y saldos, importación íntegra y coincidencia con el oráculo. Los fixtures son exclusivamente datos para pruebas y no se importan a la base personal automáticamente.

## Límites

No incluye todo árbol multiway posible: siguen pendientes continuaciones después de raises en turn/river, barrels de otros apostadores, sidepots complejos, estadísticas agrupadas por jugador y corrección de múltiples búsquedas. No se estima EV desde las frecuencias ni se infieren cartas ocultas. Las clasificaciones son actuales, no históricas. Las 14 manos sin ciegas nominales verificables siguen en cuarentena.
