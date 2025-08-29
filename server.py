from fastapi import FastAPI, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
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

# Security
security = HTTPBearer(auto_error=False)

# Simple in-memory storage
users_db = {}
dreams_db = {}
user_sessions = {}

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
    user_sessions[token] = user_profile
    
    return {
        "token": token,
        "token_type": "bearer",
        "user": user_profile
    }

@app.post("/api/auth/login") 
def login(credentials: dict):
    email = credentials.get("email", "")
    
    if email in users_db:
        user = users_db[email]
        token = f"token_{user['id']}"
        user_sessions[token] = user
        return {
            "token": token,
            "token_type": "bearer", 
            "user": user
        }
    else:
        return {"error": "User not found"}

# FIXED: Proper authentication function
def get_current_user(token_data = Depends(security)):
    if not token_data:
        return None
    
    token = token_data.credentials
    user = user_sessions.get(token)
    return user

@app.get("/api/auth/me")
def get_me(current_user = Depends(get_current_user)):
    if current_user:
        return current_user
    else:
        return {"error": "Not authenticated"}

# TOKEN RESET ENDPOINT
@app.post("/api/auth/reset-tokens")
def reset_user_tokens(current_user = Depends(get_current_user)):
    if not current_user:
        return {"error": "Authentication required"}
    
    email = current_user.get("email")
    if email and email in users_db:
        # Reset all tokens
        users_db[email]["image_tokens_used"] = 0
        users_db[email]["video_tokens_used"] = 0 
        users_db[email]["lucy_tokens_used"] = 0
        
        # Update session
        token = f"token_{current_user['id']}"
        if token in user_sessions:
            user_sessions[token]["image_tokens_used"] = 0
            user_sessions[token]["video_tokens_used"] = 0
            user_sessions[token]["lucy_tokens_used"] = 0
    
    return {
        "message": "All tokens reset successfully! You now have 3 free uses of each AI feature.",
        "image_tokens_remaining": 3,
        "video_tokens_remaining": 3,
        "lucy_tokens_remaining": 3
    }

# DREAMS ENDPOINTS
@app.get("/api/dreams")
def get_dreams(current_user = Depends(get_current_user)):
    if not current_user:
        return []
    
    user_dreams = [dream for dream in dreams_db.values() if dream.get("user_id") == current_user["id"]]
    return user_dreams

@app.post("/api/dreams")
def create_dream(dream_data: dict, current_user = Depends(get_current_user)):
    if not current_user:
        return {"error": "Authentication required"}
    
    dream_id = f"dream_{len(dreams_db) + 1}"
    dream = {
        "id": dream_id,
        "user_id": current_user["id"],
        "content": dream_data.get("content", ""),
        "mood": dream_data.get("mood", "peaceful"),
        "tags": dream_data.get("tags", []),
        "created_at": datetime.now().isoformat(),
        "user_name": current_user["name"],
        "user_role": current_user["role"],
        "has_liked": False,
        "ai_interpretation": None,
        "ai_image": None,
        "ai_video": None,
        "video_base64": None,
        "is_public": False
    }
    dreams_db[dream_id] = dream
    return dream

@app.get("/api/dreams/{dream_id}")
def get_dream(dream_id: str):
    dream = dreams_db.get(dream_id)
    if not dream:
        return {"error": "Dream not found"}
    
    # Ensure all fields exist
    if "ai_image" not in dream:
        dream["ai_image"] = None
    if "ai_video" not in dream:
        dream["ai_video"] = None
    if "ai_interpretation" not in dream:
        dream["ai_interpretation"] = None
    if "tags" not in dream:
        dream["tags"] = []
        
    return dream

# AI IMAGE GENERATION
@app.post("/api/dreams/{dream_id}/generate-image")
def generate_dream_image(dream_id: str, image_data: dict, current_user = Depends(get_current_user)):
    if not current_user:
        return {"error": "Authentication required"}
    
    # Check if dream exists AND belongs to user
    dream = dreams_db.get(dream_id)
    if not dream or dream.get("user_id") != current_user["id"]:
        return {"error": "Dream not found"}
    
    # Check limits
    if not current_user.get("is_premium", False) and current_user.get("image_tokens_used", 0) >= current_user.get("image_tokens_limit", 3):
        return {
            "error": "Image generation limit reached",
            "message": f"You've used all {current_user.get('image_tokens_limit', 3)} free image generations. Upgrade to premium!"
        }
    
    # Generate image
    mock_image = "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZGVmcz48bGluZWFyR3JhZGllbnQgaWQ9ImdyYWQiIHgxPSIwJSIgeTE9IjAlIiB4Mj0iMTAwJSIgeTI9IjEwMCUiPjxzdG9wIG9mZnNldD0iMCUiIHN0b3AtY29sb3I9IiM2MzY2ZjEiLz48c3RvcCBvZmZzZXQ9IjMzJSIgc3RvcC1jb2xvcj0iIzhhNWNmNiIvPjxzdG9wIG9mZnNldD0iNjYlIiBzdG9wLWNvbG9yPSIjYTg1NWY3Ii8+PHN0b3Agb2Zmc2V0PSIxMDAlIiBzdG9wLWNvbG9yPSIjZWM0ODk5Ii8+PC9saW5lYXJHcmFkaWVudD48L2RlZnM+PHJlY3Qgd2lkdGg9IjEwMCUiIGhlaWdodD0iMTAwJSIgZmlsbD0idXJsKCNncmFkKSIvPjx0ZXh0IHg9IjUwJSIgeT0iNDAlIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMjQiIGZpbGw9IndoaXRlIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkeT0iLjNlbSIgZm9udC13ZWlnaHQ9ImJvbGQiPkFJIEdlbmVyYXRlZCBJbWFnZTwvdGV4dD48dGV4dCB4PSI1MCUiIHk9IjYwJSIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjE0IiBmaWxsPSJ3aGl0ZSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPkZyb20geW91ciBkcmVhbSBhYm91dCBbZHJlYW1dPC90ZXh0Pjwvc3ZnPg=="
    
    # Update dream
    dreams_db[dream_id]["ai_image"] = mock_image
    dreams_db[dream_id]["is_public"] = True
    
    # Update tokens
    if not current_user.get("is_premium", False):
        email = current_user.get("email")
        if email in users_db:
            users_db[email]["image_tokens_used"] = current_user.get("image_tokens_used", 0) + 1
            # Update session
            token = f"token_{current_user['id']}"
            if token in user_sessions:
                user_sessions[token]["image_tokens_used"] = current_user.get("image_tokens_used", 0) + 1
    
    return {
        "message": "Image generated successfully!",
        "image_url": mock_image,
        "image_data": mock_image,
        "image_base64": mock_image,
        "task_id": f"img_task_{dream_id}",
        "tokens_remaining": max(0, current_user.get("image_tokens_limit", 3) - current_user.get("image_tokens_used", 0) - 1)
    }

# VIDEO GENERATION
@app.post("/api/dreams/{dream_id}/generate-video")
def generate_dream_video(dream_id: str, video_data: dict, current_user = Depends(get_current_user)):
    if not current_user:
        return {"error": "Authentication required"}
    
    dream = dreams_db.get(dream_id)
    if not dream or dream.get("user_id") != current_user["id"]:
        return {"error": "Dream not found"}
    
    if not current_user.get("is_premium", False) and current_user.get("video_tokens_used", 0) >= current_user.get("video_tokens_limit", 3):
        return {
            "error": "Video generation limit reached",
            "message": f"You've used all {current_user.get('video_tokens_limit', 3)} free video generations. Upgrade to premium!"
        }
    
    # Update dream
    dreams_db[dream_id]["ai_video"] = "https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4"
    dreams_db[dream_id]["video_base64"] = "sample_video_data"
    dreams_db[dream_id]["is_public"] = True
    
    # Update tokens
    if not current_user.get("is_premium", False):
        email = current_user.get("email")
        if email in users_db:
            users_db[email]["video_tokens_used"] = current_user.get("video_tokens_used", 0) + 1
            token = f"token_{current_user['id']}"
            if token in user_sessions:
                user_sessions[token]["video_tokens_used"] = current_user.get("video_tokens_used", 0) + 1
    
    return {
        "message": "Video generation started successfully!",
        "task_id": f"vid_task_{dream_id}",
        "estimated_time": "60-120 seconds",
        "video_url": "https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4",
        "tokens_remaining": max(0, current_user.get("video_tokens_limit", 3) - current_user.get("video_tokens_used", 0) - 1)
    }

@app.get("/api/dreams/{dream_id}/video-status")
def get_video_status(dream_id: str):
    return {
        "status": "completed",
        "video_url": "https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4",
        "progress": "100%"
    }

# LUCY AI
@app.post("/api/dreams/{dream_id}/lucy-interpretation")
def get_lucy_interpretation(dream_id: str, request_data: dict, current_user = Depends(get_current_user)):
    if not current_user:
        return {"error": "Authentication required"}
    
    dream = dreams_db.get(dream_id)
    if not dream or dream.get("user_id") != current_user["id"]:
        return {"error": "Dream not found"}
    
    if not current_user.get("is_premium", False) and current_user.get("lucy_tokens_used", 0) >= current_user.get("lucy_tokens_limit", 3):
        return {
            "error": "Lucy interpretation limit reached",
            "message": f"You've used all {current_user.get('lucy_tokens_limit', 3)} free Lucy interpretations. Upgrade to premium!"
        }
    
    interpretation = f"""Hello {current_user.get('name', 'dreamer')}! ✨

I've analyzed your dream: "{dream.get('content', 'your beautiful dream')[:50]}..."

🌙 **Symbolic Meaning**: Your dream reflects transformation and personal growth.

💫 **Emotional Insights**: The {dream.get('mood', 'peaceful')} mood indicates inner balance.

✨ **Lucy's Wisdom**: Trust your intuition, {current_user.get('name', 'dear dreamer')}!

Sweet dreams! - Lucy ✨

*You have {2 - current_user.get('lucy_tokens_used', 0)} interpretations remaining*"""
    
    # Update dream and tokens
    dreams_db[dream_id]["ai_interpretation"] = interpretation
    
    if not current_user.get("is_premium", False):
        email = current_user.get("email")
        if email in users_db:
            users_db[email]["lucy_tokens_used"] = current_user.get("lucy_tokens_used", 0) + 1
            token = f"token_{current_user['id']}"
            if token in user_sessions:
                user_sessions[token]["lucy_tokens_used"] = current_user.get("lucy_tokens_used", 0) + 1
    
    return {
        "dream_id": dream_id,
        "interpretation": interpretation,
        "cached": False
    }

# DASHBOARD
@app.get("/api/dashboard/stats")
def get_dashboard_stats(current_user = Depends(get_current_user)):
    if not current_user:
        return {"error": "Authentication required"}
    
    user_dreams = [dream for dream in dreams_db.values() if dream.get("user_id") == current_user["id"]]
    
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

# GALLERY
@app.get("/api/gallery/dreams")
def get_gallery():
    public_dreams = []
    for dream in dreams_db.values():
        if dream.get("is_public", False) and (dream.get("ai_image") or dream.get("ai_video")):
            public_dreams.append(dream)
    
    # Sample dreams if empty
    if not public_dreams:
        sample_dreams = [
            {
                "id": "sample_1",
                "content": "A magical forest filled with glowing butterflies",
                "mood": "mystical",
                "tags": ["nature", "magic"],
                "user_name": "DreamExplorer",
                "user_role": "dreamer",
                "ai_image": "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZGVmcz48bGluZWFyR3JhZGllbnQgaWQ9ImdyYWQxIiB4MT0iMCUiIHkxPSIwJSIgeDI9IjEwMCUiIHkyPSIxMDAlIj48c3RvcCBvZmZzZXQ9IjAlIiBzdG9wLWNvbG9yPSIjMTBiOTgxIi8+PHN0b3Agb2Zmc2V0PSIxMDAlIiBzdG9wLWNvbG9yPSIjMzMzOGZmIi8+PC9saW5lYXJHcmFkaWVudD48L2RlZnM+PHJlY3Qgd2lkdGg9IjEwMCUiIGhlaWdodD0iMTAwJSIgZmlsbD0idXJsKCNncmFkMSkiLz48dGV4dCB4PSI1MCUiIHk9IjUwJSIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjE2IiBmaWxsPSJ3aGl0ZSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPk1hZ2ljYWwgRm9yZXN0PC90ZXh0Pjwvc3ZnPg==",
                "created_at": datetime.now().isoformat(),
                "has_liked": False
            }
        ]
        return sample_dreams
    
    return public_dreams[-10:]

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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
