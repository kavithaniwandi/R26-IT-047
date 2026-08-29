"""SQLite-backed document collections used in place of MongoDB."""
from __future__ import annotations

import copy
import json
import sqlite3
import threading
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

from bson import ObjectId


def _normalise(value: Any) -> Any:
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, dict):
        return {key: _normalise(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_normalise(item) for item in value]
    return value


def _json_default(value: Any) -> str:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, ObjectId):
        return str(value)
    raise TypeError(f"Cannot serialize {type(value).__name__}")


def _path_values(value: Any, path: str) -> list[Any]:
    values = [value]
    for part in path.split(".") if path else []:
        next_values: list[Any] = []
        for item in values:
            if isinstance(item, dict) and part in item:
                next_values.append(item[part])
            elif isinstance(item, list):
                if part.isdigit() and int(part) < len(item):
                    next_values.append(item[int(part)])
                else:
                    next_values.extend(child[part] for child in item if isinstance(child, dict) and part in child)
        values = next_values
    return values


def _matches(document: dict[str, Any], query: dict[str, Any]) -> bool:
    for key, expected in query.items():
        values = _path_values(document, key)
        if isinstance(expected, dict) and "$regex" in expected:
            needle = str(expected["$regex"])
            insensitive = "i" in str(expected.get("$options", ""))
            if insensitive:
                needle = needle.lower()
            if not any(needle in (str(value).lower() if insensitive else str(value)) for value in values):
                return False
        elif not any(_normalise(value) == _normalise(expected) for value in values):
            return False
    return True


def _set_path(document: dict[str, Any], path: str, value: Any) -> None:
    parts = path.split(".")
    target: Any = document
    for index, part in enumerate(parts[:-1]):
        next_part = parts[index + 1]
        if isinstance(target, list):
            target = target[int(part)]
        elif part not in target:
            target[part] = [] if next_part.isdigit() else {}
            target = target[part]
        else:
            target = target[part]
    if isinstance(target, list):
        target[int(parts[-1])] = _normalise(value)
    else:
        target[parts[-1]] = _normalise(value)


@dataclass
class InsertOneResult:
    inserted_id: str


@dataclass
class InsertManyResult:
    inserted_ids: list[str]


@dataclass
class DeleteResult:
    deleted_count: int


class SQLiteCursor:
    def __init__(self, documents: list[dict[str, Any]]):
        self.documents = documents

    def sort(self, field: str, direction: int):
        self.documents.sort(key=lambda document: str((_path_values(document, field) or [""])[0]), reverse=direction < 0)
        return self

    async def to_list(self, length: int | None = None) -> list[dict[str, Any]]:
        return copy.deepcopy(self.documents[:length])


class SQLiteCollection:
    def __init__(self, name: str):
        self.name = name

    def _load_all(self) -> list[dict[str, Any]]:
        with _db_lock, _connect() as connection:
            rows = connection.execute("SELECT id, payload FROM documents WHERE collection_name = ?", (self.name,)).fetchall()
        documents = []
        for row in rows:
            document = json.loads(row["payload"])
            document["_id"] = row["id"]
            documents.append(document)
        return documents

    def _save(self, document: dict[str, Any]) -> None:
        document = _normalise(copy.deepcopy(document))
        document_id = str(document.pop("_id"))
        with _db_lock, _connect() as connection:
            connection.execute(
                "INSERT INTO documents (collection_name, id, payload) VALUES (?, ?, ?) "
                "ON CONFLICT(collection_name, id) DO UPDATE SET payload = excluded.payload",
                (self.name, document_id, json.dumps(document, default=_json_default)),
            )
            connection.commit()

    async def find_one(self, query: dict[str, Any]) -> dict[str, Any] | None:
        for document in self._load_all():
            if _matches(document, query):
                return copy.deepcopy(document)
        return None

    def find(self, query: dict[str, Any] | None = None, projection: dict[str, int] | None = None) -> SQLiteCursor:
        documents = [document for document in self._load_all() if _matches(document, query or {})]
        if projection:
            include = {key for key, selected in projection.items() if selected}
            documents = [{key: value for key, value in document.items() if key in include} for document in documents]
        return SQLiteCursor(documents)

    async def insert_one(self, document: dict[str, Any]) -> InsertOneResult:
        document_id = str(ObjectId())
        saved = copy.deepcopy(document)
        saved["_id"] = document_id
        self._save(saved)
        return InsertOneResult(inserted_id=document_id)

    async def insert_many(self, documents: list[dict[str, Any]]) -> InsertManyResult:
        ids = []
        for document in documents:
            ids.append((await self.insert_one(document)).inserted_id)
        return InsertManyResult(inserted_ids=ids)

    def import_document(self, document: dict[str, Any]) -> None:
        """Upsert a document from the legacy MongoDB database, preserving its ID."""
        if "_id" not in document:
            raise ValueError("Imported documents must contain an _id")
        self._save(document)

    async def update_one(self, query: dict[str, Any], update: dict[str, Any], upsert: bool = False):
        document = await self.find_one(query)
        if document is None:
            if not upsert:
                return None
            document = _normalise(copy.deepcopy(query))
            document["_id"] = str(ObjectId())
        self._apply_update(document, update)
        self._save(document)
        return document

    async def find_one_and_update(self, query: dict[str, Any], update: dict[str, Any], return_document: Any = None):
        document = await self.find_one(query)
        if document is None:
            return None
        self._apply_update(document, update)
        self._save(document)
        return copy.deepcopy(document)

    async def delete_one(self, query: dict[str, Any]) -> DeleteResult:
        document = await self.find_one(query)
        if document is None:
            return DeleteResult(deleted_count=0)
        with _db_lock, _connect() as connection:
            cursor = connection.execute("DELETE FROM documents WHERE collection_name = ? AND id = ?", (self.name, str(document["_id"])))
            connection.commit()
        return DeleteResult(deleted_count=cursor.rowcount)

    @staticmethod
    def _apply_update(document: dict[str, Any], update: dict[str, Any]) -> None:
        for path, value in update.get("$set", {}).items():
            _set_path(document, path, value)
        for path, value in update.get("$addToSet", {}).items():
            current = list((_path_values(document, path) or [[]])[0])
            if _normalise(value) not in [_normalise(item) for item in current]:
                current.append(_normalise(value))
            _set_path(document, path, current)
        for path, value in update.get("$push", {}).items():
            current = list((_path_values(document, path) or [[]])[0])
            if isinstance(value, dict) and "$each" in value:
                current.extend(_normalise(value["$each"]))
                if "$slice" in value:
                    size = int(value["$slice"])
                    current = current[:size] if size >= 0 else current[size:]
            else:
                current.append(_normalise(value))
            _set_path(document, path, current)


_database_path = Path(__file__).resolve().parents[1] / "disaster_relief.sqlite3"
_database_path.parent.mkdir(parents=True, exist_ok=True)
_db_lock = threading.RLock()


def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(_database_path)
    connection.row_factory = sqlite3.Row
    return connection


with _db_lock, _connect() as _connection:
    _connection.execute("CREATE TABLE IF NOT EXISTS documents (collection_name TEXT NOT NULL, id TEXT NOT NULL, payload TEXT NOT NULL, PRIMARY KEY (collection_name, id))")
    _connection.execute("CREATE INDEX IF NOT EXISTS idx_documents_collection ON documents(collection_name)")
    _connection.commit()


user_collection = SQLiteCollection("users")
disaster_donation_request_collection = SQLiteCollection("disaster_donation_requests")
donation_history_collection = SQLiteCollection("donation_history")
donation_items_collection = SQLiteCollection("donation_items")
division_collection = SQLiteCollection("administrative_divisions")
relief_camp_collection = SQLiteCollection("relief_camps")
