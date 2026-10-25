"""Explicit opportunity cases; all monetary fixtures below are synthetic."""
from dataclasses import replace
from pathlib import Path

import pytest

from src.presets import PRESETS, PRESETS_BY_KEY, limped_continuation
from src.sequences import Pattern, RoleFilter, Step, limped_barrels, sequence_report
from src.store import Store
from test_sequences import hand


def preflop_hand(actions, pot, players=2, game=800, stacks=None):
    stacks = dict(stacks or {})
    names = ['S', 'B'] if players == 2 else ['T', 'S', 'B']
    stacks = {n: stacks.get(n, 500) for n in names}
    lines = [f"GAME #{game} Version:26.7 Uncalled:Y Texas Hold'em NL  Tournament 2026-10-01 12:00:00/GMT",
             'Table Info: Size: 3, Blinds: 10/20',
             'Table Twister €5 SNG, 999, 998 (Tournament: Twister €5 SNG Buy-In: €4.65 + €0.35)']
    lines += [f'Seat {i+1}: {n} (€{stacks[n]} in chips)' + ('  DEALER' if i == 0 else '') for i, n in enumerate(names)]
    lines += ['S: Post SB €10', 'B: Post BB €20', '*** HOLE CARDS ***', *actions]
    # Complete settled test hands with check-through streets, independently of
    # the sequence matcher. Supplied pot totals are manually calculated.
    active = set(names)
    paid = dict.fromkeys(names, 0)
    paid.update(S=10, B=20)
    for line in actions:
        actor, action = line.split(': ')
        if action == 'Fold':
            active.remove(actor)
        if '€' in action:
            amount = int(action.split('€')[1])
            paid[actor] = amount if action.startswith('Raise') else paid[actor] + amount
    if len(active) > 1:
        order = ['B', 'S'] if players == 2 else ['S', 'B', 'T']
        able = [n for n in order if n in active and paid[n] < stacks[n]]
        for street, board in [('FLOP', 'C2 D5 H9'), ('TURN', 'S7'), ('RIVER', 'CQ')]:
            lines.append(f'*** {street} *** [{board}]')
            if len(able) > 1:
                lines += [f'{n}: Check' for n in able]
    lines += ['*** SUMMARY ***', f'Total pot €{pot} Rake €0', f'{sorted(active)[0]}: wins €{pot}']
    return '\n'.join(lines)


CASES = [
    ('hu_sb_open', 2, ['S: Fold'], 20, 'S', 'fold'),
    ('hu_bb_vs_limp', 2, ['S: Call €10', 'B: Check'], 40, 'B', 'check'),
    ('hu_bb_vs_minraise', 2, ['S: Raise (NF) €40', 'B: Fold'], 40, 'B', 'fold'),
    ('hu_bb_vs_raise', 2, ['S: Raise (NF) €60', 'B: Call €40'], 120, 'B', 'call'),
    ('hu_bb_vs_shove', 2, ['S: Allin €490', 'B: Fold'], 40, 'B', 'fold'),
    ('hu_limp_vs_iso', 2, ['S: Call €10', 'B: Raise (NF) €80', 'S: Fold'], 40, 'S', 'fold'),
    ('hu_limp_vs_shove', 2, ['S: Call €10', 'B: Allin €480', 'S: Call €480'], 1000, 'S', 'call'),
    ('hu_sb_vs_3bet', 2, ['S: Raise (NF) €40', 'B: Raise (NF) €100', 'S: Call €60'], 200, 'S', 'call'),
    ('3h_btn_open', 3, ['T: Fold', 'S: Fold'], 20, 'T', 'fold'),
    ('3h_sb_after_fold', 3, ['T: Fold', 'S: Raise (NF) €40', 'B: Fold'], 40, 'S', 'raise'),
    ('3h_sb_vs_btn', 3, ['T: Raise (NF) €40', 'S: Call €30', 'B: Fold'], 100, 'S', 'call'),
    ('3h_bb_vs_btn', 3, ['T: Raise (NF) €40', 'S: Fold', 'B: Call €20'], 90, 'B', 'call'),
    ('3h_bb_squeeze', 3, ['T: Raise (NF) €40', 'S: Call €30', 'B: Raise (NF) €140', 'T: Fold', 'S: Fold'], 120, 'B', 'raise'),
    ('3h_bb_vs_btn_limp', 3, ['T: Call €20', 'S: Fold', 'B: Check'], 50, 'B', 'check'),
    ('3h_bb_vs_two_limps', 3, ['T: Call €20', 'S: Call €10', 'B: Check'], 60, 'B', 'check'),
    ('3h_bb_vs_sb_limp', 3, ['T: Fold', 'S: Call €10', 'B: Check'], 40, 'B', 'check'),
    ('3h_bb_vs_sb_raise', 3, ['T: Fold', 'S: Raise (NF) €40', 'B: Call €20'], 80, 'B', 'call'),
    ('3h_btn_vs_sb_3bet', 3, ['T: Raise (NF) €40', 'S: Raise (NF) €120', 'B: Fold', 'T: Fold'], 100, 'T', 'fold'),
    ('3h_btn_vs_bb_3bet', 3, ['T: Raise (NF) €40', 'S: Fold', 'B: Raise (NF) €120', 'T: Call €80'], 250, 'T', 'call'),
]


def add(store, tmp_path, raw, name='hand'):
    path = tmp_path / (name + '.txt')
    path.write_text(raw, encoding='utf-8')
    result = store.import_file(path)
    assert result['added'] == 1, result


@pytest.mark.parametrize('key,players,actions,pot,actor,result', CASES, ids=[c[0] for c in CASES])
def test_preflop_catalog_opportunities(tmp_path, key, players, actions, pot, actor, result):
    store = Store(tmp_path / 'p.duckdb')
    add(store, tmp_path, preflop_hand(actions, pot, players))
    preset = PRESETS_BY_KEY[key]
    report = sequence_report(store, preset.pattern, {'format': preset.format})
    assert report['opportunities'] == 1
    assert [(s['actor'], s['result']) for s in report['samples']] == [(actor, result)]
    assert report['samples'][0]['position'] == preset.pattern.target_position
    assert report['rows'][0]['frequency'] == 1
    assert sequence_report(store, preset.pattern, {'format': '3H' if players == 2 else 'HU'})['opportunities'] == 0
    store.close()


def test_minraise_denominator_includes_all_responses_and_excludes_larger_raise(tmp_path):
    store = Store(tmp_path / 'p.duckdb')
    responses = [(['B: Fold'], 40), (['B: Call €20'], 80),
                 (['B: Raise (NF) €100', 'S: Fold'], 80), (['B: Allin €480', 'S: Fold'], 80)]
    for i, (response, pot) in enumerate(responses):
        add(store, tmp_path, preflop_hand(['S: Raise (NF) €40', *response], pot, game=i), str(i))
    add(store, tmp_path, preflop_hand(['S: Raise (NF) €60', 'B: Fold'], 40, game=20), 'larger')
    report = sequence_report(store, PRESETS_BY_KEY['hu_bb_vs_minraise'].pattern, {'format': 'HU'})
    assert report['opportunities'] == 4
    assert {r['result']: r['cases'] for r in report['rows']} == {'fold': 1, 'call': 1, 'raise': 1, 'shove': 1}
    assert all(r['frequency'] == .25 for r in report['rows'])
    store.close()


def test_squeeze_requires_raise_eligibility_and_rejects_sb_fold(tmp_path):
    store = Store(tmp_path / 'p.duckdb')
    add(store, tmp_path, preflop_hand(['T: Raise (NF) €40', 'S: Call €30', 'B: Allin €10'], 110, 3, stacks={'B': 30}))
    report = sequence_report(store, PRESETS_BY_KEY['3h_bb_squeeze'].pattern, {'format': '3H'})
    assert report['opportunities'] == 0  # BB may call but cannot squeeze.
    add(store, tmp_path, preflop_hand(['T: Raise (NF) €40', 'S: Fold', 'B: Raise (NF) €120', 'T: Fold'], 90, 3, game=801), 'fold')
    assert sequence_report(store, PRESETS_BY_KEY['3h_bb_squeeze'].pattern, {'format': '3H'})['opportunities'] == 0
    add(store, tmp_path, preflop_hand(['T: Raise (NF) €40', 'S: Call €30', 'B: Call €20'], 120, 3, game=802), 'legal')
    preset = PRESETS_BY_KEY['3h_bb_squeeze'].pattern
    next_node = replace(preset, steps=preset.steps + (Step(1, ('call',), role='B', position='BB', can_raise=True),),
                        target_role='', target_position='', target_street=None, target_can_raise=None)
    assert sequence_report(store, next_node, {'format': '3H'})['opportunities'] == 1
    loose = replace(next_node, steps=next_node.steps[:-1] + (replace(next_node.steps[-1], can_raise=None),))
    assert sequence_report(store, loose, {'format': '3H'})['opportunities'] == 2
    store.close()


@pytest.mark.parametrize('aggressor', ['A', 'B'])
@pytest.mark.parametrize('barrel', [2, 3])
def test_barrel_opportunity_counts_checks_as_well_as_bets(tmp_path, aggressor, barrel):
    store = Store(tmp_path / 'p.duckdb')
    add(store, tmp_path, hand('Call €80', aggressor, 100))
    # Check through turn and river (barrel 2) or river only (barrel 3).
    raw = hand('Call €80', aggressor, 101)
    defender = 'B' if aggressor == 'A' else 'A'
    for amount in ([40, 80] if barrel == 2 else [80]):
        segment = (f'{defender}: Check\n' if aggressor == 'A' else '') + f'{aggressor}: Bet €{amount}\n{defender}: Call €{amount}'
        raw = raw.replace(segment, 'B: Check\nA: Check')
    pot = 80 if barrel == 2 else 160
    raw = raw.replace('€320', f'€{pot}')
    add(store, tmp_path, raw, 'check')
    report = sequence_report(store, limped_continuation(barrel), {'format': 'HU'})
    assert report['opportunities'] == 2
    assert {r['result']: r['cases'] for r in report['rows']} == dict(bet=1, check=1)
    assert {r['actor'] for r in report['samples']} == {aggressor}
    assert sequence_report(store, limped_barrels(barrel), {'format': 'HU'})['opportunities'] == 1
    store.close()


def test_fixed_population_roles_survive_a_change_of_actor_and_roundtrip(tmp_path):
    store = Store(tmp_path / 'p.duckdb')
    add(store, tmp_path, hand('Call €80'))  # B bets, A defends in the fixture.
    store.label('A', 'Fish', profile='Calling station')
    store.label('B', 'Reg', profile='Reg tight')
    pattern = replace(limped_barrels(1), role_filters=(RoleFilter('A', 'Reg'), RoleFilter('B', 'Fish', 'Calling station')))
    assert Pattern.from_dict(pattern.to_dict()) == pattern
    assert sequence_report(store, pattern, {})['samples'][0]['actor'] == 'A'
    next_node = replace(pattern, steps=pattern.steps + (Step(2, ('call',), role='B'),), target_role='', target_street=None)
    report = sequence_report(store, next_node, {})
    assert report['opportunities'] == 1 and report['samples'][0]['actor'] == 'B'
    assert report['samples'][0]['category'] == 'Reg'
    assert report['samples'][0]['role_b'] == 'A'
    wrong = replace(next_node, role_filters=(RoleFilter('A', 'Fish'),))
    assert sequence_report(store, wrong, {})['opportunities'] == 0
    store.close()


def test_optional_unbound_role_is_not_misclassified_as_unknown(tmp_path):
    store = Store(tmp_path / 'p.duckdb')
    add(store, tmp_path, hand())
    pattern = Pattern((Step(1, ('fold',), role='C', optional=True),), target_street=1,
                      role_filters=(RoleFilter('C', 'Sin clasificar'),))
    assert sequence_report(store, pattern, {})['opportunities'] == 0
    # A real, bound and unlabelled player qualifies.
    pattern = replace(PRESETS_BY_KEY['hu_sb_open'].pattern, role_filters=(RoleFilter('A', 'Sin clasificar'),))
    assert sequence_report(store, pattern, {})['opportunities'] == 1
    assert sequence_report(store, replace(pattern, role_filters=(RoleFilter('A', player="' OR 1=1 --"),)), {})['opportunities'] == 0
    store.close()


def test_three_roles_do_not_confuse_direct_opponent_with_caller(tmp_path):
    store = Store(tmp_path / 'p.duckdb')
    case = next(c for c in CASES if c[0] == '3h_bb_squeeze')
    add(store, tmp_path, preflop_hand(case[2], case[3], 3))
    store.label('T', 'Reg'); store.label('S', 'Fish'); store.label('B', 'Reg')
    pattern = replace(PRESETS_BY_KEY[case[0]].pattern, role_filters=(RoleFilter('A', 'Reg'), RoleFilter('B', 'Reg'), RoleFilter('C', 'Fish')))
    sample = sequence_report(store, pattern, {})['samples'][0]
    assert (sample['role_a'], sample['role_b'], sample['role_c'], sample['opponent']) == ('T', 'B', 'S', 'T')
    assert sequence_report(store, pattern, {'opponent_population': 'Fish'})['opportunities'] == 0
    store.close()


def test_validation_and_backwards_compatible_saved_sequences():
    for preset in PRESETS:
        preset.pattern.validate()
        assert Pattern.from_dict(preset.pattern.to_dict()) == preset.pattern
    assert len({p.key for p in PRESETS}) == len(PRESETS)
    old = {'steps': [], 'anchor_street': 1, 'target_role': '', 'target_street': None, 'name': 'old'}
    assert Pattern.from_dict(old).role_filters == ()
    with pytest.raises(ValueError):
        replace(limped_barrels(), role_filters=(RoleFilter('C', 'Fish'),)).validate()
    with pytest.raises(ValueError):
        RoleFilter('B', 'Fish', 'Reg tight').validate()
    with pytest.raises(ValueError):
        Step(1, ('raise',), min_bb=3, max_bb=2).validate()


def test_independent_oracle_with_short_allin_and_catalog_cases(tmp_path):
    from scripts.validate_preflop_presets import validate
    store = Store(tmp_path / 'p.duckdb')
    for i, (_, players, actions, pot, _, _) in enumerate(CASES):
        add(store, tmp_path, preflop_hand(actions, pot, players, game=i), str(i))
    add(store, tmp_path, preflop_hand(['S: Allin €5'], 30, stacks={'S': 15}), 'short')
    store.close()
    reports = validate(tmp_path / 'p.duckdb')
    assert all(r['query_opportunities'] > 0 for r in reports.values())
    assert not any(r[k] for r in reports.values() for k in ('missing', 'unexpected', 'outcome_mismatches'))


@pytest.mark.parametrize('position,aggressor,result', [('BB','B','bet'),('BB','A','check'),('SB','A','bet')])
def test_flop_bet_presets_have_correct_acting_position(tmp_path,position,aggressor,result):
    store=Store(tmp_path/'p.duckdb');add(store,tmp_path,hand(aggressor=aggressor))
    preset=PRESETS_BY_KEY['hu_limped_flop_'+position.lower()]
    report=sequence_report(store,preset.pattern,{'format':'HU'})
    assert report['opportunities']==1
    assert (report['samples'][0]['position'],report['samples'][0]['result'])==(position,result)
    store.close()


def test_bet_fold_vs_raise_uses_aggressor_opportunity(tmp_path):
    store=Store(tmp_path/'p.duckdb')
    raw=hand().split('*** FLOP ***')[0]+'''*** FLOP *** [C2 D5 H9]
B: Bet €20
A: Raise (NF) €60
B: Fold
*** SUMMARY ***
Total pot €80 Rake €0
A: wins €80
'''
    add(store,tmp_path,raw)
    report=sequence_report(store,PRESETS_BY_KEY['hu_limped_vs_flop_raise'].pattern,{'format':'HU'})
    assert report['opportunities']==1
    assert report['samples'][0]['actor']=='B' and report['samples'][0]['result']=='fold'
    store.close()


def wait_panel(panel, app):
    from PySide6.QtTest import QTest
    for _ in range(500):
        app.processEvents(); QTest.qWait(10)
        if panel.worker and not panel.worker.isRunning():
            break
    app.processEvents()
    assert panel.worker and not panel.worker.isRunning()


def test_visual_fixed_roles_navigation_saved_settings_and_stale_result(tmp_path):
    from PySide6.QtWidgets import QApplication
    from src.sequence_ui import SequencePanel
    app = QApplication.instance() or QApplication([])
    store = Store(tmp_path / 'p.duckdb'); add(store, tmp_path, hand('Call €80'))
    store.label('A', 'Fish'); store.label('B', 'Reg')
    panel = SequencePanel(store); panel.presets.setCurrentIndex(2)
    assert panel.role.findText('C') == -1 and panel.target_position.findText('BTN') == -1
    panel.role_controls['A'][3].setText('Todos')
    assert panel.pattern.role_filters[0].player == 'Todos'
    panel.role_controls['A'][3].clear()
    panel.role_controls['A'][1].setCurrentText('Reg'); panel.role_controls['B'][1].setCurrentText('Fish')
    panel.name.setText('Roles fijos'); panel.save(); panel.run(); wait_panel(panel, app)
    assert panel.last['report']['opportunities'] == 1
    panel.follow(panel.tree.topLevelItem(0), 0); wait_panel(panel, app)
    assert panel.last['report']['samples'][0]['category'] == 'Reg'
    assert panel.pattern.role_filters[1].population == 'Fish'
    panel.go_back(); wait_panel(panel, app)
    assert panel.last['report']['samples'][0]['category'] == 'Fish'
    before = panel.pattern
    panel.low.setValue(99); panel.follow(panel.tree.topLevelItem(0), 0)
    assert panel.pattern == before and 'cambiaron' in panel.notice.text()
    panel.show_report(panel.last)
    assert panel.last is None and panel.tree.topLevelItemCount() == 0
    panel.load_saved(); wait_panel(panel, app)
    assert panel.low.value() == 0 and panel.role_controls['B'][1].currentText() == 'Fish'
    # A preflop preset resets only structural fields, preserving stake/date choices.
    panel.date_from.setText('2026-10-01')
    index = next(i for i, p in enumerate(PRESETS) if p.key == '3h_bb_squeeze')
    panel.presets.setCurrentIndex(index)
    assert panel.filters['format'].currentText() == '3H' and panel.target_raise.currentIndex() == 1
    assert panel.role.findText('C') >= 0 and panel.target_position.findText('BTN') >= 0
    assert panel.date_from.text() == '2026-10-01'
    panel.close(); store.close()
