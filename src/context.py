"""Versioned context derived from validated decisions, without looking ahead."""
ANALYSIS_VERSION = 2
CONTEXT_TYPES = {
    'played_at':'VARCHAR', 'tournament_format':'VARCHAR', 'pot_type':'VARCHAR',
    'active_players':'INTEGER', 'initial_stack_bb':'DOUBLE', 'initial_eff_bb':'DOUBLE',
    'street_eff_bb':'DOUBLE', 'spr':'DOUBLE', 'preflop_aggressor':'VARCHAR',
    'barrel':'INTEGER', 'facing_barrel':'INTEGER',
}


def pot_type(raises, limped):
    if raises >= 3: return '4bet+'
    if raises == 2: return '3bet'
    if raises == 1: return 'limp_iso' if limped else 'srp'
    return 'limped' if limped else 'unraised'


def enrich(hand, observations):
    raises=0; limped=False; aggressor=''; prior_bettor=''; prior_street=0; prior_barrel=0
    street_bettor=''; street_barrel=0; street_label=''; current_street=1
    for o in observations:
        street=o['street']
        if street != current_street:
            prior_bettor=street_bettor; prior_barrel=street_barrel; prior_street=current_street
            street_bettor=''; street_barrel=0; street_label=''; current_street=street
        o.update(played_at=hand.played_at,tournament_format='Spin 3-max',pot_type=pot_type(raises,limped),
                 preflop_aggressor=aggressor if street>1 else '',barrel=0,facing_barrel=0)
        if street==1:
            if o['result']=='limp':limped=True
            if o['result'] in ('raise','shove'):raises+=1;aggressor=o['actor']
            continue
        # A barrel is a first bet on consecutive streets by the same actor.
        # A raise changes the initiative, but is never a continuation barrel.
        if o['facing_bb']==0:
            continuation=prior_barrel+1 if prior_street==street-1 and prior_bettor==o['actor'] and prior_barrel else 1
            o['barrel']=continuation
            if continuation>1:
                o['spot']='SECOND_BARREL' if continuation==2 else 'THIRD_BARREL'
            elif o['spot']=='CBET' and (street!=2 or raises==0 or o['actor']!=aggressor):
                o['spot']='UNOPENED'
            if o['result']=='bet':street_bettor=o['actor'];street_barrel=continuation;street_label=o['spot']
        elif o['opponent']==street_bettor:
            o['facing_barrel']=street_barrel
            o['spot']='VS_'+street_label
            if street_barrel>1:o['spot']='VS_SECOND_BARREL' if street_barrel==2 else 'VS_THIRD_BARREL'
        if o['result'] in ('raise','check_raise'):
            street_bettor=o['actor'];street_barrel=0;street_label='CHECK_RAISE' if o['result']=='check_raise' else 'RAISE'
    return observations
