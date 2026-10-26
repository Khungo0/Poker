"""Observed behavior, evidence rules and label-free population snapshots.

No default thresholds, winner inference, solver values or hidden-card inference.
"""
import math
from datetime import datetime,timezone
from .mathutils import wilson
from .research import selection

# Each predicate is evaluated BEFORE the result in its numerator.
DEFINITIONS={
 'hu_limp':('Limp HU SB',"street=1 AND format='HU' AND spot='SB_FIRST'","result='limp'"),
 'hu_open_raise':('Open raise HU SB (sin shove)',"street=1 AND format='HU' AND spot='SB_FIRST'","result='raise'"),
 'open_shove':('Open shove first-in',"street=1 AND spot IN ('SB_FIRST','BTN_FIRST')","result='shove'"),
 'limp_fold':('Limp/fold HU vs iso/shove',"street=1 AND format='HU' AND position='SB' AND path IN ('1:SB:limp > 1:BB:raise','1:SB:limp > 1:BB:shove')","result='fold'"),
 'limp_call':('Limp/call HU vs iso/shove',"street=1 AND format='HU' AND position='SB' AND path IN ('1:SB:limp > 1:BB:raise','1:SB:limp > 1:BB:shove')","result='call'"),
 'limp_raise':('Limp/reraise HU vs iso/shove',"street=1 AND format='HU' AND position='SB' AND path IN ('1:SB:limp > 1:BB:raise','1:SB:limp > 1:BB:shove')","result IN ('raise','shove')"),
 'bb_iso':('BB iso no all-in vs limp HU',"street=1 AND format='HU' AND path='1:SB:limp'","result='raise'"),
 'bb_shove_limp':('BB shove vs limp HU',"street=1 AND format='HU' AND path='1:SB:limp'","result='shove'"),
 'bb_fold_minraise':('BB fold vs minraise HU',"street=1 AND format='HU' AND path='1:SB:raise' AND prior_size=2","result='fold'"),
 'bb_call_minraise':('BB call vs minraise HU',"street=1 AND format='HU' AND path='1:SB:raise' AND prior_size=2","result='call'"),
 'threebet':('3bet frente a una subida preflop',"street=1 AND len(regexp_extract_all(path,':(?:raise|shove)'))=1","result IN ('raise','shove')"),
 'threebet_shove':('3bet shove frente a una subida',"street=1 AND len(regexp_extract_all(path,':(?:raise|shove)'))=1","result='shove'"),
 'call_shove':('Call vs shove preflop',"street=1 AND ends_with(spot,'_VS_SHOVE')","result='call'"),
 'limped_flop_bet':('Bet flop sin apuesta en limped puro',"street=2 AND pot_type='limped' AND facing_bb=0","result='bet'"),
 'cbet':('Cbet flop en raised pot',"street=2 AND spot='CBET' AND pot_type IN ('srp','3bet','4bet+','limp_iso')","result='bet'"),
 'fold_cbet':('Fold vs cbet flop',"street=2 AND spot='VS_CBET'","result='fold'"),
 'check_raise':('Check-raise con subida legal',"street>1 AND check_raise_opportunity","result='check_raise'"),
 'probe':('Probe turn',"street=3 AND spot='PROBE'","result='bet'"),
 'second_barrel':('Segundo barrel sin apuesta enfrentada',"street=3 AND facing_bb=0 AND barrel=2","result='bet'"),
 'third_barrel':('Tercer barrel sin apuesta enfrentada',"street=4 AND facing_bb=0 AND barrel=3","result='bet'"),
 'fold_second':('Fold vs segundo barrel',"street=3 AND facing_barrel=2","result='fold'"),
 'fold_third':('Fold vs tercer barrel',"street=4 AND facing_barrel=3","result='fold'"),
 **{f'aggression_{st}':(f'Acciones agresivas · calle {st}',f'street={st}',"result IN ('bet','raise','check_raise')") for st in (2,3,4)},
}
NAMES={'vpip':'VPIP','pfr':'PFR','vpip_pfr_gap':'VPIP − PFR','hands':'Manos con decisión preflop','tournaments':'Torneos observados','days':'Días observados',**{k:v[0] for k,v in DEFINITIONS.items()}}
COUNTS={'hands','tournaments','days'}


def player_metrics(store,filters=None):
    filters=dict(filters or {})
    allowed={'format','stake','date_from','date_to','bb_eff','initial_eff_bb','actor','opponent_population','opponent_profile','include_hero'}
    if set(filters)-allowed:raise ValueError('Contexto de métricas no soportado: '+', '.join(sorted(set(filters)-allowed)))
    where,args=selection(filters)
    if filters.get('opponent_population') not in (None,'Todos'):where+=" AND o.opponent<>''"
    prefix='''WITH ordered AS MATERIALIZED (
       SELECT *,lag(size_bb) OVER (PARTITION BY hand_id ORDER BY seq) prior_size,
       row_number() OVER (PARTITION BY hand_id,actor,street ORDER BY seq) decision_index FROM observations),
       selected AS MATERIALIZED (SELECT o.* FROM ordered o LEFT JOIN labels l ON o.actor=l.player
       LEFT JOIN labels lo ON o.opponent=lo.player WHERE '''+where+'''),
       pre_selected AS (SELECT o.* FROM ordered o LEFT JOIN labels l ON o.actor=l.player
       LEFT JOIN labels lo ON o.opponent=lo.player WHERE street=1 AND decision_index=1 AND '''+where+'''),
       per_hand AS (SELECT p.actor,p.hand_id,p.session,p.played_at,
       bool_or(o.result IN ('limp','call','raise','shove')) vpip,
       bool_or(o.result IN ('raise','shove')) pfr FROM pre_selected p
       JOIN observations o ON o.hand_id=p.hand_id AND o.actor=p.actor AND o.street=1 GROUP BY ALL)
    '''
    # Filters occur twice; all values remain parameterized.
    values=args+args
    volume=store.rows(prefix+''' SELECT actor,count(*) hands,count(DISTINCT session) tournaments,
       count(DISTINCT CAST(played_at AS DATE)) AS "days",sum(CAST(vpip AS INTEGER)) vpip,
       sum(CAST(pfr AS INTEGER)) pfr,sum(CAST(vpip AND NOT pfr AS INTEGER)) gap FROM per_hand GROUP BY actor''',values)
    rows=[]
    def add(actor,key,k,n):
        lo,hi=wilson(k,n) if n else (None,None)
        rows.append(dict(player=actor,metric=key,name=NAMES[key],cases=int(k),opportunities=int(n),frequency=k/n if n else None,ci_low=lo,ci_high=hi))
    for r in volume:
        for key in COUNTS:rows.append(dict(player=r['actor'],metric=key,name=NAMES[key],value=int(r[key]),cases=None,opportunities=None,frequency=None,ci_low=None,ci_high=None))
        for key in ('vpip','pfr'):add(r['actor'],key,r[key],r['hands'])
        add(r['actor'],'vpip_pfr_gap',r['gap'],r['hands'])
    unions=[]
    for key,(_,opportunity,success) in DEFINITIONS.items():
        unions.append(f"SELECT actor,'{key}' metric,count(*) n,count(*) FILTER (WHERE {success}) k FROM selected WHERE {opportunity} GROUP BY actor")
    for r in store.rows(prefix+' UNION ALL '.join(unions),values):add(r['actor'],r['metric'],r['k'],r['n'])
    return rows


def validate_condition(node,depth=0):
    if depth>5:raise ValueError('Máximo 5 niveles de reglas')
    if node.get('op') in ('AND','OR'):
        children=node.get('conditions',[])
        if not 1<=len(children)<=20:raise ValueError('Cada grupo requiere 1–20 condiciones')
        for child in children:validate_condition(child,depth+1)
    else:
        metric=node.get('metric');low=node.get('low');high=node.get('high')
        if metric not in NAMES or not all(isinstance(x,(int,float)) and math.isfinite(x) for x in (low,high)) or not 0<=low<=high:raise ValueError('Condición inválida')
        if metric not in COUNTS and (high>1 or not isinstance(node.get('min_opportunities',30),int) or isinstance(node.get('min_opportunities',30),bool) or node.get('min_opportunities',30)<30):raise ValueError('Frecuencia requiere intervalo 0–1 y mínimo 30 oportunidades')


def evaluate(node,metrics):
    """Three-valued logic: absent evidence never satisfies a leaf, AND or OR."""
    if node.get('op') in ('AND','OR'):
        children=[evaluate(c,metrics) for c in node['conditions']];states=[s for s,e in children]
        state=(False if False in states else None if None in states else True) if node['op']=='AND' else (True if True in states else None if None in states else False)
        return state,[e for s,es in children for e in es]
    row=metrics.get(node['metric']);state=None
    if row:
        if node['metric'] in COUNTS:state=node['low']<=row['value']<=node['high']
        elif row['opportunities']>=node.get('min_opportunities',30):state=row['ci_low']>=node['low'] and row['ci_high']<=node['high']
    return state,[dict(condition=node,observed=row,state=state)]


def preview_rules(store,rules,filters=None,metrics=None):
    from .profiles import PROFILES
    if len(rules)>50:raise ValueError('Máximo 50 reglas')
    for rule in rules:
        validate_condition(rule['condition'])
        if rule.get('category') not in ('Reg','Fish') or rule.get('profile') not in (None,*PROFILES[rule['category']]):raise ValueError('Clase/subperfil inválido')
        if not isinstance(rule.get('weight',1),(int,float)) or not math.isfinite(rule.get('weight',1)) or rule.get('weight',1)<=0:raise ValueError('Puntuación debe ser positiva')
    by_player={}
    for row in (metrics if metrics is not None else player_metrics(store,filters)):by_player.setdefault(row['player'],{})[row['metric']]=row
    labels={r['player']:r for r in store.rows('SELECT * FROM labels')};profiles={d['name']:d['payload'].get('profile') for d in store.documents('player_profile')};out=[]
    for player,metrics in sorted(by_player.items()):
        evidence=[];matches=[];unknown=False
        for i,rule in enumerate(rules):
            state,detail=evaluate(rule['condition'],metrics);evidence.append(dict(rule=i,name=rule.get('name',str(i+1)),state=state,conditions=detail));unknown|=state is None
            if state is True:matches.append(rule)
        targets={(r['category'],r.get('profile')) for r in matches};manual=labels.get(player,{}).get('origin')=='manual'
        category,profile=next(iter(targets)) if len(targets)==1 else ('Sin clasificar',None)
        status='Manual protegida' if manual else 'Conflicto' if len(targets)>1 else 'Propuesta automática' if targets else 'Evidencia insuficiente' if unknown else 'Sin coincidencia'
        out.append(dict(player=player,category=labels[player]['category'] if manual else category,profile=profiles.get(player) if manual else profile,status=status,score=sum(r.get('weight',1) for r in matches),evidence=evidence))
    return out


def apply_rules(store,rules,filters=None):
    from uuid import uuid4
    preview=preview_rules(store,rules,filters)
    names=[r['player'] for r in preview if r['status']!='Manual protegida']
    def capture():
        labels={r['player']:r for r in store.rows('SELECT * FROM labels')}
        profiles={r['name']:r['payload'] for r in store.documents('player_profile')}
        return {n:dict(label=labels.get(n),profile=profiles.get(n)) for n in names}
    before=capture();old_rules=next((d['payload'] for d in store.documents('behavior_rules') if d['name']=='active'),None)
    store.con.execute('BEGIN')
    try:
        existing={r['player']:r['origin'] for r in store.rows('SELECT player,origin FROM labels')}
        for row in preview:
            # Scoped applications do not erase classifications outside this cohort.
            if row['status']!='Propuesta automática':
                if row['status']!='Manual protegida' and existing.get(row['player'])=='auto':store.label(row['player'],'Sin clasificar','auto',reason='Reevaluación multivariable: '+row['status'],transaction=False)
                continue
            store.label(row['player'],row['category'],'auto',None,'Reglas multivariable; puntuación heurística '+str(row['score']),profile=row['profile'],transaction=False)
        store.save_document('behavior_rules','active',dict(rules=rules,filters=filters or {}))
        store.save_document('classification_run',uuid4().hex,dict(before=before,after=capture(),evidence=preview,previous_rules=old_rules,applied_rules=dict(rules=rules,filters=filters or {}),recorded_at=datetime.now(timezone.utc).isoformat()))
        store.con.execute('COMMIT')
    except Exception:store.con.execute('ROLLBACK');raise
    return preview


def save_population(store,name,condition,filters=None):
    validate_condition(condition);by_player={}
    for row in player_metrics(store,filters):by_player.setdefault(row['player'],{})[row['metric']]=row
    members=[p for p,metrics in sorted(by_player.items()) if evaluate(condition,metrics)[0] is True]
    payload=dict(condition=condition,filters=filters or {},members=members,recorded_at=datetime.now(timezone.utc).isoformat(),semantics='Snapshot explícito; no cambia etiquetas, refrescar para nuevos datos')
    store.save_document('population',name,payload);return payload


def undo_classification(store,run_name):
    run=next((d['payload'] for d in store.documents('classification_run') if d['name']==run_name),None)
    if not run or run.get('undone_at'):raise ValueError('Revisión inexistente o ya restaurada')
    current_rules=next((d['payload'] for d in store.documents('behavior_rules') if d['name']=='active'),None)
    if current_rules!=run['applied_rules']:raise ValueError('Las reglas activas cambiaron después de esta revisión; no se sobrescribirán.')
    labels={r['player']:r for r in store.rows('SELECT * FROM labels')}
    profiles={d['name']:d['payload'] for d in store.documents('player_profile')}
    for player,state in run['after'].items():
        if labels.get(player)!=state['label'] or profiles.get(player)!=state['profile']:raise ValueError('Hay etiquetas o perfiles posteriores. No se sobrescribirán; revisa el historial.')
    store.con.execute('BEGIN')
    try:
        for player,state in run['before'].items():
            label=state['label']
            if label:
                store.label(player,label['category'],label['origin'],label['confidence'],'Rollback de clasificación: '+run_name,profile=(state['profile'] or {}).get('profile'),transaction=False)
                store.con.execute('UPDATE labels SET reason=? WHERE player=?',[label['reason'],player])
            else:
                store.label(player,'Sin clasificar','auto',reason='Rollback de clasificación: '+run_name,transaction=False)
                store.con.execute('DELETE FROM labels WHERE player=?',[player])
            if state['profile'] is None:store.con.execute("DELETE FROM documents WHERE kind='player_profile' AND name=?",[player])
            else:store.save_document('player_profile',player,state['profile'])
        if run['previous_rules'] is None:store.con.execute("DELETE FROM documents WHERE kind='behavior_rules' AND name='active'")
        else:store.save_document('behavior_rules','active',run['previous_rules'])
        run['undone_at']=datetime.now(timezone.utc).isoformat();store.save_document('classification_run',run_name,run);store.con.execute('COMMIT')
    except Exception:store.con.execute('ROLLBACK');raise
