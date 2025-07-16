# PowerShell скрипт для решения проблемы отсутствия API ключа Webkassa

Write-Host "🔧 Решение проблемы отсутствия API ключа Webkassa" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Проверяем работу сервера
Write-Host "1️⃣ Проверяем статус сервера..." -ForegroundColor Yellow

try {
    $response = Invoke-RestMethod -Uri "http://165.227.159.243:8001/health" -TimeoutSec 10
    Write-Host "✅ Сервер работает (165.227.159.243:8001)" -ForegroundColor Green
} catch {
    Write-Host "❌ Сервер недоступен (165.227.159.243:8001)" -ForegroundColor Red
    Write-Host "🔍 Возможные причины:" -ForegroundColor Yellow
    Write-Host "   - Сервер не запущен"
    Write-Host "   - Проблемы с сетью"
    Write-Host "   - Порт 8001 заблокирован"
    exit 1
}

Write-Host ""
Write-Host "2️⃣ Попытка автоматического получения API ключа..." -ForegroundColor Yellow

# Пытаемся обновить API ключ через эндпоинт
try {
    $apiResponse = Invoke-RestMethod -Uri "http://165.227.159.243:8001/webhook/refresh-api-key" -Method POST -TimeoutSec 30
    
    if ($apiResponse.success -eq $true) {
        Write-Host "✅ API ключ успешно обновлен через веб-эндпоинт" -ForegroundColor Green
    } else {
        Write-Host "⚠️ Веб-эндпоинт вернул ошибку: $($apiResponse.error)" -ForegroundColor Yellow
        Write-Host "📋 Проверьте логи на сервере для подробностей" -ForegroundColor Cyan
        exit 1
    }
} catch {
    Write-Host "❌ Ошибка при обращении к веб-эндпоинту: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "🔍 Возможные причины:" -ForegroundColor Yellow
    Write-Host "   - Неверные credentials в .env файле на сервере"
    Write-Host "   - Проблемы с сетью до API Webkassa"
    Write-Host "   - API Webkassa недоступен"
    Write-Host ""
    Write-Host "📋 Проверьте логи на сервере" -ForegroundColor Cyan
    exit 1
}

Write-Host ""
Write-Host "3️⃣ Проверяем результат..." -ForegroundColor Yellow

# Тестируем webhook
Write-Host "🧪 Отправляем тестовый webhook..." -ForegroundColor Cyan

$testData = @{
    test = "api_key_fix_test"
    timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
} | ConvertTo-Json

try {
    $testResponse = Invoke-RestMethod -Uri "http://165.227.159.243:8001/webhook/test" -Method POST -Body $testData -ContentType "application/json"
    Write-Host "✅ Тестовый webhook отправлен" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Ошибка при отправке тестового webhook: $($_.Exception.Message)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host ""
Write-Host "✅ Готово! Проблема должна быть решена." -ForegroundColor Green
Write-Host ""
Write-Host "📱 Проверьте уведомления в Telegram боте" -ForegroundColor Cyan
Write-Host "📋 Логи на сервере: docker logs <container_name>" -ForegroundColor Cyan
Write-Host ""
Write-Host "🔗 Ваш webhook URL для Altegio:" -ForegroundColor Cyan
Write-Host "   http://165.227.159.243:8001/webhook" -ForegroundColor White
