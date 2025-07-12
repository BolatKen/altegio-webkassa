# Примеры использования API

## Webhook от Altegio

### Пример 1: Создание новой записи

```bash
curl -X POST http://localhost/api/webhook \
  -H "Content-Type: application/json" \
  -H "X-Altegio-Signature: your_signature_here" \
  -d '{
    "company_id": 307626,
    "resource": "record",
    "resource_id": 596792978,
    "status": "create",
    "data": {
      "id": 596792978,
      "date": "2025-07-12 14:30:00",
      "comment": "Первое посещение",
      "services": [
        {
          "title": "Стрижка мужская",
          "cost": 3000
        },
        {
          "title": "Укладка",
          "cost": 1500
        }
      ],
      "client": {
        "name": "Иван Петров",
        "phone": "+77771234567"
      }
    }
  }'
```

### Пример 2: Обновление записи

```bash
curl -X POST http://localhost/api/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": 307626,
    "resource": "record",
    "resource_id": 596792978,
    "status": "update",
    "data": {
      "id": 596792978,
      "date": "2025-07-12 15:00:00",
      "comment": "Перенос времени",
      "services": [
        {
          "title": "Стрижка мужская",
          "cost": 3000
        }
      ],
      "client": {
        "name": "Иван Петров",
        "phone": "+77771234567"
      }
    }
  }'
```

### Пример 3: Отмена записи

```bash
curl -X POST http://localhost/api/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": 307626,
    "resource": "record",
    "resource_id": 596792978,
    "status": "delete",
    "data": {
      "id": 596792978,
      "date": "2025-07-12 15:00:00",
      "comment": "Отмена клиентом",
      "services": [],
      "client": {
        "name": "Иван Петров",
        "phone": "+77771234567"
      }
    }
  }'
```

## Проверка статуса обработки

```bash
# Получение статуса webhook по ID
curl -X GET http://localhost/api/webhook/status/1

# Ответ:
{
  "id": 1,
  "resource_id": 596792978,
  "processed": true,
  "created_at": "2025-07-12T12:10:00",
  "client_phone": "+77771234567",
  "status": "create"
}
```

## Health Check

```bash
# Проверка здоровья сервиса
curl -X GET http://localhost/health

# Ответ:
{
  "status": "healthy",
  "service": "altegio-webkassa-integration"
}
```

## Тестирование формы оплаты

### Заполнение формы через браузер

1. Откройте http://localhost/acquire
2. Заполните форму:
   - Имя: "Тестовый клиент"
   - Телефон: "+7 (777) 123-45-67"
   - Email: "test@example.com"
   - Способ оплаты: "Банковская карта"
3. Нажмите "Оплатить"

### Отправка данных формы через API

```bash
curl -X POST http://localhost/acquire/payment \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_name=Тестовый клиент&client_phone=+7 (777) 123-45-67&client_email=test@example.com&payment_method=card"
```

## Python примеры

### Отправка webhook

```python
import requests
import json

def send_altegio_webhook(webhook_data):
    url = "http://localhost/api/webhook"
    headers = {
        "Content-Type": "application/json",
        "X-Altegio-Signature": "your_signature_here"
    }
    
    response = requests.post(url, json=webhook_data, headers=headers)
    return response.json()

# Пример использования
webhook_data = {
    "company_id": 307626,
    "resource": "record",
    "resource_id": 596792978,
    "status": "create",
    "data": {
        "id": 596792978,
        "date": "2025-07-12 14:30:00",
        "comment": "Тестовая запись",
        "services": [
            {
                "title": "Стрижка детская",
                "cost": 4000
            }
        ],
        "client": {
            "name": "Тестовый клиент",
            "phone": "+77770220606"
        }
    }
}

result = send_altegio_webhook(webhook_data)
print(result)
```

### Проверка статуса

```python
import requests

def check_webhook_status(record_id):
    url = f"http://localhost/api/webhook/status/{record_id}"
    response = requests.get(url)
    return response.json()

# Пример использования
status = check_webhook_status(1)
print(f"Статус обработки: {status['processed']}")
```

## JavaScript примеры

### Отправка webhook через fetch

```javascript
async function sendWebhook(webhookData) {
    const response = await fetch('/api/webhook', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Altegio-Signature': 'your_signature_here'
        },
        body: JSON.stringify(webhookData)
    });
    
    return await response.json();
}

// Пример использования
const webhookData = {
    company_id: 307626,
    resource: "record",
    resource_id: 596792978,
    status: "create",
    data: {
        id: 596792978,
        date: "2025-07-12 14:30:00",
        comment: "Тестовая запись",
        services: [
            {
                title: "Стрижка детская",
                cost: 4000
            }
        ],
        client: {
            name: "Тестовый клиент",
            phone: "+77770220606"
        }
    }
};

sendWebhook(webhookData)
    .then(result => console.log(result))
    .catch(error => console.error(error));
```

## Мониторинг и отладка

### Просмотр логов в реальном времени

```bash
# Логи backend
docker-compose logs -f backend

# Логи базы данных
docker-compose logs -f db

# Логи Nginx
docker-compose logs -f nginx
```

### Подключение к базе данных

```bash
# Подключение к PostgreSQL
docker-compose exec db psql -U postgres -d altegio_webkassa_db

# Просмотр всех webhook записей
SELECT id, resource_id, client_phone, processed, created_at 
FROM webhook_records 
ORDER BY created_at DESC;

# Поиск записей по телефону
SELECT * FROM webhook_records 
WHERE client_phone = '+77770220606';

# Статистика обработки
SELECT 
    status,
    processed,
    COUNT(*) as count
FROM webhook_records 
GROUP BY status, processed;
```

