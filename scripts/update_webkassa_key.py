#!/usr/bin/env python3
"""
Скрипт для автоматического обновления API ключа Webkassa каждый день в 5 утра.
Этот скрипт должен запускаться через cron или systemd timer.
"""

import asyncio
import os
import sys
import logging
from datetime import datetime
from typing import Optional

# Добавляем путь к app модулю
sys.path.append('/app')

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.models import ApiKey
import httpx

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/webkassa_key_update.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class WebkassaKeyUpdater:
    """Класс для обновления API ключа Webkassa"""
    
    def __init__(self):
        # Строим URL базы данных из переменных окружения
        db_user = os.getenv("POSTGRES_USER", "postgres")
        db_password = os.getenv("POSTGRES_PASSWORD", "postgres")
        db_host = os.getenv("POSTGRES_HOST", "db")
        db_port = os.getenv("POSTGRES_PORT", "5432")
        db_name = os.getenv("POSTGRES_DB", "altegio_webkassa_db")
        
        self.db_url = f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        
        self.webkassa_login = os.getenv("WEBKASSA_LOGIN")
        self.webkassa_password = os.getenv("WEBKASSA_PASSWORD")
        self.webkassa_auth_url = os.getenv("WEBKASSA_AUTH_URL", "https://api.webkassa.kz/api/Authorize")
        
        # Создаем асинхронный движок базы данных
        self.engine = create_async_engine(self.db_url)
        self.SessionLocal = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    
    async def get_new_webkassa_token(self) -> Optional[dict]:
        """
        Получает новый API токен от Webkassa через логин/пароль авторизацию
        """
        if not self.webkassa_login or not self.webkassa_password:
            logger.error("Webkassa login credentials not configured in environment variables")
            return None
            
        auth_data = {
            "Login": self.webkassa_login,
            "Password": self.webkassa_password
        }
        
        try:
            async with httpx.AsyncClient() as client:
                logger.info(f"Requesting new token from {self.webkassa_auth_url}")
                response = await client.post(
                    self.webkassa_auth_url,
                    json=auth_data,
                    timeout=30
                )
                response.raise_for_status()
                
                result = response.json()
                logger.info("Successfully received new token from Webkassa")
                logger.info(f"📋 Full API response: {result}")
                return result
                
        except httpx.RequestError as e:
            logger.error(f"Network error while getting Webkassa token: {e}")
            return None
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code} while getting Webkassa token: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error while getting Webkassa token: {e}")
            return None
    
    async def update_api_key_in_db(self, new_token: str, user_id: str = None) -> bool:
        """
        Обновляет API ключ Webkassa в базе данных
        """
        try:
            async with self.SessionLocal() as db:
                # Ищем существующую запись
                result = await db.execute(
                    select(ApiKey).filter(ApiKey.service_name == "Webkassa")
                )
                api_key_record = result.scalars().first()
                
                if api_key_record:
                    # Обновляем существующую запись
                    old_key = api_key_record.api_key[:20] + "..." if api_key_record.api_key else "None"
                    logger.info(f"📝 Found existing API key record (old key: {old_key})")
                    
                    api_key_record.api_key = new_token
                    if user_id:
                        api_key_record.user_id = user_id
                    api_key_record.updated_at = datetime.utcnow()
                    
                    new_key = new_token[:20] + "..." if new_token else "None"
                    logger.info(f"✏️ Updated API key: {old_key} -> {new_key}")
                    logger.info(f"📅 Updated timestamp: {api_key_record.updated_at}")
                    if user_id:
                        logger.info(f"👤 Updated user_id: {user_id}")
                    logger.info("Updated existing Webkassa API key in database")
                else:
                    # Создаем новую запись
                    new_key = new_token[:20] + "..." if new_token else "None"
                    logger.info(f"📝 Creating new API key record")
                    logger.info(f"🔑 New API key: {new_key}")
                    if user_id:
                        logger.info(f"👤 User ID: {user_id}")
                    
                    api_key_record = ApiKey(
                        service_name="Webkassa",
                        api_key=new_token,
                        user_id=user_id
                    )
                    db.add(api_key_record)
                    logger.info("Created new Webkassa API key record in database")
                
                await db.commit()
                logger.info("Successfully committed API key changes to database")
                
                # Проверяем что записалось в базу
                await db.refresh(api_key_record)
                saved_key = api_key_record.api_key[:20] + "..." if api_key_record.api_key else "None"
                logger.info(f"✅ Verified in database - API key: {saved_key}")
                logger.info(f"✅ Verified in database - Service: {api_key_record.service_name}")
                logger.info(f"✅ Verified in database - Updated at: {api_key_record.updated_at}")
                if api_key_record.user_id:
                    logger.info(f"✅ Verified in database - User ID: {api_key_record.user_id}")
                
                return True
                
        except Exception as e:
            logger.error(f"Error updating API key in database: {e}")
            return False
    
    async def validate_new_token(self, token: str) -> bool:
        """
        Проверяет валидность нового токена через тестовый запрос к Webkassa API
        """
        test_url = os.getenv("WEBKASSA_API_URL")
        if not test_url:
            logger.warning("WEBKASSA_API_URL not configured, skipping token validation")
            return True  # Считаем валидным, если нет URL для проверки
            
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        
        # Простой тестовый запрос для проверки токена
        try:
            async with httpx.AsyncClient() as client:
                # Проверяем токен через endpoint получения информации о кассах
                test_endpoint = f"{test_url.rstrip('/')}/api/CashBox"
                response = await client.get(
                    test_endpoint,
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    logger.info("New token validation successful")
                    logger.info(f"✅ Token validation response: {response.status_code}")
                    return True
                elif response.status_code == 401:
                    logger.error("New token validation failed: Unauthorized")
                    logger.error(f"❌ Token validation response: {response.status_code}")
                    return False
                else:
                    logger.warning(f"Token validation returned status {response.status_code}, assuming valid")
                    logger.info(f"⚠️ Token validation response: {response.status_code}")
                    return True  # Считаем валидным для других статусов
                    
        except Exception as e:
            logger.warning(f"Token validation failed with error: {e}, assuming valid")
            return True  # В случае ошибки считаем токен валидным
    
    async def run_update(self) -> bool:
        """
        Основной метод для выполнения обновления API ключа
        """
        logger.info("Starting Webkassa API key update process")
        
        try:
            # Получаем новый токен
            logger.info("🔄 Step 1: Requesting new token from Webkassa API...")
            token_data = await self.get_new_webkassa_token()
            if not token_data:
                logger.error("Failed to get new token from Webkassa")
                return False
            
            logger.info("🔍 Step 2: Parsing token data...")
            # Извлекаем токен из ответа
            # Webkassa возвращает: {"Data":{"Token":"..."}}
            new_token = None
            user_id = None
            
            if "Data" in token_data and "Token" in token_data["Data"]:
                new_token = token_data["Data"]["Token"]
                logger.info("📋 Found token in Data.Token field")
            elif "token" in token_data:
                new_token = token_data["token"]
                logger.info("📋 Found token in token field")
            elif "access_token" in token_data:
                new_token = token_data["access_token"]
                logger.info("📋 Found token in access_token field")
            elif "api_key" in token_data:
                new_token = token_data["api_key"]
                logger.info("📋 Found token in api_key field")
            else:
                logger.error(f"Unable to extract token from response: {token_data}")
                return False
            
            # Извлекаем user_id если есть (для Webkassa обычно не нужен)
            if "Data" in token_data and "UserId" in token_data["Data"]:
                user_id = str(token_data["Data"]["UserId"])
                logger.info("📋 Found user_id in Data.UserId field")
            elif "user_id" in token_data:
                user_id = str(token_data["user_id"])
                logger.info("📋 Found user_id in user_id field")
            elif "id" in token_data:
                user_id = str(token_data["id"])
                logger.info("📋 Found user_id in id field")
            
            logger.info(f"🔑 Extracted token: {new_token[:20]}...{new_token[-10:] if len(new_token) > 30 else new_token[20:]}")
            if user_id:
                logger.info(f"👤 Extracted user_id: {user_id}")
            else:
                logger.info("👤 No user_id found in response (this is normal for Webkassa)")
            
            # Проверяем валидность токена
            logger.info("🔍 Step 3: Validating new token...")
            if not await self.validate_new_token(new_token):
                logger.error("New token validation failed")
                return False
            
            # Обновляем токен в базе данных
            logger.info("💾 Step 4: Saving token to database...")
            if await self.update_api_key_in_db(new_token, user_id):
                logger.info("✅ Webkassa API key update completed successfully")
                return True
            else:
                logger.error("❌ Failed to update API key in database")
                return False
                
        except Exception as e:
            logger.error(f"Unexpected error during API key update: {e}", exc_info=True)
            return False
        finally:
            await self.engine.dispose()


async def main():
    """Точка входа для скрипта"""
    updater = WebkassaKeyUpdater()
    success = await updater.run_update()
    
    if success:
        logger.info("🎉 Webkassa API key update process completed successfully")
        sys.exit(0)
    else:
        logger.error("💥 Webkassa API key update process failed")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
