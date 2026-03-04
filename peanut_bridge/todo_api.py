from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from peanut_bridge.token_manager import get_valid_access_token
from peanut_bridge.graph_api import with_auto_refresh, graph_get, graph_post, graph_patch_beta

GRAPH_BASE_V1 = "https://graph.microsoft.com/v1.0"
GRAPH_WINDOWS_TZ = "SE Asia Standard Time"
LOCAL_TZ = ZoneInfo("Asia/Bangkok")


def create_task(task_obj: dict) -> str:
    list_name = task_obj.get("listName", "Personal")
    title = task_obj.get("title", "").strip()
    sub_tasks = task_obj.get("subTasks", [])
    remind_str = task_obj.get("remind")

    if not title:
        raise ValueError("title is required")

    get_valid_access_token()

    def _req_lists(_, access_token):
        return graph_get(f"{GRAPH_BASE_V1}/me/todo/lists", access_token)

    list_resp = with_auto_refresh(_req_lists, None)
    if list_resp.status_code != 200:
        return f"⚠️ Failed to fetch lists ({list_resp.status_code})"

    lists = list_resp.json().get("value", [])
    list_id = next((l["id"] for l in lists if l["displayName"].lower() == list_name.lower()), None)
    if not list_id and lists:
        list_id = lists[0]["id"]
    if not list_id:
        return "⚠️ No To Do lists found."

    now = datetime.now(LOCAL_TZ)
    payload = {"title": title}

    remind_dt = None
    if remind_str:
        remind_dt = datetime.strptime(remind_str, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=LOCAL_TZ)
        payload.update(
            {
                "isReminderOn": True,
                "reminderDateTime": {
                    "dateTime": remind_dt.strftime("%Y-%m-%dT%H:%M:%S"),
                    "timeZone": GRAPH_WINDOWS_TZ,
                },
            }
        )

    due_dt = None
    if not remind_dt or remind_dt.date() == now.date():
        due_dt = now

    if due_dt:
        payload["dueDateTime"] = {
            "dateTime": due_dt.strftime("%Y-%m-%dT%H:%M:%S"),
            "timeZone": GRAPH_WINDOWS_TZ,
        }

    def _req_create(list_id_arg, access_token):
        return graph_post(f"{GRAPH_BASE_V1}/me/todo/lists/{list_id_arg}/tasks", access_token, payload)

    create_resp = with_auto_refresh(_req_create, list_id)
    if create_resp.status_code != 201:
        return f"❌ Failed to add task ({create_resp.status_code})"

    task = create_resp.json()
    task_id = task.get("id")

    for step in sub_tasks:
        def _req_add_check(_, access_token, step_title=step):
            url = f"{GRAPH_BASE_V1}/me/todo/lists/{list_id}/tasks/{task_id}/checklistItems"
            return graph_post(url, access_token, {"displayName": step_title})

        with_auto_refresh(_req_add_check, None)

    msg_lines = []
    if remind_dt:
        if remind_dt.date() == now.date():
            if due_dt:
                msg_lines.append(f"✅ Added to My Day: {title}")
            else:
                msg_lines.append(f"✅ Added task: {title}")
            msg_lines.append(f"⏰ Reminder set at {remind_dt.strftime('%H:%M')} today")
        else:
            msg_lines.append(f"✅ Added task: {title}")
            msg_lines.append(f"⏰ Reminder set at {remind_dt.strftime('%H:%M %d/%m/%Y')}")
    else:
        msg_lines.append(f"✅ Added to My Day: {title}")

    if sub_tasks:
        msg_lines.append(f"📝 {len(sub_tasks)} steps added")

    return "\n".join(msg_lines)


def set_my_day() -> str:
    get_valid_access_token()
    now = datetime.now(LOCAL_TZ).date()

    def _req_lists(_, access_token):
        return graph_get(f"{GRAPH_BASE_V1}/me/todo/lists", access_token)

    list_resp = with_auto_refresh(_req_lists, None)
    if list_resp.status_code != 200:
        return f"⚠️ Failed to fetch lists ({list_resp.status_code})"

    lists = list_resp.json().get("value", [])
    if not lists:
        return "⚠️ No lists found."

    moved_tasks = []

    for lst in lists:
        list_id = lst["id"]

        def _req_tasks(_, access_token, lid=list_id):
            return graph_get(f"{GRAPH_BASE_V1}/me/todo/lists/{lid}/tasks", access_token)

        task_resp = with_auto_refresh(_req_tasks, None)
        if task_resp.status_code != 200:
            continue

        tasks = task_resp.json().get("value", [])
        for t in tasks:
            rem = t.get("reminderDateTime", {})
            if not rem:
                continue

            try:
                remind_dt = (
                    datetime.strptime(rem["dateTime"], "%Y-%m-%dT%H:%M:%S.%f0")
                    .replace(tzinfo=timezone.utc)
                    .astimezone(LOCAL_TZ)
                )
            except Exception:
                try:
                    remind_dt = (
                        datetime.strptime(rem["dateTime"], "%Y-%m-%dT%H:%M:%S")
                        .replace(tzinfo=timezone.utc)
                        .astimezone(LOCAL_TZ)
                    )
                except Exception:
                    continue

            if remind_dt.date() == now and not t.get("isInMyDay", False):
                task_id = t["id"]
                title = t["title"]

                def _req_patch(_, access_token, lid=list_id, tid=task_id):
                    url = f"https://graph.microsoft.com/beta/me/todo/lists/{lid}/tasks/{tid}"
                    today_iso = datetime.now(LOCAL_TZ).strftime("%Y-%m-%dT%H:%M:%S")
                    payload = {
                        "isInMyDay": True,
                        "dueDateTime": {
                            "dateTime": today_iso,
                            "timeZone": GRAPH_WINDOWS_TZ,
                        },
                    }
                    return graph_patch_beta(url, access_token, payload)

                patch_resp = with_auto_refresh(_req_patch, None)
                if patch_resp.status_code in (200, 204):
                    moved_tasks.append((title, remind_dt))

    if not moved_tasks:
        return "☑️ No tasks to add to My Day today."

    moved_tasks.sort(key=lambda x: x[1])
    lines = ["✅ Added to My Day:"]
    for title, remind_dt in moved_tasks:
        lines.append(f"{title} – {remind_dt.strftime('%H:%M')}")

    return "\n".join(lines)
