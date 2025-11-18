# backend/auth.py

from fastapi import APIRouter, Form, Response, Depends, Request, HTTPException
from fastapi.responses import RedirectResponse
from passlib.context import CryptContext
import secrets

from .models import User
from .database import get_db

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# In-memory session store
sessions = {}


def get_current_user(
    request: Request,
    db=Depends(get_db)
):
    token = request.cookies.get("session_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not logged in")

    user_id = sessions.get(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not logged in")

    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


@router.post("/login")
def login(
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    db=Depends(get_db)
):
    user = db.query(User).filter(User.username == username).first()

    if not user or not pwd_context.verify(password, user.password_hash):
        return {"error": "Invalid credentials"}

    session_token = secrets.token_hex(16)
    sessions[session_token] = user.id

    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        samesite="lax",   # SAFE for HTTP
        secure=False,     # MUST BE OFF until HTTPS
    )

    return RedirectResponse(url="/frontend/index.html", status_code=302)


@router.post("/logout")
def logout(response: Response, request: Request):
    token = request.cookies.get("session_token")
    if token in sessions:
        del sessions[token]

    response.delete_cookie("session_token")
    return {"message": "Logged out"}

@router.get("/me")
def me(user=Depends(get_current_user)):
    return {"id": user.id, "username": user.username}


MAX_BCRYPT_LENGTH = 72  # bcrypt limitation

@router.post("/register")
def register(username: str = Form(...), password: str = Form(...), db=Depends(get_db)):
    # Check if username already exists
    if db.query(User).filter(User.username == username).first():
        return {"error": "Username already exists"}

    # --- Bcrypt safe password ---
    MAX_BCRYPT_BYTES = 72

    def truncate_password(password: str, max_bytes=MAX_BCRYPT_BYTES) -> str:
        """
        Truncate the password to fit bcrypt's 72-byte limit,
        safely handling multibyte UTF-8 characters.
        """
        encoded = password.encode("utf-8")
        if len(encoded) <= max_bytes:
            return password
        truncated = encoded[:max_bytes]
        return truncated.decode("utf-8", errors="ignore")

    safe_password = truncate_password(password)  # string, not bytes

    # Create user with hashed password
    user = User(
        username=username,
        password_hash=pwd_context.hash(safe_password)  # pass string here
    )

    # Save to DB
    db.add(user)
    db.commit()

    return {"message": "User created, you can now log in"}
