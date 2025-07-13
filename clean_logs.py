#!/usr/bin/env python3
"""Простой скрипт для просмотра логов"""

import sys

def view_clean_logs(filename="logs/errors.log", lines=20, search=""):
    """Просмотр логов с фильтрацией"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
        
        # Фильтруем по поиску если нужно
        if search:
            filtered_lines = [line for line in all_lines if search.lower() in line.lower()]
            lines_to_show = filtered_lines[-lines:] if len(filtered_lines) > lines else filtered_lines
            print(f"🔍 Найдено {len(filtered_lines)} строк с '{search}', показываем последние {len(lines_to_show)}:")
        else:
            lines_to_show = all_lines[-lines:] if len(all_lines) > lines else all_lines
            print(f"📋 Последние {len(lines_to_show)} строк из {filename}:")
        
        print("=" * 80)
        
        for i, line in enumerate(lines_to_show, 1):
            # Убираем лишние символы и показываем чисто
            clean_line = line.strip()
            if clean_line:
                print(f"{i:3d}: {clean_line}")
                
    except FileNotFoundError:
        print(f"❌ Файл {filename} не найден")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    if len(sys.argv) == 1:
        view_clean_logs()
    elif len(sys.argv) == 2:
        try:
            lines_count = int(sys.argv[1])
            view_clean_logs(lines=lines_count)
        except ValueError:
            view_clean_logs(search=sys.argv[1])
    elif len(sys.argv) == 3:
        try:
            lines_count = int(sys.argv[1])
            view_clean_logs(lines=lines_count, search=sys.argv[2])
        except ValueError:
            view_clean_logs(search=sys.argv[1])
