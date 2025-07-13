# Автоматическое обновление API ключа Webkassa

## Быстрый старт

### 1. Автоматическая установка

```bash
# Делаем скрипт установки исполняемым
chmod +x scripts/install-auto-update.sh

# Запускаем установку от имени root
sudo scripts/install-auto-update.sh
```

### 2. Настройка credentials

Отредактируйте `.env` файл и добавьте:

```env
# Webkassa credentials для автоматического обновления
WEBKASSA_LOGIN=your_webkassa_login
WEBKASSA_PASSWORD=your_webkassa_password
WEBKASSA_AUTH_URL=https://api.webkassa.kz/api/login
```

### 3. Перезапуск проекта

```bash
docker-compose down
docker-compose up -d
```

### 4. Тестирование

```bash
# Ручной запуск обновления
sudo systemctl start webkassa-key-update.service

# Проверка логов
sudo journalctl -u webkassa-key-update.service -f
```

## Статус и мониторинг

```bash
# Статус timer
sudo systemctl status webkassa-key-update.timer

# Когда будет следующий запуск
sudo systemctl list-timers webkassa-key-update.timer

# Логи последних запусков
sudo journalctl -u webkassa-key-update.service --since "7 days ago"
```

## Отключение

```bash
# Остановка и отключение
sudo systemctl stop webkassa-key-update.timer
sudo systemctl disable webkassa-key-update.timer
```

## Расписание

- **Время запуска**: каждый день в 5:00 утра
- **Случайная задержка**: до 30 минут (для снижения нагрузки на API)
- **Persistent**: если система была выключена, запустится при включении

## Логи

- **Systemd**: `journalctl -u webkassa-key-update.service`
- **Файл**: `/var/log/webkassa-key-update.log`
- **Docker**: `docker-compose logs backend | grep webkassa`
