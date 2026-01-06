from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import os
import secrets
import hashlib
import base64
import requests
import time

from pymongo import MongoClient
from bson import ObjectId


# -----------------------------
# Config
# -----------------------------
MONGO_URL = os.getenv("MONGO_URL", "").strip()
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "lucidly").strip()
TOKEN_TTL_DAYS = int(os.getenv("TOKEN_TTL_DAYS", "30"))

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com").strip().rstrip("/")

LUMA_API_KEY = os.getenv("LUMA_API_KEY", "").strip()
LUMA_BASE_URL = os.getenv("LUMA_BASE_URL", "https://api.lumalabs.ai").strip().rstrip("/")

if not MONGO_URL:
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

users_col = db["users"] if db is not None else None
dreams_col = db["dreams"] if db is not None else None
sessions_col = db["sessions"] if db is not None else None


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
    return {
        "id": str(d["_id"]),
        "user_id": str(d.get("user_id")),
        "title": d.get("title", "") or "",
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


def hash_password(password: str) -> Dict[str, str]:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 150_000)
    return {
        "salt": base64.b64encode(salt).decode("utf-8"),
        "hash": base64.b64encode(dk).decode("utf-8"),
    }


def verify_password(password: str, salt_b64: str, hash_b64: str) -> bool:
    if not salt_b64 or not hash_b64:
        return False
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


def get_current_user(creds: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    require_db()
    if not creds:
        raise HTTPException(status_code=401, detail="Authentication required")

    token = creds.credentials
    sess = sessions_col.find_one({"token": token})
    if not sess:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = users_col.find_one({"_id": sess["user_id"]})
    if not user:
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
    ok = db is not None
    details = {"db_connected": ok, "db_name": (db.name if db is not None else None), "ts": now_iso()}
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


class ImageGenPayload(BaseModel):
    style: str = "Artistic"


class VideoGenPayload(BaseModel):
    style: str = "cinematic"
    duration_seconds: int = 5


class LucyPayload(BaseModel):
    question: Optional[str] = None


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
    sessions_col.insert_one({"token": token, "user_id": user["_id"], "created_at": now_iso()})

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
    sessions_col.insert_one({"token": token, "user_id": user["_id"], "created_at": now_iso()})

    return {"token": token, "token_type": "bearer", "user": public_user(user)}


@app.get("/api/auth/me")
def me(ctx=Depends(get_current_user)):
    return public_user(ctx["user"])


@app.post("/api/auth/logout")
def logout(ctx=Depends(get_current_user)):
    sessions_col.delete_one({"token": ctx["token"]})
    return {"ok": True}


@app.delete("/api/auth/account")
def delete_account(ctx=Depends(get_current_user)):
    user = ctx["user"]
    # delete sessions
    sessions_col.delete_many({"user_id": user["_id"]})
    # delete dreams
    dreams_col.delete_many({"user_id": user["_id"]})
    # delete user
    users_col.delete_one({"_id": user["_id"]})
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
# AI: Image Generation (OpenAI)
# -----------------------------
@app.post("/api/dreams/{dream_id}/generate-image")
def generate_image(dream_id: str, payload: ImageGenPayload, ctx=Depends(get_current_user)):
    require_db()
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not configured on the backend")

    user = ctx["user"]
    d = dreams_col.find_one({"_id": oid(dream_id), "user_id": user["_id"]})
    if not d:
        raise HTTPException(status_code=404, detail="Dream not found")

    style = (payload.style or "Artistic").strip()
    prompt = (
        f"Create a high-quality dreamlike image in {style} style.\n\n"
        f"Dream title: {d.get('title','')}\n"
        f"Dream content: {d.get('content','')}\n"
        f"Mood: {d.get('mood','peaceful')}\n"
        f"Tags: {', '.join(d.get('tags', []) or [])}\n"
    )

    # NOTE: OpenAI image endpoints can vary by account/model.
    # This implementation uses a generic HTTP call and expects either a URL or base64.
    try:
        r = requests.post(
            f"{OPENAI_BASE_URL}/v1/images/generations",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
            json={
                "prompt": prompt,
                "size": "1024x1024",
                # "model": "gpt-image-1",  # uncomment if your account supports it
            },
            timeout=60,
        )
        if r.status_code >= 400:
            raise HTTPException(status_code=502, detail=f"OpenAI image error: {r.status_code} {r.text[:300]}")

        data = r.json()
        image_url = None
        image_b64 = None

        # Common shapes:
        # { data: [ { url: "..." } ] }
        # { data: [ { b64_json: "..." } ] }
        if isinstance(data, dict) and "data" in data and data["data"]:
            first = data["data"][0]
            image_url = first.get("url")
            image_b64 = first.get("b64_json")

        update = {"updated_at": now_iso()}
        if image_url:
            update["ai_image"] = image_url
        elif image_b64:
            update["ai_image"] = f"data:image/png;base64,{image_b64}"
        else:
            raise HTTPException(status_code=502, detail="OpenAI image response missing url/base64")

        dreams_col.update_one({"_id": oid(dream_id), "user_id": user["_id"]}, {"$set": update})
        fresh = dreams_col.find_one({"_id": oid(dream_id), "user_id": user["_id"]})
        return {"ok": True, "dream": dream_to_api(fresh)}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image generation failed: {type(e).__name__}")


# -----------------------------
# AI: Lucy Interpretation (OpenAI text)
# -----------------------------
@app.post("/api/dreams/{dream_id}/lucy-interpretation")
def lucy_interpretation(dream_id: str, payload: LucyPayload, ctx=Depends(get_current_user)):
    require_db()
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not configured on the backend")

    user = ctx["user"]
    d = dreams_col.find_one({"_id": oid(dream_id), "user_id": user["_id"]})
    if not d:
        raise HTTPException(status_code=404, detail="Dream not found")

    question = (payload.question or "Interpret this dream and provide gentle, practical insights.").strip()

    try:
        r = requests.post(
            f"{OPENAI_BASE_URL}/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "You are Lucy, a warm dream interpretation guide. Be supportive and concise."},
                    {"role": "user", "content": f"{question}\n\nTITLE: {d.get('title','')}\nCONTENT: {d.get('content','')}\nMOOD: {d.get('mood','')}\nTAGS: {d.get('tags',[])}"}
                ],
                "temperature": 0.7,
            },
            timeout=60,
        )
        if r.status_code >= 400:
            raise HTTPException(status_code=502, detail=f"OpenAI chat error: {r.status_code} {r.text[:300]}")

        data = r.json()
        text = None
        if data.get("choices"):
            text = data["choices"][0]["message"]["content"]

        if not text:
            raise HTTPException(status_code=502, detail="OpenAI response missing content")

        dreams_col.update_one(
            {"_id": oid(dream_id), "user_id": user["_id"]},
            {"$set": {"ai_interpretation": text, "updated_at": now_iso()}}
        )
        fresh = dreams_col.find_one({"_id": oid(dream_id), "user_id": user["_id"]})
        return {"ok": True, "dream": dream_to_api(fresh)}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lucy interpretation failed: {type(e).__name__}")


# -----------------------------
# AI: Video Generation (Luma)
# -----------------------------
@app.post("/api/dreams/{dream_id}/generate-video")
def generate_video(dream_id: str, payload: VideoGenPayload, ctx=Depends(get_current_user)):
    require_db()
    if not LUMA_API_KEY:
        raise HTTPException(status_code=500, detail="LUMA_API_KEY is not configured on the backend")

    user = ctx["user"]
    d = dreams_col.find_one({"_id": oid(dream_id), "user_id": user["_id"]})
    if not d:
        raise HTTPException(status_code=404, detail="Dream not found")

    prompt = (
        f"{d.get('title','')}\n"
        f"{d.get('content','')}\n"
        f"Mood: {d.get('mood','peaceful')}. Style: {payload.style}."
    )

    # Luma API shapes can vary by account. This uses a common “create generation then poll” pattern.
    try:
        create = requests.post(
            f"{LUMA_BASE_URL}/v1/generations",
            headers={"Authorization": f"Bearer {LUMA_API_KEY}", "Content-Type": "application/json"},
            json={
                "prompt": prompt,
                "duration_seconds": max(2, min(int(payload.duration_seconds), 12)),
                "aspect_ratio": "16:9",
            },
            timeout=60,
        )
        if create.status_code >= 400:
            raise HTTPException(status_code=502, detail=f"Luma create error: {create.status_code} {create.text[:300]}")

        job = create.json()
        gen_id = job.get("id") or job.get("generation_id")
        if not gen_id:
            raise HTTPException(status_code=502, detail="Luma response missing generation id")

        # Poll briefly (keep it short for Railway request limits)
        video_url = None
        for _ in range(10):  # ~10-20s max
            time.sleep(2)
            status = requests.get(
                f"{LUMA_BASE_URL}/v1/generations/{gen_id}",
                headers={"Authorization": f"Bearer {LUMA_API_KEY}"},
                timeout=30,
            )
            if status.status_code >= 400:
                continue
            sdata = status.json()
            state = (sdata.get("state") or sdata.get("status") or "").lower()
            if state in {"completed", "succeeded", "success"}:
                # Try common locations for URL
                video_url = (
                    sdata.get("video_url")
                    or (sdata.get("assets") or {}).get("video")
                    or (sdata.get("output") or {}).get("video")
                )
                break
            if state in {"failed", "error"}:
                raise HTTPException(status_code=502, detail="Luma generation failed")

        if not video_url:
            # Return job id so frontend can poll if desired
            dreams_col.update_one(
                {"_id": oid(dream_id), "user_id": user["_id"]},
                {"$set": {"updated_at": now_iso()}}
            )
            return {"ok": True, "status": "processing", "generation_id": gen_id}

        dreams_col.update_one(
            {"_id": oid(dream_id), "user_id": user["_id"]},
            {"$set": {"ai_video": video_url, "updated_at": now_iso()}}
        )
        fresh = dreams_col.find_one({"_id": oid(dream_id), "user_id": user["_id"]})
        return {"ok": True, "dream": dream_to_api(fresh)}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Video generation failed: {type(e).__name__}")


# -----------------------------
# Gallery (public only)
# -----------------------------
@app.get("/api/gallery/dreams")
def gallery(limit: int = 50):
    require_db()
    limit = max(1, min(limit, 200))
    cur = dreams_col.find({"is_public": True}).sort("created_at", -1).limit(limit)
    return [dream_to_api(d) for d in cur]
