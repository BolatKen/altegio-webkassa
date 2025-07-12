"""
Pydantic схемы для валидации данных от Altegio webhook
"""
from datetime import datetime
from typing import List, Optional, Any
from pydantic import BaseModel, Field


class AltegioClientTag(BaseModel):
    """Модель тега клиента из Altegio"""
    id: int
    title: str


class AltegioClient(BaseModel):
    """Модель клиента из Altegio"""
    id: int = Field(..., description="ID клиента")
    name: str = Field(..., description="Имя клиента")
    surname: Optional[str] = Field(None, description="Фамилия клиента")
    patronymic: Optional[str] = Field(None, description="Отчество клиента")
    display_name: str = Field(..., description="Отображаемое имя клиента")
    comment: Optional[str] = Field(None, description="Комментарий к клиенту")
    phone: str = Field(..., description="Телефон клиента")
    card: Optional[str] = Field(None, description="Номер карты клиента")
    email: Optional[str] = Field(None, description="Email клиента")
    success_visits_count: int = Field(..., description="Количество успешных визитов")
    fail_visits_count: int = Field(..., description="Количество неуспешных визитов")
    discount: int = Field(..., description="Скидка клиента")
    custom_fields: List[Any] = Field(..., description="Пользовательские поля клиента")
    sex: int = Field(..., description="Пол клиента (0 - не указан, 1 - мужской, 2 - женский)")
    birthday: Optional[str] = Field(None, description="День рождения клиента")
    client_tags: List[AltegioClientTag] = Field(..., description="Теги клиента")


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
    api_id: Optional[str]
    name: str
    specialization: str
    position: AltegioPosition
    avatar: str
    avatar_big: str
    rating: int
    votes_count: int


class AltegioDocument(BaseModel):
    """Модель документа из Altegio"""
    id: int
    type_id: int
    storage_id: int
    user_id: int
    company_id: int
    number: int
    comment: Optional[str]
    date_created: str
    category_id: int
    visit_id: int
    record_id: int
    type_title: str
    is_sale_bill_printed: bool


class AltegioRecordData(BaseModel):
    """Данные записи из Altegio"""
    id: int = Field(..., description="ID записи")
    company_id: int = Field(..., description="ID компании")
    staff_id: int = Field(..., description="ID сотрудника")
    clients_count: int = Field(..., description="Количество клиентов")
    date: str = Field(..., description="Дата и время записи")
    comment: Optional[str] = Field(None, description="Комментарий к записи")
    online: bool = Field(..., description="Запись сделана онлайн")
    visit_id: int = Field(..., description="ID визита")
    visit_attendance: int = Field(..., description="Посещаемость визита")
    attendance: int = Field(..., description="Посещаемость")
    confirmed: int = Field(..., description="Подтверждено")
    seance_length: int = Field(..., description="Длительность сеанса в секундах")
    length: int = Field(..., description="Длительность в секундах")
    sms_before: int = Field(..., description="SMS до")
    sms_now: int = Field(..., description="SMS сейчас")
    sms_now_text: str = Field(..., description="Текст SMS сейчас")
    email_now: int = Field(..., description="Email сейчас")
    notified: int = Field(..., description="Уведомлено")
    master_request: int = Field(..., description="Запрос мастера")
    api_id: str = Field(..., description="API ID")
    from_url: str = Field(..., description="URL, с которого сделана запись")
    review_requested: int = Field(..., description="Запрошен отзыв")
    created_user_id: int = Field(..., description="ID пользователя, создавшего запись")
    deleted: bool = Field(..., description="Удалено")
    paid_full: int = Field(..., description="Оплачено полностью")
    prepaid: bool = Field(..., description="Предоплачено")
    prepaid_confirmed: bool = Field(..., description="Предоплата подтверждена")
    is_update_blocked: bool = Field(..., description="Обновление заблокировано")
    activity_id: int = Field(..., description="ID активности")
    bookform_id: int = Field(..., description="ID формы бронирования")
    record_from: str = Field(..., description="Откуда сделана запись")
    is_mobile: int = Field(..., description="Сделано с мобильного")
    services: List[AltegioService] = Field(..., description="Список услуг")
    staff: AltegioStaff = Field(..., description="Данные сотрудника")
    goods_transactions: List[Any] = Field(..., description="Транзакции товаров")
    sms_remain_hours: int = Field(..., description="Оставшиеся часы для SMS")
    email_remain_hours: int = Field(..., description="Оставшиеся часы для Email")
    comer: Optional[Any] = Field(None, description="Пришедший")
    comer_person_info: Optional[Any] = Field(None, description="Информация о пришедшем")
    client: AltegioClient = Field(..., description="Данные клиента")
    datetime: str = Field(..., description="Дата и время записи с часовым поясом")
    create_date: str = Field(..., description="Дата создания записи с часовым поясом")
    last_change_date: str = Field(..., description="Дата последнего изменения записи с часовым поясом")
    custom_fields: List[Any] = Field(..., description="Пользовательские поля")
    custom_color: str = Field(..., description="Пользовательский цвет")
    custom_font_color: str = Field(..., description="Пользовательский цвет шрифта")
    record_labels: List[Any] = Field(..., description="Метки записи")
    documents: List[AltegioDocument] = Field(..., description="Документы")
    short_link: str = Field(..., description="Короткая ссылка")
    composite: List[Any] = Field(..., description="Композит")


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



