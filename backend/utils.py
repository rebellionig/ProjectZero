# utils.py
import bcrypt
import jwt
import os
import datetime
from dotenv import load_dotenv

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET", "supersecretchangeit")
JWT_ALGORITHM = "HS256"
JWT_EXP_DELTA_SECONDS = 3600  # токен живёт 1 час


# ------------------------
# Password hashing
# ------------------------
def hash_password(password: str) -> str:
    """Возвращает хэш пароля"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """Проверяет пароль с хэшем"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


# ------------------------
# JWT токены
# ------------------------
def create_access_token(user_id: str) -> str:
    """Создаёт JWT токен с user_id"""
    payload = {
        "user_id": user_id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(seconds=JWT_EXP_DELTA_SECONDS)
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


def decode_token(token: str) -> dict:
    """Декодирует JWT токен"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return {"error": "Token expired"}
    except jwt.InvalidTokenError:
        return {"error": "Invalid token"}


# ------------------------
# OTP / 2FA (опционально)
# ------------------------
try:
    import pyotp
except ImportError:
    pyotp = None
    print("pyotp не установлен, 2FA будет недоступен")


def generate_otp(secret: str) -> str:
    """Генерирует одноразовый пароль (TOTP)"""
    if pyotp is None:
        raise RuntimeError("pyotp не установлен")
    totp = pyotp.TOTP(secret)
    return totp.now()


def verify_otp(secret: str, token: str) -> bool:
    """Проверяет одноразовый пароль"""
    if pyotp is None:
        raise RuntimeError("pyotp не установлен")
    totp = pyotp.TOTP(secret)
    return totp.verify(token)
