# Investigación avanzada 0.6

Se conservan los 79 reportes anteriores y se añaden 59: **138 reportes más el constructor personalizado**.

## Tres jugadores postflop

En SRP puro, la línea multiway con tres jugadores es BTN raise → SB call → BB call. A = BTN, B = SB y C = BB. Un raise después de un limp pertenece a limp/iso y no se incorpora a este catálogo SRP.

Los reportes separan lead de SB, apuesta de BB después de check de SB, cbet BTN después de ambos checks, y las respuestas condicionadas a call, fold o check-raise del jugador anterior. No se asigna a todos los defensores la misma oportunidad ni se cuenta como fold una decisión que nunca ocurrió.

Barrels: se distinguen ambos callers, solo SB continuando y solo BB continuando. El tercer rol permanece vinculado aunque haya foldeado. El formato original continúa siendo 3H. Los checks previos de los defensores en turn/river pueden omitirse si están all-in; las decisiones forzadas de jugadores all-in no se inventan. Las respuestas posteriores de otro defensor requieren calls anteriores expresamente definidos, por lo que no mezclan ramas tras fold/raise.

## River

Se añaden lead, respuesta al lead, stab después de check y respuesta al stab en las cuatro líneas SRP existentes (HU SB/BB y tres líneas 3H). Dos contextos: cbet flop/call y turn check-through, o flop y turn check-through. Todos los prefijos terminan antes de la decisión investigada.

## Validación

`python -m scripts.validate_advanced --db RUTA --output INFORME.json` recorre los importes/acciones originales en solo lectura y evalúa estados por calle. No utiliza los patrones SQL para construir sus oportunidades esperadas.

En los originales de €5, Hero excluido: **59 reportes, 3.384 oportunidades sumadas, cero omitidas, adicionales o resultados distintos**. La suma incluye decisiones distintas de una misma mano, no 3.384 manos independientes. Ejemplos: cbet BTN multiway 188; SB vs cbet 151; BB después de SB call 43 y después de SB fold 71. Turn barrel BTN con ambos callers: nueve oportunidades. River triple barrel con los tres todavía en la mano: cero oportunidades como actor no Hero en esta selección.

El tercer barrel con tres jugadores se prueba positivamente con escenarios sintéticos de fold/call. La ausencia de casos reales no demuestra ninguna frecuencia ni EV. Cinco historiales reales adicionales con nombres sustituidos se incluyen como fixtures, se concilian y se contrastan con el oráculo.

La normalización distingue jugadores vivos sin fichas de jugadores que pueden actuar: un all-in no aporta checks ni folds artificiales. También se conserva un fold sin apuesta enfrentada cuando está explícitamente registrado; no se cambia por check para aparentar un denominador de solo bet/check.

## Límites

Este bloque completa las líneas SRP multiway y river descritas, no todas las secuencias imaginables. Faltan presets específicos para respuestas tras raises posteriores multiway, árboles de sidepots más extensos, limped multiway y otras líneas river después de raises. El constructor permite investigarlas, pero no sustituye su validación. Se mantienen las 14 manos ambiguas en cuarentena y la comprobación externa con el replayer de la sala sigue pendiente. No se declara la Fase 2 íntegramente terminada.
