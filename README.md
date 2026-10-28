# DutyCloud — ЛР2 (оркестрація та хореографія мікросервісів)

Стек: Python/Flask, Traefik (gateway + discovery + балансування), RabbitMQ, Docker Compose.

## Запуск
    docker compose up -d --build
    python demo.py                       # pip install requests

## Масштабування
    docker compose up -d --scale schedule-service=3 --scale notification-service=2
    docker compose ps

## Корисні адреси
- API Gateway:      http://localhost:8000/api/...
- Дашборд Traefik:  http://localhost:8080
- RabbitMQ UI:      http://localhost:15672  (guest / guest)

## Логи консьюмера
    docker compose logs -f notification-service

## Зупинка
    docker compose down        # додайте -v, щоб видалити БД
