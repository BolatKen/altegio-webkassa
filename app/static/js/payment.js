/**
 * JavaScript для обработки формы оплаты
 * Altegio-Webkassa Integration
 */

document.addEventListener('DOMContentLoaded', function() {
    const paymentForm = document.getElementById('payment-form');
    const payButton = document.getElementById('pay-button');
    const phoneInput = document.getElementById('client-phone');
    
    // Маска для телефона
    if (phoneInput) {
        phoneInput.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            
            if (value.startsWith('7')) {
                value = value.substring(1);
            }
            
            if (value.length > 0) {
                if (value.length <= 3) {
                    value = `+7 (${value}`;
                } else if (value.length <= 6) {
                    value = `+7 (${value.substring(0, 3)}) ${value.substring(3)}`;
                } else if (value.length <= 8) {
                    value = `+7 (${value.substring(0, 3)}) ${value.substring(3, 6)}-${value.substring(6)}`;
                } else {
                    value = `+7 (${value.substring(0, 3)}) ${value.substring(3, 6)}-${value.substring(6, 8)}-${value.substring(8, 10)}`;
                }
            }
            
            e.target.value = value;
        });
        
        // Автоматическое добавление +7 при фокусе
        phoneInput.addEventListener('focus', function(e) {
            if (!e.target.value) {
                e.target.value = '+7 (';
            }
        });
    }
    
    // Обработка отправки формы
    if (paymentForm) {
        paymentForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Показываем состояние загрузки
            setLoadingState(true);
            
            // Валидация формы
            if (!validateForm()) {
                setLoadingState(false);
                return;
            }
            
            // Сбор данных формы
            const formData = new FormData(paymentForm);
            
            // Отправка данных
            fetch('/acquire/payment', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Успешная обработка
                    showSuccessMessage('Платеж обрабатывается...');
                    
                    // Перенаправление на страницу успеха
                    setTimeout(() => {
                        if (data.redirect_url) {
                            window.location.href = data.redirect_url;
                        } else {
                            window.location.href = '/acquire/success';
                        }
                    }, 1500);
                } else {
                    // Ошибка обработки
                    showErrorMessage(data.message || 'Произошла ошибка при обработке платежа');
                    setLoadingState(false);
                }
            })
            .catch(error => {
                console.error('Payment error:', error);
                showErrorMessage('Произошла ошибка соединения. Попробуйте еще раз.');
                setLoadingState(false);
            });
        });
    }
    
    /**
     * Установка состояния загрузки для кнопки
     */
    function setLoadingState(loading) {
        if (!payButton) return;
        
        if (loading) {
            payButton.classList.add('loading');
            payButton.disabled = true;
        } else {
            payButton.classList.remove('loading');
            payButton.disabled = false;
        }
    }
    
    /**
     * Валидация формы
     */
    function validateForm() {
        const requiredFields = paymentForm.querySelectorAll('[required]');
        let isValid = true;
        
        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                showFieldError(field, 'Это поле обязательно для заполнения');
                isValid = false;
            } else {
                clearFieldError(field);
            }
        });
        
        // Дополнительная валидация телефона
        const phone = document.getElementById('client-phone');
        if (phone && phone.value) {
            const phoneRegex = /^\+7\s?\(\d{3}\)\s?\d{3}-\d{2}-\d{2}$/;
            if (!phoneRegex.test(phone.value)) {
                showFieldError(phone, 'Введите корректный номер телефона');
                isValid = false;
            }
        }
        
        // Валидация email (если заполнен)
        const email = document.getElementById('client-email');
        if (email && email.value) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(email.value)) {
                showFieldError(email, 'Введите корректный email адрес');
                isValid = false;
            }
        }
        
        return isValid;
    }
    
    /**
     * Показать ошибку поля
     */
    function showFieldError(field, message) {
        clearFieldError(field);
        
        field.style.borderColor = '#ef4444';
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'field-error';
        errorDiv.style.color = '#ef4444';
        errorDiv.style.fontSize = '0.875rem';
        errorDiv.style.marginTop = '4px';
        errorDiv.textContent = message;
        
        field.parentNode.appendChild(errorDiv);
    }
    
    /**
     * Очистить ошибку поля
     */
    function clearFieldError(field) {
        field.style.borderColor = '#e5e7eb';
        
        const existingError = field.parentNode.querySelector('.field-error');
        if (existingError) {
            existingError.remove();
        }
    }
    
    /**
     * Показать сообщение об успехе
     */
    function showSuccessMessage(message) {
        showNotification(message, 'success');
    }
    
    /**
     * Показать сообщение об ошибке
     */
    function showErrorMessage(message) {
        showNotification(message, 'error');
    }
    
    /**
     * Показать уведомление
     */
    function showNotification(message, type) {
        // Удаляем существующие уведомления
        const existingNotifications = document.querySelectorAll('.notification');
        existingNotifications.forEach(n => n.remove());
        
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 16px 20px;
            border-radius: 8px;
            color: white;
            font-weight: 500;
            z-index: 1000;
            max-width: 400px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.2);
            animation: slideIn 0.3s ease;
        `;
        
        if (type === 'success') {
            notification.style.background = '#10b981';
        } else {
            notification.style.background = '#ef4444';
        }
        
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        // Автоматическое скрытие через 5 секунд
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }, 5000);
    }
    
    // CSS анимации для уведомлений
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        
        @keyframes slideOut {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(100%);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);
});

