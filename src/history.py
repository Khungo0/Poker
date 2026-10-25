"""Strict reader for the supplied iPoker text export. Amounts are integer cents.
Raise (NF) = street total; Allin/Call/Bet/posts = incremental contribution.
Raw input is retained by the store; unknown/malformed hands are quarantined.
"""
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
import re

PARSER_VERSION = 'text-2'


def cents(value):
    try:
        n = Decimal(value.replace('€', '').replace(',', '').strip()) * 100
        if not n.is_finite() or n < 0 or n != n.to_integral_value():
            raise ValueError('Invalid money')
        return int(n)
    except InvalidOperation as e:
        raise ValueError('Invalid money') from e


def cards(value):
    result = []
    for c in value.split():
        if c == 'X':
            result.append('?'); continue
        if not re.fullmatch(r'[CDHS](?:[2-9]|10|[JQKA])', c):
            raise ValueError('Unknown card: '+c)
        result.append(c[1:].replace('10', 'T') + c[0].lower())
    return result


@dataclass
class TextHand:
    hand_id: str
    tournament: str
    played_at: str
    stake: str
    sb: int
    bb: int
    players: list
    actions: list
    boards: dict
    known_cards: dict
    pot: int
    rake: int
    wins: dict
    raw: str
    modality: str = 'Spin'

    @property
    def format(self):
        return 'HU' if len(self.players) == 2 else '3H'


def parse_hand(raw):
    lines = [x.strip() for x in raw.strip().splitlines() if x.strip()]
    head = re.fullmatch(r"GAME #(\d+) Version:\S+ Uncalled:[YN] Texas Hold'em NL  Tournament ([\d-]+ [\d:]+)/GMT", lines[0])
    if not head: raise ValueError('Unsupported hand header')
    blinds = re.fullmatch(r'Table Info: Size: 3, Blinds: ([\d,.]+)/([\d,.]+)(?:, Ante: ([\d,.]+))?', lines[1])
    table = re.fullmatch(r'Table Twister €[\d,.]+ SNG, (\d+), \d+ \(Tournament: Twister €[\d,.]+ SNG Buy-In: €([\d,.]+)\s*\+\s*€([\d,.]+)\)', lines[2])
    if not table: raise ValueError('Unsupported table/stake')
    if not blinds and lines[1] != 'Table Info: Size: 3, RebuyAddon: Confirmed': raise ValueError('Unsupported table info')
    players=[]; actions=[]; boards={}; known={}; wins={}; street=0; summary=False; pot=None; rake=None
    for line in lines[3:]:
        m = re.fullmatch(r'Seat (\d+): (.+) \(€([\d,.]+) in chips\)(\s+DEALER)?', line)
        if m:
            players.append(dict(seat=int(m[1]), name=m[2], stack=cents(m[3]), dealer=bool(m[4]))); continue
        if line == '*** HOLE CARDS ***': street=1; continue
        if line == '*** SUMMARY ***': summary=True; continue
        m=re.fullmatch(r'\*\*\* (FLOP|TURN|RIVER) \*\*\* \[(.+)\]',line)
        if m:
            new={'FLOP':2,'TURN':3,'RIVER':4}[m[1]]
            if new != street+1: raise ValueError('Street order')
            street=new; cs=cards(m[2])
            if len(cs)!=(3 if street==2 else 1): raise ValueError('Board length')
            boards[street]=boards.get(street-1,[])+cs; continue
        m=re.fullmatch(r'Dealt to (.+) \[(.+)\]',line)
        if m:
            known[m[1]]={'cards':cards(m[2]),'source':'dealt'}; continue
        m=re.fullmatch(r'Total pot €([\d,.]+) Rake €([\d,.]+)',line)
        if m:
            pot=cents(m[1]); rake=cents(m[2]); continue
        found=False
        for p in players:
            if not line.startswith(p['name']+': '): continue
            tail=line[len(p['name'])+2:]; name=p['name']
            m=re.fullmatch(r'(Post Ante|Post SB|Post BB)( Allin)? €([\d,.]+)',tail)
            if m and not summary and street==0:
                actions.append(dict(street=0,player=name,kind={'Post Ante':'ante','Post SB':'sb','Post BB':'bb'}[m[1]],amount=cents(m[3]))); found=True; break
            m=re.fullmatch(r'(Fold|Check|Call|Bet|Raise \(NF\)|Allin)(?: €([\d,.]+))?',tail)
            if m and not summary and street>0:
                kind={'Raise (NF)':'raise_to','Allin':'allin'}.get(m[1],m[1].lower())
                if (kind in ('fold','check')) != (m[2] is None): raise ValueError('Action amount')
                actions.append(dict(street=street,player=name,kind=kind,amount=cents(m[2]) if m[2] else 0)); found=True; break
            m=re.fullmatch(r'(Shows|Mucks) \[(.+?)\](?: .*)?',tail)
            if m and summary:
                cs=cards(m[2])
                if name in known and known[name]['cards']!=cs: raise ValueError('Conflicting cards')
                known.setdefault(name,{'cards':cs,'source':m[1].lower()}); found=True; break
            m=re.fullmatch(r'wins €([\d,.]+)',tail)
            if m and summary: wins[name]=wins.get(name,0)+cents(m[1]); found=True; break
        if not found: raise ValueError('Unknown line: '+line[:100])
    if len(players) not in (2,3) or len({p['name'] for p in players}) != len(players): raise ValueError('Invalid players')
    if sum(p['dealer'] for p in players)!=1: raise ValueError('Dealer missing')
    if not summary or pot is None or not wins: raise ValueError('Incomplete summary')
    if any(len(c['cards'])!=2 or n not in {p['name'] for p in players} for n,c in known.items()): raise ValueError('Hole cards')
    allcards=boards.get(max(boards,default=0),[])+[c for v in known.values() for c in v['cards']]
    allcards=[c for c in allcards if c!='?']
    if len(allcards)!=len(set(allcards)): raise ValueError('Duplicate visible card')
    if blinds:
        small,big=cents(blinds[1]),cents(blinds[2])
    else:
        # Only non-all-in posts establish nominal blinds; never guess from a short post.
        sb_match=re.search(r': Post SB €([\d,.]+)',raw)
        bb_match=re.search(r': Post BB €([\d,.]+)',raw)
        if not sb_match or not bb_match: raise ValueError('Nominal blinds missing with short stack')
        small,big=cents(sb_match[1]),cents(bb_match[1])
    if not 0<small<=big: raise ValueError('Invalid nominal blinds')
    from datetime import datetime
    fmt='%Y-%m-%d %H:%M:%S' if len(head[2].split('-')[0])==4 else '%m-%d-%Y %H:%M:%S'
    played=datetime.strptime(head[2],fmt).isoformat(sep=' ')
    stake=f"EUR {(cents(table[2])+cents(table[3]))/100:.2f}"
    return TextHand('ipoker:'+head[1],table[1],played,stake,small,big,players,actions,boards,known,pot,rake,wins,raw)


def read_text(data):
    if len(data)>100_000_000: raise ValueError('File exceeds 100 MB')
    text=data.decode('utf-8-sig')
    if text.startswith('PokerTracker 4 Tournament Summary'):
        fields=dict(re.findall(r'^([^:\n]+): (.*)$',text,re.M))
        required=['Tournament #','Buyin','Fee','Table Type']
        if any(k not in fields for k in required): raise ValueError('Incomplete tournament summary')
        return [],[],dict(tournament=fields['Tournament #'],buyin=cents(fields['Buyin']),fee=cents(fields['Fee']),raw=text)
    if not text.startswith('GAME #'): raise ValueError('Unsupported format: expected iPoker GAME text export')
    hands=[]; errors=[]
    for block in re.split(r'(?m)(?=^GAME #)',text):
        if not block.strip(): continue
        try: hands.append(parse_hand(block))
        except (ValueError,IndexError) as e:
            errors.append({'hand_id':block.splitlines()[0].split()[1], 'error':str(e),'raw':block})
    return hands,errors,None
