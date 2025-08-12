# app/custom_widgets.py
from PyQt6.QtWidgets import QTextEdit, QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QWheelEvent, QKeyEvent

class AdvancedTextEdit(QTextEdit):
    """
    一个增强版的文本编辑器，支持Ctrl+滚轮缩放和自动缩进。
    """
    def __init__(self, parent=None):
        super().__init__(parent)

    def wheelEvent(self, event: QWheelEvent):
        """
        重写鼠标滚轮事件，实现缩放功能。
        """
        # 使用 QApplication.keyboardModifiers() 进行更可靠的检查
        if QApplication.keyboardModifiers() == Qt.KeyboardModifier.ControlModifier:
            angle = event.angleDelta().y()
            if angle > 0:
                self.zoomIn(1)
            else:
                self.zoomOut(1)
            
            event.accept()
        else:
            # 如果没有按Ctrl，则执行默认的滚动行为
            super().wheelEvent(event)

    def keyPressEvent(self, event: QKeyEvent):
        """
        重写按键事件，实现换行时自动缩进。
        """
        super().keyPressEvent(event)
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.insertPlainText('　　')
