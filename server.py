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
        "access_token": f"token_{user_id}",
        "token_type": "bearer",
        "user": users_db[email]
    }

@app.post("/api/auth/login") 
def login(credentials: dict):
    email = credentials.get("email", "")
    
    if email in users_db:
        user = users_db[email]
        return {
            "access_token": f"token_{user['id']}",
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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
