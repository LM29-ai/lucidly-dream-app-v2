from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import uvicorn
from datetime import datetime

app = FastAPI(title="Lucidly API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple in-memory storage
users_db = {}
dreams_db = {}

@app.get("/")
def root():
    return {"message": "Lucidly API is running!", "status": "ok"}

@app.get("/api/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/api/auth/register")
def register(user_data: dict):
    email = user_data.get("email", "")
    name = user_data.get("name", "")
    
    user_id = f"user_{len(users_db) + 1}"
    users_db[email] = {
        "id": user_id,
        "name": name,
        "email": email,
        "is_premium": False,
        "role": "dreamer"
    }
    
    return {
        "token": f"token_{user_id}",
        "token_type": "bearer",
        "user": users_db[email]
    }

@app.post("/api/auth/login") 
def login(credentials: dict):
    email = credentials.get("email", "")
    
    if email in users_db:
        user = users_db[email]
        return {
            "token": f"token_{user['id']}",
            "token_type": "bearer", 
            "user": user
        }
    else:
        return {"error": "User not found"}

@app.get("/api/auth/me")
def get_me():
    return {
        "id": "user_1",
        "name": "Test User", 
        "email": "test@example.com",
        "is_premium": False,
        "role": "dreamer"
    }

# DREAMS ENDPOINTS (Added to fix 404s)
@app.get("/api/dreams")
def get_dreams():
    return []  # Empty list for now

@app.post("/api/dreams")
def create_dream(dream_data: dict):
    dream_id = f"dream_{len(dreams_db) + 1}"
    dream = {
        "id": dream_id,
        "content": dream_data.get("content", ""),
        "mood": dream_data.get("mood", "peaceful"),
        "tags": dream_data.get("tags", []),
        "created_at": datetime.now().isoformat(),
        "user_name": "Test User",
        "user_role": "dreamer",
        "has_liked": False
    }
    dreams_db[dream_id] = dream
    return dream

@app.get("/api/dreams/{dream_id}")
def get_dream(dream_id: str):
    return dreams_db.get(dream_id, {"error": "Dream not found"})

# DASHBOARD ENDPOINTS (Added to fix 404s)
@app.get("/api/dashboard/stats")
def get_dashboard_stats():
    return {
        "dream_count": len(dreams_db),
        "lucid_count": 0,
        "lucid_percentage": 0,
        "current_streak": 0,
        "longest_streak": 0,
        "ai_creations_count": 0,
        "mood_distribution": {},
        "recent_dreams": list(dreams_db.values())[-5:]  # Last 5 dreams
    }

# CHALLENGES ENDPOINTS (Added to fix 404s)
@app.get("/api/challenges")
def get_challenges():
    return [
        {
            "id": "weekly-lucid",
            "title": "Weekly Lucid Challenge",
            "description": "Achieve lucid dreaming 3 times this week",
            "type": "lucid_count",
            "target": 3,
            "reward": "Special badge + 100 points",
            "starts_at": "2025-01-20T00:00:00Z",
            "ends_at": "2025-01-27T23:59:59Z",
            "is_active": True
        }
    ]

# SOCIAL/FEED ENDPOINTS (Added to fix 404s)
@app.get("/api/feed")
def get_feed():
    return []  # Empty feed for now

@app.get("/api/gallery/dreams")
def get_gallery():
    return []  # Empty gallery for now

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
