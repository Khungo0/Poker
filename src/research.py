"""Population queries, conservative rule labels and explicit reference comparisons."""
import json, math
from .mathutils import wilson

FILTERS={'spot','street','position','format','stake','texture','previous','modality','actor','opponent','board','path','can_raise','check_raise_opportunity','pot_type','active_players','tournament_format','barrel','facing_barrel'}
RANGES={'bb_eff','bb_eff_min','facing_bb','facing_pct','size_bb','size_pct','initial_stack_bb','initial_eff_bb','street_eff_bb','spr'}


def selection(filters):
    if filters.get('format')=='HU' and filters.get('position')=='BTN':raise ValueError('En HU el botón es SB; no existe una tercera posición BTN.')
    clauses=[] if filters.get('include_hero',False) else ["o.card_source <> 'dealt'"]; args=[]
    for key,value in filters.items():
        if key=='include_hero':
            if not isinstance(value,bool):raise ValueError('include_hero must be boolean')
            continue
        if value is None or value=='Todos': continue
        if key in ('date_from','date_to'):
            from datetime import date
            day=date.fromisoformat(value)
            clauses.append('CAST(o.played_at AS DATE) '+('>=' if key=='date_from' else '<=')+' ?');args.append(day)
        elif key in FILTERS: clauses.append(f'o."{key}"=?'); args.append(value)
        elif key in RANGES:
            if len(value)!=2 or not all(math.isfinite(float(v)) for v in value) or value[0]>value[1]: raise ValueError('Invalid range')
            clauses.append(f'o."{key}" BETWEEN ? AND ?'); args.extend(value)
        elif key in ('actor_profile','opponent_profile'):
            alias='l' if key=='actor_profile' else 'lo'
            clauses.append(f"(SELECT json_extract_string(payload,'$.profile') FROM documents WHERE kind='player_profile' AND name={alias}.player)=?");args.append(value)
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


def player_profiles(store,format_=None):
    return store.rows('''WITH per_hand AS (
        SELECT actor,hand_id,bool_or(result IN ('call','limp','raise','shove')) voluntary,
        bool_or(result IN ('raise','shove')) raised FROM observations WHERE street=1 AND card_source<>'dealt' AND (? IS NULL OR format=?) GROUP BY actor,hand_id)
        SELECT actor AS player,count(*) AS hands,sum(CAST(voluntary AS INTEGER)) AS vpip_cases,
        sum(CAST(raised AS INTEGER)) AS pfr_cases,avg(CAST(voluntary AS INTEGER)) AS vpip,
        avg(CAST(raised AS INTEGER)) AS pfr,COALESCE(l.category,'Sin clasificar') category,
        l.origin,l.confidence,l.reason FROM per_hand LEFT JOIN labels l ON actor=l.player
        GROUP BY ALL ORDER BY hands DESC''',[format_,format_])


def classification_preview(store,rules):
    # Confidence is evidence strength of a rule, never a calibrated P(Reg/Fish).
    for rule in rules:
        from .profiles import PROFILES
        if rule.get('format') not in (None,'HU','3H'):raise ValueError('Invalid rule format')
        if rule.get('profile') and rule['profile'] not in PROFILES.get(rule['category'],[]):raise ValueError('Invalid rule profile')
        if rule['category'] not in ('Reg','Fish') or rule['metric'] not in ('vpip','pfr'): raise ValueError('Invalid rule')
        if rule['min_hands']<30 or not 0<=rule['low']<=rule['high']<=1: raise ValueError('Invalid rule limits')
    proposals=[]
    by_format={f:{p['player']:p for p in player_profiles(store,f)} for f in ('HU','3H')}
    for p in player_profiles(store):
        if p['origin']=='manual':
            proposals.append(dict(player=p['player'],category=p['category'],status='Manual protegida',confidence=None,reason=p['reason'],profile=None));continue
        matches=[]
        for r in rules:
            sample=by_format.get(r.get('format'),{}).get(p['player']) if r.get('format') else p
            if not sample or sample['hands']<r['min_hands']: continue
            lo,hi=wilson(sample[r['metric']+'_cases'],sample['hands'])
            if lo>=r['low'] and hi<=r['high']: matches.append(r)
        if len({(r['category'],r.get('profile')) for r in matches})!=1:
            proposals.append(dict(player=p['player'],category='Sin clasificar',status='Conflicto' if matches else 'Sin evidencia suficiente',confidence=None,reason='Reglas incompatibles' if matches else 'Ningún IC completo cumple una regla con muestra suficiente',profile=None));continue
        r=matches[0];sample=by_format[r['format']][p['player']] if r.get('format') else p;lo,hi=wilson(sample[r['metric']+'_cases'],sample['hands'])
        proposals.append(dict(player=p['player'],category=r['category'],status='Propuesta automática',confidence=1-(hi-lo),reason=f"Regla {r['metric']}; IC95 [{lo:.3f}, {hi:.3f}]; n={sample['hands']}; formato={r.get('format') or 'HU+3H'}. Fuerza heurística, no probabilidad de clase.",profile=r.get('profile')))
    return proposals


def classify(store,rules):
    proposals=classification_preview(store,rules)
    store.con.execute('BEGIN')
    try:
        old=[r[0] for r in store.con.execute("SELECT player FROM labels WHERE origin='auto'").fetchall()]
        for player in old:
            store.label(player,'Sin clasificar','auto',reason='Reevaluación de reglas: evidencia anterior retirada',transaction=False)
        store.con.execute("DELETE FROM documents WHERE kind='player_profile' AND name IN (SELECT player FROM labels WHERE origin='auto')")
        store.con.execute("DELETE FROM labels WHERE origin='auto'")
        assigned=0
        for p in proposals:
            if p['status']!='Propuesta automática':continue
            store.label(p['player'],p['category'],'auto',p['confidence'],p['reason'],profile=p['profile'],transaction=False);assigned+=1
        store.save_document('rules','active',rules);store.con.execute('COMMIT');return assigned
    except Exception:
        store.con.execute('ROLLBACK');raise


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
    if not name.strip():raise ValueError('Nombre obligatorio')
    from datetime import datetime, timezone
    from uuid import uuid4
    if payload.get('population') not in ('Reg','Fish'): raise ValueError('Choose Reg or Fish')
    selection(payload['filters'])
    if not payload.get('action') or not payload.get('rationale'): raise ValueError('Action and rationale required')
    status=payload.get('status','Hipótesis')
    if status not in ('En investigación','Hipótesis','Frecuencia validada','EV evaluado','Descartado'):raise ValueError('Estado inválido')
    totals,rows=explore(store,dict(payload['filters'],population=payload['population']))
    if status=='Frecuencia validada' and totals['opportunities']==0:raise ValueError('No hay oportunidades para validar esta frecuencia.')
    if status=='EV evaluado' and not (payload.get('ev_model') and payload.get('ev_assumptions') and isinstance(payload.get('ev'),(int,float)) and math.isfinite(payload['ev'])):raise ValueError('EV evaluado requiere modelo, supuestos y resultado numérico explícitos.')
    payload=dict(payload,status=status,evidence=dict(totals=totals,actions=rows),updated_at=datetime.now(timezone.utc).isoformat(),limitations='Etiquetas actuales; frecuencias observadas no demuestran EV.')
    store.save_document('strategy_version',name+'/'+uuid4().hex,payload)
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
