from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from peanut_bridge.todo_api import create_task

LOCAL_TZ = ZoneInfo("Asia/Bangkok")


def _next_weekday_date(anchor_date, target_weekday: int):
    days_ahead = (target_weekday - anchor_date.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    return anchor_date + timedelta(days=days_ahead)


def create_weekly_tutor_todos(list_name: str = "Funix"):
    today = datetime.now(LOCAL_TZ).date()
    tuesday = _next_weekday_date(today, 1)
    thursday = _next_weekday_date(today, 3)
    saturday = _next_weekday_date(today, 5)

    schedule = [
        (tuesday, time(18, 55), "Gia sư chị Lan"),
        (tuesday, time(19, 58), "Gia sư chị Hương"),
        (tuesday, time(21, 6), "Xác nhận gia sư chị Lan"),
        (tuesday, time(21, 7), "Xác nhận gia sư chị Hương"),
        (thursday, time(18, 55), "Gia sư chị Lan"),
        (thursday, time(19, 58), "Gia sư chị Hương"),
        (thursday, time(21, 6), "Xác nhận gia sư chị Lan"),
        (thursday, time(21, 7), "Xác nhận gia sư chị Hương"),
        (saturday, time(18, 55), "Gia sư chị Lan"),
        (saturday, time(20, 6), "Xác nhận gia sư chị Lan"),
    ]

    lines = ["📌 Weekly tutor reminders:"]
    created = 0
    failed = 0

    for day, at_time, base_title in schedule:
        if day.weekday() == 1:
            day_label = "thứ 3"
        elif day.weekday() == 3:
            day_label = "thứ 5"
        else:
            day_label = "thứ 7"

        title = f"{base_title} {day_label} {at_time.strftime('%H:%M')}"
        remind_dt = datetime.combine(day, at_time)
        remind_str = remind_dt.strftime("%Y-%m-%dT%H:%M:%S")
        task_obj = {
            "title": title,
            "remind": remind_str,
            "listName": list_name,
            "subTasks": [],
        }

        try:
            result = create_task(task_obj)
            lines.append(f"{day} {at_time.strftime('%H:%M')} - {title}: {result}")
            created += 1
        except Exception as exc:
            lines.append(f"{day} {at_time.strftime('%H:%M')} - {title}: ❌ Failed: {exc}")
            failed += 1

    return {
        "created": created,
        "failed": failed,
        "report": "\n".join(lines),
    }
