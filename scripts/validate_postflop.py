"""Independent raw-action state machine for SRP report validation (read only)."""
import argparse,json
from collections import Counter
from pathlib import Path
import duckdb
from src.history import parse_hand
from src.postflop import SRP_LINES
from src.presets import PRESETS_BY_KEY
from src.sequences import matched_query


def oracle(hand):
    seated=sorted(hand.players,key=lambda p:p['seat']);button=next(i for i,p in enumerate(seated) if p['dealer'])
    ordered=seated[button:]+seated[:button]
    positions=['SB','BB'] if hand.format=='HU' else ['BTN','SB','BB']
    pos={p['name']:position for p,position in zip(ordered,positions)}
    cap={p['name']:p['stack'] for p in ordered};paid=dict.fromkeys(cap,0);pre=[]
    for seq,a in enumerate(hand.actions):
        n,k,amount=a['player'],a['kind'],a['amount']
        if a['street']==0:
            if k=='ante':cap[n]-=amount
            else:paid[n]+=amount
        elif a['street']==1:
            total=amount if k=='raise_to' else paid[n]+amount
            kind='raise' if k=='raise_to' and total<cap[n] else 'call' if k in ('call','allin') and total<=max(hand.bb,max(paid.values())) else k
            pre.append((n,kind));paid[n]=total if k not in ('fold','check') else paid[n]
    line=next((l for l in SRP_LINES if l[1]==hand.format and [(pos[n],k) for n,k in pre]==[(p,k) for r,p,k in l[2]]),None)
    if line is None:return {}
    key,_,prefix,ip=line;roles={role:n for (role,_,_),(n,_) in zip(prefix,pre)};A=roles['A'];B=roles['B'];found={}
    chain=0;checked_flop=False;remaining={n:cap[n]-paid[n] for n in cap}
    for street in (2,3,4):
        actions=[(seq,a) for seq,a in enumerate(hand.actions) if a['street']==street]
        history=[];bet_tag=None;raised_cbet=False;this_chain=0;contributed=dict.fromkeys(cap,0)
        for seq,a in actions:
            actor,kind=a['player'],a['kind'];tag=None
            checks=all(x['kind']=='check' for x in history)
            amount=a['amount'];total=amount if kind=='raise_to' else contributed[actor]+amount
            if kind in ('allin','raise_to'):
                high=max(contributed.values())
                contestable=any(remaining[n]+contributed[n]>high for n in (A,B) if n!=actor)
                outcome=('bet' if high==0 else 'raise') if total>high and contestable else 'call'
            else:outcome=kind
            delta=total-contributed[actor] if kind=='raise_to' else amount
            remaining[actor]-=delta;contributed[actor]+=delta
            a=dict(a,kind=outcome);kind=outcome
            if checks:
                if street==2:
                    if actor==A:tag='cbet'
                    elif ip:tag='donk'
                    else:tag='flop_stab'
                elif street==3 and checked_flop:
                    if actor==A:tag='delayed_cbet'
                    elif ip:tag='probe'
                    else:tag='turn_stab'
                elif chain==street-2 and actor==A:tag=f'barrel_{street-1}'
            elif history[-1]['kind']=='bet' and bet_tag:
                tag='vs_'+bet_tag
                if street==2 and bet_tag=='cbet' and outcome=='raise':raised_cbet=True
            elif raised_cbet and actor==A:
                tag='vs_flop_raise';raised_cbet=False
            if tag and hand.known_cards.get(actor,{}).get('source')!='dealt':
                found.setdefault(f'srp_{key}_{tag}',{})[(hand.hand_id,seq)]=outcome
            if kind=='bet':bet_tag=tag
            history.append(a)
        trimmed=[a for a in history if a['kind']!='check']
        if len(trimmed)==2 and trimmed[0]['player']==A and trimmed[0]['kind']=='bet' and trimmed[1]['player']==B and trimmed[1]['kind'] in ('call','allin') and trimmed[1]['amount']<=trimmed[0]['amount']:
            if street==2 or chain==street-2:this_chain=street-1
        chain=this_chain
        if street==2:checked_flop=bool(history) and all(a['kind']=='check' for a in history)
    return found


def validate(path,stake='EUR 5.00'):
    con=duckdb.connect(str(path),read_only=True)
    try:
        expected={k:{} for k in PRESETS_BY_KEY if k.startswith('srp_')}
        for raw, in con.execute('SELECT raw FROM hands WHERE stake=?',[stake]).fetchall():
            for key,rows in oracle(parse_hand(raw)).items():expected[key].update(rows)
        reports={}
        for key,exp in expected.items():
            p=PRESETS_BY_KEY[key];sql,args=matched_query(p.pattern,dict(format=p.format,stake=stake,pot_type='srp'))
            c=con.execute(sql,args);columns=[d[0] for d in c.description]
            actual={}
            for values in c.fetchall():
                r=dict(zip(columns,values));actual[(r['hand_id'],r['seq'])]='raise' if r['result']=='check_raise' else r['result']
            reports[key]=dict(opportunities=len(actual),counts=dict(Counter(actual.values())),missing=sorted(exp.keys()-actual.keys()),unexpected=sorted(actual.keys()-exp.keys()),mismatches=sorted(k for k in exp.keys()&actual.keys() if exp[k]!=actual[k]))
        return reports
    finally:con.close()


def main():
    p=argparse.ArgumentParser();p.add_argument('--db',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    reports=validate(a.db);Path(a.output).write_text(json.dumps(reports,indent=2),encoding='utf-8')
    print(json.dumps(dict(reports=len(reports),opportunities=sum(r['opportunities'] for r in reports.values()),discrepancies={k:r for k,r in reports.items() if r['missing'] or r['unexpected'] or r['mismatches']}),indent=2))
    if any(r['missing'] or r['unexpected'] or r['mismatches'] for r in reports.values()):raise SystemExit(1)
if __name__=='__main__':main()
