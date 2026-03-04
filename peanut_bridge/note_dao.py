from datetime import datetime
from bson import ObjectId
from re import escape
from pathlib import Path
import json

from peanut_bridge.mongo_connection import get_db
from peanut_bridge.note_models import Note


db = get_db()
collection = db["notes"]
FALLBACK_PATH = Path(__file__).resolve().parents[1] / "data" / "notes_fallback.json"


def _fs_load():
    if not FALLBACK_PATH.exists():
        return []
    try:
        return json.loads(FALLBACK_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []


def _fs_save(items):
    FALLBACK_PATH.parent.mkdir(parents=True, exist_ok=True)
    FALLBACK_PATH.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")


def _fs_to_notes(items):
    out = []
    for item in items:
        out.append(
            Note(
                title=item.get("title", ""),
                content=item.get("content", ""),
                tags=item.get("tags", []),
                _id=item.get("id"),
                created_at=item.get("created_at"),
                updated_at=item.get("updated_at"),
            )
        )
    return out


def get_all():
    try:
        docs = collection.find().sort("updated_at", -1)
        return [Note.from_dict(doc) for doc in docs]
    except Exception:
        items = sorted(_fs_load(), key=lambda x: x.get("updated_at", ""), reverse=True)
        return _fs_to_notes(items)


def save(note: Note):
    note.updated_at = datetime.utcnow()
    try:
        if note.id:
            collection.update_one(
                {"_id": ObjectId(note.id)},
                {"$set": note.to_dict()},
                upsert=True,
            )
            return str(note.id)

        note.created_at = datetime.utcnow()
        res = collection.insert_one(note.to_dict())
        return str(res.inserted_id)
    except Exception:
        items = _fs_load()
        note_id = note.id or str(ObjectId())
        now_iso = datetime.utcnow().isoformat()
        found = False
        for i, item in enumerate(items):
            if item.get("id") == note_id:
                items[i] = {
                    "id": note_id,
                    "title": note.title,
                    "content": note.content,
                    "tags": note.tags,
                    "updated_at": now_iso,
                    "created_at": item.get("created_at") or now_iso,
                }
                found = True
                break
        if not found:
            items.append(
                {
                    "id": note_id,
                    "title": note.title,
                    "content": note.content,
                    "tags": note.tags,
                    "created_at": now_iso,
                    "updated_at": now_iso,
                }
            )
        _fs_save(items)
        return note_id


def find(query: str, tags: list[str] = None):
    try:
        regex = {"$regex": query, "$options": "i"}
        text_part = {"$or": [{"title": regex}, {"content": regex}, {"tags": regex}]}

        if tags:
            filter_query = {"$and": [text_part, {"tags": {"$size": len(tags), "$all": tags}}]}
        else:
            filter_query = text_part

        docs = collection.find(filter_query)
        return [Note.from_dict(doc) for doc in docs]
    except Exception:
        q = query.lower()
        out = []
        for item in _fs_load():
            hay = " ".join(
                [
                    str(item.get("title", "")),
                    str(item.get("content", "")),
                    " ".join(item.get("tags", [])),
                ]
            ).lower()
            if q in hay:
                if tags and sorted(tags) != sorted(item.get("tags", [])):
                    continue
                out.append(
                    Note(
                        title=item.get("title", ""),
                        content=item.get("content", ""),
                        tags=item.get("tags", []),
                        _id=item.get("id"),
                        created_at=item.get("created_at"),
                        updated_at=item.get("updated_at"),
                    )
                )
        return out


def find_by_title_and_tags(title: str, tags: list[str]):
    try:
        query = {"title": {"$regex": f"^{escape(title)}$", "$options": "i"}}
        if tags:
            query["tags"] = {"$all": tags}
        docs = collection.find(query).sort("updated_at", -1)
        return [Note.from_dict(doc) for doc in docs]
    except Exception:
        matches = []
        for item in _fs_load():
            if item.get("title", "").lower() == title.lower():
                if tags and not all(t in item.get("tags", []) for t in tags):
                    continue
                matches.append(
                    Note(
                        title=item.get("title", ""),
                        content=item.get("content", ""),
                        tags=item.get("tags", []),
                        _id=item.get("id"),
                        created_at=item.get("created_at"),
                        updated_at=item.get("updated_at"),
                    )
                )
        return matches
