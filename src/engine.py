"""Betting replay and observable decision opportunities; no hidden-card inference."""
from collections import Counter
from .context import enrich


class ReplayError(ValueError): pass


def texture(board):
    if not board: return 'preflop'
    ranks=Counter(c[0] for c in board); suits=Counter(c[1] for c in board)
    pair='trips' if max(ranks.values())>=3 else 'paired' if max(ranks.values())==2 else 'unpaired'
    suit={1:'rainbow',2:'two-tone',3:'three-flush',4:'four-flush',5:'five-flush'}[max(suits.values())]
    nums=sorted(set('23456789TJQKA'.index(c[0])+2 for c in board))
    if 14 in nums: nums=[1]+nums
    connected=any(sum(lo<=r<=lo+4 for r in nums)>=3 for lo in nums)
    return f'{pair}/{suit}/{"connected" if connected else "disconnected"}'


def replay(hand):
    names=[p['name'] for p in hand.players]
    stacks={p['name']:p['stack'] for p in hand.players}; remaining=stacks.copy()
    active=set(names); contributed=dict.fromkeys(names,0); paid=dict.fromkeys(names,0); antes=dict.fromkeys(names,0)
    seated=sorted(hand.players,key=lambda p:p['seat'])
    dealer=next(i for i,p in enumerate(seated) if p['dealer'])
    order=seated[dealer:]+seated[:dealer]
    pos=dict(zip([p['name'] for p in order],['SB','BB'] if len(order)==2 else ['BTN','SB','BB']))
    posted=set()
    observations=[]; events=[]; street=1; high=hand.bb; pot=0; last_aggressor=''; last_kind='unopened'; raises=0
    checked=set(); acted=set(); prior_aggressor=''; prior_checked=False; street_aggressor=''; previous='none'; last_size=None
    street_start=remaining.copy(); last_target=0; opening_pot=0; history=[]; last_full_raise=hand.bb; faced={}; preflop_aggressor=''; pending=None; cursor=0
    street_active=set(names)
    pre_order=[p['name'] for p in order]
    post_order=pre_order[1:]+pre_order[:1]
    def needed():
        return {n for n in active if remaining[n]>0 and (contributed[n]<min(high,max((remaining[x]+contributed[x] for x in active if x!=n),default=0)) or any(remaining[x]>0 for x in active if x!=n))}
    def settle():
        nonlocal pot
        ordered=sorted(contributed.values(),reverse=True)
        refund=ordered[0]-ordered[1]
        if refund:
            who=max(contributed,key=contributed.get); contributed[who]-=refund; paid[who]-=refund; remaining[who]+=refund; pot-=refund
    for i,a in enumerate(hand.actions):
        actor=a['player']; kind=a['kind']; amount=a['amount']; rd=a['street']
        if actor not in remaining: raise ReplayError('Unknown actor')
        if rd==0:
            if amount>remaining[actor]: raise ReplayError('Post exceeds stack')
            remaining[actor]-=amount; paid[actor]+=amount; pot+=amount
            if kind=='ante': antes[actor]+=amount
            else:
                if kind in posted or pos[actor]!=kind.upper(): raise ReplayError('Blind position mismatch')
                posted.add(kind); contributed[actor]+=amount
            continue
        if pending is None:
            pending=needed(); street_start={n:remaining[n]+contributed[n] for n in names}
        if rd < street or rd>street+1: raise ReplayError('Street order')
        if rd!=street:
            if pending.intersection(needed()): raise ReplayError('Incomplete betting round')
            # All surviving players must have settled their prior-street calls.
            if any(remaining[n]>0 and contributed[n]<max(contributed[x] for x in active) for n in active): raise ReplayError('Unsettled street')
            if street==1: preflop_aggressor=last_aggressor
            settle(); prior_aggressor=street_aggressor or (last_aggressor if street==1 else '')
            prior_checked=not bool(street_aggressor or (last_aggressor if street==1 else ''))
            street=rd; contributed=dict.fromkeys(names,0); high=0; checked=set(); acted=set(); raises=0
            street_aggressor=''; last_aggressor=''; last_kind='unopened'; previous='none'; last_size=None
            street_start=remaining.copy(); street_active=set(active); opening_pot=pot; last_full_raise=hand.bb; faced={}; pending=needed(); cursor=0
        if not {'SB','BB'}.issubset(pos.values()): raise ReplayError('Missing blinds')
        for n in names:
            pos.setdefault(n,'BTN')
        if actor not in pos: pos[actor]='BTN'
        if actor not in active or remaining[actor]==0: raise ReplayError('Folded/all-in actor acts')
        if len(active)<2: raise ReplayError('Action after hand ended')
        turn_order=pre_order if street==1 else post_order
        legal_pending=pending.intersection(needed())
        expected=next((turn_order[(cursor+j)%len(turn_order)] for j in range(len(turn_order)) if turn_order[(cursor+j)%len(turn_order)] in legal_pending),None)
        if expected!=actor: raise ReplayError('Action out of turn')
        cursor=(turn_order.index(actor)+1)%len(turn_order)
        effective_high=min(high,max(remaining[n]+contributed[n] for n in active if n!=actor))
        due=max(0,effective_high-contributed[actor]); before=remaining[actor]; pot_before=pot
        if kind=='raise_to': delta=amount-contributed[actor]
        else: delta=amount
        declared_allin=a['kind']=='allin'
        if declared_allin and delta!=before: raise ReplayError('Allin does not exhaust stack')
        # Export can announce an over-covering all-in when every rival is already all-in.
        # Its uncallable excess is returned; economically this is a call, not a raise.
        raw_delta=delta
        if kind in ('allin','raise_to') and effective_high<contributed[actor]+delta and not any(remaining[n]>max(0,high-contributed[n]) for n in active if n!=actor):
            delta=min(due,before); kind='call'
        elif kind=='allin': kind='raise' if contributed[actor]+delta>high else 'call'
        elif kind=='raise_to': kind='raise'
        if street > 1 and high == 0 and kind == 'raise': kind='bet'
        if kind in ('fold','check') and delta!=0: raise ReplayError('Zero action with chips')
        if kind=='check' and due>0: raise ReplayError('Check facing bet')
        if kind=='call' and (due<=0 or delta!=min(due,before)): raise ReplayError('Call amount mismatch')
        if kind=='bet' and (high>0 or delta<=0): raise ReplayError('Invalid bet')
        if kind=='raise' and contributed[actor]+delta<=high: raise ReplayError('Raise does not increase wager')
        if delta<0 or delta>before: raise ReplayError('Stack overdraw')

        allin=delta==before and delta>0
        opponents=sorted(active-{actor})
        opponent=last_aggressor if last_aggressor in opponents else (opponents[0] if len(opponents)==1 else '')
        # Maximum contestable stack against any remaining rival. Multiway min/max are retained.
        available={n:remaining[n]+contributed[n] for n in active}
        effs=[min(available[actor],available[n])/hand.bb for n in opponents]
        can_raise=any(remaining[n]>max(0,high-contributed[n]) for n in opponents) and before>due and (actor not in faced or faced[actor]==0 or high-faced[actor]>=last_full_raise)
        if kind in ('raise','bet') and not can_raise: raise ReplayError('Betting not reopened')
        if street==1:
            if raises==0 and last_kind=='unopened' and actor not in acted:
                spot=pos[actor]+'_FIRST'
            elif raises==0: spot=pos[actor]+'_VS_LIMP'
            else: spot=pos[actor]+'_VS_'+('SHOVE' if last_kind=='shove' else 'RAISE')
            result='shove' if allin and kind=='raise' else 'limp' if kind=='call' and raises==0 else kind
        else:
            if due>0:
                spot='VS_'+last_kind.upper()
                # Check-raise eligibility is an independent filter, preserving VS_CBET etc.
            elif high==0 and not acted.intersection({actor}):
                if prior_aggressor==actor: spot='CBET'
                elif street==3 and prior_checked and preflop_aggressor==actor: spot='DELAYED_CBET'
                elif prior_aggressor in active and prior_aggressor not in acted: spot='DONK'
                elif prior_checked and street==3 and preflop_aggressor and actor!=preflop_aggressor and pos[actor] in ('SB','BB') and actor==next((n for n in sorted(active,key=lambda n: ({'BB':0,'SB':1} if hand.format=='HU' else {'SB':0,'BB':1,'BTN':2}).get(pos.get(n,'BTN'),2))),None): spot='PROBE'
                elif prior_aggressor in acted: spot='STAB'
                else: spot='UNOPENED'
            else: spot='UNOPENED'
            result='check_raise' if kind=='raise' and actor in checked else kind
        eligible = (['fold','call']+(['raise','shove'] if can_raise else [])) if due else ['check']+(['bet' if street>1 else 'raise','shove'] if can_raise else [])
        if street==1 and raises==0 and due>0: eligible=['fold','limp']+(['raise','shove'] if can_raise else [])
        if street>1 and actor in checked and due>0 and can_raise: eligible=['fold','call','check_raise']
        known=hand.known_cards.get(actor,{})
        observation=dict(hand_id=hand.hand_id,seq=i,session=hand.tournament,actor=actor,opponent=opponent,opponents=opponents,
            stake=hand.stake,format=hand.format,modality=hand.modality,street=street,position=pos[actor],spot=spot,
            previous=previous,path=' > '.join(history),bb_eff=max(effs),bb_eff_min=min(effs),facing_bb=min(due,before)/hand.bb,
            facing_pct=last_size,board=' '.join(hand.boards.get(street,[])),texture=texture(hand.boards.get(street,[])),
            pot=pot_before/100,remaining=before/100,active_players=len(active),
            initial_stack_bb=stacks[actor]/hand.bb,initial_eff_bb=max(min(stacks[actor],stacks[n]) for n in names if n!=actor)/hand.bb,
            street_eff_bb=max(min(street_start[actor],street_start[n]) for n in street_active if n!=actor)/hand.bb,
            spr=max(min(street_start[actor],street_start[n]) for n in street_active if n!=actor)/opening_pot if street>1 and opening_pot else None,result=result,allin=allin,can_raise=can_raise,check_raise_opportunity=street>1 and actor in checked and due>0 and can_raise,eligible=eligible,
            size_bb=(contributed[actor]+delta)/hand.bb if delta else None,
            size_pct=delta/pot_before if delta and pot_before else None,
            known_cards=' '.join(known.get('cards',[])),card_source=known.get('source','unknown'))
        # A lone player with no call due against only all-ins has no decision.
        if due or any(remaining[n]>0 for n in opponents): observations.append(observation)
        remaining[actor]-=delta; contributed[actor]+=delta; paid[actor]+=delta; pot+=delta
        if kind=='fold': active.remove(actor)
        if kind=='check': checked.add(actor)
        if kind in ('raise','bet'):
            increase=contributed[actor]-high
            if increase<last_full_raise and not allin: raise ReplayError('Under-minimum raise')
            if increase>=last_full_raise: last_full_raise=increase
            high=contributed[actor]; last_aggressor=actor; raises+=1
            pending=needed()-{actor}
            street_aggressor=actor
            last_kind=('shove' if allin else 'raise') if street==1 else ('check_raise' if actor in checked else spot.lower() if kind=='bet' else 'raise')
            last_size=delta/pot_before if pot_before else None
        elif street==1 and kind=='call' and raises==0: last_kind='limp'
        pending.discard(actor); faced[actor]=high
        history.append(f'{street}:{pos[actor]}:{result}'); previous=result; acted.add(actor)
        events.append(dict(seq=i,street=street,actor=actor,kind=kind,delta=delta,raw_delta=raw_delta,declared_allin=declared_allin,total=contributed[actor],remaining=remaining[actor],pot=pot,allin=allin,stacks=remaining.copy(),bets=contributed.copy()))
    if len(active)>1:
        if pending is not None and pending.intersection(needed()): raise ReplayError('Incomplete final round')
        if any(remaining[n]>0 and contributed[n]<max(contributed[x] for x in active) for n in active): raise ReplayError('Unsettled final call')
        if not hand.boards.get(4): raise ReplayError('Missing showdown board')
    settle()
    if sum(paid.values())==sum(antes.values()):
        ordered=sorted(paid.values(),reverse=True); refund=ordered[0]-ordered[1]
        if refund:
            who=max(paid,key=paid.get); paid[who]-=refund; remaining[who]+=refund; pot-=refund
    if pot!=hand.pot: raise ReplayError(f'Pot mismatch: reconstructed {pot}, reported {hand.pot}')
    if sum(hand.wins.values())+hand.rake!=pot: raise ReplayError('Payout mismatch')
    if any(n not in active for n in hand.wins): raise ReplayError('Folded winner')
    return enrich(hand,observations),events,dict(pot=pot,contributions=paid,remaining=remaining)
