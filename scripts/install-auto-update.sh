#!/bin/bash
# Быстрая установка системы автоматического обновления API ключа Webkassa
# Файл: scripts/install-auto-update.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
INSTALL_DIR="/opt/altegio-webkassa-integration"

echo "🚀 Установка системы автоматического обновления API ключа Webkassa"
echo "=================================="

# Проверяем права root
if [[ $EUID -ne 0 ]]; then
   echo "❌ Этот скрипт должен запускаться от имени root (sudo)"
   exit 1
fi

# Проверяем наличие Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен. Установите Docker и повторите попытку."
    exit 1
fi

# Проверяем наличие docker-compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose не установлен. Установите Docker Compose и повторите попытку."
    exit 1
fi

echo "✅ Проверки пройдены"

# Создаем директорию для проекта, если не существует
if [ ! -d "$INSTALL_DIR" ]; then
    echo "📁 Создаем директорию проекта: $INSTALL_DIR"
    mkdir -p "$INSTALL_DIR"
    cp -r "$PROJECT_ROOT"/* "$INSTALL_DIR"/
    echo "✅ Проект скопирован в $INSTALL_DIR"
else
    echo "📁 Проект уже существует в $INSTALL_DIR"
fi

# Копируем скрипт-обертку
echo "📋 Устанавливаем скрипт-обертку..."
cp "$SCRIPT_DIR/update-webkassa-key.sh" /usr/local/bin/
chmod +x /usr/local/bin/update-webkassa-key.sh
echo "✅ Скрипт-обертка установлен: /usr/local/bin/update-webkassa-key.sh"

# Устанавливаем systemd service и timer
echo "⚙️ Устанавливаем systemd службы..."

# Обновляем пути в systemd файлах
sed "s|/opt/altegio-webkassa-integration|$INSTALL_DIR|g" "$SCRIPT_DIR/webkassa-key-update.service" > /etc/systemd/system/webkassa-key-update.service
cp "$SCRIPT_DIR/webkassa-key-update.timer" /etc/systemd/system/

echo "✅ Systemd файлы установлены"

# Перезагружаем systemd
echo "🔄 Перезагружаем systemd..."
systemctl daemon-reload

# Включаем и запускаем timer
echo "⏰ Активируем timer..."
systemctl enable webkassa-key-update.timer
systemctl start webkassa-key-update.timer

echo "✅ Timer активирован"

# Создаем директории для логов
mkdir -p /var/log
touch /var/log/webkassa-key-update.log
chmod 644 /var/log/webkassa-key-update.log

echo "📝 Файл логов создан: /var/log/webkassa-key-update.log"

# Проверяем статус
echo ""
echo "🔍 Проверяем статус установки:"
echo "--------------------------------"

# Статус timer
echo "Timer статус:"
systemctl status webkassa-key-update.timer --no-pager

echo ""
echo "Следующий запуск:"
systemctl list-timers webkassa-key-update.timer --no-pager

echo ""
echo "🎉 Установка завершена!"
echo "=================================="
echo ""
echo "📋 Следующие шаги:"
echo "1. Настройте переменные окружения в $INSTALL_DIR/.env:"
echo "   - WEBKASSA_LOGIN"
echo "   - WEBKASSA_PASSWORD"
echo "   - WEBKASSA_AUTH_URL"
echo ""
echo "2. Запустите проект:"
echo "   cd $INSTALL_DIR"
echo "   docker-compose up -d"
echo ""
echo "3. Протестируйте автоматическое обновление:"
echo "   systemctl start webkassa-key-update.service"
echo ""
echo "📊 Мониторинг:"
echo "- Логи: journalctl -u webkassa-key-update.service -f"
echo "- Статус: systemctl status webkassa-key-update.timer"
echo "- Файл логов: /var/log/webkassa-key-update.log"
echo ""
echo "⚠️ Не забудьте:"
echo "- Настроить .env файл с корректными credentials"
echo "- Проверить работу после настройки"
echo "- Настроить мониторинг логов"
