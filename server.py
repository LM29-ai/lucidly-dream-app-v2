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
        "role": "dreamer",
        # FREE TIER TOKENS!
        "lucy_tokens_used": 0,
        "lucy_tokens_limit": 3,
        "image_tokens_used": 0,
        "image_tokens_limit": 3,
        "video_tokens_used": 0,
        "video_tokens_limit": 3,
        "generation_count": 0  # For old image generation check
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
        "role": "dreamer",
        # FREE TIER TOKENS VISIBLE!
        "lucy_tokens_used": 0,
        "lucy_tokens_limit": 3,
        "image_tokens_used": 0,
        "image_tokens_limit": 3,
        "video_tokens_used": 0,
        "video_tokens_limit": 3,
        "generation_count": 0
    }

# DREAMS ENDPOINTS
@app.get("/api/dreams")
def get_dreams():
    return []

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

# AI IMAGE GENERATION ENDPOINT (FIXED - Returns proper image data!)
@app.post("/api/dreams/{dream_id}/generate-image")
def generate_dream_image(dream_id: str, image_data: dict):
    # Mock base64 image (tiny 1x1 pixel PNG)
    mock_image_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    
    # Update dream with generated image
    if dream_id in dreams_db:
        dreams_db[dream_id]["ai_image"] = f"data:image/png;base64,{mock_image_base64}"
    
    return {
        "message": "Image generated successfully",
        "image_url": f"data:image/png;base64,{mock_image_base64}",
        "image_base64": mock_image_base64,
        "task_id": f"img_task_{dream_id}",
        "demo_mode": True
    }

# AI VIDEO GENERATION ENDPOINT (ADDED!)
@app.post("/api/dreams/{dream_id}/generate-video")
def generate_dream_video(dream_id: str, video_data: dict):
    # Mock video response
    if dream_id in dreams_db:
        dreams_db[dream_id]["ai_video"] = "https://example.com/mock-video.mp4"
        dreams_db[dream_id]["video_base64"] = "mock_video_base64_data"
    
    return {
        "message": "Video generation started",
        "task_id": f"vid_task_{dream_id}",
        "estimated_time": "60-120 seconds",
        "video_url": "https://example.com/mock-video.mp4",
        "demo_mode": True
    }

# VIDEO STATUS ENDPOINT (ADDED!)
@app.get("/api/dreams/{dream_id}/video-status")
def get_video_status(dream_id: str):
    return {
        "status": "completed",
        "video_url": "https://example.com/mock-video.mp4",
        "video_base64": "mock_video_base64_data",
        "progress": "100%"
    }

# LUCY AI INTERPRETATION ENDPOINT (FIXED - FREE TIER!)
@app.post("/api/dreams/{dream_id}/lucy-interpretation")
def get_lucy_interpretation(dream_id: str, request_data: dict):
    dream = dreams_db.get(dream_id)
    if not dream:
        return {"error": "Dream not found"}
    
    # FIXED: No premium required - use free tokens!
    interpretation = f"""Hello dreamer! ✨

I've analyzed your dream about "{dream.get('content', 'your experience')[:50]}..." and here's what I see:

🌙 **Symbolic Meaning**: Your dream reflects your subconscious processing of recent experiences and emotions. The imagery suggests transformation and personal growth.

💫 **Emotional Insights**: The mood you felt ({dream.get('mood', 'peaceful')}) indicates your inner emotional state. This suggests you're seeking balance and harmony in your life.

🔮 **Deeper Analysis**: This dream may represent:
- A desire for change or new beginnings
- Processing of daily experiences and emotions  
- Your mind's way of organizing thoughts and feelings

✨ **Lucy's Wisdom**: Dreams are windows to your inner self. Trust your intuition about what resonates most with you. Each dream is a gift from your subconscious mind.

Remember, you are the best interpreter of your own dreams. I'm here to guide you on this beautiful journey of self-discovery.

Sweet dreams and keep exploring! 
- Lucy ✨

*You have used 1 of your 3 free Lucy interpretations*"""
    
    # Update dream with interpretation
    if dream_id in dreams_db:
        dreams_db[dream_id]["ai_interpretation"] = interpretation
    
    return {
        "dream_id": dream_id,
        "interpretation": interpretation,
        "cached": False
    }

# DASHBOARD ENDPOINTS
@app.get("/api/dashboard/stats")
def get_dashboard_stats():
    return {
        "dream_count": len(dreams_db),
        "lucid_count": 0,
        "lucid_percentage": 0,
        "current_streak": 0,
        "longest_streak": 0,
        "ai_creations_count": 0,
        "mood_distribution": {"peaceful": 80, "excited": 20},
        "recent_dreams": list(dreams_db.values())[-5:]
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
