from pathlib import Path
from dataclasses import replace
import pytest
from src.store import Store
from src.advanced_spots import advanced_patterns
from src.presets import PRESETS,research_presets
from src.postflop import srp_presets
from src.sequences import sequence_report
from scripts.validate_advanced import validate
from test_presets import preflop_hand


def multi(response='call',game=900):
    pre=preflop_hand(['T: Raise (NF) €40','S: Call €30','B: Call €20'],120,3,game).split('*** FLOP ***')[0]
    streets=[]
    for street,board,bet in [('FLOP','C2 D5 H9',30),('TURN','S7',60),('RIVER','CQ',120)]:
        streets += [f'*** {street} *** [{board}]','S: Check','B: Check',f'T: Bet €{bet}']
        streets += ['S: '+('Fold' if street=='RIVER' and response=='fold' else f'Call €{bet}'),f'B: Call €{bet}']
    pot=630 if response=='fold' else 750
    return pre+'\n'.join(streets)+f'\n*** SUMMARY ***\nTotal pot €{pot} Rake €0\nT: wins €{pot}\n'


def test_preserves_previous_79():
    assert PRESETS[:80]==research_presets()+srp_presets()
    assert len({p.key for p in PRESETS})==len(PRESETS)
    for p in PRESETS:p.pattern.validate()


@pytest.mark.parametrize('response',['call','fold'])
def test_multiway_same_roles_across_barrels(tmp_path,response):
    s=Store(tmp_path/'p.duckdb');p=tmp_path/'h.txt';p.write_text(multi(response),encoding='utf-8');r=s.import_file(p);assert r['added']==1,r
    patterns=advanced_patterns()
    for key in ('mw_cbet','mw_vs_cbet_sb','mw_vs_cbet_bb_call','mw_barrel_3_BC','mw_vs_barrel_3_BC_B','mw_vs_barrel_3_BC_C','mw_barrel_4_BC','mw_vs_barrel_4_BC_B'):
        report=sequence_report(s,patterns[key][1],{'format':'3H'})
        assert report['opportunities']==1,key
        sample=report['samples'][0];assert (sample['role_a'],sample['role_b'],sample['role_c'])==('T','S','B')
        assert sample['active_players']==3
    c=sequence_report(s,patterns['mw_vs_barrel_4_BC_C'][1],{'format':'3H'})
    assert c['opportunities']==(response=='call') # This node requires SB call first.
    s.close()
    reports=validate(tmp_path/'p.duckdb')
    assert not {k:r for k,r in reports.items() if r['missing'] or r['unexpected'] or r['mismatches']}


def test_checkthrough_river_denominator(tmp_path):
    raw=preflop_hand(['S: Raise (NF) €40','B: Call €20'],80)
    s=Store(tmp_path/'p.duckdb');p=tmp_path/'h.txt';p.write_text(raw,encoding='utf-8');s.import_file(p)
    r=sequence_report(s,advanced_patterns()['river_hu_sb_bb_two_checked_lead'][1],{'format':'HU'})
    assert r['opportunities']==1 and r['samples'][0]['result']=='check'
    assert sequence_report(s,advanced_patterns()['river_hu_sb_bb_two_checked_vs_lead'][1],{})['opportunities']==0
    s.close()


def test_real_advanced_fixtures_against_oracle(tmp_path):
    from src.history import read_text
    from src.engine import replay
    path=Path(__file__).parent/'fixtures/advanced_real_anonymized.txt'
    hands,errors,_=read_text(path.read_bytes());assert len(hands)==5 and not errors
    for h in hands:
        _,_,balance=replay(h)
        assert balance['pot']==h.pot==sum(h.wins.values())+h.rake
        assert all(p['name'].startswith('PLAYER_') for p in h.players)
    s=Store(tmp_path/'p.duckdb');r=s.import_file(path);assert r['added']==5 and r['rejected']==0;s.close()
    reports=validate(tmp_path/'p.duckdb')
    assert not {k:r for k,r in reports.items() if r['missing'] or r['unexpected'] or r['mismatches']}
