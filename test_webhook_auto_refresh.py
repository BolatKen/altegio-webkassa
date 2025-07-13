#!/usr/bin/env python3
"""
Тест автоматического обновления API ключа при обработке webhook
"""

import json
import requests
from datetime import datetime

# URL webhook'а
webhook_url = "http://localhost:8080/api/webhook"

# Тестовые данные webhook'а от Altegio (как массив)
test_webhook_data = [{
    "company_id": 123456,
    "resource": "record",
    "resource_id": 987654321,
    "status": "visit_confirmed",
    "data": {
        "id": 987654321,
        "datetime": "2024-01-15 12:30:00+06:00",
        "client": {
            "id": 555777,
            "name": "Тестовый Клиент",
            "phone": "77771234567"
        },
        "services": [
            {
                "id": 111222,
                "title": "Стрижка",
                "cost": 5000,  # в тиынах (50 тенге)
                "amount": 1,
                "discount": 0
            },
            {
                "id": 333444,
                "title": "Укладка",
                "cost": 3000,  # в тиынах (30 тенге)
                "amount": 1,
                "discount": 500  # скидка 5 тенге
            }
        ],
        "comment": "Тестовая запись для проверки автообновления ключа",
        "documents": [
            {
                "id": 777888999,
                "type": "receipt"
            }
        ]
    }
}]

def test_webhook():
    """
    Отправляет тестовый webhook и проверяет ответ
    """
    print("🚀 Отправка тестового webhook для проверки автообновления API ключа...")
    print(f"📡 URL: {webhook_url}")
    print(f"📋 Данные: {json.dumps(test_webhook_data, indent=2, ensure_ascii=False)}")
    
    try:
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Altegio Webhook Test"
        }
        
        response = requests.post(
            webhook_url, 
            json=test_webhook_data, 
            headers=headers, 
            timeout=60
        )
        
        print(f"\n📈 Статус ответа: {response.status_code}")
        print(f"📄 Заголовки ответа: {dict(response.headers)}")
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"✅ Успешный ответ:")
            print(f"📝 Данные ответа: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ Ошибка HTTP {response.status_code}:")
            print(f"📝 Текст ответа: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка сети: {e}")
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")

if __name__ == "__main__":
    print("🧪 Тестирование webhook с автоматическим обновлением API ключа")
    print(f"⏰ Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    test_webhook()
    
    print("=" * 70)
    print("✅ Тест завершен!")
    print("\n📊 Проверьте логи Docker контейнера для подробной информации:")
    print("docker-compose logs backend --tail=50")
