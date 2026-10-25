"""Offline desktop workspace. Import runs in a worker; SQL aggregates in DuckDB."""
import csv,json
from pathlib import Path
from PySide6.QtCore import Qt,QThread,Signal
from PySide6.QtGui import QColor,QPainter,QFont
from PySide6.QtWidgets import (QApplication,QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QGridLayout,QLabel,QPushButton,QListWidget,QStackedWidget,QComboBox,QDoubleSpinBox,QSpinBox,QCheckBox,QTableWidget,QTableWidgetItem,QHeaderView,QFileDialog,QMessageBox,QPlainTextEdit,QLineEdit,QFormLayout,QSplitter,QScrollArea)
from .store import Store
from .research import explore,player_profiles,classify,leaks,save_strategy,import_reference,terminal_bet_ev,validate_baseline,selection,FROM

DARK='''
QWidget {background:#10151e;color:#dfe6f2;font-family:Segoe UI;font-size:14px;}
QMainWindow {background:#10151e;}
QLabel#title {font-size:28px;font-weight:700;} QLabel#muted {color:#8d9bb0;}
QLabel#metric {background:#192231;border-radius:8px;padding:16px;font-size:20px;}
QListWidget {background:#141c28;border:0;padding:12px;min-width:200px;} QListWidget::item {padding:17px 10px;border-radius:6px;} QListWidget::item:selected {background:#243a48;color:#68e0bd;}
QPushButton {background:#24473f;color:#8cf2cd;border:1px solid #3b6c5c;border-radius:5px;padding:9px 15px;} QPushButton:hover {background:#315e51;} QPushButton:disabled {color:#657181;}
QComboBox,QDoubleSpinBox,QLineEdit,QPlainTextEdit {background:#192231;border:1px solid #334054;border-radius:4px;padding:6px;}
QTableWidget {background:#151d29;alternate-background-color:#192330;gridline-color:#273348;border:1px solid #273348;selection-background-color:#315448;}
QHeaderView::section {background:#202d3f;color:#9eadc3;padding:8px;border:0;} QScrollArea {border:0;} QSplitter::handle {background:#263346;}
'''


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
            p.fillRect(160,y,int(width*r['frequency']),23,QColor('#53cba6'))
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
                r=s.import_file(path)
                for k,v in r.items():
                    if isinstance(v,int):totals[k]=totals.get(k,0)+v
                self.progress.emit(f'{i+1}/{len(self.files)} archivos · {totals.get("added",0):,} manos nuevas')
            self.done.emit(json.dumps(totals,ensure_ascii=False,indent=2))
        except Exception as e:self.failed.emit(str(e))
        finally:
            if s:s.close()


class Window(QMainWindow):
    def __init__(self,path=None):
        super().__init__();self.store=Store(path);self.worker=None;self.setWindowTitle('Spin Population Lab · Offline');self.resize(1720,960);self.setMinimumSize(1180,760)
        root=QWidget();self.setCentralWidget(root);layout=QHBoxLayout(root);layout.setContentsMargins(0,0,0,0)
        side=QWidget();sl=QVBoxLayout(side);logo=QLabel('♠  SPIN LAB');logo.setObjectName('title');sl.addWidget(logo)
        self.nav=QListWidget();self.nav.addItems(['Population Explorer','Importar historiales','Regulares y Fishes','Leak Finder','Strategy Builder','Referencias y EV']);sl.addWidget(self.nav)
        sl.addWidget(QLabel('iPoker / ChampionPoker\nEstudio offline · Datos locales'));side.setMaximumWidth(265);layout.addWidget(side)
        self.stack=QStackedWidget();layout.addWidget(self.stack,1)
        self.build_explorer();self.build_import();self.build_players();self.build_leaks();self.build_strategies();self.build_references()
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
        box=self.page('Population Explorer','Decisiones observadas · IC Wilson 95% · Actor y rival se filtran por separado')
        self.kpis=QLabel();self.kpis.setObjectName('metric');box.addWidget(self.kpis)
        grid=QGridLayout();self.filters={}
        for i,(key,title) in enumerate([('spot','Spot'),('population','Actor'),('opponent_population','Rival directo'),('format','Modalidad HU/3H'),('stake','Buy-in total'),('street','Calle'),('position','Posición'),('texture','Textura'),('previous','Acción anterior')]):
            combo=QComboBox();combo.setMinimumWidth(130);self.filters[key]=combo
            grid.addWidget(QLabel(title),2*(i//5),i%5);grid.addWidget(combo,2*(i//5)+1,i%5)
        box.addLayout(grid)
        rangebox=QHBoxLayout();self.lo=QDoubleSpinBox();self.hi=QDoubleSpinBox()
        for spin,val in [(self.lo,0),(self.hi,100)]:spin.setRange(0,1000);spin.setValue(val)
        rangebox.addWidget(QLabel('Stack efectivo (BB)'));rangebox.addWidget(self.lo);rangebox.addWidget(self.hi)
        self.extra=QLineEdit('{}');self.extra.hide();rangebox.addWidget(QLabel('Apuesta previa (% bote)'));self.size_lo=QDoubleSpinBox();self.size_hi=QDoubleSpinBox()
        for spin,val in [(self.size_lo,0),(self.size_hi,1000)]:spin.setRange(0,10000);spin.setValue(val);rangebox.addWidget(spin)
        self.size_mode=QComboBox();self.size_mode.addItems(['Todos los tamaños','Filtrar apuesta previa']);rangebox.addWidget(self.size_mode)
        self.button(rangebox,'Investigar',self.refresh_explorer);self.button(rangebox,'Exportar CSV',self.export_csv);box.addLayout(rangebox)
        advanced=QHBoxLayout();self.path_filter=QLineEdit();self.path_filter.setPlaceholderText('Secuencia exacta opcional, p. ej. 1:BTN:fold > 1:SB:limp');advanced.addWidget(self.path_filter,1);self.actor_filter=QLineEdit();self.actor_filter.setPlaceholderText('Jugador concreto (opcional)');advanced.addWidget(self.actor_filter);self.include_hero=QCheckBox('Incluir Hero');advanced.addWidget(self.include_hero);box.addLayout(advanced)
        split=QSplitter(Qt.Vertical);self.results=table();self.chart=Bars();split.addWidget(self.results);split.addWidget(self.chart);box.addWidget(split,1)
        self.notice=QLabel('');self.notice.setWordWrap(True);box.addWidget(self.notice)
        buttons=QHBoxLayout();self.button(buttons,'Inspeccionar manos del spot',self.inspect_hands);self.button(buttons,'Matriz de cartas observadas',self.show_range);box.addLayout(buttons)

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
                data=self.store.con.execute('SELECT raw,events FROM hands WHERE hand_id=?',[rows[i]['hand_id']]).fetchone();raw.setPlainText(data[0]+'\n\nRECONSTRUCCIÓN (céntimos)\n'+json.dumps(json.loads(data[1]),indent=2))
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
        self.import_buttons.append(self.button(row,'Importar carpeta',lambda:self.choose_import(True)));box.addLayout(row)
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
        self.import_status.setText(json.dumps(self.store.totals(),ensure_ascii=False))
        fill(self.error_table,self.store.rows('SELECT source,hand_id,error FROM errors LIMIT 500'))

    def build_players(self):
        box=self.page('Regulares y Fishes','Sin clasificar por defecto · Etiquetas manuales prioritarias · Confianza automática heurística')
        self.players_table=table();box.addWidget(self.players_table,1)
        row=QHBoxLayout();self.player_name=QLineEdit();self.player_name.setPlaceholderText('Jugador exacto');self.category=QComboBox();self.category.addItems(['Sin clasificar','Reg','Fish']);row.addWidget(self.player_name,1);row.addWidget(self.category)
        self.button(row,'Guardar etiqueta',self.save_label);box.addLayout(row)
        self.players_table.cellClicked.connect(lambda i,j:self.player_name.setText(self.players_table.item(i,0).text()))
        box.addWidget(QLabel('Reglas: el IC95 completo debe caber en el intervalo. Mínimo 30 manos con decisión; conflictos quedan sin clasificar.'))
        rf=QHBoxLayout();self.rule_category=QComboBox();self.rule_category.addItems(['Reg','Fish']);self.rule_metric=QComboBox();self.rule_metric.addItems(['vpip','pfr']);self.rule_low=QDoubleSpinBox();self.rule_high=QDoubleSpinBox();self.rule_min=QSpinBox();self.rule_min.setRange(30,1000000);self.rule_min.setValue(200)
        for spin,value in [(self.rule_low,0),(self.rule_high,100)]:spin.setRange(0,100);spin.setValue(value);spin.setSuffix('%')
        for label,w in [('Clase',self.rule_category),('Métrica',self.rule_metric),('Desde',self.rule_low),('Hasta',self.rule_high),('Muestra mínima',self.rule_min)]:rf.addWidget(QLabel(label));rf.addWidget(w)
        self.button(rf,'Añadir regla',self.add_rule);box.addLayout(rf)
        self.rules=QPlainTextEdit('[]');self.rules.setMaximumHeight(140);box.addWidget(self.rules)
        self.button(box,'Aplicar reglas',lambda:(classify(self.store,json.loads(self.rules.toPlainText())),self.refresh_players()))

    def add_rule(self):
        rules=json.loads(self.rules.toPlainText());rules.append(dict(category=self.rule_category.currentText(),metric=self.rule_metric.currentText(),low=self.rule_low.value()/100,high=self.rule_high.value()/100,min_hands=self.rule_min.value()));self.rules.setPlainText(json.dumps(rules,indent=2))

    def save_label(self):
        if not self.player_name.text().strip():raise ValueError('Selecciona un jugador')
        self.store.label(self.player_name.text(),self.category.currentText());self.refresh_players();self.refresh_explorer()

    def refresh_players(self):fill(self.players_table,player_profiles(self.store))

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
        form=QFormLayout();self.strategy_name=QLineEdit();self.strategy_population=QComboBox();self.strategy_population.addItems(['Reg','Fish']);self.strategy_action=QLineEdit();self.strategy_filters=QLineEdit('{}');self.strategy_reason=QPlainTextEdit();self.strategy_reason.setMaximumHeight(150)
        for title,w in [('Nombre',self.strategy_name),('Población',self.strategy_population),('Filtros del spot (JSON)',self.strategy_filters),('Acción propuesta',self.strategy_action),('Evidencia y razonamiento',self.strategy_reason)]:form.addRow(title,w)
        box.addLayout(form);row=QHBoxLayout();self.button(row,'Copiar selección del Explorer',lambda:self.strategy_filters.setText(json.dumps(self.current_filters())));self.button(row,'Guardar estrategia',self.save_strategy);self.button(row,'Exportar estrategias',self.export_strategies);box.addLayout(row)
        self.strategy_table=table();box.addWidget(self.strategy_table,1)
        self.strategy_table.cellClicked.connect(self.load_strategy)

    def save_strategy(self):
        save_strategy(self.store,self.strategy_name.text(),dict(population=self.strategy_population.currentText(),filters=json.loads(self.strategy_filters.text()),action=self.strategy_action.text(),rationale=self.strategy_reason.toPlainText()));self.refresh_strategies()
    def refresh_strategies(self):
        self.strategy_docs=self.store.documents('strategy');fill(self.strategy_table,[dict(name=d['name'],**d['payload']) for d in self.strategy_docs])
    def load_strategy(self,i,j):
        d=self.strategy_docs[i];p=d['payload'];self.strategy_name.setText(d['name']);self.strategy_population.setCurrentText(p['population']);self.strategy_action.setText(p['action']);self.strategy_filters.setText(json.dumps(p['filters']));self.strategy_reason.setPlainText(p['rationale'])
    def export_strategies(self):
        name,_=QFileDialog.getSaveFileName(self,'Exportar estrategias','strategies.json','JSON (*.json)')
        if name:Path(name).write_text(json.dumps(self.store.documents('strategy'),ensure_ascii=False,indent=2),encoding='utf-8')

    def build_references(self):
        box=self.page('Referencias y EV condicional','Importa referencias propias mediante el esquema JSON documentado. No se infieren rangos desde cartas ocultas.')
        self.button(box,'Importar referencia JSON',self.load_reference);self.references_table=table();box.addWidget(self.references_table,1)
        box.addWidget(QLabel('Modelo limitado: apuesta terminal HU, rival solo foldea o paga, sin raises ni apuestas futuras. Equity aportada por ti.'))
        self.ev_input=QPlainTextEdit('{}');self.ev_input.setPlaceholderText('JSON: pot, bet, folds, opportunities, equity_when_called');self.ev_input.setMaximumHeight(130);box.addWidget(self.ev_input)
        self.ev_result=QLabel('EV sin estimar: faltan supuestos y datos.');self.ev_result.setWordWrap(True)
        self.button(box,'Evaluar escenario condicional',lambda:self.ev_result.setText(json.dumps(terminal_bet_ev(**json.loads(self.ev_input.toPlainText())),ensure_ascii=False,indent=2)));box.addWidget(self.ev_result)
    def load_reference(self):
        name,_=QFileDialog.getOpenFileName(self,'Referencia',filter='JSON (*.json)')
        if name:import_reference(self.store,Path(name).stem,json.loads(Path(name).read_text(encoding='utf-8')));self.refresh_references()
    def refresh_references(self):fill(self.references_table,self.store.documents('reference'))

    def refresh_all(self):
        for key,combo in self.filters.items():
            old=combo.currentText();combo.clear();combo.addItem('Todos')
            values=['Reg','Fish','Sin clasificar'] if key in ('population','opponent_population') else [str(r[0]) for r in self.store.con.execute(f'SELECT DISTINCT "{key}" FROM observations ORDER BY 1').fetchall()]
            combo.addItems(values)
            if old in values:combo.setCurrentText(old)
        self.refresh_explorer();self.refresh_import();self.refresh_players();self.refresh_leaks();self.refresh_strategies();self.refresh_references()
        docs=self.store.documents('rules')
        if docs:self.rules.setPlainText(json.dumps(docs[0]['payload'],indent=2))

    def closeEvent(self,event):
        if self.worker and self.worker.isRunning():QMessageBox.information(self,'Importación en curso','Espera a que termine la importación antes de cerrar.');event.ignore();return
        self.store.close();event.accept()


def main():
    import argparse,sys
    p=argparse.ArgumentParser();p.add_argument('--db');args=p.parse_args()
    app=QApplication(sys.argv);app.setApplicationName('Spin Population Lab');app.setFont(QFont('Segoe UI',10))
    w=Window(args.db);w.showMaximized();return app.exec()
