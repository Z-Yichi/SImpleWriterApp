# app/settings_manager.py
import os
import json
from PyQt6.QtCore import QStandardPaths

CONFIG_DIR = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppConfigLocation)
if not os.path.exists(CONFIG_DIR): os.makedirs(CONFIG_DIR)
SETTINGS_FILE = os.path.join(CONFIG_DIR, 'settings.json')

DEFAULT_SETTINGS = {
    "projects": [],
    "settings": {
        "theme": "vscode_dark",
        "editor_font_family": "Microsoft YaHei",
        "editor_font_size": 16,
        "auto_save_interval": 3000,
        "line_spacing_percent": 150,
        # 【新增】背景设置
        "background_image_path": "",
        "background_opacity": 80 # 百分比
    }
}

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS
    try:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            settings = json.load(f)
            # 确保所有默认键都存在
            for key, value in DEFAULT_SETTINGS["settings"].items():
                if key not in settings["settings"]:
                    settings["settings"][key] = value
            return settings
    except (json.JSONDecodeError, TypeError):
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS

def save_settings(data):
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        print(f"Error saving settings: {e}")
        return False

def add_project_to_library(project_path):
    settings = load_settings()
    normalized_path = os.path.normpath(project_path)
    if normalized_path not in settings['projects']:
        settings['projects'].append(normalized_path)
        save_settings(settings)

def remove_project_from_library(project_path):
    settings = load_settings()
    normalized_path = os.path.normpath(project_path)
    if normalized_path in settings['projects']:
        settings['projects'].remove(normalized_path)
        save_settings(settings)
