from fastapi import FastAPI, Header
from fastapi.middleware.cors import CORSMiddleware
import os
import uvicorn
from datetime import datetime
from typing import Optional

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
user_tokens = {}

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
    
    if email in users_db:
        return {"error": "Email already registered"}
    
    user_id = f"user_{len(users_db) + 1}"
    user_profile = {
        "id": user_id,
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
        "generation_count": 0
    }
    
    users_db[email] = user_profile
    token = f"token_{user_id}"
    user_tokens[token] = user_profile
    
    return {
        "token": token,
        "token_type": "bearer",
        "user": user_profile
    }

@app.post("/api/auth/login") 
def login(credentials: dict):
    email = credentials.get("email", "")
    password = credentials.get("password", "")
    
    if email in users_db:
        user = users_db[email]
        token = f"token_{user['id']}"
        user_tokens[token] = user
        return {
            "token": token,
            "token_type": "bearer", 
            "user": user
        }
    else:
        return {"error": "User not found"}

# FIXED: Proper header extraction!
def get_user_from_header(authorization: Optional[str] = Header(None)):
    if not authorization:
        return None
    
    try:
        token = authorization.replace("Bearer ", "")
        return user_tokens.get(token)
    except:
        return None

@app.get("/api/auth/me")
def get_me(authorization: Optional[str] = Header(None)):
    user = get_user_from_header(authorization)
    if user:
        return user
    else:
        return {"error": "Not authenticated"}

# DREAMS ENDPOINTS (FIXED!)
@app.get("/api/dreams")
def get_dreams(authorization: Optional[str] = Header(None)):
    user = get_user_from_header(authorization)
    if not user:
        return []
    
    user_dreams = [dream for dream in dreams_db.values() if dream.get("user_id") == user["id"]]
    return user_dreams

@app.post("/api/dreams")
def create_dream(dream_data: dict, authorization: Optional[str] = Header(None)):
    user = get_user_from_header(authorization)
    if not user:
        return {"error": "Authentication required"}
    
    dream_id = f"dream_{len(dreams_db) + 1}"
    dream = {
        "id": dream_id,
        "user_id": user["id"],
        "content": dream_data.get("content", ""),
        "mood": dream_data.get("mood", "peaceful"),
        "tags": dream_data.get("tags", []),  # FIXED: Always array
        "created_at": datetime.now().isoformat(),
        "user_name": user["name"],
        "user_role": user["role"],
        "has_liked": False,
        "ai_interpretation": None,
        "ai_image": None,
        "ai_video": None,
        "video_base64": None
    }
    dreams_db[dream_id] = dream
    return dream

@app.get("/api/dreams/{dream_id}")
def get_dream(dream_id: str):
    dream = dreams_db.get(dream_id, {"error": "Dream not found"})
    # FIXED: Ensure tags is always an array
    if dream and "tags" not in dream:
        dream["tags"] = []
    return dream

# AI IMAGE GENERATION (FIXED!)
@app.post("/api/dreams/{dream_id}/generate-image")
def generate_dream_image(dream_id: str, image_data: dict, authorization: Optional[str] = Header(None)):
    user = get_user_from_header(authorization)
    if not user:
        return {"error": "Authentication required"}
    
    # Check limits
    if not user.get("is_premium", False) and user.get("image_tokens_used", 0) >= user.get("image_tokens_limit", 3):
        return {
            "error": "Image generation limit reached",
            "message": f"You've used all {user.get('image_tokens_limit', 3)} free image generations. Upgrade to premium!"
        }
    
    # Generate mock image
    mock_image = "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZGVmcz48bGluZWFyR3JhZGllbnQgaWQ9ImdyYWQiIHgxPSIwJSIgeTE9IjAlIiB4Mj0iMTAwJSIgeTI9IjEwMCUiPjxzdG9wIG9mZnNldD0iMCUiIHN0b3AtY29sb3I9IiM2MzY2ZjEiLz48c3RvcCBvZmZzZXQ9IjUwJSIgc3RvcC1jb2xvcj0iIzhhNWNmNiIvPjxzdG9wIG9mZnNldD0iMTAwJSIgc3RvcC1jb2xvcj0iI2E4NTVmNyIvPjwvbGluZWFyR3JhZGllbnQ+PC9kZWZzPjxyZWN0IHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiIGZpbGw9InVybCgjZ3JhZCkiLz48dGV4dCB4PSI1MCUiIHk9IjQ1JSIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjIwIiBmaWxsPSJ3aGl0ZSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPkFJIEdlbmVyYXRlZCBJbWFnZTwvdGV4dD48dGV4dCB4PSI1MCUiIHk9IjYwJSIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjE2IiBmaWxsPSJ3aGl0ZSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPkRyZWFtOiAje2RyZWFtX2lkfTwvdGV4dD48L3N2Zz4="
    
    # Update dream and user tokens
    if dream_id in dreams_db:
        dreams_db[dream_id]["ai_image"] = mock_image
    
    # Update user token count
    if not user.get("is_premium", False):
        email = user.get("email")
        if email and email in users_db:
            users_db[email]["image_tokens_used"] = user.get("image_tokens_used", 0) + 1
            user_tokens[f"token_{user['id']}"]["image_tokens_used"] = user.get("image_tokens_used", 0) + 1
    
    return {
        "message": "Image generated successfully!",
        "image_url": mock_image,
        "image_base64": mock_image,
        "task_id": f"img_task_{dream_id}",
        "tokens_remaining": max(0, user.get("image_tokens_limit", 3) - user.get("image_tokens_used", 0) - 1)
    }

# AI VIDEO GENERATION (FIXED!)
@app.post("/api/dreams/{dream_id}/generate-video")
def generate_dream_video(dream_id: str, video_data: dict, authorization: Optional[str] = Header(None)):
    user = get_user_from_header(authorization)
    if not user:
        return {"error": "Authentication required"}
    
    if not user.get("is_premium", False) and user.get("video_tokens_used", 0) >= user.get("video_tokens_limit", 3):
        return {
            "error": "Video generation limit reached",
            "message": f"You've used all {user.get('video_tokens_limit', 3)} free video generations. Upgrade to premium!"
        }
    
    # Mock video
    if dream_id in dreams_db:
        dreams_db[dream_id]["ai_video"] = "https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4"
    
    # Update tokens
    if not user.get("is_premium", False):
        email = user.get("email")
        if email and email in users_db:
            users_db[email]["video_tokens_used"] = user.get("video_tokens_used", 0) + 1
            user_tokens[f"token_{user['id']}"]["video_tokens_used"] = user.get("video_tokens_used", 0) + 1
    
    return {
        "message": "Video generation started",
        "task_id": f"vid_task_{dream_id}",
        "estimated_time": "60-120 seconds",
        "video_url": "https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4",
        "tokens_remaining": max(0, user.get("video_tokens_limit", 3) - user.get("video_tokens_used", 0) - 1)
    }

@app.get("/api/dreams/{dream_id}/video-status")
def get_video_status(dream_id: str):
    return {
        "status": "completed",
        "video_url": "https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4",
        "progress": "100%"
    }

# LUCY AI (FIXED!)
@app.post("/api/dreams/{dream_id}/lucy-interpretation")
def get_lucy_interpretation(dream_id: str, request_data: dict, authorization: Optional[str] = Header(None)):
    user = get_user_from_header(authorization)
    if not user:
        return {"error": "Authentication required"}
    
    dream = dreams_db.get(dream_id)
    if not dream:
        return {"error": "Dream not found"}
    
    # Check Lucy tokens
    if not user.get("is_premium", False) and user.get("lucy_tokens_used", 0) >= user.get("lucy_tokens_limit", 3):
        return {
            "error": "Lucy interpretation limit reached",
            "message": f"You've used all {user.get('lucy_tokens_limit', 3)} free Lucy interpretations. Upgrade to premium!"
        }
    
    interpretation = f"""Hello {user.get('name', 'dreamer')}! ✨

I've analyzed your dream: "{dream.get('content', 'your experience')[:50]}..."

🌙 **Symbolic Meaning**: Your dream reflects transformation and growth.

💫 **Emotional Insights**: The {dream.get('mood', 'peaceful')} mood suggests inner balance.

✨ **Lucy's Wisdom**: Trust your intuition, {user.get('name', 'dear dreamer')}!

Sweet dreams! - Lucy ✨

*{2 - user.get('lucy_tokens_used', 0)} interpretations remaining*"""
    
    # Update dream and tokens
    if dream_id in dreams_db:
        dreams_db[dream_id]["ai_interpretation"] = interpretation
    
    if not user.get("is_premium", False):
        email = user.get("email")
        if email and email in users_db:
            users_db[email]["lucy_tokens_used"] = user.get("lucy_tokens_used", 0) + 1
            user_tokens[f"token_{user['id']}"]["lucy_tokens_used"] = user.get("lucy_tokens_used", 0) + 1
    
    return {
        "dream_id": dream_id,
        "interpretation": interpretation,
        "cached": False
    }

# DASHBOARD (FIXED!)
@app.get("/api/dashboard/stats")
def get_dashboard_stats(authorization: Optional[str] = Header(None)):
    user = get_user_from_header(authorization)
    if not user:
        return {"error": "Authentication required"}
    
    user_dreams = [dream for dream in dreams_db.values() if dream.get("user_id") == user["id"]]
    
    return {
        "dream_count": len(user_dreams),
        "lucid_count": 0,
        "lucid_percentage": 0,
        "current_streak": 1 if user_dreams else 0,
        "longest_streak": 1 if user_dreams else 0,
        "ai_creations_count": len([d for d in user_dreams if d.get("ai_image") or d.get("ai_video")]),
        "mood_distribution": {"peaceful": 60, "excited": 30, "mysterious": 10},
        "recent_dreams": user_dreams[-3:]
    }

# OTHER ENDPOINTS
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

@app.get("/api/feed")
def get_feed():
    return []

@app.get("/api/gallery/dreams")
def get_gallery():
    return []

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
