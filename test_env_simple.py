#!/usr/bin/env python3
"""Простой тест для проверки переменных окружения"""

import os
import requests
import json
import sys

def test_webhook_endpoint():
    """Тестируем эндпоинт webhook"""
    
    print("🧪 Тестируем переменные окружения и webhook...")
    
    # Полный тестовый payload на основе реальной схемы
    test_payload = [
        {
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
                "services": [
                    {
                        "id": 5034676,
                        "title": "Тестовая услуга",
                        "cost": 1000,
                        "cost_to_pay": 1000,
                        "manual_cost": 1000,
                        "cost_per_unit": 1000,
                        "discount": 0,
                        "first_cost": 1000,
                        "amount": 1
                    }
                ],
                "staff": {
                    "id": 2835418,
                    "name": "Тестовый мастер",
                    "api_id": None,
                    "specialization": "Мастер",
                    "position": {
                        "id": 122084,
                        "title": "Мастер",
                        "services_binding_type": 0
                    },
                    "avatar": "",
                    "avatar_big": "",
                    "rating": 5.0,
                    "votes_count": 10
                },
                "goods_transactions": [],
                "sms_remain_hours": 1,
                "email_remain_hours": 1,
                "comer": None,
                "comer_person_info": None,
                "client": {
                    "id": 123456,
                    "name": "Тестовый клиент",
                    "surname": "",
                    "patronymic": "",
                    "display_name": "Тестовый клиент",
                    "comment": "",
                    "phone": "+77077777777",
                    "card": "",
                    "email": "",
                    "success_visits_count": 1,
                    "fail_visits_count": 0,
                    "discount": 0,
                    "custom_fields": [],
                    "sex": 1,
                    "birthday": "",
                    "client_tags": []
                },
                "datetime": "2025-07-14T10:00:00",
                "create_date": "2025-07-14T09:00:00",
                "last_change_date": "2025-07-14T09:30:00",
                "custom_fields": [],
                "custom_color": "",
                "custom_font_color": "",
                "record_labels": [],
                "documents": [
                    {
                        "id": 123456,
                        "type_id": 7,
                        "storage_id": 0,
                        "user_id": 12795431,
                        "company_id": 307626,
                        "number": 123456,
                        "comment": "",
                        "date_created": "2025-07-14T09:30:00",
                        "category_id": 0,
                        "visit_id": 508928359,
                        "record_id": 999999,
                        "type_title": "Visit",
                        "is_sale_bill_printed": False
                    }
                ],
                "short_link": "http://test.link",
                "composite": []
            }
        }
    ]
    
    try:
        # Отправляем POST запрос
        response = requests.post(
            "http://localhost:8000/api/webhook",
            json=test_payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📋 Response: {response.text[:1000]}...")
        
        if response.status_code == 200:
            print("✅ Webhook обработан успешно!")
        else:
            print("❌ Ошибка при обработке webhook")
            
    except Exception as e:
        print(f"❌ Ошибка соединения: {e}")

def test_env_vars():
    """Проверяем переменные окружения"""
    
    print("\n🔍 Проверяем переменные окружения...")
    
    # Проверяем локальные переменные
    local_env = os.environ.get('WEBKASSA_API_URL', 'НЕ НАЙДЕНО')
    print(f"📄 Локальная WEBKASSA_API_URL: {local_env}")
    
    # Проверяем что происходит в контейнере
    try:
        response = requests.get("http://localhost:8000/health")
        print(f"🏥 Health check: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Ошибка health check: {e}")

if __name__ == "__main__":
    test_env_vars()
    test_webhook_endpoint()
