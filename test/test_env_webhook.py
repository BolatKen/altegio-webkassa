#!/usr/bin/env python3
"""
Простой тест для проверки переменных окружения в webhook
"""
import requests
import json

# Минимальный webhook payload который пройдет все проверки
webhook_data = [{
    "company_id": 307626,
    "resource": "record", 
    "resource_id": 999999,
    "status": "update",
    "data": {
        "id": 999999,
        "company_id": 307626,
        "staff_id": 2835418,
        "clients_count": 1,
        "date": "2025-07-14 10:00:00",
        "comment": "фч тест переменных окружения",
        "online": False,
        "visit_id": 508928359,
        "visit_attendance": 1,
        "attendance": 1,
        "confirmed": 1,
        "seance_length": 1500,
        "length": 1500,
        "sms_before": 1,
        "sms_now": 1,
        "sms_now_text": "",
        "email_now": 1,
        "notified": 0,
        "master_request": 0,
        "api_id": "test-api-id",
        "from_url": "",
        "review_requested": 0,
        "created_user_id": 12795431,
        "deleted": False,
        "paid_full": 1,
        "prepaid": False,
        "prepaid_confirmed": False,
        "is_update_blocked": False,
        "activity_id": 0,
        "bookform_id": 0,
        "record_from": "",
        "is_mobile": 0,
        "services": [{
            "id": 5034676,
            "title": "Тестовая услуга",
            "cost": 1000,
            "cost_to_pay": 1000,
            "manual_cost": 1000,
            "cost_per_unit": 1000,
            "discount": 0,
            "first_cost": 1000,
            "amount": 1
        }],
        "staff": {
            "id": 2835418,
            "name": "Тестовый мастер"
        },
        "sms_remain_hours": 1,
        "email_remain_hours": 1,
        "client": {
            "id": 123456,
            "name": "Тестовый клиент",
            "phone": "+77077777777"
        },
        "datetime": "2025-07-14T10:00:00",
        "create_date": "2025-07-14T09:00:00",
        "last_change_date": "2025-07-14T09:30:00",
        "short_link": "http://test.link",
        "document": {
            "id": 123456
        }
    }
}]

url = "http://localhost:8000/api/webhook"

try:
    print("🧪 Отправляем тестовый webhook...")
    response = requests.post(url, json=webhook_data, timeout=30)
    
    print(f"📊 Status Code: {response.status_code}")
    print(f"📋 Response: {response.text}")
    
    if response.status_code == 200:
        print("✅ Webhook обработан успешно!")
    else:
        print("❌ Ошибка при обработке webhook")
        
except Exception as e:
    print(f"💥 Ошибка: {e}")
