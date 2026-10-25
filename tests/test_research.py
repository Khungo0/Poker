import copy,json
from pathlib import Path
import pytest
from src.history import read_text,parse_hand,cents
from src.engine import replay,ReplayError
from src.store import Store
from src.research import explore,classify,leaks,save_strategy,import_reference,terminal_bet_ev

FIXTURE=Path(__file__).parent/'fixtures/ipoker_real_anonymized.txt'
HANDS=read_text(FIXTURE.read_bytes())[0]
BYID={h.hand_id:h for h in HANDS}

@pytest.mark.parametrize('hand',HANDS,ids=lambda h:h.hand_id)
def test_real_replay_conserves_every_cent(hand):
    oo,events,bal=replay(hand)
    assert bal['pot']==hand.pot==sum(hand.wins.values())+hand.rake
    assert sum(bal['remaining'].values())+bal['pot']==sum(p['stack'] for p in hand.players)
    assert all(e['remaining']>=0 for e in events)
    assert len({o['seq'] for o in oo})==len(oo)
    assert all(o['actor']!=o['opponent'] for o in oo)


def test_raise_to_increment_and_uncalled_return():
    h=BYID['ipoker:12543201521'];oo,ee,bal=replay(h)
    assert [e['delta'] for e in ee]==[8000,0,6000,0,17000,0]
    assert bal['pot']==17000
    assert [o['spot'] for o in oo]==['BTN_FIRST','SB_VS_RAISE','BB_VS_RAISE','DONK','CBET','VS_CBET']
    assert oo[-1]['facing_pct']==1
    assert oo[-1]['opponent']==h.players[1]['name']


def test_antes_allin_call_not_reraise():
    h=BYID['ipoker:12543199664'];oo,ee,bal=replay(h)
    assert ee[-1]['kind']=='call' and ee[-1]['allin']
    assert ee[-1]['delta']==12800
    assert oo[-1]['result']=='call'
    assert not oo[-1]['can_raise']
    assert bal['pot']==37100


def test_short_blind_call_uses_contestable_amount():
    h=BYID['ipoker:12545210094'];oo,ee,bal=replay(h)
    assert ee[0]['delta']==4000
    assert not oo[0]['can_raise']
    assert bal['pot']==20000


def test_unknown_cards_stay_unknown():
    hs=[h for h in HANDS if ' X]' in h.raw]
    assert hs
    assert any('?' in c['cards'] for h in hs for c in h.known_cards.values())
    for h in hs:
        oo,_,_=replay(h)
        unknown={p['name'] for p in h.players}-set(h.known_cards)
        assert all(not o['known_cards'] for o in oo if o['actor'] in unknown)


def test_bad_amount_and_out_of_turn_rejected():
    h=copy.deepcopy(HANDS[0]);idx=next(i for i,a in enumerate(h.actions) if a['kind']=='call');h.actions[idx]['amount']+=1
    with pytest.raises(ReplayError,match='Call amount'):replay(h)
    h=copy.deepcopy(HANDS[0]);idx=next(i for i,a in enumerate(h.actions) if a['street']==1)
    h.actions[idx],h.actions[idx+1]=h.actions[idx+1],h.actions[idx]
    with pytest.raises(ReplayError,match='out of turn'):replay(h)


def test_truncated_river_does_not_generate_observations():
    h=copy.deepcopy(BYID['ipoker:12543201556']);h.actions.pop()
    with pytest.raises(ReplayError):replay(h)


def test_import_transaction_duplicates_conflicts_errors(tmp_path):
    s=Store(tmp_path/'p.duckdb');r=s.import_file(FIXTURE)
    assert r['added']==len(HANDS) and r['rejected']==0
    before=s.totals();r2=s.import_file(FIXTURE);assert r2['already_imported'] and s.totals()==before
    renamed=tmp_path/'again.txt';renamed.write_bytes(FIXTURE.read_bytes()+b'\n')
    assert s.import_file(renamed)['duplicates']==len(HANDS)
    changed=tmp_path/'conflict.txt';changed.write_text(HANDS[0].raw.replace('03:28:50','03:28:51'), encoding="utf-8")
    assert s.import_file(changed)['conflicts']==1
    broken=tmp_path/'broken.txt';broken.write_text('not a history', encoding="utf-8");assert s.import_file(broken)['rejected']==1
    assert s.con.execute('SELECT count(*) FROM imports').fetchone()[0]==4
    assert len(list((tmp_path/'imports').glob('*.txt')))==4
    s.close()


def test_denominators_actor_opponent_and_filters(tmp_path):
    s=Store(tmp_path/'p.duckdb');s.import_file(FIXTURE)
    totals,rows=explore(s,{'spot':'BTN_FIRST','stake':'EUR 5.00'})
    oo=[o for h in HANDS for o in replay(h)[0] if o['spot']=='BTN_FIRST' and o['stake']=='EUR 5.00' and o['card_source']!='dealt']
    assert totals['opportunities']==len(oo)
    assert sum(r['cases'] for r in rows)==len(oo)
    actor=oo[0]['actor'];s.label(actor,'Reg')
    t,_=explore(s,{'population':'Reg','actor':actor});assert t['opportunities']>0
    t,_=explore(s,{'opponent_population':'Reg','opponent':actor});assert t['opportunities']>0
    with pytest.raises(ValueError):explore(s,{'bogus':'bad'})
    s.close()


def test_rules_baselines_strategies_and_reference(tmp_path):
    s=Store(tmp_path/'p.duckdb');s.import_file(FIXTURE)
    actor=HANDS[0].players[0]['name'];s.label(actor,'Fish')
    classify(s,[dict(category='Reg',metric='vpip',min_hands=30,low=0,high=1)])
    assert s.con.execute('SELECT category FROM labels WHERE player=?',[actor]).fetchone()[0]=='Fish'
    classify(s,[]);assert s.con.execute("SELECT count(*) FROM labels WHERE origin='auto'").fetchone()[0]==0
    baseline=dict(source='test only',filters={'spot':'BTN_FIRST'},action='fold',frequency=0,min_opportunities=30,min_players=2)
    # Not enough independent players/decisions: no finding is manufactured.
    assert leaks(s,[dict(baseline,min_opportunities=100000)])==[]
    with pytest.raises(ValueError):leaks(s,[dict(baseline,frequency=1.5)])
    save_strategy(s,'study',dict(population='Fish',filters={'spot':'BTN_FIRST','bb_eff':[10,15]},action='study call',rationale='test only'))
    assert s.documents('strategy')[0]['payload']['status'].startswith('Hipótesis')
    import_reference(s,'test',dict(version=1,source='test only',baselines=[baseline],ranges=[]))
    assert len(s.documents('baseline'))==1
    s.close()


def test_ev_explicit_conditional_model():
    r=terminal_bet_ev(100,50,50,100,0)
    assert r['ev']==25
    assert r['conditional_interval'][0]<25<r['conditional_interval'][1]
    with pytest.raises(ValueError):terminal_bet_ev(100,50,10,20,0)
    with pytest.raises(ValueError):cents('NaN')


def test_short_allin_does_not_reopen_raise():
    raw="""GAME #999000001 Version:26.7.1.14 Uncalled:Y Texas Hold'em NL  Tournament 2026-09-30 03:28:50/GMT
Table Info: Size: 3, Blinds: 10/20
Table Twister €5 SNG, 999, 998 (Tournament: Twister €5 SNG Buy-In: €4.65 + €0.35)
Seat 1: A (€1000 in chips)  DEALER
Seat 2: B (€150 in chips)
Seat 3: C (€1000 in chips)
B: Post SB €10
C: Post BB €20
*** HOLE CARDS ***
A: Raise (NF) €100
B: Allin €140
C: Call €130
A: Call €50
*** FLOP *** [C2 D3 H4]
C: Check
A: Check
*** TURN *** [S5]
C: Check
A: Check
*** RIVER *** [C6]
C: Check
A: Check
*** SUMMARY ***
Total pot €450 Rake €0
A: wins €450
"""
    h=parse_hand(raw);obs,_,_=replay(h)
    assert obs[2]['can_raise']
    assert not obs[3]['can_raise']
    assert obs[3]['eligible']==['fold','call']
    invalid=raw.replace('A: Call €50','A: Raise (NF) €300')
    with pytest.raises(ReplayError,match='not reopened'):replay(parse_hand(invalid))


def test_rebuild_preserves_originals_and_labels(tmp_path):
    s=Store(tmp_path/'p.duckdb');s.import_file(FIXTURE);s.label('manual','Reg');before=s.totals()
    assert s.rebuild_analysis()==before['observations']
    assert s.totals()==before
    assert s.con.execute('SELECT category FROM labels WHERE player=?',['manual']).fetchone()[0]=='Reg'
    s.close()


def test_overcovering_allin_is_economic_call():
    h=BYID['ipoker:12543204171'];obs,events,balance=replay(h)
    assert events[1]['declared_allin']
    assert events[1]['raw_delta']==76000
    assert events[1]['delta']==39500
    assert events[1]['kind']=='call'
    assert not obs[1]['can_raise']
    assert obs[1]['result']=='call'
    assert balance['pot']==113500


def test_delayed_cbet_and_probe_are_distinct():
    spots=[o['spot'] for h in HANDS for o in replay(h)[0]]
    assert 'DELAYED_CBET' in spots and 'PROBE' in spots
    assert 'VS_CBET' in spots


def test_population_excludes_hero_unless_requested(tmp_path):
    s=Store(tmp_path/'p.duckdb');s.import_file(FIXTURE)
    without,_=explore(s,{});all_,_=explore(s,{'include_hero':True})
    hero=s.con.execute("SELECT count(*) FROM observations WHERE card_source='dealt'").fetchone()[0]
    assert without['opportunities']+hero==all_['opportunities']
    s.close()
