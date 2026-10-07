import base64
import hashlib
import hmac
import os
import re
import secrets
from datetime import datetime, timezone
from fastapi import APIRouter, Cookie, HTTPException, Request, Response
from pydantic import BaseModel, Field
from api.config import COOKIE_NAME, SESSION_SECONDS, check_origin, season_now, settings
from api.db import connection

router = APIRouter()


class LoginBody(BaseModel):
    password: str = Field(min_length=1, max_length=256)


def sign_session(session_id: str, issued: int) -> str:
    payload = f"{session_id}.{issued}"
    signature = hmac.new(settings("SESSION_SECRET").encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{signature}"


def session_id_from_token(token: str | None) -> str:
    if not token:
        raise HTTPException(401, "로그인이 필요합니다.")
    try:
        session_id, issued_text, signature = token.split(".")
        issued = int(issued_text)
        expected = sign_session(session_id, issued).rsplit(".", 1)[1]
        if not hmac.compare_digest(signature, expected):
            raise ValueError("signature")
        if not re.fullmatch(r"[0-9a-f]{64}", session_id):
            raise ValueError("id")
        if issued > datetime.now(timezone.utc).timestamp() + 60:
            raise ValueError("future")
        if datetime.now(timezone.utc).timestamp() - issued > SESSION_SECONDS:
            raise ValueError("expired")
    except (ValueError, TypeError):
        raise HTTPException(401, "세션이 만료되었습니다.") from None
    return session_id


def require_session(token: str | None) -> str:
    return session_id_from_token(token)


def session_hash(session_id: str) -> str:
    return hmac.new(settings("SESSION_SECRET").encode(), session_id.encode(), hashlib.sha256).hexdigest()


def client_hash(request: Request) -> str:
    # Vercel supplies the trusted client address in x-forwarded-for. Locally, use request.client.
    address = request.headers.get("x-forwarded-for", "").split(",", 1)[0].strip()
    if not address:
        address = request.client.host if request.client else "unknown"
    return hmac.new(settings("SESSION_SECRET").encode(), address.encode(), hashlib.sha256).hexdigest()


def verify_password(password: str) -> bool:
    try:
        algorithm, rounds, salt, digest = settings("APP_PASSWORD_HASH").split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        salt_bytes = base64.urlsafe_b64decode(salt + "=" * (-len(salt) % 4))
        candidate = hashlib.pbkdf2_hmac("sha256", password.encode(), salt_bytes, int(rounds))
        return hmac.compare_digest(candidate, bytes.fromhex(digest))
    except (ValueError, TypeError):
        return False


@router.get("/api/session")
def session_status(notes_session: str | None = Cookie(default=None)):
    require_session(notes_session)
    return {"ok": True, "current_season": season_now()}


@router.post("/api/session")
def login(body: LoginBody, request: Request, response: Response):
    check_origin(request)
    key = client_hash(request)
    invalid_password = False
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT count(*) AS count FROM login_attempts "
                "WHERE client_hash = %s AND created_at > now() - interval '10 minutes'",
                (key,),
            )
            if cur.fetchone()["count"] >= 30:
                raise HTTPException(429, "잠시 후 다시 시도해 주세요.")
            if not verify_password(body.password):
                cur.execute("INSERT INTO login_attempts (client_hash) VALUES (%s)", (key,))
                invalid_password = True
    if invalid_password:
        raise HTTPException(401, "비밀번호가 맞지 않습니다.")
    now = int(datetime.now(timezone.utc).timestamp())
    response.set_cookie(
        COOKIE_NAME,
        sign_session(secrets.token_hex(32), now),
        max_age=SESSION_SECONDS,
        httponly=True,
        secure=request.url.scheme == "https" or os.getenv("VERCEL") == "1",
        samesite="lax",
        path="/api",
    )
    response.headers["Cache-Control"] = "no-store"
    return {"ok": True, "current_season": season_now()}


@router.delete("/api/session")
def logout(request: Request, response: Response):
    check_origin(request)
    response.delete_cookie(COOKIE_NAME, path="/api")
    return {"ok": True}
