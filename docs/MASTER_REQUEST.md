# SPIN POPULATION LAB — MASTER DEVELOPMENT PROMPT
## Plataforma profesional de tendencias poblacionales y estrategias explotativas para Spins

# 1. OBJETIVO PRINCIPAL

Quiero que continúes desarrollando mi proyecto **Spin Population Lab**, una aplicación de escritorio para Windows construida con Python, PySide6 y DuckDB.

El objetivo es convertirla en una herramienta profesional para investigar tendencias poblacionales, detectar patrones explotables y construir estrategias contra Regulares y Fishes.

Quiero incorporar las mejores ideas de investigación de Hand2Note Range Research y del software ORACLE de NerdSide, utilizando una implementación propia.

**El proyecto se centrará exclusivamente en tendencias reales de jugadores, análisis de historiales y estrategias explotativas.**

No desarrolles funciones de comparación con estrategias teóricas ni integraciones con solvers en esta etapa. Las funciones anteriores que dependan de referencias externas pueden conservarse sin seguir ampliándolas.

No quiero que elimines las funcionalidades que ya tenemos.

## Estado del proyecto

Trabaja sobre la última versión del repositorio de GitHub.

La última versión que he recibido tenía:

- 180 reportes poblacionales.
- 162 pruebas automáticas.
- 70.038 manos de ChampionPoker/iPoker.
- 308.439 decisiones reconstruidas.
- Importación TXT y base de datos DuckDB.
- Population Explorer y Sequence Explorer.
- Clasificación manual y automática básica.
- Comparación Reg/Fish.
- Leak Finder.
- Strategy Builder.
- Replayer.

Verifica el estado real del repositorio antes de modificarlo.

No reconstruyas el proyecto desde cero, no dupliques funcionalidades y no elimines información almacenada.

# 2. RESTRICCIÓN ABSOLUTA: SOLO SPINS

El programa será exclusivamente para Spins de tres jugadores y Heads-Up.

## Heads-Up

Únicamente:

- SB/BTN.
- BB.

## 3-handed

Únicamente:

- BTN.
- SB.
- BB.

No implementar posiciones de cash 6-max, 9-max, MTT u otras modalidades.

La estructura del programa, sus filtros, estadísticas, rangos y replayer deben adaptarse exclusivamente a estas posiciones.

Respetar el orden real de actuación en cada calle.

Diferenciar el formato del torneo y el número de jugadores activos en una mano.

El programa será exclusivamente para estudio offline.

No necesito HUD, superposiciones en mesas ni asistencia durante las partidas.

# 3. AUDITORÍA INICIAL

Antes de desarrollar:

1. Examina la arquitectura existente.
2. Revisa el importador de ChampionPoker.
3. Comprueba la reconstrucción preflop y postflop.
4. Audita los denominadores de estadísticas.
5. Revisa el esquema DuckDB.
6. Comprueba los reportes existentes.
7. Revisa el clasificador Reg/Fish.
8. Identifica los problemas de interfaz.
9. Revisa Population Explorer y Sequence Explorer.
10. Identifica los módulos incompletos.

Conserva todas las estadísticas anteriores que estén bien implementadas.

Crea pruebas de regresión antes de modificar componentes críticos.

Realiza backups antes de migraciones de bases de datos.

# 4. REDISEÑO VISUAL PROFESIONAL

Esta es una de mis mayores prioridades.

La interfaz actual sigue pareciendo un programa antiguo. Hay demasiados espacios vacíos, texto pequeño, tablas poco atractivas y filtros difíciles de interpretar.

Quiero un rediseño integral, no simplemente cambiar colores.

## Estética

Crear una aplicación moderna, elegante y profesional, similar en calidad visual a herramientas actuales de análisis de datos.

Características:

- Tema oscuro grafito o antracita.
- Contraste adecuado entre fondo y paneles.
- Acentos discretos en azul o turquesa.
- Tipografía moderna y legible.
- Jerarquía visual clara.
- Iconos consistentes.
- Paneles con separación equilibrada.
- Bordes suavemente redondeados.
- Barras visuales de frecuencia.
- Gráficos modernos.
- Tablas con formato profesional.
- Indicadores de confianza y muestras.
- Estados de carga bien diseñados.
- Tooltips explicativos.
- Mensajes de error comprensibles.
- Transiciones discretas cuando aporten utilidad.

Evita las interfaces que parezcan páginas web antiguas.

No quiero controles diminutos ni enormes paneles vacíos.

## Resoluciones

Optimizar especialmente para:

- 1440×900.
- 1920×1080.
- 2560×1440.

La principal referencia será 1440×900.

Comprobar que no se corten controles ni aparezcan desbordamientos.

## Navegación

Reorganizar las pantallas en:

1. Dashboard.
2. Population Explorer.
3. Sequence Explorer.
4. Regs & Fishes.
5. Range Research.
6. Population Comparison / Dual Mode.
7. Leak Finder.
8. Strategy Builder.
9. Replayer.
10. Mis investigaciones.
11. Importar historiales.
12. Configuración.

Combinar pantallas cuando mejore la experiencia de uso.

No añadir secciones innecesarias.

## Dashboard

El Dashboard debe resultar útil desde el primer momento.

Mostrar:

- Manos importadas.
- Decisiones registradas.
- Jugadores clasificados.
- Investigaciones guardadas.
- Spots favoritos.
- Últimas investigaciones.
- Accesos rápidos a spots frecuentes.
- Comparaciones Reg/Fish.
- Estado de la base de datos.
- Alertas sobre muestras insuficientes.

Cuando no haya estrategias guardadas, mostrar acciones para comenzar a investigar, no dos grandes paneles vacíos.

## Exploradores

Diseñar una estructura con:

- Encabezado claro.
- Filtros rápidos superiores.
- Filtros avanzados plegables.
- Área central de resultados.
- Frecuencias visuales.
- Pestañas de acciones, rangos, comparación y manos.
- Acceso inmediato al replayer.
- Botones de guardar investigaciones.

## Tablas

Implementar:

- Búsqueda.
- Ordenamiento.
- Paginación o virtualización.
- Columnas ajustables.
- Números alineados.
- Frecuencias con barras visuales.
- Diferencias en puntos porcentuales.
- Indicadores de tamaño de muestra.
- Exportaciones.

No renderizar miles de filas simultáneamente si eso afecta el rendimiento.

# 5. CLASIFICACIÓN REG/FISH AVANZADA PARA SPINS

Actualmente solo tenemos VPIP y PFR como métricas de clasificación.

Quiero un sistema mucho más completo y fiable.

Investiga las mejores prácticas de Hand2Note y comunidades especializadas en Spins para identificar patrones útiles, sin asumir que existe una regla universal para distinguir jugadores ganadores de recreacionales.

## Métricas preflop

Implementar:

- VPIP.
- PFR.
- Diferencia VPIP-PFR.
- Manos observadas.
- Torneos distintos.
- Días de actividad.
- Frecuencia de limp HU.
- Open raise HU.
- Open shove.
- Limp/fold.
- Limp/call.
- Limp/raise.
- BB iso-raise vs limp.
- Fold BB vs minraise.
- Call BB vs minraise.
- 3bet.
- 3bet shove.
- Call vs shove.
- Defensa de BB.
- Frecuencias por stack efectivo.

## Métricas postflop

Implementar:

- Bet flop en limped pot.
- Cbet flop en raised pot.
- Fold vs cbet.
- Check-raise.
- Probe bet.
- Second barrel.
- Third barrel.
- Fold vs second barrel.
- Fold vs third barrel.
- Agresión flop.
- Agresión turn.
- Agresión river.
- WTSD.
- WWSF.
- W$SD, si puede medirse correctamente.

Cada estadística debe utilizar oportunidades reales como denominador.

Mostrar tamaño de muestra y contexto.

Distinguir HU y 3-handed.

## Clasificaciones

Mantener:

- Reg.
- Fish.
- Sin clasificar.

No clasificar automáticamente a todos los jugadores no identificados como Reg como Fishes.

## Perfiles de Reg

- Reg estándar.
- Reg tight.
- Reg loose.
- Reg agresivo.
- Reg pasivo.

## Perfiles de Fish

- Fish pasivo.
- Fish agresivo.
- Calling station.
- Fish tight.
- Fish loose.

Los perfiles deben depender de comportamientos observados y criterios editables.

## Clasificador multivariable

Desarrollar reglas que puedan combinar:

- Volumen.
- Recurrencia.
- Preflop.
- Postflop.
- HU/3H.
- Stack.
- Contexto del rival.

Permitir reglas AND/OR.

Incluir puntuaciones configurables, sin presentar valores arbitrarios como probabilidades calibradas.

Las etiquetas manuales deben tener prioridad absoluta.

## Previsualización

Antes de aplicar una clasificación:

- Mostrar los jugadores afectados.
- Mostrar estadísticas utilizadas.
- Mostrar tamaño de muestra.
- Mostrar reglas activadas.
- Mostrar conflictos.
- Mostrar evidencia insuficiente.
- Permitir cancelar.
- Permitir rollback.

No reemplazar etiquetas manuales mediante reglas automáticas.

## Poblaciones personalizadas

Permitir definir grupos por comportamiento, sin tener que asignarles permanentemente una etiqueta Reg/Fish.

Ejemplos:

- Jugadores con alta frecuencia de limp.
- Jugadores que foldean mucho BB.
- Jugadores con agresividad river baja.
- Jugadores que pagan excesivamente en flop.
- Jugadores con alta frecuencia de limp/fold.

Guardar estos grupos para utilizarlos en todos los exploradores.

## Contexto del rival

Separar:

- Reg vs Reg.
- Reg vs Fish.
- Fish vs Reg.
- Fish vs Fish.

Permitir seleccionar subperfiles.

Distinguir actor y defensor durante toda la mano.

# 6. POPULATION EXPLORER AVANZADO

Quiero investigar cualquier tendencia poblacional válida en Spins.

Filtros:

- HU o 3H.
- Posiciones válidas.
- Stake.
- Stack efectivo.
- Fecha.
- Actor.
- Rival directo.
- Reg/Fish.
- Subperfil.
- Población personalizada.
- Calle.
- Acción.
- Acción anterior.
- Tipo de bote.
- Tamaño de apuesta.
- SPR.
- Textura del board.
- Secuencia completa.
- Número de jugadores activos.

No mostrar filtros imposibles para la modalidad elegida.

## Resultados

Mostrar:

- Oportunidades.
- Numerador.
- Denominador.
- Frecuencia.
- Intervalo de confianza.
- Jugadores únicos.
- Distribución de contribuciones por jugador.
- Distribución de tamaños.
- Comparaciones entre poblaciones.
- Manos originales.

Diferenciar frecuencia condicionada y frecuencia de llegada a un nodo.

Evitar mezclar spots incompatibles.

# 7. SEQUENCE EXPLORER UNIVERSAL

Actualmente existen muchos reportes predefinidos.

Quiero poder construir secuencias arbitrarias válidas, sin depender de solicitar reportes nuevos.

## Constructor visual

Ejemplo:

HU → SB Limp → BB Check → Flop Bet → Call → Turn Bet → Call → River Bet → Fold.

Permitir crear la secuencia seleccionando nodos visuales.

Cada nodo debe indicar:

- Calle.
- Actor.
- Posición.
- Acción.
- Tamaño.
- Rival.
- Stack.
- SPR.
- Tipo de bote.

Mantener identidad de jugadores en toda la secuencia.

Soportar decisiones condicionales y ramas alternativas.

## Navegación interactiva

Al hacer clic en una acción:

- Abrir la rama correspondiente.
- Conservar los filtros.
- Mostrar frecuencia.
- Mostrar oportunidades.
- Mostrar siguiente decisión.
- Mostrar distribución de tamaños.
- Permitir retroceder.
- Mostrar manos originales.
- Abrir replayer.

Conservar los reportes existentes como presets.

El nuevo constructor debe utilizar un motor general de consultas.

# 8. DUAL MODE INSPIRADO EN ORACLE

Implementar una vista donde pueda analizarse simultáneamente el comportamiento de dos jugadores o poblaciones.

## Panel izquierdo

Jugador A o población A.

## Panel derecho

Jugador B o población B.

Mostrar:

- Frecuencias de acciones.
- Respuestas del rival.
- Rangos observados cuando haya cartas disponibles.
- Distribuciones de tamaños.
- Stack.
- Posición.
- Tamaños de muestra.

Ejemplo:

HU SB Limp → BB Check / Iso-raise / Shove.

El panel de SB debe mostrar cómo juega SB y el de BB cómo responde BB.

Permitir comparar:

- Reg vs Reg.
- Reg vs Fish.
- Fish vs Reg.
- Fish vs Fish.

Sincronizar los paneles al navegar por el árbol.

No inventar EV cuando no pueda calcularse.

# 9. RANGE RESEARCH POBLACIONAL

Implementar matrices preflop 13×13 modernas e interactivas.

Permitir:

- Seleccionar manos individuales.
- Seleccionar grupos de manos.
- Filtrar pares, suited, offsuit, Ax, Kx y conectores.
- Comparar Reg y Fish.
- Comparar stacks.
- Filtrar acciones.
- Examinar las manos que forman cada frecuencia.

## Rangos postflop

Cuando se conocen las cartas, agrupar por:

- High card.
- Top pair.
- Middle pair.
- Bottom pair.
- Overpair.
- Two pair.
- Set.
- Straight.
- Flush.
- Draw.
- Combo draw.
- Air.
- Bluffcatcher.
- Value.

Definir las categorías de forma reproducible.

## Blockers

Añadir filtros por blockers cuando se conocen las cartas.

## Showdown bias

Mostrar advertencias claras sobre el sesgo de selección de cartas conocidas.

Los rangos basados únicamente en showdowns no deben presentarse como rangos completos de la población.

En el futuro puede incorporarse un modelo de estimación de rangos ocultos, pero no debe bloquear el desarrollo de los demás módulos.

No utilizar estimaciones como si fueran cartas observadas.

# 10. ANÁLISIS POSTFLOP COMPLETO

Completar los spots pendientes en:

- Limped pot HU.
- Limped pot 3H.
- Single Raised Pot HU.
- Single Raised Pot 3H.
- 3bet pots.
- Multiway.
- Second barrel.
- Third barrel.
- Check-raise.
- Reraise.
- Donk.
- Probe.
- Delayed cbet.
- River lead.
- River stab.
- Overbet.
- Check-through.
- Bet después de missed cbet.
- Continuaciones tras raises de turn/river.
- Sidepots cuando puedan reconstruirse con precisión.

Respetar todas las secuencias reales.

No llamar cbet a una apuesta en bote limpeado.

## Board Filters

Implementar:

- A-high.
- K-high.
- Paired.
- Unpaired.
- Monotone.
- Two-tone.
- Rainbow.
- Seco.
- Coordinado.
- Conectado.
- Cambio de textura turn.
- Flush completado.
- Straight completada.
- Overcard turn/river.

Definir técnicamente cada filtro.

## Bet Size Filters

Permitir categorías configurables:

- Hasta 33% pot.
- 34–50%.
- 51–75%.
- 76–100%.
- Overbet mayor de 100%.

Permitir introducir cualquier intervalo.

Mantener los tamaños reales para análisis precisos.

# 11. CASO PRIORITARIO: FISH FOLD VS THIRD BARREL EN LIMPED POT

Quiero poder investigar exactamente:

¿Cuánto foldean los Fishes frente al tercer barrel en river en limped pots HU?

Secuencia:

1. SB limpea.
2. BB pasa.
3. Jugador A apuesta flop.
4. Fish B paga.
5. Jugador A apuesta turn.
6. Fish B paga.
7. Jugador A apuesta river.
8. Fish B enfrenta esa tercera apuesta.

Medir:

- Fold.
- Call.
- Raise.

El denominador debe contar únicamente las oportunidades válidas en river.

Mostrar:

- Frecuencias.
- Oportunidades.
- Jugadores.
- Tamaños.
- Stack.
- Posición.
- Textura.
- Comparación Reg/Fish.
- Manos concretas.

Permitir modificar cualquiera de los filtros y reutilizar la misma secuencia.

Validar manualmente varias manos contra los historiales originales.

# 12. SMART REPORTS Y ESTADÍSTICAS PERSONALIZADAS

Al investigar una acción, mostrar automáticamente estadísticas relacionadas.

Ejemplo:

Fold vs Flop Bet → Call → Second Barrel → Third Barrel.

Permitir navegar a cualquier nodo sin configurar otra consulta desde cero.

## Constructor de estadísticas

Permitir definir:

- Oportunidad.
- Numerador.
- Denominador.
- Modalidad.
- Posición.
- Stack.
- Calle.
- Acción.
- Secuencia.
- Rival.
- Board.
- Tamaño.
- Tipo de bote.

Crear una descripción en lenguaje natural de la estadística.

Permitir guardar, editar, duplicar y exportar.

No exigir conocimientos de SQL.

# 13. COMPARACIÓN DE POBLACIONES

Crear un comparador avanzado.

Permitir:

- Reg vs Fish.
- Reg vs Reg.
- Fish pasivo vs Fish agresivo.
- Calling station vs Reg.
- 10bb vs 15bb.
- HU vs 3H cuando el spot sea comparable.
- Diferentes stakes.
- Diferentes fechas.
- Diferentes tamaños.

Mostrar:

- Frecuencia A.
- Frecuencia B.
- Diferencia.
- Muestras.
- Intervalos de confianza.
- Jugadores únicos.
- Distribución por jugador.

Permitir visualizar ambas poblaciones lado a lado.

No presentar diferencias pequeñas con muestras insuficientes como conclusiones definitivas.

# 14. LEAK FINDER POBLACIONAL

Quiero detectar automáticamente patrones que puedan convertirse en explotaciones.

Ejemplos:

- BB foldea mucho contra minraise.
- Fish paga demasiado flop.
- Reg abandona mucho river.
- Fish hace muy pocos raises.
- Jugadores con alta frecuencia de limp/fold.
- Poblaciones con baja frecuencia de bluff river.
- Fishes que foldean frente a overbets.
- Regs que under-iso-raisean.
- Jugadores que tienen rangos excesivamente concentrados en ciertas líneas.

## Detección

Utilizar:

- Frecuencias observadas.
- Comparaciones entre poblaciones.
- Comparaciones entre tamaños.
- Comparaciones temporales.
- Muestras.
- Consistencia entre jugadores.
- Referencias empíricas cuando sean apropiadas.

No llamar leak a cualquier frecuencia extrema.

Separar:

1. Tendencia observada.
2. Diferencia empírica.
3. Hipótesis explotativa.
4. Ajuste evaluado.

## Priorización

Ordenar investigaciones por:

- Frecuencia del spot.
- Tamaño de muestra.
- Magnitud de diferencia.
- Consistencia.
- Incertidumbre.
- Impacto potencial.

Crear una lista de posibles explotaciones para revisar.

## Navegación

Al seleccionar una tendencia:

- Abrir spot.
- Mostrar filtros.
- Mostrar manos.
- Comparar poblaciones.
- Ver siguientes acciones.
- Guardar como estrategia.

# 15. CALCULADORAS DE EXPLOTACIÓN

Desarrollar calculadoras transparentes para situaciones donde pueda estimarse el beneficio inmediato sin modelos demasiado complejos.

Ejemplos:

- Fold equity de un bluff puro.
- Umbral de fold frente a un bet.
- Beneficio inmediato de un steal.
- Escenarios de shove/call con rangos explícitos y evaluadores válidos, si se implementan posteriormente.
- Análisis de sensibilidad al cambiar la frecuencia de fold.

No asumir que una frecuencia histórica de fold seguirá siendo idéntica ante un cambio grande de estrategia.

Diferenciar:

- Dato observado.
- Supuesto.
- Cálculo.
- Hipótesis.

Mostrar claramente qué parte del resultado está respaldada por datos y qué parte depende de supuestos.

No afirmar rentabilidad exacta cuando falten componentes relevantes.

# 16. STRATEGY BUILDER

Quiero convertir las investigaciones en una biblioteca de estrategias explotativas.

Cada estrategia debe almacenar:

- Nombre.
- Modalidad.
- Posiciones.
- Stack.
- Población.
- Subperfil.
- Spot.
- Secuencia.
- Tendencia observada.
- Oportunidades.
- Evidencia.
- Ajuste propuesto.
- Modelo utilizado, si existe.
- Riesgos.
- Limitaciones.
- Manos relevantes.
- Fecha.
- Notas.

Estados:

- En investigación.
- Hipótesis.
- Tendencia validada.
- Evaluado con modelo.
- Descartado.

Permitir versiones y revisiones.

# 17. REPLAYER PROFESIONAL

Modernizar el replayer.

Mostrar mesa HU o 3H con:

- Posiciones.
- Stacks.
- Bote.
- Board.
- Cartas conocidas.
- Apuestas.
- Secuencia.
- Tamaños en BB y porcentaje del bote.

Permitir:

- Avanzar y retroceder.
- Saltar a la decisión relevante.
- Revisar varias manos.
- Filtrar manos.
- Guardar notas.
- Marcar favoritas.
- Volver a la estadística original.

No revelar cartas ocultas.

# 18. SISTEMA DE ESTUDIO

Crear una biblioteca de investigaciones.

Flujo:

Descubrir tendencia → Abrir spot → Ver manos → Comparar Reg/Fish → Investigar tamaños → Formular hipótesis → Guardar estrategia.

Incluir:

- Investigaciones recientes.
- Favoritos.
- Tendencias destacadas.
- Estrategias guardadas.
- Hipótesis pendientes.
- Manos marcadas.
- Notas de estudio.

No mostrar métricas sin una función clara.

# 19. CALIDAD ESTADÍSTICA

Esta sección es fundamental.

Mostrar:

- Numerador.
- Denominador.
- Oportunidades.
- Jugadores.
- Intervalos de confianza.
- Datos faltantes.
- Condiciones exactas de consulta.

Distinguir cero oportunidades de cero folds observados.

Considerar la dependencia de manos procedentes del mismo jugador.

Permitir estadísticas ponderadas por oportunidad o jugador cuando sea apropiado.

Controlar:

- Sesgos de clasificación.
- Muestras pequeñas.
- Diferencias entre períodos.
- Concentración de manos en pocos jugadores.
- Comparaciones múltiples.
- Sesgo de showdown.
- Diferencias entre correlación y causalidad.

Evitar afirmaciones de rentabilidad sin evidencia suficiente.

# 20. RENDIMIENTO, BASE DE DATOS Y ESTABILIDAD

Mantener DuckDB y el importador TXT existente.

Implementar:

- Importaciones incrementales.
- Detección de duplicados.
- Progreso visible.
- Cancelación.
- Consultas en workers.
- Caché de consultas.
- Tablas virtualizadas.
- Búsqueda rápida.
- Migraciones versionadas.
- Backups.
- Restauración.
- Logs de diagnóstico.
- Manejo correcto de archivos bloqueados en Windows.

Evitar errores de bloqueo de DuckDB.

Implementar detección de instancias simultáneas, liberación correcta de conexiones y mensajes claros cuando otra instancia mantenga la base abierta.

No borrar bases de datos automáticamente para resolver errores.

Mantener datos persistentes fuera de carpetas que se sustituyan al actualizar el código.

# 21. PRUEBAS Y VALIDACIÓN

Crear y mantener pruebas para:

- Importación.
- Deduplicación.
- Reconstrucción HU y 3H.
- Orden de actuación.
- Stacks.
- Pots.
- Sidepots.
- Clasificación.
- Reglas multivariable.
- Estadísticas poblacionales.
- Secuencias.
- Reportes.
- Filtros.
- Comparación.
- Replayer.
- Persistencia.
- Backups.
- Migraciones.
- Rendimiento.

Comparar los resultados contra historiales reales y verificadores independientes.

Validar manualmente muestras de cada tipo de spot complejo.

No limitar la validación a que las pruebas automáticas pasen: comprobar también coherencia estadística y usabilidad.

# 22. ORDEN DE DESARROLLO

Este es el orden que quiero seguir.

## Fase 1 — Clasificación y poblaciones

- Métricas Reg/Fish avanzadas.
- Reglas multivariable.
- Etiquetas manuales protegidas.
- Poblaciones personalizadas.
- Comparaciones por contexto.

## Fase 2 — Rediseño visual

- Dashboard moderno.
- Exploradores modernos.
- Tablas profesionales.
- Filtros intuitivos.
- Navegación clara.
- Validación 1440×900.

## Fase 3 — Constructor universal de secuencias

- Árbol visual.
- Consultas estructuradas.
- Navegación por nodos.
- Smart Reports.
- Estadísticas personalizadas.

## Fase 4 — Dual Mode y Range Research

- Análisis de ambos jugadores.
- Matrices 13×13.
- Rangos observados.
- Grupos de manos.
- Comparaciones.

## Fase 5 — Postflop avanzado

- Líneas pendientes.
- Multiway.
- Sidepots.
- Boards.
- Tamaños.
- Barrels.

## Fase 6 — Explotaciones

- Leak Finder.
- Calculadoras.
- Strategy Builder.
- Priorización.

## Fase 7 — Pulido y validación

- Replayer.
- Sistema de estudio.
- Rendimiento.
- Robustez.
- UX.
- Tests.

# 23. INSTRUCCIONES PARA CODEX

No respondas únicamente con un plan.

Empieza auditando el proyecto y continúa implementando la primera fase.

Trabaja por incrementos funcionales, con pruebas y commits.

No intentes implementar todo en una única ejecución si eso compromete la calidad.

No repitas trabajo terminado.

Conserva los reportes anteriores.

No elimines clasificaciones, manos, investigaciones ni estrategias.

Evita reescrituras masivas innecesarias.

Cada fase debe terminar con código funcional y pruebas.

Documenta:

- Qué implementaste.
- Qué archivos cambiaste.
- Qué pruebas pasaron.
- Qué funciones faltan.
- Qué limitaciones existen.
- Qué commits guardaste.
- Qué debo comprobar en Windows.

Mantén la ejecución mediante Python y `start_windows.bat`.

No trabajar en un `.exe` o instalador todavía.

Cuando finalice una iteración, deja indicado en la documentación desde qué punto debe continuar la siguiente.

## RESULTADO FINAL ESPERADO

Quiero que Spin Population Lab sea una herramienta profesional, moderna y muy potente, dedicada exclusivamente a estudiar tendencias poblacionales de Spins.

Debe permitirme analizar Regs y Fishes, investigar cualquier secuencia válida, encontrar patrones explotables, contrastar muestras, revisar manos y convertir mis descubrimientos en estrategias de estudio.

Quiero que su principal ventaja sea la combinación de:

**Profundidad de análisis + precisión estadística + interfaz moderna + facilidad para encontrar explotaciones.**

La prioridad no es tener la mayor cantidad de reportes posibles.

La prioridad es poder investigar libremente cómo juega la población y comprender qué ajustes estratégicos pueden aprovechar sus tendencias reales.