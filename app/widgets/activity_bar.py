from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton
from PyQt6.QtCore import pyqtSignal, Qt
from ..icons import get_icon

class ActivityBar(QWidget):
    selected = pyqtSignal(int)
    settings_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        # 常驻图标按钮
        for icon_name, idx in [("explorer", 0), ("search", 1)]:
            btn = QPushButton()
            btn.setIcon(get_icon(icon_name, "#d4d4d4"))
            btn.setFixedSize(40, 40)
            btn.setFlat(True)
            btn.clicked.connect(lambda _, i=idx: self.selected.emit(i))
            layout.addWidget(btn)
        layout.addStretch()
        # 设置按钮
        btn_set = QPushButton()
        btn_set.setIcon(get_icon("settings", "#d4d4d4"))
        btn_set.setFixedSize(40, 40)
        btn_set.setFlat(True)
        btn_set.clicked.connect(self.settings_clicked.emit)
        layout.addWidget(btn_set)

        self.setStyleSheet("background-color: #333;")
