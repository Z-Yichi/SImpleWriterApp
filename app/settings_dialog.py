# app/settings_dialog.py
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QDialogButtonBox, 
                                QSpinBox, QFontComboBox, QComboBox, QLabel, 
                                QDoubleSpinBox, QHBoxLayout, QLineEdit, QPushButton, QFileDialog, QSlider)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

class SettingsDialog(QDialog):
    def __init__(self, current_settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setMinimumWidth(450)
        self.settings_data = current_settings['settings']

        # --- 创建UI控件 ---
        self.theme_combo = QComboBox(); self.theme_combo.addItems(["vscode_dark", "vscode_light"])
        self.font_combo = QFontComboBox()
        self.font_size_spin = QSpinBox(); self.font_size_spin.setRange(8, 72)
        self.line_spacing_spin = QDoubleSpinBox(); self.line_spacing_spin.setRange(1.0, 3.0); self.line_spacing_spin.setSingleStep(0.1); self.line_spacing_spin.setDecimals(1)
        self.autosave_spin = QSpinBox(); self.autosave_spin.setRange(1, 60); self.autosave_spin.setSuffix(" 秒")
        
        # 【新增】背景图片设置
        self.bg_path_edit = QLineEdit()
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self.browse_for_image)
        bg_layout = QHBoxLayout()
        bg_layout.addWidget(self.bg_path_edit)
        bg_layout.addWidget(browse_btn)

        # 【新增】背景不透明度设置
        self.bg_opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.bg_opacity_slider.setRange(0, 100) # 0-100%

        # --- 应用当前设置 ---
        self.theme_combo.setCurrentText(self.settings_data.get('theme', 'vscode_dark'))
        self.font_combo.setCurrentFont(QFont(self.settings_data.get('editor_font_family', 'Microsoft YaHei')))
        self.font_size_spin.setValue(self.settings_data.get('editor_font_size', 16))
        self.line_spacing_spin.setValue(self.settings_data.get('line_spacing_percent', 150) / 100.0)
        self.autosave_spin.setValue(self.settings_data.get('auto_save_interval', 3000) // 1000)
        self.bg_path_edit.setText(self.settings_data.get('background_image_path', ''))
        self.bg_opacity_slider.setValue(self.settings_data.get('background_opacity', 80))

        # --- 布局 ---
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        form_layout.addRow("主题:", self.theme_combo)
        form_layout.addRow("编辑器字体:", self.font_combo)
        form_layout.addRow("字体大小:", self.font_size_spin)
        form_layout.addRow("行距倍数:", self.line_spacing_spin)
        form_layout.addRow("自动保存间隔:", self.autosave_spin)
        form_layout.addRow("背景图片:", bg_layout)
        form_layout.addRow("背景不透明度:", self.bg_opacity_slider)
        layout.addLayout(form_layout)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept); button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def browse_for_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择背景图片", "", "图片文件 (*.png *.jpg *.jpeg *.bmp)")
        if file_path:
            self.bg_path_edit.setText(file_path)

    def accept(self):
        self.settings_data['theme'] = self.theme_combo.currentText()
        self.settings_data['editor_font_family'] = self.font_combo.currentFont().family()
        self.settings_data['editor_font_size'] = self.font_size_spin.value()
        self.settings_data['line_spacing_percent'] = int(self.line_spacing_spin.value() * 100)
        self.settings_data['auto_save_interval'] = self.autosave_spin.value() * 1000
        self.settings_data['background_image_path'] = self.bg_path_edit.text()
        self.settings_data['background_opacity'] = self.bg_opacity_slider.value()
        super().accept()

    def get_settings(self):
        return self.settings_data
