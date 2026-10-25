"""Offline desktop workspace. Import runs in a worker; SQL aggregates in DuckDB."""
import csv,json
from pathlib import Path
from PySide6.QtCore import Qt,QThread,Signal,QEventLoop
from PySide6.QtGui import QColor,QPainter,QFont
from PySide6.QtWidgets import (QApplication,QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QGridLayout,QLabel,QPushButton,QListWidget,QStackedWidget,QComboBox,QDoubleSpinBox,QSpinBox,QCheckBox,QTableWidget,QTableWidgetItem,QHeaderView,QFileDialog,QMessageBox,QPlainTextEdit,QLineEdit,QFormLayout,QSplitter,QScrollArea,QProgressDialog,QFrame,QGroupBox,QTabWidget)
from .store import Store
from .sequence_ui import SequencePanel
from .replayer import Replayer
from .profiles import PROFILES
from .study_ui import StudyDashboard,SettingsPanel
from .research import explore,player_profiles,classify,leaks,save_strategy,import_reference,terminal_bet_ev,validate_baseline,selection,FROM

from .theme import DARK



def table():
    t=QTableWidget();t.setAlternatingRowColors(True);t.setEditTriggers(QTableWidget.NoEditTriggers);t.setSelectionBehavior(QTableWidget.SelectRows);t.verticalHeader().hide();return t


def fill(t,rows):
    keys=list(rows[0]) if rows else []
    labels={'result':'Acción','cases':'Casos','opportunities':'Oportunidades','frequency':'Frecuencia','ci_low':'IC95 inferior','ci_high':'IC95 superior','players':'Jugadores','tournaments':'Torneos'}
    t.setColumnCount(len(keys));t.setRowCount(len(rows));t.setHorizontalHeaderLabels([labels.get(k,k) for k in keys])
    for i,row in enumerate(rows):
        for j,k in enumerate(keys):
            v=row[k];text=f'{v:.1%}' if isinstance(v,float) and k in ('frequency','ci_low','ci_high','observed','reference','difference','vpip','pfr') else f'{v:.4f}' if isinstance(v,float) else '' if v is None else str(v)
            t.setItem(i,j,QTableWidgetItem(text))
    t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
    t.horizontalHeader().setStretchLastSection(True)


class Bars(QWidget):
    def __init__(self):super().__init__();self.rows=[];self.setMinimumHeight(160)
    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.Antialiasing)
        if not self.rows:p.drawText(20,30,'Sin observaciones para esta selección');return
        step=max(30,min(44,self.height()//len(self.rows)))
        width=max(10,self.width()-310)
        for i,r in enumerate(self.rows):
            y=12+i*step;p.setPen(QColor('#bdcbe0'));p.drawText(10,y+19,r['result'])
            p.fillRect(160,y,int(width*r['frequency']),23,QColor('#52c8de'))
            p.setPen(QColor('#e1ecff'));p.drawLine(160+int(width*r['ci_low']),y+12,160+int(width*r['ci_high']),y+12)
            p.drawText(170+width,y+19,f"{r['frequency']:.1%} · n={r['cases']}")
        p.end()


class ImportWorker(QThread):
    progress=Signal(str);done=Signal(str);failed=Signal(str)
    def __init__(self,path,files):super().__init__();self.path=path;self.files=files
    def run(self):
        s=None
        try:
            s=Store(self.path);totals={}
            for i,path in enumerate(self.files):
                if self.isInterruptionRequested():break
                r=s.import_file(path)
                for k,v in r.items():
                    if isinstance(v,int):totals[k]=totals.get(k,0)+v
                self.progress.emit(f'{i+1}/{len(self.files)} archivos · {totals.get("added",0):,} manos nuevas')
            self.done.emit('\n'.join(f'{k}: {v}' for k,v in totals.items())+('\nCancelado después del último archivo completo.' if self.isInterruptionRequested() else '\nImportación finalizada.'))
        except Exception as e:self.failed.emit(str(e))
        finally:
            if s:s.close()


class Window(QMainWindow):
    def __init__(self,path=None):
        super().__init__();self.store=Store(path);self.worker=None;self.setWindowTitle('Spin Population Lab · Offline');self.resize(1720,960);self.setMinimumSize(1180,760)
        root=QWidget();self.setCentralWidget(root);layout=QHBoxLayout(root);layout.setContentsMargins(0,0,0,0)
        side=QWidget();side.setObjectName('sidebar');sl=QVBoxLayout(side);logo=QLabel('♠  SPIN LAB');logo.setObjectName('title');sl.addWidget(logo)
        self.nav=QListWidget();self.nav.addItems(['Population Explorer','Importar historiales','Regulares y Fishes','Leak Finder','Strategy Builder','Referencias y EV']);sl.addWidget(self.nav)
        sl.addWidget(QLabel('iPoker / ChampionPoker\nEstudio offline · Datos locales'));side.setMaximumWidth(265);layout.addWidget(side)
        self.stack=QStackedWidget();layout.addWidget(self.stack,1)
        self.build_explorer();self.build_import();self.build_players();self.build_leaks();self.build_strategies();self.build_references()
        self.sequence_panel=SequencePanel(self.store,self);self.stack.addWidget(self.sequence_panel);self.nav.addItem('Explorador de secuencias')
        self.dashboard=StudyDashboard(self);self.stack.insertWidget(0,self.dashboard);self.nav.insertItem(0,'Panel de estudio')
        self.settings=SettingsPanel(self);self.stack.addWidget(self.settings);self.nav.addItem('Datos y configuración')
        self.nav.currentRowChanged.connect(self.stack.setCurrentIndex);self.nav.setCurrentRow(0)
        self.refresh_all();self.setStyleSheet(DARK)

    def page(self,title,subtitle):
        widget=QWidget();outer=QVBoxLayout(widget);outer.setContentsMargins(28,24,28,24);outer.setSpacing(14)
        label=QLabel(title);label.setObjectName('title');outer.addWidget(label)
        sub=QLabel(subtitle);sub.setWordWrap(True);sub.setObjectName('muted');outer.addWidget(sub)
        self.stack.addWidget(widget);return outer

    def safe(self,fn):
        try:return fn()
        except Exception as e:QMessageBox.warning(self,'No se pudo completar',str(e))

    def button(self,layout,text,fn):
        b=QPushButton(text);b.clicked.connect(lambda:self.safe(fn));layout.addWidget(b);return b

    def build_explorer(self):
        box=self.page('Population Explorer','Investiga una decisión · contrasta poblaciones · abre las manos que la explican')
        metrics=QHBoxLayout();self.metric_labels=[]
        for title in ('OPORTUNIDADES','JUGADORES ÚNICOS','TORNEOS'):
            card=QFrame();card.setObjectName('metricCard');cv=QVBoxLayout(card)
            caption=QLabel(title);caption.setObjectName('muted');value=QLabel('0');value.setObjectName('metricValue');cv.addWidget(caption);cv.addWidget(value);metrics.addWidget(card);self.metric_labels.append(value)
        box.addLayout(metrics);self.kpis=QLabel();self.kpis.hide()
        workspace=QSplitter(Qt.Horizontal);box.addWidget(workspace,1)
        filter_scroll=QScrollArea();filter_scroll.setWidgetResizable(True);filter_scroll.setMinimumWidth(300)
        filters=QWidget();left=QVBoxLayout(filters);left.setContentsMargins(0,0,14,0);filter_scroll.setWidget(filters);workspace.addWidget(filter_scroll)
        label=QLabel('Selección de población');label.setObjectName('title');left.addWidget(label)
        grid=QGridLayout();self.filters={}
        for i,(key,title) in enumerate([('format','HU / 3H'),('stake','Buy-in'),('population','Actor'),('opponent_population','Rival directo'),('street','Calle'),('position','Posición'),('spot','Decisión / spot'),('texture','Textura'),('previous','Acción anterior')]):
            combo=QComboBox();combo.setMinimumContentsLength(10);combo.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon);self.filters[key]=combo
            row=(i//2)*2;col=i%2;grid.addWidget(QLabel(title),row,col);grid.addWidget(combo,row+1,col)
        left.addLayout(grid);self.filters['format'].currentTextChanged.connect(self.explorer_positions)
        group=QGroupBox('Stack y tamaño');ranges=QGridLayout(group);self.lo=QDoubleSpinBox();self.hi=QDoubleSpinBox()
        for spin,val in [(self.lo,0),(self.hi,100)]:spin.setRange(0,1000);spin.setValue(val)
        ranges.addWidget(QLabel('Efectivo · BB'),0,0,1,2);ranges.addWidget(self.lo,1,0);ranges.addWidget(self.hi,1,1)
        self.size_mode=QComboBox();self.size_mode.addItems(['Todos los tamaños','Apuesta previa · % bote']);ranges.addWidget(self.size_mode,2,0,1,2)
        self.size_lo=QDoubleSpinBox();self.size_hi=QDoubleSpinBox()
        for spin,val in [(self.size_lo,0),(self.size_hi,1000)]:spin.setRange(0,10000);spin.setValue(val)
        ranges.addWidget(self.size_lo,3,0);ranges.addWidget(self.size_hi,3,1);left.addWidget(group)
        self.extra=QLineEdit('{}');self.extra.hide();self.path_filter=QLineEdit();self.path_filter.hide()
        self.actor_filter=QLineEdit();self.actor_filter.setPlaceholderText('Jugador concreto');left.addWidget(self.actor_filter)
        self.include_hero=QCheckBox('Incluir Hero');left.addWidget(self.include_hero)
        run=self.button(left,'Investigar población',self.refresh_explorer);run.setObjectName('primary')
        self.button(left,'Exportar resultados CSV',self.export_csv);left.addStretch()
        right=QWidget();rv=QVBoxLayout(right);rv.setContentsMargins(12,0,0,0);workspace.addWidget(right)
        self.results=table();self.chart=Bars();tabs=QTabWidget();tabs.addTab(self.results,'Frecuencias e intervalos');tabs.addTab(self.chart,'Gráfico de acciones');rv.addWidget(tabs,1)
        buttons=QHBoxLayout();self.button(buttons,'Abrir manos',self.inspect_hands);self.button(buttons,'Cartas reveladas',self.show_range);rv.addLayout(buttons)
        self.notice=QLabel();self.notice.setWordWrap(True);self.notice.setObjectName('muted');rv.addWidget(self.notice)
        workspace.setSizes([340,1100]);workspace.setStretchFactor(1,1)

    def explorer_positions(self,format_):
        c=self.filters['position'];old=c.currentText();c.clear();c.addItems(['Todos','SB','BB']+([] if format_=='HU' else ['BTN']))
        if old!='BTN' or format_!='HU':c.setCurrentText(old)

    def current_filters(self):
        f={k:w.currentText() for k,w in self.filters.items() if w.currentText() and w.currentText()!='Todos'}
        if 'street' in f:f['street']=int(f['street'])
        f['include_hero']=self.include_hero.isChecked()
        f['bb_eff']=[self.lo.value(),self.hi.value()]
        if self.size_mode.currentIndex():f['facing_pct']=[self.size_lo.value()/100,self.size_hi.value()/100]
        if self.path_filter.text().strip():f['path']=self.path_filter.text().strip()
        if self.actor_filter.text().strip():f['actor']=self.actor_filter.text().strip()
        f.update(json.loads(self.extra.text()));return f

    def refresh_explorer(self):
        totals,rows=explore(self.store,self.current_filters());self.last_rows=rows;fill(self.results,rows);self.chart.rows=rows;self.chart.update()
        self.kpis.setText(f"{totals['opportunities']:,} oportunidades     ·     {totals['players']:,} jugadores     ·     {totals['tournaments']:,} torneos")
        for label,key in zip(self.metric_labels,('opportunities','players','tournaments')):label.setText(f'{totals[key]:,}')
        share=totals['largest_player_share']
        self.notice.setText(f"Mayor contribución de un jugador: {share:.1%}. " if share is not None else 'Sin muestra. ')
        self.notice.setText(self.notice.text()+'Los IC no corrigen la dependencia entre manos del mismo jugador ni búsquedas múltiples. Una frecuencia no demuestra EV. Tamaño propio condiciona al resultado; usa facing_pct para estudiar respuestas. En spots multiway sin agresor no se asigna un rival único.')

    def export_csv(self):
        name,_=QFileDialog.getSaveFileName(self,'Exportar selección','population.csv','CSV (*.csv)')
        if name and self.last_rows:
            with open(name,'w',newline='',encoding='utf-8-sig') as f:
                w=csv.DictWriter(f,fieldnames=list(self.last_rows[0]));w.writeheader();w.writerows(self.last_rows)

    def inspect_hands(self):
        where,args=selection(self.current_filters())
        rows=self.store.rows('SELECT DISTINCT o.hand_id,o.street,o.actor,o.spot,o.result '+FROM+' WHERE '+where+' LIMIT 200',args)
        win=QWidget(self,Qt.Window);win.setWindowTitle('Auditoría · primeras 200 decisiones');win.resize(1200,800);v=QVBoxLayout(win);t=table();fill(t,rows);v.addWidget(t);raw=QPlainTextEdit();raw.setReadOnly(True);v.addWidget(raw)
        def show(i,j):
            if i<len(rows):
                data=self.store.con.execute('SELECT raw FROM hands WHERE hand_id=?',[rows[i]['hand_id']]).fetchone();raw.setPlainText(data[0]);self.replayer=Replayer(data[0],self);self.replayer.show()
        t.cellClicked.connect(show);win.show()

    def show_range(self):
        where,args=selection(self.current_filters())
        rows=self.store.rows('SELECT o.known_cards,count(*) n '+FROM+" WHERE "+where+" AND o.card_source IN ('shows','mucks') AND o.known_cards NOT LIKE '%?%' GROUP BY o.known_cards",args)
        counts={};ranks='AKQJT98765432'
        for row in rows:
            cs=row['known_cards'].split()
            if len(cs)!=2:continue
            a,b=cs;i,j=ranks.index(a[0]),ranks.index(b[0]);pair=i==j
            if not pair:
                i,j=(min(i,j),max(i,j)) if a[1]==b[1] else (max(i,j),min(i,j))
            counts[i,j]=counts.get((i,j),0)+row['n']
        win=QWidget(self,Qt.Window);win.setWindowTitle('Cartas reveladas · muestra seleccionada');win.resize(1000,850);v=QVBoxLayout(win)
        caption=QLabel('Conteos condicionados a revelar cartas; NO es un rango poblacional. Hero/dealt excluido.\nCeldas con menos de 20 observaciones se ocultan; manos repetidas por decisión pueden aparecer en selecciones amplias.');caption.setWordWrap(True);v.addWidget(caption)
        t=QTableWidget(13,13);t.setHorizontalHeaderLabels(list(ranks));t.setVerticalHeaderLabels(list(ranks))
        for i in range(13):
            for j in range(13):
                n=counts.get((i,j),0);label=ranks[min(i,j)]+ranks[max(i,j)]+('' if i==j else 's' if i<j else 'o')
                t.setItem(i,j,QTableWidgetItem(label+'\n'+(str(n) if n>=20 else '—')))
        t.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch);t.verticalHeader().setSectionResizeMode(QHeaderView.Stretch);v.addWidget(t);win.show()

    def build_import(self):
        box=self.page('Importar historiales','TXT iPoker y resúmenes PokerTracker · Importación local, con deduplicación y cuarentena')
        self.import_status=QLabel('Selecciona los TXT extraídos del archivo RAR.');box.addWidget(self.import_status)
        row=QHBoxLayout();self.import_buttons=[]
        self.import_buttons.append(self.button(row,'Elegir archivos TXT',lambda:self.choose_import(False)))
        self.import_buttons.append(self.button(row,'Importar carpeta',lambda:self.choose_import(True)));self.button(row,'Cancelar después del archivo actual',lambda:self.worker.requestInterruption() if self.worker and self.worker.isRunning() else None);box.addLayout(row)
        self.import_log=QPlainTextEdit();self.import_log.setReadOnly(True);box.addWidget(self.import_log,1)
        self.error_table=table();box.addWidget(self.error_table,1)
        self.button(box,'Actualizar informe de importación',self.refresh_import)

    def choose_import(self,folder):
        if folder:
            path=QFileDialog.getExistingDirectory(self,'Carpeta de historiales');files=list(Path(path).rglob('*.txt')) if path else []
        else:files=QFileDialog.getOpenFileNames(self,'Historiales',filter='TXT (*.txt)')[0]
        if not files:return
        for b in self.import_buttons:b.setEnabled(False)
        self.worker=ImportWorker(self.store.path,files);self.worker.progress.connect(self.import_status.setText);self.worker.done.connect(self.import_log.setPlainText);self.worker.failed.connect(self.import_log.setPlainText)
        self.worker.finished.connect(self.import_finished);self.worker.start()

    def import_finished(self):
        for b in self.import_buttons:b.setEnabled(True)
        self.refresh_all()

    def refresh_import(self):
        t=self.store.totals();self.import_status.setText(f"{t['hands']:,} manos · {t['observations']:,} decisiones · {t['summaries']:,} resúmenes · {t['errors']:,} errores conservados")
        fill(self.error_table,self.store.rows('SELECT source,hand_id,error FROM errors LIMIT 500'))

    def build_players(self):
        box=self.page('Regulares y Fishes','Sin clasificar por defecto · Etiquetas manuales prioritarias · Confianza automática heurística')
        scope=QHBoxLayout();scope.addWidget(QLabel('Estadísticas para clasificar'));self.player_format=QComboBox();self.player_format.addItems(['Todos','HU','3H']);scope.addWidget(self.player_format);box.addLayout(scope);self.player_format.currentTextChanged.connect(lambda _:self.refresh_players())
        self.players_table=table();box.addWidget(self.players_table,1)
        row=QHBoxLayout();self.player_name=QLineEdit();self.player_name.setPlaceholderText('Jugador exacto');self.category=QComboBox();self.category.addItems(['Sin clasificar','Reg','Fish']);row.addWidget(self.player_name,1);row.addWidget(self.category);self.subprofile=QComboBox();row.addWidget(self.subprofile);self.category.currentTextChanged.connect(self.update_subprofiles);self.update_subprofiles(self.category.currentText())
        self.button(row,'Guardar etiqueta',self.save_label);box.addLayout(row)
        self.players_table.cellClicked.connect(lambda i,j:self.player_name.setText(self.players_table.item(i,0).text()))
        box.addWidget(QLabel('Reglas: el IC95 completo debe caber en el intervalo. Mínimo 30 manos con decisión; conflictos quedan sin clasificar.'))
        rf=QHBoxLayout();self.rule_category=QComboBox();self.rule_category.addItems(['Reg','Fish']);self.rule_metric=QComboBox();self.rule_metric.addItems(['vpip','pfr']);self.rule_low=QDoubleSpinBox();self.rule_high=QDoubleSpinBox();self.rule_min=QSpinBox();self.rule_min.setRange(30,1000000);self.rule_min.setValue(200)
        for spin,value in [(self.rule_low,0),(self.rule_high,100)]:spin.setRange(0,100);spin.setValue(value);spin.setSuffix('%')
        for label,w in [('Clase',self.rule_category),('Métrica',self.rule_metric),('Desde',self.rule_low),('Hasta',self.rule_high),('Muestra mínima',self.rule_min)]:rf.addWidget(QLabel(label));rf.addWidget(w)
        self.button(rf,'Añadir regla',self.add_rule);box.addLayout(rf)
        self.rules=QPlainTextEdit('[]');self.rules.hide();self.rules_list=QListWidget();self.rules_list.setMaximumHeight(150);box.addWidget(self.rules_list);self.button(box,'Eliminar regla seleccionada',self.remove_rule)
        self.button(box,'Aplicar reglas',lambda:(classify(self.store,json.loads(self.rules.toPlainText())),self.refresh_players()))

    def add_rule(self):
        rules=json.loads(self.rules.toPlainText());rules.append(dict(format=None if self.player_format.currentText()=='Todos' else self.player_format.currentText(),category=self.rule_category.currentText(),metric=self.rule_metric.currentText(),low=self.rule_low.value()/100,high=self.rule_high.value()/100,min_hands=self.rule_min.value()));self.rules.setPlainText(json.dumps(rules,indent=2));self.show_rules()

    def show_rules(self):
        self.rules_list.clear()
        for r in json.loads(self.rules.toPlainText()):self.rules_list.addItem(f"{r['category']} · {r['metric'].upper()} {r['low']:.0%}–{r['high']:.0%} · mínimo {r['min_hands']} manos · {r.get('format') or 'HU+3H'}")

    def remove_rule(self):
        rules=json.loads(self.rules.toPlainText());index=self.rules_list.currentRow()
        if index>=0:rules.pop(index);self.rules.setPlainText(json.dumps(rules));self.show_rules()

    def update_subprofiles(self,category):
        self.subprofile.clear();self.subprofile.addItem('Sin subperfil');self.subprofile.addItems(PROFILES[category])

    def save_label(self):
        if not self.player_name.text().strip():raise ValueError('Selecciona un jugador')
        self.store.label(self.player_name.text(),self.category.currentText(),profile=None if self.subprofile.currentIndex()==0 else self.subprofile.currentText());self.refresh_players();self.refresh_explorer()

    def refresh_players(self):fill(self.players_table,player_profiles(self.store,None if self.player_format.currentText()=='Todos' else self.player_format.currentText()))

    def build_leaks(self):
        box=self.page('Leak Finder','Desviaciones frente a referencias explícitas · Sin baselines inventados · Sin afirmación de rentabilidad')
        self.baseline_name=QLineEdit();self.baseline_name.setPlaceholderText('Nombre de referencia');box.addWidget(self.baseline_name)
        self.baseline_source=QLineEdit();self.baseline_source.setPlaceholderText('Origen de la referencia: solver, estudio propio, versión…');box.addWidget(self.baseline_source)
        rf=QHBoxLayout();self.baseline_action=QComboBox();self.baseline_action.addItems(['fold','call','limp','raise','shove','check','bet','check_raise']);self.baseline_frequency=QDoubleSpinBox();self.baseline_frequency.setRange(0,100);self.baseline_frequency.setSuffix('%');self.baseline_n=QSpinBox();self.baseline_n.setRange(30,1000000);self.baseline_n.setValue(100);self.baseline_players=QSpinBox();self.baseline_players.setRange(2,100000);self.baseline_players.setValue(5)
        for label,w in [('Acción',self.baseline_action),('Referencia',self.baseline_frequency),('Oportunidades mínimas',self.baseline_n),('Jugadores mínimos',self.baseline_players)]:rf.addWidget(QLabel(label));rf.addWidget(w)
        box.addLayout(rf);box.addWidget(QLabel('Se guardarán los filtros actuales del Explorer. Selecciona allí un spot concreto antes de guardar.'))
        row=QHBoxLayout();self.button(row,'Guardar referencia',self.save_baseline);self.button(row,'Buscar desviaciones',self.refresh_leaks);box.addLayout(row)
        self.leak_table=table();box.addWidget(self.leak_table,1)
        box.addWidget(QLabel('Resultados exploratorios. Los IC Wilson no corrigen búsquedas múltiples ni dependencia por jugador.'))

    def save_baseline(self):
        b=validate_baseline(dict(source=self.baseline_source.text(),filters=self.current_filters(),action=self.baseline_action.currentText(),frequency=self.baseline_frequency.value()/100,min_opportunities=self.baseline_n.value(),min_players=self.baseline_players.value()));self.store.save_document('baseline',self.baseline_name.text(),b);self.refresh_leaks()

    def refresh_leaks(self):fill(self.leak_table,leaks(self.store,[dict(d['payload'],name=d['name']) for d in self.store.documents('baseline')]))

    def build_strategies(self):
        box=self.page('Strategy Builder','Cuaderno de hipótesis explotativas · Separa población, stack y situación')
        form=QFormLayout();self.strategy_name=QLineEdit();self.strategy_population=QComboBox();self.strategy_population.addItems(['Reg','Fish']);self.strategy_action=QLineEdit();self.strategy_state=QComboBox();self.strategy_state.addItems(['En investigación','Hipótesis','Frecuencia validada','EV evaluado','Descartado']);self.strategy_state.setCurrentText('Hipótesis');self.strategy_filters=QLineEdit('{}');self.strategy_filters.hide();self.strategy_reason=QPlainTextEdit();self.strategy_reason.setMaximumHeight(150)
        for title,w in [('Nombre',self.strategy_name),('Población',self.strategy_population),('Estado',self.strategy_state),('Acción propuesta',self.strategy_action),('Evidencia y razonamiento',self.strategy_reason)]:form.addRow(title,w)
        box.addLayout(form);row=QHBoxLayout();self.button(row,'Copiar selección del Explorer',lambda:self.strategy_filters.setText(json.dumps(self.current_filters())));self.button(row,'Guardar estrategia',self.save_strategy);self.button(row,'Exportar estrategias',self.export_strategies);box.addLayout(row)
        self.strategy_table=table();box.addWidget(self.strategy_table,1)
        self.strategy_table.cellClicked.connect(self.load_strategy)

    def save_strategy(self):
        save_strategy(self.store,self.strategy_name.text(),dict(status=self.strategy_state.currentText(),population=self.strategy_population.currentText(),filters=json.loads(self.strategy_filters.text()),action=self.strategy_action.text(),rationale=self.strategy_reason.toPlainText()));self.refresh_strategies()
    def refresh_strategies(self):
        self.strategy_docs=self.store.documents('strategy');fill(self.strategy_table,[dict(nombre=d['name'],población=d['payload']['population'],acción=d['payload']['action'],estado=d['payload'].get('status','Hipótesis'),muestra=d['payload'].get('evidence',{}).get('totals',{}).get('opportunities',''),fecha=d['payload'].get('updated_at','')) for d in self.strategy_docs])
    def load_strategy(self,i,j):
        d=self.strategy_docs[i];p=d['payload'];self.strategy_name.setText(d['name']);self.strategy_state.setCurrentText(p.get('status','Hipótesis'));self.strategy_population.setCurrentText(p['population']);self.strategy_action.setText(p['action']);self.strategy_filters.setText(json.dumps(p['filters']));self.strategy_reason.setPlainText(p['rationale'])
    def export_strategies(self):
        name,_=QFileDialog.getSaveFileName(self,'Exportar estrategias','strategies.json','JSON (*.json)')
        if name:Path(name).write_text(json.dumps(self.store.documents('strategy'),ensure_ascii=False,indent=2),encoding='utf-8')

    def build_references(self):
        box=self.page('Referencias y EV condicional','Importa referencias propias mediante el esquema JSON documentado. No se infieren rangos desde cartas ocultas.')
        self.button(box,'Importar referencia JSON',self.load_reference);self.references_table=table();box.addWidget(self.references_table,1)
        box.addWidget(QLabel('Modelo limitado: apuesta terminal HU, rival solo foldea o paga, sin raises ni apuestas futuras. Equity aportada por ti.'))
        self.ev_fields={};form=QFormLayout()
        for key,label,value in [('pot','Bote actual (fichas)',100),('bet','Apuesta (fichas)',50),('folds','Folds observados',0),('opportunities','Respuestas observadas',0),('equity_when_called','Equity al pagar (0–1)',0)]:
            spin=QDoubleSpinBox();spin.setRange(0,1 if key=='equity_when_called' else 10000000);spin.setDecimals(3 if key=='equity_when_called' else 0);spin.setValue(value);self.ev_fields[key]=spin;form.addRow(label,spin)
        box.addLayout(form);self.ev_result=QLabel('EV sin estimar: introduce los datos y la equity de referencia.');self.ev_result.setWordWrap(True)
        self.button(box,'Evaluar escenario condicional',self.evaluate_ev);box.addWidget(self.ev_result)
    def evaluate_ev(self):
        result=terminal_bet_ev(**{k:w.value() for k,w in self.ev_fields.items()});lo,hi=result['conditional_interval'];self.ev_result.setText(f"EV condicional: {result['ev']:.2f} fichas · intervalo {lo:.2f} a {hi:.2f}. Solo incertidumbre en fold frequency; equity y modelo se consideran fijos.")
    def load_reference(self):
        name,_=QFileDialog.getOpenFileName(self,'Referencia',filter='JSON (*.json)')
        if name:import_reference(self.store,Path(name).stem,json.loads(Path(name).read_text(encoding='utf-8')));self.refresh_references()
    def refresh_references(self):fill(self.references_table,[dict(nombre=d['name'],fuente=d['payload'].get('source',''),referencias=len(d['payload'].get('baselines',[])),rangos=len(d['payload'].get('ranges',[]))) for d in self.store.documents('reference')])

    def refresh_all(self):
        for key,combo in self.filters.items():
            old=combo.currentText();combo.clear();combo.addItem('Todos')
            values=['Reg','Fish','Sin clasificar'] if key in ('population','opponent_population') else [str(r[0]) for r in self.store.con.execute(f'SELECT DISTINCT "{key}" FROM observations ORDER BY 1').fetchall()]
            combo.addItems(values)
            if old in values:combo.setCurrentText(old)
        self.explorer_positions(self.filters['format'].currentText());self.refresh_explorer();self.refresh_import();self.refresh_players();self.refresh_leaks();self.refresh_strategies();self.refresh_references()
        docs=self.store.documents('rules')
        if docs:self.rules.setPlainText(json.dumps(docs[0]['payload'],indent=2))
        self.show_rules()

    def closeEvent(self,event):
        if (self.worker and self.worker.isRunning()) or (self.sequence_panel.worker and self.sequence_panel.worker.isRunning()):QMessageBox.information(self,'Importación en curso','Espera a que termine la importación antes de cerrar.');event.ignore();return
        self.store.save_document('preferences','sequence',dict(pattern=self.sequence_panel.pattern.to_dict(),filters=self.sequence_panel.current_filters()))
        self.store.close();event.accept()


class PrepareDatabase(QThread):
    progress=Signal(int)
    def __init__(self,path):super().__init__();self.path=path;self.error=None
    def run(self):
        try:
            s=Store(self.path,progress=self.progress.emit,cancelled=self.isInterruptionRequested);s.close()
        except Exception as exc:self.error=str(exc)


def main():
    import argparse,sys
    p=argparse.ArgumentParser();p.add_argument('--db');args=p.parse_args()
    app=QApplication(sys.argv);app.setApplicationName('Spin Population Lab');app.setFont(QFont('Segoe UI',10))
    loading=QProgressDialog('Preparando base local. Si hay una migración, se crea un backup antes de actualizar.','Cancelar',0,0);loading.setWindowTitle('Spin Population Lab');loading.setMinimumDuration(0);loading.setMinimumWidth(540);loading.show()
    preparation=PrepareDatabase(args.db);loop=QEventLoop();preparation.finished.connect(loop.quit);preparation.progress.connect(lambda n:loading.setLabelText(f'Migrando contexto: {n:,} decisiones reconstruidas.'))
    loading.canceled.connect(preparation.requestInterruption);preparation.start();loop.exec();loading.close()
    if preparation.error:QMessageBox.critical(None,'Preparación interrumpida',preparation.error);return 1
    if preparation.isInterruptionRequested():return 0
    w=Window(args.db);w.showMaximized();return app.exec()
