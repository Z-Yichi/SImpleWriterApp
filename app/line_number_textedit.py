from PyQt6.QtWidgets import QPlainTextEdit, QWidget
from PyQt6.QtCore import Qt, QRect, QSize, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QFont

class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.code_editor = editor

    def sizeHint(self):
        return QSize(self.code_editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.code_editor.line_number_area_paint_event(event)

class LineNumberTextEdit(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.line_number_area = LineNumberArea(self)
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        self._show_line_number = True
        self.update_line_number_area_width(0)
        self.highlight_current_line()

    def set_show_line_number(self, show: bool):
        self._show_line_number = show
        self.update_line_number_area_width(0)
        self.viewport().update()

    def show_line_number(self):
        return self._show_line_number

    def line_number_area_width(self):
        if not self._show_line_number:
            return 0
        digits = len(str(max(1, self.blockCount())))
        space = 3 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def line_number_area_paint_event(self, event):
        if not self._show_line_number:
            return
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor(40, 40, 40, 180))
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())
        font = self.font()
        font.setPointSize(max(10, font.pointSize()-1))
        painter.setFont(font)
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor(120, 120, 120))
                painter.drawText(0, top, self.line_number_area.width()-2, self.fontMetrics().height(), Qt.AlignmentFlag.AlignRight, number)
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1

    def highlight_current_line(self):
        extraSelections = []
        if not self.isReadOnly():
            selection = QPlainTextEdit.ExtraSelection()
            lineColor = QColor(60, 60, 60, 80)
            selection.format.setBackground(lineColor)
            selection.format.setProperty(QPlainTextEdit.ExtraSelection.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            extraSelections.append(selection)
        self.setExtraSelections(extraSelections)

    def set_line_spacing(self, spacing: float):
        fmt = self.currentCharFormat()
        fmt.setLineHeight(int(spacing * 100), fmt.LineHeightTypes.ProportionalHeight)
        self.setCurrentCharFormat(fmt)
