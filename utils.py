# utils.py
import jwt, os, datetime
from passlib.hash import bcrypt
from dotenv import load_dotenv

load_dotenv()
JWT_SECRET = os.getenv("JWT_SECRET", "supersecret")
JWT_ALG = "HS256"
ACCESS_EXPIRE_MIN = 60  # minutes

def hash_password(password: str) -> str:
    return bcrypt.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.verify(password, hashed)

def create_access_token(sub: str, extra: dict = None, minutes: int = ACCESS_EXPIRE_MIN):
    payload = {"sub": sub, "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=minutes)}
    if extra:
        payload.update(extra)
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)

def decode_token(token: str):
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except Exception as e:
        return None
