# app/icons.py
from PyQt6.QtGui import QIcon, QPixmap, QPainter
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtCore import QByteArray, Qt

# SVG 图标数据
ICON_DATA = {
    # 采用更简洁的 2px 线框风格
    # save: 扁平软盘 + 顶部缺口 + 内部标签
    "save": """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M5 3h11l3 3v13a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2z'/><path d='M12 3v6h7'/><rect x='7' y='13' width='8' height='6' rx='1'/></svg>""",
    # undo: 逆时针半弧 + 左箭头
    "undo": """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M9 7H5v4'/><path d='M5 11a9 9 0 0 1 9-7 9 9 0 0 1 8 12'/></svg>""",
    # redo: 顺时针半弧 + 右箭头
    "redo": """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M15 7h4v4'/><path d='M20 11a9 9 0 0 0-9-7 9 9 0 0 0-8 12'/></svg>""",
    # bold: 两段包裹形成双区块 B
    "bold": """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M7 4h6a4 4 0 0 1 0 8H7z'/><path d='M13 12a4 4 0 0 1 0 8H7v-8'/></svg>""",
    # italic: 顶底基准线 + 斜杆
    "italic": """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M15 4H9'/><path d='M15 20H9'/><path d='M13 4l-2 16'/></svg>""",
    # underline: U 形 + 底线
    "underline": """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M6 4v8a6 6 0 0 0 12 0V4'/><path d='M4 21h16'/></svg>""",
    # find: 放大镜（比 search 留同款，语义映射）
    "find": """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><circle cx='11' cy='11' r='6'/><path d='m17 17 4 4'/></svg>""",
    # explorer: 双栏文件浏览框
    "explorer": """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><rect x='3' y='4' width='18' height='16' rx='2'/><path d='M9 4v16'/><path d='M3 10h18'/></svg>""",
    # search: 与 find 保持一致，可做语义区分（或后续换成全局检索特征）
    "search": """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><circle cx='11' cy='11' r='6'/><path d='m17 17 4 4'/></svg>""",
    # settings: 对称六齿轮（外圈由 6 个缺口 + 中心圆），更清晰简洁
    "settings": """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><circle cx='12' cy='12' r='3'/><path d='M12 2.5 13.2 5a1 1 0 0 0 .9.6l2.5.2-.9 2.2a1 1 0 0 0 .3 1.1l1.9 1.4-1.9 1.4a1 1 0 0 0-.3 1.1l.9 2.2-2.5.2a1 1 0 0 0-.9.6L12 21.5 10.8 19a1 1 0 0 0-.9-.6l-2.5-.2.9-2.2a1 1 0 0 0-.3-1.1L5.1 13l1.9-1.4a1 1 0 0 0 .3-1.1L6.4 8.3l2.5-.2a1 1 0 0 0 .9-.6L12 2.5Z'/></svg>""",
}

_ICON_OVERRIDE_DIR = None

def set_icon_override_dir(path: str):
    global _ICON_OVERRIDE_DIR
    _ICON_OVERRIDE_DIR = path

def _icon_from_svg(svg_data: str, color: str) -> QIcon:
    colored_svg = svg_data.replace('currentColor', color)
    renderer = QSvgRenderer(QByteArray(colored_svg.encode('utf-8')))
    pm = QPixmap(24, 24)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    renderer.render(p)
    p.end()
    return QIcon(pm)

def get_icon(name, color="#333333"):
    # 覆盖目录支持 png/svg
    if _ICON_OVERRIDE_DIR:
        from pathlib import Path
        for ext in ('.png', '.svg', '.ico'):
            candidate = Path(_ICON_OVERRIDE_DIR) / f"{name}{ext}"
            if candidate.exists():
                if ext == '.svg':
                    try:
                        data = candidate.read_text(encoding='utf-8')
                        return _icon_from_svg(data, color)
                    except Exception:
                        pass
                else:
                    return QIcon(str(candidate))
    svg_data = ICON_DATA.get(name)
    if not svg_data:
        return QIcon()
    return _icon_from_svg(svg_data, color)
