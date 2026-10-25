"""Construcción de oportunidades preflop sin mezclar denominadores.

Convenciones iniciales:
- SB_FIRST: sólo HU, o 3H si BTN se ha retirado.
- BB_VS_SB_RAISE: primera respuesta del BB a raise no all-in de SB.
- BB_VS_SB_SHOVE: primera respuesta del BB a shove de SB.
- BB_VS_SB_LIMP: primera respuesta del BB al limp de SB.
- BTN_FIRST: primer movimiento voluntario de BTN 3H.
- RAISE_TO vs incremento: la cifra 'sum' se usa para determinar shove
  únicamente cuando actiontxt sugiere total ('Raise To').
"""
from __future__ import annotations
from dataclasses import dataclass
from .ipoker import Hand, Action


@dataclass(frozen=True)
class Observation:
    hand_id: str
    stake: str
    format: str
    spot: str
    actor: str
    opponent: str
    bb_eff: float
    result: str


def positions(hand: Hand) -> dict[str, str]:
    posts = [a for a in hand.actions if a.round_number == 0]
    sb = next((a.player for a in posts if a.kind == 'SB'), '')
    bb = next((a.player for a in posts if a.kind == 'BB'), '')
    if not sb or not bb or sb == bb:
        return {}
    mapping = {sb: 'SB', bb: 'BB'}
    if len(hand.players) == 3:
        others = [p.name for p in hand.players if p.name not in mapping]
        if len(others) != 1:
            return {}
        mapping[others[0]] = 'BTN'
    return mapping


def _first(actions: list[Action], actor: str, after: int = -1):
    for index, action in enumerate(actions):
        if index > after and action.player == actor and action.kind not in {'unknown', 'SB', 'BB'}:
            return index, action
    return None


def _classify_open(action: Action, stack: float, bb: float) -> str:
    if action.kind == 'fold':
        return 'fold'
    if action.kind == 'call':
        return 'limp'
    if action.kind == 'raise':
        # Avoid declaring an all-in from incremental bet amounts without proof.
        x = action.original.lower()
        if any(word in x for word in ('all-in', 'all in', 'allin', 'shove')):
            return 'shove'
        if 'raise to' in x and stack > 0 and action.amount >= stack - 1e-6:
            return 'shove'
        return 'raise'
    return 'other'


def observations(hand: Hand) -> list[Observation]:
    mapping = positions(hand)
    if not mapping:
        return []
    bypos = {v:k for k,v in mapping.items()}
    sb, bb = bypos['SB'], bypos['BB']
    pmap = {p.name:p for p in hand.players}
    # 'chips' en manos iPoker representa el stack al comienzo, pero confirmar con HH reales.
    eff = min(pmap[sb].chips, pmap[bb].chips) / hand.bb if hand.bb else 0
    if eff <= 0:
        return []
    pre = [a for a in hand.actions if a.round_number == 1]
    # Cuando hay un movimiento no identificado no es fiable reconstruir el spot.
    if any(a.kind == 'unknown' for a in pre):
        return []
    result: list[Observation] = []
    def add(spot, actor, other, stack, value):
        result.append(Observation(hand.hand_id,hand.stake,hand.format,spot,actor,other,round(stack,2),value))

    btn_folds = True
    if hand.format == '3H':
        btn = bypos['BTN']
        btn_first = _first(pre,btn)
        btn_folds = bool(btn_first and btn_first[1].kind == 'fold')
        if btn_first:
            val = _classify_open(btn_first[1], pmap[btn].chips, hand.bb)
            if val in ('fold', 'limp', 'raise', 'shove'):
                # BTN no tiene posibilidad de limp si no es ciega; call no es open lícito.
                if val != 'limp':
                    beff = min(pmap[btn].chips, pmap[sb].chips, pmap[bb].chips) / hand.bb
                    add('BTN_FIRST',btn,'',beff,val)
    if not btn_folds:
        return result

    sb_first = _first(pre,sb)
    if not sb_first:
        return result
    idx, action = sb_first
    val = _classify_open(action,pmap[sb].chips,hand.bb)
    if val in ('fold','limp','raise','shove'):
        add('SB_FIRST',sb,bb,eff,val)

    if val not in ('raise','shove','limp'):
        return result
    resp = _first(pre,bb,idx)
    if not resp:
        return result
    _, bb_action = resp
    if val in ('raise','shove'):
        bb_val = {'fold':'fold','call':'call','raise':'reraise'}.get(bb_action.kind,'other')
        if bb_val != 'other':
            add('BB_VS_SB_SHOVE' if val=='shove' else 'BB_VS_SB_RAISE',bb,sb,eff,bb_val)
    elif val == 'limp':
        bb_val = {'check':'check','raise':'raise'}.get(bb_action.kind,'other')
        if bb_val != 'other':
            add('BB_VS_SB_LIMP',bb,sb,eff,bb_val)
    return result
