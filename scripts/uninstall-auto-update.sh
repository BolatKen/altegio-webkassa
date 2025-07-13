#!/bin/bash
# Скрипт для удаления системы автоматического обновления API ключа Webkassa
# Файл: scripts/uninstall-auto-update.sh

set -e

echo "🗑️  Удаление системы автоматического обновления API ключа Webkassa"
echo "================================================================="

# Проверяем права root
if [[ $EUID -ne 0 ]]; then
   echo "❌ Этот скрипт должен запускаться от имени root (sudo)"
   exit 1
fi

echo "⚠️  ВНИМАНИЕ: Это удалит все компоненты автоматического обновления!"
echo "Продолжить? (y/N)"
read -r response

if [[ ! "$response" =~ ^[Yy]$ ]]; then
    echo "❌ Отменено пользователем"
    exit 0
fi

echo "🔄 Начинаем удаление..."

# Останавливаем и отключаем timer
echo "⏹️  Останавливаем и отключаем systemd timer..."
if systemctl is-active --quiet webkassa-key-update.timer; then
    systemctl stop webkassa-key-update.timer
    echo "✅ Timer остановлен"
fi

if systemctl is-enabled --quiet webkassa-key-update.timer; then
    systemctl disable webkassa-key-update.timer
    echo "✅ Timer отключен"
fi

# Удаляем systemd файлы
echo "🗂️  Удаляем systemd файлы..."
files_to_remove=(
    "/etc/systemd/system/webkassa-key-update.service"
    "/etc/systemd/system/webkassa-key-update.timer"
)

for file in "${files_to_remove[@]}"; do
    if [ -f "$file" ]; then
        rm "$file"
        echo "✅ Удален: $file"
    else
        echo "ℹ️  Уже отсутствует: $file"
    fi
done

# Перезагружаем systemd
echo "🔄 Перезагружаем systemd..."
systemctl daemon-reload
echo "✅ Systemd перезагружен"

# Удаляем скрипт-обертку
echo "📜 Удаляем скрипт-обертку..."
if [ -f "/usr/local/bin/update-webkassa-key.sh" ]; then
    rm "/usr/local/bin/update-webkassa-key.sh"
    echo "✅ Удален: /usr/local/bin/update-webkassa-key.sh"
else
    echo "ℹ️  Уже отсутствует: /usr/local/bin/update-webkassa-key.sh"
fi

# Удаляем логи (спрашиваем пользователя)
echo ""
echo "🗂️  Удалить файлы логов? (y/N)"
read -r log_response

if [[ "$log_response" =~ ^[Yy]$ ]]; then
    log_files=(
        "/var/log/webkassa-key-update.log"
        "/var/log/webkassa-cron.log"
    )
    
    for log_file in "${log_files[@]}"; do
        if [ -f "$log_file" ]; then
            rm "$log_file"
            echo "✅ Удален лог: $log_file"
        fi
    done
else
    echo "ℹ️  Файлы логов сохранены"
fi

# Проверяем crontab на наличие записей
echo ""
echo "🔍 Проверяем crontab на наличие записей Webkassa..."
if crontab -l 2>/dev/null | grep -q "webkassa\|update-webkassa-key"; then
    echo "⚠️  Найдены записи в crontab. Удалите их вручную:"
    echo "   sudo crontab -e"
    echo "   Найдите и удалите строки содержащие 'webkassa' или 'update-webkassa-key'"
else
    echo "✅ Записи в crontab не найдены"
fi

echo ""
echo "🎉 Удаление завершено!"
echo "======================"
echo ""
echo "📋 Что было удалено:"
echo "- systemd service и timer"
echo "- Скрипт-обертка"
if [[ "$log_response" =~ ^[Yy]$ ]]; then
    echo "- Файлы логов"
fi
echo ""
echo "📋 Что осталось:"
echo "- Python скрипт: scripts/update_webkassa_key.py"
echo "- Проект в /opt/altegio-webkassa-integration (если есть)"
echo "- Переменные окружения в .env"
echo ""
echo "ℹ️  Для полного удаления проекта выполните:"
echo "   sudo rm -rf /opt/altegio-webkassa-integration"
echo ""
echo "ℹ️  Для повторной установки запустите:"
echo "   sudo scripts/install-auto-update.sh"
