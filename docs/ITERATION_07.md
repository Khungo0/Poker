# Iteración 0.7 · reanudación y análisis multiway

## Comprobación después de la interrupción

Antes de modificar código se comprobó que el repositorio estaba limpio: sin cambios preparados ni sin guardar, sin stashes, y con HEAD y `main` de GitHub en `f169a9e`. Los commits `e417c33`, `ff3500c` y `f169a9e` estaban presentes. Se leyó ITERATION_06.md y se ejecutaron las 151 pruebas de partida: todas pasaron. No fue necesario recuperar, reiniciar ni repetir la implementación anterior.

## Entregado

- **42 reportes nuevos, 180 en total**, conservando intactos los patrones y orden de los 138 anteriores.
- 27 reportes para limped puro con BTN/SB/BB: apuestas y respuestas, barrels de BTN con ambos defensores o después del fold de uno. No se llama cbet al bet de un bote limpeado.
- 15 reportes de respuestas después de check-raises/reraises multiway en SRP: distinguen las acciones previas del tercero y mantienen los tres roles.
- Búsqueda visual de presets por varios términos, sin distinguir mayúsculas ni tildes. Ejemplos: `3H limped`, `limped barrel`, `raise SB`. Se muestran hasta 30 coincidencias con su total; seleccionar una conserva fechas/stack y carga el formato y posiciones compatibles del preset.
- Mensajes explícitos para búsquedas sin coincidencias y consultas sin decisiones: no se presentan estimaciones con denominador cero.

Se conservan filtros Reg/Fish, subperfiles por rol, comparaciones, estrategias, exportaciones y navegación al replayer. No se añaden etiquetas, tendencias ni referencias inventadas.

## Verificación

**162 pruebas pasan**: 151 anteriores y 11 nuevas. Se cubren la conservación de los 138 reportes, barrels limped multiway con fold/call, decisiones frente a raises/reraises, roles, conciliación de siete manos reales adicionales, oráculo, búsqueda y navegación HU/3H.

Sobre los historiales originales de €5, Hero excluido:

- 42 reportes, **2.377 oportunidades sumadas**.
- Cero decisiones omitidas, añadidas o con resultado distinto frente al verificador independiente de acciones originales.
- Ejemplo: bet BTN tras dos checks en limped multiway, 721 oportunidades (448 check / 273 bet). Son frecuencias de la muestra seleccionada, no tendencias atribuidas a Fish ni evidencia de EV.
- Ocho reportes tienen cero oportunidades reales. Los casos sintéticos complementan sus pruebas; no se afirma una validación positiva con manos reales donde no existe muestra.

Las oportunidades sumadas incluyen varios nodos de una misma mano; no son 2.377 manos independientes. Detalles y límites en [MULTIWAY_EXTENSIONS.md](MULTIWAY_EXTENSIONS.md).

La base conserva **70.038 manos, 308.439 decisiones, 4.140 resúmenes y 14 errores**. Esquema 2 y análisis 3 sin cambios. No se ha modificado la base personal ni se necesita rebuild/reimportación. Los originales y backups siguen fuera de Git.

La búsqueda se renderizó a **1920×1080 y 2560×1440** en Linux/offscreen y se revisó visualmente a 1920×1080. Las pruebas Qt mantienen la navegación de las vistas y controles previos. La interacción/DPI en Windows por Python sigue pendiente de contraste físico.

```bash
QT_QPA_PLATFORM=offscreen python -m pytest -q
python -m scripts.validate_extensions --db RUTA --output INFORME.json
```

## Cómo usarlo

Cierra la aplicación, actualiza el código en la misma carpeta y vuelve a ejecutar **start_windows.bat**. Si usas Git, actualiza con `git pull`. Conserva `.venv` y la carpeta de datos; no reinstales Python ni reimportes las manos.

En **Explorador de secuencias**, busca `3H limped` o `raise SB`, selecciona un resultado, revisa stake/stack/población/roles y pulsa **Investigar secuencia**. Reg/Fish sigue refiriéndose a tus etiquetas, no a una clasificación inventada. Abre las manos para revisar la decisión en el replayer.

`start_windows.bat`, dependencias, esquema y workflow se mantienen sin cambios respecto de 0.6. No se trabajó en ejecutables, instaladores ni empaquetado.

## Pendiente

| Área | Trabajo restante |
|---|---|
| Fase 2 | Más continuaciones después de raises turn/river, barrels de otros apostadores, sidepots complejos y otras líneas de river. No se declara toda la fase terminada. |
| Interfaz | Virtualización/paginación de tablas grandes, más estados vacíos y revisión Windows/DPI por Python. La búsqueda de presets ya está implementada. |
| Poblaciones y leaks | Comparaciones arbitrarias de escenarios, incertidumbre agrupada, control de múltiples búsquedas y clasificación histórica/calibrada. |
| Rangos/EV | Matrices avanzadas y evaluación por árboles con supuestos explícitos; las frecuencias siguen sin demostrar EV. |
| Datos | 14 manos ambiguas, contraste con el replayer de la sala y benchmark de millones. |

Empaquetado e instaladores permanecen aplazados por petición del usuario.
