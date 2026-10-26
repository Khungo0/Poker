"""Read-only oracle: raw chip actions + street states, independent of SQL patterns."""
import argparse,json
from pathlib import Path
from collections import Counter
import duckdb
from src.history import parse_hand
from src.postflop import SRP_LINES
from src.advanced_spots import advanced_patterns
from src.sequences import matched_query


def events(hand):
    seats=sorted(hand.players,key=lambda p:p['seat']);i=next(i for i,p in enumerate(seats) if p['dealer']);seats=seats[i:]+seats[:i]
    positions=('SB','BB') if hand.format=='HU' else ('BTN','SB','BB')
    pos={p['name']:r for p,r in zip(seats,positions)};remaining={p['name']:p['stack'] for p in seats}
    active=set(pos);paid=dict.fromkeys(pos,0);street=1;high=hand.bb;raises=0;checked=set();out=[]
    for seq,a in enumerate(hand.actions):
        n,k,amount,st=a['player'],a['kind'],a['amount'],a['street']
        if st==0:
            remaining[n]-=amount
            if k!='ante':paid[n]+=amount
            continue
        if st!=street:street=st;paid=dict.fromkeys(pos,0);high=0;checked=set()
        total=amount if k=='raise_to' else paid[n]+amount
        delta=total-paid[n] if k=='raise_to' else amount
        kind=k
        if k in ('allin','raise_to'):
            contestable=any(remaining[x]+paid[x]>high for x in active if x!=n)
            kind=('bet' if st>1 and high==0 else 'raise') if total>high and contestable else 'call'
        if kind=='call' and st==1 and not raises:kind='limp'
        if kind=='raise' and st==1 and delta==remaining[n]:kind='shove'
        if kind=='raise' and st>1 and n in checked:kind='check_raise'
        if any(remaining[x]>0 for x in active if x!=n) or high>paid[n]:out.append(dict(seq=seq,street=st,actor=n,position=pos[n],kind=kind))
        if k not in ('check','fold'):remaining[n]-=delta;paid[n]+=delta
        if kind in ('raise','shove','bet','check_raise'):high=total;raises+=st==1
        if k=='fold':active.remove(n)
        if k=='check':checked.add(n)
    return out


def oracle(hand,limped=False):
    ev=events(hand);pre=[e for e in ev if e['street']==1];found={}
    def record(key,e):
        if hand.known_cards.get(e['actor'],{}).get('source')!='dealt':
            if limped:key='lp_'+key.replace('cbet','bet_btn')
            found.setdefault(key,{})[(hand.hand_id,e['seq'])]='raise' if e['kind']=='check_raise' else e['kind']
    post={st:[e for e in ev if e['street']==st] for st in (2,3,4)}
    kinds=lambda es:[e['kind'] for e in es]
    if hand.format=='3H' and [(e['position'],e['kind']) for e in pre]==([('BTN','limp'),('SB','limp'),('BB','check')] if limped else [('BTN','raise'),('SB','call'),('BB','call')]):
        roles={e['actor']:r for e,r in zip(pre,'ABC')};flop=post[2]
        for i,e in enumerate(flop):
            hist=flop[:i];h=kinds(hist);role=roles[e['actor']];rh=''.join(roles[x['actor']] for x in hist)
            if i==0 and role=='B':record('mw_sb_lead',e)
            if h==['check'] and rh=='B' and role=='C':record('mw_bb_lead',e)
            if h==['check','check'] and rh=='BC' and role=='A':record('mw_cbet',e)
            if h==['check','check','bet'] and rh=='BCA' and role=='B':record('mw_vs_cbet_sb',e)
            if rh=='BCAB' and role=='C' and len(h)==4 and h[:3]==['check','check','bet'] and h[3] in ('call','fold','check_raise'):record('mw_vs_cbet_bb_'+h[3],e)
            if h==['bet'] and rh=='B' and role=='C':record('mw_vs_sb_lead_bb',e)
            if rh=='BC' and role=='A' and len(h)==2 and h[0]=='bet' and h[1] in ('call','fold'):record('mw_vs_sb_lead_btn_'+h[1],e)
            if h==['check','bet'] and rh=='BC' and role=='A':record('mw_vs_bb_lead_btn',e)
            if rh=='BCA' and role=='B' and len(h)==3 and h[:2]==['check','bet'] and h[2] in ('call','fold'):record('mw_vs_bb_lead_sb_'+h[2],e)
        if len(flop)==5 and ''.join(roles[e['actor']] for e in flop)=='BCABC' and kinds(flop)[:3]==['check','check','bet'] and all(e['kind'] in ('call','fold') for e in flop[3:]):
            alive=tuple(roles[e['actor']] for e in flop[3:] if e['kind']=='call');chain=bool(alive)
            for st in (3,4):
                street=post[st];tag=''.join(alive);calls=[];bettor=False
                if not chain:break
                for i,e in enumerate(street):
                    role=roles[e['actor']]
                    if role=='A' and all(x['kind']=='check' for x in street[:i]):record(f'mw_barrel_{st}_{tag}',e);bettor=e['kind']=='bet'
                    elif bettor and role in alive and tuple(calls)==alive[:alive.index(role)]:
                        record(f'mw_vs_barrel_{st}_{tag}_{role}',e)
                        if e['kind']=='call':calls.append(role)
                        else:bettor=False
                chain=bettor and tuple(calls)==alive
    if limped:return found
    for key,fmt,prefix,ip in SRP_LINES:
        if hand.format!=fmt or [(e['position'],e['kind']) for e in pre]!=[(p,k) for r,p,k in prefix]:continue
        roles={e['actor']:r for e,(r,p,k) in zip(pre,prefix)};oop,iprole=('B','A') if ip else ('A','B')
        signature=lambda es:[(roles[e['actor']],e['kind']) for e in es]
        if signature(post[3])!=[(oop,'check'),(iprole,'check')]:continue
        fl=signature(post[2]);name='missed_turn' if fl==([(oop,'check')] if ip else [])+[('A','bet'),('B','call')] else 'two_checked' if fl==[(oop,'check'),(iprole,'check')] else None
        if not name:continue
        for i,e in enumerate(post[4]):
            h=kinds(post[4][:i]);suffix='lead' if i==0 else 'vs_lead' if h==['bet'] else 'stab' if h==['check'] else 'vs_stab' if h==['check','bet'] else None
            if suffix:record(f'river_{key}_{name}_{suffix}',e)
    return found


def validate(path):
    con=duckdb.connect(str(path),read_only=True)
    try:
        expected={k:{} for k in advanced_patterns()}
        for raw, in con.execute("SELECT raw FROM hands WHERE stake='EUR 5.00'").fetchall():
            for key,rows in oracle(parse_hand(raw)).items():expected[key].update(rows)
        reports={}
        for key,(title,p,fmt) in advanced_patterns().items():
            sql,args=matched_query(p,dict(format=fmt,stake='EUR 5.00',pot_type='srp'));cur=con.execute(sql,args);cols=[d[0] for d in cur.description]
            actual={}
            for values in cur.fetchall():
                r=dict(zip(cols,values));actual[(r['hand_id'],r['seq'])]='raise' if r['result']=='check_raise' else r['result']
            exp=expected[key];reports[key]=dict(n=len(actual),counts=dict(Counter(actual.values())),missing=sorted(exp.keys()-actual.keys()),unexpected=sorted(actual.keys()-exp.keys()),mismatches=sorted(k for k in exp.keys()&actual.keys() if exp[k]!=actual[k]))
        return reports
    finally:con.close()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--db',required=True);p.add_argument('--output',required=True);a=p.parse_args();r=validate(a.db)
    Path(a.output).write_text(json.dumps(r,indent=2),encoding='utf-8');bad={k:v for k,v in r.items() if v['missing'] or v['unexpected'] or v['mismatches']}
    print(json.dumps(dict(reports=len(r),opportunities=sum(v['n'] for v in r.values()),discrepancies=bad),indent=2))
    if bad:raise SystemExit(1)
