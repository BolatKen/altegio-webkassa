#!/usr/bin/env python3
"""
Тест автообновления API ключа через webhook
"""

import requests
import json
from datetime import datetime

def test_webhook_auto_refresh():
    """
    Тестирует автообновление через webhook с правильными данными
    """
    print("🧪 Тестирование автообновления API ключа через webhook")
    print("=" * 70)
    
    # Данные для webhook
    webhook_data = {
        "id": 12345,
        "event": "record_create",
        "data": {
            "id": 67890,
            "comment": "фч",
            "cost": 1500,
            "paid": 1500,
            "client": {
                "id": 111,
                "name": "Тестовый Клиент",
                "phone": "+77771234567"
            },
            "staff": {
                "id": 222,
                "name": "Тестовый Мастер"
            },
            "company": {
                "id": 333,
                "title": "Тестовая Компания"
            },
            "services": [
                {
                    "id": 444,
                    "title": "Тестовая Услуга",
                    "cost": 1500
                }
            ],
            "datetime": "2025-07-14 03:47:00"
        }
    }
    
    print("📤 Отправка webhook запроса...")
    print("🔗 URL: http://localhost:8000/webhook/altegio")
    
    try:
        response = requests.post(
            "http://localhost:8000/webhook/altegio",
            json=webhook_data,
            timeout=30
        )
        
        print(f"📊 Статус ответа: {response.status_code}")
        print(f"📝 Ответ сервера: {response.text}")
        
        if response.status_code == 200:
            print("✅ Webhook обработан успешно")
        else:
            print(f"⚠️ Webhook вернул статус {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Не удается подключиться к серверу")
        print("💡 Проверьте, что контейнер запущен: docker-compose ps")
    except requests.exceptions.Timeout:
        print("⏱️ Таймаут запроса")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    print("🚀 Тестирование webhook с автообновлением API ключа")
    print(f"⏰ Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    test_webhook_auto_refresh()
    
    print("\n" + "=" * 70)
    print("✅ Тестирование завершено!")
