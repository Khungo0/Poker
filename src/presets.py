"""Research opportunities defined by their prior actions, never their outcome.

Roles are local to each preset and appear explicitly in its description.
Three-handed hands retain that format after a player folds.
"""
from dataclasses import dataclass, replace

from .sequences import Pattern, Step, limped_barrels


@dataclass(frozen=True)
class ResearchPreset:
    key: str
    label: str
    pattern: Pattern
    format: str = 'HU'
    pot_type: str = 'Todos'
    explanation: str = ''


def preflop(key, label, steps=(), target='B', format_='HU', position='BB', can_raise=None):
    return ResearchPreset(
        key, label, Pattern(tuple(steps), target_role=target, target_street=1, name=label, target_position=position, target_can_raise=can_raise),
        format_, explanation='Denominador: todas las decisiones siguientes a este prefijo, antes de conocer su resultado. Shove se muestra por separado de raise.',
    )


def pre(role, position, *actions, min_bb=None, max_bb=None):
    return Step(1, tuple(actions), role=role, position=position, min_bb=min_bb, max_bb=max_bb)


def limped_continuation(barrel):
    """Bet/check opportunities for the same bettor after earlier bet/call streets."""
    if barrel not in (2, 3):
        raise ValueError('Choose second or third barrel')
    prior = limped_barrels(barrel - 1)
    return replace(
        prior,
        steps=prior.steps + (Step(barrel, ('call',), role='B'),
                            Step(barrel + 1, ('check',), role='B', optional=True)),
        target_role='A', target_street=barrel + 1,
        name=f'HU limped · oportunidad de barrel {barrel}',
    )


def research_presets():
    # Preserve the original four choices and their order for saved UI shortcuts.
    presets = [ResearchPreset(
        f'hu_limped_response_{n}', f'HU limped · respuesta a barrel {n}', limped_barrels(n),
        pot_type='limped', explanation='A es el apostador; B es el defensor. Fold/call/raise comparten denominador.',
    ) for n in (3, 2, 1)]
    presets.append(ResearchPreset('custom', 'Personalizada desde preflop', Pattern()))
    presets.extend([
        preflop('hu_sb_open', 'HU · SB primera decisión', target='A', position='SB'),
        preflop('hu_bb_vs_limp', 'HU · BB frente a limp', [pre('A', 'SB', 'limp')]),
        preflop('hu_bb_vs_minraise', 'HU · BB frente a minraise (2 BB)', [pre('A', 'SB', 'raise', min_bb=2, max_bb=2)]),
        preflop('hu_bb_vs_raise', 'HU · BB frente a open raise', [pre('A', 'SB', 'raise')]),
        preflop('hu_bb_vs_shove', 'HU · BB frente a open shove', [pre('A', 'SB', 'shove')]),
        preflop('hu_limp_vs_iso', 'HU · SB limp frente a iso-raise', [pre('A', 'SB', 'limp'), pre('B', 'BB', 'raise')], 'A', position='SB'),
        preflop('hu_limp_vs_shove', 'HU · SB limp frente a shove', [pre('A', 'SB', 'limp'), pre('B', 'BB', 'shove')], 'A', position='SB'),
        preflop('hu_sb_vs_3bet', 'HU · SB frente a 3bet (incluye shove)', [pre('A', 'SB', 'raise'), pre('B', 'BB', 'raise', 'shove')], 'A', position='SB'),
        preflop('3h_btn_open', '3H · BTN primera decisión', target='A', format_='3H', position='BTN'),
        preflop('3h_sb_after_fold', '3H · SB tras fold de BTN', [pre('C', 'BTN', 'fold')], 'A', '3H', position='SB'),
        preflop('3h_sb_vs_btn', '3H · SB frente a apertura de BTN', [pre('A', 'BTN', 'raise', 'shove')], 'B', '3H', position='SB'),
        preflop('3h_bb_vs_btn', '3H · BB frente a apertura BTN, SB fold', [pre('A', 'BTN', 'raise', 'shove'), pre('C', 'SB', 'fold')], 'B', '3H'),
        preflop('3h_bb_squeeze', '3H · BB oportunidad de squeeze', [pre('A', 'BTN', 'raise'), pre('C', 'SB', 'call')], 'B', '3H', can_raise=True),
        preflop('3h_bb_vs_btn_limp', '3H · BB frente a BTN limp, SB fold', [pre('A', 'BTN', 'limp'), pre('C', 'SB', 'fold')], 'B', '3H'),
        preflop('3h_bb_vs_two_limps', '3H · BB frente a dos limps', [pre('A', 'BTN', 'limp'), pre('C', 'SB', 'limp')], 'B', '3H'),
        preflop('3h_bb_vs_sb_limp', '3H · BB frente a SB limp, BTN fold', [pre('C', 'BTN', 'fold'), pre('A', 'SB', 'limp')], 'B', '3H'),
        preflop('3h_bb_vs_sb_raise', '3H · BB frente a SB raise, BTN fold', [pre('C', 'BTN', 'fold'), pre('A', 'SB', 'raise', 'shove')], 'B', '3H'),
        preflop('3h_btn_vs_sb_3bet', '3H · BTN frente a SB 3bet, BB fold', [pre('A', 'BTN', 'raise'), pre('B', 'SB', 'raise', 'shove'), pre('C', 'BB', 'fold')], 'A', '3H', position='BTN'),
        preflop('3h_btn_vs_bb_3bet', '3H · BTN frente a BB 3bet, SB fold', [pre('A', 'BTN', 'raise'), pre('C', 'SB', 'fold'), pre('B', 'BB', 'raise', 'shove')], 'A', '3H', position='BTN'),
    ])
    for position in ('BB', 'SB'):
        steps = [pre('A' if position == 'SB' else 'B', 'SB', 'limp'),
                 pre('A' if position == 'BB' else 'B', 'BB', 'check')]
        if position == 'SB':
            steps.append(Step(2, ('check',), role='B'))
        label = f'HU limped · {position} oportunidad de bet flop'
        presets.append(ResearchPreset(f'hu_limped_flop_{position.lower()}', label,
            Pattern(tuple(steps), target_role='A', target_street=2, name=label), pot_type='limped',
            explanation='A puede apostar o pasar. En SB exige check previo de BB; no condiciona a que A termine apostando.'))
    for n in (2, 3):
        pattern = limped_continuation(n)
        presets.append(ResearchPreset(f'hu_limped_bet_{n}', pattern.name, pattern, pot_type='limped',
            explanation='A apostó en las calles anteriores y B pagó. Mide bet/check de A, no la respuesta de B.'))
    prior = limped_barrels(1)
    label = 'HU limped · apostador frente a raise flop'
    presets.append(ResearchPreset('hu_limped_vs_flop_raise', label,
        replace(prior, steps=prior.steps + (Step(2, ('raise', 'check_raise'), role='B'),),
                target_role='A', name=label), pot_type='limped',
        explanation='Después del bet de A y el raise de B, cuenta todas las respuestas de A: fold, call o nueva subida.'))
    return presets


from .postflop import srp_presets

from .advanced_spots import advanced_presets

from .multiway_extensions import extension_presets

PRESETS = research_presets() + srp_presets() + advanced_presets() + extension_presets()
PRESETS_BY_KEY = {p.key: p for p in PRESETS}
