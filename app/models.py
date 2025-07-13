"""
Модели SQLAlchemy для базы данных
"""
from datetime import datetime
from typing import List, Dict, Any, Optional

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, Numeric
from sqlalchemy.sql import func

from app.db import Base


class WebhookRecord(Base):
    """
    Модель для хранения webhook запросов от Altegio
    """
    __tablename__ = "webhook_records"
    
    # Основные поля
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Данные из webhook
    company_id = Column(Integer, nullable=False, index=True, comment="ID компании в Altegio")
    resource = Column(String(50), nullable=False, index=True, comment="Тип ресурса (record, client, etc.)")
    resource_id = Column(Integer, nullable=False, index=True, comment="ID ресурса в Altegio")
    status = Column(String(20), nullable=False, index=True, comment="Статус операции (create, update, delete)")
    
    # Данные клиента
    client_phone = Column(String(20), nullable=False, index=True, comment="Телефон клиента")
    client_name = Column(String(255), nullable=False, comment="Имя клиента")
    
    # Данные записи
    record_date = Column(DateTime, nullable=False, index=True, comment="Дата и время записи")
    comment = Column(Text, nullable=True, comment="Комментарий к записи")
    
    # Данные об услугах (JSON)
    services_data = Column(JSON, nullable=False, comment="Список услуг в формате JSON")
    
    # Полные данные webhook (для отладки и восстановления)
    raw_data = Column(JSON, nullable=False, comment="Полные данные webhook в формате JSON")
    
    # Статус обработки
    processed = Column(Boolean, default=False, nullable=False, index=True, comment="Флаг обработки webhook")
    processing_error = Column(Text, nullable=True, comment="Ошибка при обработке")
    
    # Данные фискализации Webkassa
    webkassa_request_id = Column(String(255), nullable=True, index=True, comment="ID запроса в Webkassa")
    webkassa_response = Column(JSON, nullable=True, comment="Ответ от Webkassa API")
    webkassa_status = Column(String(50), nullable=True, index=True, comment="Статус фискализации")
    
    # Временные метки
    created_at = Column(DateTime, default=func.now(), nullable=False, index=True, comment="Время создания записи")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False, comment="Время последнего обновления")
    processed_at = Column(DateTime, nullable=True, comment="Время обработки")
    
    def __repr__(self):
        return (f"<WebhookRecord(id={self.id}, company_id={self.company_id}, "
                f"resource_id={self.resource_id}, client_phone=\'{self.client_phone}\', "
                f"processed={self.processed})>")
    
    @property
    def total_amount(self) -> float:
        """Вычисление общей суммы услуг"""
        if not self.services_data:
            return 0.0
        
        total = 0
        for service in self.services_data:
            if isinstance(service, dict) and 'cost' in service:
                total += service['cost']
        
        return total / 100  # Конвертация из копеек в рубли
    
    @property
    def services_list(self) -> List[str]:
        """Получение списка названий услуг"""
        if not self.services_data:
            return []
        
        services = []
        for service in self.services_data:
            if isinstance(service, dict) and 'title' in service:
                services.append(service['title'])
        
        return services


class PaymentRecord(Base):
    """
    Модель для хранения информации о платежах
    TODO: Расширить модель при интеграции с платежной системой
    """
    __tablename__ = "payment_records"
    
    # Основные поля
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Связь с webhook
    webhook_record_id = Column(Integer, nullable=True, index=True, comment="ID связанного webhook")
    
    # Данные платежа
    external_payment_id = Column(String(255), nullable=True, index=True, comment="ID платежа во внешней системе")
    amount = Column(Numeric(10, 2), nullable=False, comment="Сумма платежа")
    currency = Column(String(3), default="KZT", nullable=False, comment="Валюта платежа")
    payment_method = Column(String(50), nullable=True, comment="Способ оплаты")
    
    # Статус платежа
    status = Column(String(20), nullable=False, index=True, comment="Статус платежа")
    
    # Данные клиента
    client_phone = Column(String(20), nullable=True, index=True, comment="Телефон клиента")
    client_email = Column(String(255), nullable=True, comment="Email клиента")
    
    # Временные метки
    created_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    paid_at = Column(DateTime, nullable=True, comment="Время оплаты")
    
    def __repr__(self):
        return (f"<PaymentRecord(id={self.id}, amount={self.amount}, "
                f"status=\'{self.status}\', client_phone=\'{self.client_phone}\')>")


class FiscalizationLog(Base):
    """
    Модель для логирования процесса фискализации
    """
    __tablename__ = "fiscalization_logs"
    
    # Основные поля
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Связи
    webhook_record_id = Column(Integer, nullable=False, index=True, comment="ID webhook записи")
    payment_record_id = Column(Integer, nullable=True, index=True, comment="ID платежа")
    
    # Данные фискализации
    webkassa_request = Column(JSON, nullable=False, comment="Запрос к Webkassa API")
    webkassa_response = Column(JSON, nullable=True, comment="Ответ от Webkassa API")
    
    # Статус и ошибки
    status = Column(String(20), nullable=False, index=True, comment="Статус фискализации")
    error_message = Column(Text, nullable=True, comment="Сообщение об ошибке")
    retry_count = Column(Integer, default=0, nullable=False, comment="Количество попыток")
    
    # Временные метки
    created_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True, comment="Время завершения фискализации")
    
    def __repr__(self):
        return (f"<FiscalizationLog(id={self.id}, webhook_record_id={self.webhook_record_id}, "
                f"status=\'{self.status}\', retry_count={self.retry_count})>")


class ApiKey(Base):
    """
    Модель для хранения API ключей сторонних сервисов (например, Webkassa)
    """
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    service_name = Column(String(50), unique=True, nullable=False, comment="Название сервиса (например, Webkassa)")
    api_key = Column(String(255), nullable=False, comment="API ключ")
    user_id = Column(String(255), nullable=True, comment="User ID для авторизации (если требуется)")
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<ApiKey(service_name=\'{self.service_name}\')>"


