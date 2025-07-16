"""
Маршруты для обработки webhook от Altegio
"""
import logging
import json
import os
import re
from datetime import datetime
from typing import Dict, Any, Optional, Union, List
import uuid

import httpx
from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db import get_db_session
from app.models import WebhookRecord, ApiKey
from app.schemas.altegio import AltegioWebhookPayload, WebhookResponse

router = APIRouter()
logger = logging.getLogger(__name__)


def decode_unicode_escapes(text: str) -> str:
    """
    Декодирует Unicode escape-последовательности в читаемый текст
    Например: "\\u0421\\u0440\\u043e\\u043a" -> "Срок"
    """
    try:
        # Заменяем двойные обратные слэши на одинарные
        text = text.replace('\\\\u', '\\u')
        
        # Декодируем unicode escape последовательности
        def decode_match(match):
            try:
                unicode_char = match.group(0)
                return unicode_char.encode().decode('unicode_escape')
            except:
                return match.group(0)
        
        # Ищем паттерны \uXXXX и декодируем их
        result = re.sub(r'\\u[0-9a-fA-F]{4}', decode_match, text)
        return result
    except Exception as e:
        logger.warning(f"Failed to decode unicode escapes in: {text[:100]}..., error: {e}")
        return text


def format_api_response(response_data: dict) -> str:
    """
    Форматирует ответ от API для логов с декодированием Unicode
    """
    try:
        # Преобразуем в JSON строку
        response_str = json.dumps(response_data, ensure_ascii=False, indent=2)
        
        # Декодируем Unicode escape-последовательности
        decoded_str = decode_unicode_escapes(response_str)
        
        return decoded_str
    except Exception as e:
        logger.warning(f"Failed to format API response: {e}")
        return str(response_data)


async def verify_webhook_signature(request: Request) -> bool:
    """
    Проверка подписи webhook от Altegio
    TODO: Реализовать проверку подписи/токена от Altegio
    """
    # Получаем заголовки для проверки подписи
    signature = request.headers.get("X-Altegio-Signature")
    token = request.headers.get("Authorization")
    
    # TODO: Добавить логику проверки подписи
    # if not signature or not verify_signature(signature, body, secret):
    #     return False
    
    logger.info(f"Webhook signature check - Signature: {signature}, Token: {token}")
    return True  # Временно пропускаем проверку


async def get_altegio_document(company_id: int, document_id: int) -> Dict[str, Any]:
    """
    Получает документ из Altegio API.
    """
    altegio_api_url = os.getenv("ALTEGIO_API_URL", "https://api.alteg.io/api/v1")
    altegio_auth_token = os.getenv("ALTEGIO_AUTH_TOKEN") # Bearer token
    altegio_user_id = os.getenv("ALTEGIO_USER_ID") # User ID

    if not altegio_auth_token or not altegio_user_id:
        logger.error("Altegio API credentials not configured in .env")
        raise HTTPException(status_code=500, detail="Altegio API credentials not configured")

    url = f"{altegio_api_url}/transactions/{company_id}/?document_id={document_id}"
    
    # Попробуем разные варианты заголовков
    header_variants = [
        {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {altegio_auth_token}, User {altegio_user_id}",
            "Accept": "application/vnd.api.v2+json"
        },
    ]

    logger.info(f"Making request to Altegio API: {url}")

    for i, headers in enumerate(header_variants):
        try:
            logger.info(f"Attempt {i+1}: Using headers: {[key for key in headers.keys() if key != 'Authorization']}")
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                logger.info(f"Success with header variant {i+1}")
                return response.json()
                
        except httpx.HTTPStatusError as e:
            logger.warning(f"Attempt {i+1} failed with status {e.response.status_code}: {e.response.text}")
            if i == len(header_variants) - 1:  # Последняя попытка
                logger.error(f"All header variants failed. Last error: {e.response.text}")
                raise HTTPException(status_code=e.response.status_code, detail=f"Altegio API error: {e.response.text}")
            continue
        except httpx.RequestError as e:
            logger.error(f"Altegio API request failed: {e}")
            raise HTTPException(status_code=500, detail=f"Altegio API request failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching Altegio document: {e}")
            raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")
    
    # Этот код не должен быть достигнут, но на всякий случай
    raise HTTPException(status_code=500, detail="Failed to authenticate with Altegio API")


async def refresh_webkassa_api_key(db: AsyncSession) -> Optional[ApiKey]:
    """
    Обновляет API ключ Webkassa, если он устарел или отсутствует.
    """
    logger.info("🔄 Attempting to refresh Webkassa API key...")
    
    try:
        # Запускаем скрипт обновления ключа
        import subprocess
        import sys
        
        logger.info("📞 Calling update script...")
        result = subprocess.run([
            sys.executable, "/app/scripts/update_webkassa_key.py"
        ], capture_output=True, text=True, cwd="/app")
        
        if result.returncode == 0:
            logger.info("✅ API key update script completed successfully")
            logger.info(f"📝 Script output: {result.stdout[-200:]}")  # Последние 200 символов
            
            # Получаем обновленный ключ из БД
            await db.commit()  # Обновляем сессию
            return await get_webkassa_api_key(db)
        else:
            logger.error(f"❌ API key update script failed with code {result.returncode}")
            logger.error(f"❌ Script error: {result.stderr}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error refreshing API key: {e}")
        return None


async def get_webkassa_api_key(db: AsyncSession) -> Optional[ApiKey]:
    """
    Получает API ключ Webkassa из базы данных с подробным логированием.
    """
    logger.info("🔍 Searching for Webkassa API key in database...")
    
    try:
        result = await db.execute(select(ApiKey).filter(ApiKey.service_name == "Webkassa"))
        api_key_obj = result.scalars().first()
        
        if api_key_obj:
            logger.info(f"✅ Found Webkassa API key in database:")
            logger.info(f"   🔑 Key ID: {api_key_obj.id}")
            logger.info(f"   🏷️ Service: {api_key_obj.service_name}")
            logger.info(f"   👤 User ID (token): {api_key_obj.user_id}")
            logger.info(f"   🗓️ Created: {api_key_obj.created_at}")
            logger.info(f"   🗓️ Updated: {api_key_obj.updated_at}")
            logger.info(f"   🔐 API Key (first 20 chars): {api_key_obj.api_key[:20]}...")
            logger.info(f"   🔐 API Key (last 20 chars): ...{api_key_obj.api_key[-20:]}")
            
            # Проверяем возраст ключа
            from datetime import datetime, timezone
            if api_key_obj.updated_at:
                age = datetime.now(timezone.utc) - api_key_obj.updated_at.replace(tzinfo=timezone.utc)
                logger.info(f"   ⏰ Key age: {age.total_seconds() / 3600:.1f} hours")
                
                if age.total_seconds() > 21600:  # 6 часов
                    logger.warning(f"⚠️ API key is older than 6 hours, might be expired!")
            
            return api_key_obj
        else:
            logger.error("❌ No Webkassa API key found in database!")
            
            # Проверяем все ключи в БД для отладки
            all_keys_result = await db.execute(select(ApiKey))
            all_keys = all_keys_result.scalars().all()
            
            if all_keys:
                logger.info(f"📋 Found {len(all_keys)} total API keys in database:")
                for key in all_keys:
                    logger.info(f"   - Service: {key.service_name}, ID: {key.id}")
            else:
                logger.error("❌ Database has no API keys at all!")
            
            return None
            
    except Exception as e:
        logger.error(f"❌ Error fetching Webkassa API key from database: {e}")
        return None


async def prepare_webkassa_data(payload: AltegioWebhookPayload, altegio_document: Dict[str, Any], db: AsyncSession, webkassa_token: str = None) -> Dict[str, Any]:
    """
    Преобразует данные из Altegio webhook и документа в формат, ожидаемый Webkassa.
    """
    # Получаем токен из базы данных, если не передан
    if not webkassa_token:
        api_key_record = await get_webkassa_api_key(db)
        if not api_key_record:
            raise ValueError("Webkassa API key not found in database")
        webkassa_token = api_key_record.user_id
        logger.info(f"🔑 Using webkassa token from database: {webkassa_token}")
    
    logger.info(f"🔄 Starting data transformation for Webkassa")
    logger.info(f"📥 Input webhook data: client_phone={payload.data.client.phone}, resource_id={payload.resource_id}")
    logger.info(f"📥 Input services count: {len(payload.data.services)}")
    logger.info(f"📥 Input altegio_document transactions count: {len(altegio_document.get('data', []))}")
    
    # Извлечение данных из Altegio webhook
    client_phone = payload.data.client.phone
    # resource_id = payload.resource_id
    services = payload.data.services
    goods = payload.data.goods_transactions

    # Извлечение данных из Altegio document
    # Предполагаем, что altegio_document['data'] содержит список транзакций
    transactions = altegio_document.get('data', [])

    positions = []
    payments = []

    logger.info(f"🛍️ Processing {len(services)} services from webhook:")

    total_sum_for_webkassa = 0

    # Обработка позиций (услуг) из webhook
    for i, service in enumerate(services):
        service_total = service.cost_per_unit * service.amount * (1 - service.discount / 100)  # Сумма с учетом скидки в процентах
        position = {
            "Count": service.amount,
            "Price": service.cost_per_unit ,#/ 100,  # Конвертация из копеек в тенге
            "PositionName": service.title,
            "Discount": service.discount * service.cost / 100,  # Скидка в тенге
            "Tax": "0",
            "TaxType": "0", 
            "TaxPercent": "0"
        }
        positions.append(position)
        total_sum_for_webkassa += service_total
        
        logger.info(f"  📦 Service {i+1}: {service.title}")
        logger.info(f"     💵 Cost: {service.cost_per_unit} тенге x {service.amount} = {(service.cost_per_unit * service.amount)} тенге")
        logger.info(f"     🎫 Discount: {service.discount}% = {service.discount * service.cost / 100} тенге")
        logger.info(f"     💰 Total: {service_total} тенге")

    for i, good in enumerate(goods):
        good_total = good.cost_per_unit * abs(good.amount) * (1 - good.discount / 100)  # Сумма с учетом скидки в процентах
        position = {
            "Count": abs(good.amount),
            "Price": service.cost_per_unit ,#/ 100,  # Конвертация из копеек в тенге
            "PositionName": good.title,
            "Discount": good.discount * good.cost / 100,  # Скидка в тенге
            "Tax": "0",
            "TaxType": "0", 
            "TaxPercent": "0"
        }
        positions.append(position)
        total_sum_for_webkassa += service_total
        
        logger.info(f"  📦 Service {i+1}: {good.title}")
        logger.info(f"     💵 Cost: {good.cost_per_unit} тенге x {abs(good.amount)} = {(good.cost_per_unit * abs(good.amount))} тенге")
        logger.info(f"     🎫 Discount: {good.discount}% = {good.discount * good.cost / 100} тенге")
        logger.info(f"     💰 Total: {good_total} тенге")



    logger.info(f"💳 Processing {len(transactions)} transactions from Altegio document:")
    # Обработка платежей из Altegio document
    # В данном примере, мы берем только транзакции с положительной суммой (поступления)
    # и маппим их на типы оплаты Webkassa
    for i, transaction in enumerate(transactions):
        if transaction.get('amount', 0) > 0:
            payment_type = 1 # По умолчанию банковская карта

            # account_title = transaction.get('account', {}).get('title', '').lower()
            # if 'kaspi' in account_title or 'каспи' in account_title:
            if transaction.get('account', {}).get('is_cash', True):
                payment_type = 1 # Kaspi обычно безналичный
            else:
                payment_type = 0 # Наличные
            # TODO: Добавить другие типы оплаты, если необходимо

            payment = {
                "Sum": transaction["amount"],
                "PaymentType": payment_type
            }
            payments.append(payment)
            
            payment_type_name = "Наличные" if payment_type == 0 else "Безналичный"
            logger.info(f"  💳 Payment {i+1}: {transaction['amount']} тенге ({payment_type_name})")
            logger.info(f"     🏦 Account: {transaction.get('account', {}).get('title', 'Unknown')}")

    # Если платежи не были найдены в документе, используем общую сумму из webhook
    if not payments:
        default_payment = {
            "Sum": total_sum_for_webkassa,
            "PaymentType": 1 # По умолчанию банковская карта
        }
        payments.append(default_payment)
        logger.warning(f"⚠️ No payments found in Altegio document, using default payment: {total_sum_for_webkassa} тенге (Безналичный)")

    webkassa_data = {
        "CashboxUniqueNumber": os.getenv("WEBKASSA_CASHBOX_ID"),
        "OperationType": 2,  # Продажа
        "Positions": positions,
        "TicketModifiers": [],
        "Payments": payments,   
        "Change": 0.0,
        "RoundType": 2,
        "ExternalCheckNumber": payload.data.id,#str(uuid.uuid4()),  # Генерируем уникальный ID для идемпотентности
        "CustomerPhone": client_phone
    }

    logger.info(f"✅ Data transformation completed: check number {webkassa_data['ExternalCheckNumber']}")
    logger.info(f"   📞 Customer phone: {client_phone}")
    logger.info(f"   📦 Positions count: {len(positions)}")
    logger.info(f"   💳 Payments count: {len(payments)}")
    logger.info(f"   💰 Total amount: {total_sum_for_webkassa} тенге")
    logger.info(f"   🔑 Token will be sent in Authorization header")
    
    return webkassa_data







async def send_to_webkassa_with_auto_refresh(db: AsyncSession, webkassa_data: dict) -> dict:
    """
    Отправляет данные в Webkassa API с автоматическим обновлением ключа при ошибке авторизации.
    """
    # Получаем API ключ
    api_key_record = await get_webkassa_api_key(db)

    if not api_key_record:
        error_message = "❌ No Webkassa API key found in database"
        logger.error(error_message)
        
        # Отправляем уведомление в Telegram
        await send_telegram_notification(
            "Отсутствует API ключ Webkassa",
            {
                "Ошибка": "API ключ не найден в базе данных",
                "Действие": "Попытка получения нового ключа"
            }
        )
        
        # Пытаемся обновить ключ
        logger.info("🔄 Attempting to get fresh API key...")
        refreshed_key = await refresh_webkassa_api_key(db)
        if refreshed_key:
            api_key_record = refreshed_key
            logger.info("✅ Successfully obtained fresh API key")
        else:
            final_error = "❌ Failed to obtain API key"
            logger.error(final_error)
            
            # Критическое уведомление в Telegram
            await send_telegram_notification(
                "КРИТИЧЕСКАЯ ОШИБКА: Невозможно получить API ключ Webkassa",
                {
                    "Проблема": "Не удалось получить API ключ из базы данных и обновить его",
                    "Влияние": "Фискализация чеков невозможна",
                    "Требуется": "Немедленное вмешательство администратора"
                }
            )
            
            return {"success": False, "error": "No API key found and unable to refresh"}
    
    api_token = api_key_record.api_key
    logger.info(f"🔑 Using API token from database (ID: {api_key_record.id})")
    logger.info(f"🔑 Token first 20 chars: {api_token[:20]}...")
    logger.info(f"🔑 Token last 20 chars: ...{api_token[-20:]}")
    
    # Первая попытка отправки
    result = await send_to_webkassa(webkassa_data, api_token)
    
    # Проверяем, нет ли ошибки авторизации
    if not result["success"] and "errors" in result:
        # Ищем ошибку истечения сессии (код 2)
        auth_error_found = False
        for error_msg in result["errors"]:
            if "Срок действия сессии истек" in error_msg or "Code 2:" in error_msg:
                auth_error_found = True
                break
        
        if auth_error_found:
            logger.warning("⚠️ Session expired error detected - attempting to refresh API key...")
            
            # Детальное логирование ошибки авторизации
            logger.error(f"🔍 Authorization error details:")
            logger.error(f"   📋 Error messages: {result.get('errors', [])}")
            logger.error(f"   📋 Raw response: {result.get('raw_response', {})}")
            logger.error(f"   🔑 Current token (first 20): {api_token[:20]}...")
            
            # Уведомление в Telegram об ошибке авторизации
            await send_telegram_notification(
                "Ошибка авторизации Webkassa - истек срок действия токена",
                {
                    "Тип ошибки": "Срок действия сессии истек (Code 2)",
                    "Текущий токен": f"{api_token[:20]}...{api_token[-10:]}",
                    "Ошибки API": "; ".join(result.get('errors', [])),
                    "Касса": os.getenv('WEBKASSA_CASHBOX_ID'),
                    "Данные запроса": json.dumps(webkassa_data, ensure_ascii=False, indent=2)[:400] + "..." if len(json.dumps(webkassa_data, ensure_ascii=False)) > 400 else json.dumps(webkassa_data, ensure_ascii=False, indent=2),
                    "Позиции": f"{len(webkassa_data.get('Positions', []))} шт.",
                    "Платежи": f"{len(webkassa_data.get('Payments', []))} шт.",
                    "Телефон клиента": webkassa_data.get('CustomerPhone', 'Не указан'),
                    "Номер чека": webkassa_data.get('ExternalCheckNumber', 'Не указан'),
                    "Действие": "Попытка обновления API ключа"
                }
            )
            
            # Пытаемся обновить ключ
            refreshed_key = await refresh_webkassa_api_key(db)
            
            if refreshed_key and refreshed_key.api_key != api_token:
                logger.info("✅ Successfully refreshed API key, retrying request...")
                logger.info(f"🔄 New token (first 20): {refreshed_key.api_key[:20]}...")
                
                # Повторяем запрос с новым ключом
                retry_result = await send_to_webkassa(webkassa_data, refreshed_key.api_key)
                if retry_result["success"]:
                    logger.info("✅ Request succeeded after key refresh")
                    
                    # Успешное уведомление
                    await send_telegram_notification(
                        "✅ Проблема с авторизацией Webkassa решена",
                        {
                            "Результат": "API ключ успешно обновлен",
                            "Новый токен": f"{refreshed_key.api_key[:20]}...{refreshed_key.api_key[-10:]}",
                            "Статус": "Запрос успешно выполнен после обновления ключа"
                        }
                    )
                else:
                    logger.error("❌ Request failed even after key refresh")
                    logger.error(f"🔍 Retry failure details: {retry_result}")
                    
                    # Критическое уведомление о неудаче после обновления
                    await send_telegram_notification(
                        "🚨 КРИТИЧЕСКАЯ ОШИБКА: Webkassa не работает даже после обновления токена",
                        {
                            "Проблема": "Запрос не прошел даже с новым API ключом",
                            "Новый токен": f"{refreshed_key.api_key[:20]}...{refreshed_key.api_key[-10:]}",
                            "Ошибки": "; ".join(retry_result.get('errors', [])),
                            "Требуется": "Немедленная проверка настроек Webkassa API"
                        }
                    )
                return retry_result
            else:
                logger.error("❌ Failed to refresh API key")
                logger.error(f"🔍 Refresh failure details: refreshed_key={refreshed_key}")
                
                # Критическое уведомление о неудаче обновления
                await send_telegram_notification(
                    "🚨 КРИТИЧЕСКАЯ ОШИБКА: Не удалось обновить API ключ Webkassa",
                    {
                        "Проблема": "Скрипт обновления API ключа не сработал",
                        "Текущий токен": f"{api_token[:20]}...{api_token[-10:]}",
                        "Статус обновления": "Неудача",
                        "Требуется": "Немедленная проверка системы обновления ключей"
                    }
                )
                return result
    
    
    # Проверяем, нет ли ошибки закрытия смены
    if not result["success"] and "errors" in result:
        # Ищем ошибку закрытия смены (код 11)
        shift_error_found = False
        for error_msg in result["errors"]:
            if "закрыть смену" in error_msg or "Code 11:" in error_msg:
                shift_error_found = True
                break
        
        if shift_error_found:
            logger.warning("⚠️ Shift close error detected - attempting to close shift...")
            
            # Детальное логирование ошибки смены
            logger.error(f"🔍 Shift close error details:")
            logger.error(f"   📋 Error messages: {result.get('errors', [])}")
            logger.error(f"   📋 Raw response: {result.get('raw_response', {})}")
            logger.error(f"   📦 Cashbox ID: {os.getenv('WEBKASSA_CASHBOX_ID')}")
            
            # Уведомление в Telegram об ошибке смены
            await send_telegram_notification(
                "Ошибка смены Webkassa - требуется закрытие смены",
                {
                    "Тип ошибки": "Необходимо закрыть смену (Code 11)",
                    "Касса": os.getenv('WEBKASSA_CASHBOX_ID'),
                    "Ошибки API": "; ".join(result.get('errors', [])),
                    "Данные запроса": json.dumps(webkassa_data, ensure_ascii=False, indent=2)[:400] + "..." if len(json.dumps(webkassa_data, ensure_ascii=False)) > 400 else json.dumps(webkassa_data, ensure_ascii=False, indent=2),
                    "Позиции": f"{len(webkassa_data.get('Positions', []))} шт.",
                    "Платежи": f"{len(webkassa_data.get('Payments', []))} шт.",
                    "Телефон клиента": webkassa_data.get('CustomerPhone', 'Не указан'),
                    "Номер чека": webkassa_data.get('ExternalCheckNumber', 'Не указан'),
                    "Токен": f"{api_token[:20]}...{api_token[-10:]}",
                    "Действие": "Попытка автоматического закрытия смены"
                }
            )
            
            # Пытаемся закрыть смену
            closed_shift = await close_webkassa_shift(db, api_token)
            
            if closed_shift["success"]:
                logger.info("✅ Successfully closed shift, retrying original request...")
                
                # Повторяем запрос после закрытия смены
                retry_result = await send_to_webkassa(webkassa_data, api_token)
                if retry_result["success"]:
                    logger.info("✅ Request succeeded after shift close")
                    
                    # Успешное уведомление
                    await send_telegram_notification(
                        "✅ Проблема со сменой Webkassa решена",
                        {
                            "Результат": "Смена успешно закрыта",
                            "Касса": os.getenv('WEBKASSA_CASHBOX_ID'),
                            "Статус": "Запрос успешно выполнен после закрытия смены"
                        }
                    )
                else:
                    logger.error("❌ Request failed even after shift close")
                    logger.error(f"🔍 Retry after shift close failure: {retry_result}")
                    
                    # Критическое уведомление о неудаче после закрытия смены
                    await send_telegram_notification(
                        "🚨 КРИТИЧЕСКАЯ ОШИБКА: Webkassa не работает даже после закрытия смены",
                        {
                            "Проблема": "Запрос не прошел даже после закрытия смены",
                            "Касса": os.getenv('WEBKASSA_CASHBOX_ID'),
                            "Ошибки": "; ".join(retry_result.get('errors', [])),
                            "Требуется": "Немедленная проверка состояния кассы"
                        }
                    )
                return retry_result
            else:
                logger.error("❌ Failed to close shift")
                logger.error(f"🔍 Shift close failure details: {closed_shift}")
                
                # Критическое уведомление о неудаче закрытия смены
                await send_telegram_notification(
                    "🚨 КРИТИЧЕСКАЯ ОШИБКА: Не удалось закрыть смену Webkassa",
                    {
                        "Проблема": "Автоматическое закрытие смены не сработало",
                        "Касса": os.getenv('WEBKASSA_CASHBOX_ID'),
                        "Ошибки закрытия": "; ".join(closed_shift.get('errors', [])),
                        "Требуется": "Ручное закрытие смены через веб-интерфейс Webkassa"
                    }
                )
                return result
    
    # Если дошли до сюда и запрос не успешен, логируем общую ошибку
    if not result["success"]:
        logger.error(f"🔍 General Webkassa error details:")
        logger.error(f"   📋 Success: {result.get('success')}")
        logger.error(f"   📋 Error: {result.get('error')}")
        logger.error(f"   📋 Errors: {result.get('errors', [])}")
        logger.error(f"   📋 Raw response: {result.get('raw_response', {})}")
        
        # Уведомление в Telegram о неопознанной ошибке
        await send_telegram_notification(
            "Неопознанная ошибка Webkassa API",
            {
                "Тип": "Общая ошибка API",
                "Ошибка": result.get('error', 'Unknown'),
                "Ошибки API": "; ".join(result.get('errors', [])),
                "Касса": os.getenv('WEBKASSA_CASHBOX_ID'),
                "Токен": f"{api_token[:20]}...{api_token[-10:]}",
                "Данные запроса": json.dumps(webkassa_data, ensure_ascii=False, indent=2)[:500] + "..." if len(json.dumps(webkassa_data, ensure_ascii=False)) > 500 else json.dumps(webkassa_data, ensure_ascii=False, indent=2),
                "Позиции": f"{len(webkassa_data.get('Positions', []))} шт.",
                "Платежи": f"{len(webkassa_data.get('Payments', []))} шт.",
                "Телефон клиента": webkassa_data.get('CustomerPhone', 'Не указан'),
                "Номер чека": webkassa_data.get('ExternalCheckNumber', 'Не указан'),
                "Требуется": "Проверка логов и состояния API"
            }
        )
    
    return result


async def send_to_webkassa(data: dict, api_token: str) -> dict:
    """
    Отправляет подготовленные данные в API Webkassa.
    """
    webkassa_api_url = os.getenv("WEBKASSA_API_URL", "https://api.webkassa.kz")
    
    # ОТЛАДКА: логируем переменную окружения
    logger.info(f"🔍 WEBKASSA_API_URL from env: '{webkassa_api_url}'")
    logger.info(f"🔍 All WEBKASSA env vars: {[k for k in os.environ.keys() if 'WEBKASSA' in k]}")
    
    # Формируем правильный URL для создания чека
    endpoint_url = f"{webkassa_api_url.rstrip('/')}/api/Check"
    
    # Правильные заголовки для Webkassa API
    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": "WKD-68D0CA3C-191F-4DBB-B280-D483724EA7A9"  # Фиксированный API ключ
    }
    
    # Добавляем Token в тело запроса
    request_data = {
        "Token": api_token,  # Токен идет в тело запроса
        **data  # Остальные данные
    }

    logger.info(f"🌐 Sending to Webkassa API: {endpoint_url}")
    logger.info(f"🔑 Using API token in body: {api_token[:20]}...")
    logger.info(f"📋 Request headers: {headers}")
    logger.info(f"📋 Request data: {json.dumps(request_data, ensure_ascii=False, indent=2)}")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(endpoint_url, json=request_data, headers=headers, timeout=30)
            response_data = response.json()
            
            # Логируем ответ с декодированием Unicode
            formatted_response = format_api_response(response_data)
            logger.info(f"📤 Webkassa API response received:")
            logger.info(f"🎯 Response: {formatted_response}")
            
            # Если есть ошибки в ответе, извлекаем и декодируем их
            if "Errors" in response_data and response_data["Errors"]:
                error_messages = []
                for error in response_data["Errors"]:
                    error_text = error.get("Text", "")
                    decoded_error = decode_unicode_escapes(error_text)
                    error_code = error.get("Code", "")
                    error_messages.append(f"Code {error_code}: {decoded_error}")
                
                logger.error(f"❌ Webkassa API errors: {'; '.join(error_messages)}")
                return {"success": False, "errors": error_messages, "raw_response": response_data}
            
            response.raise_for_status()
            return {"success": True, "data": response_data}
            
    except httpx.RequestError as e:
        logger.error(f"Webkassa API request failed: {e}")
        return {"success": False, "error": f"Network error: {e}"}
    except httpx.HTTPStatusError as e:
        error_text = e.response.text
        decoded_error = decode_unicode_escapes(error_text)
        logger.error(f"Webkassa API returned error status {e.response.status_code}: {decoded_error}")
        return {"success": False, "error": f"API error: {decoded_error}"}
    except Exception as e:
        logger.error(f"Unexpected error during Webkassa API call: {e}")
        return {"success": False, "error": f"Unexpected error: {e}"}


@router.post("/webhook", response_model=WebhookResponse)
async def handle_altegio_webhook(
    payload: Union[AltegioWebhookPayload, List[AltegioWebhookPayload]],
    request: Request,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Обработка webhook от Altegio
    Поддерживает как одиночные объекты, так и массивы webhook
    """
    try:
        # Логируем основную информацию о webhook для отладки (без полных данных)
        body = await request.body()
        body_size = len(body)
        
        # Логируем только размер и основную информацию, а не полные данные
        logger.info(f"🔍 Webhook data received: {body_size} bytes")
        
        # Логируем structured информацию о payload
        if isinstance(payload, list):
            logger.info(f"📦 Received webhook array with {len(payload)} items")
            for i, item in enumerate(payload[:3]):  # Показываем только первые 3 элемента
                logger.info(f"   📋 Item {i+1}: resource_id={item.resource_id}, company_id={item.company_id}, status={item.status}")
            if len(payload) > 3:
                logger.info(f"   ... и еще {len(payload) - 3} элементов")
        else:
            logger.info(f"📦 Received single webhook: resource_id={payload.resource_id}, company_id={payload.company_id}, status={payload.status}")
        
        # Нормализуем payload к массиву для единообразной обработки
        if isinstance(payload, list):
            webhook_list = payload
            logger.info(f"📦 Received webhook array with {len(webhook_list)} items")
        else:
            webhook_list = [payload]
            logger.info(f"📦 Received single webhook item, normalized to array")
        
        processed_records = []
        
        for single_payload in webhook_list:
            logger.info(f"Processing webhook: company_id={single_payload.company_id}, "
                       f"resource={single_payload.resource}, resource_id={single_payload.resource_id}, "
                       f"status={single_payload.status}")
            
            if not await verify_webhook_signature(request):
                logger.warning("Invalid webhook signature")
                raise HTTPException(status_code=401, detail="Invalid webhook signature")
            
            # Проверяем условия для обработки
            comment_text = single_payload.data.comment or ""
            has_fch = 'фч' in comment_text.lower() if comment_text else False
            
            conditions_met = (
                single_payload.resource == 'record' and 
                single_payload.data.comment and has_fch and 
                single_payload.data.paid_full == 1
            )
            
            logger.info(f"🔍 Checking processing conditions for webhook {single_payload.resource_id}:")
            logger.info(f"   📋 Resource: {single_payload.resource} (required: 'record') {'✅' if single_payload.resource == 'record' else '❌'}")
            logger.info(f"   💬 Comment: '{comment_text}' (must contain 'фч') {'✅' if has_fch else '❌'}")
            logger.info(f"   💬 Comment bytes: {comment_text.encode('utf-8') if comment_text else b''}")
            logger.info(f"   💬 Contains 'фч': {has_fch}")
            logger.info(f"   💰 Paid full: {single_payload.data.paid_full} (required: 1) {'✅' if single_payload.data.paid_full == 1 else '❌'}")
            logger.info(f"   🎯 Overall result: {'✅ PROCESSING' if conditions_met else '❌ SKIPPING'}")
            
            if not conditions_met:
                logger.info(f"Webhook {single_payload.resource_id} does not meet the required conditions for processing.")
                continue  # Пропускаем этот webhook, но продолжаем обработку остальных

            # Проверяем, не был ли уже обработан
            existing_record = await db.execute(
                select(WebhookRecord).filter(
                    WebhookRecord.resource_id == single_payload.resource_id,
                    WebhookRecord.company_id == single_payload.company_id,
                    WebhookRecord.processed == True
                )
            )
            if existing_record.scalars().first():
                logger.info(f"Webhook with resource_id {single_payload.resource_id} already processed.")
                continue  # Пропускаем уже обработанный webhook

            # Ищем существующую запись или создаем новую
            webhook_record = await db.execute(
                select(WebhookRecord).filter(
                    WebhookRecord.resource_id == single_payload.resource_id,
                    WebhookRecord.company_id == single_payload.company_id
                )
            )
            webhook_record = webhook_record.scalars().first()

            if webhook_record:
                # Обновляем существующую запись
                webhook_record.status = single_payload.status
                webhook_record.client_phone = single_payload.data.client.phone
                webhook_record.client_name = single_payload.data.client.name
                webhook_record.record_date = datetime.fromisoformat(single_payload.data.datetime.replace(" ", "T").split("+")[0])
                webhook_record.services_data = json.dumps([s.model_dump() for s in single_payload.data.services])
                webhook_record.comment = single_payload.data.comment
                webhook_record.raw_data = single_payload.model_dump()
                webhook_record.updated_at = datetime.utcnow()
                webhook_record.processed = False
                webhook_record.processing_error = None
                webhook_record.webkassa_status = None
                webhook_record.webkassa_response = None
                webhook_record.webkassa_request_id = None
            else:
                # Создаем новую запись
                webhook_record = WebhookRecord(
                    company_id=single_payload.company_id,
                    resource=single_payload.resource,
                    resource_id=single_payload.resource_id,
                    status=single_payload.status,
                    client_phone=single_payload.data.client.phone,
                    client_name=single_payload.data.client.name,
                    record_date=datetime.fromisoformat(single_payload.data.datetime.replace(" ", "T").split("+")[0]),
                    services_data=json.dumps([s.model_dump() for s in single_payload.data.services]),
                    comment=single_payload.data.comment,
                    raw_data=single_payload.model_dump()
                )
                db.add(webhook_record)
            
            await db.commit()
            await db.refresh(webhook_record)
            
            logger.info(f"Webhook saved/updated in database with ID: {webhook_record.id}")
            
            try:
                # Обработка фискализации
                altegio_document_id = None
                if single_payload.data.documents:
                    altegio_document_id = single_payload.data.documents[0].id
                
                if not altegio_document_id:
                    logger.warning(f"No document ID found in webhook for resource_id {single_payload.resource_id}")
                    webhook_record.processing_error = "No document ID found in webhook"
                    webhook_record.processed = False
                    await db.commit()
                    continue  # Пропускаем этот webhook

                # Попытка получить документ Altegio
                altegio_document = None
                try:
                    logger.info(f"Requesting Altegio document: company_id={single_payload.company_id}, document_id={altegio_document_id}")
                    altegio_document = await get_altegio_document(single_payload.company_id, altegio_document_id)
                    logger.info(f"✅ Successfully fetched Altegio document for resource_id {single_payload.resource_id}")
                    logger.info(f"📄 Altegio document content: {json.dumps(altegio_document, indent=2, ensure_ascii=False)}")
                except HTTPException as altegio_error:
                    logger.warning(f"❌ Failed to fetch Altegio document for resource_id {single_payload.resource_id}: {altegio_error.detail}")
                    # Продолжаем обработку без документа Altegio
                    altegio_document = {"data": []}

                fiscalization_data = await prepare_webkassa_data(single_payload, altegio_document, db)
                logger.info(f"💰 Prepared Webkassa fiscalization data:")
                logger.info(f"📋 Positions: {json.dumps(fiscalization_data.get('Positions', []), indent=2, ensure_ascii=False)}")
                logger.info(f"💳 Payments: {json.dumps(fiscalization_data.get('Payments', []), indent=2, ensure_ascii=False)}")
                logger.info(f"🧾 Full Webkassa request: {json.dumps(fiscalization_data, indent=2, ensure_ascii=False)}")

                webkassa_response = await send_to_webkassa_with_auto_refresh(db, fiscalization_data)
                
                is_success = webkassa_response.get("success", False)
                if is_success:
                    logger.info(f"✅ SUCCESS: Webkassa fiscalization completed")
                else:
                    logger.info(f"❌ FAILED: Webkassa fiscalization failed")
                    # Ошибки уже залогированы в send_to_webkassa с декодированием

                webhook_record.processed = True
                webhook_record.processed_at = datetime.utcnow()
                webhook_record.webkassa_status = "success" if webkassa_response.get("success") else "failed"
                webhook_record.webkassa_response = json.dumps(webkassa_response)
                webhook_record.webkassa_request_id = fiscalization_data.get("ExternalCheckNumber")
                await db.commit()
                
                processed_records.append(webhook_record.id)
                
            except Exception as e:
                logger.error(f"Error processing webhook {single_payload.resource_id}: {str(e)}", exc_info=True)
                webhook_record.processing_error = str(e)
                webhook_record.processed = False
                await db.commit()
                continue  # Продолжаем обработку других webhook
        
        if processed_records:
            return WebhookResponse(
                success=True,
                message=f"Successfully processed {len(processed_records)} webhook(s)",
                record_id=processed_records[0],
                record_ids=processed_records,
                processed_count=len(processed_records)
            )
        else:
            return WebhookResponse(
                success=True,
                message=f"Received {len(webhook_list)} webhook(s), but none met processing conditions",
                processed_count=0
            )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error processing webhook batch: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/webhook/status/{resource_id}", response_model=WebhookResponse)
async def get_webhook_status(
    resource_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Получение статуса обработки webhook по resource_id
    """
    try:
        webhook_record = await db.execute(
            select(WebhookRecord).filter(WebhookRecord.resource_id == resource_id)
        )
        webhook_record = webhook_record.scalars().first()

        if not webhook_record:
            raise HTTPException(status_code=404, detail="Webhook record not found")
        
        return WebhookResponse(
            success=webhook_record.processed,
            message=webhook_record.processing_error or "Processed successfully" if webhook_record.processed else "Pending processing",
            record_id=webhook_record.id
        )
        
    except Exception as e:
        logger.error(f"Error getting webhook status: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


async def close_webkassa_shift(db: AsyncSession, api_token: str) -> dict:
    """
    Закрывает смену в Webkassa через API.
    """
    # URL для закрытия смены
    shift_close_url = "https://devkkm.webkassa.kz/api/v4/ZReport"
    
    # Заголовки для запроса
    headers = {
        "Content-Type": "application/json",
        "x-api-key": "WKD-9BCE5F1E-AE33-4F39-BF8B-ABDBF2376398"  # API ключ для закрытия смены
    }
    
    # Данные для запроса
    request_data = {
        "Token": api_token,  # Токен авторизации
        "cashboxUniqueNumber": os.getenv("WEBKASSA_CASHBOX_ID")  # ID кассы
    }

    logger.info(f"🔄 Attempting to close Webkassa shift...")
    logger.info(f"🌐 Sending to: {shift_close_url}")
    logger.info(f"🔑 Using token: {api_token[:20]}...")
    logger.info(f"📦 Cashbox ID: {request_data['cashboxUniqueNumber']}")
    logger.info(f"📋 Request data: {json.dumps(request_data, ensure_ascii=False, indent=2)}")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(shift_close_url, json=request_data, headers=headers, timeout=30)
            response_data = response.json()
            
            # Логируем ответ с декодированием Unicode
            formatted_response = format_api_response(response_data)
            logger.info(f"📤 Webkassa shift close response received:")
            logger.info(f"🎯 Response: {formatted_response}")
            
            # Если есть ошибки в ответе, извлекаем и декодируем их
            if "Errors" in response_data and response_data["Errors"]:
                error_messages = []
                for error in response_data["Errors"]:
                    error_text = error.get("Text", "")
                    decoded_error = decode_unicode_escapes(error_text)
                    error_code = error.get("Code", "")
                    error_messages.append(f"Code {error_code}: {decoded_error}")
                
                logger.error(f"❌ Webkassa shift close errors: {'; '.join(error_messages)}")
                return {"success": False, "errors": error_messages, "raw_response": response_data}
            
            response.raise_for_status()
            logger.info("✅ Webkassa shift closed successfully")
            return {"success": True, "data": response_data}
            
    except httpx.RequestError as e:
        logger.error(f"Webkassa shift close request failed: {e}")
        return {"success": False, "error": f"Network error: {e}"}
    except httpx.HTTPStatusError as e:
        error_text = e.response.text
        decoded_error = decode_unicode_escapes(error_text)
        logger.error(f"Webkassa shift close returned error status {e.response.status_code}: {decoded_error}")
        return {"success": False, "error": f"API error: {decoded_error}"}
    except Exception as e:
        logger.error(f"Unexpected error during Webkassa shift close: {e}")
        return {"success": False, "error": f"Unexpected error: {e}"}


async def send_telegram_notification(message: str, error_details: dict = None) -> bool:
    """
    Отправляет уведомление в Telegram о критических ошибках
    """
    bot_token = "7922422379:AAEjk9PZuF8HgHNK3UoVDn-RIMXZhCfKewk"
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "-1002353046003")  # ID чата для уведомлений
    
    # Формируем сообщение
    telegram_message = f"🚨 ОШИБКА WEBKASSA\n\n"
    telegram_message += f"📅 Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    telegram_message += f"💬 Сообщение: {message}\n\n"
    
    if error_details:
        telegram_message += "📋 Детали ошибки:\n"
        for key, value in error_details.items():
            # Обрезаем длинные значения для читаемости
            if isinstance(value, str) and len(value) > 200:
                value = value[:200] + "..."
            telegram_message += f"• {key}: {value}\n"
    
    # Ограничиваем длину сообщения (Telegram лимит 4096 символов)
    if len(telegram_message) > 4000:
        telegram_message = telegram_message[:4000] + "\n\n[Сообщение обрезано]"
    
    try:
        telegram_api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        
        payload = {
            "chat_id": chat_id,
            "text": telegram_message,
            "parse_mode": "HTML"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(telegram_api_url, json=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info("✅ Telegram notification sent successfully")
                return True
            else:
                logger.error(f"❌ Failed to send Telegram notification: {response.status_code} - {response.text}")
                return False
                
    except Exception as e:
        logger.error(f"❌ Error sending Telegram notification: {e}")
        return False



