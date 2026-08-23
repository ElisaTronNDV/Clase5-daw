from sqlalchemy.orm import Session

from app.core import security
from app.core.exceptions import EmailAlreadyRegisteredError
from app.models.user import User
from app.schemas.user import UserCreate


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def register_user(db: Session, data: UserCreate) -> User:
    if get_user_by_email(db, data.email) is not None:
        raise EmailAlreadyRegisteredError(data.email)

    user = User(
        email=data.email,
        hashed_password=security.hash_password(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = get_user_by_email(db, email)
    if user is None:
        return None
    # Mismo camino de retorno para "no existe" y "password incorrecta": el
    # caller no puede distinguir los dos casos (AC-03 / mitigación de
    # enumeración de usuarios en login).
    if not security.verify_password(password, user.hashed_password):
        return None
    return user
