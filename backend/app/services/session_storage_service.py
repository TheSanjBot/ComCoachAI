from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import HTTPException, status

from app.core.config import settings


class SessionStorageService:
    def __init__(self, user_id: str, namespace: str):
        self.user_id = user_id
        self.namespace = namespace

    @property
    def root_dir(self) -> Path:
        path = settings.reports_dir_path / self.namespace / self.user_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def create_id(self) -> str:
        return uuid4().hex

    def load(self, session_id: str) -> dict[str, Any]:
        path = self.root_dir / f"{session_id}.json"
        if not path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} was not found.",
            )
        return json.loads(path.read_text(encoding="utf-8"))

    def save(self, session_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        path = self.root_dir / f"{session_id}.json"
        payload["updated_at"] = datetime.now(timezone.utc).isoformat()
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return payload
