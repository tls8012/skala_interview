import base64
import hashlib
import getpass
import secrets

password = getpass.getpass("공동 비밀번호: ")
if not password:
    raise SystemExit("비밀번호는 비울 수 없습니다.")
salt = secrets.token_bytes(24)
iterations = 600_000
digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations)
print(
    f"pbkdf2_sha256${iterations}$"
    f"{base64.urlsafe_b64encode(salt).decode().rstrip('=')}$"
    f"{digest.hex()}"
)
