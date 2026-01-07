from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any
from datetime import datetime
import os
import traceback
import logging

from pymongo import MongoClient
from bson import ObjectId

# ======================================================
# LOGGING (RAILWAY)
# ======================================================
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
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
# FORCE FULL TRACEBACKS IN RAILWAY LOGS
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
        return JSONResponse(status_code=500, content={"detail": "Internal Server Error (see Railway logs)"})

# ======================================================
# DATABASE
# ======================================================
MONGO_URL = os.getenv("MONGO_URL", "").strip()
DB_NAME = os.getenv("MONGO_DB_NAME", "lucidly").strip()

mongo = None
db = None

if not MONGO_URL:
    logger.error("❌ MONGO_URL NOT SET")
else:
    try:
        mongo = MongoClient(
            MONGO_URL,
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=10000,
            socketTimeoutMS=45000,
        )
        db = mongo[DB_NAME]
        logger.info("✅ Mongo configured for DB: %s", DB_NAME)
    except Exception:
        logger.error("❌ Mongo init failed")
        logger.error(traceback.format_exc())
        mongo = None
        db = None

# ✅ IMPORTANT: never do `if db:` with PyMongo
users_col = db["users"] if db is not None else None
dreams_col = db["dreams"] if db is not None else None
sessions_col = db["sessions"] if db is not None else None

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

    sess = sessions_col.find_one({"token": creds.credentials})
    if not sess:
        raise HTTPException(401, "Invalid token")

    user = users_col.find_one({"_id": sess["user_id"]})
    if not user:
        sessions_col.delete_one({"token": creds.credentials})
        raise HTTPException(401, "Invalid token")

    return {"user": user, "token": creds.credentials}

# ======================================================
# HEALTH
# ======================================================
@app.get("/api/health")
def health():
    details = {"status": "ok", "ts": now(), "db_connected": (db is not None), "db_name": (DB_NAME if db is not None else None)}
    if mongo is not None:
        try:
            mongo.admin.command("ping")
            details["db_ping"] = "ok"
        except Exception as e:
            details["db_ping"] = f"error: {type(e).__name__}"
            logger.error("❌ Mongo ping failed")
            logger.error(traceback.format_exc())
    return details

# ======================================================
# AI VIDEO ROUTE — will now show real traceback in logs
# ======================================================
@app.post("/api/dreams/{dream_id}/generate-video")
def generate_video(dream_id: str, ctx=Depends(get_current_user)):
    try:
        logger.info("🎬 VIDEO GEN START %s", dream_id)

        # TODO: your real Luma call goes here
        raise RuntimeError("TEST TRACE: replace with Luma implementation")

    except Exception:
        logger.error("❌ VIDEO GEN FAILED")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=502, detail="Video generation failed — see Railway logs")
