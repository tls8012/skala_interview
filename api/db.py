import psycopg
from psycopg.rows import dict_row
from api.config import settings


def connection():
    # The production URL is Neon's pooled endpoint. Keep each request's
    # connection short-lived and avoid session-level prepared statements.
    return psycopg.connect(
        settings("DATABASE_URL"), row_factory=dict_row, connect_timeout=10,
        prepare_threshold=None,
    )
