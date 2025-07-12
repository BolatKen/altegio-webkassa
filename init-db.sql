-- Инициализация базы данных для Altegio-Webkassa Integration
-- Этот файл выполняется при первом запуске PostgreSQL контейнера

-- Создание расширений
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Создание индексов для оптимизации производительности
-- (Таблицы создаются автоматически через SQLAlchemy)

-- Настройка часового пояса
SET timezone = 'Asia/Almaty';

-- Создание пользователя для приложения (если нужен отдельный пользователь)
-- CREATE USER app_user WITH PASSWORD 'app_password';
-- GRANT CONNECT ON DATABASE altegio_webkassa_db TO app_user;
-- GRANT USAGE ON SCHEMA public TO app_user;
-- GRANT CREATE ON SCHEMA public TO app_user;

-- Комментарий о создании таблиц
-- Таблицы создаются автоматически через SQLAlchemy при запуске приложения
-- См. app/models.py для структуры таблиц

