"""Explicit multiway SRP and river research. No inferred opponents or skips."""
from .sequences import Pattern,Step
from .postflop import SRP_LINES


def advanced_patterns():
    # Only BTN raise + two calls is a pure SRP with all three seats on flop.
    pre=(Step(1,('raise',),'A','BTN'),Step(1,('call',),'B','SB'),Step(1,('call',),'C','BB'))
    result={}
    def add(key,title,steps,role,street,format_='3H'):
        result[key]=(title,Pattern(tuple(steps),target_role=role,target_street=street,name=title),format_)
    check=lambda st,r:Step(st,('check',),r,optional=True)
    add('mw_sb_lead','3H SRP multiway · SB primera apuesta',pre,'B',2)
    add('mw_bb_lead','3H SRP multiway · BB tras SB check',pre+(Step(2,('check',),'B'),),'C',2)
    add('mw_cbet','3H SRP multiway · BTN cbet tras dos checks',pre+(Step(2,('check',),'B'),Step(2,('check',),'C')),'A',2)
    flop=pre+(Step(2,('check',),'B'),Step(2,('check',),'C'),Step(2,('bet',),'A'))
    add('mw_vs_cbet_sb','3H SRP multiway · SB frente a cbet BTN',flop,'B',2)
    for action in ('call','fold','check_raise'):
        add('mw_vs_cbet_bb_'+action,'3H SRP multiway · BB tras SB '+action,flop+(Step(2,(action,),'B'),),'C',2)
    add('mw_vs_sb_lead_bb','3H SRP multiway · BB frente a lead SB',pre+(Step(2,('bet',),'B'),),'C',2)
    for action in ('call','fold'):
        add('mw_vs_sb_lead_btn_'+action,'3H SRP multiway · BTN frente a lead SB, BB '+action,pre+(Step(2,('bet',),'B'),Step(2,(action,),'C')),'A',2)
    add('mw_vs_bb_lead_btn','3H SRP multiway · BTN frente a lead BB',pre+(Step(2,('check',),'B'),Step(2,('bet',),'C')),'A',2)
    for action in ('call','fold'):
        add('mw_vs_bb_lead_sb_'+action,'3H SRP multiway · SB frente a lead BB, BTN '+action,pre+(Step(2,('check',),'B'),Step(2,('bet',),'C'),Step(2,(action,),'A')),'B',2)
    for alive in (('B','C'),('B',),('C',)):
        prefix=flop+tuple(Step(2,('call' if r in alive else 'fold',),r) for r in ('B','C'))
        tag=''.join(alive)
        for street in (3,4):
            prefix+=tuple(check(street,r) for r in alive)
            add(f'mw_barrel_{street}_{tag}',f'3H SRP · BTN barrel {street-1} · defensores {tag}',prefix,'A',street)
            prefix+=(Step(street,('bet',),'A'),)
            for i,role in enumerate(alive):
                add(f'mw_vs_barrel_{street}_{tag}_{role}',f'3H SRP · {role} vs barrel {street-1} · defensores {tag}',prefix,role,street)
                prefix+=(Step(street,('call',),role),)
    # River after cbet/call and turn check-through, plus two missed streets.
    for key,format_,opening,ip in SRP_LINES:
        p=tuple(Step(1,(a,),r,pos) for r,pos,a in opening)
        oop,inpos=('B','A') if ip else ('A','B')
        flop=p+((Step(2,('check',),'B'),) if ip else ())+(Step(2,('bet',),'A'),Step(2,('call',),'B'))
        checked_turn=(Step(3,('check',),oop),Step(3,('check',),inpos))
        quiet=p+tuple(Step(st,('check',),r) for st in (2,3) for r in (oop,inpos))
        for name,base in (('missed_turn',flop+checked_turn),('two_checked',quiet)):
            add(f'river_{key}_{name}_lead',f'{format_} SRP · river lead {oop} · {name}',base,oop,4,format_)
            add(f'river_{key}_{name}_vs_lead',f'{format_} SRP · river respuesta {inpos} · {name}',base+(Step(4,('bet',),oop),),inpos,4,format_)
            add(f'river_{key}_{name}_stab',f'{format_} SRP · river stab {inpos} tras check · {name}',base+(Step(4,('check',),oop),),inpos,4,format_)
            add(f'river_{key}_{name}_vs_stab',f'{format_} SRP · river respuesta {oop} tras check · {name}',base+(Step(4,('check',),oop),Step(4,('bet',),inpos)),oop,4,format_)
    return result


def advanced_presets():
    from .presets import ResearchPreset
    return [ResearchPreset(key,title,pattern,format_,'srp',
        'Roles persistentes. SRP puro. Cada respuesta se condiciona a las acciones previas de los otros jugadores; no se mezclan cold calls con decisiones tras un fold o raise.')
        for key,(title,pattern,format_) in advanced_patterns().items()]
