from pathlib import Path

def test_explorer_background_query_and_player_selection(tmp_path):
    from PySide6.QtWidgets import QApplication
    from PySide6.QtTest import QTest
    from src.desktop import Window
    app=QApplication.instance() or QApplication([])
    w=Window(tmp_path/'ui.duckdb');w.store.import_file(Path(__file__).parent/'fixtures/ipoker_real_anonymized.txt');w.refresh_all()
    w.refresh_explorer(True)
    for _ in range(500):
        app.processEvents();QTest.qWait(10)
        if not w.explorer_worker.isRunning():break
    app.processEvents();assert not w.explorer_worker.isRunning() and w.explorer_run.isEnabled()
    assert w.results.rowCount()>0
    name=w.players_table.item(0,0).text();w.store.label(name,'Fish',profile='Calling station');w.refresh_players()
    row=next(i for i in range(w.players_table.rowCount()) if w.players_table.item(i,0).text()==name)
    w.select_player(row,0);assert w.category.currentText()=='Fish' and w.subprofile.currentText()=='Calling station'
    w.player_search.setText('no-such-player');assert all(w.players_table.isRowHidden(i) for i in range(w.players_table.rowCount()))
    w.close()
