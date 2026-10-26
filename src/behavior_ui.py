"""Observed metrics and graphical evidence rules, with virtualized result rows."""
import json
from PySide6.QtCore import Qt,QAbstractTableModel,QSortFilterProxyModel,QThread,Signal
from PySide6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QFormLayout,QLineEdit,QComboBox,QDoubleSpinBox,QSpinBox,QPushButton,QLabel,QListWidget,QSplitter,QScrollArea,QTableView,QTabWidget,QDialog,QStyledItemDelegate,QFileDialog)
from PySide6.QtGui import QColor
from .behavior import player_metrics,preview_rules,apply_rules,save_population,undo_classification,NAMES,COUNTS
from .store import Store
from .profiles import PROFILES


class EvidenceModel(QAbstractTableModel):
    def __init__(self,columns):super().__init__();self.columns=columns;self.rows=[]
    def replace(self,rows):self.beginResetModel();self.rows=rows;self.endResetModel()
    def rowCount(self,parent=None):return 0 if parent and parent.isValid() else len(self.rows)
    def columnCount(self,parent=None):return len(self.columns)
    def headerData(self,section,orientation,role=Qt.DisplayRole):
        if role==Qt.DisplayRole:return self.columns[section][1] if orientation==Qt.Horizontal else section+1
    def data(self,index,role=Qt.DisplayRole):
        if not index.isValid():return None
        key=self.columns[index.column()][0];value=self.rows[index.row()].get(key)
        if role==Qt.UserRole:return value
        if role==Qt.TextAlignmentRole:return int(Qt.AlignVCenter | (Qt.AlignRight if isinstance(value,(int,float)) else Qt.AlignLeft))
        if role in (Qt.DisplayRole,Qt.ToolTipRole):
            if value is None:return '—'
            if key in ('frequency','ci_low','ci_high'):return f'{value:.1%}'
            return str(value)


class FrequencyDelegate(QStyledItemDelegate):
    def paint(self,painter,option,index):
        value=index.data(Qt.UserRole)
        super().paint(painter,option,index)
        if isinstance(value,(int,float)):
            painter.save();painter.setPen(Qt.NoPen);painter.setBrush(QColor('#42b9a6'));r=option.rect.adjusted(5,option.rect.height()-5,-5,-2);r.setWidth(int(r.width()*max(0,min(1,value))));painter.drawRect(r);painter.restore()


class MetricsWorker(QThread):
    ready=Signal(object);failed=Signal(str)
    def __init__(self,path,filters,rules):super().__init__();self.path=path;self.filters=filters;self.rules=rules;self.connection=None
    def run(self):
        s=None
        try:
            s=Store(self.path);self.connection=s.con
            if self.isInterruptionRequested():return
            revision=(s.totals(),s.con.execute('SELECT count(*) FROM label_history').fetchone()[0])
            metrics=player_metrics(s,self.filters);preview=preview_rules(s,self.rules,self.filters,metrics=metrics) if self.rules else []
            if not self.isInterruptionRequested():self.ready.emit(dict(metrics=metrics,preview=preview,filters=self.filters,rules=self.rules,revision=revision))
        except Exception as exc:
            if not self.isInterruptionRequested():self.failed.emit(str(exc))
        finally:
            self.connection=None
            if s:s.close()
    def stop(self):
        self.requestInterruption()
        if self.connection:
            try:self.connection.interrupt()
            except Exception:pass


class BehaviorPanel(QWidget):
    populationsChanged=Signal()
    def __init__(self,store):
        super().__init__();self.store=store;self.conditions=[];self.rule_set=[];self.worker=None;self.last=None
        outer=QVBoxLayout(self);outer.addWidget(QLabel('Comportamientos observados · sin umbrales universales ni inferencia de jugadores ganadores'))
        split=QSplitter();outer.addWidget(split,1);scroll=QScrollArea();self.editor_scroll=scroll;scroll.setWidgetResizable(True);editor=QWidget();v=QVBoxLayout(editor);scroll.setWidget(editor);split.addWidget(scroll)
        form=QFormLayout();form.setRowWrapPolicy(QFormLayout.WrapLongRows);self.format=QComboBox();self.format.addItems(['HU','3H']);form.addRow('Estado de la mano',self.format)
        self.stake=QComboBox();self.stake.addItems(['Todos']+[r[0] for r in store.con.execute('SELECT DISTINCT stake FROM hands ORDER BY stake').fetchall()]);form.addRow('Stake',self.stake)
        self.from_date=QLineEdit();self.from_date.setPlaceholderText('AAAA-MM-DD, opcional');form.addRow('Desde',self.from_date)
        self.to_date=QLineEdit();self.to_date.setPlaceholderText('AAAA-MM-DD, opcional');form.addRow('Hasta',self.to_date)
        self.actor=QLineEdit();form.addRow('Jugador, opcional',self.actor)
        self.opponent=QComboBox();self.opponent.addItems(['Todos','Reg','Fish','Sin clasificar']);form.addRow('Rival directo',self.opponent)
        self.stack_low=QDoubleSpinBox();self.stack_high=QDoubleSpinBox()
        for w,val in ((self.stack_low,0),(self.stack_high,1000)):w.setRange(0,10000);w.setValue(val)
        form.addRow('Stack inicial efectivo BB',self.stack_low);form.addRow('Hasta BB',self.stack_high);v.addLayout(form)
        self.load=QPushButton('Calcular métricas / previsualizar');self.load.setObjectName('primary');self.load.clicked.connect(self.run);v.addWidget(self.load)
        cancel=QPushButton('Cancelar consulta');cancel.clicked.connect(lambda:self.worker.stop() if self.worker else None);v.addWidget(cancel)
        form=QFormLayout();form.setRowWrapPolicy(QFormLayout.WrapLongRows);self.metric_combo=QComboBox()
        for key,name in NAMES.items():self.metric_combo.addItem(name,key)
        form.addRow('Condición observada',self.metric_combo);self.low=QDoubleSpinBox();self.high=QDoubleSpinBox();self.minimum=QSpinBox();self.minimum.setRange(30,1000000);self.minimum.setValue(100)
        form.addRow('Límite inferior',self.low);form.addRow('Límite superior',self.high);form.addRow('Oportunidades mínimas',self.minimum);v.addLayout(form)
        self.metric_combo.currentIndexChanged.connect(self.metric_changed);self.metric_changed()
        add=QPushButton('Añadir condición');add.clicked.connect(self.add_condition);v.addWidget(add)
        self.logic=QComboBox();self.logic.addItems(['AND','OR']);v.addWidget(self.logic);self.condition_list=QListWidget();self.condition_list.setMaximumHeight(130);v.addWidget(self.condition_list)
        remove=QPushButton('Eliminar condición');remove.clicked.connect(self.remove_condition);v.addWidget(remove)
        self.name=QLineEdit();self.name.setPlaceholderText('Nombre de regla / población');v.addWidget(self.name)
        self.saved_groups=QComboBox();self.refresh_saved_groups();v.addWidget(self.saved_groups);load_group=QPushButton('Recuperar población y editar criterios');load_group.clicked.connect(self.load_group);v.addWidget(load_group)
        row=QHBoxLayout();self.category=QComboBox();self.category.addItems(['Reg','Fish']);self.profile=QComboBox();self.category.currentTextChanged.connect(self.profile_changed);self.profile_changed();row.addWidget(self.category);row.addWidget(self.profile);v.addLayout(row)
        self.weight=QDoubleSpinBox();self.weight.setRange(.01,1000);self.weight.setValue(1);v.addWidget(QLabel('Puntuación configurable; no es una probabilidad'));v.addWidget(self.weight)
        remember=QPushButton('Añadir regla al conjunto');remember.clicked.connect(self.add_rule);v.addWidget(remember)
        self.rule_list=QListWidget();self.rule_list.setMaximumHeight(100);v.addWidget(self.rule_list)
        remove_rule=QPushButton('Quitar regla del conjunto');remove_rule.clicked.connect(self.remove_rule);v.addWidget(remove_rule)
        load_rules=QPushButton('Recuperar últimas reglas aplicadas');load_rules.clicked.connect(self.load_active);v.addWidget(load_rules)
        save=QPushButton('Guardar población sin cambiar etiquetas');save.clicked.connect(self.save_group);v.addWidget(save)
        apply=QPushButton('Aplicar clasificación previsualizada');apply.clicked.connect(self.apply);v.addWidget(apply);undo=QPushButton('Deshacer última aplicación de esta sesión');undo.clicked.connect(self.undo);v.addWidget(undo);v.addStretch()
        for combo in editor.findChildren(QComboBox):combo.setMinimumContentsLength(12);combo.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        for label in editor.findChildren(QLabel):label.setWordWrap(True)
        tabs=QTabWidget();split.addWidget(tabs);split.setSizes([380,900]);split.setStretchFactor(1,1)
        self.models=[];self.views=[]
        for title,columns in [('Métricas',[('player','Jugador'),('name','Métrica'),('value','Volumen'),('cases','Casos'),('opportunities','Oportunidades'),('frequency','Frecuencia'),('ci_low','IC95 inferior'),('ci_high','IC95 superior')]),('Vista previa',[('player','Jugador'),('category','Población'),('profile','Subperfil'),('status','Estado'),('score','Puntuación')])]:
            page=QWidget();layout=QVBoxLayout(page);search=QLineEdit();search.setPlaceholderText('Buscar en resultados');layout.addWidget(search);model=EvidenceModel(columns);proxy=QSortFilterProxyModel();proxy.setSourceModel(model);proxy.setFilterKeyColumn(-1);proxy.setFilterCaseSensitivity(Qt.CaseInsensitive);proxy.setSortRole(Qt.UserRole);search.textChanged.connect(proxy.setFilterFixedString)
            view=QTableView();view.setModel(proxy);view.setSortingEnabled(True);view.setAlternatingRowColors(True);view.setSelectionBehavior(QTableView.SelectRows);view.setEditTriggers(QTableView.NoEditTriggers);view.horizontalHeader().setStretchLastSection(True);view.verticalHeader().hide()
            for i,(key,_) in enumerate(columns):
                if key=='frequency':view.setItemDelegateForColumn(i,FrequencyDelegate(view))
            layout.addWidget(view);export=QPushButton('Exportar filas visibles CSV');export.clicked.connect(lambda checked=False,p=proxy:self.export_rows(p));layout.addWidget(export);tabs.addTab(page,title);self.models.append(model);self.views.append(view)
        self.views[1].doubleClicked.connect(self.show_evidence)
        self.status=QLabel('Define tus condiciones y consulta. Sin etiquetas ni reglas iniciales inventadas. Doble clic en una propuesta para revisar evidencia.');self.status.setWordWrap(True);outer.addWidget(self.status)
    def refresh_saved_groups(self):
        self.saved_groups.clear();self.saved_groups.addItems([d['name'] for d in self.store.documents('population')])
    def apply_context(self,f):
        self.format.setCurrentText(f.get('format','HU'));self.stake.setCurrentText(f.get('stake','Todos'));self.from_date.setText(f.get('date_from',''));self.to_date.setText(f.get('date_to',''));self.actor.setText(f.get('actor',''));self.opponent.setCurrentText(f.get('opponent_population','Todos'));lo,hi=f.get('initial_eff_bb',[0,1000]);self.stack_low.setValue(lo);self.stack_high.setValue(hi)
    def load_group(self):
        doc=next((d for d in self.store.documents('population') if d['name']==self.saved_groups.currentText()),None)
        if not doc:return
        node=doc['payload']['condition'];conditions=node.get('conditions',[node])
        if any('metric' not in c for c in conditions):self.status.setText('Este grupo contiene niveles anidados; el editor visual actual permite un nivel AND/OR.');return
        self.conditions=json.loads(json.dumps(conditions));self.rule_set=[];self.logic.setCurrentText(node.get('op','AND'));self.name.setText(doc['name']);self.apply_context(doc['payload']['filters']);self.render_conditions();self.render_rules();self.last=None;self.status.setText('Criterios recuperados. Guardar con el mismo nombre actualiza explícitamente la membresía; etiquetas sin cambios.')
    def metric_changed(self,*args):
        count=self.metric_combo.currentData() in COUNTS
        for w in (self.low,self.high):w.setRange(0,1000000 if count else 100);w.setSuffix('' if count else '%')
        self.low.setValue(0);self.high.setValue(1000000 if count else 100);self.minimum.setEnabled(not count)
    def profile_changed(self,*args):self.profile.clear();self.profile.addItems(['Sin subperfil']+PROFILES[self.category.currentText()])
    def add_condition(self):
        scale=1 if self.metric_combo.currentData() in COUNTS else 100
        self.conditions.append(dict(metric=self.metric_combo.currentData(),low=self.low.value()/scale,high=self.high.value()/scale,min_opportunities=self.minimum.value()));self.render_conditions()
    def remove_condition(self):
        index=self.condition_list.currentRow()
        if index>=0:self.conditions.pop(index);self.render_conditions()
    def render_conditions(self):
        self.condition_list.clear()
        for c in self.conditions:
            interval=f"{c['low']:g}–{c['high']:g} · volumen" if c['metric'] in COUNTS else f"{c['low']:.1%}–{c['high']:.1%} · mínimo {c['min_opportunities']} oportunidades"
            self.condition_list.addItem(NAMES[c['metric']]+' · '+interval)
    def filters(self):
        f=dict(format=self.format.currentText(),initial_eff_bb=[self.stack_low.value(),self.stack_high.value()])
        for key,value in [('stake',self.stake.currentText()),('date_from',self.from_date.text().strip()),('date_to',self.to_date.text().strip()),('actor',self.actor.text().strip()),('opponent_population',self.opponent.currentText())]:
            if value and value!='Todos':f[key]=value
        return f
    def rules(self):
        if not self.conditions:return list(self.rule_set)
        return list(self.rule_set)+[dict(name=self.name.text().strip() or 'Regla de estudio',category=self.category.currentText(),profile=None if self.profile.currentIndex()==0 else self.profile.currentText(),weight=self.weight.value(),condition=dict(op=self.logic.currentText(),conditions=list(self.conditions)))]
    def add_rule(self):
        if not self.conditions:self.status.setText('Añade condiciones para crear una regla.');return
        self.rule_set.append(self.rules()[-1]);self.conditions=[];self.render_conditions();self.render_rules()
    def remove_rule(self):
        index=self.rule_list.currentRow()
        if index>=0:self.rule_set.pop(index);self.render_rules()
    def render_rules(self):
        self.rule_list.clear()
        for rule in self.rule_set:self.rule_list.addItem(f"{rule['name']} · {rule['category']} · {rule['condition']['op']} · peso {rule['weight']}")
    def load_active(self):
        doc=next((d['payload'] for d in self.store.documents('behavior_rules') if d['name']=='active'),None)
        if not doc:self.status.setText('Todavía no hay reglas multivariable aplicadas.');return
        self.rule_set=doc['rules'];self.conditions=[];self.render_conditions();self.render_rules();self.apply_context(doc['filters']);self.last=None;self.status.setText('Reglas recuperadas. Previsualiza antes de aplicar.')
    def run(self):
        if self.worker and self.worker.isRunning():return
        self.last=None;self.worker=MetricsWorker(self.store.path,self.filters(),self.rules());self.worker.ready.connect(self.receive);self.worker.failed.connect(self.status.setText);self.worker.finished.connect(lambda:self.load.setEnabled(True));self.load.setEnabled(False);self.status.setText('Calculando métricas y oportunidades…');self.worker.start()
    def receive(self,result):
        if result['filters']!=self.filters() or result['rules']!=self.rules():self.status.setText('Cambió la selección. Vuelve a consultar.');return
        self.last=result;self.models[0].replace(result['metrics']);self.models[1].replace(result['preview']);self.status.setText(f"{len(result['metrics'])} métricas observadas; {len(result['preview'])} propuestas. IC exploratorios; puntuaciones no calibradas. Los grupos guardados son snapshots explícitos.")
    def apply(self):
        if not self.last or not self.rules() or self.last['filters']!=self.filters() or self.last['rules']!=self.rules():self.status.setText('Previsualiza estas condiciones antes de aplicarlas.');return
        try:
            revision=(self.store.totals(),self.store.con.execute('SELECT count(*) FROM label_history').fetchone()[0])
            if revision!=self.last['revision']:raise ValueError('Los datos o etiquetas cambiaron: vuelve a previsualizar.')
            apply_rules(self.store,self.rules(),self.filters());self.last_run=max(self.store.documents('classification_run'),key=lambda d:d['payload']['recorded_at'])['name'];self.status.setText('Reglas aplicadas. Etiquetas manuales protegidas; automáticas del contexto reevaluadas.');self.populationsChanged.emit()
        except Exception as exc:self.status.setText(str(exc))
    def undo(self):
        try:
            if not getattr(self,'last_run',None):raise ValueError('Esta sesión no ha aplicado reglas multivariable.')
            undo_classification(self.store,self.last_run);self.status.setText('Clasificación anterior restaurada y auditada.');self.populationsChanged.emit()
        except Exception as exc:self.status.setText(str(exc))
    def save_group(self):
        if not self.name.text().strip() or not self.conditions:self.status.setText('Escribe un nombre y añade condiciones.');return
        try:
            payload=save_population(self.store,self.name.text().strip(),dict(op=self.logic.currentText(),conditions=list(self.conditions)),self.filters());self.status.setText(f"Población guardada: {len(payload['members'])} jugadores. Etiquetas sin cambios.");self.refresh_saved_groups();self.populationsChanged.emit()
        except Exception as exc:self.status.setText(str(exc))
    def export_rows(self,proxy):
        import csv
        path,_=QFileDialog.getSaveFileName(self,'Exportar filas visibles','behavior.csv','CSV (*.csv)')
        if not path:return
        try:
            columns=proxy.sourceModel().columns
            with open(path,'w',encoding='utf-8-sig',newline='') as stream:
                writer=csv.writer(stream);writer.writerow([title for key,title in columns])
                for row in range(proxy.rowCount()):writer.writerow([proxy.index(row,col).data(Qt.UserRole) for col in range(len(columns))])
        except Exception as exc:self.status.setText(str(exc))
    def show_evidence(self,index):
        source=self.views[1].model().mapToSource(index);proposal=self.models[1].rows[source.row()];rows=[]
        for rule in proposal['evidence']:
            for leaf in rule['conditions']:
                r=leaf['observed'] or {};c=leaf['condition'];rows.append(dict(rule=rule['name'],metric=NAMES[c['metric']],cases=r.get('cases'),opportunities=r.get('opportunities'),value=r.get('value'),frequency=r.get('frequency'),ci_low=r.get('ci_low'),ci_high=r.get('ci_high'),required=(f"{c['low']:g}–{c['high']:g}" if c['metric'] in COUNTS else f"{c['low']:.1%}–{c['high']:.1%}"),minimum=None if c['metric'] in COUNTS else c.get('min_opportunities',30),state='Sin evidencia' if leaf['state'] is None else 'Cumple' if leaf['state'] else 'No cumple'))
        dialog=QDialog(self);dialog.setWindowTitle('Evidencia · '+proposal['player']);dialog.resize(900,500);layout=QVBoxLayout(dialog);model=EvidenceModel([('rule','Regla'),('metric','Métrica'),('value','Volumen'),('cases','Casos'),('opportunities','Oportunidades'),('frequency','Frecuencia'),('ci_low','IC95 inferior'),('ci_high','IC95 superior'),('required','Intervalo exigido'),('minimum','Mínimo'),('state','Condición')]);model.replace(rows);view=QTableView();view.setModel(model);layout.addWidget(view);dialog.exec()
