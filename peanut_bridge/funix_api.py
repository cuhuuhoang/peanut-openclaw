import os
import re
from html import unescape
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import requests

from peanut_bridge.env import load_env
from peanut_bridge.todo_api import create_task

load_env()

LOCAL_TZ = ZoneInfo("Asia/Bangkok")
DATA_URL = "https://portal.funix.edu.vn/web/dataset/call_kw/fx.aca.live_session/read"
AVAILABLE_SLOT_URL = "https://portal.funix.edu.vn/web/dataset/call_kw/fx.calendar.available_slot/create"
PORTAL_CALENDAR_URL = (
    "https://portal.funix.edu.vn/web"
    "#menu_id=182&action=1171&model=fx.calendar.available_slot&view_type=calendar&cids=1"
)


def build_funix_headers():
    session_id = os.getenv("FUNIX_SESSION_ID", "")
    if not session_id:
        raise ValueError("FUNIX_SESSION_ID is missing in environment")

    headers = {
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
        "Content-Type": "application/json",
        "Cookie": (
            "cids=1; "
            "twk_uuid_5771f0afdef120b32d63a5ca="
            "%7B%22uuid%22%3A%221.Swrbu9qOs5lm0MoRbW9cWnOeREMrGBwce1ag1gJ56OHWwHG7En7kHgc6IYxz5JBuxYev4VSF0sDkg3gHI4f5qz9L2XhvplwbD0WPk7mlRSQJ6QS03VcQ1%22%2C%22version%22%3A3%2C%22domain%22%3A%22funix.edu.vn%22%2C%22ts%22%3A1705237419187%7D; "
            f"session_id={session_id}; "
            "_ga_H10HW2P42X=GS1.1.1716174173.194.0.1716174173.0.0.0; "
            "_ga=GA1.3.1941652760.1700298091; "
            "_gid=GA1.3.695889232.1716174173"
        ),
        "Origin": "https://portal.funix.edu.vn",
        "Referer": "https://portal.funix.edu.vn/web",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/119.0.0.0 Safari/537.36"
        ),
        "sec-ch-ua": '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Linux"',
    }
    return headers


def parse_portal_url(url: str):
    if not url.startswith("https://portal.funix.edu.vn/"):
        raise ValueError("Invalid FUNiX URL")

    parsed = urlparse(url)
    params = parse_qs(parsed.fragment or "")
    try:
        record_id = int(params.get("id", [None])[0])
        model = params.get("model", [None])[0]
    except Exception as exc:
        raise ValueError("Invalid FUNiX URL fragment") from exc

    if not record_id or not model:
        raise ValueError("Missing id or model in FUNiX URL")

    return record_id, model


def parse_zoom_summary(html_text: str):
    text = unescape(re.sub(r"<[^>]+>", " ", html_text))
    text = re.sub(r"\s+", " ", text).strip()

    zoom_id_match = re.search(r"Meeting ID[:\s]+(\d{9,})", text, re.IGNORECASE)
    zoom_id = zoom_id_match.group(1) if zoom_id_match else None

    time_match = re.search(r"(\d{1,2}:\d{2}\s+\d{1,2}/\d{1,2}/\d{4})", text)
    time_str = time_match.group(1) if time_match else None

    topic_match = re.search(r"Topic[:\s]*(.+?)Join Meeting", text, re.IGNORECASE)
    topic = topic_match.group(1).strip() if topic_match else text

    title = topic
    course = None
    course_match = re.search(r"môn\s+([A-Z]+\d+[A-Z]?)", topic, re.IGNORECASE)
    if course_match:
        course = course_match.group(1)
        if "_" in course:
            course = course.split("_")[0]

    topic_lower = topic.lower()
    if "assignment" in topic_lower:
        cat = "Asm"
    elif "lab" in topic_lower:
        cat = "Lab"
    elif "final" in topic_lower:
        cat = "Final"
    elif "hỏi đáp" in topic_lower or "hoi dap" in topic_lower:
        cat = "Zoom"
    else:
        cat = None

    if cat and course:
        title = f"{cat} {course}"
    elif cat:
        title = cat
    elif course:
        title = course

    if not (time_str and zoom_id):
        raise ValueError("Could not extract time and/or Zoom ID")

    return {"title": title, "time": time_str, "zoom_id": zoom_id}


def fetch_session_data(record_id: int, model: str):
    headers = build_funix_headers()
    payload = {
        "id": 6,
        "jsonrpc": "2.0",
        "method": "call",
        "params": {
            "args": [[record_id], ["zoom_summary"]],
            "model": model,
            "method": "read",
            "kwargs": {
                "context": {
                    "bin_size": True,
                    "lang": "vi_VN",
                    "tz": "Asia/Saigon",
                    "uid": 19851,
                    "allowed_company_ids": [1],
                }
            },
        },
    }

    resp = requests.post(DATA_URL, headers=headers, json=payload, timeout=20)
    if resp.status_code != 200:
        raise RuntimeError(f"FUNiX API returned {resp.status_code}")

    data = resp.json()
    result = data.get("result") if isinstance(data, dict) else None
    if not isinstance(result, list) or not result:
        raise RuntimeError("Invalid FUNiX response payload")

    zoom_summary = result[0].get("zoom_summary")
    if not zoom_summary:
        raise RuntimeError("No zoom_summary found in FUNiX response")

    parsed = parse_zoom_summary(zoom_summary)
    session_time = datetime.strptime(parsed["time"], "%H:%M %d/%m/%Y").replace(tzinfo=LOCAL_TZ)
    remind_time = session_time - timedelta(minutes=3)
    now = datetime.now(LOCAL_TZ)

    if remind_time <= now:
        raise ValueError("Session is too soon (remind time already passed)")
    if remind_time - now > timedelta(days=7):
        raise ValueError("Session is too far away (>7 days)")

    return {
        "title": parsed["title"],
        "time": parsed["time"],
        "zoom_id": parsed["zoom_id"],
        "session_time": session_time.strftime("%Y-%m-%dT%H:%M:%S"),
        "remind_time": remind_time.strftime("%Y-%m-%dT%H:%M:%S"),
    }


def extract_session_from_url(url: str):
    record_id, model = parse_portal_url(url)
    session = fetch_session_data(record_id, model)
    session["record_id"] = record_id
    session["model"] = model
    session["url"] = url
    return session


def create_todo_from_url(url: str, list_name: str = "Funix"):
    session = extract_session_from_url(url)
    task_obj = {
        "listName": list_name,
        "title": f"{session['title']} {session['time']} {session['zoom_id']}",
        "remind": session["remind_time"],
        "subTasks": [session["zoom_id"], url],
    }
    todo_message = create_task(task_obj)
    return {"session": session, "todo": {"task": task_obj, "message": todo_message}}


def _mentor_id() -> int:
    return int(os.getenv("FUNIX_MENTOR_ID", "41981"))


def _user_id() -> int:
    return int(os.getenv("FUNIX_UID", "19851"))


def create_available_slot(date_str: str, start_time: str, end_time: str, mentor_id: int | None = None, timeout: int = 20):
    headers = build_funix_headers()
    mentor = mentor_id or _mentor_id()
    user_id = _user_id()

    payload = {
        "id": 15,
        "jsonrpc": "2.0",
        "method": "call",
        "params": {
            "args": [
                {
                    "mentor_id": mentor,
                    "is_available": True,
                    "start_datetime": f"{date_str} {start_time}",
                    "end_datetime": f"{date_str} {end_time}",
                }
            ],
            "model": "fx.calendar.available_slot",
            "method": "create",
            "kwargs": {
                "context": {
                    "lang": "vi_VN",
                    "tz": "Asia/Saigon",
                    "uid": user_id,
                    "allowed_company_ids": [1],
                    "params": {
                        "menu_id": 182,
                        "action": 1171,
                        "model": "fx.calendar.available_slot",
                        "view_type": "calendar",
                        "cids": 1,
                    },
                    "search_default_filter_all_available_slot": 1,
                    "default_start_datetime": f"{date_str} {start_time}",
                    "default_end_datetime": f"{date_str} {end_time}",
                }
            },
        },
    }

    response = requests.post(AVAILABLE_SLOT_URL, headers=headers, json=payload, timeout=timeout)
    response.raise_for_status()
    return response.json()


def next_week_dates(anchor_date=None):
    today = anchor_date or datetime.now().date()
    days_until_monday = (7 - today.weekday()) % 7
    if days_until_monday == 0:
        days_until_monday = 7
    next_monday = today + timedelta(days=days_until_monday)
    return [(next_monday + timedelta(days=offset)).strftime("%Y-%m-%d") for offset in range(7)]


def create_weekly_slots_report(mentor_id: int | None = None):
    log_lines = []
    dates = next_week_dates()
    log_lines.append("Next week's dates (Monday-Sunday):")
    log_lines.append(", ".join(dates))

    local_tz = ZoneInfo("Asia/Bangkok")
    mon, tue, wed, thu, fri, sat, sun = range(7)
    weekly_config = [
        (mon, [("18:30:00", "20:00:00"), ("20:00:00", "20:50:00")]),
        (tue, [("18:30:00", "19:00:00")]),
        (wed, [("18:30:00", "20:00:00"), ("20:00:00", "20:50:00")]),
        (thu, [("18:30:00", "19:00:00")]),
        (fri, [("18:30:00", "20:00:00"), ("20:00:00", "21:00:00")]),
        (sat, [("18:30:00", "19:00:00"), ("20:00:00", "21:00:00"), ("09:30:00", "11:00:00")]),
        (sun, [("18:30:00", "20:00:00"), ("20:00:00", "20:50:00"), ("09:30:00", "11:00:00")]),
    ]
    weekday_to_slots = {weekday: slots for weekday, slots in weekly_config}

    created = 0
    failed = 0

    for index, day in enumerate(dates):
        for start_local, end_local in weekday_to_slots.get(index, []):
            start_local_dt = datetime.strptime(f"{day} {start_local}", "%Y-%m-%d %H:%M:%S").replace(tzinfo=local_tz)
            end_local_dt = datetime.strptime(f"{day} {end_local}", "%Y-%m-%d %H:%M:%S").replace(tzinfo=local_tz)
            start_utc = start_local_dt.astimezone(ZoneInfo("UTC"))
            end_utc = end_local_dt.astimezone(ZoneInfo("UTC"))
            try:
                result = create_available_slot(
                    start_utc.strftime("%Y-%m-%d"),
                    start_utc.strftime("%H:%M:%S"),
                    end_utc.strftime("%H:%M:%S"),
                    mentor_id=mentor_id,
                )
                log_lines.append(f"{day} ({start_local}-{end_local}): {result}")
                created += 1
            except Exception as exc:
                log_lines.append(f"{day} ({start_local}-{end_local}): ERROR {exc}")
                failed += 1

    log_lines.append(PORTAL_CALENDAR_URL)
    return {
        "created": created,
        "failed": failed,
        "report": "\n".join(log_lines),
    }
