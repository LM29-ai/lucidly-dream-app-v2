from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import uvicorn
from datetime import datetime
import base64

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
user_tokens = {}  # Track which user is logged in

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
    user_profile = {
        "id": user_id,
        "name": name,
        "email": email,
        "is_premium": False,
        "role": "dreamer",
        # FREE TIER - 3 LUCY TOKENS!
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

# FIXED: Get real user based on token (no more test user!)
def get_user_from_token(auth_header: str = None):
    if not auth_header:
        return None
    
    try:
        token = auth_header.replace("Bearer ", "")
        return user_tokens.get(token)
    except:
        return None

@app.get("/api/auth/me")
def get_me(authorization: str = None):
    # FIXED: Return actual logged-in user, not test user
    user = get_user_from_token(authorization)
    if user:
        return user
    else:
        return {
            "error": "Not authenticated"
        }

# DREAMS ENDPOINTS
@app.get("/api/dreams")
def get_dreams(authorization: str = None):
    user = get_user_from_token(authorization)
    if not user:
        return []
    
    # Return dreams for the actual user
    user_dreams = [dream for dream in dreams_db.values() if dream.get("user_id") == user["id"]]
    return user_dreams

@app.post("/api/dreams")
def create_dream(dream_data: dict, authorization: str = None):
    user = get_user_from_token(authorization)
    if not user:
        return {"error": "Authentication required"}
    
    dream_id = f"dream_{len(dreams_db) + 1}"
    dream = {
        "id": dream_id,
        "user_id": user["id"],  # FIXED: Associate with real user
        "content": dream_data.get("content", ""),
        "mood": dream_data.get("mood", "peaceful"),
        "tags": dream_data.get("tags", []),
        "created_at": datetime.now().isoformat(),
        "user_name": user["name"],  # FIXED: Use real user name
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
    return dreams_db.get(dream_id, {"error": "Dream not found"})

# AI IMAGE GENERATION ENDPOINT (FIXED!)
@app.post("/api/dreams/{dream_id}/generate-image")
def generate_dream_image(dream_id: str, image_data: dict, authorization: str = None):
    user = get_user_from_token(authorization)
    if not user:
        return {"error": "Authentication required"}
    
    # Check image token limits
    if not user.get("is_premium", False) and user.get("image_tokens_used", 0) >= user.get("image_tokens_limit", 3):
        return {
            "error": "Image generation limit reached",
            "message": f"You've used all {user.get('image_tokens_limit', 3)} free image generations. Upgrade to premium for unlimited access!"
        }
    
    # IMPROVED: Better mock image (colorful gradient)
    mock_image_base64 = "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZGVmcz48bGluZWFyR3JhZGllbnQgaWQ9ImdyYWQiIHgxPSIwJSIgeTE9IjAlIiB4Mj0iMTAwJSIgeTI9IjEwMCUiPjxzdG9wIG9mZnNldD0iMCUiIHN0b3AtY29sb3I9IiM2MzY2ZjEiLz48c3RvcCBvZmZzZXQ9IjUwJSIgc3RvcC1jb2xvcj0iIzhhNWNmNiIvPjxzdG9wIG9mZnNldD0iMTAwJSIgc3RvcC1jb2xvcj0iI2E4NTVmNyIvPjwvbGluZWFyR3JhZGllbnQ+PC9kZWZzPjxyZWN0IHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiIGZpbGw9InVybCgjZ3JhZCkiLz48dGV4dCB4PSI1MCUiIHk9IjUwJSIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjE4IiBmaWxsPSJ3aGl0ZSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPkFJIEdlbmVyYXRlZCBJbWFnZSDinajvuI88L3RleHQ+PC9zdmc+"
    
    # Update dream with generated image
    if dream_id in dreams_db:
        dreams_db[dream_id]["ai_image"] = mock_image_base64
    
    # Increment user's image tokens
    if not user.get("is_premium", False):
        users_db[user["email"]]["image_tokens_used"] = user.get("image_tokens_used", 0) + 1
        user_tokens[f"token_{user['id']}"]["image_tokens_used"] = user.get("image_tokens_used", 0) + 1
    
    return {
        "message": "Image generated successfully!",
        "image_url": mock_image_base64,
        "image_base64": mock_image_base64.split(',')[1] if ',' in mock_image_base64 else mock_image_base64,
        "task_id": f"img_task_{dream_id}",
        "tokens_remaining": max(0, user.get("image_tokens_limit", 3) - user.get("image_tokens_used", 0) - 1)
    }

# AI VIDEO GENERATION ENDPOINT
@app.post("/api/dreams/{dream_id}/generate-video")
def generate_dream_video(dream_id: str, video_data: dict, authorization: str = None):
    user = get_user_from_token(authorization)
    if not user:
        return {"error": "Authentication required"}
    
    # Check video token limits  
    if not user.get("is_premium", False) and user.get("video_tokens_used", 0) >= user.get("video_tokens_limit", 3):
        return {
            "error": "Video generation limit reached",
            "message": f"You've used all {user.get('video_tokens_limit', 3)} free video generations. Upgrade to premium for unlimited access!"
        }
    
    # Mock video response
    if dream_id in dreams_db:
        dreams_db[dream_id]["ai_video"] = "https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4"
        dreams_db[dream_id]["video_base64"] = "mock_video_base64_data"
    
    # Increment user's video tokens
    if not user.get("is_premium", False):
        users_db[user["email"]]["video_tokens_used"] = user.get("video_tokens_used", 0) + 1
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
        "video_base64": "mock_video_base64_data",
        "progress": "100%"
    }

# LUCY AI INTERPRETATION ENDPOINT (FIXED - FREE TIER WORKING!)
@app.post("/api/dreams/{dream_id}/lucy-interpretation")
def get_lucy_interpretation(dream_id: str, request_data: dict, authorization: str = None):
    user = get_user_from_token(authorization)
    if not user:
        return {"error": "Authentication required"}
    
    dream = dreams_db.get(dream_id)
    if not dream:
        return {"error": "Dream not found"}
    
    # FIXED: Check Lucy token limits (FREE TIER!)
    if not user.get("is_premium", False) and user.get("lucy_tokens_used", 0) >= user.get("lucy_tokens_limit", 3):
        return {
            "error": "Lucy interpretation limit reached",
            "message": f"You've used all {user.get('lucy_tokens_limit', 3)} free Lucy interpretations. Upgrade to premium for unlimited Lucy wisdom!"
        }
    
    interpretation = f"""Hello {user.get('name', 'dreamer')}! ✨

I've carefully analyzed your dream about "{dream.get('content', 'your experience')[:50]}..." and here's what I see:

🌙 **Symbolic Meaning**: Your dream reflects your subconscious processing of recent experiences and emotions. The imagery suggests transformation and personal growth on your horizon.

💫 **Emotional Insights**: The {dream.get('mood', 'peaceful')} mood you felt indicates your inner emotional state. This suggests you're seeking balance and harmony in your current life situation.

🔮 **Deeper Analysis**: This dream may represent:
- A desire for positive change or new beginnings  
- Your mind processing daily experiences and emotions
- Inner wisdom guiding you toward personal growth
- Unresolved feelings seeking resolution and peace

✨ **Lucy's Personal Message**: You have beautiful dream energy, {user.get('name', 'dear dreamer')}! Your subconscious is actively working to help you grow and find clarity. Trust the messages your dreams bring you.

Remember, you are the ultimate interpreter of your own dreams. I'm simply here to guide you on this magical journey of self-discovery.

Keep dreaming and exploring! 
- Lucy ✨

*You have {2 - user.get('lucy_tokens_used', 0)} Lucy interpretations remaining*"""
    
    # Update dream with interpretation
    if dream_id in dreams_db:
        dreams_db[dream_id]["ai_interpretation"] = interpretation
    
    # Increment user's Lucy tokens
    if not user.get("is_premium", False):
        users_db[user["email"]]["lucy_tokens_used"] = user.get("lucy_tokens_used", 0) + 1
        user_tokens[f"token_{user['id']}"]["lucy_tokens_used"] = user.get("lucy_tokens_used", 0) + 1
    
    return {
        "dream_id": dream_id,
        "interpretation": interpretation,
        "cached": False,
        "tokens_remaining": max(0, user.get("lucy_tokens_limit", 3) - user.get("lucy_tokens_used", 0) - 1)
    }

# DASHBOARD ENDPOINTS
@app.get("/api/dashboard/stats")
def get_dashboard_stats(authorization: str = None):
    user = get_user_from_token(authorization)
    if not user:
        return {"error": "Authentication required"}
    
    user_dreams = [dream for dream in dreams_db.values() if dream.get("user_id") == user["id"]]
    
    return {
        "dream_count": len(user_dreams),
        "lucid_count": 0,
        "lucid_percentage": 0,
        "current_streak": 1 if user_dreams else 0,
        "longest_streak": 1 if user_dreams else 0,
        "ai_creations_count": sum(1 for dream in user_dreams if dream.get("ai_image") or dream.get("ai_video")),
        "mood_distribution": {"peaceful": 60, "excited": 30, "mysterious": 10},
        "recent_dreams": user_dreams[-3:]  # Last 3 dreams
    }

# CHALLENGES ENDPOINTS
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

# SOCIAL/FEED ENDPOINTS
@app.get("/api/feed")
def get_feed():
    return []

@app.get("/api/gallery/dreams")
def get_gallery():
    return []

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
