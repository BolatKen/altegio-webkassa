"""
Маршруты для обработки webhook от Altegio
"""
import logging
import json
import os
import re
import sys
import subprocess
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, Union, List, Tuple
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

# Константа для исключения платежей с комиссией эквайринга
ACQUIRING_COMMISSION_COMMENT = "Автоматически созданная операция списания комиссии за эквайринг."

def should_skip_transaction(transaction_comment: str) -> bool:
    """
    Проверяет, нужно ли пропустить транзакцию на основе комментария
    """
    return transaction_comment == ACQUIRING_COMMISSION_COMMENT

def get_client_data(client) -> Tuple[str, str]:
    """
    Безопасно извлекает телефон и имя клиента из разных форматов данных
    Returns: (client_phone, client_name)
    """
    client_phone = ""
    client_name = ""
    
    if client:
        if isinstance(client, dict):
            client_phone = client.get('phone', '')
            client_name = client.get('name', '')
        elif isinstance(client, list) and client:
            first_client = client[0]
            if isinstance(first_client, dict):
                client_phone = first_client.get('phone', '')
                client_name = first_client.get('name', '')
        elif hasattr(client, 'phone'):
            client_phone = client.phone
            client_name = client.name
    
    return client_phone, client_name

async def send_telegram_notification(message: str, error_details: dict = None) -> bool:
    """
    Отправляет уведомление в Telegram о критических ошибках
    """
    logger.info(f"📱 Telegram notification: {message}")
    if error_details:
        logger.info(f"📋 Error details: {error_details}")
    return True

async def close_webkassa_shift(db: AsyncSession, api_token: str, webhook_info: dict = None) -> dict:
    """
    Закрывает смену в Webkassa API
    """
    webkassa_api_url = os.getenv("WEBKASSA_API_URL", "https://api.webkassa.kz")
    endpoint_url = f"{webkassa_api_url.rstrip('/')}/api/ShiftClose"
    
    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": "WKD-68D0CA3C-191F-4DBB-B280-D483724EA7A9"
    }
    
    request_data = {
        "Token": api_token,
        "CashboxUniqueNumber": os.getenv("WEBKASSA_CASHBOX_ID")
    }
    
    logger.info(f"🔒 Attempting to close Webkassa shift at {endpoint_url}")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(endpoint_url, json=request_data, headers=headers, timeout=30)
            response_data = response.json()
            
            if "Errors" in response_data and response_data["Errors"]:
                error_messages = []
                for error in response_data["Errors"]:
                    error_text = error.get("Text", "")
                    error_code = error.get("Code", "")
                    error_messages.append(f"Code {error_code}: {error_text}")
                
                return {"success": False, "errors": error_messages, "raw_response": response_data}
            
            response.raise_for_status()
            return {"success": True, "data": response_data}
            
    except Exception as e:
        logger.error(f"❌ Error closing Webkassa shift: {e}")
        return {"success": False, "error": str(e)}

def ensure_queue_worker_running():
    """
    Запускает worker для обработки очереди webhook
    """
    logger.info("🔄 Ensuring queue worker is running")
    pass

# Очередь для обработки webhook - предотвращает параллельную обработку
webhook_processing_semaphore = asyncio.Semaphore(1)  # Только один webhook одновременно
webhook_processing_queue = asyncio.Queue()

class WebhookTask:
    def __init__(self, payload, request, db_session):
        self.payload = payload
        self.request = request
        self.db_session = db_session
        self.task_id = getattr(payload, "resource_id", None)

    async def run(self):
        return await process_webhook_internal(self.payload, self.request, self.db_session)


def decode_unicode_escapes(text: str) -> str:
    """
    Декодирует Unicode escape-последовательности в читаемый текст
    Например: "\\u0421\\u0440\\u043e\\u043a" -> "Срок"
    """
    try:
        # Заменяем двойные обратные слэшы на одинарные
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


async def get_altegio_sale_document(company_id: int, document_id: int) -> Dict[str, Any]:
    """
    Получает документ из Altegio API.
    """
    altegio_api_url = os.getenv("ALTEGIO_API_URL", "https://api.alteg.io/api/v1")
    altegio_auth_token = os.getenv("ALTEGIO_AUTH_TOKEN") # Bearer token
    altegio_user_id = os.getenv("ALTEGIO_USER_ID") # User ID

    if not altegio_auth_token or not altegio_user_id:
        logger.error("Altegio API credentials not configured in .env")
        raise HTTPException(status_code=500, detail="Altegio API credentials not configured")

    url = f"{altegio_api_url}/company/{company_id}/sale/{document_id}"
    
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
        
        # Проверяем существование скрипта
        script_path = "/app/scripts/update_webkassa_key.py"
        if not os.path.exists(script_path):
            logger.error(f"❌ Update script not found at {script_path}")
            return None
        
        result = subprocess.run([
            sys.executable, script_path
        ], capture_output=True, text=True, cwd="/app", timeout=60)  # Добавляем timeout
        
        logger.info(f"📝 Script return code: {result.returncode}")
        logger.info(f"📝 Script stdout: {result.stdout[-500:]}")  # Последние 500 символов
        if result.stderr:
            logger.warning(f"📝 Script stderr: {result.stderr[-500:]}")
        
        if result.returncode == 0:
            logger.info("✅ API key update script completed successfully")
            
            # Ждем немного чтобы изменения применились
            import asyncio
            await asyncio.sleep(1)
            
            # Обновляем сессию и получаем ключ
            await db.commit()
            # НЕ используем rollback() - это отменяет изменения!
            # Вместо этого создаем новый запрос для получения свежих данных
            
            return await get_webkassa_api_key(db)
        else:
            logger.error(f"❌ API key update script failed with code {result.returncode}")
            logger.error(f"❌ Script error: {result.stderr}")
            
            # Отправляем уведомление о неудаче скрипта
            await send_telegram_notification(
                "Ошибка выполнения скрипта обновления API ключа Webkassa",
                {
                    "Код ошибки": str(result.returncode),
                    "STDOUT": result.stdout[-300:] if result.stdout else "Пусто",
                    "STDERR": result.stderr[-300:] if result.stderr else "Пусто",
                    "Путь скрипта": script_path,
                    "Рабочая директория": "/app"
                }
            )
            
            return None
            
    except subprocess.TimeoutExpired:
        logger.error("❌ API key update script timed out after 60 seconds")
        await send_telegram_notification(
            "Таймаут скрипта обновления API ключа Webкassa",
            {
                "Проблема": "Скрипт не завершился за 60 секунд",
                "Требуется": "Проверка работы API Webkassa и сетевого соединения"
            }
        )
        return None
    except Exception as e:
        logger.error(f"❌ Error refreshing API key: {e}", exc_info=True)
        await send_telegram_notification(
            "Исключение при обновлении API ключа Webкassa",
            {
                "Ошибка": str(e),
                "Тип ошибки": type(e).__name__,
                "Требуется": "Проверка логов и состояния системы"
            }
        )
        return None


async def get_webkassa_api_key(db: AsyncSession) -> Optional[ApiKey]:
    """
    Получает API ключ Webкassa из базы данных с подробным логированием.
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
            logger.warning("⚠️ No Webkassa API key found, attempting to get fresh key...")
            
            # Пытаемся получить новый ключ
            refreshed_key = await refresh_webkassa_api_key(db)
            if refreshed_key:
                api_key_record = refreshed_key
                logger.info("✅ Successfully obtained fresh API key for data preparation")
            else:
                error_msg = "Webkassa API key not found in database and unable to refresh"
                logger.error(f"❌ {error_msg}")
                
                # Отправляем уведомление в Telegram о критической ошибке
                client_phone, client_name = get_client_data(payload.data.client)
                await send_telegram_notification(
                    "КРИТИЧЕСКАЯ ОШИБКА: Невозможно получить API ключ Webкassa для обработки данных",
                    {
                        "Проблема": "API ключ не найден в базе данных и не удалось получить новый",
                        "Webhook ID": str(payload.resource_id),
                        "Company ID": str(payload.company_id),
                        "Клиент": client_name if client_name else "Неизвестен",
                        "Телефон": client_phone if client_phone else "Неизвестен",
                        "Влияние": "Обработка webhook остановлена",
                        "Требуется": "Проверка настроек Webkassa API и перезапуск скрипта обновления ключей"
                    }
                )
                
                raise ValueError(error_msg)
        
        webkassa_token = api_key_record.api_key
        logger.info(f"🔑 Using webkassa token from database: {webkassa_token}")
    
    logger.info(f"🔄 Starting data transformation for Webkassa")
    client_phone, client_name = get_client_data(payload.data.client)
    
    logger.info(f"📥 Input webhook data: client_phone={client_phone}, resource_id={payload.resource_id}")
    logger.info(f"📥 Input services count: {len(payload.data.services)}")
    logger.info(f"📥 Input altegio_document type: {type(altegio_document)}")
    if isinstance(altegio_document, dict):
        logger.info(f"📥 Input altegio_document transactions count: {len(altegio_document.get('data', []))}")
    elif isinstance(altegio_document, list):
        logger.info(f"📥 Input altegio_document transactions count: {len(altegio_document)}")
    else:
        logger.info(f"📥 Input altegio_document has unknown format: {altegio_document}")

    # Извлечение данных из Altegio webhook
    # resource_id = payload.resource_id
    services = payload.data.services
    goods = payload.data.goods_transactions

    # Извлечение данных из Altegio document
    # Поддерживаем два формата: обычный транзакции и goods sale document
    transactions = []
    
    # Проверяем тип и формат документа
    if isinstance(altegio_document, dict):
        # Проверяем, есть ли структура goods sale document
        if altegio_document.get('data', {}) and isinstance(altegio_document.get('data', {}), dict) and altegio_document.get('data', {}).get('state'):
            # Новый формат для goods_operations_sale
            logger.info(f"📦 Processing goods sale document format")
            sale_transactions = altegio_document.get('data', {}).get('state', {}).get('payment_transactions', [])
            transactions = sale_transactions
            logger.info(f"📥 Found {len(transactions)} payment transactions in goods sale document")
        else:
            # Словарь, но стандартный формат
            logger.info(f"📋 Processing standard transactions document format (dict)")
            transactions = altegio_document.get('data', [])
            logger.info(f"📥 Found {len(transactions)} transactions in standard document (dict)")
    elif isinstance(altegio_document, list):
        # Список транзакций
        logger.info(f"📋 Processing standard transactions document format (list)")
        transactions = altegio_document
        logger.info(f"📥 Found {len(transactions)} transactions in standard document (list)")
    else:
        # Неизвестный формат документа
        logger.warning(f"Unknown altegio_document format: {type(altegio_document)}")
        transactions = []
        logger.info(f"📥 Found {len(transactions)} transactions (unknown format)")

    positions = []
    payments = []

    logger.info(f"🛍️ Processing {len(services)} services from webhook:")

    total_sum_for_webkassa = 0

    # Обработка позиций (услуг) из webhook
    for i, service in enumerate(services):
        # Используем оригинальную цену и рассчитываем скидку отдельно
        original_price_per_unit = service.cost_per_unit
        discount_amount = (service.cost_per_unit * service.amount) - service.cost_to_pay
        service_total = service.cost_to_pay  # Используем реальную сумму к оплате
        
        position = {
            "Count": service.amount,
            "Price": original_price_per_unit,  # Оригинальная цена за единицу
            "PositionName": service.title,
            "Discount": discount_amount,  # Скидка в тенге
            "Tax": "0",
            "TaxType": "0", 
            "TaxPercent": "0"
        }
        positions.append(position)
        total_sum_for_webkassa += service_total
        
        logger.info(f"  📦 Service {i+1}: {service.title}")
        logger.info(f"     💵 Original cost: {service.cost_per_unit} тенге x {service.amount} = {(service.cost_per_unit * service.amount)} тенге")
        logger.info(f"     🎫 Discount: {service.discount}% = {(service.cost_per_unit * service.amount) - service.cost_to_pay} тенге")
        logger.info(f"     💰 Final price per unit: {final_price_per_unit} тенге")
        logger.info(f"     💰 Total to pay: {service_total} тенге")

    # Обработка товаров из webhook (goods_transactions)
    for i, good in enumerate(goods):
        # Используем оригинальную цену и рассчитываем скидку отдельно
        original_price_per_unit = good["cost_per_unit"]
        original_total = original_price_per_unit * abs(good["amount"])
        good_total = good.get("cost_to_pay", original_total * (1 - good["discount"] / 100))
        discount_amount = original_total - good_total
        
        position = {
            "Count": abs(good["amount"]),
            "Price": original_price_per_unit,  # Оригинальная цена за единицу
            "PositionName": good["title"],
            "Discount": discount_amount,  # Скидка в тенге
            "Tax": "0",
            "TaxType": "0", 
            "TaxPercent": "0"
        }
        positions.append(position)
        total_sum_for_webkassa += good_total
        
        logger.info(f"  📦 Good {i+1}: {good['title']}")
        logger.info(f"     💵 Original cost: {original_price_per_unit} тенге x {abs(good['amount'])} = {original_total} тенге")
        logger.info(f"     🎫 Discount: {good['discount']}% = {discount_amount} тенге")
        logger.info(f"     💰 Total to pay: {good_total} тенге")

    # Обработка платежей из transactions (уже извлеченных выше)
    logger.info(f"💳 Processing {len(transactions)} transactions from Altegio document:")
    
    # Обработка платежей из Altegio document (стандартный формат)
    for i, transaction in enumerate(transactions):
        amount = transaction.get('amount', 0)
        transaction_comment = transaction.get('comment', '')
        
        # Проверяем комментарий для исключения комиссии эквайринга
        if should_skip_transaction(transaction_comment):
            logger.info(f"  🚫 Skipping transaction {i+1}: acquiring commission fee (amount: {amount}, comment: '{transaction_comment}')")
            continue
            
        if amount > 0:
            account_info = transaction.get('account', {})
            is_cash = account_info.get('is_cash', True)
            account_title = account_info.get('title', 'Unknown')
            
            # Определяем тип платежа на основе is_cash
            payment_type = 0 if is_cash else 1  # 0 = наличные, 1 = безналичный

            payment = {
                "Sum": amount,
                "PaymentType": payment_type
            }
            payments.append(payment)
            
            payment_type_name = "Наличные" if payment_type == 0 else "Безналичный"
            logger.info(f"  💳 Payment {i+1}: {amount} тенге ({payment_type_name})")
            logger.info(f"     🏦 Account: {account_title}")
            if transaction_comment:
                logger.info(f"     💬 Comment: {transaction_comment}")

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



async def prepare_webkassa_data_for_goods_sale(payload: AltegioWebhookPayload, altegio_document: Dict[str, Any], db: AsyncSession, webkassa_token: str = None) -> Dict[str, Any]:
    """
    Преобразует данные из Altegio goods_operations_sale webhook в формат, ожидаемый Webкassa.
    Специальная обработка для продаж товаров - данные берутся из документа продажи.
    """
    # Получаем токен из базы данных, если не передан
    if not webkassa_token:
        api_key_record = await get_webkassa_api_key(db)
        if not api_key_record:
            logger.warning("⚠️ No Webkassa API key found, attempting to get fresh key...")
            
            # Пытаемся получить новый ключ
            refreshed_key = await refresh_webkassa_api_key(db)
            if refreshed_key:
                api_key_record = refreshed_key
                logger.info("✅ Successfully obtained fresh API key for goods sale data preparation")
            else:
                error_msg = "Webkassa API key not found in database and unable to refresh"
                logger.error(f"❌ {error_msg}")
                
                # Отправляем уведомление в Telegram о критической ошибке
                await send_telegram_notification(
                    "КРИТИЧЕСКАЯ ОШИБКА: Невозможно получить API ключ Webкassa для обработки продажи товаров",
                    {
                        "Проблема": "API ключ не найден в базе данных и не удалось получить новый",
                        "Webhook ID": str(payload.resource_id),
                        "Company ID": str(payload.company_id),
                        "Тип": "goods_operations_sale",
                        "Влияние": "Обработка webhook остановлена",
                        "Требуется": "Проверка настроек Webkassa API и перезапуск скрипта обновления ключей"
                    }
                )
                
                raise ValueError(error_msg)
        
        webkassa_token = api_key_record.api_key
        logger.info(f"🔑 Using webkassa token from database: {webkassa_token}")
    
    logger.info(f"🛒 Starting goods sale data transformation for Webkassa")
    client_phone, client_name = get_client_data(payload.data.client)
    logger.info(f"📥 Input goods sale webhook data: client_phone={client_phone}, resource_id={payload.resource_id}")
    
    positions = []
    payments = []
    total_sum_for_webkassa = 0

    # Обработка товаров из документа продажи
    if isinstance(altegio_document, dict) and altegio_document.get('data', {}).get('state', {}).get('items'):
        sale_items = altegio_document.get('data', {}).get('state', {}).get('items', [])
        logger.info(f"🛒 Processing {len(sale_items)} items from goods sale document:")
        
        for i, item in enumerate(sale_items):
            # Извлекаем данные из формата goods sale document
            item_count = abs(item.get('amount', 1))  # Используем абсолютное значение
            item_price = item.get('default_cost_per_unit', 0)
            item_discount_percent = item.get('client_discount_percent', 0)
            item_total = item.get('cost_to_pay_total', 0)
            
            position = {
                "Count": item_count,
                "Price": item_price,
                "PositionName": item.get('title', 'Unknown Item'),
                "Discount": (item_price * item_count) - item_total,  # Рассчитываем скидку в тенге
                "Tax": "0",
                "TaxType": "0", 
                "TaxPercent": "0"
            }
            positions.append(position)
            total_sum_for_webkassa += item_total
            
            logger.info(f"  🛒 Sale Item {i+1}: {item.get('title', 'Unknown')}")
            logger.info(f"     💵 Price: {item_price} тенге x {item_count} = {item_price * item_count} тенге")
            logger.info(f"     🎫 Discount: {item_discount_percent}% = {(item_price * item_count) - item_total} тенге")
            logger.info(f"     💰 Total to pay: {item_total} тенге")

    # Обработка платежей из документа продажи
    if isinstance(altegio_document, dict) and altegio_document.get('data', {}).get('state', {}).get('payment_transactions'):
        sale_transactions = altegio_document.get('data', {}).get('state', {}).get('payment_transactions', [])
        logger.info(f"💳 Processing {len(sale_transactions)} payment transactions from goods sale document:")
        
        for i, transaction in enumerate(sale_transactions):
            amount = transaction.get('amount', 0)
            transaction_comment = transaction.get('comment', '')
            
            # Проверяем комментарий для исключения комиссии эквайринга
            if should_skip_transaction(transaction_comment):
                logger.info(f"  🚫 Skipping payment transaction {i+1}: acquiring commission fee (amount: {amount}, comment: '{transaction_comment}')")
                continue
                
            if amount > 0:
                account_info = transaction.get('account', {})
                is_cash = account_info.get('is_cash', True)
                account_title = account_info.get('title', 'Unknown')
                
                # Определяем тип платежа на основе is_cash
                payment_type = 0 if is_cash else 1  # 0 = наличные, 1 = безналичный

                payment = {
                    "Sum": amount,
                    "PaymentType": payment_type
                }
                payments.append(payment)
                
                payment_type_name = "Наличные" if payment_type == 0 else "Безналичный"
                logger.info(f"  💳 Payment {i+1}: {amount} тенге ({payment_type_name})")
                logger.info(f"     🏦 Account: {account_title}")
                if transaction_comment:
                    logger.info(f"     💬 Comment: {transaction_comment}")

    # Если платежи не были найдены в документе, используем общую сумму
    if not payments:
        default_payment = {
            "Sum": total_sum_for_webkassa,
            "PaymentType": 1  # По умолчанию безналичный
        }
        payments.append(default_payment)
        logger.warning(f"⚠️ No payments found in goods sale document, using default payment: {total_sum_for_webkassa} тенге (Безналичный)")

    webkassa_data = {
        "CashboxUniqueNumber": os.getenv("WEBKASSA_CASHBOX_ID"),
        "OperationType": 2,  # Продажа
        "Positions": positions,
        "TicketModifiers": [],
        "Payments": payments,   
        "Change": 0.0,
        "RoundType": 2,
        "ExternalCheckNumber": payload.data.id,
        "CustomerPhone": client_phone
    }

    logger.info(f"✅ Goods sale data transformation completed: check number {webkassa_data['ExternalCheckNumber']}")
    logger.info(f"   📞 Customer phone: {client_phone}")
    logger.info(f"   📦 Positions count: {len(positions)}")
    logger.info(f"   💳 Payments count: {len(payments)}")
    logger.info(f"   💰 Total amount: {total_sum_for_webkassa} тенге")
    logger.info(f"   🔑 Token will be sent in Authorization header")
    
    return webkassa_data



async def send_to_webkassa_with_auto_refresh(db: AsyncSession, webkassa_data: dict, webhook_info: dict = None) -> dict:
    """
    Отправляет данные в Webkassa API с автоматическим обновлением ключа при ошибке авторизации.
    
    Args:
        db: сессия базы данных
        webkassa_data: данные для отправки в Webkassa
        webhook_info: информация о webhook для улучшенного логирования
    """
    # Получаем API ключ
    api_key_record = await get_webkassa_api_key(db)

    if not api_key_record:
        error_message = "❌ No Webkassa API key found in database"
        logger.error(error_message)
        
        # Отправляем уведомление в Telegram
        await send_telegram_notification(
            "Отсутствует API ключ Webкassa",
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
                "КРИТИЧЕСКАЯ ОШИБКА: Невозможно получить API ключ Webкassa",
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
    result = await send_to_webkassa(webkassa_data, api_token, webhook_info)
    
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
                "Ошибка авторизации Webкassa - истек срок действия токена",
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
            
            if refreshed_key:
                logger.info("✅ Successfully refreshed API key, retrying request...")
                logger.info(f"🔄 Using token (first 20): {refreshed_key.api_key[:20]}...")
                logger.info(f"🔄 Using token (last 20): ...{refreshed_key.api_key[-20:]}")
                logger.info(f"🔄 Old token was: {api_token[:20]}...{api_token[-20:]}")
                logger.info(f"🔄 Token changed: {refreshed_key.api_key != api_token}")
                
                # Повторяем запрос с обновленным ключом (может быть тот же самый)
                retry_result = await send_to_webkassa(webkassa_data, refreshed_key.api_key, webhook_info)
                if retry_result["success"]:
                    logger.info("✅ Request succeeded after key refresh")
                    
                    # Успешное уведомление
                    token_changed = refreshed_key.api_key != api_token
                    status_message = "API ключ успешно обновлен" if token_changed else "API ключ актуален, повторный запрос успешен"
                    
                    await send_telegram_notification(
                        "✅ Проблема с авторизацией Webкassa решена",
                        {
                            "Результат": status_message,
                            "Токен": f"{refreshed_key.api_key[:20]}...{refreshed_key.api_key[-10:]}",
                            "Изменился": "Да" if token_changed else "Нет",
                            "Статус": "Запрос успешно выполнен после обновления ключа"
                        }
                    )
                else:
                    logger.error("❌ Request failed even after key refresh")
                    logger.error(f"🔍 Retry failure details: {retry_result}")
                    
                    # Критическое уведомление о неудаче после обновления
                    await send_telegram_notification(
                        "🚨 КРИТИЧЕСКАЯ ОШИБКА: Webкassa не работает даже после обновления токена",
                        {
                            "Проблема": "Запрос не прошел даже с обновленным API ключом",
                            "Токен": f"{refreshed_key.api_key[:20]}...{refreshed_key.api_key[-10:]}",
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
                    "🚨 КРИТИЧЕСКАЯ ОШИБКА: Не удалось обновить API ключ Webкassa",
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
                "Ошибка смены Webкassa - требуется закрытие смены",
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
            closed_shift = await close_webkassa_shift(db, api_token, webhook_info)
            
            if closed_shift["success"]:
                logger.info("✅ Successfully closed shift, retrying original request...")
                
                # Повторяем запрос после закрытия смены
                retry_result = await send_to_webkassa(webkassa_data, api_token, webhook_info)
                if retry_result["success"]:
                    logger.info("✅ Request succeeded after shift close")
                    
                    # Успешное уведомление
                    await send_telegram_notification(
                        "✅ Проблема со сменой Webкassa решена",
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
                        "🚨 КРИТИЧЕСКАЯ ОШИБКА: Webкassa не работает даже после закрытия смены",
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
                    "🚨 КРИТИЧЕСКАЯ ОШИБКА: Не удалось закрыть смену Webкassa",
                    {
                        "Проблема": "Автоматическое закрытие смены не сработало",
                        "Касса": os.getenv('WEBKASSA_CASHBOX_ID'),
                        "Ошибки закрытия": "; ".join(closed_shift.get('errors', [])),
                        "Требуется": "Ручное закрытие смены через веб-интерфейс Webкassa"
                    }
                )
                return result
    
    # Если дошли до сюда и запрос не успешен, логируем общую ошибку
    if not result["success"]:
        logger.error(f"🔍 General Webкassa error details:")
        logger.error(f"   📋 Success: {result.get('success')}")
        logger.error(f"   📋 Error: {result.get('error')}")
        logger.error(f"   📋 Errors: {result.get('errors', [])}")
        logger.error(f"   📋 Raw response: {result.get('raw_response', {})}")
        
        # Уведомление в Telegram о неопознанной ошибке
        await send_telegram_notification(
            "Неопознанная ошибка Webкassa API",
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


async def send_to_webkassa(data: dict, api_token: str, webhook_info: dict = None) -> dict:
    """
    Отправляет подготовленные данные в API Webkassa.
    
    Args:
        data: данные для отправки в Webkassa
        api_token: API токен
        webhook_info: дополнительная информация о webhook для логирования ошибок
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
                
                # Формируем детальное сообщение об ошибке с информацией о webhook
                error_log_message = f"❌ Webkassa API errors: {'; '.join(error_messages)}"
                if webhook_info:
                    error_log_message += f" | Webhook Details: resource_id={webhook_info.get('resource_id')}, company_id={webhook_info.get('company_id')}, client={webhook_info.get('client_name', 'Unknown')}, phone={webhook_info.get('client_phone', 'Unknown')}, comment='{webhook_info.get('comment', '')}'"
                    # Также логируем полный webhook для детального анализа
                    logger.error(f"🔍 Full webhook data for error analysis: {json.dumps(webhook_info.get('full_webhook', {}), ensure_ascii=False, indent=2)}")
                
                logger.error(error_log_message)
                return {"success": False, "errors": error_messages, "raw_response": response_data}
            
            response.raise_for_status()
            return {"success": True, "data": response_data}
            
    except httpx.RequestError as e:
        error_message = f"Webkassa API request failed: {e}"
        if webhook_info:
            error_message += f" | Webhook Details: resource_id={webhook_info.get('resource_id')}, company_id={webhook_info.get('company_id')}, client={webhook_info.get('client_name', 'Unknown')}, phone={webhook_info.get('client_phone', 'Unknown')}"
            logger.error(f"🔍 Full webhook data for network error: {json.dumps(webhook_info.get('full_webhook', {}), ensure_ascii=False, indent=2)}")
        logger.error(error_message)
        return {"success": False, "error": f"Network error: {e}"}
    except httpx.HTTPStatusError as e:
        error_text = e.response.text
        decoded_error = decode_unicode_escapes(error_text)
        error_message = f"Webkassa API returned error status {e.response.status_code}: {decoded_error}"
        if webhook_info:
            error_message += f" | Webhook Details: resource_id={webhook_info.get('resource_id')}, company_id={webhook_info.get('company_id')}, client={webhook_info.get('client_name', 'Unknown')}, phone={webhook_info.get('client_phone', 'Unknown')}"
            logger.error(f"🔍 Full webhook data for HTTP error: {json.dumps(webhook_info.get('full_webhook', {}), ensure_ascii=False, indent=2)}")
        logger.error(error_message)
        return {"success": False, "error": f"API error: {decoded_error}"}
    except Exception as e:
        error_message = f"Unexpected error during Webkassa API call: {e}"
        if webhook_info:
            error_message += f" | Webhook Details: resource_id={webhook_info.get('resource_id')}, company_id={webhook_info.get('company_id')}, client={webhook_info.get('client_name', 'Unknown')}, phone={webhook_info.get('client_phone', 'Unknown')}"
            logger.error(f"🔍 Full webhook data for unexpected error: {json.dumps(webhook_info.get('full_webhook', {}), ensure_ascii=False, indent=2)}")
        logger.error(error_message)
        return {"success": False, "error": f"Unexpected error: {e}"}


@router.post("/webhook", response_model=WebhookResponse)
async def handle_altegio_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Обработка webhook от Altegio с универсальной обработкой ошибок валидации
    """
    try:
        # Получаем сырые данные
        body = await request.body()
        body_text = body.decode('utf-8') if body else ""
        
        logger.info(f"🎯 Received webhook data: {body_text[:500]}...")
        
        # Пытаемся распарсить JSON
        try:
            raw_data = json.loads(body_text) if body_text else {}
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON received: {e}")
            return WebhookResponse(
                success=False,
                message="Invalid JSON format",
                processed_count=0
            )
        
        # Пытаемся валидировать с помощью Pydantic
        try:
            # Проверяем, является ли это списком или одиночным webhook
            if isinstance(raw_data, list):
                # Пытаемся валидировать каждый элемент списка
                webhook_list = []
                for item in raw_data:
                    try:
                        payload = AltegioWebhookPayload(**item)
                        webhook_list.append(payload)
                    except Exception as validation_error:
                        logger.warning(f"⚠️ Failed to validate webhook item, skipping: {validation_error}")
                        continue
            else:
                # Одиночный webhook
                payload = AltegioWebhookPayload(**raw_data)
                webhook_list = [payload]
                
        except Exception as validation_error:
            logger.warning(f"⚠️ Pydantic validation failed, trying flexible parsing: {validation_error}")
            
            # Создаем webhook с минимально необходимыми полями
            try:
                if isinstance(raw_data, list):
                    webhook_list = []
                    for item in raw_data:
                        flexible_webhook = create_flexible_webhook(item)
                        if flexible_webhook:
                            webhook_list.append(flexible_webhook)
                else:
                    flexible_webhook = create_flexible_webhook(raw_data)
                    webhook_list = [flexible_webhook] if flexible_webhook else []
                    
                if not webhook_list:
                    logger.error(f"❌ Could not parse webhook data: {validation_error}")
                    return WebhookResponse(
                        success=False,
                        message=f"Webhook validation failed: {str(validation_error)}",
                        processed_count=0
                    )
                    
            except Exception as e:
                logger.error(f"❌ Flexible parsing also failed: {e}")
                return WebhookResponse(
                    success=False,
                    message=f"Complete parsing failed: {str(e)}",
                    processed_count=0
                )
        
        # Запускаем worker если он не запущен
        # ensure_queue_worker_running()
        
        logger.info(f"🎯 Successfully parsed {len(webhook_list)} webhook(s), adding to processing queue")
        
        # Создаем задачи для каждого webhook и добавляем в очередь
        tasks = []
        results = []
        for single_payload in webhook_list:
            task = WebhookTask(single_payload, request, db)
            tasks.append(task)
            result = await task.run()
            logger.info(f"📤 Webhook {task.task_id} processed immediately")
            results.append(result)
        
        # ...existing code...
        
        # Объединяем результаты
        total_success = sum(1 for r in results if r.get("success", False))
        total_processed = sum(r.get("processed_count", 0) for r in results)
        
        if total_success > 0:
            return WebhookResponse(
                success=True,
                message=f"Successfully processed {total_success} of {len(webhook_list)} webhook(s) via queue",
                processed_count=total_processed
            )
        else:
            return WebhookResponse(
                success=False,
                message=f"Failed to process {len(webhook_list)} webhook(s)",
                processed_count=0
            )
            
    except Exception as e:
        logger.error(f"❌ Critical error in webhook handler: {e}", exc_info=True)
        return WebhookResponse(
            success=False,
            message=f"Critical error: {str(e)}",
            processed_count=0
        )


def create_flexible_webhook(raw_data: dict) -> Optional[AltegioWebhookPayload]:
    """
    Создает webhook с гибкой обработкой данных, заменяя недостающие поля значениями по умолчанию
    """
    try:
        # Обязательные поля
        if not all(key in raw_data for key in ['company_id', 'resource', 'resource_id', 'status']):
            logger.error(f"❌ Missing required fields in webhook data: {raw_data.keys()}")
            return None
        
        # Создаем базовую структуру данных с безопасными значениями по умолчанию
        safe_data = raw_data.get('data', {})
        
        # Убеждаемся, что у нас есть ID
        if 'id' not in safe_data:
            safe_data['id'] = raw_data.get('resource_id', 0)

        # Исправляем поле prepaid, если оно невалидное
        if 'prepaid' in safe_data:
            val = safe_data['prepaid']
            # Если это строка и не похоже на bool, ставим False
            if isinstance(val, str) and val not in ['true', 'false', '1', '0', 'True', 'False']:
                safe_data['prepaid'] = False
            # Если это не bool и не int, тоже ставим False
            elif not isinstance(val, (bool, int)):
                safe_data['prepaid'] = False

        # Безопасно обрабатываем custom_fields
        if 'custom_fields' in safe_data:
            if isinstance(safe_data['custom_fields'], dict):
                # Если это объект, оставляем как есть
                pass
            elif not isinstance(safe_data['custom_fields'], list):
                # Если это не список и не объект, делаем пустым объектом
                safe_data['custom_fields'] = {}
        else:
            safe_data['custom_fields'] = {}
        
        # Безопасно обрабатываем списки
        for list_field in ['services', 'goods_transactions', 'documents', 'client_tags', 'record_labels', 'composite', 'service', 'supplier']:
            if list_field not in safe_data:
                safe_data[list_field] = []
        
        # Создаем webhook с исправленными данными
        webhook_data = {
            'company_id': raw_data['company_id'],
            'resource': raw_data['resource'],
            'resource_id': raw_data['resource_id'],
            'status': raw_data['status'],
            'data': safe_data
        }
        
        return AltegioWebhookPayload(**webhook_data)
        
    except Exception as e:
        logger.error(f"❌ Failed to create flexible webhook: {e}")
        return None


async def process_webhook_internal(
    payload: AltegioWebhookPayload,
    request: Request,
    db: AsyncSession
) -> dict:
    """
    Внутренняя функция обработки одного webhook
    """
    try:
        logger.info(f"Processing webhook: company_id={payload.company_id}, "
                   f"resource={payload.resource}, resource_id={payload.resource_id}, "
                   f"status={payload.status}")
        
        if not await verify_webhook_signature(request):
            logger.warning("Invalid webhook signature")
            raise HTTPException(status_code=401, detail="Invalid webhook signature")
        
        # Проверяем условия для обработки
        comment_text = payload.data.comment or ""
        has_fch = 'фч' in comment_text.lower() if comment_text else False
        
        # Условия для обработки разных типов webhook
        # Поддерживаем только 'record' и 'goods_operations_sale' типы
        if payload.resource == 'record':
            # Обычные записи требуют комментарий с 'фч' и полную оплату
            conditions_met = (
                payload.data.comment and has_fch and 
                payload.data.paid_full == 1
            )
        elif payload.resource == 'goods_operations_sale':
            # Продажи товаров тоже требуют комментарий с 'фч'
            conditions_met = (
                payload.data.comment and has_fch
            )
        else:
            # Неподдерживаемый тип webhook - игнорируем
            logger.info(f"🚫 Unsupported resource type '{payload.resource}' for webhook {payload.resource_id}, ignoring...")
            return {
                "success": True,
                "message": f"Webhook {payload.resource_id} ignored - unsupported resource type '{payload.resource}'",
                "processed_count": 0
            }
        
        logger.info(f"� Checking processing conditions for webhook {payload.resource_id}:")
        logger.info(f"   📋 Resource: {payload.resource} (supported: 'record', 'goods_operations_sale') {'✅' if payload.resource in ['record', 'goods_operations_sale'] else '❌'}")
        logger.info(f"   💬 Comment: '{comment_text}' (must contain 'фч') {'✅' if has_fch else '❌'}")
        logger.info(f"   �️ Goods sale: requires 'фч' comment {'✅' if has_fch else '❌'}")
        
        if payload.resource == 'record':
            logger.info(f"   💰 Paid full: {payload.data.paid_full} (required: 1) {'✅' if payload.data.paid_full == 1 else '❌'}")
        elif payload.resource == 'goods_operations_sale':
            logger.info(f"   �️ Goods sale: requires 'фч' comment {'✅' if has_fch else '❌'}")
        
        logger.info(f"   🎯 Overall result: {'✅ PROCESSING' if conditions_met else '❌ SKIPPING'}")
        
        if not conditions_met:
            logger.info(f"Webhook {payload.resource_id} does not meet the required conditions for processing.")
            return {
                "success": True,
                "message": f"Webhook {payload.resource_id} skipped due to conditions",
                "processed_count": 0
            }

        # Проверяем, не был ли уже обработан
        existing_record = await db.execute(
            select(WebhookRecord).filter(
                WebhookRecord.resource_id == payload.resource_id,
                WebhookRecord.company_id == payload.company_id,
                WebhookRecord.processed == True
            )
        )
        if existing_record.scalars().first():
            logger.info(f"✅ Webhook with resource_id {payload.resource_id} already successfully processed, skipping.")
            return {
                "success": True,
                "message": f"Webhook {payload.resource_id} already processed",
                "processed_count": 0
            }

        # Остальная логика обработки webhook
        # Ищем существующую запись или создаем новую
        webhook_record = await db.execute(
            select(WebhookRecord).filter(
                WebhookRecord.resource_id == payload.resource_id,
                WebhookRecord.company_id == payload.company_id
            )
        )
        webhook_record = webhook_record.scalars().first()

        if webhook_record:
            # Обновляем существующую запись
            logger.info(f"🔄 Found existing webhook record (ID: {webhook_record.id}), updating for retry...")
            webhook_record.status = payload.status
            client_phone, client_name = get_client_data(payload.data.client)
            webhook_record.client_phone = client_phone
            webhook_record.client_name = client_name
            # Обрабатываем datetime
            if payload.data.datetime:
                webhook_record.record_date = datetime.fromisoformat(payload.data.datetime.replace(" ", "T").split("+")[0])
            elif payload.data.create_date:
                webhook_record.record_date = datetime.fromisoformat(payload.data.create_date.replace(" ", "T").split("+")[0])
            else:
                webhook_record.record_date = datetime.utcnow()
            webhook_record.services_data = json.dumps([s.model_dump() for s in payload.data.services])
            webhook_record.comment = payload.data.comment
            webhook_record.raw_data = payload.model_dump()
            webhook_record.updated_at = datetime.utcnow()
            webhook_record.processed = False
            webhook_record.processing_error = None
            webhook_record.webkassa_status = None
            webhook_record.webkassa_response = None
            webhook_record.webkassa_request_id = None
        else:
            # Создаем новую запись
            logger.info(f"📝 Creating new webhook record for resource_id {payload.resource_id}")
            record_date = datetime.utcnow()
            if payload.data.datetime:
                try:
                    record_date = datetime.fromisoformat(payload.data.datetime.replace(" ", "T").split("+")[0])
                except (ValueError, AttributeError) as e:
                    logger.warning(f"Failed to parse datetime '{payload.data.datetime}': {e}, using current time")
            elif payload.data.create_date:
                try:
                    record_date = datetime.fromisoformat(payload.data.create_date.replace(" ", "T").split("+")[0])
                except (ValueError, AttributeError) as e:
                    logger.warning(f"Failed to parse create_date '{payload.data.create_date}': {e}, using current time")
            
            client_phone, client_name = get_client_data(payload.data.client)
            webhook_record = WebhookRecord(
                company_id=payload.company_id,
                resource=payload.resource,
                resource_id=payload.resource_id,
                status=payload.status,
                client_phone=client_phone,
                client_name=client_name,
                record_date=record_date,
                services_data=json.dumps([s.model_dump() for s in payload.data.services]),
                comment=payload.data.comment,
                raw_data=payload.model_dump()
            )
            db.add(webhook_record)
        
        await db.commit()
        await db.refresh(webhook_record)
        
        logger.info(f"Webhook saved/updated in database with ID: {webhook_record.id}")
        
        # Теперь обрабатываем фискализацию
        try:
            # Получаем document_id
            altegio_document_id = None
            if payload.resource == "goods_operations_sale":
                altegio_document_id = payload.data.document_id
            else:
                if payload.data.documents:
                    altegio_document_id = payload.data.documents[0].id
            
            if not altegio_document_id:
                logger.warning(f"No document ID found in webhook for resource_id {payload.resource_id}")
                webhook_record.processing_error = "No document ID found in webhook"
                webhook_record.processed = False
                await db.commit()
                return {
                    "success": False,
                    "message": f"No document ID found for webhook {payload.resource_id}",
                    "processed_count": 0
                }

            # Получаем документ Altegio
            altegio_document = None
            try:
                logger.info(f"Requesting Altegio document: company_id={payload.company_id}, document_id={altegio_document_id}, resource={payload.resource}")
                
                if payload.resource == "goods_operations_sale":
                    logger.info(f"🛍️ Using goods sale document API for resource_id {payload.resource_id}")
                    altegio_document = await get_altegio_sale_document(payload.company_id, altegio_document_id)
                else:
                    logger.info(f"📋 Using transactions document API for resource_id {payload.resource_id}")
                    altegio_document = await get_altegio_document(payload.company_id, altegio_document_id)
                
                logger.info(f"✅ Successfully fetched Altegio document for resource_id {payload.resource_id}")
            except HTTPException as altegio_error:
                logger.warning(f"❌ Failed to fetch Altegio document for resource_id {payload.resource_id}: {altegio_error.detail}")
                altegio_document = {"data": []}

            # Проверяем данные
            has_data = False
            if isinstance(altegio_document, dict):
                has_data = bool(altegio_document.get("data"))
            elif isinstance(altegio_document, list):
                has_data = bool(altegio_document)
            else:
                has_data = False
                
            if not has_data:
                logger.warning(f"No data found in Altegio document for resource_id {payload.resource_id}")
                webhook_record.processing_error = "No data found in Altegio document"
                webhook_record.processed = False
                await db.commit()
                return {
                    "success": False,
                    "message": f"No data in Altegio document for webhook {payload.resource_id}",
                    "processed_count": 0
                }

            # Подготавливаем данные для Webkassa
            if payload.resource == "goods_operations_sale":
                webkassa_data = await prepare_webkassa_data_for_goods_sale(payload, altegio_document, db)
            else:
                webkassa_data = await prepare_webkassa_data(payload, altegio_document, db)
            
            logger.info(f"💰 Prepared Webkassa fiscalization data for {payload.resource_id}")

            # Подготавливаем информацию о webhook для логирования
            client_phone, client_name = get_client_data(payload.data.client)
            webhook_info = {
                "resource_id": payload.resource_id,
                "company_id": payload.company_id,
                "client_name": client_name if client_name else "Unknown",
                "client_phone": client_phone if client_phone else "Unknown",
                "record_date": payload.data.datetime if payload.data.datetime else (payload.data.create_date if payload.data.create_date else "Unknown"),
                "comment": payload.data.comment,
                "status": payload.status,
                "resource": payload.resource,
                "full_webhook": payload.model_dump()
            }

            webkassa_response = await send_to_webkassa_with_auto_refresh(db, webkassa_data, webhook_info)
            
            is_success = webkassa_response.get("success", False)
            if is_success:
                logger.info(f"✅ SUCCESS: Webkassa fiscalization completed for {payload.resource_id}")
                webhook_record.processed = True
                webhook_record.processed_at = datetime.utcnow()
                webhook_record.webkassa_status = "success"
                webhook_record.processing_error = None
                processed_count = 1
            else:
                logger.info(f"❌ FAILED: Webkassa fiscalization failed for {payload.resource_id}")
                webhook_record.processed = False
                webhook_record.processed_at = None
                webhook_record.webkassa_status = "failed"
                
                error_details = []
                if "errors" in webkassa_response:
                    error_details.extend(webkassa_response["errors"])
                if "error" in webkassa_response:
                    error_details.append(webkassa_response["error"])
                webhook_record.processing_error = "; ".join(error_details) if error_details else "Unknown Webkassa error"
                processed_count = 0

            # Сохраняем результат
            webhook_record.webkassa_response = json.dumps(webkassa_response)
            external_check_number = webkassa_data.get("ExternalCheckNumber")
            webhook_record.webkassa_request_id = str(external_check_number) if external_check_number is not None else None
            await db.commit()
            
            return {
                "success": is_success,
                "message": f"Webhook {payload.resource_id} processed {'successfully' if is_success else 'with errors'}",
                "processed_count": processed_count,
                "record_id": webhook_record.id
            }
            
        except Exception as e:
            logger.error(f"Error processing webhook {payload.resource_id}: {str(e)}", exc_info=True)
            webhook_record.processing_error = str(e)
            webhook_record.processed = False
            await db.commit()
            return {
                "success": False,
                "message": f"Processing error for webhook {payload.resource_id}: {str(e)}",
                "processed_count": 0
            }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Critical error in webhook processing: {str(e)}", exc_info=True)
        return {
            "success": False,
            "message": f"Critical processing error: {str(e)}",
            "processed_count": 0
        }


# Вспомогательные функции
async def send_telegram_notification(message: str, error_details: dict = None) -> bool:
    """
    Отправляет уведомление в Telegram о критических ошибках
    """
    bot_token = "7922422379:AAEjk9PZuF8HgHNK3UoVDn-RIMXZhCfKewk"
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "1125559425")  # ID чата для уведомлений
    
    # Формируем сообщение
    telegram_message = f"🚨 ОШИБКА WEBKASSA\n\n"
    telegram_message += f"📅 Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    telegram_message += f"💬 Сообщение: {message}\n\n"
    
    if error_details:
        telegram_message += "📋 Детали ошибки:\n"
        for key, value in error_details.items():
            # Обрезаем длинные значения для читаемости
            if isinstance(value, str) and len(value) > 400:
                value = value[:400] + "..."
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


@router.post("/webhook/test")
async def test_webhook_endpoint(request: Request):
    """
    Тестовый эндпоинт для проверки получения webhook от Altegio
    """
    try:
        # Получаем все заголовки
        headers = dict(request.headers)
        
        # Получаем тело запроса
        body = await request.body()
        body_text = body.decode('utf-8') if body else ""
        
        # Получаем query параметры
        query_params = dict(request.query_params)
        
        # Логируем всю информацию
        logger.info("=" * 50)
        logger.info("🧪 TEST WEBHOOK RECEIVED")
        logger.info("=" * 50)
        logger.info(f"📍 Method: {request.method}")
        logger.info(f"📍 URL: {request.url}")
        logger.info(f"📍 Client IP: {request.client.host if request.client else 'Unknown'}")
        logger.info(f"📋 Headers:")
        for key, value in headers.items():
            logger.info(f"   {key}: {value}")
        logger.info(f"🔍 Query params: {query_params}")
        logger.info(f"📦 Body size: {len(body)} bytes")
        logger.info(f"📦 Body content: {body_text[:1000]}{'...' if len(body_text) > 1000 else ''}")
        logger.info("=" * 50)
        
        # Пытаемся распарсить JSON если возможно
        try:
            if body_text:
                import json
                parsed_json = json.loads(body_text)
                logger.info(f"✅ JSON parsed successfully:")
                logger.info(f"📋 JSON content: {json.dumps(parsed_json, ensure_ascii=False, indent=2)}")
        except json.JSONDecodeError:
            logger.info("⚠️ Body is not valid JSON")
        
        # Отправляем уведомление в Telegram
        await send_telegram_notification(
            "🧪 Тестовый webhook получен",
            {
                "URL": str(request.url),
                "Method": request.method,
                "IP": request.client.host if request.client else 'Unknown',
                "Headers": str(headers),
                "Body size": f"{len(body)} bytes",
                "Body preview": body_text[:500] + "..." if len(body_text) > 500 else body_text
            }
        )
        
        return {
            "success": True,
            "message": "Test webhook received successfully",
            "received_data": {
                "method": request.method,
                "headers": headers,
                "query_params": query_params,
                "body_size": len(body),
                "body_preview": body_text[:200] + "..." if len(body_text) > 200 else body_text
            }
        }
        
    except Exception as e:
        logger.error(f"Error in test webhook: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/webhook/refresh-api-key")
async def manual_refresh_api_key(db: AsyncSession = Depends(get_db_session)):
    """
    Ручное обновление API ключа Webkassa через эндпоинт
    """
    try:
        logger.info("🔄 Manual API key refresh requested")
        
        # Проверяем текущий ключ
        current_key = await get_webkassa_api_key(db)
        if current_key:
            logger.info(f"📋 Current key found: ID {current_key.id}, updated {current_key.updated_at}")
        else:
            logger.info("📋 No current key found in database")
        
        # Обновляем ключ
        refreshed_key = await refresh_webkassa_api_key(db)
        
        if refreshed_key:
            logger.info("✅ Manual API key refresh successful")
            
            # Отправляем уведомление об успехе
            await send_telegram_notification(
                "✅ Ручное обновление API ключа Webkassa выполнено успешно",
                {
                    "Результат": "Успех",
                    "Новый ключ ID": str(refreshed_key.id),
                    "Обновлен": str(refreshed_key.updated_at),
                    "Токен": f"{refreshed_key.user_id[:20]}...{refreshed_key.user_id[-10:]}",
                    "API ключ": f"{refreshed_key.api_key[:20]}...{refreshed_key.api_key[-10:]}"
                }
            )
            
            return {
                "success": True,
                "message": "API key refreshed successfully",
                "key_info": {
                    "id": refreshed_key.id,
                    "service_name": refreshed_key.service_name,
                    "updated_at": refreshed_key.updated_at.isoformat(),
                    "token_preview": f"{refreshed_key.user_id[:20]}...{refreshed_key.user_id[-10:]}",
                    "api_key_preview": f"{refreshed_key.api_key[:20]}...{refreshed_key.api_key[-10:]}"
                }
            }
        else:
            logger.error("❌ Manual API key refresh failed")
            
            # Отправляем уведомление о неудаче
            await send_telegram_notification(
                "❌ Ручное обновление API ключа Webkassa не удалось",
                {

                    "Результат": "Неудача",
                    "Требуется": "Проверка логов и настроек API"
                }
            )
            
            return {
                "success": False,
                "message": "Failed to refresh API key",
                "error": "API key refresh script failed"
            }
            
    except Exception as e:
        logger.error(f"❌ Error in manual API key refresh: {e}", exc_info=True)
        
        await send_telegram_notification(
            "🚨 Ошибка при ручном обновлении API ключа Webкassa",
            {
                "Ошибка": str(e),
                "Тип": type(e).__name__,
                "Требуется": "Проверка системы"
            }
        )
        
        return {
            "success": False,
            "message": "Internal server error during API key refresh",
            "error": str(e)
        }


@router.delete("/webhook/record/{record_id}")
async def delete_webhook_record(
    record_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Удаляет конкретную webhook запись по ID
    """
    try:
        # Ищем запись
        webhook_record = await db.execute(
            select(WebhookRecord).filter(WebhookRecord.id == record_id)
        )
        webhook_record = webhook_record.scalars().first()

        if not webhook_record:
            raise HTTPException(status_code=404, detail="Webhook record not found")
        
        # Сохраняем информацию для логов
        resource_id = webhook_record.resource_id
        company_id = webhook_record.company_id
        processed = webhook_record.processed
        
        # Удаляем запись
        await db.delete(webhook_record)
        await db.commit()
        
        logger.info(f"🗑️ Deleted webhook record: ID={record_id}, resource_id={resource_id}, processed={processed}")
        
        return {
            "success": True,
            "message": f"Webhook record {record_id} deleted successfully",
            "deleted_record": {
                "id": record_id,
                "resource_id": resource_id,
                "company_id": company_id,
                "was_processed": processed
            }
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error deleting webhook record {record_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/webhook/resource/{resource_id}")
async def delete_webhook_by_resource_id(
    resource_id: int,
    company_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Удаляет все webhook записи для конкретного resource_id
    Опционально можно указать company_id для более точного поиска
    """
    try:
        # Строим запрос
        query = select(WebhookRecord).filter(WebhookRecord.resource_id == resource_id)
        if company_id:
            query = query.filter(WebhookRecord.company_id == company_id)
        
        # Получаем все записи для удаления
        result = await db.execute(query)
        records_to_delete = result.scalars().all()
        
        if not records_to_delete:
            message = f"No webhook records found for resource_id {resource_id}"
            if company_id:
                message += f" and company_id {company_id}"
            raise HTTPException(status_code=404, detail=message)
        
        deleted_info = []
        for record in records_to_delete:
            deleted_info.append({
                "id": record.id,
                "resource_id": record.resource_id,
                "company_id": record.company_id,
                "was_processed": record.processed,
                "webkassa_status": record.webkassa_status
            })
            await db.delete(record)
        
        await db.commit()
        
        logger.info(f"🗑️ Deleted {len(deleted_info)} webhook records for resource_id {resource_id}")
        for info in deleted_info:
            logger.info(f"   - ID: {info['id']}, processed: {info['was_processed']}, status: {info['webkassa_status']}")
        
        return {
            "success": True,
            "message": f"Deleted {len(deleted_info)} webhook records for resource_id {resource_id}",
            "deleted_count": len(deleted_info),
            "deleted_records": deleted_info
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error deleting webhook records for resource_id {resource_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/webhook/failed")
async def delete_failed_webhook_records(
    confirm: bool = False,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Удаляет все неуспешно обработанные webhook записи (processed=False)
    
    Параметры:
    - confirm: Обязательный параметр для подтверждения операции (должен быть True)
    """
    if not confirm:
        raise HTTPException(
            status_code=400, 
            detail="This operation requires confirmation. Add ?confirm=true to the request"
        )
    
    try:
        # Получаем все неуспешные записи
        result = await db.execute(
            select(WebhookRecord).filter(WebhookRecord.processed == False)
        )
        failed_records = result.scalars().all()
        
        if not failed_records:
            return {
                "success": True,
                "message": "No failed webhook records found to delete",
                "deleted_count": 0
            }
        
        deleted_info = []
        for record in failed_records:
            deleted_info.append({
                "id": record.id,
                "resource_id": record.resource_id,
                "company_id": record.company_id,
                "webkassa_status": record.webkassa_status,
                "processing_error": record.processing_error
            })
            await db.delete(record)
        
        await db.commit()
        
        logger.info(f"🗑️ Deleted {len(deleted_info)} failed webhook records")
        for info in deleted_info[:5]:  # Показываем только первые 5 для логов
            logger.info(f"   - ID: {info['id']}, resource_id: {info['resource_id']}, error: {info['processing_error'][:100] if info['processing_error'] else 'None'}")
        if len(deleted_info) > 5:
            logger.info(f"   ... и еще {len(deleted_info) - 5} записей")
        
        return {
            "success": True,
            "message": f"Deleted {len(deleted_info)} failed webhook records",
            "deleted_count": len(deleted_info),
            "deleted_records": deleted_info
        }
        
    except Exception as e:
        logger.error(f"Error deleting failed webhook records: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/webhook/records")
async def list_webhook_records(
    limit: int = 50,
    offset: int = 0,
    processed: Optional[bool] = None,
    webkassa_status: Optional[str] = None,
    resource_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Получает список webhook записей с фильтрацией
    
    Параметры:
    - limit: максимальное количество записей (по умолчанию 50)
    - offset: смещение для пагинации (по умолчанию 0)
    - processed: фильтр по статусу обработки (True/False)
    - webkassa_status: фильтр по статусу Webkassa (success/failed)
    - resource_id: фильтр по конкретному resource_id
    """
    try:
        # Строим запрос с фильтрами
        query = select(WebhookRecord)
        
        if processed is not None:
            query = query.filter(WebhookRecord.processed == processed)
        
        if webkassa_status:
            query = query.filter(WebhookRecord.webkassa_status == webkassa_status)
            
        if resource_id:
            query = query.filter(WebhookRecord.resource_id == resource_id)
        
        # Добавляем сортировку и пагинацию
        query = query.order_by(WebhookRecord.created_at.desc()).offset(offset).limit(limit)
        
        # Выполняем запрос
        result = await db.execute(query)
        records = result.scalars().all()
        
        # Получаем общее количество записей для статистики
        count_query = select(WebhookRecord)
        if processed is not None:
            count_query = count_query.filter(WebhookRecord.processed == processed)
        if webkassa_status:
            count_query = count_query.filter(WebhookRecord.webkassa_status == webkassa_status)
        if resource_id:
            count_query = count_query.filter(WebhookRecord.resource_id == resource_id)
            
        count_result = await db.execute(count_query)
        total_count = len(count_result.scalars().all())
        
        # Формируем ответ
        records_data = []
        for record in records:
            records_data.append({
                "id": record.id,
                "resource_id": record.resource_id,
                "company_id": record.company_id,
                "resource": record.resource,
                "status": record.status,
                "client_phone": record.client_phone,
                "client_name": record.client_name,
                "processed": record.processed,
                "webkassa_status": record.webkassa_status,
                "processing_error": record.processing_error,
                "created_at": record.created_at.isoformat() if record.created_at else None,
                "processed_at": record.processed_at.isoformat() if record.processed_at else None,
                "comment": record.comment
            })
        
        return {
            "success": True,
            "records": records_data,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "total_count": total_count,
                "returned_count": len(records_data)
            },
            "filters": {
                "processed": processed,
                "webkassa_status": webkassa_status,
                "resource_id": resource_id
            }
        }
        
    except Exception as e:
        logger.error(f"Error listing webhook records: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/webhook/stats")
async def get_webhook_stats(db: AsyncSession = Depends(get_db_session)):
    """
    Получает статистику по webhook записям
    """
    try:
        # Общее количество записей
        total_result = await db.execute(select(WebhookRecord))
        total_count = len(total_result.scalars().all())
        
        # Количество обработанных
        processed_result = await db.execute(select(WebhookRecord).filter(WebhookRecord.processed == True))
        processed_count = len(processed_result.scalars().all())
        
        # Количество неоработанных
        unprocessed_result = await db.execute(select(WebhookRecord).filter(WebhookRecord.processed == False))
        unprocessed_count = len(unprocessed_result.scalars().all())
        
        # Количество успешных в Webkassa
        success_result = await db.execute(select(WebhookRecord).filter(WebhookRecord.webkassa_status == "success"))
        success_count = len(success_result.scalars().all())
        
        # Количество неуспешных в Webkassa
        failed_result = await db.execute(select(WebhookRecord).filter(WebhookRecord.webkassa_status == "failed"))
        failed_count = len(failed_result.scalars().all())
        
        return {
            "success": True,
            "stats": {
                "total_records": total_count,
                "processed_records": processed_count,
                "unprocessed_records": unprocessed_count,
                "webkassa_success": success_count,
                "webkassa_failed": failed_count,
                "processing_rate": round((processed_count / total_count * 100), 2) if total_count > 0 else 0,
                "success_rate": round((success_count / total_count * 100), 2) if total_count > 0 else 0
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting webhook stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


async def webhook_queue_worker():
    """
    Worker для обработки webhook из очереди последовательно
    """
    logger.info("🚀 Starting webhook queue worker...")
    
    while True:
        try:
            # Получаем задачу из очереди
            task: WebhookTask = await webhook_processing_queue.get()
            logger.info(f"📋 Processing webhook task: {task.task_id}")
            
            try:
                # Обрабатываем webhook с семафором для гарантии последовательности
                async with webhook_processing_semaphore:
                    result = await process_webhook_internal(task.payload, task.request, task.db_session)
                    task.result_future.set_result(result)
                    logger.info(f"✅ Completed webhook task: {task.task_id}")
            except Exception as e:
                logger.error(f"❌ Failed webhook task {task.task_id}: {e}", exc_info=True)
                task.result_future.set_exception(e)
            finally:
                # Помечаем задачу как выполненную
                webhook_processing_queue.task_done()
                
        except Exception as e:
            logger.error(f"❌ Error in webhook queue worker: {e}", exc_info=True)
            await asyncio.sleep(1)  # Небольшая пауза при ошибке

# Запускаем worker в фоновом режиме
_queue_worker_task = None

def ensure_queue_worker_running():
    """
    Заглушка для запуска worker очереди
    """
    logger.info("🔄 Ensuring queue worker is running")
    pass



