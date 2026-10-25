"""Explicit SRP heads-up postflop lines, preserving the original HU/3H format.

A = preflop raiser; B = sole caller; C = folded third player.
No implicit skips: a donk excludes the cbet opportunity on that street.
"""
from .sequences import Pattern, Step

# key, format, preflop prefix, aggressor in position
SRP_LINES = (
    ('hu_sb_bb', 'HU', (('A','SB','raise'),('B','BB','call')), True),
    ('3h_btn_bb', '3H', (('A','BTN','raise'),('C','SB','fold'),('B','BB','call')), True),
    ('3h_btn_sb', '3H', (('A','BTN','raise'),('B','SB','call'),('C','BB','fold')), True),
    ('3h_sb_bb', '3H', (('C','BTN','fold'),('A','SB','raise'),('B','BB','call')), False),
)


def srp_patterns(line):
    key, format_, prefix, ip = line
    pre = tuple(Step(1,(action,),role=role,position=pos) for role,pos,action in prefix)
    patterns = {}

    def add(name, steps, role, street):
        patterns[name] = Pattern(pre+tuple(steps), target_role=role, target_street=street,
                                 name=f'{key} · {name}')

    # check-through order follows the actual postflop order, including SB vs BB in 3H.
    oop, inpos = ('B','A') if ip else ('A','B')
    checked = [Step(2,('check',),role=oop),Step(2,('check',),role=inpos)]
    flop = [Step(2,('check',),role='B')] if ip else []
    add('cbet',flop,'A',2)
    flop += [Step(2,('bet',),role='A')]
    add('vs_cbet',flop,'B',2)
    add('vs_flop_raise',flop+[Step(2,('raise','check_raise'),role='B')],'A',2)
    if ip:
        add('donk',[],'B',2)
        add('vs_donk',[Step(2,('bet',),role='B')],'A',2)
        add('probe',checked,'B',3)
        add('vs_probe',checked+[Step(3,('bet',),role='B')],'A',3)
    else:
        add('flop_stab',[Step(2,('check',),role='A')],'B',2)
        add('vs_flop_stab',[Step(2,('check',),role='A'),Step(2,('bet',),role='B')],'A',2)
        add('turn_stab',checked+[Step(3,('check',),role='A')],'B',3)
        add('vs_turn_stab',checked+[Step(3,('check',),role='A'),Step(3,('bet',),role='B')],'A',3)
    delayed = checked+([Step(3,('check',),role='B')] if ip else [])
    add('delayed_cbet',delayed,'A',3)
    add('vs_delayed_cbet',delayed+[Step(3,('bet',),role='A')],'B',3)
    for street in (3,4):
        flop += [Step(street-1,('call',),role='B')]
        if ip:flop += [Step(street,('check',),role='B')]
        add(f'barrel_{street-1}',flop,'A',street)
        flop += [Step(street,('bet',),role='A')]
        add(f'vs_barrel_{street-1}',flop,'B',street)
    return patterns


def srp_presets():
    from .presets import ResearchPreset
    labels = {'cbet':'Cbet flop · bet/check','vs_cbet':'Respuesta a cbet flop',
              'donk':'Donk flop · bet/check','vs_donk':'Respuesta a donk flop',
              'probe':'Probe turn · bet/check','vs_probe':'Respuesta a probe turn',
              'flop_stab':'Stab flop tras missed cbet','vs_flop_stab':'Respuesta a stab flop',
              'turn_stab':'Stab turn tras check-through','vs_turn_stab':'Respuesta a stab turn',
              'delayed_cbet':'Delayed cbet turn · bet/check','vs_delayed_cbet':'Respuesta a delayed cbet',
              'barrel_2':'Segundo barrel · bet/check','vs_barrel_2':'Respuesta al segundo barrel',
              'barrel_3':'Tercer barrel · bet/check','vs_barrel_3':'Fold/call/raise vs tercer barrel',
              'vs_flop_raise':'Apostador frente a raise flop'}
    result=[]
    for line in SRP_LINES:
        key,format_,prefix,ip=line
        positions=' → '.join(pos for role,pos,action in prefix if role!='C')
        for name,pattern in srp_patterns(line).items():
            result.append(ResearchPreset(f'srp_{key}_{name}',f'{format_} SRP {positions} · {labels[name]}',
                pattern,format_,'srp','A = agresor preflop; B = único caller; C = tercero que foldeó. Denominador anterior al resultado; sin limp/iso, 3bet ni bote multiway.'))
    return result
