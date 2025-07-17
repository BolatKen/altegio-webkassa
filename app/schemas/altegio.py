"""
Pydantic схемы для валидации данных от Altegio webhook
"""
from datetime import datetime
from typing import List, Optional, Any, Union
from pydantic import BaseModel, Field


class AltegioClientTag(BaseModel):
    """Модель тега клиента из Altegio"""
    id: int
    title: str


class AltegioClient(BaseModel):
    """Модель клиента из Altegio"""
    id: int = Field(..., description="ID клиента")
    name: str = Field(..., description="Имя клиента")
    surname: Optional[str] = Field("", description="Фамилия клиента")  # Значение по умолчанию
    patronymic: Optional[str] = Field("", description="Отчество клиента")  # Значение по умолчанию
    display_name: str = Field(..., description="Отображаемое имя клиента")
    comment: Optional[str] = Field("", description="Комментарий к клиенту")  # Значение по умолчанию
    phone: str = Field(..., description="Телефон клиента")
    card: Optional[str] = Field("", description="Номер карты клиента")  # Значение по умолчанию
    email: Optional[str] = Field("", description="Email клиента")  # Значение по умолчанию
    success_visits_count: int = Field(..., description="Количество успешных визитов")
    fail_visits_count: int = Field(..., description="Количество неуспешных визитов")
    discount: int = Field(..., description="Скидка клиента")
    custom_fields: List[Any] = Field(default_factory=list, description="Пользовательские поля клиента")  # Значение по умолчанию
    sex: int = Field(..., description="Пол клиента (0 - не указан, 1 - мужской, 2 - женский)")
    birthday: Optional[str] = Field("", description="День рождения клиента")  # Значение по умолчанию
    client_tags: List[AltegioClientTag] = Field(default_factory=list, description="Теги клиента")  # Значение по умолчанию


class AltegioService(BaseModel):
    """Модель услуги из Altegio"""
    id: int = Field(..., description="ID услуги")
    title: str = Field(..., description="Название услуги")
    cost: int = Field(..., description="Стоимость услуги в копейках")
    cost_to_pay: int = Field(..., description="Стоимость к оплате в копейках")
    manual_cost: int = Field(..., description="Ручная стоимость в копейках")
    cost_per_unit: int = Field(..., description="Стоимость за единицу в копейках")
    discount: int = Field(..., description="Скидка на услугу")
    first_cost: int = Field(..., description="Первоначальная стоимость в копейках")
    amount: int = Field(..., description="Количество услуг")


class AltegioPosition(BaseModel):
    """Модель должности сотрудника из Altegio"""
    id: int
    title: str
    services_binding_type: int


class AltegioStaff(BaseModel):
    """Модель сотрудника из Altegio"""
    id: int
    api_id: Optional[str] = Field(None, description="API ID сотрудника (может отсутствовать)")
    name: str
    specialization: str
    position: AltegioPosition
    avatar: str
    avatar_big: str
    rating: float  # Изменили с int на float, так как Altegio отправляет дробные числа
    votes_count: int


class AltegioDocument(BaseModel):
    """Модель документа из Altegio"""
    id: int
    type_id: int
    storage_id: int
    user_id: int
    company_id: int
    number: int
    comment: Optional[str] = Field("", description="Комментарий к документу")
    date_created: str
    category_id: int
    visit_id: int
    record_id: int
    type_title: str
    is_sale_bill_printed: bool


# Дополнительные модели для goods_operations_sale
class AltegioGood(BaseModel):
    """Модель товара из Altegio"""
    id: int
    title: str

class AltegioUnit(BaseModel):
    """Модель единицы измерения из Altegio"""
    id: int
    title: str
    short_title: str

class AltegioStorage(BaseModel):
    """Модель склада из Altegio"""
    id: int
    title: str

class AltegioMaster(BaseModel):
    """Модель мастера из Altegio"""
    id: int
    title: str

class AltegioSimpleClient(BaseModel):
    """Упрощенная модель клиента для goods_operations_sale"""
    id: int
    name: str
    phone: str


class AltegioRecordData(BaseModel):
    """
    Универсальные данные из Altegio webhook.
    Поддерживает как record, так и goods_operations_sale форматы.
    """
    id: int = Field(..., description="ID записи/операции")
    
    # Общие поля
    comment: Optional[str] = Field(None, description="Комментарий")
    
    # Поля для record webhook
    company_id: Optional[int] = Field(None, description="ID компании (для record)")
    staff_id: Optional[int] = Field(None, description="ID сотрудника (для record)")
    clients_count: Optional[int] = Field(None, description="Количество клиентов")
    date: Optional[str] = Field(None, description="Дата и время записи")
    online: Optional[bool] = Field(None, description="Запись сделана онлайн")
    visit_id: Optional[int] = Field(None, description="ID визита")
    visit_attendance: Optional[int] = Field(None, description="Посещаемость визита")
    attendance: Optional[int] = Field(None, description="Посещаемость")
    confirmed: Optional[int] = Field(None, description="Подтверждено")
    seance_length: Optional[int] = Field(None, description="Длительность сеанса в секундах")
    length: Optional[int] = Field(None, description="Длительность в секундах")
    sms_before: Optional[int] = Field(None, description="SMS до")
    sms_now: Optional[int] = Field(None, description="SMS сейчас")
    sms_now_text: Optional[str] = Field("", description="Текст SMS сейчас")
    email_now: Optional[int] = Field(None, description="Email сейчас")
    notified: Optional[int] = Field(None, description="Уведомлено")
    master_request: Optional[int] = Field(None, description="Запрос мастера")
    api_id: Optional[str] = Field(None, description="API ID")
    from_url: Optional[str] = Field("", description="URL, с которого сделана запись")
    review_requested: Optional[int] = Field(None, description="Запрошен отзыв")
    created_user_id: Optional[int] = Field(None, description="ID пользователя, создавшего запись")
    deleted: Optional[bool] = Field(None, description="Удалено")
    paid_full: Optional[int] = Field(None, description="Оплачено полностью")
    prepaid: Optional[bool] = Field(None, description="Предоплачено")
    prepaid_confirmed: Optional[bool] = Field(None, description="Предоплата подтверждена")
    is_update_blocked: Optional[bool] = Field(None, description="Обновление заблокировано")
    activity_id: Optional[int] = Field(None, description="ID активности")
    bookform_id: Optional[int] = Field(None, description="ID формы бронирования")
    record_from: Optional[str] = Field("", description="Откуда сделана запись")
    is_mobile: Optional[int] = Field(None, description="Сделано с мобильного")
    services: List[AltegioService] = Field(default_factory=list, description="Список услуг (для record)")
    staff: Optional[AltegioStaff] = Field(None, description="Данные сотрудника (для record)")
    goods_transactions: List[Any] = Field(default_factory=list, description="Транзакции товаров")
    sms_remain_hours: Optional[int] = Field(None, description="Оставшиеся часы для SMS")
    email_remain_hours: Optional[int] = Field(None, description="Оставшиеся часы для Email")
    comer: Optional[Any] = Field(None, description="Пришедший")
    comer_person_info: Optional[Any] = Field(None, description="Информация о пришедшем")
    datetime: Optional[str] = Field(None, description="Дата и время записи с часовым поясом (для record)")
    custom_fields: List[Any] = Field(default_factory=list, description="Пользовательские поля")
    custom_color: str = Field("", description="Пользовательский цвет")
    custom_font_color: str = Field("", description="Пользовательский цвет шрифта")
    record_labels: List[Any] = Field(default_factory=list, description="Метки записи")
    documents: List[AltegioDocument] = Field(default_factory=list, description="Документы")
    short_link: Optional[str] = Field(None, description="Короткая ссылка")
    composite: List[Any] = Field(default_factory=list, description="Композит")
    
    # Поля для goods_operations_sale webhook
    document_id: Optional[int] = Field(None, description="ID документа (для goods_operations_sale)")
    type_id: Optional[int] = Field(None, description="Тип операции")
    type: Optional[str] = Field(None, description="Тип операции (название)")
    operation_unit_type: Optional[int] = Field(None, description="Тип единицы операции")
    amount: Optional[int] = Field(None, description="Количество (может быть отрицательным)")
    create_date: Optional[str] = Field(None, description="Дата создания (для goods_operations_sale)")
    last_change_date: Optional[str] = Field(None, description="Дата последнего изменения")
    cost_per_unit: Optional[int] = Field(None, description="Стоимость за единицу")
    cost: Optional[int] = Field(None, description="Общая стоимость")
    discount: Optional[int] = Field(None, description="Скидка")
    record_id: Optional[int] = Field(None, description="ID записи")
    loyalty_abonement_id: Optional[int] = Field(None, description="ID абонемента лояльности")
    loyalty_certificate_id: Optional[int] = Field(None, description="ID сертификата лояльности")
    
    # Объекты для goods_operations_sale
    good: Optional[AltegioGood] = Field(None, description="Товар (для goods_operations_sale)")
    unit: Optional[AltegioUnit] = Field(None, description="Единица измерения (для goods_operations_sale)")
    storage: Optional[AltegioStorage] = Field(None, description="Склад (для goods_operations_sale)")
    master: Optional[AltegioMaster] = Field(None, description="Мастер (для goods_operations_sale)")
    service: List[Any] = Field(default_factory=list, description="Услуги (для goods_operations_sale)")
    supplier: List[Any] = Field(default_factory=list, description="Поставщики (для goods_operations_sale)")
    
    # Клиент - может быть разного формата
    client: Optional[Any] = Field(None, description="Клиент")
    
    class Config:
        extra = "allow"  # Разрешаем дополнительные поля, которые не описаны в схеме


class AltegioWebhookPayload(BaseModel):
    """Основная модель webhook от Altegio"""
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
                    "company_id": 307626,
                    "staff_id": 2835418,
                    "clients_count": 1,
                    "date": "2025-07-12 12:10:00",
                    "comment": "фч",
                    "online": False,
                    "visit_id": 508928359,
                    "visit_attendance": 1,
                    "attendance": 1,
                    "confirmed": 1,
                    "seance_length": 1500,
                    "length": 1500,
                    "sms_before": 1,
                    "sms_now": 1,
                    "sms_now_text": "",
                    "email_now": 1,
                    "notified": 0,
                    "master_request": 0,
                    "api_id": "01effc9e-09da-4db1-98a1-e317b214df2c",
                    "from_url": "",
                    "review_requested": 0,
                    "created_user_id": 12795431,
                    "deleted": False,
                    "paid_full": 1,
                    "prepaid": False,
                    "prepaid_confirmed": False,
                    "is_update_blocked": False,
                    "activity_id": 0,
                    "bookform_id": 0,
                    "record_from": "",
                    "is_mobile": 0,
                    "services": [
                        {
                            "id": 5034676,
                            "title": "Стрижка детская (от 3х лет до 13 лет)",
                            "cost": 4000,
                            "cost_to_pay": 4000,
                            "manual_cost": 4000,
                            "cost_per_unit": 4000,
                            "discount": 0,
                            "first_cost": 4000,
                            "amount": 1
                        }
                    ],
                    "staff": {
                        "id": 2835418,
                        "api_id": None,
                        "name": "Нурзад",
                        "specialization": "Barber",
                        "position": {
                            "id": 122084,
                            "title": "Барбер",
                            "services_binding_type": 0
                        },
                        "avatar": "https://assets.alteg.io/masters/sm/d/d1/d1c0beac46776cc_20250418094518.png",
                        "avatar_big": "https://assets.alteg.io/masters/origin/8/87/87766b4d0d03dcd_20250418094519.png",
                        "rating": 5,
                        "votes_count": 0
                    },
                    "goods_transactions": [],
                    "sms_remain_hours": 1,
                    "email_remain_hours": 1,
                    "comer": None,
                    "comer_person_info": None,
                    "client": {
                        "id": 169711586,
                        "name": "Вячослав",
                        "surname": "",
                        "patronymic": "",
                        "display_name": "Вячослав",
                        "comment": "",
                        "phone": "+77770220606",
                        "card": "",
                        "email": "",
                        "success_visits_count": 3,
                        "fail_visits_count": 0,
                        "discount": 0,
                        "custom_fields": [],
                        "sex": 0,
                        "birthday": "",
                        "client_tags": []
                    },
                    "datetime": "2025-07-12T12:10:00+05:00",
                    "create_date": "2025-07-12T11:49:08+0500",
                    "last_change_date": "2025-07-13T00:15:24+0500",
                    "custom_fields": [],
                    "custom_color": "",
                    "custom_font_color": "",
                    "record_labels": [],
                    "documents": [
                        {
                            "id": 683647047,
                            "type_id": 7,
                            "storage_id": 0,
                            "user_id": 12795431,
                            "company_id": 307626,
                            "number": 683647047,
                            "comment": "",
                            "date_created": "2025-07-12 13:10:00",
                            "category_id": 0,
                            "visit_id": 508928359,
                            "record_id": 596792978,
                            "type_title": "Visit",
                            "is_sale_bill_printed": False
                        }
                    ],
                    "short_link": "http://openhc.kz/c/Oyfhm/BqNtT/",
                    "composite": []
                }
            }
        }


class WebhookResponse(BaseModel):
    """Ответ на webhook запрос"""
    success: bool = Field(..., description="Статус обработки")
    message: str = Field(..., description="Сообщение о результате")
    record_id: Optional[int] = Field(None, description="ID созданной записи в БД (для одиночного webhook)")
    record_ids: Optional[List[int]] = Field(None, description="Список ID созданных записей в БД (для массива webhook)")
    processed_count: Optional[int] = Field(None, description="Количество обработанных webhook")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Successfully processed 1 webhook(s)",
                "record_id": 123,
                "record_ids": [123, 124, 125],
                "processed_count": 3
            }
        }



