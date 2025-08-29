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

# TOKEN RESET ENDPOINT (FIXED: Reset tokens for current user)
@app.post("/api/auth/reset-tokens")
def reset_user_tokens(authorization: Optional[str] = Header(None)):
    user = get_user_from_header(authorization)
    if not user:
        return {"error": "Authentication required"}
    
    email = user.get("email")
    if email and email in users_db:
        # Reset all tokens for testing
        users_db[email]["image_tokens_used"] = 0
        users_db[email]["video_tokens_used"] = 0 
        users_db[email]["lucy_tokens_used"] = 0
        
        # Update the active session too
        user_tokens[f"token_{user['id']}"]["image_tokens_used"] = 0
        user_tokens[f"token_{user['id']}"]["video_tokens_used"] = 0
        user_tokens[f"token_{user['id']}"]["lucy_tokens_used"] = 0
    
    return {
        "message": "All tokens reset successfully! You now have 3 free uses of each AI feature.",
        "image_tokens_remaining": 3,
        "video_tokens_remaining": 3,
        "lucy_tokens_remaining": 3
    }

# DREAMS ENDPOINTS (FIXED: Properly handle AI content)
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
        "tags": dream_data.get("tags", []),
        "created_at": datetime.now().isoformat(),
        "user_name": user["name"],
        "user_role": user["role"],
        "has_liked": False,
        "ai_interpretation": None,
        "ai_image": None,
        "ai_video": None,
        "video_base64": None,
        "is_public": False  # FIXED: Add this field
    }
    dreams_db[dream_id] = dream
    return dream

@app.get("/api/dreams/{dream_id}")
def get_dream(dream_id: str):
    dream = dreams_db.get(dream_id)
    if not dream:
        return {"error": "Dream not found"}
    
    # FIXED: Ensure all AI content fields exist
    if "ai_image" not in dream:
        dream["ai_image"] = None
    if "ai_video" not in dream:
        dream["ai_video"] = None
    if "ai_interpretation" not in dream:
        dream["ai_interpretation"] = None
    if "tags" not in dream:
        dream["tags"] = []
    if "is_public" not in dream:
        dream["is_public"] = False
        
    return dream

# AI IMAGE GENERATION (FIXED: Actually save and display images)
@app.post("/api/dreams/{dream_id}/generate-image")
def generate_dream_image(dream_id: str, image_data: dict, authorization: Optional[str] = Header(None)):
    user = get_user_from_header(authorization)
    if not user:
        return {"error": "Authentication required"}
    
    # Check limits
    if not user.get("is_premium", False) and user.get("image_tokens_used", 0) >= user.get("image_tokens_limit", 3):
        return {
            "error": "Image generation limit reached",
            "message": f"You've used all {user.get('image_tokens_limit', 3)} free image generations. Upgrade to premium for unlimited access!"
        }
    
    # Create a better mock image with dream content
    dream = dreams_db.get(dream_id)
    dream_text = dream.get("content", "Dream") if dream else "Dream"
    
    # Enhanced mock image (beautiful gradient with dream info)
    mock_image = "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZGVmcz48bGluZWFyR3JhZGllbnQgaWQ9ImdyYWQiIHgxPSIwJSIgeTE9IjAlIiB4Mj0iMTAwJSIgeTI9IjEwMCUiPjxzdG9wIG9mZnNldD0iMCUiIHN0b3AtY29sb3I9IiM2MzY2ZjEiLz48c3RvcCBvZmZzZXQ9IjMzJSIgc3RvcC1jb2xvcj0iIzhhNWNmNiIvPjxzdG9wIG9mZnNldD0iNjYlIiBzdG9wLWNvbG9yPSIjYTg1NWY3Ii8+PHN0b3Agb2Zmc2V0PSIxMDAlIiBzdG9wLWNvbG9yPSIjZWM0ODk5Ii8+PC9saW5lYXJHcmFkaWVudD48L2RlZnM+PHJlY3Qgd2lkdGg9IjEwMCUiIGhlaWdodD0iMTAwJSIgZmlsbD0idXJsKCNncmFkKSIvPjx0ZXh0IHg9IjUwJSIgeT0iNDAlIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMjQiIGZpbGw9IndoaXRlIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkeT0iLjNlbSIgZm9udC13ZWlnaHQ9ImJvbGQiPkFJIEdlbmVyYXRlZCBJbWFnZTwvdGV4dD48dGV4dCB4PSI1MCUiIHk9IjYwJSIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjE0IiBmaWxsPSJ3aGl0ZSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPkZyb20geW91ciBkcmVhbSBhYm91dDwvdGV4dD48dGV4dCB4PSI1MCUiIHk9IjcwJSIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjEyIiBmaWxsPSJ3aGl0ZSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iIGZvbnQtc3R5bGU9Iml0YWxpYyI+IuKAnOKAnTwvdGV4dD48L3N2Zz4="
    
    # FIXED: Actually update the dream with the image
    if dream_id in dreams_db:
        dreams_db[dream_id]["ai_image"] = mock_image
        dreams_db[dream_id]["is_public"] = True  # Make it visible in gallery
    
    # Update user token count
    if not user.get("is_premium", False):
        email = user.get("email")
        if email and email in users_db:
            users_db[email]["image_tokens_used"] = user.get("image_tokens_used", 0) + 1
            user_tokens[f"token_{user['id']}"]["image_tokens_used"] = user.get("image_tokens_used", 0) + 1
    
    return {
        "message": "Image generated successfully!",
        "image_url": mock_image,
        "image_data": mock_image,  # FIXED: Frontend expects this field
        "image_base64": mock_image,
        "task_id": f"img_task_{dream_id}",
        "tokens_remaining": max(0, user.get("image_tokens_limit", 3) - user.get("image_tokens_used", 0) - 1)
    }

# AI VIDEO GENERATION (FIXED)
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
    
    # FIXED: Actually save video to dream
    if dream_id in dreams_db:
        dreams_db[dream_id]["ai_video"] = "https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4"
        dreams_db[dream_id]["video_base64"] = "sample_video_data"
        dreams_db[dream_id]["is_public"] = True  # Make visible in gallery
    
    # Update tokens
    if not user.get("is_premium", False):
        email = user.get("email")
        if email and email in users_db:
            users_db[email]["video_tokens_used"] = user.get("video_tokens_used", 0) + 1
            user_tokens[f"token_{user['id']}"]["video_tokens_used"] = user.get("video_tokens_used", 0) + 1
    
    return {
        "message": "Video generation started successfully!",
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

# LUCY AI (FIXED)
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

I've analyzed your dream: "{dream.get('content', 'your beautiful dream')[:50]}..."

🌙 **Symbolic Meaning**: Your dream reflects transformation and personal growth. The imagery suggests you're processing recent experiences and emotions in a healthy way.

💫 **Emotional Insights**: The {dream.get('mood', 'peaceful')} mood indicates your inner emotional state is seeking balance and harmony.

🔮 **Deeper Analysis**: This dream represents:
- Your subconscious mind organizing thoughts and feelings
- Potential for positive change and new beginnings
- Inner wisdom guiding you toward clarity and peace

✨ **Lucy's Personal Message**: You have beautiful dream energy, {user.get('name', 'dear dreamer')}! Trust your intuition and the messages your dreams bring you.

Sweet dreams and keep exploring! 
- Lucy ✨

*You have {2 - user.get('lucy_tokens_used', 0)} Lucy interpretations remaining*"""
    
    # FIXED: Update dream and tokens
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

# DASHBOARD (FIXED)
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

# GALLERY ENDPOINT (FIXED: Actually return dreams with AI content)
@app.get("/api/gallery/dreams")
def get_gallery():
    # FIXED: Return public dreams with AI content
    public_dreams = []
    for dream in dreams_db.values():
        if dream.get("is_public", False) and (dream.get("ai_image") or dream.get("ai_video")):
            public_dreams.append(dream)
    
    # If no public dreams, create some sample ones for testing
    if not public_dreams:
        sample_dreams = [
            {
                "id": "sample_1",
                "content": "A magical forest filled with glowing butterflies and floating crystals",
                "mood": "mystical",
                "tags": ["nature", "magic", "peaceful"],
                "user_name": "DreamExplorer",
                "user_role": "dreamer",
                "ai_image": "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZGVmcz48bGluZWFyR3JhZGllbnQgaWQ9ImdyYWQxIiB4MT0iMCUiIHkxPSIwJSIgeDI9IjEwMCUiIHkyPSIxMDAlIj48c3RvcCBvZmZzZXQ9IjAlIiBzdG9wLWNvbG9yPSIjMTBiOTgxIi8+PHN0b3Agb2Zmc2V0PSIxMDAlIiBzdG9wLWNvbG9yPSIjMzMzOGZmIi8+PC9saW5lYXJHcmFkaWVudD48L2RlZnM+PHJlY3Qgd2lkdGg9IjEwMCUiIGhlaWdodD0iMTAwJSIgZmlsbD0idXJsKCNncmFkMSkiLz48dGV4dCB4PSI1MCUiIHk9IjUwJSIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjE2IiBmaWxsPSJ3aGl0ZSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPk1hZ2ljYWwgRm9yZXN0IERyZWFtPC90ZXh0Pjwvc3ZnPg==",
                "created_at": datetime.now().isoformat(),
                "has_liked": False
            },
            {
                "id": "sample_2", 
                "content": "Flying through clouds above a rainbow-colored city",
                "mood": "exciting",
                "tags": ["flying", "city", "adventure"],
                "user_name": "SkyDreamer",
                "user_role": "dreamer",
                "ai_image": "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZGVmcz48bGluZWFyR3JhZGllbnQgaWQ9ImdyYWQyIiB4MT0iMCUiIHkxPSIwJSIgeDI9IjEwMCUiIHkyPSIxMDAlIj48c3RvcCBvZmZzZXQ9IjAlIiBzdG9wLWNvbG9yPSIjZjU5ZTBiIi8+PHN0b3Agb2Zmc2V0PSIxMDAlIiBzdG9wLWNvbG9yPSIjZWY0NDQ0Ii8+PC9saW5lYXJHcmFkaWVudD48L2RlZnM+PHJlY3Qgd2lkdGg9IjEwMCUiIGhlaWdodD0iMTAwJSIgZmlsbD0idXJsKCNncmFkMikiLz48dGV4dCB4PSI1MCUiIHk9IjUwJSIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjE2IiBmaWxsPSJ3aGl0ZSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPkZseWluZyBEcmVhbSBBZHZlbnR1cmU8L3RleHQ+PC9zdmc+",
                "created_at": datetime.now().isoformat(),
                "has_liked": False
            }
        ]
        return sample_dreams
    
    return public_dreams[-10:]  # Return last 10 public dreams

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
