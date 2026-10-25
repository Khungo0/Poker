import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from src.desktop import Window
from pathlib import Path


def test_desktop_real_data_pages_and_resolutions(tmp_path):
    app=QApplication.instance() or QApplication([])
    window=Window(tmp_path/'ui.duckdb')
    window.store.import_file(Path(__file__).parent/'fixtures/ipoker_real_anonymized.txt')
    window.refresh_all()
    window.filters['spot'].setCurrentText('BTN_FIRST');window.refresh_explorer()
    assert window.results.rowCount()>0
    depth=len(window.sequence_panel.history)
    window.dashboard.open_sequence(1)
    for _ in range(500):
        app.processEvents();QTest.qWait(10)
        if not window.sequence_panel.worker.isRunning():break
    app.processEvents()
    assert not window.sequence_panel.worker.isRunning()
    assert len(window.sequence_panel.history)==depth+1
    assert window.sequence_panel.last is not None
    for width,height in [(1920,1080),(2560,1440)]:
        window.resize(width,height);window.show();app.processEvents()
        assert window.width()==width
        for page in range(window.stack.count()):
            window.nav.setCurrentRow(page);app.processEvents()
            assert window.stack.currentIndex()==page
    window.close()
