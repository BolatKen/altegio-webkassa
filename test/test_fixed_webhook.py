#!/usr/bin/env python3
"""
Тест для проверки исправленной обработки Altegio API
"""
import json
import requests

# Тестовые данные webhook с документом
test_webhook = {
    "company_id": 307626,
    "resource": "record",
    "resource_id": 596792980,  # Новый ID для тестирования
    "status": "update",
    "data": {
        "id": 596792980,
        "company_id": 307626,
        "staff_id": 2835418,
        "clients_count": 1,
        "date": "2025-07-13 12:10:00",
        "comment": "фч тест",
        "online": False,
        "visit_id": 508928360,
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
        "api_id": "01effc9e-09da-4db1-98a1-e317b214df2c",
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
                "title": "Стрижка детская (от 3х лет до 13 лет)",
                "cost": 4000,
                "cost_to_pay": 4000,
                "manual_cost": 4000,
                "cost_per_unit": 4000,
                "discount": 0,
                "first_cost": 4000,
                "amount": 1
            }
        ],
        "staff": {
            "id": 2835418,
            "api_id": None,
            "name": "Нурзад",
            "specialization": "Barber",
            "position": {
                "id": 122084,
                "title": "Барбер",
                "services_binding_type": 0
            },
            "avatar": "https://assets.alteg.io/masters/sm/d/d1/d1c0beac46776cc_20250418094518.png",
            "avatar_big": "https://assets.alteg.io/masters/origin/8/87/87766b4d0d03dcd_20250418094519.png",
            "rating": 5,
            "votes_count": 0
        },
        "goods_transactions": [],
        "sms_remain_hours": 1,
        "email_remain_hours": 1,
        "comer": None,
        "comer_person_info": None,
        "client": {
            "id": 169711586,
            "name": "Вячослав",
            "surname": "",
            "patronymic": "",
            "display_name": "Вячослав",
            "comment": "",
            "phone": "+77770220606",
            "card": "",
            "email": "",
            "success_visits_count": 3,
            "fail_visits_count": 0,
            "discount": 0,
            "custom_fields": [],
            "sex": 0,
            "birthday": "",
            "client_tags": []
        },
        "datetime": "2025-07-13T12:10:00+05:00",
        "create_date": "2025-07-13T11:49:08+0500",
        "last_change_date": "2025-07-13T12:15:24+0500",
        "custom_fields": [],
        "custom_color": "",
        "custom_font_color": "",
        "record_labels": [],
        "documents": [
            {
                "id": 683647048,  # Новый ID документа
                "type_id": 7,
                "storage_id": 0,
                "user_id": 12795431,
                "company_id": 307626,
                "number": 683647048,
                "comment": "",
                "date_created": "2025-07-13 13:10:00",
                "category_id": 0,
                "visit_id": 508928360,
                "record_id": 596792980,
                "type_title": "Visit",
                "is_sale_bill_printed": False
            }
        ],
        "short_link": "http://openhc.kz/c/Oyfhm/BqNtU/",
        "composite": []
    }
}


def test_webhook_endpoint():
    """Тест webhook с исправленной обработкой Altegio API"""
    url = "http://localhost/api/webhook"
    headers = {
        "Content-Type": "application/json"
    }
    
    print("🔄 ТЕСТИРОВАНИЕ ИСПРАВЛЕННОГО WEBHOOK")
    print("=" * 50)
    print(f"URL: {url}")
    print(f"Resource ID: {test_webhook['resource_id']}")
    
    try:
        response = requests.post(url, json=test_webhook, headers=headers)
        print(f"\nStatus: {response.status_code}")
        
        if response.headers.get('content-type', '').startswith('application/json'):
            response_data = response.json()
            print(f"Response: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
        else:
            print(f"Response: {response.text}")
            
        if response.status_code == 200:
            print("\n✅ SUCCESS: Webhook processed successfully!")
        else:
            print(f"\n❌ ERROR: Status {response.status_code}")
            
    except Exception as e:
        print(f"\n❌ REQUEST ERROR: {e}")


if __name__ == "__main__":
    test_webhook_endpoint()
    print("\n" + "=" * 50)
    print("🏁 ТЕСТ ЗАВЕРШЕН")
