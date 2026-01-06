from fastapi import FastAPI, Depends, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import os
import secrets
import hashlib
import base64

from pymongo import MongoClient
from bson import ObjectId


# -----------------------------
# Config
# -----------------------------
MONGO_URL = os.getenv("MONGO_URL", "").strip()
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "lucidly").strip()
TOKEN_TTL_DAYS = int(os.getenv("TOKEN_TTL_DAYS", "30"))

if not MONGO_URL:
    # We allow app to start so Railway healthcheck can show the error clearly
    # but protected endpoints will fail if DB isn't connected.
    mongo_client = None
    db = None
else:
    mongo_client = MongoClient(
        MONGO_URL,
        serverSelectionTimeoutMS=10000,
        connectTimeoutMS=10000,
        socketTimeoutMS=45000,
        retryWrites=True,
    )
    db = mongo_client[MONGO_DB_NAME]

users_col = db["users"] if db else None
dreams_col = db["dreams"] if db else None
sessions_col = db["sessions"] if db else None


# -----------------------------
# Helpers
# -----------------------------
def now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def oid(s: str) -> ObjectId:
    try:
        return ObjectId(s)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid id format")


def public_user(u: Dict[str, Any]) -> Dict[str, Any]:
    # Never return password hash/salt
    return {
        "id": str(u["_id"]),
        "email": u.get("email"),
        "name": u.get("name", ""),
        "bio": u.get("bio", ""),
        "avatar_url": u.get("avatar_url", ""),
        "is_premium": bool(u.get("is_premium", False)),
        "role": u.get("role", "dreamer"),
        "privacy_public_profile": bool(u.get("privacy_public_profile", False)),
        "notifications_enabled": bool(u.get("notifications_enabled", True)),
        "created_at": u.get("created_at"),
        "updated_at": u.get("updated_at"),
    }


def dream_to_api(d: Dict[str, Any]) -> Dict[str, Any]:
    # Ensure these fields always exist (prevents UI regressions)
    return {
        "id": str(d["_id"]),
        "user_id": str(d.get("user_id")),
        "title": d.get("title", "") or "",  # ✅ always present
        "content": d.get("content", "") or "",
        "mood": d.get("mood", "peaceful") or "peaceful",
        "tags": d.get("tags", []) or [],
        "created_at": d.get("created_at", now_iso()),
        "updated_at": d.get("updated_at"),
        "ai_interpretation": d.get("ai_interpretation"),
        "ai_image": d.get("ai_image"),
        "ai_video": d.get("ai_video"),
        "is_public": bool(d.get("is_public", False)),
    }


def require_db():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not connected")
    return True


# Password hashing (no extra libs required)
def hash_password(password: str) -> Dict[str, str]:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 150_000)
    return {
        "salt": base64.b64encode(salt).decode("utf-8"),
        "hash": base64.b64encode(dk).decode("utf-8"),
    }


def verify_password(password: str, salt_b64: str, hash_b64: str) -> bool:
    salt = base64.b64decode(salt_b64.encode("utf-8"))
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 150_000)
    return base64.b64encode(dk).decode("utf-8") == hash_b64


def new_token() -> str:
    return "tok_" + secrets.token_urlsafe(32)


# -----------------------------
# App
# -----------------------------
app = FastAPI(title="Lucidly API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer(auto_error=False)


def get_current_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(security),
):
    require_db()
    if not creds:
        raise HTTPException(status_code=401, detail="Authentication required")

    token = creds.credentials
    sess = sessions_col.find_one({"token": token})
    if not sess:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = users_col.find_one({"_id": sess["user_id"]})
    if not user:
        # stale session
        sessions_col.delete_one({"token": token})
        raise HTTPException(status_code=401, detail="Invalid token")

    return {"user": user, "token": token}


# -----------------------------
# Health / Root
# -----------------------------
@app.get("/")
def root():
    return {"message": "Lucidly API is running!", "status": "ok"}


@app.get("/api/health")
def health_check():
    # Health should not 500 due to bool(db) checks etc.
    ok = db is not None
    details = {"db_connected": ok, "db_name": (db.name if db is not None else None), "ts": now_iso()}
    # If DB exists, attempt ping for real connectivity
    if db is not None:
        try:
            mongo_client.admin.command("ping")
            details["db_ping"] = "ok"
        except Exception as e:
            details["db_ping"] = f"error: {type(e).__name__}"
    return details


# -----------------------------
# Models
# -----------------------------
class RegisterPayload(BaseModel):
    email: str
    password: str
    name: str = ""


class LoginPayload(BaseModel):
    email: str
    password: str


class ProfilePatch(BaseModel):
    name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    privacy_public_profile: Optional[bool] = None
    notifications_enabled: Optional[bool] = None


class DreamCreate(BaseModel):
    title: str = ""
    content: str = ""
    mood: str = "peaceful"
    tags: List[str] = Field(default_factory=list)
    is_public: bool = False


class DreamPatch(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    mood: Optional[str] = None
    tags: Optional[List[str]] = None
    is_public: Optional[bool] = None


# -----------------------------
# Auth
# -----------------------------
@app.post("/api/auth/register")
def register(payload: RegisterPayload):
    require_db()
    email = payload.email.strip().lower()
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Valid email is required")
    if not payload.password or len(payload.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    existing = users_col.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    pw = hash_password(payload.password)

    user_doc = {
        "email": email,
        "name": payload.name.strip(),
        "bio": "",
        "avatar_url": "",
        "privacy_public_profile": False,
        "notifications_enabled": True,
        "is_premium": False,
        "role": "dreamer",
        "pw_salt": pw["salt"],
        "pw_hash": pw["hash"],
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    ins = users_col.insert_one(user_doc)
    user = users_col.find_one({"_id": ins.inserted_id})

    token = new_token()
    sessions_col.insert_one({
        "token": token,
        "user_id": user["_id"],
        "created_at": now_iso(),
    })

    return {"token": token, "token_type": "bearer", "user": public_user(user)}


@app.post("/api/auth/login")
def login(payload: LoginPayload):
    require_db()
    email = payload.email.strip().lower()
    user = users_col.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not verify_password(payload.password, user.get("pw_salt", ""), user.get("pw_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = new_token()
    sessions_col.insert_one({
        "token": token,
        "user_id": user["_id"],
        "created_at": now_iso(),
    })

    return {"token": token, "token_type": "bearer", "user": public_user(user)}


@app.get("/api/auth/me")
def me(ctx=Depends(get_current_user)):
    return public_user(ctx["user"])


@app.post("/api/auth/logout")
def logout(ctx=Depends(get_current_user)):
    # ✅ server-side token invalidation
    sessions_col.delete_one({"token": ctx["token"]})
    return {"ok": True}


@app.delete("/api/auth/account")
def delete_account(ctx=Depends(get_current_user)):
    user = ctx["user"]
    token = ctx["token"]

    # delete sessions
    sessions_col.delete_many({"user_id": user["_id"]})
    # delete dreams
    dreams_col.delete_many({"user_id": user["_id"]})
    # delete user
    users_col.delete_one({"_id": user["_id"]})

    # also ensure current token is invalidated
    sessions_col.delete_one({"token": token})
    return {"ok": True}


# -----------------------------
# Profile
# -----------------------------
@app.patch("/api/profile")
def patch_profile(payload: ProfilePatch, ctx=Depends(get_current_user)):
    user = ctx["user"]
    update: Dict[str, Any] = {"updated_at": now_iso()}

    if payload.name is not None:
        update["name"] = payload.name.strip()
    if payload.bio is not None:
        update["bio"] = payload.bio
    if payload.avatar_url is not None:
        update["avatar_url"] = payload.avatar_url
    if payload.privacy_public_profile is not None:
        update["privacy_public_profile"] = bool(payload.privacy_public_profile)
    if payload.notifications_enabled is not None:
        update["notifications_enabled"] = bool(payload.notifications_enabled)

    users_col.update_one({"_id": user["_id"]}, {"$set": update})
    fresh = users_col.find_one({"_id": user["_id"]})
    return public_user(fresh)


# -----------------------------
# Dreams CRUD
# -----------------------------
@app.get("/api/dreams")
def list_dreams(ctx=Depends(get_current_user)):
    user = ctx["user"]
    cur = dreams_col.find({"user_id": user["_id"]}).sort("created_at", -1)
    return [dream_to_api(d) for d in cur]


@app.post("/api/dreams")
def create_dream(payload: DreamCreate, ctx=Depends(get_current_user)):
    user = ctx["user"]
    doc = {
        "user_id": user["_id"],
        "title": payload.title.strip(),
        "content": payload.content,
        "mood": payload.mood,
        "tags": payload.tags or [],
        "is_public": bool(payload.is_public),
        "ai_interpretation": None,
        "ai_image": None,
        "ai_video": None,
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    ins = dreams_col.insert_one(doc)
    d = dreams_col.find_one({"_id": ins.inserted_id})
    return dream_to_api(d)


@app.get("/api/dreams/{dream_id}")
def get_dream(dream_id: str, ctx=Depends(get_current_user)):
    user = ctx["user"]
    d = dreams_col.find_one({"_id": oid(dream_id), "user_id": user["_id"]})
    if not d:
        raise HTTPException(status_code=404, detail="Dream not found")
    return dream_to_api(d)


@app.patch("/api/dreams/{dream_id}")
def patch_dream(dream_id: str, payload: DreamPatch, ctx=Depends(get_current_user)):
    user = ctx["user"]
    update: Dict[str, Any] = {"updated_at": now_iso()}
    if payload.title is not None:
        update["title"] = payload.title.strip()
    if payload.content is not None:
        update["content"] = payload.content
    if payload.mood is not None:
        update["mood"] = payload.mood
    if payload.tags is not None:
        update["tags"] = payload.tags
    if payload.is_public is not None:
        update["is_public"] = bool(payload.is_public)

    res = dreams_col.update_one({"_id": oid(dream_id), "user_id": user["_id"]}, {"$set": update})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Dream not found")

    d = dreams_col.find_one({"_id": oid(dream_id), "user_id": user["_id"]})
    return dream_to_api(d)


@app.delete("/api/dreams/{dream_id}")
def delete_dream(dream_id: str, ctx=Depends(get_current_user)):
    user = ctx["user"]
    res = dreams_col.delete_one({"_id": oid(dream_id), "user_id": user["_id"]})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Dream not found")
    return {"ok": True}


# -----------------------------
# Gallery (public only)
# -----------------------------
@app.get("/api/gallery/dreams")
def gallery(limit: int = 50):
    require_db()
    limit = max(1, min(limit, 200))
    cur = dreams_col.find({"is_public": True}).sort("created_at", -1).limit(limit)
    return [dream_to_api(d) for d in cur]
