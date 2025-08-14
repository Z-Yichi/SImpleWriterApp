# app/project_manager.py
import os
import json
import uuid
import re
import html as _html
from .config import (CHAPTER_PREFIX, CHAPTER_SUFFIX, CHAPTER_PADDING,
                     VOLUME_PREFIX, VOLUME_SUFFIX, VOLUME_USE_CHINESE_NUMERALS)

# 中文/阿拉伯数字转换相关的辅助函数 (保持不变)
CHINESE_NUMERALS_MAP = {
    '一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '十': 10
}
INT_TO_CHINESE_MAP = {v: k for k, v in CHINESE_NUMERALS_MAP.items()}

def to_chinese_numeral(n):
    if n <= 10: return INT_TO_CHINESE_MAP.get(n, str(n))
    if n < 20: return f"十{INT_TO_CHINESE_MAP.get(n % 10, '')}"
    return str(n)

def sanitize_filename(name):
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    name = name.replace(" ", "_")
    return name

def get_next_volume_number(data):
    max_num = 0
    for volume in data.get('structure', []):
        title = volume.get('title', '')
        match = re.search(f"{VOLUME_PREFIX}(.+?){VOLUME_SUFFIX}", title)
        if match:
            num_str = match.group(1)
            if num_str in CHINESE_NUMERALS_MAP:
                max_num = max(max_num, CHINESE_NUMERALS_MAP[num_str])
            elif num_str.isdigit():
                max_num = max(max_num, int(num_str))
    return max_num + 1

def get_next_chapter_number(data):
    max_num = 0
    for volume in data.get('structure', []):
        for chapter in volume.get('children', []):
            title = chapter.get('title', '')
            num_part = re.search(r'\d+', title)
            if num_part:
                max_num = max(max_num, int(num_part.group()))
    return max_num + 1

# --- 以下函数中的逻辑有修正 ---

def add_new_volume(data, volume_topic):
    next_num = get_next_volume_number(data)
    if VOLUME_USE_CHINESE_NUMERALS:
        num_str = to_chinese_numeral(next_num)
    else:
        num_str = str(next_num)
    full_title = f"{VOLUME_PREFIX}{num_str}{VOLUME_SUFFIX}：{volume_topic}"
    new_volume = {"id": f"vol-{uuid.uuid4().hex[:8]}", "type": "volume", "title": full_title, "children": []}
    data['structure'].append(new_volume)
    return True

def add_new_chapter(project_path, data, volume_id, chapter_topic):
    """修正此函数的逻辑错误。"""
    for volume in data['structure']:
        if volume['id'] == volume_id:
            next_num = get_next_chapter_number(data)
            num_str = str(next_num).zfill(CHAPTER_PADDING)
            full_title = f"{CHAPTER_PREFIX}{num_str}{CHAPTER_SUFFIX} {chapter_topic}"
            sanitized_topic = sanitize_filename(chapter_topic)
            new_filename = f"{num_str}-{sanitized_topic}.txt"
            new_chapter_id = f"chap-{uuid.uuid4().hex[:8]}"
            new_chapter = {"id": new_chapter_id, "type": "chapter", "title": full_title, "filename": new_filename}
            volume['children'].append(new_chapter)
            try:
                open(os.path.join(project_path, 'chapters', new_filename), 'w', encoding='utf-8').close()
                # 找到并处理完后，直接返回True，退出函数
                return True
            except Exception as e:
                # 如果文件创建失败，回滚操作
                volume['children'].pop()
                print(f"Error creating chapter file: {e}")
                return False
    
    # --- 【关键修正】---
    # 这句 return False 必须放在 for 循环的外面！
    # 这样才能保证在遍历完所有卷都找不到匹配的id后，才返回False。
    return False

# --- 其他函数保持不变 ---
def rename_item_in_structure(data, item_id, new_title):
    for volume in data['structure']:
        if volume['id'] == item_id: volume['title'] = new_title; return True
        for chapter in volume['children']:
            if chapter['id'] == item_id: chapter['title'] = new_title; return True
    return False

def delete_item(project_path, data, item_id):
    for i, volume in enumerate(data['structure']):
        if volume['id'] == item_id:
            for chapter in volume.get('children', []):
                if chapter.get('filename'):
                    chapter_filename = chapter.get('filename')
                    # 删富文本文件
                    try: os.remove(os.path.join(project_path, 'chapters', chapter_filename))
                    except FileNotFoundError: pass
                    # 删纯文本备份
                    try: os.remove(os.path.join(project_path, 'plain_backup', chapter_filename))
                    except FileNotFoundError: pass
            del data['structure'][i]
            return True
        for j, chapter in enumerate(volume.get('children', [])):
            if chapter['id'] == item_id:
                if chapter.get('filename'):
                    chapter_filename = chapter.get('filename')
                    try: os.remove(os.path.join(project_path, 'chapters', chapter_filename))
                    except FileNotFoundError: pass
                    try: os.remove(os.path.join(project_path, 'plain_backup', chapter_filename))
                    except FileNotFoundError: pass
                del volume['children'][j]
                return True
    return False

def load_project_structure(project_path):
    json_path = os.path.join(project_path, "project.json")
    try:
        with open(json_path, 'r', encoding='utf-8') as f: return json.load(f)
    except Exception as e: return None

def save_project_structure(project_path, data):
    json_path = os.path.join(project_path, "project.json")
    try:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e: return False

def load_chapter_content(project_path, filename):
    chapter_path = os.path.join(project_path, 'chapters', filename)
    try:
        with open(chapter_path, 'r', encoding='utf-8') as f: return f.read()
    except FileNotFoundError: return f"错误：无法加载文件\n路径：{chapter_path}"
    except Exception as e: return f"错误：读取文件失败\n{e}"

def save_chapter_content(project_path, filename, content):
    chapter_path = os.path.join(project_path, 'chapters', filename)
    try:
        with open(chapter_path, 'w', encoding='utf-8') as f:
            f.write(content)
        # 生成纯文本备份
        try:
            backup_dir = os.path.join(project_path, 'plain_backup')
            os.makedirs(backup_dir, exist_ok=True)
            plain = content
            # 保留段落/换行
            plain = re.sub(r'(?i)<br\s*/?>', '\n', plain)
            plain = re.sub(r'(?i)</p>', '\n', plain)
            # 去除样式与脚本
            plain = re.sub(r'(?is)<style.*?</style>', '', plain)
            plain = re.sub(r'(?is)<script.*?</script>', '', plain)
            # 去标签
            plain = re.sub(r'<[^>]+>', '', plain)
            # HTML 实体
            plain = _html.unescape(plain)
            # 规范换行: 去除多余连续空行（保留最多两个）
            plain = re.sub(r'\n{3,}', '\n\n', plain)
            with open(os.path.join(backup_dir, filename), 'w', encoding='utf-8') as pf:
                pf.write(plain.strip() + '\n')
        except Exception:
            pass
        return True, "保存成功"
    except Exception as e: return False, str(e)