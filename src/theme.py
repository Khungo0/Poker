"""Native Qt desktop theme: compact controls, quiet surfaces, clear hierarchy."""
DARK = '''
QWidget { background:#11151c; color:#dce3ec; font-family:"Segoe UI"; font-size:13px; }
QMainWindow { background:#11151c; }
QLabel { background:transparent; }
QLabel#title { font-size:25px; font-weight:600; color:#f4f7fb; }
QLabel#muted { color:#8897aa; }
QLabel#metric { background:#1a2230; border:1px solid #293545; border-radius:8px; padding:14px; font-size:19px; }
QFrame#metricCard { background:#19212c; border:1px solid #293545; border-radius:8px; }
QLabel#metricValue { font-size:28px; font-weight:600; color:#f3f7fc; }
QWidget#sidebar { background:#151c26; border-right:1px solid #253142; }
QListWidget { background:#151c26; border:0; padding:8px; min-width:190px; outline:0; }
QListWidget::item { padding:14px 12px; margin:2px; border-radius:6px; color:#9aabc0; }
QListWidget::item:hover { background:#1c2938; }
QListWidget::item:selected { background:#21384a; color:#83dace; border-left:3px solid #5bceba; }
QPushButton { background:#24354a; border:1px solid #344b63; border-radius:5px; padding:8px 13px; color:#e2edf7; }
QPushButton:hover { background:#304860; border-color:#5d8a9c; }
QPushButton:pressed { background:#1a293b; }
QPushButton:disabled { color:#647487; border-color:#293545; background:#1a222e; }
QPushButton#primary { background:#277b70; border-color:#3f9e91; color:white; font-weight:600; }
QPushButton#primary:hover { background:#328e81; }
QComboBox,QDoubleSpinBox,QSpinBox,QLineEdit,QPlainTextEdit { background:#18212e; border:1px solid #334154; border-radius:4px; padding:7px; selection-background-color:#2f655e; }
QComboBox:focus,QLineEdit:focus,QDoubleSpinBox:focus { border-color:#5bceba; }
QComboBox QAbstractItemView { background:#1c2938; selection-background-color:#2c514f; padding:4px; }
QGroupBox { border:1px solid #2b394b; border-radius:6px; margin-top:12px; padding:12px 8px 8px; font-weight:600; }
QGroupBox::title { subcontrol-origin:margin; left:10px; padding:0 6px; color:#a1b3c8; }
QTableWidget,QTreeWidget { background:#141d29; alternate-background-color:#192432; border:1px solid #29384a; gridline-color:#223043; selection-background-color:#274e50; outline:0; }
QTableWidget::item { padding:5px; }
QTreeWidget::item { padding:10px 7px; }
QHeaderView::section { background:#1f2c3c; color:#93a9c2; padding:10px 8px; border:0; border-bottom:1px solid #34475c; font-weight:600; }
QTabWidget::pane { border:1px solid #29384a; border-radius:5px; }
QTabBar::tab { background:#182331; color:#8fa3bb; padding:10px 19px; border-bottom:2px solid transparent; }
QTabBar::tab:selected { background:#213142; color:#a0e6d9; border-bottom:2px solid #5bceba; }
QScrollArea { border:0; }
QScrollBar:vertical { background:#131b25; width:10px; margin:0; }
QScrollBar::handle:vertical { background:#35465b; border-radius:4px; min-height:24px; }
QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical { height:0; }
QSplitter::handle { background:#263446; width:3px; height:3px; }
QProgressBar { background:#202f40; border:0; border-radius:3px; max-height:7px; }
QProgressBar::chunk { background:#5bceba; }
QToolTip { background:#283d50; color:#f0f6ff; border:1px solid #4e677d; padding:7px; }
'''
