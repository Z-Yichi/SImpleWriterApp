# app/themes.py

THEMES = {
    "vscode_dark": """
        QWidget {
            background-color: #1e1e1e;
            color: #d4d4d4;
            font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
            border: none;
        }
        QMainWindow, QDialog {
            background-color: #252526;
        }
        QTreeView, QListWidget {
            background-color: #252526;
            border: 1px solid #3c3c3c;
            font-size: 14px;
        }
        QTreeView::item:hover, QListWidget::item:hover {
            background-color: #2a2d2e;
        }
        QTreeView::item:selected, QListWidget::item:selected {
            background-color: #094771;
            color: #ffffff;
        }
        QPushButton {
            background-color: #3e3e42;
            border: 1px solid #555555;
            border-radius: 4px;
            padding: 8px 12px;
            font-size: 14px;
        }
        QPushButton:hover { background-color: #4f4f53; }
        QPushButton:pressed { background-color: #2a2a2d; }
        QTabWidget::pane { border: none; }
        QTabBar::tab {
            background: #2d2d2d;
            color: #aaaaaa;
            padding: 8px 15px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            margin-right: 1px;
        }
        QTabBar::tab:selected {
            background: #1e1e1e;
            color: #ffffff;
        }
        QTabBar::tab:!selected:hover { background: #3c3c3c; }
        QToolBar {
            background-color: #333333;
            border-bottom: 1px solid #3c3c3c;
            padding: 3px;
            spacing: 5px;
        }
        QToolBar QToolButton {
            background-color: transparent;
            border: none;
            padding: 5px;
            border-radius: 4px;
        }
        QToolBar QToolButton:hover { background-color: #4f4f53; }
        QToolBar QToolButton:pressed, QToolBar QToolButton:checked { background-color: #094771; }
        QTextEdit {
            background-color: #1e1e1e;
            color: #d4d4d4;
            padding: 10px;
        }
        QStatusBar { background-color: #007acc; color: #ffffff; }
        QMenu { background-color: #252526; border: 1px solid #3c3c3c; }
        QMenu::item:selected { background-color: #094771; }
    """,
    "vscode_light": """
        QWidget {
            background-color: #ffffff;
            color: #333333;
            font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
            border: none;
        }
        QMainWindow, QDialog {
            background-color: #f3f3f3;
        }
        QTreeView, QListWidget {
            background-color: #f3f3f3;
            border: 1px solid #e0e0e0;
            font-size: 14px;
        }
        QTreeView::item:hover, QListWidget::item:hover {
            background-color: #e8e8e8;
        }
        QTreeView::item:selected, QListWidget::item:selected {
            background-color: #cce5ff;
            color: #000000;
        }
        QPushButton {
            background-color: #f0f0f0;
            border: 1px solid #cccccc;
            border-radius: 4px;
            padding: 8px 12px;
            font-size: 14px;
        }
        QPushButton:hover { background-color: #e0e0e0; }
        QPushButton:pressed { background-color: #cccccc; }
        QTabWidget::pane { border: none; }
        QTabBar::tab {
            background: #ececec;
            color: #555555;
            padding: 8px 15px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            margin-right: 1px;
            border: 1px solid #e0e0e0;
            border-bottom: none;
        }
        QTabBar::tab:selected {
            background: #ffffff;
            color: #000000;
        }
        QTabBar::tab:!selected:hover { background: #f5f5f5; }
        QToolBar {
            background-color: #f3f3f3;
            border-bottom: 1px solid #e0e0e0;
            padding: 3px;
            spacing: 5px;
        }
        QToolBar QToolButton {
            background-color: transparent;
            border: none;
            padding: 5px;
            border-radius: 4px;
        }
        QToolBar QToolButton:hover { background-color: #e8e8e8; }
        QToolBar QToolButton:pressed, QToolBar QToolButton:checked { background-color: #cce5ff; }
        QTextEdit {
            background-color: #ffffff;
            color: #333333;
            padding: 10px;
        }
        QStatusBar { background-color: #007acc; color: #ffffff; }
        QMenu { background-color: #ffffff; border: 1px solid #e0e0e0; }
        QMenu::item:selected { background-color: #cce5ff; }
    """
}
