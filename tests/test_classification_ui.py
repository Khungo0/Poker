from pathlib import Path
import pytest
from src.store import Store
from src.research import classify,classification_preview
from src.sequences import compare_reports
from test_sequences import hand


def sample(tmp_path):
    s=Store(tmp_path/'p.duckdb')
    for i in range(31):
        p=tmp_path/f'{i}.txt';p.write_text(hand(game=i),encoding='utf-8');s.import_file(p)
    return s


def test_preview_conflicts_manual_and_atomic_rollback(tmp_path,monkeypatch):
    s=sample(tmp_path);s.label('A','Fish',profile='Calling station')
    rule=dict(category='Reg',metric='vpip',low=0,high=1,min_hands=30)
    before=s.con.execute('SELECT * FROM labels').fetchall();preview=classification_preview(s,[rule])
    assert s.con.execute('SELECT * FROM labels').fetchall()==before
    assert next(r for r in preview if r['player']=='A')['status']=='Manual protegida'
    assert classify(s,[rule])==1
    assert s.con.execute("SELECT category FROM labels WHERE player='A'").fetchone()[0]=='Fish'
    assert next(r for r in classification_preview(s,[rule,dict(rule,category='Fish')]) if r['player']=='B')['status']=='Conflicto'
    old=s.con.execute('SELECT * FROM labels ORDER BY player').fetchall();old_history=s.con.execute('SELECT count(*) FROM label_history').fetchone()
    original=s.save_document
    def fail(kind,name,payload):
        if kind=='rules':raise RuntimeError('Synthetic write failure')
        return original(kind,name,payload)
    monkeypatch.setattr(s,'save_document',fail)
    with pytest.raises(RuntimeError):classify(s,[])
    assert s.con.execute('SELECT * FROM labels ORDER BY player').fetchall()==old
    assert s.con.execute('SELECT count(*) FROM label_history').fetchone()==old_history
    monkeypatch.setattr(s,'save_document',original);classify(s,[])
    assert s.con.execute("SELECT count(*) FROM documents WHERE kind='player_profile' AND name='B'").fetchone()[0]==0
    s.close()


def test_comparison_zero_cases_are_not_missing_sample():
    a=dict(opportunities=10,players=4,rows=[dict(street=4,result='fold',cases=10)])
    b=dict(opportunities=20,players=6,rows=[dict(street=4,result='call',cases=20)])
    rows=compare_reports(a,b);fold=next(r for r in rows if r['action']=='fold')
    assert fold['difference_pp']==100 and fold['b_frequency']==0 and fold['b_high']>0
    assert compare_reports(a,dict(opportunities=0,players=0,rows=[]))[0]['difference_pp'] is None


def test_replayer_targets_decision_without_showdown(tmp_path):
    from PySide6.QtWidgets import QApplication
    from src.replayer import Replayer
    app=QApplication.instance() or QApplication([])
    s=sample(tmp_path);row=s.rows("SELECT seq FROM observations WHERE street=4 AND actor='A' LIMIT 1")[0]
    player=Replayer(hand());player.seek_decision(row['seq']);frame=player.frames[player.slider.value()]
    assert frame['street']==4 and frame['pot']==24000
    assert all(cards==['?','?'] for cards in frame['cards'].values())
    assert sum(frame['stacks'].values())+frame['pot']==100000
    player.close();s.close()
