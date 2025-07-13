#!/bin/bash
# Тестовый скрипт для проверки обновления API ключа Webkassa
# Файл: scripts/test-update.sh

set -e

echo "🧪 Тестирование системы обновления API ключа Webkassa"
echo "====================================================="

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

# Проверяем, что проект запущен
echo "🔍 Проверяем статус Docker контейнеров..."
if ! docker-compose ps | grep -q "Up"; then
    echo "❌ Docker контейнеры не запущены. Запускаем..."
    docker-compose up -d
    echo "✅ Контейнеры запущены"
    sleep 10
else
    echo "✅ Контейнеры уже запущены"
fi

# Проверяем переменные окружения
echo ""
echo "🔍 Проверяем конфигурацию..."
if [ ! -f ".env" ]; then
    echo "❌ .env файл не найден"
    exit 1
fi

if ! grep -q "WEBKASSA_LOGIN" .env || ! grep -q "WEBKASSA_PASSWORD" .env; then
    echo "❌ WEBKASSA_LOGIN или WEBKASSA_PASSWORD не настроены в .env"
    echo "Добавьте следующие строки в .env:"
    echo "WEBKASSA_LOGIN=your_webkassa_login"
    echo "WEBKASSA_PASSWORD=your_webkassa_password"
    exit 1
fi

echo "✅ Конфигурация в порядке"

# Запускаем тестовое обновление
echo ""
echo "🧪 Запускаем тестовое обновление API ключа..."
echo "Это может занять до 30 секунд..."

# Запускаем Python скрипт внутри контейнера
docker-compose exec -T backend python /app/scripts/update_webkassa_key.py

if [ $? -eq 0 ]; then
    echo "✅ Тестовое обновление прошло успешно!"
    
    # Проверяем результат в базе данных
    echo ""
    echo "🔍 Проверяем результат в базе данных..."
    result=$(docker-compose exec -T db psql -U postgres -d altegio_webkassa_db -t -c "SELECT service_name, updated_at FROM api_keys WHERE service_name = 'Webkassa';" 2>/dev/null || echo "ERROR")
    
    if [ "$result" != "ERROR" ] && [ -n "$result" ]; then
        echo "✅ API ключ успешно обновлен в базе данных:"
        echo "$result"
    else
        echo "⚠️  Не удалось проверить результат в базе данных"
    fi
    
else
    echo "❌ Тестовое обновление завершилось с ошибкой"
    echo "Проверьте логи: docker-compose logs backend | grep webkassa"
    exit 1
fi

echo ""
echo "🎉 Тестирование завершено!"
echo "=========================="
echo ""
echo "📋 Если тест прошел успешно, вы можете:"
echo "1. Установить автоматическое обновление: sudo scripts/install-auto-update.sh"
echo "2. Проверить статус: scripts/check-status.sh"
echo "3. Просмотреть логи: docker-compose logs backend | grep webkassa"
