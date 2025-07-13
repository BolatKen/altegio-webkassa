#!/usr/bin/env python3
"""Скрипт для красивого просмотра логов"""

import json
import re
import sys
from datetime import datetime

def decode_unicode_escapes(text):
    """Декодирует Unicode escape-последовательности"""
    try:
        # Декодируем unicode escape последовательности
        return text.encode().decode('unicode_escape')
    except:
        return text

def pretty_print_json(json_str):
    """Красиво форматирует JSON"""
    try:
        # Убираем экранированные кавычки
        clean_json = json_str.replace('\\"', '"')
        # Парсим JSON
        data = json.loads(clean_json)
        # Красиво форматируем
        return json.dumps(data, indent=2, ensure_ascii=False)
    except:
        return json_str

def format_log_line(line):
    """Форматирует строку лога"""
    # Декодируем Unicode
    line = decode_unicode_escapes(line)
    
    # Ищем JSON в строке
    json_pattern = r'(\{.*\}|\[.*\])'
    match = re.search(json_pattern, line)
    
    if match:
        json_part = match.group(1)
        before_json = line[:match.start()]
        after_json = line[match.end():]
        
        # Форматируем JSON
        formatted_json = pretty_print_json(json_part)
        
        return f"{before_json}\n{formatted_json}{after_json}"
    
    return line

def view_logs(filename="logs/errors.log", tail_lines=50):
    """Просматривает последние строки логов"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        # Берем последние строки
        recent_lines = lines[-tail_lines:] if len(lines) > tail_lines else lines
        
        print(f"📋 Последние {len(recent_lines)} строк из {filename}:")
        print("=" * 80)
        
        for i, line in enumerate(recent_lines, 1):
            line = line.strip()
            if line:
                formatted = format_log_line(line)
                print(f"{i:3d}: {formatted}")
                print("-" * 80)
                
    except FileNotFoundError:
        print(f"❌ Файл {filename} не найден")
    except Exception as e:
        print(f"❌ Ошибка при чтении файла: {e}")

def search_logs(filename="logs/errors.log", search_term="", last_minutes=60):
    """Ищет в логах за последние минуты"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        # Ищем строки с термином
        found_lines = []
        for line in lines:
            if search_term.lower() in line.lower():
                found_lines.append(line.strip())
        
        if found_lines:
            print(f"🔍 Найдено {len(found_lines)} строк с '{search_term}':")
            print("=" * 80)
            
            for i, line in enumerate(found_lines[-20:], 1):  # Последние 20 найденных
                formatted = format_log_line(line)
                print(f"{i:3d}: {formatted}")
                print("-" * 80)
        else:
            print(f"❌ Строки с '{search_term}' не найдены")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "search" and len(sys.argv) > 2:
            search_logs(search_term=sys.argv[2])
        else:
            try:
                tail_lines = int(sys.argv[1])
                view_logs(tail_lines=tail_lines)
            except ValueError:
                search_logs(search_term=sys.argv[1])
    else:
        view_logs()
