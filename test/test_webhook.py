#!/usr/bin/env python3
"""
Test script for webhook endpoint to verify array payload handling
"""
import json
import requests

# Test data based on the error log from Altegio
test_payload = [
    {
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
]


def test_webhook_array():
    """Test webhook endpoint with array payload"""
    url = "http://localhost/api/webhook"
    headers = {
        "Content-Type": "application/json",
        "X-Altegio-Signature": "test-signature"
    }
    
    print("Testing webhook endpoint with array payload...")
    print(f"URL: {url}")
    print(f"Payload size: {len(test_payload)} webhook(s)")
    
    try:
        response = requests.post(url, json=test_payload, headers=headers)
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.headers.get('content-type', '').startswith('application/json'):
            response_data = response.json()
            print(f"Response Body: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
        else:
            print(f"Response Body: {response.text}")
            
        if response.status_code == 200:
            print("\n✅ SUCCESS: Webhook array payload processed successfully!")
        else:
            print(f"\n❌ ERROR: Webhook failed with status {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ REQUEST ERROR: {e}")
    except json.JSONDecodeError as e:
        print(f"\n❌ JSON DECODE ERROR: {e}")
        print(f"Raw response: {response.text}")


def test_webhook_single():
    """Test webhook endpoint with single payload"""
    url = "http://localhost/api/webhook"
    headers = {
        "Content-Type": "application/json",
        "X-Altegio-Signature": "test-signature"
    }
    
    # Use first element from array as single payload
    single_payload = test_payload[0]
    
    print("\nTesting webhook endpoint with single payload...")
    print(f"URL: {url}")
    
    try:
        response = requests.post(url, json=single_payload, headers=headers)
        print(f"\nResponse Status: {response.status_code}")
        
        if response.headers.get('content-type', '').startswith('application/json'):
            response_data = response.json()
            print(f"Response Body: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
        else:
            print(f"Response Body: {response.text}")
            
        if response.status_code == 200:
            print("\n✅ SUCCESS: Webhook single payload processed successfully!")
        else:
            print(f"\n❌ ERROR: Webhook failed with status {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ REQUEST ERROR: {e}")
    except json.JSONDecodeError as e:
        print(f"\n❌ JSON DECODE ERROR: {e}")
        print(f"Raw response: {response.text}")


if __name__ == "__main__":
    print("=" * 60)
    print("WEBHOOK ENDPOINT TEST")
    print("=" * 60)
    
    # Test both array and single webhook payloads
    test_webhook_array()
    test_webhook_single()
    
    print("\n" + "=" * 60)
    print("TEST COMPLETED")
    print("=" * 60)
