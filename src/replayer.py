"""Offline replay from verified hands, with cards disclosed only when known."""
from copy import deepcopy
from PySide6.QtCore import Qt,QRectF
from PySide6.QtGui import QPainter,QColor,QFont
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QPushButton,QSlider,QLabel,QPlainTextEdit,QTabWidget
from .history import parse_hand
from .engine import replay


def replay_frames(hand):
    _,events,balance=replay(hand)
    names=[p['name'] for p in sorted(hand.players,key=lambda p:p['seat'])]
    dealer=next(p['name'] for p in hand.players if p['dealer']);d=names.index(dealer);order=names[d:]+names[:d]
    positions=dict(zip(order,['SB / BTN','BB'] if hand.format=='HU' else ['BTN','SB','BB']))
    state=dict(stacks={p['name']:p['stack'] for p in hand.players},bets={n:0 for n in names},pot=0,board=[],cards={n:(hand.known_cards[n]['cards'] if hand.known_cards.get(n,{}).get('source')=='dealt' else ['?','?']) for n in names},positions=positions,street=1,text='Inicio · stacks antes de las ciegas',active=names.copy())
    frames=[deepcopy(state)]
    for a in hand.actions:
        if a['street']!=0:break
        state['stacks'][a['player']]-=a['amount'];state['pot']+=a['amount']
        if a['kind']!='ante':state['bets'][a['player']]+=a['amount']
        state['text']=f"{a['player']} · {a['kind']} · {a['amount']/hand.bb:.2f} BB";frames.append(deepcopy(state))
    for e in events:
        if e['street']!=state['street']:
            state['bets']={n:0 for n in names};state['street']=e['street']
        state['board']=hand.boards.get(e['street'],[])
        state['stacks']=e['stacks'].copy();state['bets']=e['bets'].copy();state['pot']=e['pot']
        if e['kind']=='fold':state['active'].remove(e['actor'])
        state['seq']=e['seq']
        state['text']=f"{e['actor']} · {e['kind']} · aporta {e['delta']/hand.bb:.2f} BB";frames.append(deepcopy(state))
    for street in range(max(2,state['street']+1),5):
        if street in hand.boards:
            state['street']=street;state['board']=hand.boards[street];state['text']='Board · '+{2:'Flop',3:'Turn',4:'River'}[street];frames.append(deepcopy(state))
    state['stacks']={n:balance['remaining'][n]+hand.wins.get(n,0) for n in names}
    state['pot']=0;state['bets']={n:0 for n in names}
    state['cards']={n:hand.known_cards.get(n,{}).get('cards',['?','?']) for n in names}
    state['text']=f"Reparto final · bote verificado {hand.pot/100:g} fichas";frames.append(deepcopy(state))
    return frames


class TableCanvas(QWidget):
    def __init__(self,frames,bb):super().__init__();self.frames=frames;self.index=0;self.bb=bb;self.setMinimumHeight(300)
    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.Antialiasing);w,h=self.width(),self.height();f=self.frames[self.index]
        p.setBrush(QColor('#152d39'));p.setPen(QColor('#304c5c'));p.drawRoundedRect(QRectF(w*.15,h*.24,w*.7,h*.55),h*.2,h*.2)
        p.setPen(QColor('#96d9ea'));p.setFont(QFont('Segoe UI',12));p.drawText(QRectF(w*.3,h*.33,w*.4,30),Qt.AlignCenter,f"Bote · {f['pot']/self.bb:.2f} BB")
        def card(x,y,c):
            p.setBrush(QColor('#26374d') if c=='?' else QColor('#e2e8ef'));p.setPen(Qt.NoPen);p.drawRoundedRect(QRectF(x,y,42,56),5,5)
            p.setPen(QColor('#8299b2') if c=='?' else QColor('#a33153') if c[-1] in 'dh' else QColor('#172733'))
            face='?' if c=='?' else c[0]+{'c':'♣','d':'♦','h':'♥','s':'♠'}[c[-1]];p.drawText(QRectF(x,y,42,56),Qt.AlignCenter,face)
        for i,c in enumerate(f['board']):card(w/2-120+i*48,h*.46,c)
        n=len(f['stacks']);seats=[(.15,.12),(.74,.12),(.44,.78)] if n==3 else [(.15,.14),(.74,.72)]
        for (name,stack),(x,y) in zip(f['stacks'].items(),seats):
            x*=w;y*=h;p.setPen(QColor('#dbe7f2') if name in f['active'] else QColor('#687789'))
            p.drawText(QRectF(x-45,y-30,210,28),Qt.AlignCenter,name+' · '+f['positions'][name])
            p.drawText(QRectF(x-45,y,210,28),Qt.AlignCenter,f"{stack/self.bb:.2f} BB · apuesta {f['bets'][name]/self.bb:.2f}")
            for j,c in enumerate(f['cards'][name]):card(x+j*48,y+30,c)
        p.end()


class Replayer(QWidget):
    def __init__(self,raw,parent=None):
        super().__init__(parent,Qt.Window);self.setWindowTitle('Replayer · Spin Population Lab');self.resize(1050,760)
        self.hand=parse_hand(raw);self.frames=replay_frames(self.hand)
        layout=QVBoxLayout(self);tabs=QTabWidget();layout.addWidget(tabs)
        page=QWidget();v=QVBoxLayout(page);self.canvas=TableCanvas(self.frames,self.hand.bb);v.addWidget(self.canvas,1)
        self.caption=QLabel();v.addWidget(self.caption);row=QHBoxLayout();v.addLayout(row)
        back=QPushButton('← Anterior');forward=QPushButton('Siguiente →');self.slider=QSlider(Qt.Horizontal);self.slider.setRange(0,len(self.frames)-1)
        row.addWidget(back);row.addWidget(self.slider,1);row.addWidget(forward)
        back.clicked.connect(lambda:self.slider.setValue(self.slider.value()-1));forward.clicked.connect(lambda:self.slider.setValue(self.slider.value()+1))
        self.slider.valueChanged.connect(self.seek);tabs.addTab(page,'Mesa y acciones')
        original=QPlainTextEdit(raw);original.setReadOnly(True);tabs.addTab(original,'Historial original');self.seek(0)
    def seek(self,index):self.canvas.index=index;self.canvas.update();self.caption.setText(f"{index}/{len(self.frames)-1} · {self.frames[index]['text']}")

    def seek_decision(self,seq):
        # Stop immediately before the selected action. Prepare its street/board
        # from the known hand but never reveal showdown cards at this point.
        index=next((i for i,f in enumerate(self.frames) if f.get('seq')==seq),0)
        if index:
            before=deepcopy(self.frames[index-1]);before['board']=self.frames[index]['board'];before['street']=self.frames[index]['street']
            if self.frames[index-1]['street']!=before['street']:before['bets']={n:0 for n in before['bets']}
            before['text']='Antes de la decisión seleccionada';before.pop('seq',None)
            self.frames.insert(index,before);self.slider.setMaximum(len(self.frames)-1);self.slider.setValue(index)
