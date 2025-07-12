"""
Pydantic схемы для валидации данных от Altegio webhook
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class AltegioClient(BaseModel):
    """Модель клиента из Altegio"""
    name: str = Field(..., description="Имя клиента")
    phone: str = Field(..., description="Телефон клиента")


class AltegioService(BaseModel):
    """Модель услуги из Altegio"""
    title: str = Field(..., description="Название услуги")
    cost: int = Field(..., description="Стоимость услуги в копейках")


class AltegioRecordData(BaseModel):
    """Данные записи из Altegio"""
    id: int = Field(..., description="ID записи")
    date: str = Field(..., description="Дата и время записи")
    comment: Optional[str] = Field(None, description="Комментарий к записи")
    services: List[AltegioService] = Field(..., description="Список услуг")
    client: AltegioClient = Field(..., description="Данные клиента")
    
    # TODO: Добавить дополнительные поля по мере необходимости
    # master: Optional[dict] = None
    # salon: Optional[dict] = None
    # payment_status: Optional[str] = None


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


class WebhookResponse(BaseModel):
    """Ответ на webhook запрос"""
    success: bool = Field(..., description="Статус обработки")
    message: str = Field(..., description="Сообщение о результате")
    record_id: Optional[int] = Field(None, description="ID созданной записи в БД")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Webhook processed successfully",
                "record_id": 123
            }
        }

