#!/bin/bash

echo "🔧 Решение проблемы отсутствия API ключа Webkassa"
echo "================================================"
echo ""

# Проверяем работу сервера
echo "1️⃣ Проверяем статус сервера..."
if curl -s http://165.227.159.243:8001/health > /dev/null 2>&1; then
    echo "✅ Сервер работает (165.227.159.243:8001)"
else
    echo "❌ Сервер недоступен (165.227.159.243:8001)"
    echo "🔍 Возможные причины:"
    echo "   - Сервер не запущен"
    echo "   - Проблемы с сетью"
    echo "   - Порт 8001 заблокирован"
    exit 1
fi

echo ""
echo "2️⃣ Попытка автоматического получения API ключа..."

# Пытаемся обновить API ключ через эндпоинт
if curl -s -X POST http://165.227.159.243:8001/webhook/refresh-api-key | grep -q '"success": *true'; then
    echo "✅ API ключ успешно обновлен через веб-эндпоинт"
else
    echo "❌ Не удалось обновить API ключ"
    echo ""
    echo "🔍 Возможные причины:"
    echo "   - Неверные credentials в .env файле на сервере"
    echo "   - Проблемы с сетью до API Webkassa"
    echo "   - API Webkassa недоступен"
    echo ""
    echo "📋 Проверьте логи на сервере"
    exit 1
fi

echo ""
echo "3️⃣ Проверяем результат..."

# Тестируем webhook
echo "🧪 Отправляем тестовый webhook..."
curl -s -X POST -H "Content-Type: application/json" \
    http://165.227.159.243:8001/webhook/test \
    -d '{"test": "api_key_fix_test", "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"}'

echo ""
echo ""
echo "✅ Готово! Проблема должна быть решена."
echo ""
echo "📱 Проверьте уведомления в Telegram боте"
echo "📋 Логи на сервере: docker logs <container_name>"
echo ""
echo "🔗 Ваш webhook URL для Altegio:"
echo "   http://165.227.159.243:8001/webhook"
