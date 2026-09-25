from sqlalchemy.orm import Session

from models.models import User
from services.auth_service import hash_password


def create_initial_admin(
    db: Session,
    username: str,
    password: str
):
    """Create the first administrator account if one does not exist."""

    existing_admin = (
        db.query(User)
        .filter(User.role == "ADMIN")
        .first()
    )

    if existing_admin:
        return False, "An administrator account already exists."

    existing_username = (
        db.query(User)
        .filter(User.username == username)
        .first()
    )

    if existing_username:
        return False, "Username already exists."

    admin = User(
        username=username,
        password_hash=hash_password(password),
        role="ADMIN",
        is_active=True
    )

    db.add(admin)
    db.commit()
    db.refresh(admin)

    return True, "Initial administrator account created successfully."