from PyQt6.QtWidgets import QWidget, QVBoxLayout, QToolBar, QTabWidget, QFontComboBox, QSpinBox
from PyQt6.QtGui import QAction, QKeySequence
from ..icons import get_icon


class EditorPanel(QWidget):
    panel_toggle_requested = None  # 预留：切换其它侧栏

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 工具栏
        toolbar = QToolBar("格式化")
        toolbar.setMovable(False)
        layout.addWidget(toolbar)

        # 保存
        self.save_requested = QAction(get_icon("save", "#d4d4d4"), "保存 (Ctrl+S)", self)
        self.save_requested.setShortcut(QKeySequence.StandardKey.Save)
        toolbar.addAction(self.save_requested)

        # 撤销 / 重做
        self.undo_action = QAction(get_icon("undo", "#d4d4d4"), "撤销", self)
        toolbar.addAction(self.undo_action)
        self.redo_action = QAction(get_icon("redo", "#d4d4d4"), "重做", self)
        toolbar.addAction(self.redo_action)
        toolbar.addSeparator()

        # 字体族 & 字号
        self.font_combo = QFontComboBox()
        toolbar.addWidget(self.font_combo)
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 72)
        self.font_size_spin.setSingleStep(1)
        self.font_size_spin.setButtonSymbols(QSpinBox.ButtonSymbols.UpDownArrows)
        self.font_size_spin.setAccelerated(True)
        self.font_size_spin.setStyleSheet("QSpinBox { width:60px; }")
        toolbar.addWidget(self.font_size_spin)
        toolbar.addSeparator()

        # 样式：避免下方正文透出造成干扰
        toolbar.setStyleSheet(toolbar.styleSheet() + """
QToolBar {background:rgba(25,25,25,150);}
QToolBar QFontComboBox, QToolBar QSpinBox {background:rgba(32,32,32,210); border:1px solid #444; border-radius:3px; padding:1px 4px; color:#ddd;}
QToolBar QFontComboBox QAbstractItemView {background:#202020; color:#ddd; selection-background-color:#444;}
""")

        # 文本样式
        self.bold_action = QAction(get_icon("bold", "#d4d4d4"), "粗体", self); self.bold_action.setCheckable(True); toolbar.addAction(self.bold_action)
        self.italic_action = QAction(get_icon("italic", "#d4d4d4"), "斜体", self); self.italic_action.setCheckable(True); toolbar.addAction(self.italic_action)
        self.underline_action = QAction(get_icon("underline", "#d4d4d4"), "下划线", self); self.underline_action.setCheckable(True); toolbar.addAction(self.underline_action)

        # 标签编辑区
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        layout.addWidget(self.tab_widget)
