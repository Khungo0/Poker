"""Bound-role sequence matcher compiled to parameterized DuckDB joins.

Prefixes consume consecutive decisions. Optional steps consume zero or one;
no silent skipping, and roles A/B/C always denote the same distinct players.
"""
from dataclasses import dataclass,field,asdict
from collections import Counter,defaultdict
import math
from .research import selection,FROM
from .mathutils import wilson
from .profiles import PROFILES

ACTIONS={'fold','check','call','limp','bet','raise','check_raise','shove'}
POSITIONS={'SB','BB','BTN'}

@dataclass(frozen=True)
class Step:
    street:int
    actions:tuple[str,...]
    role:str=''
    position:str=''
    optional:bool=False
    exclude:bool=False
    min_size:float|None=None
    max_size:float|None=None
    min_bb:float|None=None
    max_bb:float|None=None
    can_raise:bool|None=None

    def validate(self):
        if self.street not in (1,2,3,4) or not self.actions or not set(self.actions)<=ACTIONS:raise ValueError('Invalid sequence action')
        if self.role not in ('','A','B','C') or self.position not in ('','SB','BB','BTN'):raise ValueError('Invalid role/position')
        if self.can_raise is not None and not isinstance(self.can_raise,bool):raise ValueError('Invalid step raise eligibility')
        for low,high in ((self.min_size,self.max_size),(self.min_bb,self.max_bb)):
            if (low is None)!=(high is None):raise ValueError('Both size limits required')
            if low is not None and (not all(math.isfinite(x) for x in (low,high)) or not 0<=low<=high):raise ValueError('Invalid bet size range')


@dataclass(frozen=True)
class RoleFilter:
    """Current classification of a bound player, independent of the next actor."""
    role:str
    population:str=''
    profile:str=''
    player:str=''

    def validate(self):
        if self.role not in ('A','B','C'):raise ValueError('Invalid population role')
        if self.population and self.population not in PROFILES:raise ValueError('Invalid role population')
        profiles=PROFILES.get(self.population,[]) if self.population else sum(PROFILES.values(),[])
        if self.profile and self.profile not in profiles:raise ValueError('Subperfil incompatible con la población del rol '+self.role)
        if not isinstance(self.player,str):raise ValueError('Invalid role player')

@dataclass(frozen=True)
class Pattern:
    steps:tuple[Step,...]=()
    anchor_street:int=1
    target_role:str=''
    target_street:int|None=None
    name:str='Secuencia personalizada'
    role_filters:tuple[RoleFilter,...]=()
    target_position:str=''
    target_can_raise:bool|None=None

    def validate(self):
        if self.anchor_street not in (1,2,3,4) or self.target_role not in ('','A','B','C'):raise ValueError('Invalid pattern')
        if self.target_street is not None and self.target_street not in (1,2,3,4):raise ValueError('Invalid target street')
        if self.target_position not in ('','SB','BB','BTN'):raise ValueError('Invalid target position')
        if self.target_can_raise is not None and not isinstance(self.target_can_raise,bool):raise ValueError('Invalid raise eligibility')
        if len(self.steps)>24 or sum(s.optional for s in self.steps)>8:raise ValueError('Sequence exceeds complexity limit')
        if any(a.street>b.street for a,b in zip(self.steps,self.steps[1:])):raise ValueError('Street order in sequence')
        for s in self.steps:s.validate()
        roles={s.role for s in self.steps}|{self.target_role}
        if len({f.role for f in self.role_filters})!=len(self.role_filters):raise ValueError('Duplicate role filter')
        for f in self.role_filters:
            f.validate()
            if f.role not in roles:raise ValueError('Asigna el rol '+f.role+' a un paso o a la siguiente decisión antes de filtrarlo.')

    def to_dict(self):return asdict(self)
    @classmethod
    def from_dict(cls,value):
        return cls(**dict(value,steps=tuple(Step(**dict(s,actions=tuple(s['actions']))) for s in value['steps']),
                          role_filters=tuple(RoleFilter(**f) for f in value.get('role_filters',[]))))


def limped_barrels(streets=3):
    if streets not in (1,2,3):raise ValueError('Choose one, two or three barrels')
    steps=[Step(1,('limp',),position='SB'),Step(1,('check',),position='BB')]
    for street in range(2,2+streets):
        steps.extend([Step(street,('check',),role='B',optional=True),Step(street,('bet',),role='A')])
        if street<1+streets:steps.append(Step(street,('call',),role='B'))
    return Pattern(tuple(steps),target_role='B',target_street=1+streets,name=f'HU limped · respuesta a barrel {streets}')


def compile_pattern(pattern):
    pattern.validate();params=[]
    ctes=['b AS MATERIALIZED (SELECT *, row_number() OVER (PARTITION BY hand_id ORDER BY seq)-1 AS idx FROM observations)',
          'm0 AS MATERIALIZED (SELECT hand_id,min(idx) AS cursor, CAST(NULL AS VARCHAR) AS a, CAST(NULL AS VARCHAR) AS b, CAST(NULL AS VARCHAR) AS c FROM b WHERE street=? GROUP BY hand_id)']
    params.append(pattern.anchor_street)
    for index,step in enumerate(pattern.steps,1):
        prior=f'm{index-1}';conds=['o.street=?'];params.append(step.street)
        conds.append('o.result '+('NOT IN' if step.exclude else 'IN')+' ('+','.join('?' for _ in step.actions)+')');params.extend(step.actions)
        if step.position:conds.append('o.position=?');params.append(step.position)
        if step.min_size is not None:conds.append('o.size_pct BETWEEN ? AND ?');params.extend([step.min_size,step.max_size])
        if step.min_bb is not None:conds.append('o.size_bb BETWEEN ? AND ?');params.extend([step.min_bb,step.max_bb])
        if step.can_raise is not None:conds.append('o.can_raise=?');params.append(step.can_raise)
        columns=[]
        for role in 'abc':
            if role==step.role.lower():
                conds.append(f'(m.{role} IS NULL OR m.{role}=o.actor)')
                for other in 'abc':
                    if other!=role:conds.append(f'(m.{other} IS NULL OR m.{other}<>o.actor)')
                columns.append(f'COALESCE(m.{role},o.actor) AS {role}')
            else:columns.append('m.'+role)
        branch=f'SELECT m.hand_id,o.idx+1 AS cursor,'+','.join(columns)+f' FROM {prior} m JOIN b o ON o.hand_id=m.hand_id AND o.idx=m.cursor WHERE '+' AND '.join(conds)
        if step.optional:branch+=f' UNION SELECT * FROM {prior}'
        ctes.append(f'm{index} AS MATERIALIZED ({branch})')
    role_columns=','.join((f'COALESCE(m.{r},o.actor)' if r==pattern.target_role.lower() else f'm.{r}')+f' AS role_{r}' for r in 'abc')
    final=f'SELECT DISTINCT o.*,{role_columns} FROM m{len(pattern.steps)} m JOIN b o ON o.hand_id=m.hand_id AND o.idx=m.cursor'
    cond=[]
    if pattern.target_role:
        role=pattern.target_role.lower();cond.append(f'(m.{role} IS NULL OR o.actor=m.{role})')
        for other in 'abc':
            if other!=role:cond.append(f'(m.{other} IS NULL OR o.actor<>m.{other})')
    if pattern.target_street:cond.append('o.street=?');params.append(pattern.target_street)
    if pattern.target_position:cond.append('o.position=?');params.append(pattern.target_position)
    if pattern.target_can_raise is not None:cond.append('o.can_raise=?');params.append(pattern.target_can_raise)
    if cond:final+=' WHERE '+' AND '.join(cond)
    ctes.append('candidates AS MATERIALIZED ('+final+')')
    ctes.append('matched AS MATERIALIZED (SELECT * FROM candidates QUALIFY count(*) OVER (PARTITION BY hand_id,seq)=1)')
    return 'WITH '+',\n'.join(ctes),params


def matched_query(pattern,filters):
    prefix,params=compile_pattern(pattern);where,args=selection(filters)
    for f in pattern.role_filters:
        role='o.role_'+f.role.lower()
        where+=f' AND {role} IS NOT NULL'
        if f.population:
            where+=f" AND COALESCE((SELECT category FROM labels WHERE player={role}),'Sin clasificar')=?";args.append(f.population)
        if f.profile:
            where+=f" AND (SELECT json_extract_string(payload,'$.profile') FROM documents WHERE kind='player_profile' AND name={role})=?";args.append(f.profile)
        if f.player:where+=f' AND {role}=?';args.append(f.player)
    sql=prefix+' SELECT o.*,COALESCE(l.category,\'Sin clasificar\') AS category,COALESCE(lo.category,\'Sin clasificar\') AS opponent_category FROM matched o LEFT JOIN labels l ON o.actor=l.player LEFT JOIN labels lo ON o.opponent=lo.player WHERE '+where
    return sql,params+args


def sequence_report(store,pattern,filters,limit=200):
    sql,args=matched_query(pattern,filters)
    # SQL aggregation bounds returned data; sample rows are for inspection only.
    groups=store.rows('WITH selected AS ('+sql+''') SELECT street,result,actor,count(*) AS n,
        min(facing_pct) min_size,max(facing_pct) max_size,avg(street_eff_bb) stack_bb,
        avg(spr) spr FROM selected GROUP BY street,result,actor''',args)
    counts=Counter();players=set();by_player=defaultdict(Counter)
    for g in groups:key=(g['street'],'raise' if g['street']>1 and g['result']=='check_raise' else g['result']);counts[key]+=g['n'];players.add(g['actor']);by_player[g['actor']][key]+=g['n']
    n=sum(counts.values());out=[]
    for action,k in sorted(counts.items()):
        lo,hi=wilson(k,n)
        weighted=sum(c[action]/sum(c.values()) for c in by_player.values())/len(players)
        out.append(dict(street=action[0],result=action[1],cases=k,opportunities=n,frequency=k/n,ci_low=lo,ci_high=hi,player_weighted=weighted,players=len(players)))
    samples=store.rows(sql+' ORDER BY o.hand_id,o.seq LIMIT ?',args+[limit])
    # Arrival uses a separate, explicit universe: hands with the selected hand-level filters.
    root_filters={k:v for k,v in filters.items() if k in ('format','stake','modality','date_from','date_to','tournament_format')}
    root_filters['include_hero']=True
    where,rootargs=selection(root_filters)
    root=store.con.execute('SELECT count(DISTINCT o.hand_id) '+FROM+' WHERE '+where,rootargs).fetchone()[0]
    reached=store.con.execute('SELECT count(DISTINCT hand_id) FROM ('+sql+')',args).fetchone()[0]
    # Conditional distributions use only information available before acting.
    strata=store.rows('WITH selected AS ('+sql+'''), strata AS (
        SELECT 'Textura' dimension,texture value,result,street FROM selected
        UNION ALL SELECT 'Apuesta enfrentada' dimension,
        CASE WHEN facing_pct IS NULL THEN 'Sin apuesta'
        WHEN facing_pct<=0.33 THEN '0–33%'
        WHEN facing_pct<=0.5 THEN '>33–50%'
        WHEN facing_pct<=0.75 THEN '>50–75%'
        WHEN facing_pct<=1 THEN '>75–100%' ELSE '>100%' END value,result,street FROM selected)
        SELECT dimension,value,CASE WHEN street>1 AND result='check_raise' THEN 'raise' ELSE result END result,
        count(*) cases FROM strata GROUP BY ALL ORDER BY dimension,value,result''',args)
    denominators=Counter()
    for r in strata:denominators[(r['dimension'],r['value'])]+=r['cases']
    for r in strata:
        total=denominators[(r['dimension'],r['value'])];lo,hi=wilson(r['cases'],total)
        r.update(opportunities=total,frequency=r['cases']/total,ci_low=lo,ci_high=hi)
    return dict(opportunities=n,players=len(players),root_hands=root,reached_hands=reached,
                arrival=reached/root if root else None,rows=out,samples=samples,breakdowns=strata,
                contributions=sorted([dict(actor=p,opportunities=sum(c.values())) for p,c in by_player.items()],key=lambda x:x['opportunities'],reverse=True),
                note='Frecuencia condicionada: acción / decisiones coincidentes. Llegada: manos coincidentes / manos del mismo formato, stake y período; los demás filtros solo afectan al numerador. IC Wilson por decisión, sin corrección por dependencia o búsquedas múltiples.')


def describe(pattern):
    names={1:'Preflop',2:'Flop',3:'Turn',4:'River'}
    steps=[]
    for s in pattern.steps:
        who=' / '.join(x for x in (s.role,s.position) if x) or 'cualquier jugador'
        size=(f' [{s.min_bb:g}–{s.max_bb:g} BB en la calle]' if s.min_bb is not None else '')+(f' [{s.min_size:.0%}–{s.max_size:.0%} del bote]' if s.min_size is not None else '')
        eligibility=' · subida legal' if s.can_raise is True else ' · sin subida legal' if s.can_raise is False else ''
        steps.append(f"{names[s.street]} · {who}: {'excepto ' if s.exclude else ''}{'/'.join(s.actions)}{size}{eligibility}{' (opcional)' if s.optional else ''}")
    steps.append(f"decisión de {pattern.target_role or 'siguiente jugador'}"+(f' ({pattern.target_position})' if pattern.target_position else '')+(f' en {names[pattern.target_street]}' if pattern.target_street else '')+(' · subida legal requerida' if pattern.target_can_raise is True else ' · sin subida legal' if pattern.target_can_raise is False else ''))
    roles='; '.join(f"Rol {f.role}: "+' · '.join(x for x in (f.population,f.profile,f.player) if x) for f in pattern.role_filters)
    return ' → '.join(steps)+(f'. Poblaciones fijas: {roles}.' if roles else '')


def compare_reports(a,b):
    """Descriptive differences; each population retains its own Wilson interval.

    A zero case count with a nonzero denominator is evidence of zero observed
    cases, not an absent sample. No independence/EV claim is made here.
    """
    actions=sorted({(r['street'],r['result']) for report in (a,b) for r in report['rows']})
    out=[]
    for street,action in actions:
        row=dict(street=street,action=action)
        for name,report in (('a',a),('b',b)):
            n=report['opportunities'];k=next((r['cases'] for r in report['rows'] if (r['street'],r['result'])==(street,action)),0)
            lo,hi=wilson(k,n) if n else (None,None)
            row.update({name+'_n':n,name+'_players':report['players'],name+'_frequency':k/n if n else None,name+'_low':lo,name+'_high':hi})
        row['difference_pp']=100*(row['a_frequency']-row['b_frequency']) if a['opportunities'] and b['opportunities'] else None
        out.append(row)
    return out
