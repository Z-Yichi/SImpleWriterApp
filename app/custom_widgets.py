"""Custom widgets module."""
from PyQt6.QtWidgets import QTextEdit, QApplication
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QWheelEvent, QKeyEvent


class AdvancedTextEdit(QTextEdit):
    """增强版 QTextEdit: Ctrl+滚轮/加减缩放、Ctrl+-/+=、可配置回车缩进"""
    fontZoomRequested = pyqtSignal(int)  # 发射 +1 / -1

    def __init__(self, parent=None):
        super().__init__(parent)
        self.enter_mode: str = 'fullwidth'

    def set_enter_mode(self, mode: str):
        if mode in ('fullwidth', 'halfwidth', 'none'):
            self.enter_mode = mode

    def wheelEvent(self, event: QWheelEvent):
        if QApplication.keyboardModifiers() == Qt.KeyboardModifier.ControlModifier:
            delta = 1 if event.angleDelta().y() > 0 else -1
            self.fontZoomRequested.emit(delta)
            event.accept()
            return
        super().wheelEvent(event)

    def keyPressEvent(self, event: QKeyEvent):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if event.key() in (Qt.Key.Key_Plus, Qt.Key.Key_Equal):
                self.fontZoomRequested.emit(1); event.accept(); return
            if event.key() == Qt.Key.Key_Minus:
                self.fontZoomRequested.emit(-1); event.accept(); return
        super().keyPressEvent(event)
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self.enter_mode == 'fullwidth':
                self.insertPlainText('　　')
            elif self.enter_mode == 'halfwidth':
                self.insertPlainText('  ')
