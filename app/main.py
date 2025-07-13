"""
Основное FastAPI приложение для интеграции Altegio и Webkassa
"""
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.db import create_tables
from app.routes.webhook import router as webhook_router
from app.routes.acquire import router as acquire_router


# Настройка логирования
def setup_logging():
    """Настройка логирования в файл и консоль с корректной обработкой Unicode"""
    log_level = os.getenv("LOG_LEVEL", "INFO")
    log_file = os.getenv("LOG_FILE", "logs/errors.log")
    
    # Создаем директорию для логов если её нет
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    
    # Пользовательский форматтер для правильной обработки Unicode
    class UnicodeFormatter(logging.Formatter):
        def format(self, record):
            # Форматируем запись
            formatted = super().format(record)
            # Убеждаемся что это строка в правильной кодировке
            if isinstance(formatted, bytes):
                formatted = formatted.decode('utf-8', errors='replace')
            return formatted
    
    # Настройка форматирования с правильной кодировкой
    formatter = UnicodeFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Удаляем старые handlers если есть
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Логирование в файл с правильной кодировкой
    file_handler = logging.FileHandler(
        log_file, 
        encoding='utf-8', 
        mode='a'  # append mode
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(getattr(logging, log_level.upper()))
    
    # Логирование в консоль с правильной кодировкой
    import sys
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    
    # Настройка root logger
    root_logger.setLevel(getattr(logging, log_level.upper()))
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Отключаем слишком подробные логи от сторонних библиотек
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    
    # Тестовое сообщение для проверки кодировки
    root_logger.info("🚀 Логирование настроено. Тест Unicode: фч тест кириллицы")
    
    return root_logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Startup
    logger = setup_logging()
    logger.info("Starting Altegio-Webkassa Integration Service")
    
    # Создание таблиц в базе данных
    await create_tables()
    logger.info("Database tables created/verified")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Altegio-Webkassa Integration Service")


# Создание FastAPI приложения
app = FastAPI(
    title="Altegio-Webkassa Integration",
    description="Сервис интеграции между Altegio и Webkassa для фискализации",
    version="1.0.0",
    lifespan=lifespan
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение статических файлов
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Настройка шаблонов
templates = Jinja2Templates(directory="app/templates")

# Подключение маршрутов
app.include_router(webhook_router, prefix="/api", tags=["webhook"])
app.include_router(acquire_router, tags=["frontend"])


@app.get("/")
async def root():
    """Корневой эндпоинт для проверки работоспособности"""
    return {
        "message": "Altegio-Webkassa Integration Service",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Эндпоинт для проверки здоровья сервиса"""
    return {
        "status": "healthy",
        "service": "altegio-webkassa-integration"
    }


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", 8000))
    debug = os.getenv("DEBUG", "False").lower() == "true"
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )

