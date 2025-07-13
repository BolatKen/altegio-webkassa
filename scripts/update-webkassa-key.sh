#!/bin/bash
# Скрипт-обертка для запуска обновления API ключа Webkassa через Docker
# Файл: /usr/local/bin/update-webkassa-key.sh

set -e

# Логирование
LOG_FILE="/var/log/webkassa-key-update.log"
SCRIPT_DIR="/opt/altegio-webkassa-integration"

# Функция логирования
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "Starting Webkassa API key update process"

# Проверяем, что Docker Compose проект запущен
if ! docker-compose -f "$SCRIPT_DIR/docker-compose.yml" ps | grep -q "Up"; then
    log "ERROR: Docker Compose services are not running"
    exit 1
fi

# Запускаем скрипт обновления внутри контейнера
log "Executing update script in backend container"
docker-compose -f "$SCRIPT_DIR/docker-compose.yml" exec -T backend python /app/scripts/update_webkassa_key.py

if [ $? -eq 0 ]; then
    log "✅ Webkassa API key update completed successfully"
else
    log "❌ Webkassa API key update failed"
    exit 1
fi

log "Webkassa API key update process finished"
