# Semántica de datos y oportunidades

## Formato real validado

Los adjuntos contienen un exportador de historiales iPoker en texto (`GAME #…`), no XML: 71 TXT de manos y 4.140 TXT de resumen PokerTracker. Solo se aceptan mesas Twister, NL Hold'em, 2/3 jugadores y buy-in verificable. El stake se obtiene de **buy-in + comisión**; los importes con símbolo € dentro de la mano son fichas de torneo, no ganancias monetarias.

- `Raise (NF)` es el **total en la calle**, excluyendo antes. Call, Bet, Allin y posts son aportaciones incrementales.
- Un Allin puede ser call, subida o una declaración con exceso que nadie puede igualar. Se conserva el importe original y se devuelve el exceso; este último caso no cuenta como raise.
- Ante consume stack y entra en el bote, pero no cuenta como aportación de apuesta preflop. Ciegas cortas y jugadores all-in pagando ante están soportados.
- Los saldos se reconstruyen en **céntimos enteros**. Se comprueban stacks no negativos, orden de acciones, cierre de rondas, mínimo de subida, reapertura, bote tras devoluciones y suma de premios + rake.
- La posición se obtiene de botón y orden de asientos, comprobándola contra los posts. En HU el botón es SB y actúa último postflop. En 3H actúan SB, BB, BTN postflop.
- Las cartas usan rango/palo normalizados. `X` se conserva como `?`. Solo se guardan cartas expresamente repartidas o reveladas; las ausentes permanecen desconocidas. Las cartas no se usan para calcular frecuencias de acciones.
- `Uncalled:N` también está soportado. En headers sin blinds solo se usan posts completos de SB y BB. Nunca se deduce la ciega nominal duplicando SB ni extrapolando otro torneo. Los casos ambiguos quedan en cuarentena.
- Las fechas YYYY-MM-DD y MM-DD-YYYY se normalizan. Se conserva el texto íntegro.

## Persistencia

DuckDB contiene `hands`, `observations`, `summaries`, `imports`, `errors`, `labels`, `documents` y `metadata`. Los originales completos también se archivan en `imports/` junto a la BD, por SHA-256. La importación es transaccional por archivo. Una mano se identifica por red + game ID, independientemente del nombre del archivo. Un mismo ID con contenido diferente se registra como conflicto y no reemplaza el original. Los resúmenes no generan oportunidades.

`rebuild` regenera las observaciones derivadas desde los textos originales en una transacción y mantiene etiquetas y estrategias. Las adiciones de columnas son compatibles con las bases de esta versión en desarrollo. Antes de migrar una base importante, cerrar la app y copiar **la carpeta completa de datos**. La base SQLite del prototipo se conserva por separado; no se migra automáticamente.

## Oportunidades

Una fila por decisión efectivamente registrada, no por jugador sentado. Las manos con reconstrucción inválida no contribuyen parcialmente. No se cuentan acciones automáticas de jugadores all-in ni walks como decisiones. `eligible` conserva las acciones posibles, `can_raise` considera stacks y reapertura, y `check_raise_opportunity` permite filtrar la oportunidad de check-raise sin perder el spot VS_CBET.

Spots preflop: `BTN_FIRST`, `SB_FIRST`, respuestas `*_VS_LIMP`, `*_VS_RAISE`, `*_VS_SHOVE`. El BTN sí puede limpear. Los prefijos contienen la posición del actor. `path` conserva toda la secuencia anterior (calle:posición:resultado), permitiendo separar cold calls, limp/raise, 3bet y respuestas posteriores. No se colapsan las acciones de una misma mano en una primera acción inventada.

Postflop: `CBET` (incluye continuación de la agresión de la calle anterior), `DELAYED_CBET` en turn tras flop sin apuestas, `DONK`, `PROBE` de turn desde fuera de posición tras check-through del agresor preflop, `STAB`, `UNOPENED`, `VS_*`. Seleccionar también **calle** para separar flop, turn y river. No es una taxonomía completa de todas las líneas de póker; usar `path` y revisar manos para spots más específicos.

Stack efectivo: fichas disponibles antes de decidir más lo ya aportado en la calle, excluidos antes y calles anteriores, dividido por BB nominal. En multiway `bb_eff` es el máximo stack contestable con algún rival activo; `bb_eff_min` conserva el mínimo. No se presenta el mínimo de tres stacks como si fuera un enfrentamiento HU. `opponent` es el último agresor, o el único rival si es HU; en spots multiway sin agresor queda vacío.

`facing_bb`: coste de igualar / BB. `facing_pct`: aportación incremental de la última apuesta agresiva / bote antes de esa apuesta. `size_bb`: total propio en la calle / BB; `size_pct`: aportación propia / bote previo. **Filtrar por tamaño propio condiciona al resultado**: usar tamaño enfrentado al investigar fold/call/raise. La textura registra pares, concentración de palos y al menos tres rangos dentro de una ventana de cinco (As puede ser bajo); no es una estimación de equity ni de ventaja de rango.

Hero se excluye por defecto mediante la procedencia `dealt` de cada mano; puede incluirse explícitamente en el Explorer (`include_hero: true` en la API). No se depende de un alias fijo.

Frecuencias: casos / decisiones seleccionadas. IC Wilson 95% binomial. Se muestran jugadores únicos, torneos y peso del jugador más representado. Los IC no corrigen dependencia entre manos ni búsquedas múltiples. No son intervalos de EV. Las matrices de cartas reveladas tienen sesgo de selección, excluyen dealt/hero y ocultan celdas con menos de 20 observaciones; no representan rangos completos.

## Clasificación, referencias y EV

Manual por defecto; reglas automáticas desactivadas hasta que se definen. Las etiquetas manuales prevalecen. Las reglas usan VPIP/PFR sobre **manos con decisión preflop**; no incluyen walks, lo que debe tenerse en cuenta al elegir umbrales. Exigen mínimo 30 y que el IC Wilson completo entre en el intervalo configurado. Reglas incompatibles dejan Sin clasificar. Confianza automática = 1 − anchura del IC: fuerza heurística de evidencia, **no probabilidad calibrada de ser Reg/Fish**. La confianza manual queda vacía, porque no se estima una certeza estadística.

Leak Finder compara una acción/spot seleccionado contra una referencia explícita, con mínimos configurables de oportunidades/jugadores. Solo lista desviaciones cuyo IC excluye la referencia. Son señales exploratorias; no incluyen corrección por búsquedas múltiples ni confirman explotación rentable. No hay referencias GTO predeterminadas.

El modelo EV disponible es solo una apuesta **terminal HU** con fold/call, sin raises y sin apuestas posteriores. Requiere equity cuando pagan suministrada independientemente. EV = f·pot + (1−f)·[equity·(pot+2·bet)−bet]. El intervalo varía solo fold frequency; excluye incertidumbre del modelo/equity. No estima EV general, ICM, rake, multiway ni ganancias en euros.
