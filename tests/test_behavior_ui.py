from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from src.desktop import Window
from src.behavior_ui import EvidenceModel


def test_graphical_metrics_group_and_context_filters(tmp_path):
    app=QApplication.instance() or QApplication([])
    w=Window(tmp_path/'p.duckdb');w.store.import_file(Path(__file__).parent/'fixtures/ipoker_real_anonymized.txt');w.refresh_all();p=w.behavior_panel
    p.metric_combo.setCurrentIndex(p.metric_combo.findData('hands'));p.low.setValue(1);p.high.setValue(1000000);p.add_condition();p.name.setText('Observed group');p.save_group()
    assert 'guardada' in p.status.text()
    p.conditions=[];p.load_group();assert p.conditions and p.name.text()=='Observed group'
    assert w.group_filters['actor_group'].findText('Observed group')>=0
    assert w.sequence_panel.filters['actor_group'].findText('Observed group')>=0
    p.run()
    for _ in range(500):
        app.processEvents();QTest.qWait(10)
        if not p.worker.isRunning():break
    app.processEvents();assert not p.worker.isRunning() and p.last
    assert p.models[0].rowCount()>0
    w.nav.setCurrentRow(3);w.population_workspace.setCurrentIndex(1)
    for width,height in [(1440,900),(1920,1080),(2560,1440)]:
        w.resize(width,height);w.show();app.processEvents();assert w.width()==width and w.height()==height
        app.processEvents();assert p.editor_scroll.horizontalScrollBar().maximum()==0
        assert callable(p.metric) and not p.grab().isNull()
    # Changing label evidence invalidates the reviewed cohort before application.
    w.store.label('Changed','Reg');p.apply();assert 'previsualizar' in p.status.text()
    w.close()
