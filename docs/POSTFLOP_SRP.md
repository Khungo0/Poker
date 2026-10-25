# Reportes SRP · iteración 0.5

Se añaden 52 reportes a los 27 existentes (79 en total, más el constructor). A representa al raiser preflop, B al único caller y C al tercero que foldeó. Los roles y filtros de población se conservan entre calles.

Cobertura explícita:

- HU: SB raise → BB call, agresor en posición.
- 3H: BTN raise → SB fold → BB call; BTN raise → SB call → BB fold.
- 3H: BTN fold → SB raise → BB call, agresor fuera de posición.

Cada línea ofrece cbet flop, respuesta a cbet, respuesta del apostador al raise, delayed cbet, segundo y tercer barrel y sus respuestas. Con agresor IP se añaden donk y probe del caller OOP; con agresor OOP se añaden stabs del caller IP tras missed cbet y tras check-through. Las manos de tres asientos siguen siendo 3H cuando el tercero foldea.

Las oportunidades de apostar incluyen bet/check. Las respuestas incluyen fold/call/raise (check-raises agrupados como raise), incluso calls all-in. El prefijo termina antes del resultado: no se selecciona únicamente a quienes terminaron apostando o foldeando. Un donk excluye la cbet de esa calle y una subida rompe la cadena de barrels. Limp/iso, 3bets y botes con tres jugadores postflop no se mezclan en estos reportes.

## Verificación

El verificador `python -m scripts.validate_postflop --db RUTA --output INFORME.json` abre la base en solo lectura y construye oportunidades mediante una máquina de estados sobre acciones originales, independientemente de los patrones SQL y las etiquetas de spots.

En la muestra real de €5, Hero excluido: **52 reportes, 17.315 oportunidades sumadas, cero omitidas, adicionales o resultados distintos**. La suma incluye distintos nodos de una misma mano y no significa 17.315 manos independientes. No se han asignado categorías Reg/Fish para producir estos números.

Se conservan 36 manos completas con nombres sustituidos en `tests/fixtures/srp_real_anonymized.txt`, seleccionadas de las oportunidades reales del catálogo. Se comprueba su conciliación de fichas, se contrastan ambos fixtures SRP con el oráculo y se prueban las cuatro líneas con fold/call/raise como denominador común. Ejemplo revisado: mano 12543201521, BTN raise a 80, SB fold y BB call: bote 170. BB check, BTN bet 170 y BB fold; tamaño enfrentado 100%, bote antes de decidir 340.

El spot prioritario HU limped third barrel vuelve a coincidir con el oráculo independiente: **196 oportunidades, 100 fold, 88 call, 8 raise**. Las etiquetas Fish siguen dependiendo de clasificaciones aportadas por el usuario.

## Corrección de all-ins y datos

Se detectaron nueve decisiones en la base original en las que un all-in/raise-to que abría una calle postflop se había etiquetado como raise. Ahora se normaliza como bet; conserva su indicador all-in y los importes originales. Las nueve se verificaron contra el backup: cero raises restantes sin apuesta enfrentada.

El esquema sigue siendo 2 y la versión de análisis sube a 3. La apertura de un análisis anterior crea backup verificado y recalcula en una transacción con progreso/cancelación. No requiere reimportar los originales. En esta base se mantienen 70.038 manos, 308.439 decisiones, 4.140 resúmenes y 14 manos en cuarentena.

Los informes incorporan frecuencias e IC Wilson condicionados por textura y tamaño de la apuesta enfrentada (sin apuesta, hasta 33%, hasta 50%, hasta 75%, hasta 100%, overbet). Cada grupo tiene su denominador; no se utilizan tamaños futuros. Los intervalos siguen siendo exploratorios, sin dependencia agrupada ni corrección por múltiples búsquedas.

## Alcance pendiente de Fase 2

El bloque SRP con dos jugadores postflop, los barrels limped prioritarios y los desgloses están implementados y contrastados. La fase completa sigue pendiente: SRP multiway con tres jugadores en el flop, catálogo river stab/bet después de otras líneas missed cbet, combinaciones avanzadas de tamaños y validación externa con el replayer de la sala. El constructor conserva secuencias arbitrarias, pero su existencia no equivale a tener todo ese catálogo verificado.
