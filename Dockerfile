# Dockerfile для FastAPI приложения
# Altegio-Webkassa Integration

FROM python:3.11-slim

# Установка переменных окружения для корректной работы с UTF-8
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV PYTHONIOENCODING=utf-8

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    locales \
    && echo "en_US.UTF-8 UTF-8" > /etc/locale.gen \
    && locale-gen \
    && rm -rf /var/lib/apt/lists/*

# Создание пользователя для приложения
RUN useradd --create-home --shell /bin/bash app

# Установка рабочей директории
WORKDIR /app

# Копирование файлов зависимостей
COPY requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копирование кода приложения
COPY app/ ./app/
COPY .env .

# Создание директории для логов
RUN mkdir -p logs && chown -R app:app logs

# Переключение на пользователя приложения
USER app

# Открытие порта
EXPOSE 8000

# Проверка здоровья контейнера
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Команда запуска
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]

