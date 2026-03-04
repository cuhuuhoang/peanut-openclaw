from datetime import datetime
from bson import ObjectId


class Note:
    def __init__(
        self,
        title: str,
        content: str,
        tags=None,
        _id=None,
        created_at=None,
        updated_at=None,
    ):
        self.id = str(_id) if _id else None
        self.title = title
        self.content = content
        self.tags = tags or []
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()

    def to_dict(self):
        data = {
            "title": self.title,
            "content": self.content,
            "tags": self.tags,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        if self.id:
            data["_id"] = ObjectId(self.id)
        return data

    @staticmethod
    def from_dict(data):
        return Note(
            title=data["title"],
            content=data.get("content", ""),
            tags=data.get("tags", []),
            _id=data.get("_id"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )
