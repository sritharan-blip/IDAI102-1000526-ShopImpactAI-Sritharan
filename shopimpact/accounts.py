"""Email/password accounts backed by ShopImpact's PostgreSQL database."""
from email.utils import parseaddr
from hashlib import scrypt, sha256
from hmac import compare_digest
from secrets import token_bytes
from threading import BoundedSemaphore
from uuid import uuid4

from .cloud import _connect


_hash_slots = BoundedSemaphore(4)
_dummy_salt = token_bytes(16)


class AccountInputError(ValueError):
    """The form data was rejected before opening a workspace."""


def _email(value: str) -> str:
    email = value.strip().lower()
    _, address = parseaddr(email)
    local, _, domain = email.rpartition("@")
    if (not local or "." not in domain or len(email) > 254 or address != email
            or email.count("@") != 1 or any(c.isspace() for c in email)):
        raise AccountInputError("Enter a valid email address.")
    return email


def _derive(password: str, salt: bytes) -> bytes:
    # This scrypt work factor uses 32 MiB per check. The semaphore limits parallel work.
    return scrypt(password.encode("utf-8"), salt=salt, n=2**15, r=8, p=3, dklen=32, maxmem=64 * 1024**2)


def _limit(conn, bucket: str, maximum: int) -> bool:
    key = sha256(bucket.encode()).hexdigest()
    # Count each attempt before hashing, across Streamlit sessions and workers.
    count, = conn.execute(
        """INSERT INTO shopimpact_private.shopimpact_auth_limits AS limits (bucket, starts_at, attempts)
           VALUES (%s, CURRENT_TIMESTAMP, 1)
           ON CONFLICT (bucket) DO UPDATE
           SET starts_at = CASE WHEN limits.starts_at < CURRENT_TIMESTAMP - INTERVAL '5 minutes'
                                THEN CURRENT_TIMESTAMP ELSE limits.starts_at END,
               attempts = CASE WHEN limits.starts_at < CURRENT_TIMESTAMP - INTERVAL '5 minutes'
                               THEN 1 ELSE LEAST(limits.attempts + 1, 1000) END
           RETURNING attempts""",
        (key,),
    ).fetchone()
    return count <= maximum


def authenticate(dsn: str, email: str, password: str, client_ip: str | None,
                 *, name: str | None = None) -> tuple[str, str]:
    email = _email(email)
    if not password or len(password) > 128:
        raise AccountInputError("Use a password between 1 and 128 characters.")
    if name is not None:
        name = name.strip()
        if not 1 <= len(name) <= 80 or len(password) < 15:
            raise AccountInputError("Enter a name and use at least 15 characters for your password.")

    with _connect(dsn) as conn:
        if not _limit(conn, f"source:{client_ip or 'unknown'}", 45):
            allowed = False
        else:
            allowed = _limit(conn, f"email:{email}", 8)
    if not allowed:
        raise AccountInputError("Too many attempts. Try again in five minutes.")

    if not _hash_slots.acquire(blocking=False):
        raise AccountInputError("Sign-in is busy. Please try again in a moment.")
    try:
        if name is not None:
            return _register(dsn, email, password, name)
        with _connect(dsn) as conn:
            row = conn.execute(
                "SELECT owner, display_name, password_hash FROM shopimpact_private.shopimpact_accounts WHERE email = %s",
                (email,),
            ).fetchone()
        salt, expected = (map(bytes.fromhex, row[2].split("$", 1)) if row
                          else (_dummy_salt, bytes(32)))
        # Do the same work for missing accounts and mistyped passwords.
        matched = compare_digest(_derive(password, salt), expected)
        if row is None or not matched:
            raise AccountInputError("Email or password is incorrect.")
        return row[0], row[1]
    finally:
        _hash_slots.release()


def _register(dsn: str, email: str, password: str, name: str) -> tuple[str, str]:
    owner = sha256(uuid4().bytes).hexdigest()
    salt = token_bytes(16)
    password_hash = f"{salt.hex()}${_derive(password, salt).hex()}"
    with _connect(dsn) as conn:
        row = conn.execute(
            """INSERT INTO shopimpact_private.shopimpact_accounts (email, owner, display_name, password_hash)
               VALUES (%s, %s, %s, %s) ON CONFLICT (email) DO NOTHING RETURNING owner""",
            (email, owner, name, password_hash),
        ).fetchone()
    if row is None:
        raise AccountInputError("This account could not be created. If you already have an account, sign in.")
    return owner, name
