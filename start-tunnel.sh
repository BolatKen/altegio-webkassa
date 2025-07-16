#!/bin/bash

echo "🚀 Запуск туннеля для Altegio webhook тестирования"
echo "=================================================="
echo ""

# Проверяем доступность сервера
echo "📡 Проверяем локальный сервер..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Сервер доступен на http://localhost:8000"
else
    echo "❌ Сервер недоступен! Запустите: docker-compose up"
    exit 1
fi

echo ""
echo "🔧 Выберите способ создания туннеля:"
echo "1) ngrok (рекомендуется)"
echo "2) localtunnel"
echo "3) cloudflared"
echo ""
read -p "Введите номер (1-3): " choice

case $choice in
    1)
        echo "🔥 Запускаем ngrok..."
        echo ""
        echo "📋 После запуска:"
        echo "   - Скопируйте HTTPS URL (например: https://abc123.ngrok.io)"
        echo "   - Тестовый webhook: https://abc123.ngrok.io/webhook/test"
        echo "   - Основной webhook: https://abc123.ngrok.io/webhook"
        echo ""
        ngrok http 8000
        ;;
    2)
        echo "🔥 Запускаем localtunnel..."
        echo ""
        if ! command -v lt &> /dev/null; then
            echo "⚠️ localtunnel не установлен. Устанавливаем..."
            npm install -g localtunnel
        fi
        echo "📋 URL будет: https://altegio-webhook.loca.lt"
        echo "   - Тестовый webhook: https://altegio-webhook.loca.lt/webhook/test"
        echo "   - Основной webhook: https://altegio-webhook.loca.lt/webhook"
        echo ""
        lt --port 8000 --subdomain altegio-webhook
        ;;
    3)
        echo "🔥 Запускаем cloudflared..."
        echo ""
        if ! command -v cloudflared &> /dev/null; then
            echo "❌ cloudflared не установлен. Скачайте с:"
            echo "   https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/"
            exit 1
        fi
        echo "📋 URL будет показан после запуска"
        echo "   Добавьте /webhook/test или /webhook к URL"
        echo ""
        cloudflared tunnel --url http://localhost:8000
        ;;
    *)
        echo "❌ Неверный выбор"
        exit 1
        ;;
esac
