from pathlib import Path
import pytest
from src.presets import PRESETS,research_presets
from src.postflop import srp_presets
from src.advanced_spots import advanced_presets
from src.multiway_extensions import extension_patterns
from src.store import Store
from src.sequences import sequence_report
from scripts.validate_extensions import validate
from test_advanced import multi
from test_presets import preflop_hand


def test_all_138_previous_reports_are_unchanged():
    assert PRESETS[:139]==research_presets()+srp_presets()+advanced_presets()
    for p in PRESETS:p.pattern.validate()


@pytest.mark.parametrize('response',['call','fold'])
def test_limped_multiway_barrels_and_roles(tmp_path,response):
    raw=multi(response).replace('T: Raise (NF) €40\nS: Call €30\nB: Call €20','T: Call €20\nS: Call €10\nB: Check')
    raw=raw.replace('€750','€690').replace('€630','€570')
    s=Store(tmp_path/'p.duckdb');p=tmp_path/'h.txt';p.write_text(raw,encoding='utf-8');r=s.import_file(p);assert r['added']==1,r
    for key in ('lp_mw_bet_btn','lp_mw_vs_bet_btn_sb','lp_mw_barrel_3_BC','lp_mw_barrel_4_BC','lp_mw_vs_barrel_4_BC_B'):
        _,pattern,fmt,pot=extension_patterns()[key];r=sequence_report(s,pattern,dict(format=fmt,pot_type=pot))
        assert r['opportunities']==1 and (r['samples'][0]['role_a'],r['samples'][0]['role_b'],r['samples'][0]['role_c'])==('T','S','B')
        assert 'CBET' not in r['samples'][0]['spot']
    s.close();reports=validate(tmp_path/'p.duckdb')
    assert not any(r[k] for r in reports.values() for k in ('missing','unexpected','mismatches'))


CASES=[
('raise_sb_btn_after_bb_call',['S: Raise (NF) €90','B: Call €90','T: Fold'],330,'T','fold'),
('raise_sb_btn_after_bb_fold',['S: Raise (NF) €90','B: Fold','T: Call €60'],300,'T','call'),
('reraise_bb_sb_after_btn_fold',['S: Raise (NF) €90','B: Raise (NF) €210','T: Fold','S: Call €120'],570,'S','call'),
('reraise_btn_sb_after_bb_call',['S: Raise (NF) €90','B: Call €90','T: Raise (NF) €210','S: Fold','B: Call €120'],630,'S','fold'),
('reraise_btn_bb_after_sb_fold',['S: Raise (NF) €90','B: Call €90','T: Raise (NF) €210','S: Fold','B: Call €120'],630,'B','call'),
('raise_bb_sb_after_btn_call',['S: Call €30','B: Raise (NF) €90','T: Call €60','S: Fold'],330,'S','fold'),
]


def raised(actions,pot,game=990):
    raw=preflop_hand(['T: Raise (NF) €40','S: Call €30','B: Call €20'],120,3,game).split('*** FLOP ***')[0]
    flop=['S: Check','B: Check','T: Bet €30']+actions
    active=[n for n in ('S','B','T') if n+': Fold' not in flop]
    body='*** FLOP *** [C2 D5 H9]\n'+'\n'.join(flop)+'\n'
    for st,board in [('TURN','S7'),('RIVER','CQ')]:body+=f'*** {st} *** [{board}]\n'+'\n'.join(n+': Check' for n in active)+'\n'
    return raw+body+f'*** SUMMARY ***\nTotal pot €{pot} Rake €0\n{active[0]}: wins €{pot}\n'


@pytest.mark.parametrize('key,actions,pot,actor,result',CASES)
def test_raise_opportunities_stop_before_result(tmp_path,key,actions,pot,actor,result):
    s=Store(tmp_path/'p.duckdb');p=tmp_path/'h.txt';p.write_text(raised(actions,pot),encoding='utf-8');r=s.import_file(p);assert r['added']==1,r
    _,pattern,fmt,pot_type=extension_patterns()[key];report=sequence_report(s,pattern,dict(format=fmt,pot_type=pot_type))
    assert report['opportunities']==1
    assert (report['samples'][0]['actor'],report['samples'][0]['result'])==(actor,result)
    s.close();reports=validate(tmp_path/'p.duckdb')
    assert not {k:r for k,r in reports.items() if r['missing'] or r['unexpected'] or r['mismatches']}


def test_real_extensions_fixture_conservation_and_oracle(tmp_path):
    from src.history import read_text
    from src.engine import replay
    path=Path(__file__).parent/'fixtures/extensions_real_anonymized.txt'
    hands,errors,_=read_text(path.read_bytes());assert len(hands)==7 and not errors
    for hand in hands:
        _,_,balance=replay(hand)
        assert balance['pot']==hand.pot==sum(hand.wins.values())+hand.rake
        assert sum(balance['remaining'].values())+hand.pot==sum(p['stack'] for p in hand.players)
        assert all(p['name'].startswith('PLAYER_') for p in hand.players)
    s=Store(tmp_path/'p.duckdb');r=s.import_file(path);assert r['added']==7 and r['rejected']==0;s.close()
    reports=validate(tmp_path/'p.duckdb')
    assert not {k:r for k,r in reports.items() if r['missing'] or r['unexpected'] or r['mismatches']}
