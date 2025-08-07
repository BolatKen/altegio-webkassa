#!/usr/bin/env python3
"""
Тест для проверки webhook системы в Docker окружении
"""

import asyncio
import json
import httpx
from datetime import datetime

# Тестовые данные webhook'а из Altegio
test_webhook_data = {
    "resource_type": "record",
    "resource_id": 987654321,
    "data": {
        "id": 987654321,
        "document": "transaction",
        "status": 1,
        "client": {
            "name": "Тестовый Клиент",
            "phone": "+77001234567",
            "email": "test@example.com",
            "custom_fields": []
        },
        "services": [
            {
                "id": 445566,
                "title": "Тестовая услуга",
                "cost": 5000
            }
        ],
        "goods": [],
        "staff": {
            "id": 112233,
            "name": "Тестовый мастер",
            "position": "Специалист"
        },
        "company": {
            "id": 123456,
            "title": "Тестовая компания"
        },
        "datetime": "2025-07-20 16:05:00"
    }
}

async def test_webhook():
    """Тестирует webhook обработку"""
    webhook_url = "http://localhost:8001/webhook/altegio"
    
    print("🧪 Testing Altegio webhook processing...")
    print(f"📍 URL: {webhook_url}")
    print(f"📋 Test data: {json.dumps(test_webhook_data, ensure_ascii=False, indent=2)}")
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                webhook_url,
                json=test_webhook_data,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "Altegio-Webhook-Test"
                }
            )
            
            print(f"📤 Response status: {response.status_code}")
            print(f"📤 Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Success! Response: {json.dumps(result, ensure_ascii=False, indent=2)}")
                return True
            else:
                print(f"❌ Error response: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Request error: {e}")
        return False

async def test_health():
    """Тестирует health endpoint"""
    health_url = "http://localhost:8001/health"
    
    print("🔍 Testing health endpoint...")
    print(f"📍 URL: {health_url}")
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(health_url)
            
            print(f"📤 Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Health check: {json.dumps(result, ensure_ascii=False, indent=2)}")
                return True
            else:
                print(f"❌ Health check failed: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

async def main():
    print("=" * 60)
    print("🧪 DOCKER WEBHOOK SYSTEM TEST")
    print("=" * 60)
    
    # Тест 1: Health check
    print("\n🔍 Step 1: Health Check")
    health_ok = await test_health()
    
    if not health_ok:
        print("\n❌ Health check failed, cannot proceed with webhook test")
        return
    
    # Тест 2: Webhook processing
    print("\n📨 Step 2: Webhook Processing Test")
    webhook_ok = await test_webhook()
    
    print("\n" + "=" * 60)
    if health_ok and webhook_ok:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
