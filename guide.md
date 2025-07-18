# Руководство по реализации бизнес-логики в проекте FastAPI

## Введение

Это руководство предназначено для помощи в реализации вашей бизнес-логики в проекте FastAPI, который был создан для интеграции Altegio и Webkassa. Мы подробно рассмотрим ключевые аспекты FastAPI, такие как Pydantic схемы для валидации данных, а также методы мониторинга и тестирования запросов, чтобы вы могли эффективно разрабатывать и отлаживать ваше приложение.

## 1. Pydantic Схемы: Валидация и Сериализация Данных

### Что такое Pydantic?

Pydantic — это библиотека для Python, которая позволяет определять схемы данных с использованием стандартных аннотаций типов Python. Она обеспечивает валидацию данных во время выполнения и сериализацию/десериализацию данных. В контексте FastAPI, Pydantic является основой для обработки входящих запросов (JSON, формы) и формирования исходящих ответов.

FastAPI автоматически использует Pydantic для:

1.  **Валидации входящих данных**: Когда ваш API-эндпоинт получает данные (например, JSON в теле POST-запроса), FastAPI использует Pydantic-схему, чтобы убедиться, что полученные данные соответствуют ожидаемой структуре и типам. Если данные не соответствуют схеме, FastAPI автоматически возвращает ошибку валидации (HTTP 422 Unprocessable Entity) с подробным описанием проблемы, что значительно упрощает разработку и отладку.
2.  **Сериализации исходящих данных**: Когда ваш эндпоинт возвращает данные (например, объект Python), FastAPI использует Pydantic-схему, чтобы преобразовать эти данные в формат, который может быть отправлен клиенту (обычно JSON). Это гарантирует, что ответ всегда будет иметь предсказуемую структуру и типы данных.
3.  **Генерации документации API**: Pydantic-схемы используются FastAPI для автоматической генерации интерактивной документации API (Swagger UI и ReDoc). Это позволяет разработчикам легко понимать, какие данные ожидаются на вход и какие данные будут возвращены на выход.

### Как работают Pydantic схемы?

В проекте, который я для вас создал, Pydantic схемы определены в файле `app/schemas/altegio.py`. Давайте рассмотрим пример `AltegioWebhookPayload`:

```python
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class AltegioClient(BaseModel):
    name: str = Field(..., description="Имя клиента")
    phone: str = Field(..., description="Телефон клиента")


class AltegioService(BaseModel):
    title: str = Field(..., description="Название услуги")
    cost: int = Field(..., description="Стоимость услуги в копейках")


class AltegioRecordData(BaseModel):
    id: int = Field(..., description="ID записи")
    date: str = Field(..., description="Дата и время записи")
    comment: Optional[str] = Field(None, description="Комментарий к записи")
    services: List[AltegioService] = Field(..., description="Список услуг")
    client: AltegioClient = Field(..., description="Данные клиента")


class AltegioWebhookPayload(BaseModel):
    company_id: int = Field(..., description="ID компании в Altegio")
    resource: str = Field(..., description="Тип ресурса (record, client, etc.)")
    resource_id: int = Field(..., description="ID ресурса")
    status: str = Field(..., description="Статус операции (create, update, delete)")
    data: AltegioRecordData = Field(..., description="Данные записи")

    class Config:
        json_schema_extra = {
            "example": {
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
        }
```

**Ключевые моменты:**

*   **`BaseModel`**: Все Pydantic схемы наследуются от `pydantic.BaseModel`. Это базовый класс, который предоставляет функциональность валидации и сериализации.
*   **Аннотации типов Python**: Вы используете стандартные аннотации типов (например, `str`, `int`, `List[AltegioService]`, `Optional[str]`) для определения ожидаемого типа данных для каждого поля. Pydantic использует эти аннотации для валидации.
*   **`Field`**: Функция `pydantic.Field` используется для добавления дополнительной информации о поле, такой как описание (`description`), значение по умолчанию, или для указания, что поле является обязательным (`...`).
*   **Вложенные схемы**: Вы можете вкладывать Pydantic схемы друг в друга. Например, `AltegioWebhookPayload` содержит поле `data` типа `AltegioRecordData`, которое, в свою очередь, содержит `services` (список `AltegioService`) и `client` (`AltegioClient`). Это позволяет создавать сложные, но строго типизированные структуры данных.
*   **`Config` и `json_schema_extra`**: Вложенный класс `Config` позволяет настраивать поведение Pydantic. `json_schema_extra` используется для предоставления примера JSON-данных, который будет отображаться в документации Swagger UI. Это очень полезно для разработчиков, использующих ваш API.

### Зачем нужны Pydantic схемы?

1.  **Автоматическая валидация данных**: Это самая важная причина. Вам не нужно писать код для проверки, является ли `company_id` целым числом, или содержит ли `services` список объектов с `title` и `cost`. Pydantic делает это за вас. Если входящие данные не соответствуют схеме, FastAPI автоматически отклонит запрос с понятной ошибкой.
2.  **Чистый и читаемый код**: Определяя схемы данных отдельно, вы делаете ваш код более модульным и легким для понимания. Логика валидации отделена от бизнес-логики.
3.  **Автоматическая документация API**: Как уже упоминалось, FastAPI использует Pydantic схемы для генерации интерактивной документации. Это значительно сокращает время на написание и поддержку документации вручную.
4.  **Улучшенная автодополнение и проверка типов (IDE support)**: Благодаря аннотациям типов, ваша IDE (например, VS Code, PyCharm) может предоставлять более точное автодополнение и выявлять потенциальные ошибки типов еще до запуска кода.
5.  **Преобразование данных**: Pydantic может автоматически преобразовывать данные из одного типа в другой, если это возможно (например, строку 


в число, если она содержит только цифры). Это упрощает работу с данными, поступающими из разных источников.

### Использование Pydantic схем в FastAPI эндпоинтах

В вашем проекте, в файле `app/routes/webhook.py`, вы увидите, как Pydantic схема `AltegioWebhookPayload` используется в эндпоинте `handle_altegio_webhook`:

```python
from fastapi import APIRouter, HTTPException, Depends, Request
from app.schemas.altegio import AltegioWebhookPayload, WebhookResponse

router = APIRouter()

@router.post("/webhook", response_model=WebhookResponse)
async def handle_altegio_webhook(
    payload: AltegioWebhookPayload,
    request: Request,
    db: AsyncSession = Depends(get_db_session)
):
    # ... ваша логика обработки ...
    pass
```

Здесь `payload: AltegioWebhookPayload` является ключевым моментом. FastAPI автоматически:

1.  **Считывает тело запроса**: Ожидается, что тело POST-запроса будет содержать JSON-данные.
2.  **Валидирует данные**: FastAPI передает эти JSON-данные в Pydantic-схему `AltegioWebhookPayload`. Если данные не соответствуют схеме (например, отсутствует обязательное поле `company_id` или `resource_id` не является числом), FastAPI автоматически генерирует ошибку 422 Unprocessable Entity и возвращает клиенту детальное описание проблемы.
3.  **Преобразует в объект Python**: Если валидация прошла успешно, FastAPI создает экземпляр класса `AltegioWebhookPayload` со всеми данными, доступными как атрибуты объекта (например, `payload.company_id`, `payload.data.client.phone`). Это позволяет вам работать с данными в удобном, объектно-ориентированном стиле, без необходимости вручную парсить JSON и проверять типы.
4.  **`response_model=WebhookResponse`**: Этот параметр в декораторе `@router.post` указывает FastAPI, что ответ от этого эндпоинта должен быть сериализован в соответствии со схемой `WebhookResponse`. Это гарантирует, что ваш API всегда будет возвращать предсказуемый формат ответа, даже если ваша внутренняя логика возвращает более сложный объект. FastAPI автоматически преобразует ваш возвращаемый объект в `WebhookResponse` и затем в JSON.

### Расширение Pydantic Схем для вашей логики

В файле `app/schemas/altegio.py` я оставил `TODO` комментарии, чтобы вы могли легко расширить схемы по мере необходимости. Например, если Altegio начнет присылать новые поля в данных о записи, вы можете просто добавить их в `AltegioRecordData`:

```python
class AltegioRecordData(BaseModel):
    # ... существующие поля ...
    master: Optional[dict] = None # Новое поле: информация о мастере
    salon: Optional[dict] = None  # Новое поле: информация о салоне
    payment_status: Optional[str] = None # Новое поле: статус оплаты
```

Это позволит FastAPI автоматически валидировать эти новые поля, если они присутствуют в webhook, и сделает их доступными в вашем коде. Если эти поля необязательны, используйте `Optional` и укажите `None` в качестве значения по умолчанию. Если они обязательны, просто укажите их тип без `Optional`.

### Резюме по Pydantic

Pydantic — это мощный инструмент, который значительно упрощает работу с данными в FastAPI. Он обеспечивает надежную валидацию, удобную сериализацию/десериализацию и автоматическую документацию, позволяя вам сосредоточиться на бизнес-логике, а не на рутинных проверках данных. Используя Pydantic, вы пишете меньше кода, делаете его более надежным и легким для поддержки.



## 2. Мониторинг и Тестирование Запросов

После того как вы настроили схемы и эндпоинты, важно понимать, как отслеживать и проверять, что ваши запросы обрабатываются корректно. В этом разделе мы рассмотрим различные методы мониторинга и тестирования в вашем проекте.

### 2.1. Логирование

Логирование — это первый и самый важный инструмент для отслеживания работы вашего приложения. В проекте настроено логирование в консоль и в файл `logs/errors.log`.

**Как это работает:**

В файле `app/main.py` функция `setup_logging()` настраивает корневой логгер, который записывает сообщения в консоль и в файл `logs/errors.log`. Уровень логирования по умолчанию установлен на `INFO`, но его можно изменить через переменную окружения `LOG_LEVEL` в файле `.env`.

В файлах маршрутов (например, `app/routes/webhook.py`) вы увидите использование логгера:

```python
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# ...

@router.post("/webhook", response_model=WebhookResponse)
async def handle_altegio_webhook(
    payload: AltegioWebhookPayload,
    request: Request,
    db: AsyncSession = Depends(get_db_session)
):
    try:
        logger.info(f"Received webhook: company_id={payload.company_id}, "
                   f"resource={payload.resource}, resource_id={payload.resource_id}, "
                   f"status={payload.status}")
        # ... остальная логика ...
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
```

*   `logger.info()`: Используется для записи информационных сообщений, например, о получении нового webhook.
*   `logger.error()`: Используется для записи сообщений об ошибках. Параметр `exc_info=True` позволяет включить информацию о трассировке стека, что очень полезно для отладки.

**Как мониторить логи:**

1.  **Через Docker Compose логи**: Самый простой способ — просматривать логи контейнеров в реальном времени:
    ```bash
    docker-compose logs -f backend
    ```
    Эта команда будет выводить все логи из контейнера `backend` (вашего FastAPI приложения) прямо в вашу консоль. Вы увидите сообщения `INFO` о получении webhook, а также любые ошибки `ERROR`.

2.  **Просмотр файла логов**: Вы также можете просмотреть файл `logs/errors.log` напрямую. Этот файл находится в корневой директории вашего проекта и монтируется в контейнер `backend` через `volumes` в `docker-compose.yml`.
    ```bash
    # Из корневой директории проекта
    tail -f logs/errors.log
    ```
    Это особенно полезно для просмотра только ошибок или для анализа логов после перезапуска контейнера.

### 2.2. Проверка Базы Данных

Каждый полученный webhook от Altegio сохраняется в базе данных PostgreSQL в таблице `webhook_records`. Это позволяет вам отслеживать все входящие запросы, их статус обработки и данные. Вы можете напрямую подключиться к базе данных, чтобы проверить записи.

**Как подключиться к базе данных:**

```bash
docker-compose exec db psql -U postgres -d altegio_webkassa_db
```

После подключения вы можете выполнять SQL-запросы:

*   **Просмотр всех записей webhook:**
    ```sql
    SELECT id, resource_id, client_phone, processed, created_at, status, processing_error
    FROM webhook_records
    ORDER BY created_at DESC
    LIMIT 10;
    ```
*   **Поиск записей по телефону клиента:**
    ```sql
    SELECT * FROM webhook_records
    WHERE client_phone = "+77770220606";
    ```
*   **Проверка статуса обработки:**
    ```sql
    SELECT
        status,
        processed,
        COUNT(*) as count
    FROM webhook_records
    GROUP BY status, processed;
    ```

Эти запросы помогут вам убедиться, что webhook-и сохраняются, и отслеживать их статус обработки (`processed` флаг).

### 2.3. Тестирование с помощью `examples.md` и Swagger UI

В корневой директории проекта находится файл `examples.md`, который содержит примеры запросов `curl` и Python-скриптов для тестирования ваших эндпоинтов. Это отличный способ быстро проверить работоспособность API.

**Использование `examples.md`:**

1.  **Отправка тестового webhook:**
    Откройте `examples.md` и скопируйте пример `curl` для `POST /api/webhook`. Выполните его в вашей консоли. После отправки запроса, проверьте логи (`docker-compose logs -f backend`) и базу данных, чтобы убедиться, что webhook был получен и сохранен.

2.  **Проверка статуса webhook:**
    Используйте пример `curl` для `GET /api/webhook/status/{record_id}`, заменив `{record_id}` на ID записи, которую вы получили после отправки тестового webhook.

**Использование Swagger UI:**

FastAPI автоматически генерирует интерактивную документацию API, доступную по адресу `http://localhost/docs` (если ваш Nginx настроен правильно). Это Swagger UI, который позволяет вам:

*   **Просматривать все доступные эндпоинты**: Вы увидите `/api/webhook`, `/acquire`, `/health` и другие.
*   **Просматривать Pydantic схемы**: Для каждого эндпоинта вы увидите ожидаемую структуру запроса и ответа, включая примеры JSON, которые мы добавили через `json_schema_extra`.
*   **Отправлять тестовые запросы прямо из браузера**: Вы можете нажать на эндпоинт, затем на кнопку "Try it out", ввести данные в поля (или использовать предоставленный пример) и нажать "Execute". Вы увидите отправленный запрос, полученный ответ и статус код. Это очень удобно для быстрой проверки без использования `curl` или написания скриптов.

### 2.4. Мониторинг ресурсов Docker

Для общего мониторинга состояния ваших контейнеров Docker вы можете использовать команду `docker stats`:

```bash
docker stats
```

Эта команда покажет вам в реальном времени использование CPU, памяти, сетевой активности и дискового ввода/вывода для всех запущенных контейнеров. Это полезно для выявления проблем с производительностью или утечек памяти.

### 2.5. Настройка Nginx

Nginx выступает в роли обратного прокси, перенаправляя запросы к вашему FastAPI приложению. В файле `nginx/default.conf` настроены правила проксирования. Если вы столкнетесь с проблемами доступа к API или статическим файлам, проверьте этот файл.

*   **Логи Nginx**: Логи доступа и ошибок Nginx также доступны:
    ```bash
    docker-compose logs -f nginx
    ```
    Эти логи помогут вам понять, доходят ли запросы до Nginx и как они перенаправляются.

### Резюме по Мониторингу и Тестированию

Комбинируя логирование, проверку базы данных, тестирование через `examples.md` и Swagger UI, а также мониторинг Docker ресурсов, вы получаете полный набор инструментов для эффективной отладки и обеспечения стабильной работы вашего проекта. Это позволит вам быстро выявлять и устранять проблемы, а также проверять корректность реализации вашей бизнес-логики.



## Заключение

Это руководство предоставило вам глубокое понимание того, как Pydantic схемы используются для валидации и сериализации данных в FastAPI, а также как эффективно мониторить и тестировать запросы в вашем проекте. Используя эти знания, вы сможете уверенно реализовывать вашу бизнес-логику, интегрируя Altegio и Webkassa.

Помните, что ключевые точки для вашей реализации находятся в файлах:

*   `app/routes/webhook.py`: Здесь вы будете дорабатывать логику `process_fiscalization` и `prepare_webkassa_data` для интеграции с Webkassa.
*   `app/routes/acquire.py`: Здесь вы будете дорабатывать логику `process_payment` для интеграции с реальной платежной системой.
*   `app/schemas/altegio.py`: Расширяйте Pydantic схемы по мере необходимости, чтобы они соответствовали полному объему данных, которые вы ожидаете от Altegio и Webkassa.
*   `app/models.py`: Добавляйте или изменяйте модели базы данных, если вам потребуется хранить дополнительную информацию.

Не забывайте использовать логирование (`logger.info`, `logger.error`), проверять логи Docker (`docker-compose logs -f <service_name>`) и базу данных (`docker-compose exec db psql`) для отладки и мониторинга. Swagger UI (`http://localhost/docs`) будет вашим лучшим другом для тестирования API-эндпоинтов.

Удачи в реализации вашего проекта!

