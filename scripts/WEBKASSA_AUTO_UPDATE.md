# Установка и настройка автоматического обновления API ключа Webkassa

## Описание

Данная система обеспечивает автоматическое обновление API ключа Webkassa каждый день в 5 утра через systemd timer или cron.

## Файлы системы

- `scripts/update_webkassa_key.py` - Python скрипт для обновления API ключа
- `scripts/update-webkassa-key.sh` - Bash обертка для запуска через Docker
- `scripts/webkassa-key-update.service` - Systemd service
- `scripts/webkassa-key-update.timer` - Systemd timer
- `scripts/webkassa-cron.txt` - Альтернативная cron задача

## Установка через systemd (рекомендуется)

### 1. Копирование файлов

```bash
# Копируем скрипт-обертку
sudo cp scripts/update-webkassa-key.sh /usr/local/bin/
sudo chmod +x /usr/local/bin/update-webkassa-key.sh

# Копируем systemd файлы
sudo cp scripts/webkassa-key-update.service /etc/systemd/system/
sudo cp scripts/webkassa-key-update.timer /etc/systemd/system/
```

### 2. Настройка переменных окружения

Добавьте в ваш `.env` файл:

```env
# Webkassa API конфигурация для автоматического обновления токена
WEBKASSA_LOGIN=your_webkassa_login
WEBKASSA_PASSWORD=your_webkassa_password
WEBKASSA_AUTH_URL=https://api.webkassa.kz/api/login
WEBKASSA_API_URL=https://api.webkassa.kz
```

### 3. Активация systemd timer

```bash
# Перезагружаем systemd
sudo systemctl daemon-reload

# Включаем и запускаем timer
sudo systemctl enable webkassa-key-update.timer
sudo systemctl start webkassa-key-update.timer

# Проверяем статус
sudo systemctl status webkassa-key-update.timer
```

### 4. Проверка работы

```bash
# Просмотр статуса timer
sudo systemctl list-timers webkassa-key-update.timer

# Тестовый запуск service
sudo systemctl start webkassa-key-update.service

# Просмотр логов
sudo journalctl -u webkassa-key-update.service -f
```

## Установка через cron (альтернатива)

### 1. Копирование скрипта

```bash
sudo cp scripts/update-webkassa-key.sh /usr/local/bin/
sudo chmod +x /usr/local/bin/update-webkassa-key.sh
```

### 2. Добавление в crontab

```bash
# Редактируем crontab root пользователя
sudo crontab -e

# Добавляем строку (каждый день в 5:00 утра):
0 5 * * * /usr/local/bin/update-webkassa-key.sh
```

## Мониторинг и логи

### Systemd логи

```bash
# Просмотр логов service
sudo journalctl -u webkassa-key-update.service

# Просмотр логов timer
sudo journalctl -u webkassa-key-update.timer

# Следить за логами в реальном времени
sudo journalctl -u webkassa-key-update.service -f
```

### Файлы логов

- `/var/log/webkassa-key-update.log` - Основные логи скрипта
- `/app/logs/webkassa_key_update.log` - Логи Python скрипта (внутри контейнера)

### Проверка статуса

```bash
# Статус timer
sudo systemctl status webkassa-key-update.timer

# Список всех timers
sudo systemctl list-timers

# Последнее выполнение
sudo systemctl show webkassa-key-update.timer -p LastTriggerUSec
```

## Тестирование

### Ручной запуск

```bash
# Через systemd
sudo systemctl start webkassa-key-update.service

# Напрямую
sudo /usr/local/bin/update-webkassa-key.sh

# Внутри Docker контейнера
docker-compose exec backend python /app/scripts/update_webkassa_key.py
```

### Проверка результата

```bash
# Проверяем обновление в базе данных
docker-compose exec db psql -U postgres -d altegio_webkassa_db -c "SELECT service_name, updated_at FROM api_keys WHERE service_name = 'Webkassa';"
```

## Устранение неполадок

### Общие проблемы

1. **Docker не запущен**

   ```bash
   sudo systemctl start docker
   ```

2. **Проект не запущен**

   ```bash
   cd /opt/altegio-webkassa-integration
   docker-compose up -d
   ```

3. **Неверные credentials**

   - Проверьте `WEBKASSA_LOGIN` и `WEBKASSA_PASSWORD` в `.env`

4. **Права доступа**
   ```bash
   sudo chmod +x /usr/local/bin/update-webkassa-key.sh
   ```

### Просмотр детальных логов

```bash
# Системные логи
sudo journalctl -u webkassa-key-update.service --since "24 hours ago"

# Логи Docker контейнера
docker-compose logs backend | grep webkassa

# Файловые логи
sudo tail -f /var/log/webkassa-key-update.log
```

## Отключение

### Systemd

```bash
# Останавливаем и отключаем timer
sudo systemctl stop webkassa-key-update.timer
sudo systemctl disable webkassa-key-update.timer

# Удаляем файлы
sudo rm /etc/systemd/system/webkassa-key-update.{service,timer}
sudo systemctl daemon-reload
```

### Cron

```bash
# Удаляем из crontab
sudo crontab -e
# Удалить строку с webkassa-key-update
```

## Безопасность

- Скрипт запускается от имени root для доступа к Docker
- Credentials хранятся в `.env` файле проекта
- Логи содержат только статус операций, не содержат чувствительных данных
- Рекомендуется настроить ротацию логов

## Мониторинг производительности

Рекомендуется настроить мониторинг:

1. **Успешность обновлений** - через журнал systemd
2. **Время выполнения** - через метрики systemd
3. **Ошибки авторизации** - через анализ логов
4. **Доступность Webkassa API** - через health checks
