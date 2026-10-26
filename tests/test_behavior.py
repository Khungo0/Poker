from pathlib import Path
import pytest
from src.behavior import player_metrics,preview_rules,apply_rules,save_population,evaluate
from src.research import explore
from src.store import Store
from test_sequences import hand
from test_presets import preflop_hand


def import_raw(s,path,raw):
    path.write_text(raw,encoding='utf-8');r=s.import_file(path);assert r['added']==1,r


def condition(metric='hu_limp',low=0,high=1,n=30):return dict(metric=metric,low=low,high=high,min_opportunities=n)


def test_metrics_exact_opportunities(tmp_path):
    s=Store(tmp_path/'p.duckdb')
    import_raw(s,tmp_path/'a.txt',hand('Call €80'))
    import_raw(s,tmp_path/'b.txt',preflop_hand(['S: Raise (NF) €40','B: Fold'],40,game=801))
    metrics={(r['player'],r['metric']):r for r in player_metrics(s,{'format':'HU'})}
    assert metrics['A','hu_limp']['cases']==1 and metrics['A','hu_limp']['opportunities']==1
    assert metrics['A','vpip']['cases']==1
    assert metrics['A','pfr']['cases']==0
    assert metrics['B','bb_fold_minraise']['cases']==1
    assert metrics['B','bb_fold_minraise']['opportunities']==1
    assert metrics['B','third_barrel']['opportunities']==1
    assert metrics['A','fold_third']['opportunities']==1 and metrics['A','fold_third']['cases']==0
    assert metrics['B','days']['value']==1
    assert not player_metrics(s,{'format':'3H'})
    s.close()


def test_three_valued_rules_manual_priority_groups_and_rollback(tmp_path,monkeypatch):
    s=Store(tmp_path/'p.duckdb')
    for i in range(31):import_raw(s,tmp_path/f'{i}.txt',hand(game=i))
    combined=dict(op='AND',conditions=[condition(),dict(metric='hands',low=30,high=100)])
    rules=[dict(name='Test only',category='Fish',profile='Calling station',condition=combined,weight=2)]
    s.label('A','Reg');before=s.con.execute('SELECT * FROM labels').fetchall()
    preview=preview_rules(s,rules,{'format':'HU'})
    assert next(r for r in preview if r['player']=='A')['status']=='Manual protegida'
    assert next(r for r in preview if r['player']=='A')['profile'] is None
    assert s.con.execute('SELECT * FROM labels').fetchall()==before
    # B has no SB limp opportunities; unknown must never turn into a 0% value.
    assert next(r for r in preview if r['player']=='B')['status']=='Evidencia insuficiente'
    assert evaluate(condition(low=0,high=.2),{})[0] is None
    snapshot=save_population(s,'Limpers',combined,{'format':'HU'})
    assert snapshot['members']==['A'] and s.con.execute('SELECT * FROM labels').fetchall()==before
    assert explore(s,{'actor_group':'Limpers'})[0]['opportunities']>0
    assert explore(s,{'actor_group':'missing'})[0]['opportunities']==0
    assert explore(s,{'opponent_group':'Limpers'})[0]['opportunities']>0
    broad=[dict(category='Fish',condition=condition('vpip'),weight=1)]
    apply_rules(s,broad);assert s.con.execute("SELECT category FROM labels WHERE player='A'").fetchone()[0]=='Reg'
    assert s.con.execute("SELECT category FROM labels WHERE player='B'").fetchone()[0]=='Fish'
    conflicting=broad+[dict(category='Reg',condition=condition('vpip'))]
    assert next(r for r in preview_rules(s,conflicting) if r['player']=='B')['status']=='Conflicto'
    before=s.con.execute('SELECT * FROM labels ORDER BY player').fetchall();original=s.save_document
    def fail(kind,name,payload):
        if kind=='behavior_rules':raise RuntimeError('Synthetic write failure')
        return original(kind,name,payload)
    monkeypatch.setattr(s,'save_document',fail)
    with pytest.raises(RuntimeError):apply_rules(s,conflicting)
    assert s.con.execute('SELECT * FROM labels ORDER BY player').fetchall()==before
    s.close()


def test_multivariable_undo_preserves_later_manual_labels(tmp_path):
    from src.behavior import undo_classification
    s=Store(tmp_path/'p.duckdb')
    for i in range(31):import_raw(s,tmp_path/f'{i}.txt',hand(game=i))
    rules=[dict(category='Fish',condition=condition('vpip'))]
    before=s.con.execute('SELECT * FROM labels').fetchall();apply_rules(s,rules)
    run=s.documents('classification_run')[0]['name'];undo_classification(s,run)
    assert s.con.execute('SELECT * FROM labels').fetchall()==before
    apply_rules(s,rules);run=next(d['name'] for d in s.documents('classification_run') if not d['payload'].get('undone_at'))
    s.label('A','Reg')
    with pytest.raises(ValueError,match='posteriores'):undo_classification(s,run)
    assert s.con.execute("SELECT category,origin FROM labels WHERE player='A'").fetchone()==('Reg','manual')
    s.close()


def test_nested_rules_and_unknown_evidence():
    from src.behavior import validate_condition
    metrics={'hands':dict(value=50)}
    tree=dict(op='OR',conditions=[condition('vpip'),dict(metric='hands',low=40,high=60)])
    validate_condition(tree);assert evaluate(tree,metrics)[0] is True
    tree['op']='AND';assert evaluate(tree,metrics)[0] is None
    with pytest.raises(ValueError):validate_condition(dict(metric='vpip',low=0,high=1,min_opportunities=5))


def test_first_decision_context_and_hero_exclusion(tmp_path):
    s=Store(tmp_path/'p.duckdb')
    import_raw(s,tmp_path/'h.txt',hand().replace('*** HOLE CARDS ***','*** HOLE CARDS ***\nDealt to A [CA DK]'))
    rows=player_metrics(s,{'format':'HU'});assert not any(r['player']=='A' for r in rows)
    rows=player_metrics(s,{'format':'HU','include_hero':True,'initial_eff_bb':[24,26]});assert any(r['player']=='A' for r in rows)
    assert not player_metrics(s,{'initial_eff_bb':[5,10]})
    import_raw(s,tmp_path/'3h.txt',preflop_hand(['T: Raise (NF) €40','S: Fold','B: Call €20'],90,3,game=999))
    rows=player_metrics(s,{'format':'3H','opponent_population':'Sin clasificar'})
    assert not any(r['player']=='T' and r['metric']=='vpip' for r in rows) # No unique opponent at BTN opening.
    s.close()


def test_real_metrics_against_raw_oracle(tmp_path):
    from scripts.validate_behavior import validate
    s=Store(tmp_path/'p.duckdb');s.import_file(Path(__file__).parent/'fixtures/ipoker_real_anonymized.txt');s.close()
    report=validate(tmp_path/'p.duckdb')
    assert report['players']>0 and report['discrepancies']==[]
