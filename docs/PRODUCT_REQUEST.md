# SPIN POPULATION LAB — DESARROLLO PROFESIONAL COMPLETO

## INSTRUCCIÓN PRINCIPAL

Quiero que continúes desarrollando mi programa Spin Population Lab, actualmente construido en Python, PySide6 y DuckDB.

Debes trabajar sobre el proyecto existente, no crear uno nuevo.

Mi objetivo es desarrollar una aplicación profesional para Windows, inspirada en las mejores funciones de investigación de Hand2Note 4, especialmente Range Research, Multi-Player Reports, Custom Filters, Smart Reports y navegación interactiva.

**EL PROGRAMA SERÁ EXCLUSIVAMENTE PARA SPINS / SPIN & GO DE 3 JUGADORES Y HEADS-UP.**

No quiero herramientas para cash games, MTT, mesas de 6 jugadores ni mesas de 9 jugadores.

El objetivo principal es analizar tendencias poblacionales, descubrir desviaciones y construir estrategias explotativas contra Regulares y Fishes para mejorar mi chipEV.

No necesito HUD, funciones en tiempo real ni asistencia durante el juego.

El programa debe funcionar offline y utilizar historiales legítimos de mis propias partidas.

---

# 1. FORMATO EXCLUSIVO DE SPINS

Esta restricción es obligatoria y debe aplicarse a toda la aplicación.

## Posiciones permitidas

### Heads-Up (2 jugadores)

- SB / BTN: mismo jugador.
- BB: rival.

### 3-Handed (3 jugadores)

- BTN.
- SB.
- BB.

No crear posiciones UTG, MP, HJ, CO, LJ ni ninguna otra propia de mesas de más jugadores.

En Heads-Up, SB y BTN representan el mismo asiento. Evita duplicar artificialmente esa posición.

Adapta el motor de acciones al orden real de actuación:

- Preflop HU: SB actúa primero.
- Postflop HU: BB actúa primero.
- Preflop 3H: BTN, SB y BB.
- Postflop 3H: SB, BB y BTN, considerando los jugadores que continúan activos.

No asumas que todos los jugadores llegan a cada calle.

## Modalidades

Implementar exclusivamente:

- Spins de 3 jugadores.
- Heads-Up dentro de Spins.

Permitir filtrar un torneo por su estado 3H o HU.

No confundir el formato original del torneo con el número de jugadores activos en una mano.

## Stacks

Permitir filtros libres de stack efectivo y presets:

- 5bb.
- 6bb.
- 8bb.
- 10bb.
- 12bb.
- 15bb.
- 20bb.
- 25bb.

Los presets deben aceptar rangos configurables.

Diferenciar stack inicial, stack efectivo al comienzo de una calle y SPR.

---

# 2. INVESTIGAR HAND2NOTE Y HERRAMIENTAS PROFESIONALES

Antes de realizar cambios importantes, investiga la documentación oficial y referencias públicas de Hand2Note 4.

Funciones prioritarias:

- Range Research.
- Multi-Player Reports.
- Custom Statistics.
- Custom Filters.
- Smart Reports.
- Report Navigation.
- Next Actions.
- Hand Replayer.
- Range Matrix.
- Action Profit.

Consulta también discusiones técnicas de usuarios de Hand2Note, PokerTracker y herramientas MDA en Two Plus Two, Reddit y comunidades especializadas de póker.

Identifica:

1. Qué funciones facilitan realmente el estudio.
2. Qué tipos de filtros utilizan los jugadores avanzados.
3. Qué limitaciones encuentran.
4. Cómo reducir la complejidad.
5. Qué funciones podemos mejorar para Spins.

No copies código propietario, marcas, iconos ni recursos gráficos protegidos.

Crea una implementación independiente inspirada en las capacidades analíticas.

El producto debe ser más sencillo y visual que Hand2Note para investigar Spins.

---

# 3. REDISEÑO VISUAL COMPLETO

La interfaz actual es demasiado básica y parece un programa web antiguo.

Quiero rediseñarla como una aplicación moderna de análisis profesional.

## Estilo

- Tema oscuro premium.
- Fondo grafito o antracita.
- Paneles visualmente separados.
- Acentos azul o turquesa discretos.
- Tipografía moderna y legible.
- Bordes suaves y espaciado consistente.
- Tablas profesionales.
- Iconografía coherente.
- Barras de progreso modernas.
- Gráficos claros.
- Animaciones discretas, solo cuando aporten utilidad.
- Interfaz completamente en español, conservando términos técnicos de póker habituales.

Utiliza PySide6/Qt con componentes propios.

No quiero que parezca una página web antigua ni una interfaz de depuración.

Evita enormes paneles vacíos y bloques de JSON visibles al usuario.

## Resoluciones

Optimizar especialmente para:

- 1440×900.
- 1920×1080.
- 2560×1440.

Todas las pantallas deben funcionar correctamente con escalado de Windows.

## Navegación principal

Quiero estas secciones:

1. Dashboard.
2. Population Explorer.
3. Sequence Explorer.
4. Regs & Fishes.
5. Range Research.
6. Leak Finder.
7. Strategy Builder.
8. Hand Replayer.
9. Mis investigaciones.
10. Importar historiales.
11. Configuración.

Puedes combinar secciones cuando mejore la experiencia.

No añadas menús innecesarios.

## Experiencia de uso

Quiero que sea posible investigar un spot en pocos clics.

Implementa:

- Filtros rápidos.
- Filtros avanzados plegables.
- Búsqueda de estadísticas.
- Favoritos.
- Presets de Spots.
- Historial de navegación.
- Comparación lado a lado.
- Tooltips explicativos.
- Indicadores de tamaño de muestra.
- Estados vacíos informativos.
- Guardado automático de preferencias.

---

# 4. MOTOR DE IMPORTACIÓN Y BASE DE DATOS

Mantener compatibilidad con los historiales TXT de ChampionPoker/iPoker.

Actualmente el proyecto ha importado aproximadamente:

- 70.038 manos.
- 308.439 decisiones.
- 4.140 resúmenes de torneos.

Estos valores son referencias de validación existentes, no deben tratarse como resultados inmutables.

Antes de modificar la base de datos:

- Audita su estructura.
- Comprueba compatibilidad.
- Crea un backup.
- Implementa migraciones versionadas.

Mantener:

- Importación TXT.
- Detección de duplicados.
- Conservación de originales.
- Reconstrucción de acciones.
- Manejo de errores.
- Cuarentena de manos ambiguas.
- Procesamiento eficiente.

No perder los datos importados ni las clasificaciones manuales.

Permitir importación incremental de nuevas manos.

Optimizar DuckDB y las consultas para bases de datos mucho mayores.

---

# 5. CLASIFICACIÓN DE REGULARES Y FISHES

Es una de las funciones más importantes.

## Categorías

### Regulares

- Reg estándar.
- Reg tight.
- Reg loose.
- Reg agresivo.
- Reg pasivo.

### Fishes / Recreacionales

- Fish pasivo.
- Fish agresivo.
- Calling station.
- Fish tight.
- Fish loose.

### Adicional

- Sin clasificar.

## Clasificación

Permitir:

- Clasificación manual.
- Clasificación automática por reglas.
- Umbrales configurables.
- Tamaño mínimo de muestra.
- Confianza de clasificación.
- Inspeccionar las estadísticas utilizadas.
- Corregir una clasificación manualmente.

No utilizar umbrales estándar de cash 6-max sin adaptarlos a Spins.

Separar estadísticas HU y 3H cuando corresponda.

Evitar utilizar información futura para clasificar jugadores en estudios históricos cuando sea posible.

## Contexto del rival

Poder investigar:

- Reg vs Reg.
- Reg vs Fish.
- Fish vs Reg.
- Fish vs Fish.

También comparaciones entre subperfiles.

Diferenciar siempre quién realiza la acción y quién la enfrenta.

No mezclar poblaciones con contextos diferentes sin indicarlo.

---

# 6. POPULATION EXPLORER

Quiero un explorador poblacional muy completo.

Debe permitir filtros por:

- HU / 3H.
- BTN, SB y BB según modalidad.
- Stack efectivo.
- Stake.
- Fecha.
- Reg o Fish.
- Subperfil.
- Clasificación del rival.
- Calle.
- Tipo de bote.
- Acción previa.
- Secuencia de apuestas.
- Tamaños de apuesta.
- Textura del board.
- SPR.
- Número de jugadores activos.
- Jugador concreto.
- Exclusión o inclusión de Hero.

No presentar opciones incompatibles.

Por ejemplo, no mostrar BTN como una tercera posición independiente cuando estamos en HU.

## Resultados

Mostrar:

- Oportunidades.
- Número de acciones.
- Frecuencias.
- Intervalos de confianza.
- Jugadores únicos.
- Tamaño de muestra.
- Desviación frente a referencia.
- Manos que forman la estadística.
- Comparaciones entre poblaciones.

Diferenciar frecuencia condicionada de frecuencia de llegada a un spot.

No mostrar únicamente estadísticas generales mezcladas.

---

# 7. SEQUENCE EXPLORER

Quiero uno de los módulos más potentes de Hand2Note, pero más intuitivo.

Implementar un árbol visual de decisiones.

Ejemplo:

HU → Limped Pot → Bet Flop → Fish Call → Bet Turn → Fish Call → Bet River → Fish Fold.

Poder navegar haciendo clic en:

- Fold.
- Check.
- Call.
- Bet.
- Raise.
- Shove.

Cada nodo debe mostrar:

- Frecuencia de acción.
- Oportunidades.
- Frecuencia de llegada.
- Distribución de tamaños.
- Stack efectivo.
- SPR.
- Categoría de jugador.
- Contexto del rival.
- Siguiente acción.
- Manos originales.

Conservar todos los filtros al avanzar.

Permitir retroceder, comparar ramas y guardar secuencias.

La identidad de cada jugador debe mantenerse en todas las calles.

## Constructor visual

Debe ser posible crear cualquier secuencia utilizando controles gráficos.

El usuario no debería necesitar escribir códigos internos ni SQL.

Representar la secuencia de forma clara, indicando en cada acción quién apuesta y quién responde.

Permitir condiciones opcionales y excluyentes.

---

# 8. TIPOS DE BOTES

Detectar correctamente:

- Unraised pot.
- Limped pot.
- Single Raised Pot.
- Limp/iso-raised pot.
- 3bet pot.
- 4bet pot cuando sea posible.
- Multiway pot.
- Heads-up pot.
- Preflop all-in.

Distinguir limpiamente un limped pot puro de un limp/raise.

No llamar Cbet a una apuesta en un bote limpeado.

Registrar quién tuvo la iniciativa preflop y quién realizó cada apuesta postflop.

---

# 9. ESTADÍSTICAS PREFLOP PARA SPINS

## HU

- SB limp.
- SB minraise.
- SB open raise.
- SB open shove.
- SB limp/fold.
- SB limp/call.
- SB limp/raise.
- BB check vs limp.
- BB iso-raise vs limp.
- BB shove vs limp.
- BB fold vs raise.
- BB call vs raise.
- BB 3bet vs raise.
- BB shove vs raise.
- SB fold vs 3bet.
- SB call vs shove.
- Rangos observados por stack.

## 3H

### BTN

- Open raise.
- Open shove.
- Open fold.
- Limp si es legal en el spot.
- Call vs 3bet.
- Fold vs 3bet.

### SB

- Acciones después de BTN fold.
- Limp.
- Raise.
- Shove.
- Call.
- Defensa ante aperturas de BTN.

### BB

- Defensa vs BTN.
- Defensa vs SB.
- Check vs limp.
- Iso-raise.
- Call.
- 3bet.
- Squeeze cuando corresponda.
- Shove.

Todas las estadísticas deben usar oportunidades correctas.

No incluir spots imposibles según el orden de actuación.

---

# 10. ESTADÍSTICAS POSTFLOP

Implementar para HU y 3H:

- Bet flop en limped pot.
- Cbet flop en SRP.
- Fold vs flop bet.
- Fold vs flop cbet.
- Check-raise.
- Donk bet.
- Probe bet.
- Delayed cbet.
- Second barrel.
- Fold vs second barrel.
- Third barrel.
- Fold vs third barrel.
- Bet/fold.
- Bet/call.
- Raise vs bet.
- Fold vs raise.
- Check/fold.
- Check/call.
- Overbet.
- River bluffcatch.
- River fold vs diferentes tamaños.
- Bet después de missed cbet.
- Turn stab.
- River stab.

Desglosar por tamaños, posiciones, stacks, tipos de bote y textura.

---

# 11. SPOT PRIORITARIO: FISH FOLD VS 3-BARREL EN LIMPED POT

Esta funcionalidad debe implementarse y verificarse rigurosamente.

Quiero investigar:

¿Cuánto foldean los Fishes cuando enfrentan un tercer barrel en river en un bote limpeado HU?

Secuencia:

1. Preflop: SB limpea y BB pasa.
2. Flop: jugador A apuesta, Fish B paga.
3. Turn: el mismo jugador A vuelve a apostar, Fish B paga.
4. River: jugador A realiza una tercera apuesta.
5. Fish B enfrenta la apuesta y puede foldear, pagar o subir.

El Fish debe ser el defensor de la secuencia, no necesariamente el jugador que apuesta.

La identidad del agresor y del defensor debe mantenerse entre calles.

## Denominador

Todas las oportunidades válidas en las que el Fish enfrenta el tercer barrel en river cumpliendo las condiciones anteriores.

## Numerador

Las oportunidades en las que ese Fish foldea.

Mostrar:

- Fold%.
- Call%.
- Raise%.
- Oportunidades.
- Jugadores únicos.
- Intervalos de confianza.
- Tamaños de apuesta.
- Posición del defensor.
- Stack efectivo.
- Textura del board.
- Comparación Reg vs Fish.
- Manos originales.

Excluir manos ambiguas e imposibles de reconstruir.

Probar el resultado manualmente con muestras de historiales.

Esta misma arquitectura debe servir para estudiar otras secuencias arbitrarias.

---

# 12. RANGE RESEARCH

Implementar matrices preflop 13×13.

Mostrar por combinación:

- Frecuencia observada.
- Número de casos.
- Acciones.
- Frecuencias por acción.
- Tamaños utilizados.
- Comparación Reg vs Fish.
- Comparación por stack.

Permitir hacer clic sobre una combinación para consultar las manos.

## Postflop

Agrupar manos conocidas por:

- High card.
- Pair.
- Top pair.
- Middle pair.
- Bottom pair.
- Two pair.
- Sets.
- Straights.
- Flushes.
- Draws.
- Combo draws.
- Air.

Permitir investigar cómo juega cada población con distintos tipos de manos.

No inventar cartas ocultas.

Distinguir siempre rangos observados en cartas conocidas y estimaciones inferidas.

Advertir sobre sesgos de showdown y selección de muestra.

---

# 13. SMART REPORTS

Crear informes inteligentes que se adapten al spot.

Ejemplo:

Al analizar Bet Flop, mostrar automáticamente:

- Fold del rival.
- Call.
- Raise.
- Continuación del agresor.
- Second barrel.
- Fold vs second barrel.
- Third barrel.
- Fold vs third barrel.

Las estadísticas deben poder abrirse haciendo clic.

Implementar navegación interactiva sin obligar al usuario a reconstruir todos los filtros.

## Presets de investigación

Crear reportes preconfigurados:

- HU SB limp/raise/shove por stack.
- BB vs limp.
- BB vs minraise.
- Fold vs 3bet.
- Limp/fold.
- Limp/call.
- Flop bet en limped pot.
- Second barrel.
- Third barrel.
- Fold vs third barrel.
- River overbet.
- River bluffcatch.
- Check-raise por board.
- Comparación Reg vs Fish.

Permitir guardar nuevos presets.

---

# 14. COMPARACIÓN DE POBLACIONES

Crear una vista de comparación lado a lado.

Ejemplos:

- Reg vs Fish.
- Reg vs Reg.
- Fish vs Reg.
- Calling station vs Fish pasivo.
- 10bb vs 15bb.
- SB vs BB.
- €5 vs €10.
- Primer período vs segundo período.

Mostrar:

- Frecuencia A.
- Frecuencia B.
- Diferencia en puntos porcentuales.
- Oportunidades por grupo.
- Intervalos de confianza.
- Advertencias de muestras reducidas.

Permitir abrir las manos detrás de cada estadística.

---

# 15. ESTADÍSTICAS PERSONALIZADAS

Implementar un constructor visual.

Cada estadística debe contener:

- Nombre.
- Descripción.
- Oportunidad exacta.
- Numerador.
- Denominador.
- Filtros.
- Secuencia.
- Categoría del actor.
- Categoría del rival.
- Condiciones del board.
- Condiciones del stack.

Debe mostrar una descripción en lenguaje natural de qué mide exactamente.

Permitir guardar, editar, duplicar y exportar.

No exigir programación ni SQL.

---

# 16. LEAK FINDER

Quiero que el programa detecte posibles tendencias explotables.

Ejemplos:

- Regs que foldean demasiado BB vs minraise.
- Fishes que pagan demasiado las cbets.
- Regs que abandonan frente a overbets.
- Fishes que hacen poco bluff en river.
- Poblaciones que foldean demasiado frente a third barrel.

El sistema debe comparar las frecuencias con referencias apropiadas.

## Prioridades

Ordenar las desviaciones utilizando:

- Frecuencia del spot.
- Tamaño de muestra.
- Magnitud de desviación.
- Confianza estadística.
- Número de jugadores independientes.
- Impacto potencial.
- Calidad de la referencia.

No etiquetar una acción como error únicamente porque tiene una frecuencia alta o baja.

Distinguir:

1. Tendencia observada.
2. Desviación respecto a referencia.
3. Hipótesis explotativa.
4. Ajuste evaluado mediante EV.

No declarar que una explotación es rentable sin un modelo suficiente.

---

# 17. STRATEGY BUILDER

Quiero transformar investigaciones en estrategias de estudio.

Cada estrategia debe guardar:

- Spot.
- Reg o Fish.
- Subperfil.
- Stack.
- Posiciones.
- Contexto.
- Frecuencia observada.
- Muestra.
- Referencia.
- Desviación.
- Ajuste propuesto.
- Hipótesis de EV.
- Manos relevantes.
- Limitaciones.
- Fecha.

Crear estados:

- En investigación.
- Hipótesis.
- Frecuencia validada.
- EV evaluado.
- Descartado.

Permitir organizar estrategias preflop y postflop.

Guardar versiones y notas.

El programa debe utilizarse exclusivamente para estudio fuera de las mesas.

---

# 18. HAND REPLAYER

Crear un replayer visual para Spins.

Mostrar:

- Mesa de 2 o 3 jugadores.
- BTN, SB y BB según corresponda.
- Cartas conocidas.
- Board.
- Stacks.
- Bote.
- Apuestas.
- Acciones por orden.
- Calle.
- Tamaños en BB y porcentaje del bote.

Permitir navegar acción por acción.

Desde cualquier estadística, abrir las manos concretas que la componen.

Permitir volver inmediatamente al reporte.

No mostrar cartas ocultas como conocidas.

---

# 19. SISTEMA DE ESTUDIO

Crear un Study Dashboard.

Secciones:

- Investigaciones recientes.
- Spots favoritos.
- Tendencias importantes.
- Comparaciones Reg vs Fish.
- Posibles leaks.
- Hipótesis pendientes.
- Estrategias guardadas.
- Manos marcadas.

Permitir guardar investigaciones para revisarlas posteriormente.

Crear una biblioteca personal de estrategias explotativas por stack, posición y población.

---

# 20. FIABILIDAD ESTADÍSTICA

Es extremadamente importante.

Mostrar siempre:

- Numerador.
- Denominador.
- Intervalo de confianza.
- Número de jugadores.
- Distribución de contribuciones.
- Advertencias de baja muestra.

Implementar:

- Estadísticas ponderadas por decisión.
- Estadísticas ponderadas por jugador.
- Comparación por períodos.
- Advertencias de comparaciones múltiples.
- Control de sesgos de selección.
- Exclusión de manos no verificables.
- Seguimiento de cambios en clasificación.

No confundir diferencias estadísticas con ganancias de EV demostradas.

En estudios muy específicos, permitir ampliar rangos de stack o agrupar tamaños para obtener más muestra, indicando siempre el cambio de filtros.

---

# 21. RENDIMIENTO Y SEGURIDAD

Quiero que sea rápido incluso con millones de manos.

Implementar:

- Consultas optimizadas.
- Índices o estructuras auxiliares cuando aporten beneficio.
- Caché de consultas frecuentes.
- Procesamiento en segundo plano mediante workers.
- UI sin bloqueos.
- Importación incremental.
- Progreso real.
- Cancelación segura de operaciones.
- Backups automáticos.
- Restauración de datos.
- Logs de errores.

No sacrificar precisión por velocidad.

Mantener el funcionamiento completamente offline.

---

# 22. TESTS Y VALIDACIÓN

Antes de declarar terminada cualquier estadística:

1. Verificar el parser contra historiales reales.
2. Validar reconstrucción de posiciones HU/3H.
3. Confirmar el orden de acciones.
4. Confirmar stacks y tamaños.
5. Comprobar que los denominadores representan oportunidades reales.
6. Probar secuencias complejas.
7. Probar all-ins.
8. Probar raises y check-raises.
9. Probar limp pots.
10. Probar second y third barrel.
11. Comparar muestras contra replays manuales.
12. Confirmar que los filtros conservan las condiciones correctamente.
13. Verificar que una actualización no modifica estadísticas existentes sin justificación.

Crear pruebas unitarias, de integración y regresión.

Documentar los casos ambiguos.

No inventar estadísticas ausentes.

---

# 23. EJECUTABLE PARA WINDOWS

El objetivo final es disponer de una aplicación que pueda utilizar sin abrir Python ni ejecutar comandos manuales.

Preparar:

- Ejecutable Windows.
- Instalador Windows.
- Acceso directo en el escritorio.
- Carpeta de datos persistente.
- Base de datos protegida ante actualizaciones.
- Sistema de actualización compatible con versiones posteriores.

Utilizar PyInstaller y, si conviene, Inno Setup.

No afirmar que el instalador está probado si no se ha ejecutado y verificado en Windows.

---

# 24. ORDEN DE DESARROLLO

Trabaja por fases.

### Fase 1 — Auditoría y motor de investigación

- Revisar el código actual.
- Comprobar los datos.
- Corregir errores.
- Implementar un motor de secuencias fiable.
- Crear tests.

### Fase 2 — Investigación avanzada

- Limped pots.
- Second barrel.
- Third barrel.
- Fold vs third barrel.
- Reg vs Fish según contexto.
- Reportes preconfigurados.

### Fase 3 — Rediseño visual

- Modernizar PySide6.
- Rediseñar Population Explorer.
- Crear filtros más intuitivos.
- Implementar Sequence Explorer.

### Fase 4 — Range Research y comparación

- Matrices 13×13.
- Comparaciones poblacionales.
- Estadísticas personalizadas.
- Smart Reports.

### Fase 5 — Estrategias explotativas

- Leak Finder avanzado.
- Strategy Builder.
- Study Dashboard.
- Replayer integrado.

### Fase 6 — Finalización

- Rendimiento.
- Backups.
- Pruebas.
- Instalador Windows.
- Documentación.

## INSTRUCCIONES DE EJECUCIÓN

No te limites a escribir un plan.

Comienza examinando el código existente, identificando sus limitaciones y desarrollando la Fase 1.

Continúa con las siguientes fases de forma incremental, siempre que las pruebas lo permitan.

Evita reescribir grandes partes del proyecto sin necesidad.

No elimines funcionalidades existentes.

No rompas la compatibilidad con los historiales ya importados.

Cuando haya una decisión de diseño importante, elige la solución que aporte mayor precisión, flexibilidad, rendimiento y facilidad de uso para Spins.

Entrega código funcional, pruebas y documentación.

Si una fase no está completa, indícalo expresamente.

Quiero que Spin Population Lab llegue a ser una herramienta profesional de investigación poblacional especializada en Spins, comparable en profundidad analítica a Hand2Note Range Research, pero con una interfaz más moderna, fácil de usar y orientada a descubrir estrategias explotativas contra Regs y Fishes.