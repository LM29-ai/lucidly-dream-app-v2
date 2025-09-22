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
