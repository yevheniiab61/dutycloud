"""Демонстрація роботи DutyCloud через API Gateway (http://localhost:8000).
Запуск:  pip install requests   і   python demo.py
"""
import collections
import json
import sys

import requests

BASE = "http://localhost:8000/api"


def show(title, resp):
    print(f"\n=== {title}  [HTTP {resp.status_code}]")
    try:
        print(json.dumps(resp.json(), ensure_ascii=False, indent=2))
    except ValueError:
        print(resp.text)


def main():
    # 1. Синхронний ланцюжок з рядком: schedule -> identity -> notification
    r = requests.get(f"{BASE}/schedule/chain", params={"text": "Hello"})
    show("1. Синхронний ланцюжок (HTTP/REST)", r)

    # 2. Балансування: 12 запитів, дивимось, які інстанси schedule-service відповіли
    hits = collections.Counter(
        requests.get(f"{BASE}/schedule/health").json()["instance"] for _ in range(12)
    )
    print("\n=== 2. Балансування навантаження (12 запитів до schedule-service)")
    for instance, count in hits.items():
        print(f"  {instance}: {count}")

    # 3. Автентифікація (identity-service)
    r = requests.post(f"{BASE}/identity/login", json={"username": "admin", "password": "admin123"})
    show("3. Login", r)
    headers = {"Authorization": f"Bearer {r.json()['token']}"}

    # 4. Створення розкладу -> подія ScheduleCreated у RabbitMQ
    r = requests.post(f"{BASE}/schedule/schedules", headers=headers, json={
        "title": "Чергування жовтень", "period_start": "2026-10-01", "period_end": "2026-10-31"})
    show("4. Створення розкладу", r)
    sid = r.json()["id"]

    # 5. Призначення -> AssignmentCreated
    slot = {"schedule_id": sid, "participant": "ivan", "date": "2026-10-10",
            "start": "08:00", "end": "16:00"}
    r = requests.post(f"{BASE}/schedule/assignments", headers=headers, json=slot)
    show("5. Призначення чергування", r)
    aid = r.json()["id"]

    # 6. Конфлікт (той самий учасник, перетин часу) -> 409
    r = requests.post(f"{BASE}/schedule/assignments", headers=headers,
                      json={**slot, "start": "12:00", "end": "20:00"})
    show("6. Перевірка конфлікту", r)

    # 7. Зміна -> AssignmentUpdated
    r = requests.put(f"{BASE}/schedule/assignments/{aid}", headers=headers,
                     json={"start": "09:00", "end": "17:00"})
    show("7. Зміна призначення", r)

    # 8. Публікація -> SchedulePublished
    r = requests.post(f"{BASE}/schedule/schedules/{sid}/publish", headers=headers)
    show("8. Публікація розкладу", r)

    # 9. Запит без токена -> 401 (перевірка через identity-service)
    r = requests.post(f"{BASE}/schedule/schedules", json={})
    show("9. Запит без токена", r)

    # 10. Результат асинхронної обробки: що спожив notification-service
    import time
    time.sleep(2)
    r = requests.get(f"{BASE}/notifications")
    show("10. Сповіщення, створені консьюмером", r)


if __name__ == "__main__":
    try:
        main()
    except requests.ConnectionError:
        sys.exit("Gateway недоступний. Спочатку: docker compose up -d --build")
