# nginx/Dockerfile
FROM nginx:1.25-alpine

# Копируем конфигурацию
COPY conf.d/default.conf /etc/nginx/conf.d/default.conf

# Создаем папку для статических файлов
RUN mkdir -p /app/static

# Создаем папку для логов
RUN mkdir -p /var/log/nginx

# Открываем порт 80
EXPOSE 80

# Запускаем Nginx
CMD ["nginx", "-g", "daemon off;"]