#!/usr/bin/env python3
"""
Тест системы автообновления API ключей для Webkassa
"""

import requests
import json
from datetime import datetime

def test_api_key_refresh():
    """
    Тестирует автообновление API ключа
    """
    print("🔄 Тестирование системы автообновления API ключей")
    print("=" * 60)
    
    # Проверим текущий ключ в базе
    print("1️⃣ Проверка текущего API ключа в базе данных...")
    
    try:
        import subprocess
        result = subprocess.run([
            "docker", "exec", "altegio_webkassa_db", "psql", "-U", "postgres", 
            "-d", "altegio_webkassa_db", "-c", 
            "SELECT LEFT(api_key, 20) as key_start, RIGHT(api_key, 20) as key_end, updated_at FROM api_keys WHERE service_name='Webkassa';"
        ], capture_output=True, text=True, timeout=10)
        
        print(f"📊 База данных ответ: {result.stdout}")
        if result.stderr:
            print(f"⚠️ Предупреждения: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Ошибка проверки базы данных: {e}")
    
    print("\n" + "="*60 + "\n")
    
    # Запустим обновление ключа
    print("2️⃣ Запуск скрипта обновления API ключа...")
    
    try:
        result = subprocess.run([
            "docker", "exec", "altegio_webkassa_backend", 
            "python", "scripts/update_webkassa_key.py"
        ], capture_output=True, text=True, timeout=30)
        
        print(f"📊 Код возврата: {result.returncode}")
        print(f"📝 Вывод скрипта:")
        print(result.stdout)
        
        if result.stderr:
            print(f"⚠️ Ошибки:")
            print(result.stderr)
            
        if result.returncode == 0:
            print("✅ Скрипт обновления выполнен успешно")
        else:
            print(f"❌ Скрипт завершился с ошибкой: {result.returncode}")
            
    except Exception as e:
        print(f"❌ Ошибка выполнения скрипта: {e}")
    
    print("\n" + "="*60 + "\n")
    
    # Проверим ключ после обновления
    print("3️⃣ Проверка API ключа после обновления...")
    
    try:
        result = subprocess.run([
            "docker", "exec", "altegio_webkassa_db", "psql", "-U", "postgres", 
            "-d", "altegio_webkassa_db", "-c", 
            "SELECT LEFT(api_key, 20) as key_start, RIGHT(api_key, 20) as key_end, updated_at FROM api_keys WHERE service_name='Webkassa';"
        ], capture_output=True, text=True, timeout=10)
        
        print(f"📊 База данных ответ: {result.stdout}")
        if result.stderr:
            print(f"⚠️ Предупреждения: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Ошибка проверки базы данных: {e}")

if __name__ == "__main__":
    print("🧪 Тестирование системы управления API ключами Webkassa")
    print(f"⏰ Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    test_api_key_refresh()
    
    print("\n" + "=" * 70)
    print("✅ Тестирование завершено!")
    print("\n💡 Рекомендации:")
    print("   - Если ключ обновился, система работает правильно")
    print("   - Если ошибки, проверьте переменные окружения WEBKASSA_*")
    print("   - Убедитесь, что логин/пароль Webkassa актуальны")
