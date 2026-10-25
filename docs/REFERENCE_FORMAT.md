# Intercambio de referencias

La app importa JSON UTF-8 versión 1. Es una frontera de intercambio para adaptar exportaciones legales de un solver; **no lee formatos nativos propietarios automáticamente**. `source` debe identificar herramienta, versión y configuración. Frecuencias 0..1. No se incluyen datos solver ni tendencias de ejemplo en la base.

Estructura (metavariables, no archivo listo para importar):

```text
{
  "version": 1,
  "source": "solver / versión / parámetros",
  "baselines": [
    {
      "filters": {"spot": "SB_FIRST", "format": "HU", "street": 1,
                  "stake": "EUR 5.00", "population": "Fish", "bb_eff": [10, 15]},
      "action": "raise",
      "frequency": FRECUENCIA_DE_TU_REFERENCIA,
      "min_opportunities": 200,
      "min_players": 10
    }
  ],
  "ranges": [
    {"filters": {"spot": "SB_FIRST", "format": "HU", "bb_eff": [10, 15]},
     "action": "raise", "hands": {"AA": PESO, "AKs": PESO, "AKo": PESO}}
  ]
}
```

Los rangos se conservan como referencias de estudio; no completan manos ocultas ni alimentan automáticamente la equity del modelo. Strategy Builder guarda población Reg/Fish, filtros, acción, razonamiento y estado de hipótesis. Exporta JSON local.

Filtros avanzados disponibles en la API Python: spot, street, position, format, stake, texture, previous, modality, actor, opponent, board, path, can_raise, check_raise_opportunity; rangos bb_eff, bb_eff_min, facing_bb, facing_pct, size_bb, size_pct. `population` y `opponent_population` se resuelven contra etiquetas actuales sin reimportar historiales.
