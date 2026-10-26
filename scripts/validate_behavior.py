"""Read-only per-player validation against original HU actions, without SQL spots."""
import argparse,json
from collections import Counter,defaultdict
from pathlib import Path
import duckdb
from src.history import parse_hand
from src.behavior import player_metrics
from scripts.validate_advanced import events
from scripts.validate_preflop_presets import oracle as pre_oracle


class ReadOnly:
    def __init__(self,path):self.con=duckdb.connect(str(path),read_only=True)
    def rows(self,sql,args=None):
        c=self.con.execute(sql,args or []);names=[d[0] for d in c.description];return [dict(zip(names,r)) for r in c.fetchall()]


def validate(path):
    s=ReadOnly(path)
    try:
        expected=defaultdict(lambda:[0,0]);volume=defaultdict(lambda:dict(hands=set(),tournaments=set(),days=set()))
        def count(player,metric,success):expected[player,metric][0]+=int(success);expected[player,metric][1]+=1
        for raw, in s.con.execute("SELECT raw FROM hands WHERE format='HU' AND stake='EUR 5.00'").fetchall():
            h=parse_hand(raw);ev=events(h);pre=[e for e in ev if e['street']==1];per_player=defaultdict(list)
            hero=lambda n:h.known_cards.get(n,{}).get('source')=='dealt'
            for e in pre:
                if not hero(e['actor']):per_player[e['actor']].append(e)
            for player,rows in per_player.items():
                v=volume[player];v['hands'].add(h.hand_id);v['tournaments'].add(h.tournament);v['days'].add(h.played_at[:10])
                voluntary=any(e['kind'] in ('limp','call','raise','shove') for e in rows);raised=any(e['kind'] in ('raise','shove') for e in rows)
                count(player,'vpip',voluntary);count(player,'pfr',raised);count(player,'vpip_pfr_gap',voluntary and not raised)
            if pre and pre[0]['position']=='SB' and not hero(pre[0]['actor']):count(pre[0]['actor'],'hu_limp',pre[0]['kind']=='limp')
            selected=pre_oracle(h).get('hu_bb_vs_minraise')
            if selected:
                e=next(e for e in ev if e['seq']==selected[1]);count(e['actor'],'bb_fold_minraise',e['kind']=='fold')
            post={st:[e for e in ev if e['street']==st] for st in (2,3,4)};bets=[];valid=True
            for st in (2,3):
                aggression=[e for e in post[st] if e['kind'] in ('bet','raise','check_raise')]
                if len(aggression)!=1 or aggression[0]['kind']!='bet':valid=False;break
                bets.append(aggression[0]['actor'])
            if valid and len(set(bets))==1:
                rv=post[4];index=next((i for i,e in enumerate(rv) if e['kind'] in ('bet','raise','check_raise')),None)
                if index is not None and rv[index]['actor']==bets[0] and rv[index]['kind']=='bet' and index+1<len(rv):
                    response=rv[index+1]
                    if not hero(response['actor']):count(response['actor'],'fold_third',response['kind']=='fold')
        actual={(r['player'],r['metric']):r for r in player_metrics(s,dict(format='HU',stake='EUR 5.00'))}
        discrepancies=[];keys=('vpip','pfr','vpip_pfr_gap','hu_limp','bb_fold_minraise','fold_third')
        for key in set(expected)|{k for k in actual if k[1] in keys}:
            observed=actual.get(key);pair=[observed['cases'],observed['opportunities']] if observed else [0,0]
            if pair!=expected.get(key,[0,0]):discrepancies.append(dict(player=key[0],metric=key[1],expected=expected.get(key,[0,0]),actual=pair))
        for player,v in volume.items():
            for metric,values in v.items():
                row=actual.get((player,metric))
                if not row or row.get('value')!=len(values):discrepancies.append(dict(player=player,metric=metric))
        totals={metric:dict(cases=sum(v[0] for (p,m),v in expected.items() if m==metric),opportunities=sum(v[1] for (p,m),v in expected.items() if m==metric)) for metric in keys}
        return dict(players=len(volume),frequency_metrics=totals,discrepancies=discrepancies)
    finally:s.con.close()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--db',required=True);p.add_argument('--output',required=True);a=p.parse_args();report=validate(a.db);Path(a.output).write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
    if report['discrepancies']:raise SystemExit(1)
