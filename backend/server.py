from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any, List
from datetime import datetime
import os
import traceback
import logging

from pymongo import MongoClient
from bson import ObjectId

# ======================================================
# LOGGING (THIS IS THE IMPORTANT PART)
# ======================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger("lucidly")

# ======================================================
# APP INIT
# ======================================================
app = FastAPI(title="Lucidly API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer(auto_error=False)

# ======================================================
# GLOBAL STACK TRACE MIDDLEWARE (FOR RAILWAY)
# ======================================================
@app.middleware("http")
async def force_tracebacks(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        logger.error("🔥 UNHANDLED EXCEPTION")
        logger.error("PATH: %s %s", request.method, request.url.path)
        logger.error("ERROR: %s", str(e))
        logger.error(traceback.format_exc())

        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error (see Railway logs)"}
        )

# ======================================================
# DATABASE
# ======================================================
MONGO_URL = os.getenv("MONGO_URL")
DB_NAME = os.getenv("MONGO_DB_NAME", "lucidly")

if not MONGO_URL:
    mongo = None
    db = None
    logger.error("❌ MONGO_URL NOT SET")
else:
    mongo = MongoClient(
        MONGO_URL,
        serverSelectionTimeoutMS=10000,
        connectTimeoutMS=10000,
        socketTimeoutMS=45000,
    )
    db = mongo[DB_NAME]

users_col = db["users"] if db else None
dreams_col = db["dreams"] if db else None
sessions_col = db["sessions"] if db else None

# ======================================================
# HELPERS
# ======================================================
def now():
    return datetime.utcnow().isoformat() + "Z"

def oid(id: str):
    try:
        return ObjectId(id)
    except Exception:
        raise HTTPException(400, "Invalid ID")

def require_db():
    if db is None:
        raise HTTPException(500, "Database not connected")

def get_current_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    require_db()
    if not creds:
        raise HTTPException(401, "Authentication required")

    session = sessions_col.find_one({"token": creds.credentials})
    if not session:
        raise HTTPException(401, "Invalid token")

    user = users_col.find_one({"_id": session["user_id"]})
    if not user:
        raise HTTPException(401, "Invalid session")

    return {"user": user, "token": creds.credentials}

# ======================================================
# HEALTH CHECK
# ======================================================
@app.get("/api/health")
def health():
    try:
        if mongo:
            mongo.admin.command("ping")
        return {"status": "ok", "db": True, "ts": now()}
    except Exception as e:
        logger.error(traceback.format_exc())
        return {"status": "error", "db": False}

# ======================================================
# AI IMAGE GENERATION (WRAPPED)
# ======================================================
@app.post("/api/dreams/{dream_id}/generate-image")
def generate_image(dream_id: str, ctx=Depends(get_current_user)):
    try:
        logger.info("🎨 IMAGE GEN START %s", dream_id)

        # 🔧 TEMP MOCK (replace with OpenAI when stable)
        image_data = "data:image/png;base64,MOCK_IMAGE_DATA"

        dreams_col.update_one(
            {"_id": oid(dream_id)},
            {"$set": {"ai_image": image_data}}
        )

        return {"ok": True, "image": image_data}

    except Exception as e:
        logger.error("❌ IMAGE GEN FAILED")
        logger.error(traceback.format_exc())
        raise HTTPException(502, "Image generation failed")

# ======================================================
# AI VIDEO GENERATION (THIS IS FAILING — NOW LOGGED)
# ======================================================
@app.post("/api/dreams/{dream_id}/generate-video")
def generate_video(dream_id: str, ctx=Depends(get_current_user)):
    try:
        logger.info("🎬 VIDEO GEN START %s", dream_id)

        # 👇 YOUR LUMA CODE IS FAILING HERE
        # KEEP THIS WRAPPED SO TRACEBACK SHOWS
        raise RuntimeError("INTENTIONAL TRACE TEST — replace with Luma call")

    except Exception as e:
        logger.error("❌ VIDEO GEN FAILED")
        logger.error(str(e))
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=502,
            detail="Video generation failed — see Railway logs"
        )

# ======================================================
# LUCY AI
# ======================================================
@app.post("/api/dreams/{dream_id}/lucy-interpretation")
def lucy(dream_id: str, ctx=Depends(get_current_user)):
    try:
        return {
            "dream_id": dream_id,
            "interpretation": "Lucy interpretation placeholder"
        }
    except Exception:
        logger.error(traceback.format_exc())
        raise HTTPException(500, "Lucy failed")

