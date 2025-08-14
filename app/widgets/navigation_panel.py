from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTreeView, QLineEdit, QListWidget, QLabel, QStackedWidget,
    QHBoxLayout, QPushButton, QFileDialog, QSlider, QSpinBox, QFontComboBox, QDoubleSpinBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QFont
from ..project_manager import load_project_structure


class NavigationPanel(QWidget):
    tree_item_clicked = pyqtSignal(object)
    search_requested = pyqtSignal(str)
    find_submitted = pyqtSignal(str)
    find_prev_requested = pyqtSignal()
    find_next_requested = pyqtSignal()
    setting_selected = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.stack = QStackedWidget()
        layout.addWidget(self.stack)

        # 树视图页
        self.tree_view = QTreeView(); self.tree_view.setHeaderHidden(True)
        self.tree_view.clicked.connect(lambda idx: self.tree_item_clicked.emit(idx))
        self.tree_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.stack.addWidget(self.tree_view)

        # 搜索页
        self._build_search_page()
        # 设置页
        self._build_settings_page()

        self.project_path = None
        self.project_data = None
        self.tree_model = QStandardItemModel(); self.tree_view.setModel(self.tree_model)
        self._load_current_settings()

    def _build_search_page(self):
        page = QWidget(); lay = QVBoxLayout(page)
        lay.addWidget(QLabel('项目搜索 (标题匹配)'))
        self.search_input = QLineEdit(); self.search_input.setPlaceholderText('输入关键词 回车')
        self.search_results = QListWidget()
        self.search_input.returnPressed.connect(lambda: self.search_requested.emit(self.search_input.text().strip()))
        lay.addWidget(self.search_input); lay.addWidget(self.search_results); lay.addWidget(QLabel('——'))
        lay.addWidget(QLabel('当前章节查找 (Ctrl+F)'))
        row = QHBoxLayout()
        self.find_input = QLineEdit(); self.find_input.setPlaceholderText('输入要查找的内容')
        self.find_prev_btn = QPushButton('上一个'); self.find_next_btn = QPushButton('下一个'); self.find_count_label = QLabel('0/0')
        row.addWidget(self.find_input, 1); row.addWidget(self.find_prev_btn); row.addWidget(self.find_next_btn); row.addWidget(self.find_count_label)
        lay.addLayout(row)
        self.find_input.returnPressed.connect(lambda: self.find_submitted.emit(self.find_input.text().strip()))
        self.find_prev_btn.clicked.connect(self.find_prev_requested.emit)
        self.find_next_btn.clicked.connect(self.find_next_requested.emit)
        self.stack.addWidget(page)

    def _build_settings_page(self):
        page = QWidget(); lay = QVBoxLayout(page); lay.setContentsMargins(4,4,4,4)
        #lay.addWidget(QLabel('快速设置'))
        fr = QHBoxLayout(); fr.addWidget(QLabel('字体:')); self.inline_font_combo = QFontComboBox(); fr.addWidget(self.inline_font_combo); lay.addLayout(fr)
        uifr = QHBoxLayout(); uifr.addWidget(QLabel('界面字体:')); self.inline_ui_font_combo = QFontComboBox(); uifr.addWidget(self.inline_ui_font_combo); lay.addLayout(uifr)
        sr = QHBoxLayout(); sr.addWidget(QLabel('字号:')); self.inline_font_size = QSpinBox(); self.inline_font_size.setRange(8,72); sr.addWidget(self.inline_font_size); lay.addLayout(sr)
        uisr = QHBoxLayout(); uisr.addWidget(QLabel('界面字号:')); self.inline_ui_font_size = QSpinBox(); self.inline_ui_font_size.setRange(8,48); uisr.addWidget(self.inline_ui_font_size); lay.addLayout(uisr)
        lr = QHBoxLayout(); lr.addWidget(QLabel('行距倍数:')); self.inline_line_spacing = QDoubleSpinBox(); self.inline_line_spacing.setRange(1.0,3.0); self.inline_line_spacing.setSingleStep(0.1); self.inline_line_spacing.setDecimals(1); lr.addWidget(self.inline_line_spacing); lay.addLayout(lr)
        br = QHBoxLayout(); br.addWidget(QLabel('背景图:')); self.inline_bg_path = QLineEdit(); browse_btn = QPushButton('…'); br.addWidget(self.inline_bg_path,1); br.addWidget(browse_btn); lay.addLayout(br)
        orow = QHBoxLayout(); orow.addWidget(QLabel('不透明度:')); self.inline_bg_opacity = QSlider(); self.inline_bg_opacity.setOrientation(Qt.Orientation.Horizontal); self.inline_bg_opacity.setRange(0,100); orow.addWidget(self.inline_bg_opacity,1); lay.addLayout(orow)
        apply_btn = QPushButton('保存并应用'); lay.addWidget(apply_btn)
        browse_btn.clicked.connect(self._pick_bg_image); apply_btn.clicked.connect(self._apply_inline_settings)
        self.stack.addWidget(page)

    def _load_current_settings(self):
        from ..settings_manager import load_settings
        s = load_settings()['settings']
        self.inline_font_combo.setCurrentFont(QFont(s.get('editor_font_family','Microsoft YaHei')))
        self.inline_font_size.setValue(s.get('editor_font_size',16))
        self.inline_ui_font_combo.setCurrentFont(QFont(s.get('ui_font_family', s.get('editor_font_family','Microsoft YaHei'))))
        self.inline_ui_font_size.setValue(s.get('ui_font_size',14))
        self.inline_line_spacing.setValue(s.get('line_spacing_percent',150)/100.0)
        self.inline_bg_path.setText(s.get('background_image_path',''))
        self.inline_bg_opacity.setValue(s.get('background_opacity',80))

    def _pick_bg_image(self):
        path, _ = QFileDialog.getOpenFileName(self, '选择背景图片', '', 'Images (*.png *.jpg *.jpeg *.bmp)')
        if path:
            self.inline_bg_path.setText(path)

    def _apply_inline_settings(self):
        from ..settings_manager import load_settings, save_settings
        data = load_settings(); s = data['settings']
        s['editor_font_family'] = self.inline_font_combo.currentFont().family()
        s['editor_font_size'] = self.inline_font_size.value()
        s['ui_font_family'] = self.inline_ui_font_combo.currentFont().family()
        s['ui_font_size'] = self.inline_ui_font_size.value()
        s['line_spacing_percent'] = int(self.inline_line_spacing.value()*100)
        s['background_image_path'] = self.inline_bg_path.text()
        s['background_opacity'] = self.inline_bg_opacity.value()
        if save_settings(data): self.setting_selected.emit()

    def load_project(self, project_path):
        self.project_path = project_path; self.project_data = load_project_structure(project_path)
        if not self.project_data: return
        self.tree_model.clear(); root = self.tree_model.invisibleRootItem()
        for vol in self.project_data.get('structure', []):
            vi = QStandardItem(vol.get('title','卷')); vi.setEditable(False); vi.setData('volume', Qt.ItemDataRole.UserRole); vi.setData(vol.get('id'), Qt.ItemDataRole.UserRole + 1); root.appendRow(vi)
            for ch in vol.get('children', []):
                ci = QStandardItem(ch.get('title','章节')); ci.setEditable(False); ci.setData('chapter', Qt.ItemDataRole.UserRole); ci.setData(ch.get('id'), Qt.ItemDataRole.UserRole + 1); ci.setData(ch.get('filename'), Qt.ItemDataRole.UserRole + 2); vi.appendRow(ci)
        self.tree_view.expandAll()
