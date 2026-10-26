from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from src.sequence_ui import SequencePanel
from src.store import Store
from src.presets import PRESETS


def test_search_navigation_keeps_indices_and_does_not_touch_data(tmp_path):
    app=QApplication.instance() or QApplication([])
    s=Store(tmp_path/'p.duckdb');panel=SequencePanel(s);before=s.totals()
    panel.date_from.setText('2026-01-01');panel.low.setValue(8)
    panel.preset_search.setText('LÍMPED barrel')
    assert panel.search_results.count()>0
    item=panel.search_results.item(0);index=item.data(Qt.UserRole)
    panel.open_search_result(item)
    assert panel.presets.currentIndex()==index and panel.pattern==PRESETS[index].pattern
    assert panel.date_from.text()=='2026-01-01' and panel.low.value()==8
    assert not panel.preset_search.text()
    panel.preset_search.setText('3H limped')
    assert panel.search_results.count()>0
    panel.open_search_result(panel.search_results.item(0))
    assert panel.filters['format'].currentText()=='3H' and panel.filters['position'].findText('BTN')>=0
    panel.preset_search.setText('does-not-exist')
    assert panel.search_results.count()==0 and 'Sin coincidencias' in panel.search_status.text()
    assert s.totals()==before
    panel.close();s.close()
