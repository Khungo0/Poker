import copy,json,shutil
from pathlib import Path
import pytest,duckdb
from src.history import parse_hand
from src.engine import replay
from src.sequences import Pattern,Step,limped_barrels,sequence_report
from src.store import Store
from src.migrations import restore_copy

# Synthetic HU histories with explicitly calculated amounts and pots.
def hand(response='Fold',aggressor='B',game=100):
    defender='A' if aggressor=='B' else 'B'
    lines=[f'GAME #{game} Version:26.7 Uncalled:Y Texas Hold\'em NL  Tournament 2026-10-01 12:00:00/GMT',
      'Table Info: Size: 3, Blinds: 10/20',
      'Table Twister €5 SNG, 999, 998 (Tournament: Twister €5 SNG Buy-In: €4.65 + €0.35)',
      'Seat 1: A (€500 in chips)  DEALER','Seat 2: B (€500 in chips)',
      'A: Post SB €10','B: Post BB €20','*** HOLE CARDS ***','A: Call €10','B: Check']
    for street,board,amount in [('FLOP','C2 D5 H9',20),('TURN','S7',40),('RIVER','CQ',80)]:
        lines.append(f'*** {street} *** [{board}]')
        if aggressor=='A':lines.append('B: Check')
        lines.append(f'{aggressor}: Bet €{amount}')
        lines.append(f'{defender}: '+(response if street=='RIVER' else f'Call €{amount}'))
    if response.startswith('Raise'):lines.append(f'{aggressor}: Fold')
    pot={'Fold':160,'Call €80':320,'Raise (NF) €160':320}[response]
    lines+=['*** SUMMARY ***',f'Total pot €{pot} Rake €0',f'{defender if response.startswith("Raise") else aggressor}: wins €{pot}']
    return '\n'.join(lines)

@pytest.mark.parametrize('aggressor',['A','B'])
@pytest.mark.parametrize('response',['Fold','Call €80','Raise (NF) €160'])
def test_priority_denominator_and_role_binding(tmp_path,aggressor,response):
    s=Store(tmp_path/'p.duckdb');p=tmp_path/'hand.txt';p.write_text(hand(response,aggressor), encoding="utf-8")
    assert s.import_file(p)['added']==1
    defender='A' if aggressor=='B' else 'B'
    s.label(defender,'Fish');s.label(aggressor,'Reg')
    r=sequence_report(s,limped_barrels(),dict(format='HU',pot_type='limped',population='Fish',opponent_population='Reg'))
    assert r['opportunities']==1 and r['players']==1
    assert sequence_report(s,limped_barrels(1),dict(format='HU',population='Fish'))['opportunities']==1
    assert sequence_report(s,limped_barrels(2),dict(format='HU',population='Fish'))['opportunities']==1
    assert r['samples'][0]['actor']==defender and r['samples'][0]['role_a']==aggressor and r['samples'][0]['role_b']==defender
    assert r['samples'][0]['facing_barrel']==3
    assert r['samples'][0]['spr']==pytest.approx(420/160)
    wrong=sequence_report(s,limped_barrels(),dict(population='Reg'))
    assert wrong['opportunities']==0
    s.close()


def test_limped_not_cbet_and_stacks():
    oo,_,_=replay(parse_hand(hand()))
    assert not any('CBET' in o['spot'] for o in oo)
    assert oo[0]['initial_stack_bb']==25
    assert next(o for o in oo if o['street']==2)['street_eff_bb']==24
    assert next(o for o in oo if o['street']==2)['spr']==12
    assert oo[-1]['spot']=='VS_THIRD_BARREL'
    assert oo[-1]['pot_type']=='limped'
    assert all(o['tournament_format']=='Spin 3-max' for o in oo)


def test_prefix_never_uses_future_result(tmp_path):
    s=Store(tmp_path/'p.duckdb')
    for i,response in enumerate(['Fold','Call €80','Raise (NF) €160']):
        p=tmp_path/f'{i}.txt';p.write_text(hand(response,game=i), encoding="utf-8");s.import_file(p)
    r=sequence_report(s,limped_barrels(),{'include_hero':True,'format':'HU'})
    assert r['opportunities']==3
    assert sum(row['cases'] for row in r['rows'])==3
    assert next(row for row in r['rows'] if row['result']=='fold')['frequency']==pytest.approx(1/3)
    assert r['arrival']==1
    # Filtering a previous river bet size must not inspect the response's own size.
    assert sequence_report(s,limped_barrels(),{'facing_pct':[0.49,0.51]})['opportunities']==3
    assert sequence_report(s,limped_barrels(),{'facing_pct':[0.6,0.8]})['opportunities']==0
    s.close()


def test_swapped_aggressor_turn_and_iso_are_excluded(tmp_path):
    s=Store(tmp_path/'p.duckdb')
    raw=hand().replace('B: Bet €40\nA: Call €40','B: Check\nA: Bet €40\nB: Call €40')
    p=tmp_path/'switch.txt';p.write_text(raw, encoding="utf-8");assert s.import_file(p)['added']==1
    assert sequence_report(s,limped_barrels(),{})['opportunities']==0
    iso=hand().replace('A: Call €10\nB: Check','A: Call €10\nB: Raise (NF) €40\nA: Call €20').replace('Total pot €160','Total pot €200').replace('wins €160','wins €200')
    p=tmp_path/'iso.txt';p.write_text(iso.replace('GAME #100','GAME #101'), encoding="utf-8");assert s.import_file(p)['added']==1
    assert sequence_report(s,limped_barrels(),{})['opportunities']==0
    assert s.con.execute("SELECT count(*) FROM observations WHERE pot_type='limp_iso'").fetchone()[0]>0
    s.close()


def test_optional_steps_exclusions_round_trip(tmp_path):
    s=Store(tmp_path/'p.duckdb');p=tmp_path/'h.txt';p.write_text(hand(aggressor='A'), encoding="utf-8");s.import_file(p)
    pattern=limped_barrels();assert Pattern.from_dict(pattern.to_dict())==pattern
    bad=Pattern((Step(1,('fold',),exclude=True),),target_street=1)
    assert sequence_report(s,bad,{})['opportunities']==1
    with pytest.raises(ValueError):sequence_report(s,pattern,dict(format='HU',position='BTN'))
    assert sequence_report(s,pattern,{'date_from':'2026-10-02'})['opportunities']==0
    s.close()


def test_old_database_backup_migration_and_restore(tmp_path):
    s=Store(tmp_path/'p.duckdb');p=tmp_path/'h.txt';p.write_text(hand(), encoding="utf-8");s.import_file(p);s.label('A','Fish');s.save_document('strategy','keep',{'test':1})
    before=s.totals();s.con.execute('UPDATE metadata SET version=1')
    for column in ['pot_type','played_at','spr']:s.con.execute('ALTER TABLE observations DROP COLUMN '+column)
    s.close()
    new=Store(tmp_path/'p.duckdb')
    assert new.totals()==before and new.migration_backup.exists()
    assert new.con.execute('SELECT category FROM labels WHERE player=?',['A']).fetchone()[0]=='Fish'
    assert new.documents('strategy')[0]['name']=='keep'
    assert sequence_report(new,limped_barrels(),{})['opportunities']==1
    restored=restore_copy(new.migration_backup,tmp_path/'restored.duckdb')
    c=duckdb.connect(str(restored),read_only=True);assert c.execute('SELECT version FROM metadata').fetchone()[0]==1;c.close()
    new.close()


def test_cancel_rebuild_rolls_back(tmp_path):
    s=Store(tmp_path/'p.duckdb');p=tmp_path/'h.txt';p.write_text(hand(), encoding="utf-8");s.import_file(p)
    rows=s.con.execute('SELECT * FROM observations ORDER BY seq').fetchall()
    with pytest.raises(InterruptedError):s.rebuild_analysis(cancelled=lambda:True)
    assert s.con.execute('SELECT * FROM observations ORDER BY seq').fetchall()==rows
    s.close()


def test_replayer_conserves_chips_and_hides_unknown_cards():
    from src.replayer import replay_frames
    h=parse_hand(hand());frames=replay_frames(h)
    for f in frames:
        assert sum(f['stacks'].values())+f['pot']==100000
        assert all(cs==['?','?'] for cs in f['cards'].values())
    assert frames[-1]['pot']==0


def test_visual_builder_worker_and_saved_filters(tmp_path):
    from PySide6.QtWidgets import QApplication
    from PySide6.QtTest import QTest
    from src.sequence_ui import SequencePanel
    app=QApplication.instance() or QApplication([])
    s=Store(tmp_path/'p.duckdb');p=tmp_path/'h.txt';p.write_text(hand(), encoding="utf-8");s.import_file(p)
    panel=SequencePanel(s);panel.name.setText('Mi secuencia');panel.date_from.setText('2026-10-01');panel.size_enabled.setChecked(True);panel.size_low.setValue(49);panel.size_high.setValue(51);panel.save()
    panel.low.setValue(50);panel.date_from.clear();panel.size_enabled.setChecked(False);panel.load_saved()
    for _ in range(500):
        app.processEvents();QTest.qWait(10)
        if panel.worker and not panel.worker.isRunning():break
    app.processEvents();assert panel.last and panel.last['report']['opportunities']==1
    assert panel.breakdowns.rowCount()>0
    assert panel.date_from.text()=='2026-10-01' and panel.low.value()==0 and panel.size_enabled.isChecked()
    for width,height in [(1440,900),(1920,1080),(2560,1440)]:panel.resize(width,height);panel.show();app.processEvents();assert panel.width()==width
    panel.open_hand(0,0);app.processEvents();assert len(panel.replayer.frames)>5;panel.replayer.close();panel.pattern=Pattern();panel.street.setCurrentText('Flop');panel.action.setCurrentText('bet');panel.add_step();assert sequence_report(s,panel.pattern,{})['opportunities']==1;panel.close();s.close()


def test_real_priority_fixtures_and_response_denominator(tmp_path):
    from src.history import read_text
    fixture=Path(__file__).parent/'fixtures/third_barrel_real_anonymized.txt'
    hands,errors,_=read_text(fixture.read_bytes());assert not errors and len(hands)==3
    s=Store(tmp_path/'p.duckdb');assert s.import_file(fixture)['added']==3
    result=sequence_report(s,limped_barrels(),dict(format='HU',pot_type='limped'))
    assert result['opportunities']==3
    assert {r['result']:r['cases'] for r in result['rows']}=={'fold':1,'call':1,'raise':1}
    sample=next(r for r in result['samples'] if r['hand_id']=='ipoker:12543199593')
    # Manually reconciled: 70 preflop, +60 flop, +194 turn = 324 before river bet.
    assert sample['facing_pct']==pytest.approx(180/324)
    assert sample['pot']==504
    assert sample['actor']=='DEFENDER' and sample['opponent']=='AGGRESSOR'
    s.label('AGGRESSOR','Fish');assert sequence_report(s,limped_barrels(),dict(population='Fish'))['opportunities']==0
    s.label('DEFENDER','Fish');assert sequence_report(s,limped_barrels(),dict(population='Fish'))['opportunities']==3
    s.close()


def test_subprofile_filter_and_label_audit(tmp_path):
    from src.research import explore
    s=Store(tmp_path/'p.duckdb');p=tmp_path/'h.txt';p.write_text(hand(), encoding="utf-8");s.import_file(p)
    s.label('A','Fish',profile='Calling station')
    n=explore(s,dict(actor_profile='Calling station'))[0]['opportunities'];assert n>0
    s.label('A','Reg',profile='Reg tight');assert explore(s,dict(actor_profile='Calling station'))[0]['opportunities']==0
    assert s.con.execute('SELECT count(*) FROM label_history WHERE player=?',['A']).fetchone()[0]==2
    with pytest.raises(ValueError):s.label('A','Fish',profile='Reg tight')
    s.close()


def test_raise_in_limped_pot_never_becomes_cbet():
    raw=hand(aggressor='A').replace('B: Check\nA: Bet €20\nB: Call €20','B: Check\nA: Bet €20\nB: Raise (NF) €80\nA: Call €60').replace('B: Check\nA: Bet €40\nB: Call €40','B: Bet €50\nA: Call €50').replace('B: Check\nA: Bet €80\nB: Fold','B: Bet €100\nA: Fold').replace('Total pot €160','Total pot €300').replace('A: wins €160','B: wins €300')
    oo,_,_=replay(parse_hand(raw));assert not any('CBET' in o['spot'] for o in oo)

@pytest.mark.parametrize('response',['Fold','Call €80'])
def test_third_barrel_allin_counts_real_response(tmp_path,response):
    s=Store(tmp_path/'p.duckdb');p=tmp_path/'h.txt';p.write_text(hand(response).replace('€500 in chips','€160 in chips'), encoding="utf-8")
    assert s.import_file(p)['added']==1
    r=sequence_report(s,limped_barrels(),{});assert r['opportunities']==1
    assert not r['samples'][0]['can_raise']
    s.close()


def test_tournament_format_hand_state_and_active_players():
    raw=hand().replace('Seat 1: A (€500 in chips)  DEALER\nSeat 2: B (€500 in chips)','Seat 1: C (€500 in chips)  DEALER\nSeat 2: A (€500 in chips)\nSeat 3: B (€500 in chips)').replace('*** HOLE CARDS ***','*** HOLE CARDS ***\nC: Fold').replace('B: Bet','A: Check\nB: Bet')
    h=parse_hand(raw);oo,_,_=replay(h)
    assert all(o['format']=='3H' and o['tournament_format']=='Spin 3-max' for o in oo)
    assert oo[0]['active_players']==3
    assert all(o['active_players']==2 for o in oo if o['street']>1)


def test_cost_to_call_cannot_exceed_remaining_stack():
    fixture=Path(__file__).parent/'fixtures/third_barrel_real_anonymized.txt'
    from src.history import read_text
    for h in read_text(fixture.read_bytes())[0]:
        for o in replay(h)[0]:assert o['facing_bb']<=o['remaining']/(h.bb/100)
