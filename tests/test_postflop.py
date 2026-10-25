from pathlib import Path
from dataclasses import replace
import pytest
from src.postflop import SRP_LINES,srp_patterns
from src.presets import PRESETS,research_presets
from src.store import Store
from src.sequences import sequence_report
from src.history import read_text
from src.engine import replay
from scripts.validate_postflop import validate
from test_sequences import hand


def test_original_reports_are_preserved():
    assert PRESETS[:28]==research_presets()
    for p in PRESETS:p.pattern.validate()


@pytest.mark.parametrize('fixture',['ipoker_real_anonymized.txt','srp_real_anonymized.txt'])
def test_real_fixtures_against_independent_state_machine(tmp_path,fixture):
    s=Store(tmp_path/'p.duckdb')
    result=s.import_file(Path(__file__).parent/'fixtures'/fixture);assert result['rejected']==0;s.close()
    reports=validate(tmp_path/'p.duckdb')
    assert sum(r['opportunities'] for r in reports.values())>0
    assert not {k:r for k,r in reports.items() if r['missing'] or r['unexpected'] or r['mismatches']}


@pytest.mark.parametrize('line',SRP_LINES,ids=lambda l:l[0])
@pytest.mark.parametrize('response',['Fold','Call €80','Raise (NF) €160'])
def test_srp_barrel_denominators_and_positions(tmp_path,line,response):
    # Explicit 2 BB open and call, same 80 chip preflop pot in HU and 3H
    # when BTN folds. For a folded SB there are 10 extra dead chips.
    key,format_,prefix,ip=line
    raw=hand(response,aggressor='A' if ip else 'B')
    if format_=='HU':
        raw=raw.replace('A: Call €10\nB: Check','A: Raise (NF) €40\nB: Call €20')
    else:
        # Build seating and preflop actions from declared roles, mapping the
        # betting aggressor to the appropriate existing synthetic name.
        names={'A':'A' if ip else 'B','B':'B' if ip else 'A','C':'C'}
        seats={pos:names[role] for role,pos,action in prefix}
        raw=raw.replace('Seat 1: A (€500 in chips)  DEALER\nSeat 2: B (€500 in chips)', '\n'.join(f'Seat {i+1}: {seats[pos]} (€500 in chips)'+('  DEALER' if i==0 else '') for i,pos in enumerate(('BTN','SB','BB'))))
        raw=raw.replace('A: Post SB €10\nB: Post BB €20',f"{seats['SB']}: Post SB €10\n{seats['BB']}: Post BB €20")
        paid={'BTN':0,'SB':10,'BB':20}
        pre=[]
        for role,pos,act in prefix:
            pre.append(f"{names[role]}: "+('Raise (NF) €40' if act=='raise' else f'Call €{40-paid[pos]}' if act=='call' else 'Fold'))
        raw=raw.replace('A: Call €10\nB: Check','\n'.join(pre))
    extra=40+(10 if key=='3h_btn_bb' else 20 if key=='3h_btn_sb' else 0)
    pot={'Fold':160,'Call €80':320,'Raise (NF) €160':320}[response]+extra
    old={'Fold':160,'Call €80':320,'Raise (NF) €160':320}[response]
    raw=raw.replace(f'€{old}',f'€{pot}')
    s=Store(tmp_path/'p.duckdb');p=tmp_path/'h.txt';p.write_text(raw,encoding='utf-8');r=s.import_file(p);assert r['added']==1,r
    patterns=srp_patterns(line)
    for name in ('cbet','vs_cbet','barrel_2','vs_barrel_2','barrel_3','vs_barrel_3'):
        report=sequence_report(s,patterns[name],{'format':format_,'include_hero':True})
        assert report['opportunities']==1,name
        assert report['samples'][0]['actor']==('A' if ip else 'B') if not name.startswith('vs_') else report['samples'][0]['actor']==('B' if ip else 'A')
    s.close()


def test_unopened_allin_is_bet_and_existing_analysis_upgrades_safely(tmp_path):
    raw=hand().replace('B: Bet €20','B: Allin €480').split('*** TURN ***')[0]
    raw=raw.replace('A: Call €20','A: Fold')+'*** SUMMARY ***\nTotal pot €40 Rake €0\nB: wins €40\n'
    s=Store(tmp_path/'p.duckdb');p=tmp_path/'h.txt';p.write_text(raw,encoding='utf-8');assert s.import_file(p)['added']==1
    assert s.con.execute("SELECT result FROM observations WHERE street=2 AND actor='B'").fetchone()[0]=='bet'
    s.con.execute('UPDATE analysis_metadata SET version=2');s.close()
    s=Store(tmp_path/'p.duckdb');assert s.con.execute('SELECT version FROM analysis_metadata').fetchone()[0]==3
    assert list((tmp_path/'backups').glob('*.duckdb'))
    assert sequence_report(s, __import__('src.sequences',fromlist=['limped_barrels']).limped_barrels(1),{})['opportunities']==1
    s.close()


def test_breakdown_denominators_and_limp_exclusion(tmp_path):
    from src.sequences import limped_barrels
    s=Store(tmp_path/'p.duckdb');p=tmp_path/'h.txt';p.write_text(hand(),encoding='utf-8');s.import_file(p)
    for line in SRP_LINES:
        assert sequence_report(s,srp_patterns(line)['cbet'],{'include_hero':True})['opportunities']==0
    report=sequence_report(s,limped_barrels(),{})
    for dimension in ('Textura','Apuesta enfrentada'):
        rows=[r for r in report['breakdowns'] if r['dimension']==dimension]
        assert sum(r['cases'] for r in rows)==report['opportunities']
        assert all(r['opportunities']==1 and r['frequency']==1 for r in rows)
    s.close()


def test_real_srp_pot_and_full_fixture_balances(tmp_path):
    fixture=Path(__file__).parent/'fixtures/srp_real_anonymized.txt'
    hands,errors,_=read_text(fixture.read_bytes());assert len(hands)==36 and not errors
    for h in hands:
        obs,events,balance=replay(h)
        assert balance['pot']==h.pot==sum(h.wins.values())+h.rake
        assert sum(balance['remaining'].values())+h.pot==sum(p['stack'] for p in h.players)
    s=Store(tmp_path/'p.duckdb');s.import_file(Path(__file__).parent/'fixtures/ipoker_real_anonymized.txt')
    r=sequence_report(s,srp_patterns(SRP_LINES[1])['vs_cbet'],{'include_hero':True})
    row=next(x for x in r['samples'] if x['hand_id']=='ipoker:12543201521')
    assert row['position']=='BB' and row['result']=='fold'
    assert row['pot']==340 and row['facing_pct']==1 # 170 before flop bet + 170 bet
    s.close()
