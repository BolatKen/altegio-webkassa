"""
Маршруты для обработки webhook от Altegio
"""
import logging
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db_session
from app.models import WebhookRecord
from app.schemas.altegio import AltegioWebhookPayload, WebhookResponse

router = APIRouter()
logger = logging.getLogger(__name__)


async def verify_webhook_signature(request: Request) -> bool:
    """
    Проверка подписи webhook от Altegio
    TODO: Реализовать проверку подписи/токена от Altegio
    """
    # Получаем заголовки для проверки подписи
    signature = request.headers.get("X-Altegio-Signature")
    token = request.headers.get("Authorization")
    
    # TODO: Добавить логику проверки подписи
    # if not signature or not verify_signature(signature, body, secret):
    #     return False
    
    logger.info(f"Webhook signature check - Signature: {signature}, Token: {token}")
    return True  # Временно пропускаем проверку


@router.post("/webhook", response_model=WebhookResponse)
async def handle_altegio_webhook(
    payload: AltegioWebhookPayload,
    request: Request,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Обработка webhook от Altegio
    
    Принимает данные о записях/клиентах от Altegio,
    сохраняет в БД и инициирует процесс фискализации через Webkassa
    """
    try:
        logger.info(f"Received webhook: company_id={payload.company_id}, "
                   f"resource={payload.resource}, resource_id={payload.resource_id}, "
                   f"status={payload.status}")
        
        # Проверка подписи webhook (опционально)
        if not await verify_webhook_signature(request):
            logger.warning("Invalid webhook signature")
            raise HTTPException(status_code=401, detail="Invalid webhook signature")
        
        # Сохранение webhook в базу данных
        webhook_record = WebhookRecord(
            company_id=payload.company_id,
            resource=payload.resource,
            resource_id=payload.resource_id,
            status=payload.status,
            client_phone=payload.data.client.phone,
            client_name=payload.data.client.name,
            record_date=datetime.fromisoformat(payload.data.date.replace(' ', 'T')),
            services_data=payload.data.services,
            comment=payload.data.comment,
            raw_data=payload.dict(),
            processed=False,
            created_at=datetime.utcnow()
        )
        
        db.add(webhook_record)
        await db.commit()
        await db.refresh(webhook_record)
        
        logger.info(f"Webhook saved to database with ID: {webhook_record.id}")
        
        # TODO: Инициировать процесс фискализации через Webkassa
        await process_fiscalization(webhook_record, payload)
        
        return WebhookResponse(
            success=True,
            message="Webhook processed successfully",
            record_id=webhook_record.id
        )
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


async def process_fiscalization(webhook_record: WebhookRecord, payload: AltegioWebhookPayload):
    """
    Обработка фискализации через Webkassa
    TODO: Реализовать интеграцию с Webkassa API
    """
    try:
        logger.info(f"Starting fiscalization process for record {webhook_record.id}")
        
        # TODO: Подготовка данных для Webkassa
        fiscalization_data = prepare_webkassa_data(payload)
        
        # TODO: Отправка запроса в Webkassa API
        # webkassa_response = await send_to_webkassa(fiscalization_data)
        
        # TODO: Обновление статуса обработки в БД
        # webhook_record.processed = True
        # webhook_record.webkassa_response = webkassa_response
        # await db.commit()
        
        logger.info(f"Fiscalization completed for record {webhook_record.id}")
        
    except Exception as e:
        logger.error(f"Error in fiscalization process: {str(e)}", exc_info=True)
        # TODO: Обновить статус ошибки в БД
        raise


def prepare_webkassa_data(payload: AltegioWebhookPayload) -> Dict[str, Any]:
    """
    Подготовка данных для отправки в Webkassa
    TODO: Реализовать маппинг данных Altegio -> Webkassa
    """
    # Расчет общей суммы
    total_amount = sum(service.cost for service in payload.data.services)
    
    # Базовая структура для Webkassa
    webkassa_data = {
        "external_id": f"altegio_{payload.resource_id}",
        "client": {
            "name": payload.data.client.name,
            "phone": payload.data.client.phone
        },
        "items": [
            {
                "name": service.title,
                "price": service.cost / 100,  # Конвертация из копеек в рубли
                "quantity": 1,
                "total": service.cost / 100
            }
            for service in payload.data.services
        ],
        "total_amount": total_amount / 100,
        "payment_method": "card",  # TODO: Определить из данных Altegio
        "timestamp": payload.data.date
    }
    
    logger.info(f"Prepared Webkassa data: {webkassa_data}")
    return webkassa_data


@router.get("/webhook/status/{record_id}")
async def get_webhook_status(
    record_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Получение статуса обработки webhook по ID записи
    """
    try:
        webhook_record = await db.get(WebhookRecord, record_id)
        if not webhook_record:
            raise HTTPException(status_code=404, detail="Webhook record not found")
        
        return {
            "id": webhook_record.id,
            "resource_id": webhook_record.resource_id,
            "processed": webhook_record.processed,
            "created_at": webhook_record.created_at,
            "client_phone": webhook_record.client_phone,
            "status": webhook_record.status
        }
        
    except Exception as e:
        logger.error(f"Error getting webhook status: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

