@echo off
echo Запуск ngrok туннеля для Altegio webhook...
echo.
echo Ваш сервер должен быть запущен на порту 8000
echo Проверьте: docker-compose up
echo.
echo После запуска ngrok:
echo 1. Скопируйте HTTPS URL (например: https://abc123.ngrok.io)
echo 2. В Altegio укажите webhook URL: https://abc123.ngrok.io/webhook/test
echo 3. После тестирования замените на: https://abc123.ngrok.io/webhook
echo.
pause
ngrok http 8000
