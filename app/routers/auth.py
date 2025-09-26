# app/routers/auth.py
import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from twilio.rest import Client
import jwt as pyjwt
from jwt import PyJWTError

from app import models, schemas
from app.database import get_db

# -------------------------
# Configuration (env vars)
# -------------------------
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_VERIFY_SERVICE_SID = os.getenv("TWILIO_VERIFY_SERVICE_SID")

# JWT config
SECRET_KEY = os.getenv("JWT_SECRET", "change_this_to_a_long_random_secret_in_prod")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))

# OTP / behaviour flags
ALLOW_AUTO_CREATE_USER = os.getenv("ALLOW_AUTO_CREATE_USER", "true").lower() in ("1", "true", "yes")
OTP_COOLDOWN_SECONDS = int(os.getenv("OTP_COOLDOWN_SECONDS", "30"))

# in-memory last OTP request tracker (keyed by username). Replace with Redis for production.
_otp_last_request: dict[str, datetime] = {}

# Twilio client (if configured)
twilio_client: Optional[Client] = None
if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    try:
        twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    except Exception:
        twilio_client = None

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Router + oauth helper
router = APIRouter(prefix="/auth", tags=["Auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")  # kept for dependencies

# -------------------------
# Local Pydantic models
# -------------------------
class LoginWithPhone(BaseModel):
    username: str
    password: str
    phone: str   # E.164 format expected (e.g. "+9198XXXXXXXX")

class VerifyOTPBody(BaseModel):
    username: str
    code: str

# -------------------------
# Helpers
# -------------------------
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    if not hashed:
        return False
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    token = pyjwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return token

# -------------------------
# Endpoints
# -------------------------
@router.post("/register", response_model=schemas.User)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.username == user.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    hashed = get_password_hash(user.password)
    new_user = models.User(username=user.username, hashed_password=hashed, phone_number=user.phone_number)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login")
def login(req: LoginWithPhone, db: Session = Depends(get_db)):
    """
    Single-step login that:
      1. verifies username+password
      2. sets/updates the user's phone_number in DB to the provided phone (if different)
      3. sends OTP to that phone via Twilio Verify
    After scanning/receiving OTP the client should call /auth/verify-otp with username+code to get the JWT.
    """
    username = req.username
    password = req.password
    phone = req.phone.strip()

    # basic phone format check (E.164-ish)
    if not phone.startswith("+") or len(phone) < 7:
        raise HTTPException(status_code=400, detail="Phone must be in E.164 format (e.g. +9198XXXXXXXX)")

    # find user
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

    # verify password
    if not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

    # update user's phone if it's missing or different
    if user.phone_number != phone:
        user.phone_number = phone
        db.add(user)
        db.commit()
        db.refresh(user)

    # OTP cooldown keyed by username
    last = _otp_last_request.get(username)
    now = datetime.utcnow()
    if last and (now - last).total_seconds() < OTP_COOLDOWN_SECONDS:
        raise HTTPException(status_code=429, detail=f"Please wait {OTP_COOLDOWN_SECONDS} seconds between OTP requests")

    if twilio_client is None or not TWILIO_VERIFY_SERVICE_SID:
        raise HTTPException(status_code=500, detail="Twilio not configured. Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN and TWILIO_VERIFY_SERVICE_SID in .env")

    try:
        verification = twilio_client.verify.services(TWILIO_VERIFY_SERVICE_SID).verifications.create(
            to=phone,
            channel="sms"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Twilio error while requesting OTP: {e}")

    _otp_last_request[username] = now
    return {"detail": "OTP sent to provided phone"}

@router.post("/verify-otp")
def verify_otp(body: VerifyOTPBody, db: Session = Depends(get_db)):
    """
    Verify OTP for username. Request body: {"username":"...","code":"123456"}
    On success returns JWT token and basic user info.
    """
    username = body.username.strip()
    code = body.code.strip()

    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if twilio_client is None or not TWILIO_VERIFY_SERVICE_SID:
        raise HTTPException(status_code=500, detail="Twilio not configured on server")

    try:
        check = twilio_client.verify.services(TWILIO_VERIFY_SERVICE_SID).verification_checks.create(
            to=user.phone_number, code=code
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Twilio verification error: {e}")

    if getattr(check, "status", None) != "approved":
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    # OTP approved -> create token
    token = create_access_token({"sub": user.username, "uid": user.id})
    return {"access_token": token, "token_type": "bearer", "user": {"id": user.id, "username": user.username, "phone": user.phone_number}}

# -------------------------
# Current user helper (dependency)
# -------------------------
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    credentials_exception = HTTPException(status_code=401, detail="Invalid or expired token", headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = pyjwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: Optional[str] = payload.get("sub")
        if username is None:
            raise credentials_exception
    except PyJWTError:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise credentials_exception
    return user
