#!/usr/bin/env python3
"""
Простой тест автоматического обновления API ключа
"""

import requests
import json

def test_api_key_management():
    """
    Тестирует получение ключа из базы данных и систему автообновления
    """
    
    # Тест 1: Прямой вызов endpoint для получения ключа
    print("🔍 Тест 1: Проверка получения API ключа из базы данных")
    try:
        # Попробуем вызвать endpoint, который использует get_webkassa_api_key
        response = requests.get("http://localhost:8080/api/webhook/status/123", timeout=10)
        print(f"📊 Статус ответа: {response.status_code}")
        print(f"📝 Ответ: {response.text}")
        
        if response.status_code in [200, 404]:  # 404 ожидаем, так как записи нет
            print("✅ Endpoint доступен, проверяем логи...")
        else:
            print(f"⚠️ Неожиданный статус: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Ошибка тестирования endpoint: {e}")
    
    print("\n" + "="*70 + "\n")
    
    # Тест 2: Попробуем вызвать скрипт обновления ключа через Docker
    print("🔄 Тест 2: Проверка скрипта обновления ключа")
    try:
        import subprocess
        result = subprocess.run([
            "docker", "exec", "altegio_webkassa_backend", 
            "python", "/app/scripts/update_webkassa_key.py"
        ], capture_output=True, text=True, timeout=30)
        
        print(f"📊 Код возврата: {result.returncode}")
        print(f"📝 Вывод: {result.stdout}")
        if result.stderr:
            print(f"⚠️ Ошибки: {result.stderr}")
            
        if result.returncode == 0:
            print("✅ Скрипт обновления выполнен успешно")
        else:
            print(f"❌ Скрипт завершился с ошибкой: {result.returncode}")
            
    except Exception as e:
        print(f"❌ Ошибка выполнения скрипта: {e}")

def check_logs():
    """
    Проверяет логи для поиска информации об API ключах
    """
    print("🔍 Тест 3: Анализ логов приложения")
    try:
        import subprocess
        result = subprocess.run([
            "docker-compose", "logs", "backend", "--tail=20"
        ], capture_output=True, text=True, timeout=10, cwd=".")
        
        print("📋 Последние 20 строк логов backend:")
        print(result.stdout)
        
        if "webkassa" in result.stdout.lower() or "api" in result.stdout.lower():
            print("✅ Найдены упоминания API или Webkassa в логах")
        else:
            print("⚠️ Не найдено упоминаний API или Webkassa в логах")
            
    except Exception as e:
        print(f"❌ Ошибка получения логов: {e}")

if __name__ == "__main__":
    print("🧪 Тестирование системы управления API ключами")
    print("="*70)
    
    test_api_key_management()
    
    print("\n" + "="*70 + "\n")
    
    check_logs()
    
    print("\n" + "="*70)
    print("✅ Тестирование завершено!")
