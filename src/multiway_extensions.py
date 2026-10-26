"""Pure limped three-way pots and explicitly ordered raise responses."""
from dataclasses import replace
from .sequences import Step,Pattern
from .advanced_spots import advanced_patterns


def extension_patterns():
    result={}
    limps=(Step(1,('limp',),'A','BTN'),Step(1,('limp',),'B','SB'),Step(1,('check',),'C','BB'))
    for key,(title,pattern,fmt) in advanced_patterns().items():
        if not key.startswith('mw_'):continue
        key='lp_'+key.replace('cbet','bet_btn')
        title=title.replace('SRP','limped').replace('cbet','bet flop')
        result[key]=(title,replace(pattern,steps=limps+pattern.steps[3:],name=title),fmt,'limped')
    pre=(Step(1,('raise',),'A','BTN'),Step(1,('call',),'B','SB'),Step(1,('call',),'C','BB'))
    flop=pre+(Step(2,('check',),'B'),Step(2,('check',),'C'),Step(2,('bet',),'A'))
    raise_=lambda r:Step(2,('raise','check_raise'),r)
    def add(key,title,steps,role):
        title='3H SRP · '+title
        result[key]=(title,Pattern(tuple(steps),target_role=role,target_street=2,name=title),'3H','srp')
    sb=flop+(raise_('B'),)
    for action in ('fold','call','raise'):
        step=raise_('C') if action=='raise' else Step(2,(action,),'C')
        add('raise_sb_btn_after_bb_'+action,'BTN vs raise SB · BB '+action,sb+(step,),'A')
    for action in ('fold','call','raise'):
        step=raise_('A') if action=='raise' else Step(2,(action,),'A')
        add('reraise_bb_sb_after_btn_'+action,'SB vs reraise BB · BTN '+action,sb+(raise_('C'),step),'B')
    for action in ('fold','call'):
        step=Step(2,(action,),'C')
        add('reraise_btn_sb_after_bb_'+action,'SB vs reraise BTN · BB '+action,sb+(step,raise_('A')),'B')
        for b in ('fold','call'):
            if action=='call':add('reraise_btn_bb_after_sb_'+b,'BB vs reraise BTN · SB '+b,sb+(step,raise_('A'),Step(2,(b,),'B')),'C')
    for b in ('fold','call'):
        base=flop+(Step(2,(b,),'B'),raise_('C'))
        add('raise_bb_btn_after_sb_'+b,'BTN vs raise BB · SB '+b,base,'A')
        if b=='call':
            for a in ('fold','call','raise'):
                step=raise_('A') if a=='raise' else Step(2,(a,),'A')
                add('raise_bb_sb_after_btn_'+a,'SB vs raise BB · BTN '+a,base+(step,),'B')
    return result


def extension_presets():
    from .presets import ResearchPreset
    return [ResearchPreset(key,title,pattern,fmt,pot,
        'Tres roles distintos. La oportunidad termina antes de la respuesta; mantiene las acciones del tercero y excluye otras ramas. Limped puro no se etiqueta como cbet.')
        for key,(title,pattern,fmt,pot) in extension_patterns().items()]
