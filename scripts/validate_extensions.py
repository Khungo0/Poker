"""Read-only cross-check of limped pots and raise responses from original actions."""
import argparse,json
from pathlib import Path
from collections import Counter
import duckdb
from src.history import parse_hand
from src.multiway_extensions import extension_patterns
from src.sequences import matched_query
from scripts.validate_advanced import events,oracle as street_oracle


def oracle(hand):
    found=street_oracle(hand,limped=True)
    ev=events(hand);pre=[e for e in ev if e['street']==1]
    if hand.format!='3H' or [(e['position'],e['kind']) for e in pre]!=[('BTN','raise'),('SB','call'),('BB','call')]:return found
    roles={e['actor']:r for e,r in zip(pre,'ABC')};flop=[e for e in ev if e['street']==2]
    if len(flop)<5:return found
    sig=[(roles[e['actor']],'raise' if e['kind']=='check_raise' else e['kind']) for e in flop]
    if sig[:3]!=[('B','check'),('C','check'),('A','bet')]:return found
    def record(key,i):
        e=flop[i]
        if hand.known_cards.get(e['actor'],{}).get('source')!='dealt':found.setdefault(key,{})[(hand.hand_id,e['seq'])]=sig[i][1]
    if sig[3]==('B','raise'):
        if len(sig)>5 and sig[4][0]=='C' and sig[4][1] in ('fold','call','raise') and sig[5][0]=='A':
            c=sig[4][1];a=sig[5][1];record('raise_sb_btn_after_bb_'+c,5)
            if len(sig)>6 and sig[6][0]=='B':
                if c=='raise' and a in ('fold','call','raise'):record('reraise_bb_sb_after_btn_'+a,6)
                if c in ('fold','call') and a=='raise':
                    record('reraise_btn_sb_after_bb_'+c,6)
                    if c=='call' and len(sig)>7 and sig[6][1] in ('fold','call') and sig[7][0]=='C':record('reraise_btn_bb_after_sb_'+sig[6][1],7)
    elif sig[3] in (('B','call'),('B','fold')) and sig[4]==('C','raise'):
        b=sig[3][1]
        if len(sig)>5 and sig[5][0]=='A':
            record('raise_bb_btn_after_sb_'+b,5)
            if b=='call' and len(sig)>6 and sig[6][0]=='B' and sig[5][1] in ('fold','call','raise'):record('raise_bb_sb_after_btn_'+sig[5][1],6)
    return found


def validate(path):
    con=duckdb.connect(str(path),read_only=True)
    try:
        expected={k:{} for k in extension_patterns()}
        for raw, in con.execute("SELECT raw FROM hands WHERE format='3H' AND stake='EUR 5.00'").fetchall():
            for key,rows in oracle(parse_hand(raw)).items():
                if key in expected:expected[key].update(rows)
        reports={}
        for key,(_,pattern,fmt,pot) in extension_patterns().items():
            sql,args=matched_query(pattern,dict(format=fmt,pot_type=pot,stake='EUR 5.00'));cur=con.execute(sql,args);cols=[d[0] for d in cur.description];actual={}
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
