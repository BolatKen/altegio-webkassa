# SSL Сертификаты

Эта директория предназначена для размещения SSL сертификатов.

## Получение SSL сертификатов с Let's Encrypt

### 1. Установка Certbot

```bash
# На Ubuntu/Debian
sudo apt update
sudo apt install certbot python3-certbot-nginx

# На CentOS/RHEL
sudo yum install certbot python3-certbot-nginx
```

### 2. Получение сертификата

```bash
# Замените your-domain.com на ваш домен
sudo certbot --nginx -d your-domain.com

# Или для нескольких доменов
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

### 3. Автоматическое обновление

```bash
# Добавить в crontab для автоматического обновления
sudo crontab -e

# Добавить строку:
0 12 * * * /usr/bin/certbot renew --quiet
```

## Ручная установка сертификатов

Если у вас есть готовые сертификаты, разместите их в этой директории:

- `fullchain.pem` - полная цепочка сертификатов
- `privkey.pem` - приватный ключ

### Пример структуры:

```
nginx/ssl/
├── fullchain.pem
├── privkey.pem
└── README.md
```

## Настройка Nginx

После получения сертификатов:

1. Раскомментируйте HTTPS блок в `nginx/default.conf`
2. Замените `your-domain.com` на ваш домен
3. Перезапустите контейнеры:

```bash
docker-compose down
docker-compose up -d
```

## Проверка SSL

После настройки проверьте SSL:

```bash
# Проверка сертификата
openssl s_client -connect your-domain.com:443 -servername your-domain.com

# Проверка через браузер
https://your-domain.com
```

## Безопасность

- Убедитесь, что файлы сертификатов имеют правильные права доступа
- Регулярно обновляйте сертификаты
- Используйте HSTS заголовки для дополнительной безопасности

