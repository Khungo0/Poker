"""Visual sequence research, independent of the legacy desktop pages."""
import json
from dataclasses import replace
from PySide6.QtCore import Qt,QThread,Signal
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QGridLayout,QLabel,QComboBox,QPushButton,QDoubleSpinBox,QCheckBox,QLineEdit,QTreeWidget,QTreeWidgetItem,QTableWidget,QTableWidgetItem,QHeaderView,QGroupBox,QScrollArea,QProgressBar,QFileDialog,QMessageBox
from .sequences import Pattern,Step,limped_barrels,sequence_report,describe
from .store import Store
from .replayer import Replayer
from .profiles import PROFILES

STREETS={'Preflop':1,'Flop':2,'Turn':3,'River':4}
ACTION_NAMES={'fold':'Fold','call':'Call','check':'Check','limp':'Limp','bet':'Bet','raise':'Raise','check_raise':'Check-raise','shove':'Shove'}

class ResearchWorker(QThread):
    ready=Signal(object);failed=Signal(str)
    def __init__(self,path,pattern,filters):super().__init__();self.path=path;self.pattern=pattern;self.filters=filters
    def run(self):
        s=None
        try:
            s=Store(self.path);self.connection=s.con
            if self.isInterruptionRequested():return
            report=sequence_report(s,self.pattern,self.filters)
            comparison={cat:sequence_report(s,self.pattern,dict(self.filters,population=cat),limit=0)['rows'] for cat in ('Reg','Fish')}
            if not self.isInterruptionRequested():self.ready.emit(dict(report=report,comparison=comparison))
        except Exception as e:
            if not self.isInterruptionRequested():self.failed.emit(str(e))
        finally:
            self.connection=None
            if s:s.close()


    def stop(self):
        self.requestInterruption()
        con=getattr(self,'connection',None)
        if con:
            try:con.interrupt()
            except Exception:pass


class SequencePanel(QWidget):
    def __init__(self,store,parent=None):
        super().__init__(parent);self.store=store;self.pattern=limped_barrels();self.history=[];self.worker=None;self.last=None
        outer=QVBoxLayout(self);outer.setContentsMargins(0,0,0,0);scroll=QScrollArea();scroll.setWidgetResizable(True);content=QWidget();scroll.setWidget(content);outer.addWidget(scroll);v=QVBoxLayout(content);v.setContentsMargins(24,20,24,20);v.setSpacing(12)
        title=QLabel('Explorador de secuencias');title.setObjectName('title');v.addWidget(title)
        v.addWidget(QLabel('Un mismo agresor. Un mismo defensor. Cada oportunidad conserva su historial.'))
        top=QHBoxLayout();self.presets=QComboBox();self.presets.addItems(['HU limped · tercer barrel','HU limped · segundo barrel','HU limped · bet flop','Personalizada desde preflop']);top.addWidget(self.presets,1)
        self.presets.currentIndexChanged.connect(self.load_preset);self.back=QPushButton('← Atrás');self.back.clicked.connect(self.go_back);top.addWidget(self.back)
        self.name=QLineEdit();self.name.setPlaceholderText('Nombre de investigación');top.addWidget(self.name);save=QPushButton('★ Guardar');save.clicked.connect(self.save);top.addWidget(save);v.addLayout(top)
        grid=QGridLayout();self.filters={}
        for i,(key,label,values) in enumerate([('format','Estado',['HU','3H']),('population','Defensor / actor',['Todos','Reg','Fish','Sin clasificar']),('opponent_population','Rival directo',['Todos','Reg','Fish','Sin clasificar']),('stake','Stake',['Todos']+[r[0] for r in store.con.execute('SELECT DISTINCT stake FROM hands ORDER BY stake').fetchall()]),('position','Posición',['Todos','SB','BB']),('pot_type','Bote',['Todos','limped','limp_iso','srp','3bet','4bet+','unraised']),('actor_profile','Subperfil actor',['Todos']+PROFILES['Reg']+PROFILES['Fish']),('opponent_profile','Subperfil rival',['Todos']+PROFILES['Reg']+PROFILES['Fish'])]):
            combo=QComboBox();combo.addItems(values);grid.addWidget(QLabel(label),2*(i//4),i%4);grid.addWidget(combo,2*(i//4)+1,i%4);self.filters[key]=combo
        self.filters['format'].currentTextChanged.connect(self.positions);self.filters['pot_type'].setCurrentText('limped');v.addLayout(grid)
        quick=QHBoxLayout();self.stack_preset=QComboBox();self.stack_preset.addItems(['Stack libre']+[f'{x} BB ±1' for x in [5,6,8,10,12,15,20,25]]);quick.addWidget(self.stack_preset)
        self.low=QDoubleSpinBox();self.high=QDoubleSpinBox()
        for spin,val in [(self.low,0),(self.high,100)]:spin.setRange(0,1000);spin.setValue(val);quick.addWidget(spin)
        self.stack_preset.currentIndexChanged.connect(self.set_stack);self.hero=QCheckBox('Incluir Hero');quick.addWidget(self.hero)
        self.run_button=QPushButton('Investigar secuencia');self.run_button.clicked.connect(self.run);quick.addWidget(self.run_button,1)
        self.cancel=QPushButton('Cancelar');self.cancel.clicked.connect(self.cancel_query);self.cancel.setEnabled(False);quick.addWidget(self.cancel);v.addLayout(quick)
        self.advanced=QGroupBox('Constructor visual y filtros avanzados');self.advanced.setCheckable(True);self.advanced.setChecked(False);av=QVBoxLayout(self.advanced);self.controls=QWidget();controls=QVBoxLayout(self.controls);self.controls.hide();self.advanced.toggled.connect(self.controls.setVisible);av.addWidget(self.controls);v.addWidget(self.advanced)
        line=QHBoxLayout();self.street=QComboBox();self.street.addItems(STREETS);self.role=QComboBox();self.role.addItems(['Sin rol','A','B','C']);self.action=QComboBox();self.action.addItems(ACTION_NAMES);self.position=QComboBox();self.position.addItems(['Cualquiera','SB','BB','BTN']);self.optional=QCheckBox('Opcional');self.exclude=QCheckBox('Excluir acción')
        for widget in [self.street,self.role,self.position,self.action,self.optional,self.exclude]:line.addWidget(widget)
        add=QPushButton('Añadir paso');add.clicked.connect(self.add_step);line.addWidget(add);remove=QPushButton('Quitar último');remove.clicked.connect(self.remove_step);line.addWidget(remove);controls.addLayout(line)
        dates=QHBoxLayout();self.date_from=QLineEdit();self.date_to=QLineEdit();self.date_from.setPlaceholderText('Desde AAAA-MM-DD');self.date_to.setPlaceholderText('Hasta AAAA-MM-DD');dates.addWidget(self.date_from);dates.addWidget(self.date_to)
        self.size_enabled=QCheckBox('Apuesta anunciada (% bote)');self.size_low=QDoubleSpinBox();self.size_high=QDoubleSpinBox()
        for spin,val in [(self.size_low,0),(self.size_high,200)]:spin.setRange(0,10000);spin.setValue(val)
        dates.addWidget(self.size_enabled);dates.addWidget(self.size_low);dates.addWidget(self.size_high);controls.addLayout(dates)
        sprline=QHBoxLayout();self.spr_enabled=QCheckBox('Filtrar SPR al inicio de la calle');sprline.addWidget(self.spr_enabled);self.spr_low=QDoubleSpinBox();self.spr_high=QDoubleSpinBox()
        for spin,value in [(self.spr_low,0),(self.spr_high,100)]:spin.setRange(0,10000);spin.setValue(value);sprline.addWidget(spin)
        self.active=QComboBox();self.active.addItems(['Todos','2','3']);sprline.addWidget(QLabel('Jugadores activos'));sprline.addWidget(self.active);controls.addLayout(sprline)
        self.description=QLabel();self.description.setWordWrap(True);self.description.setObjectName('muted');v.addWidget(self.description)
        self.progress=QProgressBar();self.progress.hide();v.addWidget(self.progress);self.kpis=QLabel('Selecciona un preset y pulsa Investigar.');self.kpis.setObjectName('metric');v.addWidget(self.kpis)
        self.tree=QTreeWidget();self.tree.setHeaderLabels(['Siguiente acción','Casos / oportunidades','Frecuencia · IC95','Por jugador','Reg','Fish']);self.tree.header().setSectionResizeMode(QHeaderView.ResizeToContents);self.tree.header().setStretchLastSection(True);self.tree.itemDoubleClicked.connect(self.follow);v.addWidget(self.tree,2)
        self.hands=QTableWidget();self.hands.setEditTriggers(QTableWidget.NoEditTriggers);self.hands.setAlternatingRowColors(True);self.hands.cellDoubleClicked.connect(self.open_hand);v.addWidget(self.hands,1)
        self.notice=QLabel('Las categorías proceden de tus etiquetas. Sin etiquetas Fish no se generan estadísticas Fish.');self.notice.setWordWrap(True);v.addWidget(self.notice)
        foot=QHBoxLayout();self.saved=QComboBox();foot.addWidget(self.saved,1);load=QPushButton('Abrir investigación');load.clicked.connect(self.load_saved);foot.addWidget(load);export=QPushButton('Exportar investigación');export.clicked.connect(self.export);foot.addWidget(export);v.addLayout(foot)
        self.refresh_saved();self.describe();self.positions(self.filters['format'].currentText())
        prefs=store.documents('preferences')
        previous=next((d['payload'] for d in prefs if d['name']=='sequence'),None)
        if previous:self.apply_payload(previous)

    def positions(self,format_):
        current=self.filters['position'].currentText();self.filters['position'].clear();self.filters['position'].addItems(['Todos','SB','BB']+(['BTN'] if format_=='3H' else []))
        if current!='BTN' or format_=='3H':self.filters['position'].setCurrentText(current)
        self.position.clear();self.position.addItems(['Cualquiera','SB','BB']+(['BTN'] if format_=='3H' else []))
    def describe(self):self.description.setText(describe(self.pattern));self.back.setEnabled(bool(self.history))
    def remember(self):self.history.append(self.pattern)
    def load_preset(self,index):
        self.remember();self.pattern=limped_barrels(3-index) if index<3 else Pattern();self.filters['pot_type'].setCurrentText('limped' if index<3 else 'Todos');self.filters['format'].setCurrentText('HU');self.describe()
    def set_stack(self,index):
        if index:bb=[5,6,8,10,12,15,20,25][index-1];self.low.setValue(max(0,bb-1));self.high.setValue(bb+1)
    def add_step(self):
        self.remember();step=Step(STREETS[self.street.currentText()],(self.action.currentText(),),role='' if self.role.currentIndex()==0 else self.role.currentText(),position='' if self.position.currentIndex()==0 else self.position.currentText(),optional=self.optional.isChecked(),exclude=self.exclude.isChecked())
        self.pattern=replace(self.pattern,steps=self.pattern.steps+(step,),anchor_street=self.pattern.anchor_street if self.pattern.steps else step.street,target_role='',target_street=None);self.describe()
    def remove_step(self):self.remember();self.pattern=replace(self.pattern,steps=self.pattern.steps[:-1],target_role='',target_street=None);self.describe()
    def go_back(self):
        if self.history:self.pattern=self.history.pop();self.describe();self.run()
    def current_filters(self):
        f={k:c.currentText() for k,c in self.filters.items() if c.currentText()!='Todos'};f.update(include_hero=self.hero.isChecked(),street_eff_bb=[self.low.value(),self.high.value()])
        for key,w in [('date_from',self.date_from),('date_to',self.date_to)]:
            if w.text().strip():f[key]=w.text().strip()
        if self.spr_enabled.isChecked():f['spr']=[self.spr_low.value(),self.spr_high.value()]
        if self.active.currentText()!='Todos':f['active_players']=int(self.active.currentText())
        if self.size_enabled.isChecked():f['facing_pct']=[self.size_low.value()/100,self.size_high.value()/100]
        return f
    def run(self):
        if self.worker and self.worker.isRunning():return
        self.worker=ResearchWorker(self.store.path,self.pattern,self.current_filters());self.worker.ready.connect(self.show_report);self.worker.failed.connect(self.show_error);self.worker.finished.connect(self.finished)
        self.run_button.setEnabled(False);self.cancel.setEnabled(True);self.progress.setRange(0,0);self.progress.show();self.worker.start()
    def cancel_query(self):
        if self.worker:self.worker.stop();self.notice.setText('Cancelación solicitada; el resultado de esta consulta se descartará.');self.cancel.setEnabled(False)
    def finished(self):self.run_button.setEnabled(True);self.cancel.setEnabled(False);self.progress.hide()
    def show_error(self,error):self.notice.setText(error)
    def show_report(self,result):
        self.last=result;report=result['report'];self.kpis.setText(f"{report['opportunities']:,} oportunidades  ·  {report['players']:,} jugadores  ·  llegada {report['reached_hands']:,}/{report['root_hands']:,} manos")
        self.tree.clear()
        for row in report['rows']:
            compare=[]
            for cat in ('Reg','Fish'):
                r=next((r for r in result['comparison'][cat] if r['result']==row['result'] and r['street']==row['street']),None);compare.append(f"{r['frequency']:.1%} · n={r['opportunities']}" if r else 'Sin muestra')
            item=QTreeWidgetItem([f"{row['street']} · {ACTION_NAMES[row['result']]}",f"{row['cases']} / {row['opportunities']}",f"{row['frequency']:.1%} [{row['ci_low']:.1%}, {row['ci_high']:.1%}]",f"{row['player_weighted']:.1%}",*compare]);item.setData(0,Qt.UserRole,row);self.tree.addTopLevelItem(item)
        samples=report['samples'];keys=['hand_id','actor','opponent','position','result','facing_pct','street_eff_bb','spr','board'];self.hands.setColumnCount(len(keys));self.hands.setHorizontalHeaderLabels(['Mano','Actor','Rival','Posición','Acción','Apuesta anunciada / bote','Stack calle BB','SPR','Board']);self.hands.setRowCount(len(samples))
        for i,r in enumerate(samples):
            for j,key in enumerate(keys):self.hands.setItem(i,j,QTableWidgetItem(f'{r[key]:.3f}' if isinstance(r[key],float) else str(r[key])))
        self.hands.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        largest=report['contributions'][0]['opportunities']/report['opportunities'] if report['opportunities'] else 0
        self.notice.setText(f'Mayor contribución individual: {largest:.1%}. '+('Muestra reducida. ' if report['opportunities']<100 else '')+report['note']+' Doble clic en acción: avanzar; en mano: replayer. Se muestran hasta 200 manos.')
    def follow(self,item,column):
        row=item.data(0,Qt.UserRole);self.remember();actions=('raise','check_raise') if row['result']=='raise' and row['street']>1 else (row['result'],)
        self.pattern=replace(self.pattern,steps=self.pattern.steps+(Step(row['street'],actions,role=self.pattern.target_role),),target_role='',target_street=None);self.describe();self.run()
    def open_hand(self,row,column):
        if not self.last:return
        ident=self.last['report']['samples'][row]['hand_id'];raw=self.store.con.execute('SELECT raw FROM hands WHERE hand_id=?',[ident]).fetchone()[0];self.replayer=Replayer(raw,self);self.replayer.show()
    def save(self):
        if not self.name.text().strip():self.notice.setText('Escribe un nombre para guardar la investigación.');return
        self.store.save_document('investigation',self.name.text(),dict(pattern=self.pattern.to_dict(),filters=self.current_filters()));self.refresh_saved()
    def refresh_saved(self):self.saved.clear();self.saved.addItems([d['name'] for d in self.store.documents('investigation')])
    def load_saved(self):
        doc=next((d for d in self.store.documents('investigation') if d['name']==self.saved.currentText()),None)
        if not doc:return
        self.remember();self.apply_payload(doc['payload']);self.name.setText(doc['name']);self.run()
    def apply_payload(self,payload):
        self.pattern=Pattern.from_dict(payload['pattern']);f=payload['filters']
        self.filters['format'].setCurrentText(f.get('format','HU'))
        for k,c in self.filters.items():c.setCurrentText(f.get(k,'Todos'))
        self.hero.setChecked(f.get('include_hero',False));lo,hi=f.get('street_eff_bb',[0,100]);self.low.setValue(lo);self.high.setValue(hi)
        self.spr_enabled.setChecked('spr' in f);lo,hi=f.get('spr',[0,100]);self.spr_low.setValue(lo);self.spr_high.setValue(hi);self.active.setCurrentText(str(f.get('active_players','Todos')))
        self.date_from.setText(f.get('date_from',''));self.date_to.setText(f.get('date_to',''));self.size_enabled.setChecked('facing_pct' in f)
        if 'facing_pct' in f:self.size_low.setValue(f['facing_pct'][0]*100);self.size_high.setValue(f['facing_pct'][1]*100)
        self.describe()
    def export(self):
        path,_=QFileDialog.getSaveFileName(self,'Exportar investigación','investigation.json','JSON (*.json)')
        if path:
            from pathlib import Path
            Path(path).write_text(json.dumps(dict(pattern=self.pattern.to_dict(),filters=self.current_filters()),ensure_ascii=False,indent=2),encoding='utf-8')
