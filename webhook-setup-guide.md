# Инструкция по настройке webhook для тестирования

## Вариант 1: Использование ngrok (рекомендуется)

### Установка ngrok:

1. Скачайте ngrok с официального сайта: https://ngrok.com/download
2. Или установите через winget: `winget install ngrok`
3. Или установите через chocolatey: `choco install ngrok`

### Создание туннеля:

1. Откройте новый терминал
2. Выполните команду:
   ```bash
   ngrok http 8000
   ```
3. Скопируйте HTTPS URL из вывода ngrok (например: https://abc123.ngrok.io)

### URL для webhook в Altegio:

- **Основной webhook**: `https://abc123.ngrok.io/webhook`
- **Тестовый webhook**: `https://abc123.ngrok.io/webhook/test`

## Вариант 2: Использование localtunnel

### Установка:

```bash
npm install -g localtunnel
```

### Создание туннеля:

```bash
lt --port 8000 --subdomain altegio-test
```

### URL для webhook:

- **Основной webhook**: `https://altegio-test.loca.lt/webhook`
- **Тестовый webhook**: `https://altegio-test.loca.lt/webhook/test`

## Вариант 3: Использование Cloudflare Tunnel

### Установка:

1. Скачайте cloudflared: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/
2. Выполните:
   ```bash
   cloudflared tunnel --url http://localhost:8000
   ```

## Настройка webhook в Altegio

1. Войдите в админ-панель Altegio
2. Перейдите в раздел "Интеграции" -> "Webhook"
3. Добавьте новый webhook:
   - **URL**: Ваш туннель URL + `/webhook/test` (для начального тестирования)
   - **События**: Выберите нужные события (например, "Запись создана", "Запись изменена")
   - **Метод**: POST
   - **Формат**: JSON

## Тестирование

### 1. Первичное тестирование:

- Используйте тестовый эндпоинт `/webhook/test`
- Этот эндпоинт логирует все данные и отправляет уведомление в Telegram

### 2. Проверка логов:

- Логи сохраняются в папку `./logs/errors.log`
- Также проверяйте Docker логи: `docker-compose logs -f backend`

### 3. Мониторинг:

- Все webhook будут отправлять уведомления в Telegram
- Проверьте чат с ботом для получения уведомлений

## Примеры запросов для ручного тестирования

### Тестовый запрос с curl:

```bash
curl -X POST https://your-tunnel.ngrok.io/webhook/test \
  -H "Content-Type: application/json" \
  -d '{"test": "data", "resource": "record", "resource_id": 123}'
```

### Проверка статуса сервера:

```bash
curl https://your-tunnel.ngrok.io/health
```

## Отладка

1. **Проверьте доступность сервера**:

   ```bash
   curl http://localhost:8000/health
   ```

2. **Проверьте логи Docker**:

   ```bash
   docker-compose logs -f backend
   ```

3. **Проверьте статус ngrok**:

   - Откройте http://localhost:4040 в браузере (веб-интерфейс ngrok)

4. **Тестирование webhook**:
   - Сначала используйте `/webhook/test`
   - После успешного тестирования переключитесь на `/webhook`

## После успешного тестирования

Когда тестирование пройдет успешно, замените в настройках Altegio:

- С: `https://your-tunnel.ngrok.io/webhook/test`
- На: `https://your-tunnel.ngrok.io/webhook`

## Conditions для обработки

Webhook будет обрабатываться только если:

1. `resource == "record"`
2. `comment` содержит "фч" (фискальный чек)
3. `paid_full == 1` (полная оплата)

Убедитесь, что тестовые записи в Altegio соответствуют этим условиям.
