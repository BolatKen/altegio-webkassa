"""
Настройка подключения к базе данных PostgreSQL
"""
import os
import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import MetaData

logger = logging.getLogger(__name__)

# Базовый класс для моделей
Base = declarative_base()

# Метаданные для таблиц
metadata = MetaData()

# Настройка подключения к базе данных
def get_database_url() -> str:
    """Формирование URL для подключения к PostgreSQL"""
    db_user = os.getenv("POSTGRES_USER", "postgres")
    db_password = os.getenv("POSTGRES_PASSWORD", "postgres")
    db_host = os.getenv("POSTGRES_HOST", "localhost")
    db_port = os.getenv("POSTGRES_PORT", "5432")
    db_name = os.getenv("POSTGRES_DB", "altegio_webkassa_db")
    
    # Асинхронный URL для PostgreSQL
    database_url = f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    logger.info(f"Database URL configured: postgresql+asyncpg://{db_user}:***@{db_host}:{db_port}/{db_name}")
    return database_url


# Создание асинхронного движка
engine = create_async_engine(
    get_database_url(),
    echo=os.getenv("DEBUG", "False").lower() == "true",  # Логирование SQL запросов в debug режиме
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Проверка соединения перед использованием
    pool_recycle=3600,   # Переподключение каждый час
)

# Создание фабрики сессий
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency для получения сессии базы данных
    Используется в FastAPI endpoints через Depends()
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {str(e)}")
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables():
    """
    Создание всех таблиц в базе данных
    Вызывается при запуске приложения
    """
    try:
        # Импортируем модели для регистрации в метаданных
        from app.models import WebhookRecord  # noqa
        
        async with engine.begin() as conn:
            # Создаем все таблицы
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")
            
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
        raise


async def drop_tables():
    """
    Удаление всех таблиц (для тестирования)
    """
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            logger.info("Database tables dropped successfully")
            
    except Exception as e:
        logger.error(f"Error dropping database tables: {str(e)}")
        raise


async def check_database_connection():
    """
    Проверка подключения к базе данных
    """
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute("SELECT 1")
            logger.info("Database connection successful")
            return True
            
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        return False

