import base64
import json
import re
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Cookie, HTTPException, Query, Request
from pydantic import BaseModel, Field
from api.auth import require_session, session_hash
from api.config import check_origin, season_now
from api.db import connection

router = APIRouter()
SEASON_RE = re.compile(r"^\d{4}-H[12]$")


class NoteBody(BaseModel):
    channel: str
    title: str | None = Field(default=None, max_length=120)
    body: str = Field(min_length=1, max_length=5000)
    website: str = ""


def encode_cursor(created_at: datetime, note_id: int) -> str:
    data = json.dumps([created_at.isoformat(), note_id], separators=(",", ":"))
    return base64.urlsafe_b64encode(data.encode()).decode().rstrip("=")


def decode_cursor(cursor: str) -> tuple[datetime, int]:
    try:
        raw = base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4))
        created_at_text, note_id = json.loads(raw)
        created_at = datetime.fromisoformat(created_at_text)
        if created_at.tzinfo is None or not isinstance(note_id, int) or note_id < 1:
            raise ValueError("cursor")
        return created_at, note_id
    except (ValueError, TypeError, UnicodeDecodeError, json.JSONDecodeError):
        raise HTTPException(400, "잘못된 페이지 위치입니다.") from None


def public_note(row: dict) -> dict:
    return {key: row[key] for key in ("id", "season_key", "channel", "title", "body", "created_at")}


@router.get("/api/seasons")
def seasons(notes_session: str | None = Cookie(default=None)):
    require_session(notes_session)
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT DISTINCT season_key FROM notes WHERE status = 'visible' ORDER BY season_key DESC")
            values = [row["season_key"] for row in cur.fetchall()]
    current = season_now()
    return {"current_season": current, "seasons": sorted(set(values + [current]), reverse=True)}


@router.get("/api/notes")
def list_notes(
    notes_session: str | None = Cookie(default=None),
    season: str | None = None,
    channel: str = "info",
    q: str = Query(default="", max_length=100),
    cursor: str | None = Query(default=None, max_length=200),
    limit: int = Query(default=50, ge=1, le=100),
):
    require_session(notes_session)
    if channel not in ("info", "chat"):
        raise HTTPException(400, "잘못된 목록입니다.")
    season = season or season_now()
    if season != "all" and not SEASON_RE.fullmatch(season):
        raise HTTPException(400, "잘못된 시즌입니다.")
    where = ["status = 'visible'", "channel = %s"]
    args: list = [channel]
    if season != "all":
        where.append("season_key = %s")
        args.append(season)
    if q.strip():
        where.append("(title ILIKE %s OR body ILIKE %s)")
        pattern = "%" + q.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
        args.extend([pattern, pattern])
    if cursor:
        where.append("(created_at, id) < (%s, %s)")
        args.extend(decode_cursor(cursor))
    sql = (
        "SELECT id, season_key, channel, title, body, created_at FROM notes WHERE "
        + " AND ".join(where)
        + " ORDER BY created_at DESC, id DESC LIMIT %s"
    )
    args.append(limit + 1)
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, args)
            rows = cur.fetchall()
    has_more = len(rows) > limit
    rows = rows[:limit]
    next_cursor = encode_cursor(rows[-1]["created_at"], rows[-1]["id"]) if has_more else None
    return {"items": [public_note(row) for row in rows], "next_cursor": next_cursor}


@router.get("/api/notes/{note_id}")
def get_note(note_id: int, notes_session: str | None = Cookie(default=None)):
    require_session(notes_session)
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, season_key, channel, title, body, created_at FROM notes "
                "WHERE id = %s AND status = 'visible'",
                (note_id,),
            )
            row = cur.fetchone()
    if row is None:
        raise HTTPException(404, "글을 찾을 수 없습니다.")
    return public_note(row)


@router.post("/api/notes", status_code=201)
def add_note(body: NoteBody, request: Request, notes_session: str | None = Cookie(default=None)):
    session_id = require_session(notes_session)
    check_origin(request)
    if body.channel not in ("info", "chat"):
        raise HTTPException(400, "잘못된 목록입니다.")
    title = body.title.strip() if body.title else None
    content = body.body.strip()
    if not content or len(content) > 5000:
        raise HTTPException(422, "내용은 1~5000자로 입력해 주세요.")
    if title and len(title) > 120:
        raise HTTPException(422, "제목은 120자 이내로 입력해 주세요.")
    key = session_hash(session_id)
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT body, created_at FROM notes WHERE session_hash = %s "
                "AND created_at > now() - interval '1 minute' ORDER BY created_at DESC LIMIT 6",
                (key,),
            )
            recent = cur.fetchall()
            spam_score = 0
            if body.website:
                spam_score += 10
            if recent and recent[0]["created_at"] > datetime.now(timezone.utc) - timedelta(seconds=10):
                spam_score += 3
            if len(recent) >= 5:
                spam_score += 5
            if any(row["body"] == content for row in recent):
                spam_score += 5
            if len(re.findall(r"https?://", content, re.IGNORECASE)) >= 5:
                spam_score += 3
            status = "quarantined" if spam_score >= 3 else "visible"
            cur.execute(
                "INSERT INTO notes (season_key, channel, title, body, status, session_hash, spam_score) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s) "
                "RETURNING id, season_key, channel, title, body, created_at",
                (season_now(), body.channel, title, content, status, key, spam_score),
            )
            row = cur.fetchone()
    return {"item": public_note(row) if status == "visible" else None, "quarantined": status == "quarantined"}
