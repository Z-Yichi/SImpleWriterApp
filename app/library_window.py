# app/library_window.py
import os
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QPushButton, 
                             QListWidget, QListWidgetItem, QLabel, QMessageBox,
                             QInputDialog, QFileDialog)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt

from .main_window import MainWindow
from .settings_manager import load_settings, save_settings, add_project_to_library, remove_project_from_library
from .project_manager import load_project_structure, save_project_structure
from .settings_dialog import SettingsDialog

class LibraryWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("我的书架")
        self.resize(800, 600)
        self.open_editors = {}
        self.setup_ui()
        self.setup_menu_bar()
        self.populate_project_list()

    def setup_menu_bar(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("文件(&F)")
        exit_action = QAction("退出", self); exit_action.triggered.connect(self.close); file_menu.addAction(exit_action)
        edit_menu = menu_bar.addMenu("编辑(&E)")
        settings_action = QAction("设置...", self); settings_action.triggered.connect(self.handle_open_settings); edit_menu.addAction(settings_action)

    def handle_open_settings(self):
        """【修改】保存设置后，通知所有打开的编辑器实时刷新。"""
        current_settings = load_settings()
        dialog = SettingsDialog(current_settings, self)
        
        if dialog.exec():
            updated_settings_data = dialog.get_settings()
            current_settings['settings'] = updated_settings_data
            if save_settings(current_settings):
                QMessageBox.information(self, "成功", "设置已保存！\n\n主题等部分设置需要重启应用生效。")
                # 通知所有打开的编辑器窗口刷新设置
                for editor_window in self.open_editors.values():
                    if editor_window:
                        editor_window.reload_settings_and_apply()
            else:
                QMessageBox.warning(self, "失败", "设置保存失败！")

    # ... 其他所有函数与之前版本完全相同 ...
    def setup_ui(self):
        central_widget = QWidget(); self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        title_label = QLabel("我的所有书籍"); title_label.setAlignment(Qt.AlignmentFlag.AlignCenter); title_label.setStyleSheet("font-size: 24px; font-weight: bold; margin: 10px;"); layout.addWidget(title_label)
        self.project_list_widget = QListWidget(); self.project_list_widget.itemDoubleClicked.connect(self.open_selected_project); self.project_list_widget.setStyleSheet("font-size: 16px;"); layout.addWidget(self.project_list_widget)
        button_layout = QVBoxLayout(); new_project_btn = QPushButton("新建书籍项目"); new_project_btn.clicked.connect(self.handle_new_project); remove_project_btn = QPushButton("从书架移除"); remove_project_btn.clicked.connect(self.handle_remove_project)
        button_layout.addWidget(new_project_btn); button_layout.addWidget(remove_project_btn); layout.addLayout(button_layout)
    def populate_project_list(self):
        self.project_list_widget.clear()
        settings = load_settings()
        for path in settings.get('projects', []):
            if os.path.exists(path):
                project_data = load_project_structure(path)
                book_title = project_data.get('bookTitle', '未知书籍') if project_data else os.path.basename(path)
                item = QListWidgetItem(book_title); item.setToolTip(path); item.setData(Qt.ItemDataRole.UserRole, path); self.project_list_widget.addItem(item)
    def open_selected_project(self, item: QListWidgetItem):
        project_path = item.data(Qt.ItemDataRole.UserRole)
        if not project_path: return
        if project_path in self.open_editors and self.open_editors[project_path].isVisible():
            self.open_editors[project_path].activateWindow(); return
        editor_window = MainWindow(project_path); editor_window.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        editor_window.destroyed.connect(lambda: self.open_editors.pop(project_path, None)); self.open_editors[project_path] = editor_window; editor_window.show()
    def handle_new_project(self):
        project_path = QFileDialog.getExistingDirectory(self, "选择一个空文件夹作为项目根目录")
        if not project_path or not os.path.isdir(project_path): return
        if os.listdir(project_path): QMessageBox.warning(self, "提醒", "请选择一个空文件夹！"); return
        book_title, ok = QInputDialog.getText(self, "设置书名", "请输入你的书籍名称：")
        if ok and book_title:
            initial_data = {"bookTitle": book_title, "author": "（请填写作者名）", "projectVersion": "1.0", "structure": []}
            os.makedirs(os.path.join(project_path, 'chapters'), exist_ok=True)
            if save_project_structure(project_path, initial_data):
                add_project_to_library(project_path); self.populate_project_list()
                QMessageBox.information(self, "成功", f"书籍 '{book_title}' 已创建！\n现在可以双击列表中的书名来打开它。")
            else: QMessageBox.critical(self, "错误", "无法创建项目文件！")
    def handle_remove_project(self):
        selected_item = self.project_list_widget.currentItem()
        if not selected_item: QMessageBox.warning(self, "提醒", "请先在列表中选择一本书。"); return
        project_path = selected_item.data(Qt.ItemDataRole.UserRole); book_title = selected_item.text()
        reply = QMessageBox.question(self, "确认移除", f"你确定要将 '{book_title}' 从书架移除吗？\n\n（注意：这只会从列表移除，不会删除硬盘上的实际文件。）", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes: remove_project_from_library(project_path); self.populate_project_list()
