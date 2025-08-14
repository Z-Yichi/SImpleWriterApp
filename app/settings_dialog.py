from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QDialogButtonBox,
    QSpinBox, QFontComboBox, QComboBox,
    QDoubleSpinBox, QHBoxLayout, QLineEdit, QPushButton, QFileDialog, QSlider, QCheckBox
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt


class SettingsDialog(QDialog):
    def __init__(self, current_settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setMinimumWidth(520)
        self.settings_data = current_settings['settings']

        # 控件
        self.theme_combo = QComboBox(); self.theme_combo.addItems(["vscode_dark", "vscode_light"])
        self.font_combo = QFontComboBox()
        self.font_size_spin = QSpinBox(); self.font_size_spin.setRange(8, 72)
        self.ui_font_combo = QFontComboBox()
        self.ui_font_size_spin = QSpinBox(); self.ui_font_size_spin.setRange(8, 48)
        self.line_spacing_spin = QDoubleSpinBox(); self.line_spacing_spin.setRange(1.0, 3.0); self.line_spacing_spin.setSingleStep(0.1); self.line_spacing_spin.setDecimals(1)
        self.autosave_spin = QSpinBox(); self.autosave_spin.setRange(1, 60); self.autosave_spin.setSuffix(" 秒")
        self.enter_mode_combo = QComboBox(); self.enter_mode_combo.addItems(["none", "halfwidth", "fullwidth"])
        self.show_line_numbers_cb = QCheckBox("状态栏显示行数")

        # 背景相关
        self.bg_path_edit = QLineEdit(); browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self.browse_for_image)
        bg_layout = QHBoxLayout(); bg_layout.addWidget(self.bg_path_edit); bg_layout.addWidget(browse_btn)
        self.bg_opacity_slider = QSlider(Qt.Orientation.Horizontal); self.bg_opacity_slider.setRange(0, 100)

        # 初始值
        sd = self.settings_data
        self.theme_combo.setCurrentText(sd.get('theme', 'vscode_dark'))
        self.font_combo.setCurrentFont(QFont(sd.get('editor_font_family', 'Microsoft YaHei')))
        self.font_size_spin.setValue(sd.get('editor_font_size', 16))
        self.ui_font_combo.setCurrentFont(QFont(sd.get('ui_font_family', sd.get('editor_font_family', 'Microsoft YaHei'))))
        self.ui_font_size_spin.setValue(sd.get('ui_font_size', 14))
        self.line_spacing_spin.setValue(sd.get('line_spacing_percent', 150) / 100.0)
        self.autosave_spin.setValue(sd.get('auto_save_interval', 3000) // 1000)
        self.bg_path_edit.setText(sd.get('background_image_path', ''))
        self.bg_opacity_slider.setValue(sd.get('background_opacity', 80))
        self.enter_mode_combo.setCurrentText(sd.get('enter_mode', 'fullwidth'))
        self.show_line_numbers_cb.setChecked(sd.get('show_line_numbers', False))

        # 布局
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.addRow("主题:", self.theme_combo)
        form.addRow("字体:", self.font_combo)
        form.addRow("字号:", self.font_size_spin)
        form.addRow("界面字体:", self.ui_font_combo)
        form.addRow("界面字号:", self.ui_font_size_spin)
        form.addRow("行距倍数:", self.line_spacing_spin)
        form.addRow("自动保存:", self.autosave_spin)
        form.addRow("背景图片:", bg_layout)
        form.addRow("背景不透明度:", self.bg_opacity_slider)
        form.addRow("回车缩进:", self.enter_mode_combo)
        form.addRow("状态栏行数:", self.show_line_numbers_cb)
        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def browse_for_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择背景图片", "", "图片 (*.png *.jpg *.jpeg *.bmp)")
        if path:
            self.bg_path_edit.setText(path)

    def accept(self):
        sd = self.settings_data
        sd['theme'] = self.theme_combo.currentText()
        sd['editor_font_family'] = self.font_combo.currentFont().family()
        sd['editor_font_size'] = self.font_size_spin.value()
        sd['ui_font_family'] = self.ui_font_combo.currentFont().family()
        sd['ui_font_size'] = self.ui_font_size_spin.value()
        sd['line_spacing_percent'] = int(self.line_spacing_spin.value() * 100)
        sd['auto_save_interval'] = self.autosave_spin.value() * 1000
        sd['background_image_path'] = self.bg_path_edit.text()
        sd['background_opacity'] = self.bg_opacity_slider.value()
        sd['enter_mode'] = self.enter_mode_combo.currentText()
        sd['show_line_numbers'] = self.show_line_numbers_cb.isChecked()
        super().accept()

    def get_settings(self):
        return self.settings_data
