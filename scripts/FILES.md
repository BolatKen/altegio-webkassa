# Структура файлов системы автоматического обновления API ключа Webkassa

## Файлы проекта

```
scripts/
├── update_webkassa_key.py          # Основной Python скрипт обновления
├── update-webkassa-key.sh          # Bash обертка для Docker
├── webkassa-key-update.service     # Systemd service
├── webkassa-key-update.timer       # Systemd timer
├── webkassa-cron.txt              # Альтернативная cron задача
├── install-auto-update.sh         # Скрипт автоматической установки
├── uninstall-auto-update.sh       # Скрипт удаления
├── check-status.sh                # Скрипт проверки статуса
├── README.md                      # Краткая инструкция
└── WEBKASSA_AUTO_UPDATE.md        # Подробная документация
```

## Системные файлы (после установки)

```
/usr/local/bin/update-webkassa-key.sh              # Исполняемый скрипт
/etc/systemd/system/webkassa-key-update.service    # Systemd service
/etc/systemd/system/webkassa-key-update.timer      # Systemd timer
/var/log/webkassa-key-update.log                   # Основные логи
/opt/altegio-webkassa-integration/                 # Копия проекта
```

## Команды управления

### Установка

```bash
sudo scripts/install-auto-update.sh
```

### Проверка статуса

```bash
scripts/check-status.sh
sudo systemctl status webkassa-key-update.timer
```

### Мониторинг

```bash
sudo journalctl -u webkassa-key-update.service -f
```

### Ручной запуск

```bash
sudo systemctl start webkassa-key-update.service
```

### Удаление

```bash
sudo scripts/uninstall-auto-update.sh
```

## Переменные окружения

Добавьте в `.env`:

```env
WEBKASSA_LOGIN=your_webkassa_login
WEBKASSA_PASSWORD=your_webkassa_password
WEBKASSA_AUTH_URL=https://api.webkassa.kz/api/login
```

## Логи

- **Systemd**: `journalctl -u webkassa-key-update.service`
- **Файл**: `/var/log/webkassa-key-update.log`
- **Python скрипт**: `/app/logs/webkassa_key_update.log` (внутри контейнера)

## Расписание

- **Время**: каждый день в 5:00 утра
- **Случайная задержка**: до 30 минут
- **Persistent**: запустится после перезагрузки, если пропущен
