# Altegio-Webkassa Integration

Базовый проект на FastAPI для интеграции между Altegio (источник webhook-ов) и Webkassa (фискализация чеков).

## 🚀 Описание

Этот проект представляет собой микросервис для обработки webhook-запросов от системы записи Altegio и последующей фискализации данных через API Webkassa. Проект готов к развертыванию на VPS-сервере с использованием Docker и Docker Compose.

## 🏗️ Архитектура

- **Backend**: FastAPI с асинхронной обработкой
- **База данных**: PostgreSQL с SQLAlchemy ORM
- **Frontend**: HTML шаблоны с Jinja2
- **Reverse Proxy**: Nginx
- **Контейнеризация**: Docker + Docker Compose

## 📁 Структура проекта

```
altegio-webkassa-integration/
├── app/                          # Основное приложение
│   ├── main.py                   # Точка входа FastAPI
│   ├── db.py                     # Настройка базы данных
│   ├── models.py                 # Модели SQLAlchemy
│   ├── routes/                   # Маршруты API
│   │   ├── webhook.py            # Обработка webhook от Altegio
│   │   └── acquire.py            # Frontend страницы
│   ├── schemas/                  # Pydantic схемы
│   │   └── altegio.py            # Схемы для валидации Altegio
│   ├── templates/                # HTML шаблоны
│   │   ├── acquire.html          # Страница оплаты
│   │   └── success.html          # Страница успеха
│   └── static/                   # Статические файлы
│       ├── css/style.css         # Стили
│       └── js/payment.js         # JavaScript
├── nginx/                        # Конфигурация Nginx
│   ├── default.conf              # Основная конфигурация
│   └── ssl/                      # SSL сертификаты
├── logs/                         # Логи приложения
├── docker-compose.yml            # Конфигурация Docker Compose
├── Dockerfile                    # Образ для backend
├── requirements.txt              # Python зависимости
├── .env                          # Переменные окружения
└── README.md                     # Документация
```



## 🔧 Требования

### Системные требования

- **CPU**: 1 ядро @ 3.3 GHz (минимум)
- **RAM**: 2 GB (рекомендуется)
- **Диск**: 30 GB NVMe
- **ОС**: Ubuntu 20.04+ / CentOS 7+ / Debian 10+

### Программное обеспечение

- Docker 20.10+
- Docker Compose 2.0+
- Git

## 🚀 Быстрый старт

### 1. Клонирование проекта

```bash
git clone <repository-url>
cd altegio-webkassa-integration
```

### 2. Настройка переменных окружения

Скопируйте и отредактируйте файл `.env`:

```bash
cp .env.example .env
nano .env
```

Основные переменные для настройки:

```env
# База данных
POSTGRES_DB=altegio_webkassa_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password_here

# Приложение
DEBUG=False
SECRET_KEY=your_super_secret_key_here

# Altegio
ALTEGIO_WEBHOOK_SECRET=your_altegio_webhook_secret

# Webkassa (TODO: настроить при интеграции)
WEBKASSA_API_TOKEN=your_webkassa_token
WEBKASSA_SHOP_ID=your_shop_id
```

### 3. Запуск проекта

```bash
# Сборка и запуск всех сервисов
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Проверка статуса
docker-compose ps
```

### 4. Проверка работоспособности

После запуска сервисы будут доступны по адресам:

- **Основное приложение**: http://localhost
- **API документация**: http://localhost/docs
- **Страница оплаты**: http://localhost/acquire
- **Health check**: http://localhost/health

## 🔗 API Endpoints

### Webhook от Altegio

```http
POST /api/webhook
Content-Type: application/json

{
  "company_id": 307626,
  "resource": "record",
  "resource_id": 596792978,
  "status": "update",
  "data": {
    "id": 596792978,
    "date": "2025-07-12 12:10:00",
    "comment": "фч",
    "services": [
      {
        "title": "Стрижка детская",
        "cost": 4000
      }
    ],
    "client": {
      "name": "Вячослав",
      "phone": "+77770220606"
    }
  }
}
```

### Проверка статуса webhook

```http
GET /api/webhook/status/{record_id}
```

### Страница оплаты

```http
GET /acquire
```


## 🌐 Развертывание в продакшене

### 1. Подготовка сервера

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Установка Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. Настройка SSL (Let's Encrypt)

```bash
# Установка Certbot
sudo apt install certbot python3-certbot-nginx

# Получение сертификата
sudo certbot --nginx -d your-domain.com

# Настройка автообновления
echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -
```

### 3. Настройка файрвола

```bash
# UFW (Ubuntu)
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable

# Или iptables
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
```

### 4. Мониторинг и логи

```bash
# Просмотр логов
docker-compose logs -f backend
docker-compose logs -f nginx
docker-compose logs -f db

# Мониторинг ресурсов
docker stats

# Резервное копирование БД
docker-compose exec db pg_dump -U postgres altegio_webkassa_db > backup.sql
```

## 🛠️ Разработка

### Локальная разработка

```bash
# Клонирование проекта
git clone <repository-url>
cd altegio-webkassa-integration

# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt

# Запуск только базы данных
docker-compose up -d db

# Запуск приложения локально
cd app
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Тестирование webhook

```bash
# Тестовый запрос к webhook
curl -X POST http://localhost:8000/api/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": 307626,
    "resource": "record",
    "resource_id": 596792978,
    "status": "create",
    "data": {
      "id": 596792978,
      "date": "2025-07-12 12:10:00",
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
  }'
```

### Структура базы данных

Основные таблицы:

- **webhook_records** - записи webhook от Altegio
- **payment_records** - информация о платежах
- **fiscalization_logs** - логи фискализации Webkassa

## 🔧 TODO: Интеграция с Webkassa

Для завершения интеграции с Webkassa необходимо:

### 1. Настройка API Webkassa

```python
# В app/routes/webhook.py
async def send_to_webkassa(fiscalization_data):
    """
    Отправка данных в Webkassa API
    """
    webkassa_url = os.getenv("WEBKASSA_API_URL")
    api_token = os.getenv("WEBKASSA_API_TOKEN")
    
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{webkassa_url}/api/receipts",
            json=fiscalization_data,
            headers=headers
        )
        return response.json()
```

### 2. Маппинг данных Altegio → Webkassa

```python
def prepare_webkassa_data(payload: AltegioWebhookPayload) -> Dict[str, Any]:
    """
    Подготовка данных для Webkassa
    """
    return {
        "external_id": f"altegio_{payload.resource_id}",
        "cashier": {
            "name": "Система Altegio",
            "vatin": "123456789012"
        },
        "client": {
            "name": payload.data.client.name,
            "phone": payload.data.client.phone
        },
        "items": [
            {
                "name": service.title,
                "price": service.cost / 100,
                "quantity": 1,
                "total": service.cost / 100,
                "tax": "VAT_12"  # НДС 12%
            }
            for service in payload.data.services
        ],
        "payments": [
            {
                "type": "CARD",
                "amount": sum(s.cost for s in payload.data.services) / 100
            }
        ]
    }
```

### 3. Обработка ошибок и повторные попытки

```python
async def process_fiscalization_with_retry(webhook_record, max_retries=3):
    """
    Фискализация с повторными попытками
    """
    for attempt in range(max_retries):
        try:
            result = await send_to_webkassa(fiscalization_data)
            # Обновление статуса в БД
            webhook_record.processed = True
            webhook_record.webkassa_response = result
            await db.commit()
            break
        except Exception as e:
            if attempt == max_retries - 1:
                # Последняя попытка - сохраняем ошибку
                webhook_record.processing_error = str(e)
                await db.commit()
            else:
                # Ждем перед повторной попыткой
                await asyncio.sleep(2 ** attempt)
```


## 🐛 Устранение неполадок

### Проблемы с запуском

```bash
# Проверка статуса контейнеров
docker-compose ps

# Просмотр логов
docker-compose logs backend
docker-compose logs db
docker-compose logs nginx

# Перезапуск сервисов
docker-compose restart

# Полная пересборка
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Проблемы с базой данных

```bash
# Подключение к PostgreSQL
docker-compose exec db psql -U postgres -d altegio_webkassa_db

# Проверка таблиц
\dt

# Просмотр записей webhook
SELECT * FROM webhook_records ORDER BY created_at DESC LIMIT 10;
```

### Проблемы с Nginx

```bash
# Проверка конфигурации
docker-compose exec nginx nginx -t

# Перезагрузка конфигурации
docker-compose exec nginx nginx -s reload

# Просмотр логов доступа
docker-compose exec nginx tail -f /var/log/nginx/access.log
```

### Мониторинг производительности

```bash
# Использование ресурсов
docker stats

# Размер логов
du -sh logs/

# Размер базы данных
docker-compose exec db du -sh /var/lib/postgresql/data
```

## 📊 Мониторинг и метрики

### Health Check endpoints

- `GET /health` - общее состояние сервиса
- `GET /api/webhook/status/{id}` - статус обработки webhook

### Логирование

Логи сохраняются в:
- `logs/errors.log` - ошибки приложения
- Nginx access/error logs в контейнере
- PostgreSQL logs в контейнере

### Рекомендуемые метрики для мониторинга

- Количество обработанных webhook в минуту
- Время ответа API endpoints
- Использование CPU и памяти
- Размер базы данных
- Количество ошибок фискализации

## 🔒 Безопасность

### Рекомендации

1. **Изменить пароли по умолчанию** в `.env`
2. **Настроить SSL сертификаты** для HTTPS
3. **Ограничить доступ к портам** через файрвол
4. **Регулярно обновлять** Docker образы
5. **Настроить резервное копирование** базы данных
6. **Использовать секреты** для чувствительных данных

### Проверка webhook подписи

```python
import hmac
import hashlib

def verify_altegio_signature(payload, signature, secret):
    """
    Проверка подписи webhook от Altegio
    """
    expected_signature = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)
```

## 📝 Changelog

### v1.0.0 (2025-07-12)

- ✅ Базовая структура FastAPI приложения
- ✅ Обработка webhook от Altegio
- ✅ Модели базы данных PostgreSQL
- ✅ HTML страница оплаты
- ✅ Docker и Docker Compose конфигурация
- ✅ Nginx reverse proxy
- ✅ SSL готовность
- 🔄 TODO: Интеграция с Webkassa API
- 🔄 TODO: Обработка платежей
- 🔄 TODO: Уведомления и отчеты

## 🤝 Участие в разработке

1. Fork проекта
2. Создайте feature branch (`git checkout -b feature/amazing-feature`)
3. Commit изменения (`git commit -m 'Add amazing feature'`)
4. Push в branch (`git push origin feature/amazing-feature`)
5. Создайте Pull Request

## 📄 Лицензия

Этот проект распространяется под лицензией MIT. См. файл `LICENSE` для подробностей.

## 📞 Поддержка

Если у вас возникли вопросы или проблемы:

1. Проверьте раздел [Устранение неполадок](#-устранение-неполадок)
2. Создайте Issue в репозитории
3. Обратитесь к документации API Altegio и Webkassa

---

**Создано с ❤️ для интеграции Altegio и Webkassa**

