<<<<<<< HEAD
# 🌙 Lucidly - AI Dream Journaling App

A comprehensive mobile dream journaling app with AI-powered features, social platform, and analytics.

## ✨ Features

- **Dream Journaling**: Log and organize your dreams with mood tracking
- **AI Image Generation**: Create visual representations using OpenAI DALL-E 3
- **AI Video Generation**: Generate dream videos using Luma Dream Machine
- **Lucy AI Interpreter**: Premium dream analysis and interpretation
- **Social Platform**: Share dreams, get interpretations, connect with community
- **Analytics Dashboard**: Comprehensive stats, mood insights, and progress tracking

## 🚀 Deployment

Backend deployed on Railway with FastAPI and MongoDB.

## 🛠 Tech Stack

- **Frontend**: Expo React Native
- **Backend**: FastAPI (Python)
- **Database**: MongoDB
- **AI**: OpenAI GPT-4 & DALL-E 3, Luma Dream Machine

---

**Built with ❤️ for dreamers worldwide**
=======
# Lucidly – Expo SDK 54 + expo-router Skeleton

**How to use (Windows PowerShell):**

1. Create the folder and extract the ZIP:
```
New-Item -ItemType Directory -Path 'C:\dev\lucidly_app\Lucidly' -Force | Out-Null
```
Extract this ZIP into that folder.

2. Install deps & align versions:
```
Set-Location 'C:\dev\lucidly_app\Lucidly'
npm install
npx expo install
```

3. Update IDs:
- Edit `app.json` → set `"android.package"` to your real id (e.g., `com.yourcompany.lucidly`).

4. Local test:
```
npx expo start --clear
```

5. Link & build:
```
npm i -g eas-cli
eas login
eas project:link
eas project:info
eas build -p android --profile production --clear-cache
```
>>>>>>> 03b9abe (Initial commit of real repo root)
