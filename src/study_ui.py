"""Study overview and local backup controls; no synthetic insights."""
from pathlib import Path
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QListWidget,QFileDialog,QMessageBox
from .migrations import backup_database,restore_copy

class StudyDashboard(QWidget):
    def __init__(self,window):
        super().__init__();self.window=window;v=QVBoxLayout(self);v.setContentsMargins(28,24,28,24);v.setSpacing(16)
        title=QLabel('Tu espacio de investigación');title.setObjectName('title');v.addWidget(title)
        v.addWidget(QLabel('Spins 3-max · HU y 3H · estudio offline'))
        self.summary=QLabel();self.summary.setObjectName('metric');v.addWidget(self.summary)
        buttons=QHBoxLayout()
        for label,barrels in [('Respuesta a bet flop · limped pot',1),('Respuesta al segundo barrel',2),('Tercer barrel · respuestas',3)]:
            b=QPushButton(label);b.clicked.connect(lambda checked=False,n=barrels:self.open_sequence(n));buttons.addWidget(b)
        v.addLayout(buttons);v.addWidget(QLabel('Mis investigaciones guardadas'));self.investigations=QListWidget();self.investigations.itemDoubleClicked.connect(self.open_saved);v.addWidget(self.investigations,1)
        v.addWidget(QLabel('Estrategias de estudio'));self.strategies=QListWidget();v.addWidget(self.strategies,1)
        self.note=QLabel();self.note.setWordWrap(True);v.addWidget(self.note)
        refresh=QPushButton('Actualizar resumen');refresh.clicked.connect(self.refresh);v.addWidget(refresh);self.refresh()
    def refresh(self):
        s=self.window.store;t=s.totals();self.summary.setText(f"{t['hands']:,} manos  ·  {t['observations']:,} decisiones  ·  {t['errors']:,} registros en cuarentena")
        self.investigations.clear();self.investigations.addItems([d['name'] for d in s.documents('investigation')]);self.strategies.clear();self.strategies.addItems([d['name']+' · '+d['payload'].get('status','Hipótesis') for d in s.documents('strategy')])
        n=s.con.execute('SELECT count(*) FROM labels').fetchone()[0]
        self.note.setText(f'{n} jugadores etiquetados. Las comparaciones Reg/Fish usan tus etiquetas actuales; no se rellenan categorías ni referencias ausentes. Guarda tus investigaciones para retomarlas aquí.')
    def open_sequence(self,barrels):
        panel=self.window.sequence_panel;panel.presets.blockSignals(True);panel.presets.setCurrentIndex(3-barrels);panel.presets.blockSignals(False);panel.load_preset(3-barrels);self.window.nav.setCurrentRow(self.window.stack.indexOf(panel));panel.run()
    def open_saved(self,item):
        panel=self.window.sequence_panel;panel.refresh_saved();panel.saved.setCurrentText(item.text());self.window.nav.setCurrentRow(self.window.stack.indexOf(panel));panel.load_saved()


class SettingsPanel(QWidget):
    def __init__(self,window):
        super().__init__();self.window=window;v=QVBoxLayout(self);v.setContentsMargins(28,24,28,24)
        title=QLabel('Datos y configuración');title.setObjectName('title');v.addWidget(title)
        info=QLabel('Base local: '+str(window.store.path)+'\nLas actualizaciones conservan los originales. Antes de una migración se crea un backup verificado.');info.setWordWrap(True);v.addWidget(info)
        backup=QPushButton('Crear backup verificado');backup.clicked.connect(self.backup);v.addWidget(backup)
        restore=QPushButton('Restaurar backup como copia nueva');restore.clicked.connect(self.restore);v.addWidget(restore)
        self.status=QLabel('Conserva también la carpeta imports/ junto a tus backups. La restauración no sobrescribe la base que tienes abierta.');self.status.setWordWrap(True);v.addWidget(self.status);v.addStretch()
    def backup(self):
        if self.window.worker and self.window.worker.isRunning():self.status.setText('Espera a que finalice la importación antes del backup.');return
        try:self.status.setText('Backup verificado: '+str(backup_database(self.window.store.path,self.window.store.con)))
        except Exception as e:self.status.setText(str(e))
    def restore(self):
        source,_=QFileDialog.getOpenFileName(self,'Seleccionar backup',str(self.window.store.path.parent/'backups'),'DuckDB (*.duckdb)')
        if not source:return
        dest,_=QFileDialog.getSaveFileName(self,'Guardar copia restaurada',str(self.window.store.path.parent/'restaurada.duckdb'),'DuckDB (*.duckdb)')
        if not dest:return
        try:self.status.setText('Copia restaurada y verificada: '+str(restore_copy(source,dest)))
        except Exception as e:self.status.setText(str(e))
