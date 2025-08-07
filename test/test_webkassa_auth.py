#!/usr/bin/env python3
"""
Простой тест для проверки обновления API ключа Webkassa
"""

import asyncio
import os
import json
import httpx
from datetime import datetime

async def test_webkassa_auth():
    """
    Тестирует получение нового токена от Webkassa
    """
    webkassa_login = "5837503@gmail.com"
    webkassa_password = "Amina2005@Webkassa"
    webkassa_auth_url = "https://api.webkassa.kz/api/Authorize"
    
    auth_data = {
        "Login": webkassa_login,
        "Password": webkassa_password
    }
    
    print(f"🔄 Testing Webkassa authentication...")
    print(f"📍 URL: {webkassa_auth_url}")
    print(f"👤 Login: {webkassa_login}")
    print(f"🔑 Password: {'*' * len(webkassa_password)}")
    print(f"📋 Request data: {json.dumps(auth_data, ensure_ascii=False, indent=2)}")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                webkassa_auth_url,
                json=auth_data,
                timeout=30,
                headers={
                    "Content-Type": "application/json"
                }
            )
            
            print(f"📤 Response status: {response.status_code}")
            print(f"📤 Response headers: {dict(response.headers)}")
            
            response.raise_for_status()
            
            result = response.json()
            print(f"✅ Success! Response: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            # Извлекаем данные
            if "Data" in result:
                data_section = result["Data"]
                if "Token" in data_section:
                    token = data_section["Token"]
                    print(f"🔑 Found token: {token[:20]}...{token[-10:] if len(token) > 30 else token[20:]}")
                if "UserId" in data_section:
                    user_id = data_section["UserId"]
                    print(f"👤 Found user_id: {user_id}")
            
            return result
            
    except httpx.HTTPStatusError as e:
        print(f"❌ HTTP error {e.response.status_code}: {e.response.text}")
        return None
    except httpx.RequestError as e:
        print(f"❌ Network error: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

async def test_webkassa_api_with_token(token: str):
    """
    Тестирует использование токена для проверки его валидности
    """
    webkassa_api_url = "https://api.webkassa.kz"
    cashbox_id = "SWK00499214"
    
    # Тестовый запрос - получение информации о кассе
    test_url = f"{webkassa_api_url}/api/CheckCashboxUniqueNumber"
    
    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": "WKD-68D0CA3C-191F-4DBB-B280-D483724EA7A9"
    }
    
    request_data = {
        "Token": token,
        "CashboxUniqueNumber": cashbox_id
    }
    
    print(f"\n🧪 Testing token with Webkassa API...")
    print(f"📍 URL: {test_url}")
    print(f"🔑 Token: {token[:20]}...{token[-10:] if len(token) > 30 else token[20:]}")
    print(f"📦 Cashbox: {cashbox_id}")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                test_url,
                json=request_data,
                headers=headers,
                timeout=30
            )
            
            print(f"📤 Response status: {response.status_code}")
            
            result = response.json()
            print(f"📤 Response: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            if "Errors" in result and result["Errors"]:
                print(f"⚠️ API returned errors: {result['Errors']}")
                return False
            else:
                print(f"✅ Token is valid!")
                return True
                
    except Exception as e:
        print(f"❌ Error testing token: {e}")
        return False

async def main():
    print("=" * 60)
    print("🧪 WEBKASSA API KEY TEST")
    print("=" * 60)
    
    # Шаг 1: Получаем новый токен
    auth_result = await test_webkassa_auth()
    
    if not auth_result:
        print("\n❌ Authentication failed, cannot proceed with token test")
        return
    
    # Шаг 2: Тестируем токен
    if "Data" in auth_result and "Token" in auth_result["Data"]:
        token = auth_result["Data"]["Token"]
        await test_webkassa_api_with_token(token)
    else:
        print("\n❌ No token found in response")
    
    print("\n" + "=" * 60)
    print("🏁 TEST COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
