"""Population queries, conservative rule labels and explicit reference comparisons."""
import json, math
from .mathutils import wilson

FILTERS={'spot','street','position','format','stake','texture','previous','modality','actor','opponent','board','path','can_raise','check_raise_opportunity'}
RANGES={'bb_eff','bb_eff_min','facing_bb','facing_pct','size_bb','size_pct'}


def selection(filters):
    clauses=[] if filters.get('include_hero',False) else ["o.card_source <> 'dealt'"]; args=[]
    for key,value in filters.items():
        if key=='include_hero':
            if not isinstance(value,bool):raise ValueError('include_hero must be boolean')
            continue
        if value is None or value=='Todos': continue
        if key in FILTERS: clauses.append(f'o."{key}"=?'); args.append(value)
        elif key in RANGES:
            if len(value)!=2 or not all(math.isfinite(float(v)) for v in value) or value[0]>value[1]: raise ValueError('Invalid range')
            clauses.append(f'o."{key}" BETWEEN ? AND ?'); args.extend(value)
        elif key in ('population','opponent_population'):
            alias='l' if key=='population' else 'lo'
            clauses.append(f"COALESCE({alias}.category,'Sin clasificar')=?"); args.append(value)
        else: raise ValueError('Unsupported filter '+key)
    return ' AND '.join(clauses) or 'TRUE',args


FROM="FROM observations o LEFT JOIN labels l ON l.player=o.actor LEFT JOIN labels lo ON lo.player=o.opponent"


def explore(store,filters):
    where,args=selection(filters)
    rows=store.rows('''SELECT result,count(*) AS cases FROM observations o
        LEFT JOIN labels l ON l.player=o.actor LEFT JOIN labels lo ON lo.player=o.opponent
        WHERE '''+where+' GROUP BY result ORDER BY cases DESC',args)
    totals=store.rows('SELECT count(*) AS opportunities,count(DISTINCT actor) AS players,count(DISTINCT session) AS tournaments '+FROM+' WHERE '+where,args)[0]
    n=totals['opportunities']
    concentration=store.con.execute('SELECT max(n) FROM (SELECT count(*) n '+FROM+' WHERE '+where+' GROUP BY actor)',args).fetchone()[0] or 0
    totals['largest_player_share']=concentration/n if n else None
    for r in rows:
        k=r['cases']; lo,hi=wilson(k,n); r.update(opportunities=n,frequency=k/n,ci_low=lo,ci_high=hi)
    return totals,rows


def player_profiles(store):
    return store.rows('''WITH per_hand AS (
        SELECT actor,hand_id,bool_or(result IN ('call','limp','raise','shove')) voluntary,
        bool_or(result IN ('raise','shove')) raised FROM observations WHERE street=1 AND card_source<>'dealt' GROUP BY actor,hand_id)
        SELECT actor AS player,count(*) AS hands,sum(CAST(voluntary AS INTEGER)) AS vpip_cases,
        sum(CAST(raised AS INTEGER)) AS pfr_cases,avg(CAST(voluntary AS INTEGER)) AS vpip,
        avg(CAST(raised AS INTEGER)) AS pfr,COALESCE(l.category,'Sin clasificar') category,
        l.origin,l.confidence,l.reason FROM per_hand LEFT JOIN labels l ON actor=l.player
        GROUP BY ALL ORDER BY hands DESC''')


def classify(store,rules):
    # Confidence is evidence strength of a rule, never a calibrated P(Reg/Fish).
    for rule in rules:
        if rule['category'] not in ('Reg','Fish') or rule['metric'] not in ('vpip','pfr'): raise ValueError('Invalid rule')
        if rule['min_hands']<30 or not 0<=rule['low']<=rule['high']<=1: raise ValueError('Invalid rule limits')
    store.con.execute("DELETE FROM labels WHERE origin='auto'")
    assigned=0
    for p in player_profiles(store):
        if p['origin']=='manual': continue
        matches=[]
        for r in rules:
            if p['hands']<r['min_hands']: continue
            lo,hi=wilson(p[r['metric']+'_cases'],p['hands'])
            if lo>=r['low'] and hi<=r['high']: matches.append(r)
        if len({r['category'] for r in matches})!=1: continue
        r=matches[0]; lo,hi=wilson(p[r['metric']+'_cases'],p['hands'])
        store.label(p['player'],r['category'],'auto',1-(hi-lo),f"Regla {r['metric']}; IC95 [{lo:.3f}, {hi:.3f}]; n={p['hands']}. Confianza heurística, no probabilidad de clase.")
        assigned+=1
    store.save_document('rules','active',rules)
    return assigned


def validate_baseline(b):
    selection(b['filters'])
    if any(k in b['filters'] for k in ('size_bb','size_pct')): raise ValueError('Use facing size for baselines; own size conditions on outcome')
    if b.get('action') not in {'fold','call','limp','raise','shove','check','bet','check_raise'}: raise ValueError('Unsupported action')
    if not b.get('source') or not b.get('action') or not b['filters'].get('spot'): raise ValueError('Source, action and exact spot required')
    if not math.isfinite(b['frequency']) or not 0<=b['frequency']<=1: raise ValueError('Invalid frequency')
    if b.get('min_opportunities',100)<30 or b.get('min_players',5)<2: raise ValueError('Insufficient minimum sample')
    return b


def leaks(store,baselines):
    out=[]
    for b in baselines:
        validate_baseline(b); totals,rows=explore(store,b['filters']); n=totals['opportunities']
        if n<b.get('min_opportunities',100) or totals['players']<b.get('min_players',5): continue
        k=next((r['cases'] for r in rows if r['result']==b['action']),0); lo,hi=wilson(k,n)
        if lo<=b['frequency']<=hi: continue
        out.append(dict(name=b.get('name',b['action']),source=b['source'],action=b['action'],observed=k/n,reference=b['frequency'],difference=k/n-b['frequency'],ci_low=lo,ci_high=hi,**totals,conclusion='Desviación exploratoria; EV no demostrado'))
    return sorted(out,key=lambda x:abs(x['difference']),reverse=True)


def save_strategy(store,name,payload):
    if payload.get('population') not in ('Reg','Fish'): raise ValueError('Choose Reg or Fish')
    selection(payload['filters'])
    if not payload.get('action') or not payload.get('rationale'): raise ValueError('Action and rationale required')
    payload['status']='Hipótesis de estudio; EV no demostrado'
    store.save_document('strategy',name,payload)


def import_reference(store,name,data):
    """Versioned adapter boundary. Never interprets arbitrary native solver files."""
    if data.get('version')!=1 or not data.get('source'): raise ValueError('Reference needs version=1 and source')
    for b in data.get('baselines',[]): validate_baseline(dict(b,source=data['source']))
    for r in data.get('ranges',[]):
        selection(r['filters'])
        for combo,freq in r['hands'].items():
            import re
            if not re.fullmatch(r'(?:[2-9TJQKA]{2}[so]?)',combo) or not 0<=freq<=1: raise ValueError('Invalid range')
    store.save_document('reference',name,data)
    for i,b in enumerate(data.get('baselines',[])): store.save_document('baseline',f'{name}/{i}',dict(b,source=data['source']))


def terminal_bet_ev(pot,bet,folds,opportunities,equity_when_called,min_samples=100):
    """Only a terminal heads-up bet with fold/call, no raises or future betting.
    Equity must be supplied independently, never inferred from shown cards.
    """
    if not all(math.isfinite(v) for v in (pot,bet,folds,opportunities,equity_when_called)) or int(opportunities)!=opportunities or int(folds)!=folds: raise ValueError('Invalid EV inputs')
    if opportunities<min_samples: raise ValueError('Insufficient response sample')
    if not 0<=folds<=opportunities or not 0<=equity_when_called<=1 or pot<=0 or bet<=0: raise ValueError('Invalid EV inputs')
    called=equity_when_called*(pot+2*bet)-bet
    value=lambda f:f*pot+(1-f)*called
    lo,hi=wilson(folds,opportunities)
    return dict(ev=value(folds/opportunities),conditional_interval=sorted([value(lo),value(hi)]),assumption='HU terminal, fold/call only; fixed supplied equity; interval excludes equity/model uncertainty')
