"""
Маршруты для frontend страниц
"""
import logging
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

router = APIRouter()
logger = logging.getLogger(__name__)

# Настройка шаблонов
templates = Jinja2Templates(directory="app/templates")


@router.get("/acquire", response_class=HTMLResponse)
async def acquire_page(request: Request):
    """
    Страница с кнопкой оплаты
    Отображает простую HTML страницу с формой оплаты
    """
    try:
        logger.info("Serving acquire page")
        
        # Данные для передачи в шаблон
        context = {
            "request": request,
            "title": "Оплата услуг",
            "company_name": "Салон красоты",
            "service_name": "Услуги салона",
            "amount": "0.00"  # Placeholder сумма
        }
        
        return templates.TemplateResponse("acquire.html", context)
        
    except Exception as e:
        logger.error(f"Error serving acquire page: {str(e)}")
        # Возвращаем простую HTML страницу с ошибкой
        error_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Ошибка</title>
            <meta charset="utf-8">
        </head>
        <body>
            <h1>Ошибка загрузки страницы</h1>
            <p>Попробуйте обновить страницу позже.</p>
        </body>
        </html>
        """
        return HTMLResponse(content=error_html, status_code=500)


@router.post("/acquire/payment")
async def process_payment(request: Request):
    """
    Обработка запроса на оплату
    TODO: Интеграция с реальной платежной системой
    """
    try:
        form_data = await request.form()
        logger.info(f"Payment request received: {dict(form_data)}")
        
        # TODO: Здесь должна быть логика обработки платежа
        # - Валидация данных
        # - Создание платежа в платежной системе
        # - Сохранение информации о платеже в БД
        # - Отправка данных в Webkassa для фискализации
        
        # Пока возвращаем заглушку
        return {
            "success": True,
            "message": "Платеж обрабатывается",
            "payment_id": "placeholder_payment_id",
            "redirect_url": "/acquire/success"
        }
        
    except Exception as e:
        logger.error(f"Error processing payment: {str(e)}")
        return {
            "success": False,
            "message": "Ошибка обработки платежа",
            "error": str(e)
        }


@router.get("/acquire/success", response_class=HTMLResponse)
async def payment_success(request: Request):
    """
    Страница успешной оплаты
    """
    try:
        context = {
            "request": request,
            "title": "Оплата успешна",
            "message": "Ваш платеж успешно обработан"
        }
        
        return templates.TemplateResponse("success.html", context)
        
    except Exception as e:
        logger.error(f"Error serving success page: {str(e)}")
        success_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Оплата успешна</title>
            <meta charset="utf-8">
        </head>
        <body>
            <h1>Оплата успешна</h1>
            <p>Ваш платеж обработан.</p>
            <a href="/acquire">Вернуться к оплате</a>
        </body>
        </html>
        """
        return HTMLResponse(content=success_html)

