# main.py
import sys
from PyQt6.QtWidgets import QApplication

from app.library_window import LibraryWindow
from app.settings_manager import load_settings
from app.themes import THEMES
from PyQt6.QtGui import QIcon
import os

def main():
    """程序主入口"""
    app = QApplication(sys.argv)
    app.setOrganizationName("MyCoolCompany")
    app.setApplicationName("MyWritingApp")

    # 全局窗口图标设置：依次尝试项目根目录下的 icon.ico / icon.png / icon.svg
    base_dir = os.path.dirname(__file__)
    for candidate in ("icon.ico", "icon.png", "icon.svg"):
        p = os.path.join(base_dir, candidate)
        if os.path.exists(p):
            # svg 也可直接作为 QIcon 载入（Qt 会处理多分辨率缩放）
            app.setWindowIcon(QIcon(p))
            break

    # --- 【修改】加载并应用新的 VS Code 风格主题 ---
    settings = load_settings()
    # 默认使用我们新的 vscode_dark 主题
    theme_name = settings.get('settings', {}).get('theme', 'vscode_dark') 
    # 如果配置文件里的主题名不存在，则强制使用 vscode_dark
    app.setStyleSheet(THEMES.get(theme_name, THEMES['vscode_dark']))

    window = LibraryWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
