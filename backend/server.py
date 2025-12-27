from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from datetime import datetime
import os
import uvicorn
from typing import Dict, Any

from pymongo import MongoClient
from bson import ObjectId


# -----------------------------
# Helpers
# -----------------------------
def now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def make_token(user_id: str) -> str:
    # Simple token for now. Replace with JWT later.
    return f"token_{user_id}"


def objid_to_str(doc: Dict[str, Any]) -> Dict[str, Any]:
    if doc is None:
        return doc
    if "_id" in doc:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
    return doc


# -----------------------------
# App + Middleware
# -----------------------------
app = FastAPI(title="Lucidly API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later when you know domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer(auto_error=False)


# -----------------------------
# Mongo Connection
# -----------------------------
# Primary: MONGO_URL (your Railway var)
# Fallbacks included to prevent future confusion
MONGO_URL = (
    os.getenv("MONGO_URL")
    or os.getenv("MONGODB_URI")
    or os.getenv("MONGO_URI")
    or os.getenv("DATABASE_URL")
)

mongo_client = None
db = None

if MONGO_URL:
    mongo_client = MongoClient(MONGO_URL)
    db_name = os.getenv("MONGODB_DB") or "lucidly"
    db = mongo_client[db_name]

    users_col = db["users"]
    dreams_col = db["dreams"]
    sessions_col = db["sessions"]
else:
    users_col = None
    dreams_col = None
    sessions_col = None


def require_mongo():
    if db is None:
        raise HTTPException(
            status_code=500,
            detail="MongoDB is not configured. Set MONGO_URL (and optionally MONGODB_DB).",
        )


# -----------------------------
# Auth
# -----------------------------
def get_current_user(token_data=Depends(security)):
    """
    Reads bearer token and returns the user document (from Mongo).
    Returns None if missing/invalid.
    """
    if not token_data:
        return None

    token = token_data.credentials
    if not token:
        return None

    require_mongo()

    session = sessions_col.find_one({"token": token})
    if not session:
        return None

    user_id = session.get("user_id")
    if not user_id:
        return None

    user = users_col.find_one({"user_id": user_id})
    if not user:
        return None

    return objid_to_str(user)


def require_user(current_user=Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return current_user


# -----------------------------
# Health / Root
# -----------------------------
@app.get("/")
def root():
    return {"message": "Lucidly API is running!", "status": "ok"}


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": now_iso(),
        "mongo_configured": bool(MONGO_URL),
        "db_name": (db.name if db is not None else None),
    }


# -----------------------------
# Auth Endpoints (Mongo-backed)
# -----------------------------
@app.post("/api/auth/register")
def register(user_data: dict):
    require_mongo()

    email = normalize_email(user_data.get("email", ""))
    name = (user_data.get("name") or "").strip()

    if not email:
        raise HTTPException(status_code=400, detail="Email is required")

    existing = users_col.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    user_id = f"user_{int(datetime.utcnow().timestamp())}"
    user_profile = {
        "user_id": user_id,
        "name": name,
        "email": email,
        "is_premium": False,
        "role": "dreamer",
        "lucy_tokens_used": 0,
        "lucy_tokens_limit": 3,
        "image_tokens_used": 0,
        "image_tokens_limit": 3,
        "video_tokens_used": 0,
        "video_tokens_limit": 3,
        "generation_count": 0,
        "created_at": now_iso(),
    }

    users_col.insert_one(user_profile)

    token = make_token(user_id)
    sessions_col.insert_one({"token": token, "user_id": user_id, "created_at": now_iso()})

    saved_user = users_col.find_one({"email": email})
    return {"token": token, "token_type": "bearer", "user": objid_to_str(saved_user)}


@app.post("/api/auth/login")
def login(credentials: dict):
    require_mongo()

    email = normalize_email(credentials.get("email", ""))
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")

    user = users_col.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    token = make_token(user["user_id"])

    sessions_col.update_one(
        {"token": token},
        {
            "$set": {"token": token, "user_id": user["user_id"], "updated_at": now_iso()},
            "$setOnInsert": {"created_at": now_iso()},
        },
        upsert=True,
    )

    return {"token": token, "token_type": "bearer", "user": objid_to_str(user)}


@app.post("/api/auth/logout")
def logout(token_data=Depends(security)):
    """
    Server-side logout. Frontend MUST still delete its local token.
    """
    require_mongo()

    if not token_data or not token_data.credentials:
        raise HTTPException(status_code=401, detail="Authentication required")

    token = token_data.credentials
    sessions_col.delete_many({"token": token})
    return {"ok": True}


@app.get("/api/auth/me")
def get_me(current_user=Depends(require_user)):
    return current_user


@app.post("/api/auth/reset-tokens")
def reset_user_tokens(current_user=Depends(require_user)):
    require_mongo()

    users_col.update_one(
        {"email": current_user["email"]},
        {"$set": {"image_tokens_used": 0, "video_tokens_used": 0, "lucy_tokens_used": 0, "updated_at": now_iso()}},
    )
    updated = users_col.find_one({"email": current_user["email"]})
    return {
        "message": "All tokens reset successfully!",
        "user": objid_to_str(updated),
    }


# -----------------------------
# Dreams (Mongo-backed + protected)
# -----------------------------
@app.get("/api/dreams")
def get_dreams(current_user=Depends(require_user)):
    require_mongo()
    user_id = current_user["user_id"]
    docs = list(dreams_col.find({"user_id": user_id}).sort("created_at", -1))
    return [objid_to_str(d) for d in docs]


@app.post("/api/dreams")
def create_dream(dream_data: dict, current_user=Depends(require_user)):
    require_mongo()
    dream = {
        "user_id": current_user["user_id"],
        "content": dream_data.get("content", ""),
        "mood": dream_data.get("mood", "peaceful"),
        "tags": dream_data.get("tags", []),
        "created_at": now_iso(),
        "user_name": current_user.get("name", ""),
        "user_role": current_user.get("role", "dreamer"),
        "has_liked": False,
        "ai_interpretation": None,
        "ai_image": None,
        "ai_video": None,
        "video_base64": None,
        "is_public": False,
    }
    res = dreams_col.insert_one(dream)
    saved = dreams_col.find_one({"_id": res.inserted_id})
    return objid_to_str(saved)


@app.get("/api/dreams/{dream_id}")
def get_dream(dream_id: str, current_user=Depends(require_user)):
    require_mongo()

    try:
        oid = ObjectId(dream_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid dream id")

    doc = dreams_col.find_one({"_id": oid, "user_id": current_user["user_id"]})
    if not doc:
        raise HTTPException(status_code=404, detail="Dream not found")
    return objid_to_str(doc)

content = (dream_data.get("content") or "").strip()
title = (dream_data.get("title") or "").strip()
if not title:
    # auto-title from content
    title = content[:40] + ("..." if len(content) > 40 else "")

dream = {
    "id": dream_id,
    "user_id": current_user["id"],
    "title": title,
    "content": content,
    ...
}

# -----------------------------
# AI Endpoints (mock but functional + protected)
# -----------------------------
@app.post("/api/dreams/{dream_id}/generate-image")
def generate_dream_image(dream_id: str, payload: dict, current_user=Depends(require_user)):
    require_mongo()

    try:
        oid = ObjectId(dream_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid dream id")

    dream = dreams_col.find_one({"_id": oid, "user_id": current_user["user_id"]})
    if not dream:
        raise HTTPException(status_code=404, detail="Dream not found")

    if not current_user.get("is_premium", False) and current_user.get("image_tokens_used", 0) >= current_user.get("image_tokens_limit", 3):
        raise HTTPException(status_code=402, detail="Image generation limit reached (upgrade required)")

    mock_image = "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48dGV4dCB4PSI1MCUiIHk9IjUwJSIgZm9udC1zaXplPSIyMCIgdGV4dC1hbmNob3I9Im1pZGRsZSI+TW9jayBBSSBJbWFnZTwvdGV4dD48L3N2Zz4="

    dreams_col.update_one({"_id": oid}, {"$set": {"ai_image": mock_image, "is_public": True, "updated_at": now_iso()}})
    if not current_user.get("is_premium", False):
        users_col.update_one({"email": current_user["email"]}, {"$inc": {"image_tokens_used": 1}})

    return {"ok": True, "image": mock_image}


@app.post("/api/dreams/{dream_id}/generate-video")
def generate_dream_video(dream_id: str, payload: dict, current_user=Depends(require_user)):
    require_mongo()

    try:
        oid = ObjectId(dream_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid dream id")

    dream = dreams_col.find_one({"_id": oid, "user_id": current_user["user_id"]})
    if not dream:
        raise HTTPException(status_code=404, detail="Dream not found")

    if not current_user.get("is_premium", False) and current_user.get("video_tokens_used", 0) >= current_user.get("video_tokens_limit", 3):
        raise HTTPException(status_code=402, detail="Video generation limit reached (upgrade required)")

    sample_url = "https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4"
    dreams_col.update_one({"_id": oid}, {"$set": {"ai_video": sample_url, "is_public": True, "updated_at": now_iso()}})
    if not current_user.get("is_premium", False):
        users_col.update_one({"email": current_user["email"]}, {"$inc": {"video_tokens_used": 1}})

    return {"ok": True, "video_url": sample_url}


@app.post("/api/dreams/{dream_id}/lucy-interpretation")
def get_lucy_interpretation(dream_id: str, payload: dict, current_user=Depends(require_user)):
    require_mongo()

    try:
        oid = ObjectId(dream_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid dream id")

    dream = dreams_col.find_one({"_id": oid, "user_id": current_user["user_id"]})
    if not dream:
        raise HTTPException(status_code=404, detail="Dream not found")

    if not current_user.get("is_premium", False) and current_user.get("lucy_tokens_used", 0) >= current_user.get("lucy_tokens_limit", 3):
        raise HTTPException(status_code=402, detail="Lucy interpretation limit reached (upgrade required)")

    interpretation = (
        f"Hello {current_user.get('name','dreamer')}! ✨\n\n"
        f"I analyzed your dream: \"{(dream.get('content') or '')[:80]}...\"\n\n"
        f"Symbolic Meaning: transformation and personal growth.\n"
        f"Emotional Insights: mood = {dream.get('mood','peaceful')}.\n"
        f"Lucy’s Wisdom: trust your intuition.\n"
    )

    dreams_col.update_one({"_id": oid}, {"$set": {"ai_interpretation": interpretation, "updated_at": now_iso()}})
    if not current_user.get("is_premium", False):
        users_col.update_one({"email": current_user["email"]}, {"$inc": {"lucy_tokens_used": 1}})

    return {"ok": True, "interpretation": interpretation}


# -----------------------------
# Run
# -----------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=False)
