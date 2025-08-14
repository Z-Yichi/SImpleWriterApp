"""MainWindow 主窗口：精简修复版本。"""

import logging
import os
from PyQt6.QtCore import Qt, QModelIndex, QTimer, QPoint
from PyQt6.QtGui import (
    QPainter, QPixmap, QColor, QAction, QKeySequence, QFont,
    QTextCharFormat, QTextCursor, QTextBlockFormat
)
from PyQt6.QtWidgets import (
    QMainWindow, QSplitter, QStatusBar, QLabel, QMenu, QMessageBox,
    QInputDialog, QTextEdit, QPushButton
)

from .widgets.activity_bar import ActivityBar
from .widgets.navigation_panel import NavigationPanel
from .widgets.editor_panel import EditorPanel
from .custom_widgets import AdvancedTextEdit
from .settings_manager import load_settings, save_settings
from .settings_dialog import SettingsDialog
from .project_manager import (
    load_chapter_content, save_chapter_content, save_project_structure,
    add_new_chapter, delete_item, add_new_volume, rename_item_in_structure
)

logging.basicConfig(filename='debug.log', level=logging.INFO, format='%(asctime)s %(message)s')


class LockFirstSplitter(QSplitter):
    def moveSplitter(self, pos: int, index: int):
        if index == 1:
            w0 = self.widget(0)
            if w0 and w0.minimumWidth() == w0.maximumWidth():
                return
        super().moveSplitter(pos, index)


class MainWindow(QMainWindow):
    def __init__(self, project_path: str, parent=None):
        super().__init__(parent)
        self.settings = load_settings()['settings']
        self.project_path: str | None = None
        self.project_data = None
        self.open_tabs: dict = {}
        self.bg_pixmap = None
        self.auto_save_timer: QTimer | None = None
        self._side_visible = True
        self._saved_split_sizes = None
        self.current_find_pattern = ''
        self.current_find_index = 0
        self._current_find_matches = []
        self._current_find_pattern_cache = ''
        self.setup_ui()
        self.apply_runtime_settings()
        self.load_project(project_path)

    # UI 构建
    def setup_ui(self):
        self.setWindowTitle("我的码字软件")
        self.resize(1400, 900)
        splitter = LockFirstSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(6)
        self.setCentralWidget(splitter)
        self.activity_bar = ActivityBar(self); self.activity_bar.setFixedWidth(50); splitter.addWidget(self.activity_bar)
        self.nav_panel = NavigationPanel(self); splitter.addWidget(self.nav_panel)
        self.editor_panel = EditorPanel(self); splitter.addWidget(self.editor_panel)
        self.font_combo = self.editor_panel.font_combo
        self.font_size_spin = self.editor_panel.font_size_spin
        self.bold_action = self.editor_panel.bold_action
        self.italic_action = self.editor_panel.italic_action
        self.underline_action = self.editor_panel.underline_action
        self.tab_widget = self.editor_panel.tab_widget
        self.tree_view = self.nav_panel.tree_view
        self.tree_model = self.nav_panel.tree_model
        # 信号
        self.activity_bar.selected.connect(lambda idx: self.nav_panel.stack.setCurrentIndex(idx))
        self.activity_bar.settings_clicked.connect(lambda: self.nav_panel.stack.setCurrentIndex(2))
        self.editor_panel.save_requested.triggered.connect(self.save_current_tab)
        self.editor_panel.undo_action.triggered.connect(self.undo_current_tab)
        self.editor_panel.redo_action.triggered.connect(self.redo_current_tab)
        self.font_combo.currentFontChanged.connect(self.apply_font_family)
        self.font_size_spin.valueChanged.connect(self.apply_font_size)
        self.bold_action.triggered.connect(self.toggle_bold)
        self.italic_action.triggered.connect(self.toggle_italic)
        self.underline_action.triggered.connect(self.toggle_underline)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(lambda _: self.update_ui_on_tab_change())
        # 快捷键
        if not self.bold_action.shortcut(): self.bold_action.setShortcut(QKeySequence.StandardKey.Bold)
        if not self.italic_action.shortcut(): self.italic_action.setShortcut(QKeySequence.StandardKey.Italic)
        if not self.underline_action.shortcut(): self.underline_action.setShortcut(QKeySequence.StandardKey.Underline)
        splitter.setSizes([50, 260, 1000])
        self.nav_panel.setMinimumWidth(120); self.editor_panel.setMinimumWidth(300)
        self.status_bar = QStatusBar(self); self.setStatusBar(self.status_bar)
        self.word_count_label = QLabel("请打开一个章节进行编辑"); self.status_bar.addPermanentWidget(self.word_count_label)
        self.side_toggle_btn = QPushButton('隐藏侧栏'); self.side_toggle_btn.setFlat(True); self.side_toggle_btn.clicked.connect(self.toggle_side_panels); self.status_bar.addPermanentWidget(self.side_toggle_btn)
        self.find_action = QAction(self); self.find_action.setShortcut(QKeySequence.StandardKey.Find); self.find_action.triggered.connect(self.trigger_focus_inline_find); self.addAction(self.find_action)
        # 导航面板信号
        self.nav_panel.tree_item_clicked.connect(self.open_chapter_in_tab)
        self.nav_panel.search_requested.connect(self.do_search)
        if hasattr(self.nav_panel, 'find_submitted'):
            self.nav_panel.find_submitted.connect(self.find_in_current_chapter_submit)
            self.nav_panel.find_prev_requested.connect(self.find_in_current_prev)
            self.nav_panel.find_next_requested.connect(self.find_in_current_next)
        self.nav_panel.tree_view.customContextMenuRequested.connect(self.show_tree_context_menu)
        self.nav_panel.setting_selected.connect(self.open_settings_dialog_from_panel)
        if hasattr(self.nav_panel, 'settings_live_changed'):
            self.nav_panel.settings_live_changed.connect(self.reload_settings_and_apply)

    def toggle_side_panels(self):
        splitter = self.centralWidget()
        if not isinstance(splitter, QSplitter): return
        if self._side_visible:
            self._saved_split_sizes = splitter.sizes(); self.activity_bar.hide(); self.nav_panel.hide()
            total = sum(self._saved_split_sizes) if self._saved_split_sizes else self.width(); splitter.setSizes([0,0,total])
            self._side_visible = False; self.side_toggle_btn.setText('显示侧栏')
        else:
            self.activity_bar.show(); self.nav_panel.show()
            if self._saved_split_sizes and len(self._saved_split_sizes)==3: splitter.setSizes(self._saved_split_sizes)
            else: splitter.setSizes([50,260,max(600,self.width()-310)])
            self._side_visible = True; self.side_toggle_btn.setText('隐藏侧栏')

    # 设置与外观
    def apply_runtime_settings(self):
        if not self.auto_save_timer:
            self.auto_save_timer = QTimer(self); self.auto_save_timer.setSingleShot(True); self.auto_save_timer.timeout.connect(self.save_current_tab)
        self.auto_save_timer.setInterval(self.settings.get('auto_save_interval',3000))
        self.apply_background()
        try:
            from PyQt6.QtWidgets import QApplication
            ui_font = QFont(self.settings.get('ui_font_family', self.settings.get('editor_font_family','Microsoft YaHei')),
                            self.settings.get('ui_font_size',14))
            QApplication.instance().setFont(ui_font)
        except Exception: pass
        icon_dir = self.settings.get('icon_dir','')
        if icon_dir and os.path.isdir(icon_dir):
            try:
                from .icons import set_icon_override_dir; set_icon_override_dir(icon_dir)
            except Exception: pass
        for info in self.open_tabs.values():
            editor = info['editor']
            editor.setFont(QFont(self.settings.get('editor_font_family'), self.settings.get('editor_font_size')))
            if hasattr(editor,'set_enter_mode'): editor.set_enter_mode(self.settings.get('enter_mode','fullwidth'))
            try:
                percent = self.settings.get('line_spacing_percent',150)
                cursor = QTextCursor(editor.document()); cursor.beginEditBlock(); cursor.select(QTextCursor.SelectionType.Document)
                fmt = QTextBlockFormat(); fmt.setLineHeight(percent, QTextBlockFormat.LineHeightTypes.ProportionalHeight); cursor.setBlockFormat(fmt); cursor.endEditBlock()
            except Exception: pass
        self.font_combo.setCurrentFont(QFont(self.settings.get('editor_font_family'))); self.font_size_spin.setValue(self.settings.get('editor_font_size'))

    def reload_settings_and_apply(self):
        self.settings = load_settings()['settings']; self.apply_runtime_settings()

    def open_settings_dialog_from_panel(self):
        current_all = load_settings(); dialog = SettingsDialog(current_all, self)
        if dialog.exec():
            current_all['settings'] = dialog.get_settings()
            if save_settings(current_all): self.reload_settings_and_apply()

    def apply_background(self):
        path = self.settings.get('background_image_path',''); self.bg_pixmap = QPixmap(path) if path and os.path.exists(path) else None
        cw = self.centralWidget();
        if not cw: return
        for w in [cw, self.nav_panel, self.editor_panel, self.tab_widget]:
            if w: w.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True); w.setStyleSheet(w.styleSheet()+"\nbackground: transparent;")
        for info in self.open_tabs.values():
            ed = info['editor']; ed.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True); ed.setStyleSheet(ed.styleSheet()+"\nbackground: transparent;")

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.bg_pixmap:
            p = QPainter(self); p.setOpacity(0.25); p.drawPixmap(self.rect(), self.bg_pixmap); p.setOpacity(1.0)
            p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver); p.fillRect(self.rect(), QColor(0,0,0,40))

    # 项目 / 章节
    def load_project(self, project_path: str):
        self.project_path = project_path; self.nav_panel.load_project(project_path); self.project_data = self.nav_panel.project_data

    def refresh_tree_view(self):
        if self.project_path: self.nav_panel.load_project(self.project_path); self.project_data = self.nav_panel.project_data

    def open_chapter_in_tab(self, index: QModelIndex):
        item = self.tree_model.itemFromIndex(index)
        if item.data(Qt.ItemDataRole.UserRole) != 'chapter': return
        chap_id = item.data(Qt.ItemDataRole.UserRole+1)
        if chap_id in self.open_tabs:
            self.tab_widget.setCurrentWidget(self.open_tabs[chap_id]['editor']); return
        filename = item.data(Qt.ItemDataRole.UserRole+2)
        if not filename: return
        html = load_chapter_content(self.project_path, filename)
        editor = AdvancedTextEdit(); editor.setFont(QFont(self.font_combo.currentFont().family(), self.font_size_spin.value())); editor.setHtml(html)
        base_size = self.settings.get('editor_font_size', self.font_size_spin.value())
        try:
            cursor = QTextCursor(editor.document()); cursor.beginEditBlock(); cursor.select(QTextCursor.SelectionType.Document)
            fmt_all = QTextCharFormat(); fmt_all.setFontPointSize(base_size); cursor.mergeCharFormat(fmt_all); cursor.endEditBlock()
            base_font = editor.document().defaultFont(); base_font.setPointSize(base_size); editor.document().setDefaultFont(base_font)
        except Exception: pass
        editor.set_enter_mode(self.settings.get('enter_mode','fullwidth'))
        editor.fontZoomRequested.connect(self.handle_editor_zoom)
        if self.bg_pixmap: editor.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True); editor.setStyleSheet(editor.styleSheet()+"\nbackground: transparent;")
        editor.textChanged.connect(lambda e=editor: self.mark_tab_as_dirty(e))
        editor.cursorPositionChanged.connect(self.update_format_toolbar_state)
        tab_index = self.tab_widget.addTab(editor, item.text()); self.tab_widget.setCurrentIndex(tab_index)
        self.open_tabs[chap_id] = {'editor': editor,'original_title': item.text(),'filename': filename,'current_font_size': base_size}
        self.update_ui_on_tab_change()

    # 编辑状态
    def mark_tab_as_dirty(self, editor):
        self.update_status_bar(); idx = self.tab_widget.indexOf(editor)
        if idx == -1: return
        for cid, info in self.open_tabs.items():
            if info['editor'] == editor: original = info['original_title']; break
        else: return
        if not self.tab_widget.tabText(idx).endswith(' ●'): self.tab_widget.setTabText(idx, f"{original} ●")
        if self.auto_save_timer and self.auto_save_timer.isActive(): self.auto_save_timer.stop()
        if self.auto_save_timer: self.auto_save_timer.start()

    def update_ui_on_tab_change(self):
        self.update_status_bar(); self.update_format_toolbar_state()

    def update_format_toolbar_state(self):
        editor = self.tab_widget.currentWidget()
        if not isinstance(editor, AdvancedTextEdit): return
        fmt = editor.currentCharFormat(); self.bold_action.setChecked(fmt.fontWeight()==QFont.Weight.Bold)
        self.italic_action.setChecked(fmt.fontItalic()); self.underline_action.setChecked(fmt.fontUnderline())
        self.font_combo.blockSignals(True); self.font_size_spin.blockSignals(True)
        self.font_combo.setCurrentFont(fmt.font())
        if fmt.font().pointSize()>0: self.font_size_spin.setValue(fmt.font().pointSize())
        self.font_combo.blockSignals(False); self.font_size_spin.blockSignals(False)

    # 字体 / 格式
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
        if font_family or font_size:
            base_font = editor.document().defaultFont()
            if font_family: base_font.setFamily(font_family)
            if font_size: base_font.setPointSize(font_size)
            editor.document().setDefaultFont(base_font)

    # 缩放
    def handle_editor_zoom(self, delta: int):
        editor = self.tab_widget.currentWidget();
        if not isinstance(editor, AdvancedTextEdit): return
        chapter_id = None
        for cid, info in self.open_tabs.items():
            if info['editor']==editor:
                chapter_id = cid; current_size = info.get('current_font_size', editor.fontPointSize() or editor.font().pointSize() or self.settings.get('editor_font_size',14)); break
        if chapter_id is None: return
        step = 1 if delta>0 else -1; new_size = max(8, min(72, current_size+step))
        if new_size == current_size: return
        sel = QTextCursor(editor.document()); sel.select(QTextCursor.SelectionType.Document); fmt = QTextCharFormat(); fmt.setFontPointSize(new_size); sel.mergeCharFormat(fmt)
        base_font = editor.document().defaultFont(); base_font.setPointSize(new_size); editor.document().setDefaultFont(base_font)
        self.open_tabs[chapter_id]['current_font_size'] = new_size
        self.font_size_spin.blockSignals(True); self.font_size_spin.setValue(new_size); self.font_size_spin.blockSignals(False)
        self.status_bar.showMessage(f"字号: {new_size}pt",1500)

    # 保存 / 标签
    def save_current_tab(self):
        editor = self.tab_widget.currentWidget();
        if not isinstance(editor, AdvancedTextEdit): return
        for cid, info in self.open_tabs.items():
            if info['editor']==editor:
                content = editor.toHtml(); success, msg = save_chapter_content(self.project_path, info['filename'], content)
                if success:
                    self.status_bar.showMessage(msg or '已保存',2500); idx = self.tab_widget.indexOf(editor)
                    if idx!=-1: self.tab_widget.setTabText(idx, info['original_title'])
                else: QMessageBox.warning(self,'保存失败',msg)
                break

    def close_tab(self, index: int, force: bool=False):
        editor = self.tab_widget.widget(index)
        if not editor: return
        target_cid=None
        for cid, info in self.open_tabs.items():
            if info['editor']==editor:
                target_cid=cid
                if (self.tab_widget.tabText(index).endswith(' ●')) and not force:
                    reply = QMessageBox.question(self,'未保存','此章节有未保存修改，仍要关闭吗？', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
                    if reply!=QMessageBox.StandardButton.Yes: return
                break
        self.tab_widget.removeTab(index)
        if target_cid: self.open_tabs.pop(target_cid,None)
        self.update_status_bar()

    # 树结构操作
    def show_tree_context_menu(self, position: QPoint):
        index = self.tree_view.indexAt(position); menu = QMenu(self)
        if index.isValid():
            item = self.tree_model.itemFromIndex(index)
            if item.data(Qt.ItemDataRole.UserRole)=='volume': menu.addAction('新建章节', lambda: self.handle_new_chapter(item))
            menu.addAction('重命名', lambda: self.handle_rename_item(item)); menu.addAction('删除', lambda: self.handle_delete_item(item))
        else: menu.addAction('新建卷', self.handle_new_volume)
        menu.exec(self.tree_view.viewport().mapToGlobal(position))

    def handle_new_volume(self):
        topic, ok = QInputDialog.getText(self,'新建卷','请输入卷的主题：')
        if ok and topic:
            if add_new_volume(self.project_data, topic): self.save_and_refresh('新卷已创建')
            else: QMessageBox.warning(self,'错误','创建失败')

    def handle_new_chapter(self, volume_item):
        volume_id = volume_item.data(Qt.ItemDataRole.UserRole+1)
        topic, ok = QInputDialog.getText(self,'新建章节','请输入章节主题：')
        if ok and topic:
            if add_new_chapter(self.project_path, self.project_data, volume_id, topic): self.save_and_refresh('新章节已创建')
            else: QMessageBox.warning(self,'错误','创建新章节失败')

    def handle_rename_item(self, item):
        item_id = item.data(Qt.ItemDataRole.UserRole+1); old = item.text(); new, ok = QInputDialog.getText(self,'重命名','新的名称：', text=old)
        if ok and new and new!=old:
            if rename_item_in_structure(self.project_data, item_id, new): self.save_and_refresh('已重命名')
            else: QMessageBox.warning(self,'错误','重命名失败')

    def handle_delete_item(self, item):
        item_id = item.data(Qt.ItemDataRole.UserRole+1); title = item.text(); is_volume = item.data(Qt.ItemDataRole.UserRole)=='volume'
        if not is_volume:
            all_chapters=[]
            for vol in self.project_data.get('structure', []):
                for ch in vol.get('children', []): all_chapters.append(ch)
            if not all_chapters: return
            if item_id != all_chapters[-1]['id']:
                QMessageBox.information(self,'限制','只能删除最后一章（最新一章）。'); return
        reply = QMessageBox.question(self,'确认删除', f"确定删除 '{title}'?\n此操作不可恢复", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes: return
        if is_volume:
            target_volume=None
            for vol in self.project_data.get('structure', []):
                if vol['id']==item_id: target_volume=vol; break
            if not target_volume: return
            first_volume=None
            for vol in self.project_data.get('structure', []):
                if vol['id']!=target_volume['id']: first_volume=vol; break
            if first_volume: first_volume['children'].extend(target_volume.get('children', []))
            for i, vol in enumerate(self.project_data.get('structure', [])):
                if vol['id']==target_volume['id']: del self.project_data['structure'][i]; break
            if save_project_structure(self.project_path, self.project_data): self.refresh_tree_view(); self.status_bar.showMessage('卷已合并删除',2500)
            else: QMessageBox.warning(self,'错误','保存结构失败'); return
        else:
            if delete_item(self.project_path, self.project_data, item_id):
                if item_id in self.open_tabs:
                    ed = self.open_tabs[item_id]['editor']; idx = self.tab_widget.indexOf(ed)
                    if idx!=-1: self.close_tab(idx, force=True)
                # 立即持久化结构到 project.json，确保删除链可继续（6->5->4...）
                if save_project_structure(self.project_path, self.project_data):
                    self.refresh_tree_view(); self.status_bar.showMessage('章节已删除',2500)
                else:
                    QMessageBox.warning(self,'错误','保存结构失败（章节已从内存删除）')
            else: QMessageBox.warning(self,'错误','删除失败'); return

    def save_and_refresh(self, msg):
        if save_project_structure(self.project_path, self.project_data): self.status_bar.showMessage(msg,2000); self.refresh_tree_view()
        else: QMessageBox.critical(self,'严重错误','无法保存 project.json')

    # 标题搜索
    def do_search(self, keyword: str):
        keyword=(keyword or '').strip(); self.nav_panel.search_results.clear()
        if not keyword or not self.project_data: return
        for vol in self.project_data.get('structure', []):
            for ch in vol.get('children', []):
                title = ch.get('title','')
                if keyword.lower() in title.lower(): self.nav_panel.search_results.addItem(title)
        self.nav_panel.stack.setCurrentIndex(1)

    # 章节内查找
    def trigger_focus_inline_find(self):
        self.nav_panel.stack.setCurrentIndex(1)
        if hasattr(self.nav_panel,'find_input'):
            self.nav_panel.find_input.setFocus(); self.nav_panel.find_input.selectAll()

    def _get_current_editor_and_text(self):
        ed = self.tab_widget.currentWidget();
        if not isinstance(ed, AdvancedTextEdit): return None, ''
        return ed, ed.toPlainText()

    def _collect_find_matches(self, pattern: str):
        ed, text = self._get_current_editor_and_text();
        if not ed or not pattern: return []
        matches=[]; start=0; plen=len(pattern)
        while True:
            idx = text.find(pattern, start)
            if idx==-1: break
            matches.append((idx, plen)); start = idx + plen
        return matches

    def _update_find_highlight(self, pattern: str, current_index: int, rebuild: bool=True):
        ed, text = self._get_current_editor_and_text();
        if not ed: return
        if not pattern:
            ed.setExtraSelections([])
            if hasattr(self.nav_panel,'find_count_label'): self.nav_panel.find_count_label.setText('0/0')
            return
        if rebuild or not hasattr(self,'_current_find_matches') or pattern != getattr(self,'_current_find_pattern_cache',''):
            self._current_find_matches = self._collect_find_matches(pattern); self._current_find_pattern_cache = pattern
        matches = self._current_find_matches; total = len(matches)
        if total==0:
            ed.setExtraSelections([])
            if hasattr(self.nav_panel,'find_count_label'): self.nav_panel.find_count_label.setText('0/0')
            return
        current_index = max(0, min(current_index, total-1))
        sels=[]; normal_color=QColor(255,230,150); current_color=QColor(255,180,60)
        for i,(pos,length) in enumerate(matches):
            sel = QTextEdit.ExtraSelection(); c = QTextCursor(ed.document()); c.setPosition(pos); c.setPosition(pos+length, QTextCursor.MoveMode.KeepAnchor)
            sel.cursor=c; fmt = QTextCharFormat(); fmt.setBackground(current_color if i==current_index else normal_color); sel.format=fmt; sels.append(sel)
        ed.setExtraSelections(sels)
        pos,length = matches[current_index]; vis = QTextCursor(ed.document()); vis.setPosition(pos); vis.setPosition(pos+length, QTextCursor.MoveMode.KeepAnchor); ed.setTextCursor(vis)
        if hasattr(ed,'ensureCursorVisible'): ed.ensureCursorVisible()
        if hasattr(self.nav_panel,'find_count_label'): self.nav_panel.find_count_label.setText(f"{current_index+1}/{total}")

    def find_in_current_chapter_submit(self, pattern: str):
        self.current_find_pattern = pattern; self.current_find_index = 0; self._update_find_highlight(pattern,0, rebuild=True)

    def find_in_current_next(self):
        pattern = getattr(self,'current_find_pattern','');
        if not pattern: return
        matches = getattr(self,'_current_find_matches', None)
        if matches is None or pattern != getattr(self,'_current_find_pattern_cache',''):
            matches = self._collect_find_matches(pattern); self._current_find_matches = matches; self._current_find_pattern_cache = pattern
        if not matches: return
        self.current_find_index = (getattr(self,'current_find_index',0)+1)%len(matches)
        self._update_find_highlight(pattern, self.current_find_index, rebuild=False)

    def find_in_current_prev(self):
        pattern = getattr(self,'current_find_pattern','');
        if not pattern: return
        matches = getattr(self,'_current_find_matches', None)
        if matches is None or pattern != getattr(self,'_current_find_pattern_cache',''):
            matches = self._collect_find_matches(pattern); self._current_find_matches = matches; self._current_find_pattern_cache = pattern
        if not matches: return
        self.current_find_index = (getattr(self,'current_find_index',0)-1)%len(matches)
        self._update_find_highlight(pattern, self.current_find_index, rebuild=False)

    # 撤销/重做/状态 & 统计
    def undo_current_tab(self):
        ed = self.tab_widget.currentWidget()
        if hasattr(ed, 'undo'):
            ed.undo()

    def redo_current_tab(self):
        ed = self.tab_widget.currentWidget()
        if hasattr(ed, 'redo'):
            ed.redo()

    def update_status_bar(self):
        ed = self.tab_widget.currentWidget();
        if not hasattr(ed,'toPlainText'): self.word_count_label.setText('请打开一个章节进行编辑'); return
        text = ed.toPlainText(); stats = self._calc_text_stats(text); line_part=''
        if self.settings.get('show_line_numbers', False): line_count = text.count('\n') + (1 if text else 0); line_part = f" | 行: {line_count}"
        self.word_count_label.setText(f"字数(不含空格): {stats['chars_no_space']} | 汉字: {stats['chinese']} | 英文: {stats['english']} | 数字: {stats['digits']} | 符号: {stats['symbols']}{line_part}")

    def _calc_text_stats(self, text: str) -> dict:
        t = text.replace('\r',''); no_space = len([c for c in t if not c.isspace()])
        chinese=english=digits=symbols=0
        for c in t:
            if c.isspace(): continue
            code = ord(c)
            if 0x4E00<=code<=0x9FFF: chinese+=1
            elif c.isalpha() and c.isascii(): english+=1
            elif c.isdigit(): digits+=1
            else: symbols+=1
        return {'chars_with_space': len(t), 'chars_no_space': no_space, 'chinese': chinese, 'english': english, 'digits': digits, 'symbols': symbols}

    # ---------- 编辑/状态 ----------
    def mark_tab_as_dirty(self, editor):
        self.update_status_bar()
        idx = self.tab_widget.indexOf(editor)
        if idx == -1:
            return
        # 找到原始标题
        for cid, info in self.open_tabs.items():
            if info['editor'] == editor:
                original = info['original_title']
                break
        else:
            return
        if not self.tab_widget.tabText(idx).endswith(' ●'):
            self.tab_widget.setTabText(idx, f"{original} ●")
        if self.auto_save_timer and self.auto_save_timer.isActive():
            self.auto_save_timer.stop()
        if self.auto_save_timer:
            self.auto_save_timer.start()

    def update_ui_on_tab_change(self):
        self.update_status_bar()
        self.update_format_toolbar_state()

    def update_format_toolbar_state(self):
        editor = self.tab_widget.currentWidget()
        if not isinstance(editor, AdvancedTextEdit):
            return
        fmt = editor.currentCharFormat()
        self.bold_action.setChecked(fmt.fontWeight() == QFont.Weight.Bold)
        self.italic_action.setChecked(fmt.fontItalic())
        self.underline_action.setChecked(fmt.fontUnderline())
        self.font_combo.blockSignals(True)
        self.font_size_spin.blockSignals(True)
        self.font_combo.setCurrentFont(fmt.font())
        if fmt.font().pointSize() > 0:
            self.font_size_spin.setValue(fmt.font().pointSize())
        self.font_combo.blockSignals(False)
        self.font_size_spin.blockSignals(False)

    def apply_font_family(self, font):
        self.apply_text_format(font_family=font.family())

    def apply_font_size(self, size):
        self.apply_text_format(font_size=size)

    def toggle_bold(self):
        self.apply_text_format(bold=self.bold_action.isChecked())

    def toggle_italic(self):
        self.apply_text_format(italic=self.italic_action.isChecked())

    def toggle_underline(self):
        self.apply_text_format(underline=self.underline_action.isChecked())

    def apply_text_format(self, bold=None, italic=None, underline=None, font_family=None, font_size=None):
        editor = self.tab_widget.currentWidget()
        if not isinstance(editor, AdvancedTextEdit):
            return
        fmt = QTextCharFormat()
        if bold is not None:
            fmt.setFontWeight(QFont.Weight.Bold if bold else QFont.Weight.Normal)
        if italic is not None:
            fmt.setFontItalic(italic)
        if underline is not None:
            fmt.setFontUnderline(underline)
        if font_family is not None:
            fmt.setFontFamily(font_family)
        if font_size is not None:
            fmt.setFontPointSize(font_size)
        editor.mergeCurrentCharFormat(fmt)
        # 如果修改了字号/字体，则同步 document 默认字体，保证后续输入一致
        if font_family or font_size:
            base_font = editor.document().defaultFont()
            if font_family:
                base_font.setFamily(font_family)
            if font_size:
                base_font.setPointSize(font_size)
            editor.document().setDefaultFont(base_font)

    # ---------- 缩放逻辑 ----------
    def handle_editor_zoom(self, delta: int):
        editor = self.tab_widget.currentWidget()
        if not isinstance(editor, AdvancedTextEdit):
            return
        # 查找该编辑器对应章节记录，获取并更新当前字号
        chapter_id = None
        for cid, info in self.open_tabs.items():
            if info['editor'] == editor:
                chapter_id = cid
                current_size = info.get('current_font_size', editor.fontPointSize() or editor.font().pointSize() or self.settings.get('editor_font_size', 14))
                break
        if chapter_id is None:
            return
        step = 1 if delta > 0 else -1
        new_size = max(8, min(72, current_size + step))
        if new_size == current_size:
            return
        # 全文应用新字号（不改变其它格式属性）
        cursor = QTextCursor(editor.document())
        cursor.beginEditBlock()
        sel = QTextCursor(editor.document())
        sel.select(QTextCursor.SelectionType.Document)
        fmt = QTextCharFormat()
        fmt.setFontPointSize(new_size)
        sel.mergeCharFormat(fmt)
        cursor.endEditBlock()
        # 更新默认字体
        base_font = editor.document().defaultFont()
        base_font.setPointSize(new_size)
        editor.document().setDefaultFont(base_font)
        # 记录与同步工具栏字号
        self.open_tabs[chapter_id]['current_font_size'] = new_size
        self.font_size_spin.blockSignals(True)
        self.font_size_spin.setValue(new_size)
        self.font_size_spin.blockSignals(False)
        self.status_bar.showMessage(f"字号: {new_size}pt", 1500)

    def save_current_tab(self):
        editor = self.tab_widget.currentWidget()
        if not isinstance(editor, AdvancedTextEdit):
            return
        for cid, info in self.open_tabs.items():
            if info['editor'] == editor:
                content = editor.toHtml()
                success, msg = save_chapter_content(self.project_path, info['filename'], content)
                if success:
                    self.status_bar.showMessage(msg or '已保存', 2500)
                    idx = self.tab_widget.indexOf(editor)
                    if idx != -1:
                        self.tab_widget.setTabText(idx, info['original_title'])
                else:
                    QMessageBox.warning(self, '保存失败', msg)
                break

    def close_tab(self, index: int, force: bool = False):
        editor = self.tab_widget.widget(index)
        if not editor:
            return
        # 查找章节 id
        target_cid = None
        for cid, info in self.open_tabs.items():
            if info['editor'] == editor:
                target_cid = cid
                # 未保存修改确认
                if (self.tab_widget.tabText(index).endswith(' ●')) and not force:
                    reply = QMessageBox.question(self, '未保存', '此章节有未保存修改，仍要关闭吗？', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
                    if reply != QMessageBox.StandardButton.Yes:
                        return
                break
        self.tab_widget.removeTab(index)
        if target_cid:
            self.open_tabs.pop(target_cid, None)
        self.update_status_bar()

    # ---------- 树与结构操作 ----------
    def show_tree_context_menu(self, position: QPoint):
        index = self.tree_view.indexAt(position)
        menu = QMenu(self)
        if index.isValid():
            item = self.tree_model.itemFromIndex(index)
            if item.data(Qt.ItemDataRole.UserRole) == 'volume':
                menu.addAction('新建章节', lambda: self.handle_new_chapter(item))
            menu.addAction('重命名', lambda: self.handle_rename_item(item))
            menu.addAction('删除', lambda: self.handle_delete_item(item))
        else:
            menu.addAction('新建卷', self.handle_new_volume)
        menu.exec(self.tree_view.viewport().mapToGlobal(position))

    def handle_new_volume(self):
        topic, ok = QInputDialog.getText(self, '新建卷', '请输入卷的主题：')
        if ok and topic:
            if add_new_volume(self.project_data, topic):
                self.save_and_refresh('新卷已创建')
            else:
                QMessageBox.warning(self, '错误', '创建失败')

    def handle_new_chapter(self, volume_item):
        volume_id = volume_item.data(Qt.ItemDataRole.UserRole + 1)
        topic, ok = QInputDialog.getText(self, '新建章节', '请输入章节主题：')
        if ok and topic:
            if add_new_chapter(self.project_path, self.project_data, volume_id, topic):
                self.save_and_refresh('新章节已创建')
            else:
                QMessageBox.warning(self, '错误', '创建新章节失败')

    def handle_rename_item(self, item):
        item_id = item.data(Qt.ItemDataRole.UserRole + 1)
        old = item.text()
        new, ok = QInputDialog.getText(self, '重命名', '新的名称：', text=old)
        if ok and new and new != old:
            if rename_item_in_structure(self.project_data, item_id, new):
                self.save_and_refresh('已重命名')
            else:
                QMessageBox.warning(self, '错误', '重命名失败')

    def handle_delete_item(self, item):
        item_id = item.data(Qt.ItemDataRole.UserRole + 1)
        title = item.text()
        # 判断类型
        is_volume = item.data(Qt.ItemDataRole.UserRole) == 'volume'
        if not is_volume:
            # 章节删除限制：只能删除整体结构里最后一章
            # 找出所有章节按出现顺序
            all_chapters = []
            for vol in self.project_data.get('structure', []):
                for ch in vol.get('children', []):
                    all_chapters.append(ch)
            if not all_chapters:
                return
            last_id = all_chapters[-1]['id']
            if item_id != last_id:
                QMessageBox.information(self, '限制', '只能删除最后一章（最新一章）。')
                return
        reply = QMessageBox.question(self, '确认删除', f"确定删除 '{title}'?\n此操作不可恢复", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return
        if is_volume:
            # 删除卷：将其章节合并到第一卷（若存在且不是自己），然后删除空卷
            target_volume = None
            for vol in self.project_data.get('structure', []):
                if vol['id'] == item_id:
                    target_volume = vol; break
            if not target_volume:
                return
            # 找第一卷（按现有顺序第一个不同于 target）
            first_volume = None
            for vol in self.project_data.get('structure', []):
                if vol['id'] != target_volume['id']:
                    first_volume = vol; break
            if first_volume:
                # 合并章节（追加到末尾）
                first_volume['children'].extend(target_volume.get('children', []))
            # 真正删除该卷（不额外删除章节文件）
            for i, vol in enumerate(self.project_data.get('structure', [])):
                if vol['id'] == target_volume['id']:
                    del self.project_data['structure'][i]; break
            if save_project_structure(self.project_path, self.project_data):
                self.refresh_tree_view(); self.status_bar.showMessage('卷已合并删除', 2500)
            else:
                QMessageBox.warning(self, '错误', '保存结构失败')
            return
        # 普通章节删除（此时已确认是最后一章）
        if delete_item(self.project_path, self.project_data, item_id):
            if item_id in self.open_tabs:
                ed = self.open_tabs[item_id]['editor']
                idx = self.tab_widget.indexOf(ed)
                if idx != -1:
                    self.close_tab(idx, force=True)
            if save_project_structure(self.project_path, self.project_data):
                self.refresh_tree_view()
                self.status_bar.showMessage('章节已删除', 2500)
            else:
                QMessageBox.warning(self,'错误','保存结构失败（章节已从内存删除）')
        else:
            QMessageBox.warning(self, '错误', '删除失败')

    def save_and_refresh(self, msg):
        if save_project_structure(self.project_path, self.project_data):
            self.status_bar.showMessage(msg, 2000)
            self.refresh_tree_view()
        else:
            QMessageBox.critical(self, '严重错误', '无法保存 project.json')

    # ---------- 搜索 ----------
    def do_search(self, keyword: str):
        keyword = (keyword or '').strip()
        self.nav_panel.search_results.clear()
        if not keyword or not self.project_data:
            return
        for vol in self.project_data.get('structure', []):
            for ch in vol.get('children', []):
                title = ch.get('title', '')
                if keyword.lower() in title.lower():
                    self.nav_panel.search_results.addItem(title)
        self.nav_panel.stack.setCurrentIndex(1)

    # ---------- 当前章节内查找 ----------
    def trigger_focus_inline_find(self):
        # 切换到搜索页并聚焦 find_input
        self.nav_panel.stack.setCurrentIndex(1)
        if hasattr(self.nav_panel, 'find_input'):
            self.nav_panel.find_input.setFocus()
            self.nav_panel.find_input.selectAll()

    def _get_current_editor_and_text(self):
        ed = self.tab_widget.currentWidget()
        if not isinstance(ed, AdvancedTextEdit):
            return None, ''
        return ed, ed.toPlainText()

    def _collect_find_matches(self, pattern: str):
        ed, text = self._get_current_editor_and_text()
        if not ed or not pattern:
            return []
        matches = []
        start = 0
        plen = len(pattern)
        while True:
            idx = text.find(pattern, start)
            if idx == -1:
                break
            matches.append((idx, plen))
            start = idx + plen
        return matches

    def _update_find_highlight(self, pattern: str, current_index: int, rebuild: bool = True):
        """使用 ExtraSelections 高亮，避免整篇反复重写格式造成卡顿。"""
        ed, text = self._get_current_editor_and_text()
        if not ed:
            return
        if not pattern:
            ed.setExtraSelections([])
            if hasattr(self.nav_panel, 'find_count_label'):
                self.nav_panel.find_count_label.setText('0/0')
            return
        if rebuild or not hasattr(self, '_current_find_matches') or pattern != getattr(self, '_current_find_pattern_cache', ''):
            self._current_find_matches = self._collect_find_matches(pattern)
            self._current_find_pattern_cache = pattern
        matches = self._current_find_matches
        total = len(matches)
        if total == 0:
            ed.setExtraSelections([])
            if hasattr(self.nav_panel, 'find_count_label'):
                self.nav_panel.find_count_label.setText('0/0')
            return
        current_index = max(0, min(current_index, total - 1))
        # 构建 ExtraSelections
        base_sel = []
        normal_color = QColor(255, 230, 150)
        current_color = QColor(255, 180, 60)
        for i, (pos, length) in enumerate(matches):
            sel = QTextEdit.ExtraSelection()
            c = QTextCursor(ed.document())
            c.setPosition(pos)
            c.setPosition(pos + length, QTextCursor.MoveMode.KeepAnchor)
            sel.cursor = c
            fmt = QTextCharFormat()
            fmt.setBackground(current_color if i == current_index else normal_color)
            sel.format = fmt
            base_sel.append(sel)
        ed.setExtraSelections(base_sel)
        # 移动主光标
        pos, length = matches[current_index]
        vis = QTextCursor(ed.document())
        vis.setPosition(pos)
        vis.setPosition(pos + length, QTextCursor.MoveMode.KeepAnchor)
        ed.setTextCursor(vis)
        if hasattr(ed, 'ensureCursorVisible'):
            ed.ensureCursorVisible()
        if hasattr(self.nav_panel, 'find_count_label'):
            self.nav_panel.find_count_label.setText(f"{current_index+1}/{total}")

    def find_in_current_chapter_submit(self, pattern: str):
        self.current_find_pattern = pattern
        self.current_find_index = 0
        self._update_find_highlight(pattern, 0, rebuild=True)

    def find_in_current_next(self):
        pattern = getattr(self, 'current_find_pattern', '')
        if not pattern:
            return
        matches = getattr(self, '_current_find_matches', None)
        if matches is None or pattern != getattr(self, '_current_find_pattern_cache', ''):
            matches = self._collect_find_matches(pattern)
            self._current_find_matches = matches
            self._current_find_pattern_cache = pattern
        if not matches:
            return
        self.current_find_index = (getattr(self, 'current_find_index', 0) + 1) % len(matches)
        self._update_find_highlight(pattern, self.current_find_index, rebuild=False)

    def find_in_current_prev(self):
        pattern = getattr(self, 'current_find_pattern', '')
        if not pattern:
            return
        matches = getattr(self, '_current_find_matches', None)
        if matches is None or pattern != getattr(self, '_current_find_pattern_cache', ''):
            matches = self._collect_find_matches(pattern)
            self._current_find_matches = matches
            self._current_find_pattern_cache = pattern
        if not matches:
            return
        self.current_find_index = (getattr(self, 'current_find_index', 0) - 1) % len(matches)
        self._update_find_highlight(pattern, self.current_find_index, rebuild=False)

    # ---------- 撤销 / 重做 / 状态 ----------
    def undo_current_tab(self):
        ed = self.tab_widget.currentWidget()
        if hasattr(ed, 'undo'):
            ed.undo()

    def redo_current_tab(self):
        ed = self.tab_widget.currentWidget()
        if hasattr(ed, 'redo'):
            ed.redo()

    def update_status_bar(self):
        ed = self.tab_widget.currentWidget()
        if not hasattr(ed, 'toPlainText'):
            self.word_count_label.setText('请打开一个章节进行编辑')
            return
        text = ed.toPlainText()
        stats = self._calc_text_stats(text)
        # 模仿 Word：主要显示不含空格字符数，同时补充分类
        line_part = ''
        if self.settings.get('show_line_numbers', False):
            line_count = text.count('\n') + (1 if text else 0)
            line_part = f" | 行: {line_count}"
        self.word_count_label.setText(
            f"字数(不含空格): {stats['chars_no_space']} | 汉字: {stats['chinese']} | 英文: {stats['english']} | 数字: {stats['digits']} | 符号: {stats['symbols']}{line_part}"
        )

    # ---------- 文本统计 ----------
    def _calc_text_stats(self, text: str) -> dict:
        # 去除 Windows \r
        t = text.replace('\r', '')
        total_with_space = len(t)
        no_space = len([c for c in t if not c.isspace()])
        chinese = 0
        english = 0
        digits = 0
        symbols = 0
        for c in t:
            if c.isspace():
                continue
            code = ord(c)
            if 0x4E00 <= code <= 0x9FFF:
                chinese += 1
            elif c.isalpha() and c.isascii():
                english += 1
            elif c.isdigit():
                digits += 1
            else:
                symbols += 1
        return {
            'chars_with_space': total_with_space,
            'chars_no_space': no_space,
            'chinese': chinese,
            'english': english,
            'digits': digits,
            'symbols': symbols
        }

