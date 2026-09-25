import hashlib
import hmac
import secrets

from sqlalchemy.orm import Session

from models.models import User


def hash_password(password: str) -> str:
    """Create a secure salted password hash."""
    salt = secrets.token_bytes(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        100_000
    )

    return f"{salt.hex()}:{password_hash.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify a password against the stored hash."""
    try:
        salt_hex, hash_hex = stored_hash.split(":")

        salt = bytes.fromhex(salt_hex)
        expected_hash = bytes.fromhex(hash_hex)

        actual_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            100_000
        )

        return hmac.compare_digest(actual_hash, expected_hash)

    except (ValueError, TypeError):
        return False


def authenticate_user(
    db: Session,
    username: str,
    password: str
):
    """Authenticate an active user."""
    user = (
        db.query(User)
        .filter(
            User.username == username,
            User.is_active.is_(True)
        )
        .first()
    )

    if user is None:
        return None

    if not verify_password(password, user.password_hash):
        return None

    return user