from __future__ import annotations
import threading
import uuid
from datetime import datetime, timezone

import numpy as np

from app.models.identity import Identity
from app.store.db import get_connection


class IdentityRepo:
    """CRUD for identities and face embeddings.

    Maintains an in-memory embedding cache that is reloaded on every mutation.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._embedding_cache: dict[str, list[np.ndarray]] = {}
        self._name_cache: dict[str, str] = {}  # identity_id → name

    def load_cache(self) -> None:
        """Load all embeddings into memory. Call once at startup and after mutations."""
        conn = get_connection()
        try:
            conn.execute("PRAGMA foreign_keys = ON")
            rows = conn.execute(
                "SELECT e.identity_id, e.embedding, i.name "
                "FROM embeddings e JOIN identities i ON i.id = e.identity_id"
            ).fetchall()
        finally:
            conn.close()

        cache: dict[str, list[np.ndarray]] = {}
        names: dict[str, str] = {}
        for row in rows:
            iid = row["identity_id"]
            emb = np.frombuffer(row["embedding"], dtype=np.float32).copy()
            cache.setdefault(iid, []).append(emb)
            names[iid] = row["name"]

        with self._lock:
            self._embedding_cache = cache
            self._name_cache = names

    def get_embeddings(self) -> dict[str, list[np.ndarray]]:
        with self._lock:
            return dict(self._embedding_cache)

    def get_name(self, identity_id: str) -> str | None:
        with self._lock:
            return self._name_cache.get(identity_id)

    def list_identities(self) -> list[Identity]:
        conn = get_connection()
        try:
            rows = conn.execute(
                "SELECT i.id, i.name, i.created_at, COUNT(e.id) as sample_count "
                "FROM identities i LEFT JOIN embeddings e ON e.identity_id = i.id "
                "GROUP BY i.id ORDER BY i.created_at DESC"
            ).fetchall()
        finally:
            conn.close()
        return [
            Identity(
                id=r["id"],
                name=r["name"],
                createdAt=r["created_at"],
                sampleCount=r["sample_count"],
            )
            for r in rows
        ]

    def create_identity(self, name: str) -> Identity:
        identity_id = str(uuid.uuid4())
        created_at = datetime.now(tz=timezone.utc).isoformat()
        conn = get_connection()
        try:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute(
                "INSERT INTO identities (id, name, created_at) VALUES (?, ?, ?)",
                (identity_id, name, created_at),
            )
            conn.commit()
        finally:
            conn.close()
        return Identity(id=identity_id, name=name, createdAt=created_at, sampleCount=0)

    def delete_identity(self, identity_id: str) -> bool:
        conn = get_connection()
        try:
            conn.execute("PRAGMA foreign_keys = ON")
            cur = conn.execute("DELETE FROM identities WHERE id = ?", (identity_id,))
            conn.commit()
            deleted = cur.rowcount > 0
        finally:
            conn.close()
        if deleted:
            self.load_cache()
        return deleted

    def add_embedding(self, identity_id: str, embedding: np.ndarray) -> None:
        emb_id = str(uuid.uuid4())
        created_at = datetime.now(tz=timezone.utc).isoformat()
        blob = embedding.astype(np.float32).tobytes()
        conn = get_connection()
        try:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute(
                "INSERT INTO embeddings (id, identity_id, embedding, created_at) VALUES (?, ?, ?, ?)",
                (emb_id, identity_id, blob, created_at),
            )
            conn.commit()
        finally:
            conn.close()
        self.load_cache()
