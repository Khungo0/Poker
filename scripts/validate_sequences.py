"""Independent raw-action oracle for the required HU limped triple-barrel spot.
Run against a local database; emits aggregates and IDs, never original names.
"""
import argparse,json
from pathlib import Path
from collections import Counter
from src.store import Store
from src.history import parse_hand
from src.sequences import limped_barrels,matched_query,sequence_report


def oracle(hand):
    if hand.format!='HU':return None
    pre=[a for a in hand.actions if a['street']==1]
    if len(pre)!=2 or [a['kind'] for a in pre]!=['call','check']:return None
    aggressor=defender=None
    for street in (2,3,4):
        actions=[a for a in hand.actions if a['street']==street]
        if actions and actions[0]['kind']=='check':actions=actions[1:]
        if len(actions)<2 or actions[0]['kind']!='bet':return None
        bet,response=actions[:2]
        if aggressor is None:aggressor=bet['player'];defender=response['player']
        if bet['player']!=aggressor or response['player']!=defender or aggressor==defender:return None
        if street<4:
            if len(actions)!=2 or response['kind'] not in ('call','allin'):return None
        else:
            if hand.known_cards.get(defender,{}).get('source')=='dealt':return None
            kind=response['kind']
            if kind=='allin':kind='raise' if response['amount']>bet['amount'] else 'call'
            elif kind=='raise_to':kind='raise'
            return kind if kind in ('fold','call','raise') else None


def main():
    p=argparse.ArgumentParser();p.add_argument('--db',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    s=Store(a.db);expected={}
    for ident,raw in s.con.execute("SELECT hand_id,raw FROM hands WHERE format='HU' AND stake='EUR 5.00'").fetchall():
        outcome=oracle(parse_hand(raw))
        if outcome:expected[ident]=outcome
    sql,args=matched_query(limped_barrels(),dict(format='HU',pot_type='limped',stake='EUR 5.00'))
    actual={r['hand_id']:'raise' if r['result']=='check_raise' else r['result'] for r in s.rows(sql,args)}
    report=dict(oracle_opportunities=len(expected),query_opportunities=len(actual),counts=dict(Counter(expected.values())),missing=sorted(expected.keys()-actual.keys()),unexpected=sorted(actual.keys()-expected.keys()),outcome_mismatches=[k for k in expected.keys() & actual.keys() if expected[k]!=actual[k]])
    Path(a.output).write_text(json.dumps(report,indent=2), encoding="utf-8");print(json.dumps(report,indent=2));s.close()
    if expected!=actual:raise SystemExit(1)
if __name__=='__main__':main()
