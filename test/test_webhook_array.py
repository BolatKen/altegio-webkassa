#!/usr/bin/env python3
"""
Тест для проверки обработки как массивов, так и одиночных webhook от Altegio
"""
import json
import requests

# Тестовые данные webhook
test_webhook = {
    "company_id": 307626,
    "resource": "record",
    "resource_id": 596792978,
    "status": "update",
    "data": {
        "id": 596792978,
        "company_id": 307626,
        "staff_id": 2835418,
        "clients_count": 1,
        "date": "2025-07-12 12:10:00",
        "comment": "фч",
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
        "datetime": "2025-07-12T12:10:00+05:00",
        "create_date": "2025-07-12T11:49:08+0500",
        "last_change_date": "2025-07-13T00:15:24+0500",
        "custom_fields": [],
        "custom_color": "",
        "custom_font_color": "",
        "record_labels": [],
        "documents": [
            {
                "id": 683647047,
                "type_id": 7,
                "storage_id": 0,
                "user_id": 12795431,
                "company_id": 307626,
                "number": 683647047,
                "comment": "",
                "date_created": "2025-07-12 13:10:00",
                "category_id": 0,
                "visit_id": 508928359,
                "record_id": 596792978,
                "type_title": "Visit",
                "is_sale_bill_printed": False
            }
        ],
        "short_link": "http://openhc.kz/c/Oyfhm/BqNtT/",
        "composite": []
    }
}


def test_webhook_endpoint(payload, test_name):
    """Функция для тестирования webhook endpoint"""
    url = "http://localhost/api/webhook"
    headers = {
        "Content-Type": "application/json",
        "X-Altegio-Signature": "test-signature"
    }
    
    print(f"\n=== {test_name} ===")
    print(f"URL: {url}")
    
    if isinstance(payload, list):
        print(f"Payload: массив из {len(payload)} элемент(ов)")
    else:
        print("Payload: одиночный объект")
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f"Status: {response.status_code}")
        
        if response.headers.get('content-type', '').startswith('application/json'):
            response_data = response.json()
            print(f"Response: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
        else:
            print(f"Response: {response.text}")
            
        if response.status_code == 200:
            print("✅ SUCCESS")
        else:
            print("❌ FAILED")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")


def main():
    print("🔄 ТЕСТИРОВАНИЕ WEBHOOK ENDPOINT")
    print("=" * 50)
    
    # Тест 1: Одиночный webhook объект
    test_webhook_endpoint(test_webhook, "Тест 1: Одиночный webhook")
    
    # Тест 2: Массив с одним webhook
    test_webhook_endpoint([test_webhook], "Тест 2: Массив с одним webhook")
    
    # Тест 3: Массив с несколькими webhook (изменим resource_id для второго)
    test_webhook_2 = test_webhook.copy()
    test_webhook_2["resource_id"] = 596792979
    test_webhook_2["data"] = test_webhook["data"].copy()
    test_webhook_2["data"]["id"] = 596792979
    
    test_webhook_endpoint([test_webhook, test_webhook_2], "Тест 3: Массив с двумя webhook")
    
    print("\n" + "=" * 50)
    print("🏁 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")


if __name__ == "__main__":
    main()
