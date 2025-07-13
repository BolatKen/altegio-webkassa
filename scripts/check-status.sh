#!/bin/bash
# Скрипт для проверки статуса системы автоматического обновления API ключа Webkassa
# Файл: scripts/check-status.sh

set -e

echo "🔍 Проверка статуса системы автоматического обновления Webkassa API"
echo "=================================================================="

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для вывода статуса
print_status() {
    local status=$1
    local message=$2
    
    if [ "$status" = "OK" ]; then
        echo -e "${GREEN}✅ $message${NC}"
    elif [ "$status" = "WARNING" ]; then
        echo -e "${YELLOW}⚠️  $message${NC}"
    else
        echo -e "${RED}❌ $message${NC}"
    fi
}

# Проверяем systemd timer
echo -e "\n${BLUE}🔹 Systemd Timer Status${NC}"
echo "------------------------"

if systemctl is-active --quiet webkassa-key-update.timer; then
    print_status "OK" "Timer активен"
else
    print_status "ERROR" "Timer не активен"
fi

if systemctl is-enabled --quiet webkassa-key-update.timer; then
    print_status "OK" "Timer включен для автозапуска"
else
    print_status "ERROR" "Timer не включен для автозапуска"
fi

# Показываем следующий запуск
echo -e "\n${BLUE}🔹 Расписание запуска${NC}"
echo "---------------------"
systemctl list-timers webkassa-key-update.timer --no-pager | tail -n +2

# Проверяем последние логи
echo -e "\n${BLUE}🔹 Последние выполнения${NC}"
echo "------------------------"
if journalctl -u webkassa-key-update.service --since "7 days ago" --no-pager | grep -q "Starting"; then
    print_status "OK" "Есть записи о запуске за последние 7 дней"
    echo "Последние запуски:"
    journalctl -u webkassa-key-update.service --since "7 days ago" --no-pager | grep "Starting\|completed\|failed" | tail -5
else
    print_status "WARNING" "Нет записей о запуске за последние 7 дней"
fi

# Проверяем успешность последнего выполнения
echo -e "\n${BLUE}🔹 Последний результат${NC}"
echo "-----------------------"
last_log=$(journalctl -u webkassa-key-update.service -n 20 --no-pager | grep -E "(completed successfully|failed|ERROR)" | tail -1)
if echo "$last_log" | grep -q "completed successfully"; then
    print_status "OK" "Последнее выполнение успешно"
elif echo "$last_log" | grep -q "failed\|ERROR"; then
    print_status "ERROR" "Последнее выполнение завершилось с ошибкой"
    echo "Ошибка: $last_log"
else
    print_status "WARNING" "Статус последнего выполнения неизвестен"
fi

# Проверяем Docker проект
echo -e "\n${BLUE}🔹 Docker Project Status${NC}"
echo "-------------------------"
PROJECT_DIR="/opt/altegio-webkassa-integration"
if [ -f "$PROJECT_DIR/docker-compose.yml" ]; then
    cd "$PROJECT_DIR"
    if docker-compose ps | grep -q "Up"; then
        print_status "OK" "Docker контейнеры запущены"
    else
        print_status "ERROR" "Docker контейнеры не запущены"
    fi
else
    print_status "ERROR" "Проект не найден в $PROJECT_DIR"
fi

# Проверяем API ключ в базе данных
echo -e "\n${BLUE}🔹 Database API Key Status${NC}"
echo "---------------------------"
if [ -f "$PROJECT_DIR/docker-compose.yml" ]; then
    cd "$PROJECT_DIR"
    if docker-compose ps | grep -q "db.*Up"; then
        api_key_info=$(docker-compose exec -T db psql -U postgres -d altegio_webkassa_db -t -c "SELECT service_name, updated_at FROM api_keys WHERE service_name = 'Webkassa';" 2>/dev/null || echo "ERROR")
        
        if [ "$api_key_info" != "ERROR" ] && [ -n "$api_key_info" ]; then
            print_status "OK" "API ключ найден в базе данных"
            echo "Детали: $api_key_info"
        else
            print_status "WARNING" "API ключ не найден в базе данных"
        fi
    else
        print_status "ERROR" "База данных не доступна"
    fi
fi

# Проверяем файлы системы
echo -e "\n${BLUE}🔹 System Files Status${NC}"
echo "-----------------------"

files_to_check=(
    "/usr/local/bin/update-webkassa-key.sh"
    "/etc/systemd/system/webkassa-key-update.service"
    "/etc/systemd/system/webkassa-key-update.timer"
    "/var/log/webkassa-key-update.log"
)

for file in "${files_to_check[@]}"; do
    if [ -f "$file" ]; then
        print_status "OK" "Найден: $file"
    else
        print_status "ERROR" "Отсутствует: $file"
    fi
done

# Проверяем переменные окружения
echo -e "\n${BLUE}🔹 Environment Variables${NC}"
echo "-------------------------"
if [ -f "$PROJECT_DIR/.env" ]; then
    if grep -q "WEBKASSA_LOGIN" "$PROJECT_DIR/.env"; then
        print_status "OK" "WEBKASSA_LOGIN настроен"
    else
        print_status "ERROR" "WEBKASSA_LOGIN не настроен"
    fi
    
    if grep -q "WEBKASSA_PASSWORD" "$PROJECT_DIR/.env"; then
        print_status "OK" "WEBKASSA_PASSWORD настроен"
    else
        print_status "ERROR" "WEBKASSA_PASSWORD не настроен"
    fi
    
    if grep -q "WEBKASSA_AUTH_URL" "$PROJECT_DIR/.env"; then
        print_status "OK" "WEBKASSA_AUTH_URL настроен"
    else
        print_status "WARNING" "WEBKASSA_AUTH_URL не настроен (будет использован по умолчанию)"
    fi
else
    print_status "ERROR" ".env файл не найден"
fi

# Итоговый статус
echo -e "\n${BLUE}📊 Сводка${NC}"
echo "=========="

# Тестовый запуск (только статус, не выполняем)
echo -e "\n${YELLOW}💡 Для тестового запуска выполните:${NC}"
echo "sudo systemctl start webkassa-key-update.service"
echo ""
echo -e "${YELLOW}💡 Для просмотра логов в реальном времени:${NC}"
echo "sudo journalctl -u webkassa-key-update.service -f"
echo ""
echo -e "${YELLOW}💡 Для отключения автоматического обновления:${NC}"
echo "sudo systemctl stop webkassa-key-update.timer"
echo "sudo systemctl disable webkassa-key-update.timer"
