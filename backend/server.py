from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
import os
import uuid
import hashlib
import secrets
import uvicorn

from pymongo import MongoClient
from pymongo.errors import PyMongoError
from bson import ObjectId
from bson.errors import InvalidId

# -----------------------------
# App + Middleware
# -----------------------------
app = FastAPI(title="Lucidly API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Auth / Security
# -----------------------------
security = HTTPBearer(auto_error=False)

# -----------------------------
# Helpers
# -----------------------------
def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def safe_str(x: Any) -> str:
    return "" if x is None else str(x)

def new_token() -> str:
    return "token_" + uuid.uuid4().hex

def hash_password(password: str) -> str:
    """
    PBKDF2 hash using stdlib only (no external deps).
    Stored format: pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>
    """
    password = password or ""
    iterations = 200_000
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"pbkdf2_sha256${iterations}${salt.hex()}${dk.hex()}"

def verify_password(password: str, stored: str) -> bool:
    try:
        algo, iters, salt_hex, hash_hex = stored.split("$", 3)
        if algo != "pbkdf2_sha256":
            return False
        iterations = int(iters)
        salt = bytes.fromhex(salt_hex)
        dk = hashlib.pbkdf2_hmac("sha256", (password or "").encode("utf-8"), salt, iterations)
        return secrets.compare_digest(dk.hex(), hash_hex)
    except Exception:
        return False

def user_public(u: Dict[str, Any]) -> Dict[str, Any]:
    """Never return password hash."""
    return {
        "id": safe_str(u.get("id") or u.get("_id")),
        "email": u.get("email", ""),
        "name": u.get("name", ""),
        "is_premium": bool(u.get("is_premium", False)),
        "role": u.get("role", "dreamer"),
        "lucy_tokens_used": int(u.get("lucy_tokens_used", 0)),
        "lucy_tokens_limit": int(u.get("lucy_tokens_limit", 3)),
        "image_tokens_used": int(u.get("image_tokens_used", 0)),
        "image_tokens_limit": int(u.get("image_tokens_limit", 3)),
        "video_tokens_used": int(u.get("video_tokens_used", 0)),
        "video_tokens_limit": int(u.get("video_tokens_limit", 3)),
        "generation_count": int(u.get("generation_count", 0)),
        "created_at": u.get("created_at"),
    }

def dream_to_response(d: Dict[str, Any]) -> Dict[str, Any]:
    """Map Mongo _id to id and ensure title exists."""
    out = dict(d)
    if "_id" in out:
        out["id"] = str(out.pop("_id"))
    out.setdefault("title", (out.get("content", "")[:40] + ("..." if len(out.get("content", "")) > 40 else "")) or "Untitled Dream")
    out.setdefault("tags", [])
    out.setdefault("ai_interpretation", None)
    out.setdefault("ai_image", None)
    out.setdefault("ai_video", None)
    out.setdefault("video_base64", None)
    out.setdefault("is_public", False)
    out.setdefault("created_at", now_iso())
    return out

# -----------------------------
# MongoDB (preferred) + fallback
# -----------------------------
MONGO_URL = os.getenv("MONGO_URL") or os.getenv("MONGO_URI") or os.getenv("MONGODB_URL")
DB_NAME = os.getenv("MONGO_DB_NAME", "lucidly")

mongo_client: Optional[MongoClient] = None
db = None
users_col = None
dreams_col = None
sessions_col = None

# In-memory fallback (only used if MONGO_URL not set)
users_mem: Dict[str, Dict[str, Any]] = {}       # email -> user doc
dreams_mem: Dict[str, Dict[str, Any]] = {}      # id -> dream doc
sessions_mem: Dict[str, Dict[str, Any]] = {}    # token -> user doc

def init_mongo():
    global mongo_client, db, users_col, dreams_col, sessions_col
    if not MONGO_URL:
        return
    # Sane timeouts for hosted environments
    mongo_client = MongoClient(
        MONGO_URL,
        serverSelectionTimeoutMS=10_000,
        connectTimeoutMS=10_000,
        socketTimeoutMS=45_000,
        maxPoolSize=10,
        minPoolSize=1,
        retryWrites=True,
    )
    db = mongo_client[DB_NAME]
    users_col = db["users"]
    dreams_col = db["dreams"]
    sessions_col = db["sessions"]

    # Indexes (safe to call repeatedly)
    try:
        users_col.create_index("email", unique=True)
        dreams_col.create_index([("user_id", 1), ("created_at", -1)])
        sessions_col.create_index("token", unique=True)
        sessions_col.create_index("user_id")
    except Exception:
        pass

@app.on_event("startup")
def on_startup():
    init_mongo()

def using_mongo() -> bool:
    return db is not None and users_col is not None and dreams_col is not None and sessions_col is not None

# -----------------------------
# Auth dependency
# -----------------------------
def get_current_user(token_data=Depends(security)) -> Dict[str, Any]:
    if not token_data:
        raise HTTPException(status_code=401, detail="Authentication required")

    token = token_data.credentials

    # Mongo sessions
    if using_mongo():
        sess = sessions_col.find_one({"token": token})
        if not sess:
            raise HTTPException(status_code=401, detail="Invalid session")
        user = users_col.find_one({"_id": sess["user_id"]})
        if not user:
            raise HTTPException(status_code=401, detail="Invalid session")
        user["id"] = str(user["_id"])
        return user

    # In-memory fallback
    user = sessions_mem.get(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid session")
    return user

# -----------------------------
# Health / Root
# -----------------------------
@app.get("/")
def root():
    return {"message": "Lucidly API is running!", "status": "ok"}

@app.get("/api/health")
def health_check():
    mongo_ok = False
    db_name = None
    error = None

    if using_mongo():
        try:
            mongo_client.admin.command("ping")
            mongo_ok = True
            db_name = DB_NAME
        except Exception as e:
            mongo_ok = False
            error = str(e)

    return {
        "status": "healthy",
        "timestamp": now_iso(),
        "mongo_enabled": bool(MONGO_URL),
        "mongo_connected": mongo_ok,
        "db_name": db_name,
        "error": error,
    }

# -----------------------------
# Auth Endpoints
# -----------------------------
@app.post("/api/auth/register")
def register(user_data: dict):
    email = (user_data.get("email") or "").strip().lower()
    password = user_data.get("password") or ""
    name = (user_data.get("name") or "").strip()

    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    if not password or len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    if using_mongo():
        try:
            existing = users_col.find_one({"email": email})
            if existing:
                raise HTTPException(status_code=400, detail="Email already registered")

            user_doc = {
                "email": email,
                "password_hash": hash_password(password),
                "name": name,
                "is_premium": False,
                "role": "dreamer",
                "lucy_tokens_used": 0, "lucy_tokens_limit": 3,
                "image_tokens_used": 0, "image_tokens_limit": 3,
                "video_tokens_used": 0, "video_tokens_limit": 3,
                "generation_count": 0,
                "created_at": now_iso(),
            }
            ins = users_col.insert_one(user_doc)
            user_id = ins.inserted_id

            token = new_token()
            sessions_col.insert_one({"token": token, "user_id": user_id, "created_at": now_iso()})

            user = users_col.find_one({"_id": user_id})
            user["id"] = str(user["_id"])

            return {"token": token, "token_type": "bearer", "user": user_public(user)}
        except HTTPException:
            raise
        except PyMongoError as e:
            raise HTTPException(status_code=500, detail=f"DB error: {str(e)}")

    # In-memory fallback
    if email in users_mem:
        raise HTTPException(status_code=400, detail="Email already registered")

    user_id = f"user_{len(users_mem) + 1}"
    user_doc = {
        "id": user_id,
        "email": email,
        "password_hash": hash_password(password),
        "name": name,
        "is_premium": False,
        "role": "dreamer",
        "lucy_tokens_used": 0, "lucy_tokens_limit": 3,
        "image_tokens_used": 0, "image_tokens_limit": 3,
        "video_tokens_used": 0, "video_tokens_limit": 3,
        "generation_count": 0,
        "created_at": now_iso(),
    }
    users_mem[email] = user_doc
    token = new_token()
    sessions_mem[token] = user_doc
    return {"token": token, "token_type": "bearer", "user": user_public(user_doc)}

@app.post("/api/auth/login")
def login(credentials: dict):
    email = (credentials.get("email") or "").strip().lower()
    password = credentials.get("password") or ""

    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    if not password:
        raise HTTPException(status_code=400, detail="Password is required")

    if using_mongo():
        user = users_col.find_one({"email": email})
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        if not verify_password(password, user.get("password_hash", "")):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        token = new_token()
        sessions_col.insert_one({"token": token, "user_id": user["_id"], "created_at": now_iso()})
        user["id"] = str(user["_id"])
        return {"token": token, "token_type": "bearer", "user": user_public(user)}

    user = users_mem.get(email)
    if not user or not verify_password(password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = new_token()
    sessions_mem[token] = user
    return {"token": token, "token_type": "bearer", "user": user_public(user)}

@app.get("/api/auth/me")
def me(current_user=Depends(get_current_user)):
    return user_public(current_user)

@app.post("/api/auth/logout")
def logout(token_data=Depends(security)):
    if not token_data:
        raise HTTPException(status_code=401, detail="Authentication required")
    token = token_data.credentials

    if using_mongo():
        sessions_col.delete_one({"token": token})
        return {"ok": True}

    sessions_mem.pop(token, None)
    return {"ok": True}

@app.post("/api/auth/reset-tokens")
def reset_user_tokens(current_user=Depends(get_current_user)):
    if using_mongo():
        users_col.update_one(
            {"_id": current_user["_id"]},
            {"$set": {"image_tokens_used": 0, "video_tokens_used": 0, "lucy_tokens_used": 0}}
        )
        user = users_col.find_one({"_id": current_user["_id"]})
        user["id"] = str(user["_id"])
        return {
            "message": "All tokens reset successfully!",
            "user": user_public(user)
        }

    email = current_user["email"]
    users_mem[email]["image_tokens_used"] = 0
    users_mem[email]["video_tokens_used"] = 0
    users_mem[email]["lucy_tokens_used"] = 0
    return {"message": "All tokens reset successfully!", "user": user_public(users_mem[email])}

# -----------------------------
# Dreams Endpoints
# -----------------------------
@app.get("/api/dreams")
def get_dreams(current_user=Depends(get_current_user)):
    user_id = str(current_user.get("_id") or current_user.get("id"))

    if using_mongo():
        docs = dreams_col.find({"user_id": user_id}).sort("created_at", -1)
        return [dream_to_response(d) for d in docs]

    return [dream_to_response(d) for d in dreams_mem.values() if d.get("user_id") == user_id]

@app.post("/api/dreams")
def create_dream(dream_data: dict, current_user=Depends(get_current_user)):
    user_id = str(current_user.get("_id") or current_user.get("id"))

    content = (dream_data.get("content") or "").strip()
    mood = (dream_data.get("mood") or "peaceful").strip()
    tags = dream_data.get("tags") or []
    title = (dream_data.get("title") or "").strip()
    if not title:
        title = content[:40] + ("..." if len(content) > 40 else "")
        if not title:
            title = "Untitled Dream"

    dream_doc = {
        "user_id": user_id,
        "title": title,
        "content": content,
        "mood": mood,
        "tags": tags if isinstance(tags, list) else [],
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "user_name": current_user.get("name", ""),
        "user_role": current_user.get("role", "dreamer"),
        "has_liked": False,
        "ai_interpretation": None,
        "ai_image": None,
        "ai_video": None,
        "video_base64": None,
        "is_public": False,
    }

    if using_mongo():
        ins = dreams_col.insert_one(dream_doc)
        saved = dreams_col.find_one({"_id": ins.inserted_id})
        return dream_to_response(saved)

    dream_id = f"dream_{len(dreams_mem) + 1}"
    dream_doc["id"] = dream_id
    dreams_mem[dream_id] = dream_doc
    return dream_to_response(dream_doc)

@app.get("/api/dreams/{dream_id}")
def get_dream(dream_id: str, current_user=Depends(get_current_user)):
    user_id = str(current_user.get("_id") or current_user.get("id"))

    if using_mongo():
        try:
            oid = ObjectId(dream_id)
        except InvalidId:
            raise HTTPException(status_code=400, detail="Invalid dream id")
        doc = dreams_col.find_one({"_id": oid, "user_id": user_id})
        if not doc:
            raise HTTPException(status_code=404, detail="Dream not found")
        return dream_to_response(doc)

    doc = dreams_mem.get(dream_id)
    if not doc or doc.get("user_id") != user_id:
        raise HTTPException(status_code=404, detail="Dream not found")
    return dream_to_response(doc)

@app.delete("/api/dreams/{dream_id}")
def delete_dream(dream_id: str, current_user=Depends(get_current_user)):
    user_id = str(current_user.get("_id") or current_user.get("id"))

    if using_mongo():
        try:
            oid = ObjectId(dream_id)
        except InvalidId:
            raise HTTPException(status_code=400, detail="Invalid dream id")

        res = dreams_col.delete_one({"_id": oid, "user_id": user_id})
        if res.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Dream not found")
        return {"ok": True, "deleted_id": dream_id}

    doc = dreams_mem.get(dream_id)
    if not doc or doc.get("user_id") != user_id:
        raise HTTPException(status_code=404, detail="Dream not found")
    del dreams_mem[dream_id]
    return {"ok": True, "deleted_id": dream_id}

@app.patch("/api/dreams/{dream_id}")
def update_dream(dream_id: str, payload: dict, current_user=Depends(get_current_user)):
    """Optional: supports editing title/content/tags/mood/public."""
    user_id = str(current_user.get("_id") or current_user.get("id"))

    allowed = {}
    for k in ["title", "content", "mood", "tags", "is_public"]:
        if k in payload:
            allowed[k] = payload[k]

    allowed["updated_at"] = now_iso()

    if using_mongo():
        try:
            oid = ObjectId(dream_id)
        except InvalidId:
            raise HTTPException(status_code=400, detail="Invalid dream id")

        res = dreams_col.update_one({"_id": oid, "user_id": user_id}, {"$set": allowed})
        if res.matched_count == 0:
            raise HTTPException(status_code=404, detail="Dream not found")
        doc = dreams_col.find_one({"_id": oid})
        return dream_to_response(doc)

    doc = dreams_mem.get(dream_id)
    if not doc or doc.get("user_id") != user_id:
        raise HTTPException(status_code=404, detail="Dream not found")
    doc.update(allowed)
    dreams_mem[dream_id] = doc
    return dream_to_response(doc)

@app.post("/api/dreams/{dream_id}/make-public")
def make_public(dream_id: str, payload: dict, current_user=Depends(get_current_user)):
    """Toggle public visibility."""
    is_public = bool(payload.get("is_public", True))
    return update_dream(dream_id, {"is_public": is_public}, current_user)

# -----------------------------
# AI Endpoints (mock/premium gate)
# -----------------------------
def require_available_token(current_user: Dict[str, Any], kind: str):
    """
    kind: image | video | lucy
    Returns updated user doc if Mongo is used, else in-memory user.
    """
    is_premium = bool(current_user.get("is_premium", False))
    if is_premium:
        return

    used_key = f"{kind}_tokens_used"
    limit_key = f"{kind}_tokens_limit"
    used = int(current_user.get(used_key, 0))
    limit = int(current_user.get(limit_key, 3))

    if used >= limit:
        raise HTTPException(status_code=402, detail=f"{kind.capitalize()} generation limit reached")

@app.post("/api/dreams/{dream_id}/generate-image")
def generate_image(dream_id: str, payload: dict, current_user=Depends(get_current_user)):
    require_available_token(current_user, "image")

    # Ensure dream exists
    dream = get_dream(dream_id, current_user)

    # Mock image
    mock_image = "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjN2MzYWVkIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZpbGw9IndoaXRlIiBmb250LXNpemU9IjIwIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIj5MdWNpZGx5IE1vY2sgSW1hZ2U8L3RleHQ+PC9zdmc+"

    # Update dream
    update_dream(dream_id, {"ai_image": mock_image, "is_public": True}, current_user)

    # Increment token usage
    if not bool(current_user.get("is_premium", False)):
        if using_mongo():
            users_col.update_one({"_id": current_user["_id"]}, {"$inc": {"image_tokens_used": 1}})
        else:
            current_user["image_tokens_used"] = int(current_user.get("image_tokens_used", 0)) + 1

    return {"ok": True, "image_url": mock_image}

@app.post("/api/dreams/{dream_id}/generate-video")
def generate_video(dream_id: str, payload: dict, current_user=Depends(get_current_user)):
    require_available_token(current_user, "video")
    _ = get_dream(dream_id, current_user)

    sample_url = "https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4"
    update_dream(dream_id, {"ai_video": sample_url, "is_public": True}, current_user)

    if not bool(current_user.get("is_premium", False)):
        if using_mongo():
            users_col.update_one({"_id": current_user["_id"]}, {"$inc": {"video_tokens_used": 1}})
        else:
            current_user["video_tokens_used"] = int(current_user.get("video_tokens_used", 0)) + 1

    return {"ok": True, "video_url": sample_url, "status": "completed"}

@app.post("/api/dreams/{dream_id}/lucy-interpretation")
def lucy(dream_id: str, payload: dict, current_user=Depends(get_current_user)):
    require_available_token(current_user, "lucy")
    d = get_dream(dream_id, current_user)

    interpretation = f"""Hello {current_user.get('name','dreamer')} ✨
I analyzed: "{(d.get('content') or '')[:80]}..."
Symbolic Meaning: Transformation and personal growth.
Lucy’s Wisdom: Trust your intuition.
"""

    update_dream(dream_id, {"ai_interpretation": interpretation}, current_user)

    if not bool(current_user.get("is_premium", False)):
        if using_mongo():
            users_col.update_one({"_id": current_user["_id"]}, {"$inc": {"lucy_tokens_used": 1}})
        else:
            current_user["lucy_tokens_used"] = int(current_user.get("lucy_tokens_used", 0)) + 1

    return {"ok": True, "interpretation": interpretation}

# -----------------------------
# Dashboard / Gallery
# -----------------------------
@app.get("/api/dashboard/stats")
def dashboard(current_user=Depends(get_current_user)):
    dreams = get_dreams(current_user)
    ai_count = sum(1 for d in dreams if d.get("ai_image") or d.get("ai_video"))
    return {
        "dream_count": len(dreams),
        "ai_creations_count": ai_count,
        "current_streak": 1 if dreams else 0,
        "longest_streak": 1 if dreams else 0,
        "mood_distribution": {"peaceful": 60, "excited": 30, "mysterious": 10},
        "recent_dreams": dreams[:3],
    }

@app.get("/api/gallery/dreams")
def gallery(limit: int = 10):
    limit = max(1, min(int(limit), 50))

    if using_mongo():
        docs = dreams_col.find(
            {"is_public": True, "$or": [{"ai_image": {"$ne": None}}, {"ai_video": {"$ne": None}}]}
        ).sort("created_at", -1).limit(limit)
        return [dream_to_response(d) for d in docs]

    docs = [
        d for d in dreams_mem.values()
        if d.get("is_public") and (d.get("ai_image") or d.get("ai_video"))
    ]
    docs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return [dream_to_response(d) for d in docs[:limit]]

# -----------------------------
# Local dev / Railway
# -----------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)

