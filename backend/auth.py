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
        httponly=True
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
    if db.query(User).filter(User.username == username).first():
        return {"error": "Username already exists"}

    MAX_BCRYPT_BYTES = 72

    # truncate to fit bcrypt limit (in bytes)
    def truncate_password(password: str, max_bytes=MAX_BCRYPT_BYTES) -> str:
        encoded = password.encode("utf-8")
        if len(encoded) <= max_bytes:
            return password
        # truncate and decode safely
        truncated = encoded[:max_bytes]
        # decode ignoring incomplete multibyte at the end
        return truncated.decode("utf-8", errors="ignore")

    safe_password = truncate_password(password)

    user = User(
        username=username,
        password_hash=pwd_context.hash(safe_password)
    )

    db.add(user)
    db.commit()
    return {"message": "User created, you can now log in"}
