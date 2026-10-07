import os
from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi import HTTPException, Request

KST = ZoneInfo("Asia/Seoul")
SESSION_SECONDS = 30 * 24 * 60 * 60
COOKIE_NAME = "notes_session"


def settings(name: str) -> str:
    value = os.getenv(name, "")
    if not value:
        raise RuntimeError(f"Missing {name}")
    return value


def season_now() -> str:
    now = datetime.now(KST)
    return f"{now.year}-H{1 if now.month <= 6 else 2}"


def check_origin(request: Request) -> None:
    origin = request.headers.get("origin")
    expected = settings("APP_ORIGIN").rstrip("/")
    if origin != expected:
        raise HTTPException(403, "허용되지 않은 요청입니다.")
