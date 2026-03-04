#!/usr/bin/env python3
import json
import sys
from pathlib import Path

# Ensure repo root is importable even when invoked from arbitrary cwd.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from peanut_bridge.note_dao import save as save_note, find as find_notes, get_all as get_all_notes
from peanut_bridge.note_models import Note
from peanut_bridge.todo_api import create_task, set_my_day
from peanut_bridge.funix_api import extract_session_from_url, create_todo_from_url, create_weekly_slots_report
from peanut_bridge.tutor_weekly import create_weekly_tutor_todos


def _ok(data):
    print(json.dumps({"ok": True, "data": data}, ensure_ascii=False))


def _err(msg):
    print(json.dumps({"ok": False, "error": str(msg)}, ensure_ascii=False))


def _load_payload(raw: str):
    if not raw:
        return {}
    return json.loads(raw)


def main():
    if len(sys.argv) < 2:
        _err("missing action")
        sys.exit(1)

    action = sys.argv[1]
    payload_raw = sys.argv[2] if len(sys.argv) > 2 else "{}"

    try:
        payload = _load_payload(payload_raw)
        if action == "todo_create_task":
            msg = create_task(payload)
            _ok({"message": msg})
            return

        if action == "todo_set_my_day":
            msg = set_my_day()
            _ok({"message": msg})
            return

        if action == "note_save":
            title = (payload.get("title") or "").strip()
            content = payload.get("content") or ""
            tags = payload.get("tags") or []
            if not title:
                raise ValueError("title is required")
            note = Note(title=title, content=content, tags=tags)
            note_id = save_note(note)
            _ok({"id": note_id, "title": title})
            return

        if action == "note_find":
            query = (payload.get("query") or "").strip()
            tags = payload.get("tags")
            if not query:
                raise ValueError("query is required")
            notes = find_notes(query, tags)
            _ok(
                {
                    "count": len(notes),
                    "items": [
                        {
                            "id": n.id,
                            "title": n.title,
                            "content": n.content,
                            "tags": n.tags,
                        }
                        for n in notes
                    ],
                }
            )
            return

        if action == "note_all":
            notes = get_all_notes()
            _ok(
                {
                    "count": len(notes),
                    "items": [
                        {
                            "id": n.id,
                            "title": n.title,
                            "content": n.content,
                            "tags": n.tags,
                        }
                        for n in notes
                    ],
                }
            )
            return

        if action == "funix_extract_session_from_url":
            url = (payload.get("url") or "").strip()
            if not url:
                raise ValueError("url is required")
            data = extract_session_from_url(url)
            _ok(data)
            return

        if action == "funix_create_todo_from_url":
            url = (payload.get("url") or "").strip()
            if not url:
                raise ValueError("url is required")
            list_name = (payload.get("listName") or "Funix").strip() or "Funix"
            data = create_todo_from_url(url, list_name)
            _ok(data)
            return

        if action == "funix_create_weekly_slots":
            mentor_id = payload.get("mentorId")
            data = create_weekly_slots_report(mentor_id=mentor_id)
            _ok(data)
            return

        if action == "todo_create_weekly_tutor":
            list_name = (payload.get("listName") or "Funix").strip() or "Funix"
            data = create_weekly_tutor_todos(list_name=list_name)
            _ok(data)
            return

        raise ValueError(f"unknown action: {action}")
    except Exception as exc:
        _err(exc)
        sys.exit(2)


if __name__ == "__main__":
    main()
