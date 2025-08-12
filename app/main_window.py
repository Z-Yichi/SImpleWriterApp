# app/main_window.py
import sys
import logging
logging.basicConfig(filename='debug.log', level=logging.INFO, format='%(asctime)s %(message)s')
from PyQt6.QtGui import QPainter, QPixmap, QColor
import os
import re
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QToolBar, QTabWidget, QTreeView,
                             QStatusBar, QSplitter, QMenu, QMessageBox, 
                             QInputDialog, QFileDialog, QLabel, QFontComboBox, QSpinBox)
from PyQt6.QtCore import Qt, QModelIndex, QTimer, QPoint
from PyQt6.QtGui import QAction, QKeySequence, QFont, QTextCharFormat, QColor, QStandardItemModel, QStandardItem

from .icons import get_icon
from .custom_widgets import AdvancedTextEdit
from .settings_manager import load_settings
from .project_manager import (
    load_project_structure, load_chapter_content, save_chapter_content,
    save_project_structure, add_new_chapter, delete_item,
    add_new_volume, rename_item_in_structure
)

class MainWindow(QMainWindow):
    def __init__(self, project_path, parent=None):
        super().__init__(parent)
        
        # 1. 立即加载设置，确保 self.settings 属性在任何UI创建之前就存在
        self.settings = load_settings()['settings']
        
        # 2. 初始化其他成员变量
        self.project_path = None
        self.project_data = None
        self.open_tabs = {}
        self.bg_pixmap = None

        # 3. 创建UI界面 (现在可以安全地访问 self.settings)
        self.setup_ui()
        
        # 4. 应用运行时设置并启动定时器
        self.apply_runtime_settings()
        
        # 5. 加载项目数据
        self.load_project(project_path)

    def apply_runtime_settings(self):
        """应用所有运行时设置，并启动定时器。"""
        if not hasattr(self, 'auto_save_timer'):
            self.auto_save_timer = QTimer(self)
            self.auto_save_timer.setSingleShot(True)
            self.auto_save_timer.timeout.connect(self.save_current_tab)
        self.auto_save_timer.setInterval(self.settings.get('auto_save_interval', 3000))

        self.apply_background()

        for tab_info in self.open_tabs.values():
            editor = tab_info["editor"]
            font = QFont(self.settings.get('editor_font_family'), self.settings.get('editor_font_size'))
            editor.setFont(font)
        
        self.font_combo.setCurrentFont(QFont(self.settings.get('editor_font_family')))
        self.font_size_spin.setValue(self.settings.get('editor_font_size'))
    
    def reload_settings_and_apply(self):
        """供外部调用，用于实时刷新设置。"""
        self.settings = load_settings()['settings']
        self.apply_runtime_settings()


    def setup_ui(self):
        self.setWindowTitle("我的码字软件")
        self.resize(1400, 900)
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.setCentralWidget(main_splitter)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(10, 10, 5, 10)
        
        self.tree_view = QTreeView()
        self.tree_view.setHeaderHidden(True)
        self.tree_view.doubleClicked.connect(self.open_chapter_in_tab)
        # 恢复右键菜单功能
        self.tree_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self.show_tree_context_menu)
        left_layout.addWidget(self.tree_view)
        
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # 修复了将 toolbar 添加到 QWidget 而不是 Layout 的错误
        self.setup_editor_toolbar(right_layout)

        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(self.update_ui_on_tab_change)
        right_layout.addWidget(self.tab_widget)

        main_splitter.addWidget(left_panel)
        main_splitter.addWidget(right_panel)
        main_splitter.setSizes([280, 1120])

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.word_count_label = QLabel("请打开一个章节进行编辑")
        self.status_bar.addPermanentWidget(self.word_count_label)
        
    def setup_editor_toolbar(self, layout):
        toolbar = QToolBar("格式化")
        toolbar.setMovable(False)
        layout.addWidget(toolbar)
        
        is_dark_theme = "dark" in self.settings.get("theme", "vscode_dark")
        icon_color = "#d4d4d4" if is_dark_theme else "#333333"
        self.save_action = QAction(get_icon("save", icon_color), "保存 (Ctrl+S)", self); self.save_action.setShortcut(QKeySequence.StandardKey.Save); self.save_action.triggered.connect(self.save_current_tab); toolbar.addAction(self.save_action)
        toolbar.addSeparator()
        self.undo_action = QAction(get_icon("undo", icon_color), "撤销", self); self.undo_action.triggered.connect(self.undo_current_tab); toolbar.addAction(self.undo_action)
        self.redo_action = QAction(get_icon("redo", icon_color), "重做", self); self.redo_action.triggered.connect(self.redo_current_tab); toolbar.addAction(self.redo_action)
        toolbar.addSeparator()
        self.font_combo = QFontComboBox(); self.font_combo.currentFontChanged.connect(self.apply_font_family); toolbar.addWidget(self.font_combo)
        self.font_size_spin = QSpinBox(); self.font_size_spin.setRange(8, 72); self.font_size_spin.valueChanged.connect(self.apply_font_size); toolbar.addWidget(self.font_size_spin)
        toolbar.addSeparator()
        self.bold_action = QAction(get_icon("bold", icon_color), "粗体", self); self.bold_action.setCheckable(True); self.bold_action.triggered.connect(self.toggle_bold); toolbar.addAction(self.bold_action)
        self.italic_action = QAction(get_icon("italic", icon_color), "斜体", self); self.italic_action.setCheckable(True); self.italic_action.triggered.connect(self.toggle_italic); toolbar.addAction(self.italic_action)
        self.underline_action = QAction(get_icon("underline", icon_color), "下划线", self); self.underline_action.setCheckable(True); self.underline_action.triggered.connect(self.toggle_underline); toolbar.addAction(self.underline_action)

    def apply_background(self):
        path = self.settings.get("background_image_path", "")
        if path and os.path.exists(path):
            self.bg_pixmap = QPixmap(path.replace("\\", "/"))
        else:
            self.bg_pixmap = None

        # 让 centralWidget 及其所有子控件都透明
        cw = self.centralWidget()
        if cw:
            cw.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
            for child in cw.findChildren(QWidget):
                child.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
                child.setStyleSheet("background: transparent;")
        # 让所有编辑器透明
        for tab_info in self.open_tabs.values():
            editor = tab_info["editor"]
            editor.setStyleSheet("background: transparent;")

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.bg_pixmap:
            painter = QPainter(self)
            painter.setOpacity(0.25)  # 图片本身透明度，0.0~1.0
            painter.drawPixmap(self.rect(), self.bg_pixmap)
            painter.setOpacity(1.0)
            # 添加淡灰色遮罩，提升质感
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            painter.fillRect(self.rect(), QColor(0, 0, 0, 40))  # 40为遮罩透明度，可调

    def mark_tab_as_dirty(self, editor):
        self.update_status_bar()
        tab_index = self.tab_widget.indexOf(editor)
        if tab_index == -1: return
        original_title = ""
        for info in self.open_tabs.values():
            if info["editor"] == editor: original_title = info["original_title"]; break
        current_title = self.tab_widget.tabText(tab_index)
        if not current_title.endswith(" ●"): self.tab_widget.setTabText(tab_index, f"{original_title} ●")
        if self.auto_save_timer.isActive(): self.auto_save_timer.stop()
        self.auto_save_timer.start()

    def show_tree_context_menu(self, position: QPoint):
        index = self.tree_view.indexAt(position); menu = QMenu()
        if index.isValid():
            item = self.tree_model.itemFromIndex(index)
            if item.data(Qt.ItemDataRole.UserRole) == 'volume': menu.addAction("新建章节").triggered.connect(lambda: self.handle_new_chapter(item))
            menu.addAction("重命名").triggered.connect(lambda: self.handle_rename_item(item)); menu.addAction("删除").triggered.connect(lambda: self.handle_delete_item(item))
        else: menu.addAction("新建卷").triggered.connect(self.handle_new_volume)
        menu.exec(self.tree_view.viewport().mapToGlobal(position))

    def handle_new_volume(self):
        volume_topic, ok = QInputDialog.getText(self, "新建卷", "请输入卷的主题（无需输入序号和卷名）：")
        if ok and volume_topic:
            if add_new_volume(self.project_data, volume_topic): self.save_and_refresh("新卷已创建。")
            else: QMessageBox.warning(self, "错误", "创建新卷失败！")

    def handle_new_chapter(self, volume_item):
        volume_id = volume_item.data(Qt.ItemDataRole.UserRole + 1)
        chapter_topic, ok = QInputDialog.getText(self, "新建章节", "请输入章节主题（无需输入序号和章名）：")
        if ok and chapter_topic:
            if add_new_chapter(self.project_path, self.project_data, volume_id, chapter_topic): self.save_and_refresh("新章节已创建。")
            else: QMessageBox.warning(self, "错误", "创建新章节失败！")

    def handle_rename_item(self, item):
        item_id = item.data(Qt.ItemDataRole.UserRole + 1); old_title = item.text()
        new_title, ok = QInputDialog.getText(self, "重命名", "请输入新的名称：", text=old_title)
        if ok and new_title and new_title != old_title:
            if rename_item_in_structure(self.project_data, item_id, new_title): self.save_and_refresh(f"'{old_title}' 已重命名。")
            else: QMessageBox.warning(self, "错误", "重命名失败！")

    def handle_delete_item(self, item):
        item_id = item.data(Qt.ItemDataRole.UserRole + 1); item_title = item.text()
        reply = QMessageBox.question(self, "确认删除", f"你确定要删除 '{item_title}' 吗？\n此操作不可恢复！", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            if delete_item(self.project_path, self.project_data, item_id):
                self.status_bar.showMessage(f"'{item_title}' 已被删除。", 3000)
                if item_id in self.open_tabs:
                    editor_to_close = self.open_tabs[item_id]['editor']
                    tab_index_to_close = self.tab_widget.indexOf(editor_to_close)
                    if tab_index_to_close != -1: self.close_tab(tab_index_to_close, force=True)
                self.refresh_tree_view()
            else: QMessageBox.warning(self, "错误", "删除失败！")

    def save_and_refresh(self, status_message):
        if save_project_structure(self.project_path, self.project_data):
            self.status_bar.showMessage(status_message, 3000); self.refresh_tree_view()
        else: QMessageBox.critical(self, "严重错误", "无法保存项目文件 project.json！")

    def open_chapter_in_tab(self, index: QModelIndex):
        item = self.tree_model.itemFromIndex(index)
        if item.data(Qt.ItemDataRole.UserRole) != 'chapter': return
        chapter_id = item.data(Qt.ItemDataRole.UserRole + 1)
        if chapter_id in self.open_tabs:
            self.tab_widget.setCurrentWidget(self.open_tabs[chapter_id]["editor"]); return
        filename = item.data(Qt.ItemDataRole.UserRole + 2)
        if not filename: return
        content = load_chapter_content(self.project_path, filename)
        editor = AdvancedTextEdit()
        editor.setFont(QFont(self.font_combo.currentFont().family(), self.font_size_spin.value()))
        editor.setHtml(content)
        editor.textChanged.connect(lambda: self.mark_tab_as_dirty(editor))
        editor.cursorPositionChanged.connect(self.update_format_toolbar_state)
        tab_index = self.tab_widget.addTab(editor, item.text()); self.tab_widget.setCurrentIndex(tab_index)
        self.open_tabs[chapter_id] = {"editor": editor, "original_title": item.text(), "filename": filename}
        self.update_ui_on_tab_change()

    def update_ui_on_tab_change(self):
        self.update_status_bar(); self.update_format_toolbar_state()
        
    def update_format_toolbar_state(self):
        editor = self.tab_widget.currentWidget()
        if not isinstance(editor, AdvancedTextEdit): return
        fmt = editor.currentCharFormat()
        self.bold_action.setChecked(fmt.fontWeight() == QFont.Weight.Bold)
        self.italic_action.setChecked(fmt.fontItalic())
        self.underline_action.setChecked(fmt.fontUnderline())
        self.font_combo.blockSignals(True); self.font_size_spin.blockSignals(True)
        self.font_combo.setCurrentFont(fmt.font()); self.font_size_spin.setValue(fmt.font().pointSize())
        self.font_combo.blockSignals(False); self.font_size_spin.blockSignals(False)

    def apply_font_family(self, font): self.apply_text_format(font_family=font.family())
    def apply_font_size(self, size): self.apply_text_format(font_size=size)
    def toggle_bold(self): self.apply_text_format(bold=self.bold_action.isChecked())
    def toggle_italic(self): self.apply_text_format(italic=self.italic_action.isChecked())
    def toggle_underline(self): self.apply_text_format(underline=self.underline_action.isChecked())

    def apply_text_format(self, bold=None, italic=None, underline=None, font_family=None, font_size=None):
        editor = self.tab_widget.currentWidget()
        if not isinstance(editor, AdvancedTextEdit): return
        fmt = QTextCharFormat()
        if bold is not None: fmt.setFontWeight(QFont.Weight.Bold if bold else QFont.Weight.Normal)
        if italic is not None: fmt.setFontItalic(italic)
        if underline is not None: fmt.setFontUnderline(underline)
        if font_family is not None: fmt.setFontFamily(font_family)
        if font_size is not None: fmt.setFontPointSize(font_size)
        editor.mergeCurrentCharFormat(fmt)

    def save_current_tab(self):
        current_editor = self.tab_widget.currentWidget()
        if not isinstance(current_editor, AdvancedTextEdit): return
        chapter_id, info = None, None
        for cid, i in self.open_tabs.items():
            if i["editor"] == current_editor: chapter_id, info = cid, i; break
        if not info: return
        content = current_editor.toHtml()
        success, message = save_chapter_content(self.project_path, info["filename"], content)
        if success:
            tab_index = self.tab_widget.indexOf(current_editor)
            if tab_index != -1: self.tab_widget.setTabText(tab_index, info["original_title"])
            self.status_bar.showMessage(f"章节 '{info['original_title']}' 已保存。", 3000)
        else: QMessageBox.warning(self, "保存失败", f"无法保存章节：\n{message}")

    def undo_current_tab(self):
        current_editor = self.tab_widget.currentWidget()
        if isinstance(current_editor, AdvancedTextEdit): current_editor.undo()
    def redo_current_tab(self):
        current_editor = self.tab_widget.currentWidget()
        if isinstance(current_editor, AdvancedTextEdit): current_editor.redo()
    def close_tab(self, index, force=False):
        editor = self.tab_widget.widget(index); tab_title = self.tab_widget.tabText(index)
        if tab_title.endswith(" ●") and not force:
            reply = QMessageBox.question(self, "保存更改", f"你想保存对 '{tab_title.strip(' ●')}' 的更改吗？", QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel)
            if reply == QMessageBox.StandardButton.Save: self.save_current_tab()
            elif reply == QMessageBox.StandardButton.Cancel: return
        chapter_id_to_close = None
        for cid, info in self.open_tabs.items():
            if info["editor"] == editor: chapter_id_to_close = cid; break
        if chapter_id_to_close: self.open_tabs.pop(chapter_id_to_close)
        self.tab_widget.removeTab(index)
    def update_status_bar(self):
        current_editor = self.tab_widget.currentWidget()
        if not isinstance(current_editor, AdvancedTextEdit): self.word_count_label.setText("无打开的章节"); return
        text = current_editor.toPlainText()
        chinese_chars_count = len(re.findall(r'[\u4e00-\u9fa5]', text)); english_words_count = len(re.findall(r'\b[a-zA-Z]+\b', text)); total_chars_no_space = len(re.sub(r'\s', '', text))
        stats_text = f"汉字: {chinese_chars_count} | 英文单词: {english_words_count} | 总字符: {total_chars_no_space}"; self.word_count_label.setText(stats_text)
    def load_project(self, project_path):
        self.project_path = project_path; self.project_data = load_project_structure(project_path)
        if self.project_data is None: QMessageBox.critical(self, "错误", "加载项目失败！"); self.close(); return
        self.setWindowTitle(f"编辑 - {self.project_data.get('bookTitle', '未知书籍')}"); self.refresh_tree_view()
        self.status_bar.showMessage(f"项目 '{self.project_data.get('bookTitle')}' 已成功加载。", 5000)
    def refresh_tree_view(self):
        if not hasattr(self, 'tree_model'): self.tree_model = QStandardItemModel(); self.tree_view.setModel(self.tree_model)
        self.tree_model.clear(); root_node = self.tree_model.invisibleRootItem()
        if not self.project_data: return
        for volume_data in self.project_data.get('structure', []):
            volume_item = QStandardItem(volume_data.get('title', '未知卷')); volume_item.setEditable(False); volume_item.setData("volume", Qt.ItemDataRole.UserRole); volume_item.setData(volume_data.get('id'), Qt.ItemDataRole.UserRole + 1); root_node.appendRow(volume_item)
            for chapter_data in volume_data.get('children', []):
                chapter_item = QStandardItem(chapter_data.get('title', '未知章节')); chapter_item.setEditable(False); chapter_item.setData("chapter", Qt.ItemDataRole.UserRole); chapter_item.setData(chapter_data.get('id'), Qt.ItemDataRole.UserRole + 1); chapter_item.setData(chapter_data.get('filename'), Qt.ItemDataRole.UserRole + 2); volume_item.appendRow(chapter_item)
        self.tree_view.expandAll()
