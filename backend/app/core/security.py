from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

# Cost factor 12 explícito (NFR-01: bcrypt >= 12).
_pwd_context = CryptContext(
    schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12
)

_ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)


def create_access_token(subject: int) -> str:
    # Claims mínimos (mitigación #3 del threat model): solo sub y exp.
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.JWT_EXPIRE_MINUTES
    )
    claims = {"sub": str(subject), "exp": expire}
    return jwt.encode(claims, settings.JWT_SECRET, algorithm=_ALGORITHM)


def decode_access_token(token: str) -> dict:
    # algorithms fijado explícitamente (mitigación #1 del threat model): nunca
    # confiar en el "alg" que declara el propio token.
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[_ALGORITHM])
